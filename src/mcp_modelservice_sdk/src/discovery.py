"""
Module for discovering Python files and functions with enhanced support for directory-based routing.
This module provides functionality to discover Python files from a source path and extract
functions from those files, preserving file path information for routing purposes.
"""

import importlib.util
import inspect  # Moved from bottom to top
import logging
import os
import pathlib
from enum import Enum
from typing import Any, Callable, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ValidFileTypes(Enum):
    PYTHON = ".py"


def discover_py_files(source_path_str: str) -> List[pathlib.Path]:
    """
    Discovers Python files from a given file or directory path.

    This function scans a file or directory path and identifies all Python files.
    It preserves the full path information which is essential for directory-based routing.

    Args:
        source_path_str: The path to a Python file or a directory.

    Returns:
        A list of pathlib.Path objects for discovered .py files with full path information.

    Raises:
        FileNotFoundError: If the source_path_str does not exist.
        ValueError: If source_path_str is not a file or directory.
    """
    # Normalize the path first to handle both relative and absolute paths
    try:
        from .core import _normalize_path
    except ImportError:
        # Define the function locally if import fails
        def _normalize_path(path_str):
            import os
            import pathlib

            path_obj = pathlib.Path(path_str)
            if path_obj.is_absolute():
                return str(path_obj)
            return str(pathlib.Path(os.getcwd()) / path_obj)

    normalized_path = _normalize_path(source_path_str)
    logger.debug(
        f"Normalized source path: {normalized_path} (original: {source_path_str})"
    )
    source_path = pathlib.Path(normalized_path).resolve()  # Get absolute path
    if not source_path.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path_str}")

    py_files: List[pathlib.Path] = []
    if source_path.is_file():
        if source_path.suffix == ValidFileTypes.PYTHON.value:
            py_files.append(source_path)
            logger.info(f"Discovered Python file: {source_path}")
        else:
            logger.warning(f"Source file is not a Python file, skipping: {source_path}")
    elif source_path.is_dir():
        logger.info(f"Scanning directory for Python files: {source_path}")
        for root, _, files in os.walk(source_path):
            root_path = pathlib.Path(root)
            for file_name in files:  # Renamed 'file' to 'file_name' to avoid conflict
                if file_name.endswith(ValidFileTypes.PYTHON.value):
                    file_path = root_path / file_name
                    py_files.append(file_path)
                    # Log the relative path for better debugging
                    rel_path = file_path.relative_to(source_path)
                    logger.debug(
                        f"Discovered Python file: {rel_path} (full path: {file_path})"
                    )
    else:
        raise ValueError(f"Source path is not a file or directory: {source_path}")

    if not py_files:
        logger.warning(f"No Python files found in: {source_path}")
    else:
        logger.info(f"Discovered {len(py_files)} Python file(s) from {source_path}")
    return py_files


def _load_module_from_path(
    file_path: pathlib.Path,
) -> Optional[Any]:  # Changed to Any from types.ModuleType for broader compatibility
    """
    Loads a Python module dynamically from a file path.

    Args:
        file_path: The path to the Python file.

    Returns:
        The loaded module object, or None if loading fails.
    """
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            logger.error(
                f"Failed to load module '{module_name}' from '{file_path}': {e}",
                exc_info=True,
            )
            return None
    else:
        logger.error(f"Could not create module spec for '{file_path}'")
        return None


def discover_functions(
    file_paths: List[pathlib.Path], target_function_names: Optional[List[str]] = None
) -> List[Tuple[Callable[..., Any], str, pathlib.Path]]:  # Made Callable more specific
    """
    Discovers functions from a list of Python files.

    This function loads each Python file as a module and discovers functions within it.
    It preserves the file path information which is essential for directory-based routing.

    Args:
        file_paths: A list of paths to Python files.
        target_function_names: An optional list of specific function names to discover.
                               If None, all functions are discovered.

    Returns:
        A list of tuples, each containing (function_object, function_name, file_path).
        The file_path is the full path to the Python file containing the function.
    """
    discovered_functions: List[Tuple[Callable[..., Any], str, pathlib.Path]] = []
    function_name_set = set(target_function_names) if target_function_names else set()

    for file_path in file_paths:
        logger.info(f"Discovering functions in: {file_path}")
        module = _load_module_from_path(file_path)
        if module:
            logger.debug(f"Module loaded successfully: {module.__name__}")
            module_functions = []
            for name, member in inspect.getmembers(module):
                logger.debug(f"Found member: {name}, type: {type(member).__name__}")
                # Only include functions defined in this module (not imported)
                if inspect.isfunction(member):
                    logger.debug(f"Member {name} is a function. Module: {member.__module__}, Expected: {module.__name__}")
                    if member.__module__ == module.__name__:
                        # Skip private functions (starting with underscore)
                        if name.startswith("_") and not (
                            name.startswith("__") and name.endswith("__")
                        ):
                            logger.debug(
                                f"Skipping private function: {name} in {file_path}"
                            )
                            continue

                        if not function_name_set or name in function_name_set:
                            logger.debug(f"Adding function {name} to discovered functions")
                            module_functions.append((member, name))
                            if function_name_set and name in function_name_set:
                                function_name_set.remove(name)
                    else:
                        logger.debug(f"Skipping function {name} because it's not defined in this module")

            if module_functions:
                logger.info(f"Found {len(module_functions)} function(s) in {file_path}")
                for func, name in module_functions:
                    discovered_functions.append((func, name, file_path))
            else:
                logger.warning(f"No suitable functions found in {file_path}")
        else:
            logger.warning(f"Failed to load module from {file_path}")

    if function_name_set and len(function_name_set) > 0:
        logger.warning(
            f"Could not find the following specified functions: {list(function_name_set)}"
        )

    return discovered_functions
