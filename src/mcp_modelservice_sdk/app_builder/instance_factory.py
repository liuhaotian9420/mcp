"""
Factory for creating MCP instances from discovered functions.
"""

import logging
import os
import pathlib
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..discovery import discover_py_files, discover_functions
from ..utils import TransformationError, normalize_path
from .mocking import get_fastmcp_class, FastMCPType
from .routing import get_route_from_path, validate_resource_prefix
from .validation import validate_and_wrap_tool, get_module_docstring
from .caching import SessionToolCallCache

logger = logging.getLogger(__name__)


def discover_and_group_functions(
    source_path_str: str, target_function_names: Optional[List[str]] = None
) -> Tuple[Dict[pathlib.Path, List[Tuple[Callable[..., Any], str]]], pathlib.Path]:
    """
    Discovers Python files, extracts functions, and groups them by file path.

    Args:
        source_path_str: Path to the Python file or directory containing functions.
        target_function_names: Optional list of function names to expose. If None, all are exposed.

    Returns:
        A tuple containing:
        - Dictionary mapping file paths to lists of (function, function_name) tuples
        - Base directory path for relative path calculations

    Raises:
        TransformationError: If no Python files or functions are found.
    """
    try:
        py_files = discover_py_files(source_path_str)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Error discovering Python files: {e}")
        raise TransformationError(f"Failed to discover Python files: {e}")

    if not py_files:
        logger.error("No Python files found to process. Cannot create any MCP tools.")
        raise TransformationError(
            "No Python files found to process. Ensure the path is correct and contains Python files."
        )

    # Normalize the path and convert to Path object for consistent handling
    normalized_path = normalize_path(source_path_str)
    source_path = pathlib.Path(normalized_path)
    logger.debug(f"Normalized source path: {normalized_path}")
    logger.debug(f"Original source path: {source_path_str}")

    # Ensure the path exists
    if not source_path.exists():
        error_msg = f"Source path does not exist: {normalized_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    if source_path.is_file():
        base_dir = source_path.parent
    else:
        base_dir = source_path

    functions_to_wrap = discover_functions(py_files, target_function_names)

    if not functions_to_wrap:
        message = "No functions found to wrap as MCP tools."
        if target_function_names:
            message += f" (Specified functions: {target_function_names} not found, or no functions in source matching criteria)."
        else:
            message += (
                " (No functions discovered in the source path matching criteria)."
            )
        logger.error(message)
        raise TransformationError(message)

    # Group functions by file path to create one FastMCP instance per file
    functions_by_file: Dict[pathlib.Path, List[Tuple[Callable[..., Any], str]]] = {}
    for func, func_name, file_path in functions_to_wrap:
        if file_path not in functions_by_file:
            functions_by_file[file_path] = []
        functions_by_file[file_path].append((func, func_name))

    return functions_by_file, base_dir


def create_mcp_instances(
    functions_by_file: Dict[pathlib.Path, List[Tuple[Callable[..., Any], str]]],
    base_dir: pathlib.Path,
    mcp_server_name: str,
    tool_call_cache: Optional[SessionToolCallCache] = None,
) -> Dict[pathlib.Path, Tuple[Any, str, int]]:
    """
    Creates FastMCP instances for each file and registers functions as tools.

    Args:
        functions_by_file: Dictionary mapping file paths to lists of (function, function_name) tuples
        base_dir: Base directory path for relative path calculations
        mcp_server_name: Base name for FastMCP servers
        tool_call_cache: Optional cache for tool call results

    Returns:
        Dictionary mapping file paths to tuples of (FastMCP instance, route path, tools count)
    """
    # Get the FastMCP class (real or mock)
    FastMCP = get_fastmcp_class()

    # Create the main FastMCP instance that will host all the mounted subservers
    logger.info(f"Created main FastMCP instance '{mcp_server_name}'")

    mcp_instances = {}

    # Create a FastMCP instance for each file and register its tools
    for file_path, funcs in functions_by_file.items():
        # Generate a unique name for this FastMCP instance based on file path
        relative_path = file_path.relative_to(base_dir)
        file_specific_name = str(relative_path).replace(os.sep, "_").replace(".py", "")
        instance_name = f"{file_specific_name}"

        # Extract the module docstring to use as instructions
        instructions = get_module_docstring(file_path)
        if instructions:
            logger.info(
                f"Using module docstring as instructions for FastMCP instance '{instance_name}'"
            )
        else:
            logger.info(
                f"No module docstring found for '{instance_name}', using default instructions"
            )
            # Default instructions based on the file path
            instructions = f"MCP server for {relative_path} functionality"

        logger.info(f"Creating FastMCP instance '{instance_name}' for {file_path}")
        file_mcp: FastMCPType = FastMCP(name=instance_name, instructions=instructions)

        # Register all functions from this file as tools
        tools_registered = 0
        for func, func_name in funcs:
            logger.info(f"Processing function '{func_name}' from {file_path}...")
            try:
                validate_and_wrap_tool(
                    file_mcp, func, func_name, file_path, tool_call_cache
                )
                tools_registered += 1
            except Exception as e:
                logger.error(f"Error registering function {func_name}: {e}")
                continue

        # Skip if no tools were registered
        if tools_registered == 0:
            logger.warning(
                f"No tools were successfully created and registered for {file_path}. Skipping."
            )
            continue

        # Determine the mount prefix for this FastMCP instance
        route_path = get_route_from_path(file_path, base_dir)
        route_path_verified = validate_resource_prefix(f"{route_path}")

        # Store the instance, route path, and tools count
        mcp_instances[file_path] = (file_mcp, route_path_verified, tools_registered)

    return mcp_instances
