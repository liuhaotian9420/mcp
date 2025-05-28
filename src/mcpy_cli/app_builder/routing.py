"""
Routing utilities for MCP applications.
"""

import os
import pathlib
import re
import logging
from pydantic import AnyUrl
import pydantic

logger = logging.getLogger(__name__)

# Compile the "valid scheme" regex
_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*$")


def get_route_from_path(file_path: pathlib.Path, base_dir: pathlib.Path) -> str:
    """
    Converts a file path to a route path based on its directory structure.

    Args:
        file_path: Path to the Python file.
        base_dir: Base directory where all source files are located.

    Returns:
        A route path for the FastMCP instance derived from the file path.
        Example: base_dir/subdir/module.py -> subdir/module
        Note: Does NOT include a leading slash to allow clean path joining later.
    """
    # Handle special case for __init__.py files
    if file_path.name == "__init__.py":
        # For __init__.py, use the parent directory name instead
        rel_path = file_path.parent.relative_to(base_dir)
        # Return empty string for root __init__.py to avoid extra slashes
        if str(rel_path) == ".":
            return ""
        return str(rel_path).replace(os.sep, "/")

    # Regular Python files
    rel_path = file_path.relative_to(base_dir)
    # Remove .py extension and convert path separators to route segments
    route_path = str(rel_path.with_suffix("")).replace(os.sep, "/")
    # Handle case where route_path is just "." (this happens for files directly in base_dir)
    if route_path == ".":
        return ""
    return route_path


def sanitize_prefix(raw: str, *, fallback: str = "x") -> str:
    """
    Turn `raw` into a valid URL scheme: must start with [A-Za-z],
    then contain only [A-Za-z0-9+.-].  If the result would be empty
    or start with a non-letter, we prepend `fallback` (default "x").
    """
    # Drop any leading/trailing whitespace
    s = raw.strip()
    # Replace invalid chars with hyphens (you could use '' instead)
    s = re.sub(r"[^A-Za-z0-9+.\-]", "-", s)
    # Collapse multiple hyphens
    s = re.sub(r"-{2,}", "-", s)
    # Trim hyphens/dots from ends (they're legal but ugly)
    s = s.strip("-.")
    # If it doesn't start with a letter, prepend fallback
    if not s or not s[0].isalpha():
        s = fallback + s
    # Final sanity-check: if it still doesn't match, fallback entirely
    if not _SCHEME_RE.match(s):
        return fallback
    return s


def validate_resource_prefix(prefix: str) -> str:
    """
    Validate and sanitize a resource prefix for use in URLs.

    Args:
        prefix: The prefix to validate

    Returns:
        A valid resource prefix
    """
    valid_resource = "resource://path/to/resource"
    test_case = f"{prefix}{valid_resource}"
    try:
        AnyUrl(test_case)
        return prefix
    except pydantic.ValidationError:
        # update the prefix such that it is valid
        new_prefix = sanitize_prefix(prefix)
        return new_prefix
    except Exception as e:
        logger.error(f"Error validating resource prefix: {e}")
        return prefix
