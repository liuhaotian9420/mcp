"""
Utility functions for packaging MCP model services.
"""

import inspect
import logging
import pathlib
import shutil
from typing import Dict, List, Optional

from .discovery import discover_py_files, discover_functions
from .utils import TransformationError  # For _copy_source_code

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
                if inspect.getcomments(func):
                    docstring += f"""\n\nAdditional comments:\n{inspect.getcomments(func)}"""
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
    enable_event_store: bool = False,
    event_store_path: Optional[str] = None,
    stateless_http: bool = False,
    json_response: bool = False,
    legacy_sse: bool = False,
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
        mode: Mode for the MCP application (composed or routed).
        enable_event_store: Whether to enable the SQLite event store.
        event_store_path: Optional custom path for the event store database.
        stateless_http: Whether to enable stateless HTTP mode.
        json_response: Whether to use JSON response format instead of SSE.
        legacy_sse: Whether to enable legacy SSE mode.

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

    # Handle event store flags
    if enable_event_store:
        cli_flags.append("--enable-event-store")
        if event_store_path:
            cli_flags.append(f'--event-store-path "{event_store_path}"')

    # Handle transport configuration flags
    if stateless_http:
        cli_flags.append("--stateless-http")

    if json_response:
        cli_flags.append("--json-response")

    # Handle legacy SSE flag
    if legacy_sse:
        cli_flags.append("--legacy-sse")

    # Handle reload and workers for uvicorn
    uvicorn_flags = []
    if reload_dev_mode:
        uvicorn_flags.append("--reload")

    if workers_uvicorn and workers_uvicorn > 0:
        uvicorn_flags.append(f"--workers {workers_uvicorn}")

    # Join all CLI flags
    cli_flags_str = " ".join(cli_flags) if cli_flags else ""
    uvicorn_flags_str = " ".join(uvicorn_flags) if uvicorn_flags else ""

    # Replace placeholders in the template
    content = template_str.format(
        source_path=source_path,
        mcp_server_name=mcp_server_name,
        mcp_server_root_path=mcp_server_root_path,
        mcp_service_base_path=mcp_service_base_path,
        log_level=log_level,
        effective_host=effective_host,
        effective_port=effective_port,
        cli_flags=cli_flags_str,
        uvicorn_flags=uvicorn_flags_str,
        run_options_with_continuation=f" {uvicorn_flags_str}" if uvicorn_flags_str else "",
    )

    return content


def _generate_readme_md_content(
    package_name: str,
    mcp_server_name: str,
    service_url_example: str,
    tool_docs: List[Dict[str, str]],
) -> str:
    """
    Generate README.md content for the packaged service.
    """
    # Read the template
    template_str = _read_template("README.md.template")

    # Generate tool documentation section
    tools_section = ""
    if tool_docs:
        for tool in tool_docs:
            tools_section += f"### `{tool['name']}`\n\n"
            tools_section += f"**Signature:** `{tool['signature']}`\n\n"
            tools_section += f"**Description:**\n```\n{tool['docstring']}\n```\n\n"
            tools_section += f"**Source File:** `{tool['file_path']}`\n\n---\n"
    else:
        tools_section = "No tools were automatically documented during packaging. Please refer to the service provider for details on available tools.\n"

    # Create a dictionary with all the replacements
    replacements = {
        "package_name": package_name,
        "mcp_server_name": mcp_server_name,
        "service_url_example": service_url_example,
        "tool_documentation_section": tools_section,
        "service_purpose_description": "performing specific tasks",  # Default placeholder
        "service_purpose_description_short": "specific tasks",  # Default placeholder for shorter description
    }
    
    # Manually replace each placeholder in the template
    content = template_str
    for key, value in replacements.items():
        placeholder = "{" + key + "}"
        content = content.replace(placeholder, value)

    return content


def _generate_readme_zh_md_content(
    package_name: str,
    mcp_server_name: str,
    service_url_example: str,
    tool_docs: List[Dict[str, str]],
) -> str:
    """
    Generate Chinese README.md content for the packaged service.
    """
    # Read the template
    template_str = _read_template("README_zh.md.template")

    # Generate tool documentation section in Chinese
    tools_section = ""
    if tool_docs:
        for tool in tool_docs:
            tools_section += f"### `{tool['name']}`\n\n"
            tools_section += f"**函数签名:** `{tool['signature']}`\n\n"
            tools_section += f"**描述:**\n```\n{tool['docstring']}\n```\n\n"
            tools_section += f"**源文件:** `{tool['file_path']}`\n\n---\n"
    else:
        tools_section = "打包过程中未自动记录任何工具。请联系服务提供商了解可用工具的详细信息。\n"

    # Create a dictionary with all the replacements
    replacements = {
        "package_name": package_name,
        "mcp_server_name": mcp_server_name,
        "service_url_example": service_url_example,
        "tool_documentation_section": tools_section,
        "service_purpose_description": "执行特定任务",  # Default placeholder in Chinese
        "service_purpose_description_short": "特定任务",  # Default placeholder for shorter description in Chinese
    }
    
    # Manually replace each placeholder in the template
    content = template_str
    for key, value in replacements.items():
        placeholder = "{" + key + "}"
        content = content.replace(placeholder, value)

    return content


def _copy_source_code(
    source_path_obj: pathlib.Path,
    project_dir: pathlib.Path,
    logger_to_use: logging.Logger,
) -> str:
    """
    Copy the user's source code to the project directory.

    Args:
        source_path_obj: Path to the source code (file or directory).
        project_dir: Destination project directory.
        logger_to_use: Logger to use for messages.

    Returns:
        The relative path to the copied source within the project directory.

    Raises:
        TransformationError: If copying fails.
    """
    try:
        if source_path_obj.is_file():
            # Copy single file
            dest_file = project_dir / source_path_obj.name
            shutil.copy2(source_path_obj, dest_file)
            logger_to_use.info(f"Copied source file: {source_path_obj} -> {dest_file}")
            return source_path_obj.name
        elif source_path_obj.is_dir():
            # Copy entire directory
            dest_dir = project_dir / source_path_obj.name
            shutil.copytree(source_path_obj, dest_dir)
            logger_to_use.info(
                f"Copied source directory: {source_path_obj} -> {dest_dir}"
            )
            return source_path_obj.name
        else:
            raise TransformationError(
                f"Source path is neither file nor directory: {source_path_obj}"
            )
    except Exception as e:
        logger_to_use.error(f"Failed to copy source code: {e}")
        raise TransformationError(f"Failed to copy source code: {e}")
