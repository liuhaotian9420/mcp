"""
Module for discovering Python files and functions.
"""

import importlib.util
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

    Args:
        source_path_str: The path to a Python file or a directory.

    Returns:
        A list of pathlib.Path objects for discovered .py files.

    Raises:
        FileNotFoundError: If the source_path_str does not exist.
        ValueError: If source_path_str is not a file or directory.
    """
    source_path = pathlib.Path(source_path_str)
    if not source_path.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path_str}")

    py_files: List[pathlib.Path] = []
    if source_path.is_file():
        if source_path.suffix == ValidFileTypes.PYTHON.value:
            py_files.append(source_path)
        else:
            logger.warning(
                f"Source file is not a Python file, skipping: {source_path_str}"
            )
    elif source_path.is_dir():
        for root, _, files in os.walk(source_path):
            for file_name in files:  # Renamed 'file' to 'file_name' to avoid conflict
                if file_name.endswith(ValidFileTypes.PYTHON.value):
                    py_files.append(pathlib.Path(root) / file_name)
    else:
        raise ValueError(f"Source path is not a file or directory: {source_path_str}")

    if not py_files:
        logger.warning(f"No Python files found in: {source_path_str}")
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

    Args:
        file_paths: A list of paths to Python files.
        target_function_names: An optional list of specific function names to discover.
                               If None, all functions are discovered.

    Returns:
        A list of tuples, each containing (function_object, function_name, file_path).
    """
    discovered_functions: List[Tuple[Callable[..., Any], str, pathlib.Path]] = []
    function_name_set = set(target_function_names) if target_function_names else None
    import inspect  # Moved import here as it's only used in this function

    for file_path in file_paths:
        module = _load_module_from_path(file_path)
        if module:
            for name, member in inspect.getmembers(module):
                if inspect.isfunction(member) and member.__module__ == module.__name__:
                    if function_name_set is None or name in function_name_set:
                        discovered_functions.append((member, name, file_path))
                        if function_name_set and name in function_name_set:
                            function_name_set.remove(name)

    if function_name_set and len(function_name_set) > 0:
        logger.warning(
            f"Could not find the following specified functions: {list(function_name_set)}"
        )

    return discovered_functions
