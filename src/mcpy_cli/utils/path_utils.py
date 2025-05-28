"""
Path utilities for the MCP-CLI.
"""

import os
import pathlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_path(path_str: str) -> str:
    """
    Normalize a path string to handle both relative and absolute paths.

    Args:
        path_str: Path string to normalize

    Returns:
        Normalized absolute path string
    """
    path_obj = pathlib.Path(path_str)

    # If it's already absolute, return it
    if path_obj.is_absolute():
        return str(path_obj)

    # Otherwise, make it absolute relative to the current working directory
    return str(pathlib.Path(os.getcwd()) / path_obj)


def validate_source_path(source_path: Optional[str], logger: logging.Logger) -> bool:
    """
    Validate that the source path exists and contains valid Python files.

    Args:
        source_path: Path to validate
        logger: Logger to use for messages

    Returns:
        True if the path is valid, False otherwise
    """
    if source_path is None:
        logger.error("Source path is None")
        return False

    path_obj = pathlib.Path(source_path)

    # Check if the path exists
    if not path_obj.exists():
        logger.error(f"Source path does not exist: {path_obj.absolute()}")
        logger.error(f"Current working directory: {pathlib.Path.cwd()}")
        return False

    # If it's a file, check if it's a Python file
    if path_obj.is_file() and path_obj.suffix.lower() != ".py":
        logger.error(f"Source path is not a Python file: {path_obj.absolute()}")
        return False

    # If it's a directory, check if it contains any Python files
    if path_obj.is_dir():
        py_files = list(path_obj.glob("**/*.py"))
        if not py_files:
            logger.error(f"No Python files found in directory: {path_obj.absolute()}")
            return False

    return True
