"""
Utility functions for packaging MCP model services.
"""

import inspect
import logging
import pathlib
import shutil
from typing import Dict, List, Optional, Any

from .discovery import discover_py_files, discover_functions
from .app_builder import TransformationError  # For _copy_source_code

logger = logging.getLogger(__name__)

TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"


def _read_template(template_name: str) -> str:
    """Reads a template file from the templates directory."""
    template_file = TEMPLATES_DIR / template_name
    try:
        with open(template_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_file}")
        raise  # Or handle more gracefully, e.g., return a default string or raise specific error
    except Exception as e:
        logger.error(f"Error reading template {template_file}: {e}")
        raise


def _get_tool_documentation_details(
    source_path_str: str,
    target_function_names: Optional[List[str]],
    logger_to_use: logging.Logger,
) -> List[Dict[str, str]]:
    """
    Discovers functions and extracts their name, signature, and docstring for documentation.
    """
    tool_details = []
    try:
        py_files = discover_py_files(source_path_str)
        if not py_files:
            logger_to_use.warning(
                f"No Python files found in {source_path_str} for documentation generation."
            )
            return []

        functions_to_document = discover_functions(py_files, target_function_names)
        if not functions_to_document:
            logger_to_use.warning(
                f"No functions found in {source_path_str} for documentation generation."
            )
            return []

        for func, func_name, file_path in functions_to_document:
            try:
                sig = inspect.signature(func)
                docstring = inspect.getdoc(func) or "No docstring provided."
                params = []
                for p_name, p in sig.parameters.items():
                    param_str = p_name
                    if p.annotation is not inspect.Parameter.empty:
                        ann_str = (
                            getattr(p.annotation, "__name__", None)
                            or getattr(p.annotation, "_name", None)
                            or str(p.annotation)
                        )
                        param_str += f": {ann_str}"
                    if p.default is not inspect.Parameter.empty:
                        param_str += f" = {p.default!r}"
                    params.append(param_str)

                return_annotation_str = ""
                if sig.return_annotation is not inspect.Signature.empty:
                    ret_ann_str = (
                        getattr(sig.return_annotation, "__name__", None)
                        or getattr(sig.return_annotation, "_name", None)
                        or str(sig.return_annotation)
                    )
                    if ret_ann_str != "<class 'inspect._empty'>":
                        return_annotation_str = f" -> {ret_ann_str}"

                full_signature = (
                    f"{func_name}({', '.join(params)}){return_annotation_str}"
                )

                tool_details.append(
                    {
                        "name": func_name,
                        "signature": full_signature,
                        "docstring": docstring,
                        "file_path": str(file_path.name),
                    }
                )
            except Exception as e:
                logger_to_use.error(
                    f"Error processing function {func_name} from {file_path} for documentation: {e}"
                )

    except Exception as e:
        logger_to_use.error(
            f"Failed to generate tool documentation details from {source_path_str}: {e}",
            exc_info=True,
        )

    return tool_details


def _generate_start_sh_content(
    source_path: str,
    mcp_server_name: str,
    mcp_server_root_path: str,
    mcp_service_base_path: str,
    log_level: str,
    effective_host: str,
    effective_port: int,
    cors_enabled: bool,
    cors_allow_origins: Optional[List[str]],
    target_function_names: Optional[List[str]],
    reload_dev_mode: bool,
    workers_uvicorn: Optional[int],
    mode: str,
) -> str:
    """
    Generate a start.sh script that directly uses the CLI to run the service.

    This approach eliminates the need for generating Python files, making the package
    simpler and more maintainable. The script installs the SDK package and any user
    dependencies, then runs the CLI with the appropriate parameters.

    Args:
        source_path: Path to the user's source code within the package.
        mcp_server_name: Name for the FastMCP server.
        mcp_server_root_path: Root path for the MCP service in Starlette.
        mcp_service_base_path: Base path for MCP protocol endpoints.
        log_level: Logging level for the service.
        effective_host: Host to configure in the packaged service.
        effective_port: Port to configure in the packaged service.
        cors_enabled: Whether to enable CORS middleware.
        cors_allow_origins: List of origins to allow for CORS.
        target_function_names: Optional list of specific function names to expose.
        reload_dev_mode: Whether to enable auto-reload in the packaged service.
        workers_uvicorn: Number of worker processes for uvicorn.

    Returns:
        The content of the start.sh script.
    """
    template_str = _read_template(
        "start.sh.template"
    )  # Using our lightweight template as the default

    # Prepare CLI flags - collect non-empty flags
    cli_flags = []
    
    # CORS settings
    if cors_enabled:
        cli_flags.append("--cors-enabled")
    else:
        cli_flags.append("--no-cors-enabled")

    # Handle CORS origins
    if cors_allow_origins and len(cors_allow_origins) > 0:
        for origin in cors_allow_origins:
            # Quote the origin to prevent shell expansion (e.g., * would expand to filenames)
            cli_flags.append(f'--cors-allow-origins "{origin}"')

    # Handle functions list
    if target_function_names and len(target_function_names) > 0:
        for func in target_function_names:
            # Quote the function name to handle names with spaces or special characters
            cli_flags.append(f'--functions "{func}"')

    # Handle mode flag
    if mode:
        cli_flags.append(f"--mode {mode}")

    # Command options
    run_options = []
    
    # Handle reload flag
    if reload_dev_mode:
        run_options.append("--reload")

    # Handle workers flag
    if workers_uvicorn is not None:
        run_options.append(f"--workers {workers_uvicorn}")

    # Join flags with proper line continuations
    cli_flags_str = " \\\n        ".join(cli_flags) if cli_flags else ""
    run_options_str = " \\\n        ".join(run_options) if run_options else ""
    
    # Handle run_options with continuation - only add \ and newline if there are run_options
    if run_options_str:
        run_options_with_continuation = f" \\\n        {run_options_str}"
    else:
        run_options_with_continuation = ""

    return template_str.format(
        source_path=source_path,
        mcp_server_name=mcp_server_name,
        mcp_server_root_path=mcp_server_root_path,
        mcp_service_base_path=mcp_service_base_path,
        log_level=log_level,
        effective_host=effective_host,
        effective_port=effective_port,
        cli_flags=cli_flags_str,
        run_options=run_options_str,
        run_options_with_continuation=run_options_with_continuation,
    )


def _generate_readme_md_content(
    package_name: str,
    mcp_server_name: str,
    mcp_server_root_path: str,
    mcp_service_base_path: str,
    effective_host: str,
    effective_port: int,
    tool_docs: List[Dict[str, str]],
) -> str:
    service_url_example = f"http://{effective_host}:{effective_port}{mcp_server_root_path}{mcp_service_base_path}"
    list_tools_endpoint = f"{service_url_example}/list_tools"

    tool_doc_md_parts = []
    if not tool_docs:
        tool_doc_md_parts.append("*No tools were found or specified for exposure.*\n")
    else:
        for tool in tool_docs:
            tool_doc_md_parts.append(f"### `{tool['name']}`")
            tool_doc_md_parts.append(f"*Source: `{tool['file_path']}`*\n")
            tool_doc_md_parts.append(
                f"**Signature:**\n```python\n{tool['signature']}\n```\n"
            )
            tool_doc_md_parts.append(
                f"**Description:**\n```\n{tool['docstring']}\n```\n---"
            )
    tool_documentation_section = "\n".join(tool_doc_md_parts)

    template_str = _read_template("README.md.template")

    context: Dict[str, Any] = {
        "package_name": package_name,
        "mcp_server_name": mcp_server_name,
        "mcp_server_root_path": mcp_server_root_path,
        "mcp_service_base_path": mcp_service_base_path,
        "service_url_example": service_url_example,
        "list_tools_endpoint": list_tools_endpoint,
        "tool_documentation_section": tool_documentation_section,
        "architecture_description": "Multi-mount architecture with directory-based routing",
        "architecture_detailed_explanation": """## Multi-Mount Architecture

This service uses a **directory-based routing** approach where each Python file in your source directory gets its own FastMCP instance mounted at a path derived from its location in the directory structure.

For example, if your source directory contains:
- `moduleA.py` → mounted at `{mcp_server_root_path}/moduleA{mcp_service_base_path}`
- `subsystemB/moduleC.py` → mounted at `{mcp_server_root_path}/subsystemB/moduleC{mcp_service_base_path}`
- `subsystemB/__init__.py` → mounted at `{mcp_server_root_path}/subsystemB{mcp_service_base_path}`

This organization allows for a more intuitive grouping of related tools based on your code's directory structure.""",
        "source_structure": "# Your source code structure",
        "sdk_version": "latest",
    }
    return template_str.format(**context)


def _generate_readme_zh_md_content(
    package_name: str,
    mcp_server_name: str,
    mcp_server_root_path: str,
    mcp_service_base_path: str,
    effective_host: str,
    effective_port: int,
    tool_docs: List[Dict[str, str]],
) -> str:
    """Generate Chinese README content using the Chinese template."""
    service_url_example = f"http://{effective_host}:{effective_port}{mcp_server_root_path}{mcp_service_base_path}"
    list_tools_endpoint = f"{service_url_example}/list_tools"

    tool_doc_md_parts = []
    if not tool_docs:
        tool_doc_md_parts.append("*未找到工具。*\n")
    else:
        for tool in tool_docs:
            tool_doc_md_parts.append(f"### `{tool['name']}`")
            tool_doc_md_parts.append(f"*来源: `{tool['file_path']}`*\n")
            tool_doc_md_parts.append(
                f"**函数签名:**\n```python\n{tool['signature']}\n```\n"
            )
            tool_doc_md_parts.append(
                f"**描述:**\n```\n{tool['docstring']}\n```\n---"
            )
    tool_documentation_section = "\n".join(tool_doc_md_parts)

    template_str = _read_template("README_zh.md.template")

    context: Dict[str, Any] = {
        "package_name": package_name,
        "mcp_server_name": mcp_server_name,
        "mcp_server_root_path": mcp_server_root_path,
        "mcp_service_base_path": mcp_service_base_path,
        "service_url_example": service_url_example,
        "list_tools_endpoint": list_tools_endpoint,
        "tool_documentation_section": tool_documentation_section,
        "architecture_description": "基于目录的多挂载架构路由",
        "architecture_detailed_explanation": """## 多挂载架构

此服务使用**基于目录的路由**方法，其中源目录中的每个 Python 文件都有自己的 FastMCP 实例，挂载在根据其在目录结构中的位置派生的路径上。

例如，如果您的源目录包含：
- `moduleA.py` → 挂载在 `{mcp_server_root_path}/moduleA{mcp_service_base_path}`
- `subsystemB/moduleC.py` → 挂载在 `{mcp_server_root_path}/subsystemB/moduleC{mcp_service_base_path}`
- `subsystemB/__init__.py` → 挂载在 `{mcp_server_root_path}/subsystemB{mcp_service_base_path}`

这种组织方式允许根据代码的目录结构对相关工具进行更直观的分组。""",
        "source_structure": "# 您的源代码结构",
        "sdk_version": "latest",
    }
    return template_str.format(**context)


def _copy_source_code(
    source_path_obj: pathlib.Path,
    project_dir: pathlib.Path,
    logger_to_use: logging.Logger,
) -> str:
    user_src_target_dir = project_dir
    try:
        if not user_src_target_dir.exists():
            user_src_target_dir.mkdir(parents=True, exist_ok=True)
        if source_path_obj.is_file():
            target_file = user_src_target_dir / source_path_obj.name
            shutil.copy2(source_path_obj, target_file)
            logger_to_use.info(f"Copied source file {source_path_obj} to {target_file}")
            return f"{source_path_obj.name}".replace(
                "\\", "/"
            )  # Ensure forward slashes
        elif source_path_obj.is_dir():
            target_dir_for_user_module = user_src_target_dir / source_path_obj.name
            if target_dir_for_user_module.exists():
                logger_to_use.info(
                    f"Removing existing target directory for user module: {target_dir_for_user_module}"
                )
                shutil.rmtree(target_dir_for_user_module)
            shutil.copytree(
                source_path_obj, target_dir_for_user_module, dirs_exist_ok=False
            )
            logger_to_use.info(
                f"Copied source directory {source_path_obj} to {target_dir_for_user_module}"
            )
            return f"{source_path_obj.name}".replace(
                "\\", "/"
            )  # Ensure forward slashes
        else:
            raise ValueError(
                f"Source path {source_path_obj} is not a file or directory."
            )
    except FileNotFoundError as e:
        logger_to_use.error(
            f"Error copying source code: File not found {e.filename if hasattr(e, 'filename') else e}"
        )
        raise TransformationError(f"Failed to copy source code: {e}")
    except Exception as e:
        logger_to_use.error(
            f"An unexpected error occurred while copying source code from {source_path_obj}: {e}",
            exc_info=True,
        )
        raise TransformationError(f"Failed to copy source code: {e}")
