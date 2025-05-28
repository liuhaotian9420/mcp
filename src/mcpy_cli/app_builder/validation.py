"""
Function validation and tool wrapping utilities for MCP applications.
"""

import inspect
import logging
import pathlib
from typing import Any, Callable, Optional

from ..discovery import _load_module_from_path
from .caching import SessionToolCallCache

logger = logging.getLogger(__name__)


def validate_and_wrap_tool(
    mcp_instance: Any,  # Use Any instead of FastMCP to avoid type errors
    func: Callable[..., Any],
    func_name: str,
    file_path: pathlib.Path,
    tool_call_cache: Optional[SessionToolCallCache] = None,
):
    """
    Validates function signature and docstring, then wraps it as an MCP tool.
    Logs warnings for missing type hints or docstrings.

    Args:
        mcp_instance: The FastMCP instance to add the tool to.
        func: The function to wrap as a tool.
        func_name: The name of the function.
        file_path: The path to the file containing the function.
        tool_call_cache: Optional cache for tool call results.
    """
    if not inspect.getdoc(func):
        logger.warning(
            f"Function '{func_name}' in '{file_path}' is missing a docstring."
        )
    else:
        # We'll be less strict about docstrings to make it easier to register functions
        docstring = inspect.getdoc(func) or ""
        logger.info(
            f"Processing function '{func_name}' with docstring: {docstring[:100]}..."
        )

        # Only log missing params, don't prevent registration
        sig = inspect.signature(func)
        missing_param_docs = []
        for p_name in sig.parameters:
            if not (
                f":param {p_name}:" in docstring
                or f"Args:\n    {p_name}" in docstring
                or f"{p_name}:" in docstring  # More relaxed pattern matching
                or f"{p_name} " in docstring  # More relaxed pattern matching
            ):
                missing_param_docs.append(p_name)
        if missing_param_docs:
            logger.info(
                f"Note: Function '{func_name}' has params that might need better docs: {', '.join(missing_param_docs)}."
            )

    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        if param.annotation is inspect.Parameter.empty:
            logger.warning(
                f"Parameter '{param_name}' in function '{func_name}' in '{file_path}' is missing a type hint."
            )
    if sig.return_annotation is inspect.Signature.empty:
        logger.warning(
            f"Return type for function '{func_name}' in '{file_path}' is missing a type hint."
        )

    try:
        # Apply caching if tool_call_cache is provided
        if tool_call_cache is not None:
            cached_func = tool_call_cache.create_cached_tool(func)
            mcp_instance.tool(name=func_name)(cached_func)
            logger.info(
                f"Successfully wrapped function '{func_name}' from '{file_path}' as a cached MCP tool."
            )
        else:
            mcp_instance.tool(name=func_name)(func)
            logger.info(
                f"Successfully wrapped function '{func_name}' from '{file_path}' as an MCP tool."
            )
    except Exception as e:
        logger.error(
            f"Failed to wrap function '{func_name}' from '{file_path}' as an MCP tool: {e}",
            exc_info=True,
        )


def get_module_docstring(file_path: pathlib.Path) -> Optional[str]:
    """
    Extract the module docstring from a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        The module docstring if found, None otherwise
    """
    try:
        module = _load_module_from_path(file_path)
        if module and module.__doc__:
            # Clean up the docstring - remove leading/trailing whitespace and normalize newlines
            docstring = inspect.cleandoc(module.__doc__)
            logger.debug(f"Extracted docstring from {file_path}: {docstring[:100]}...")
            return docstring
        else:
            logger.debug(f"No docstring found in {file_path}")
            return None
    except Exception as e:
        logger.warning(f"Error extracting docstring from {file_path}: {e}")
        return None
