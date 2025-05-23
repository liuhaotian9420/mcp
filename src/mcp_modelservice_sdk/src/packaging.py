"""
Module for building MCP model service packages.

This module provides functionality for packaging MCP services using a lightweight approach
that directly leverages the CLI rather than generating Python files.
"""

import logging
import os
import pathlib
import shutil
from typing import List, Optional

from .app_builder import TransformationError
from .packaging_utils import (
    _copy_source_code,
    _get_tool_documentation_details,
    _generate_start_sh_content,
    _generate_readme_md_content,
    _generate_readme_zh_md_content,
)
# Assuming _setup_logging will be exposed via core or a new utils module
# from .core import _setup_logging

logger = logging.getLogger(__name__)


def build_mcp_package(
    package_name_from_cli: str,
    source_path_str: str,
    target_function_names: Optional[List[str]],
    mcp_server_name: str,
    mcp_server_root_path: str,
    mcp_service_base_path: str,
    log_level: str,
    cors_enabled: bool,
    cors_allow_origins: List[str],
    effective_host: str,
    effective_port: int,
    reload_dev_mode: bool,
    workers_uvicorn: Optional[int],
    cli_logger: logging.Logger,  # Logger to use for packaging messages
    mode: str,
):
    print("DEBUG_PACKAGING: Entered build_mcp_package function.")
    # Use the provided logger for packaging messages
    packaging_logger = cli_logger
    source_path_obj = pathlib.Path(source_path_str).resolve()
    if not source_path_obj.exists():
        packaging_logger.error(
            f"Source path for packaging does not exist: {source_path_obj}"
        )
        raise FileNotFoundError(f"Source path {source_path_obj} not found.")

    base_output_dir = pathlib.Path.cwd() / package_name_from_cli
    project_dir = base_output_dir / "project"
    zip_file_name = f"{package_name_from_cli}.zip"
    zip_file_path = pathlib.Path.cwd() / zip_file_name

    packaging_logger.info(f"Preparing package: {package_name_from_cli}")
    packaging_logger.info(f"Project directory will be: {project_dir}")
    packaging_logger.info(f"Output zip file will be: {zip_file_path}")

    if base_output_dir.exists():
        packaging_logger.info(f"Removing existing output directory: {base_output_dir}")
        try:
            shutil.rmtree(base_output_dir)
        except OSError as e:
            packaging_logger.error(
                f"Failed to remove existing directory {base_output_dir}: {e}."
            )
            raise TransformationError(
                f"Could not remove existing directory {base_output_dir}: {e}"
            )
    if zip_file_path.exists():
        packaging_logger.info(f"Removing existing zip file: {zip_file_path}")
        try:
            zip_file_path.unlink()
        except OSError as e:
            packaging_logger.error(
                f"Failed to remove existing zip file {zip_file_path}: {e}."
            )
            raise TransformationError(
                f"Could not remove existing zip file {zip_file_path}: {e}"
            )

    try:
        print("DEBUG_PACKAGING: Entered main try block.")
        project_dir.mkdir(parents=True, exist_ok=True)
        print(f"DEBUG_PACKAGING: After project_dir.mkdir. project_dir: {project_dir}")
        packaging_logger.info(f"Created project directory: {project_dir}")

        print(
            f"DEBUG_PACKAGING: About to call _copy_source_code. Source: {source_path_obj}, Dest: {project_dir}"
        )
        # Copy the user's source code to the project directory
        original_source_rel_path_in_project = _copy_source_code(
            source_path_obj, project_dir, packaging_logger
        )

        # Get tool documentation for README
        tool_docs = _get_tool_documentation_details(
            str(source_path_obj), target_function_names, packaging_logger
        )

        # Using lightweight CLI-based packaging approach
        packaging_logger.info("Using lightweight CLI-based packaging approach...")
        if not tool_docs and target_function_names:
            packaging_logger.warning(
                f"Specified functions {target_function_names} not found for documentation. README tool list may be incomplete."
            )
        elif not tool_docs:
            packaging_logger.info(
                "No functions found or specified for documentation in README."
            )

        # Generate start.sh script that uses the CLI
        start_sh_content = _generate_start_sh_content(
            source_path=original_source_rel_path_in_project,
            mcp_server_name=mcp_server_name,
            mcp_server_root_path=mcp_server_root_path,
            mcp_service_base_path=mcp_service_base_path,
            log_level=log_level,
            effective_host=effective_host,
            effective_port=effective_port,
            cors_enabled=cors_enabled,
            cors_allow_origins=cors_allow_origins,
            target_function_names=target_function_names,
            reload_dev_mode=reload_dev_mode,
            workers_uvicorn=workers_uvicorn,
            mode=mode,
        )

        # Create a requirements.txt file for user dependencies if needed
        # This is a placeholder - in a real implementation, you might want to
        # analyze the user's code to determine dependencies
        requirements_file = project_dir / "requirements.txt"
        with open(requirements_file, "w", encoding="utf-8") as f:
            f.write("# Add your dependencies here\n")
        packaging_logger.info(f"Generated {requirements_file}")

        # Write the start.sh file
        start_sh_file = project_dir / "start.sh"
        with open(start_sh_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(start_sh_content)
        if os.name != "nt":  # 'nt' is the name for Windows
            start_sh_file.chmod(start_sh_file.stat().st_mode | 0o111)
            packaging_logger.info(f"Generated {start_sh_file} and made it executable.")
        else:
            packaging_logger.info(
                f"Generated {start_sh_file} (chmod skipped on Windows)."
            )

        # Generate README.md (for both modes)
        readme_md_content = _generate_readme_md_content(
            package_name=package_name_from_cli,
            mcp_server_name=mcp_server_name,
            mcp_server_root_path=mcp_server_root_path,
            mcp_service_base_path=mcp_service_base_path,
            effective_host=effective_host,
            effective_port=effective_port,
            tool_docs=tool_docs,
        )
        readme_file = project_dir / "README.md"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_md_content)
        packaging_logger.info(f"Generated {readme_file}")

        # Generate Chinese README.md
        readme_zh_md_content = _generate_readme_zh_md_content(
            package_name=package_name_from_cli,
            mcp_server_name=mcp_server_name,
            mcp_server_root_path=mcp_server_root_path,
            mcp_service_base_path=mcp_service_base_path,
            effective_host=effective_host,
            effective_port=effective_port,
            tool_docs=tool_docs,
        )
        readme_zh_file = project_dir / "README_zh.md"
        with open(readme_zh_file, "w", encoding="utf-8") as f:
            f.write(readme_zh_md_content)
        packaging_logger.info(f"Generated {readme_zh_file}")

        packaging_logger.info(
            f"Creating zip file: {zip_file_path} from directory {project_dir}"
        )
        shutil.make_archive(
            base_name=str(pathlib.Path.cwd() / package_name_from_cli),
            format="zip",
            root_dir=base_output_dir,
            base_dir="project",
        )
        # remove the project folder once zipping is done
        # ModelWhale is the bbbbbbbbeeessssssst
        # shutil.rmtree(str(pathlib.Path.cwd() / package_name_from_cli))
        packaging_logger.info(f"Successfully created package: {zip_file_path}")
        packaging_logger.info(
            f"Build directory: {base_output_dir}. This contains the 'project' folder."
        )

    except TransformationError as e:
        packaging_logger.error(
            f"Transformation error during packaging: {e}", exc_info=False
        )
        if base_output_dir.exists():
            try:
                shutil.rmtree(base_output_dir)
            except Exception as e_clean:
                packaging_logger.warning(
                    f"Failed to cleanup {base_output_dir}: {e_clean}"
                )
        raise
    except FileNotFoundError as e:
        packaging_logger.error(f"File not found during packaging: {e}", exc_info=True)
        if base_output_dir.exists():
            try:
                shutil.rmtree(base_output_dir)
            except Exception as e_clean:
                packaging_logger.warning(
                    f"Failed to cleanup {base_output_dir}: {e_clean}"
                )
        raise
    except Exception as e:
        packaging_logger.error(f"Unexpected error during packaging: {e}", exc_info=True)
        if base_output_dir.exists():
            packaging_logger.warning(f"Attempting to clean up {base_output_dir}.")
            try:
                shutil.rmtree(base_output_dir)
            except Exception as cleanup_e:
                packaging_logger.error(
                    f"Failed to cleanup {base_output_dir}: {cleanup_e}"
                )
        if zip_file_path.exists():
            try:
                zip_file_path.unlink()
            except Exception as zip_cleanup_e:
                packaging_logger.error(
                    f"Failed to cleanup zip file {zip_file_path}: {zip_cleanup_e}"
                )
        raise TransformationError(f"Unexpected error during packaging: {e}")
