"""
Function validation and tool wrapping utilities for MCP applications.
"""

import inspect
import pathlib
from logging import getLogger
from typing import Any, Callable, Dict, Optional

from ..discovery import _load_module_from_path
from .caching import SessionToolCallCache
from ..utils.schema_utils import get_cached_typeadapter

logger = getLogger(__name__)


def validate_tool_meta(
    func: Callable[..., Any],
    func_name: str,
    file_path: pathlib.Path,
) -> str:
    """
    Validates a function for use as an MCP tool by checking docstrings and type hints.
    The validation only produce warning logs to notify users

    Args:
        func: The function to validate
        func_name: The name of the function
        file_path: The path to the file containing the function

    Returns:
        Tuple containing (docstring, is_valid)
    """

    # 1. Function docstring -> tool description
    docstring = inspect.getdoc(func) or ""
    if not docstring:
        logger.warning(
            f"Function '{func_name}' in '{file_path}' is missing a docstring."
        )
    else:
        logger.info(
            f"Processing function '{func_name}' with docstring: {docstring[:100]}..."
        )

        # Check parameter documentation
        sig = inspect.signature(func)
        missing_param_docs = []
        for p_name in sig.parameters:
            if not (
                f":param {p_name}:" in docstring
                or f"Args:\n    {p_name}" in docstring
                or f"{p_name}:" in docstring
                or f"{p_name} " in docstring
            ):
                missing_param_docs.append(p_name)

        if missing_param_docs:
            logger.info(
                f"Note: Function '{func_name}' has params that might need better docs: {', '.join(missing_param_docs)}."
            )

    # Validate type hints in the docstring
    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        if param.annotation is inspect.Parameter.empty:
            logger.warning(
                f"Parameter '{param_name}' in function '{func_name}' in '{file_path}' is missing a type hint."
            )
            # is_valid = False

    if sig.return_annotation is inspect.Signature.empty:
        logger.warning(
            f"Return type for function '{func_name}' in '{file_path}' is missing a type hint."
        )
        # is_valid = False

    # Check for unsupported parameter types (*args, **kwargs)
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            raise ValueError(
                f"Function '{func_name}' with *args is not supported as a tool"
            )
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            raise ValueError(
                f"Function '{func_name}' with **kwargs is not supported as a tool"
            )

    #  2. Function String comment
    comments = inspect.getcomments(func)

    # 3. Append the comments to the docstring for additional info
    if comments:
        docstring = (
            docstring
            + f"""
            \n\nAdditional Comments:\n{comments}\n
            """
        )

    return docstring


def generate_tool_schema(
    func: Callable[..., Any], func_name: str
) -> Optional[Dict[str, Any]]:
    """
    Generates a JSON schema for a function using its type hints.

    Args:
        func: The function to generate a schema for
        func_name: The name of the function (for logging)

    Returns:
        A dictionary containing the processed schema, or None if generation failed
    """
    try:
        # Handle callable class
        if not inspect.isroutine(func):
            logger.info(
                f"Detected callable class for '{func_name}', extracting __call__ method"
            )
            # Use proper type checking for callable objects
            if hasattr(func, "__call__"):
                func = func.__call__

        # Use cached TypeAdapter for performance
        type_adapter = get_cached_typeadapter(func)
        schema = type_adapter.json_schema()

        # Process schema for MCP compatibility
        processed_schema = {
            "properties": schema.get("properties", {}),
            "required": schema.get("required", []),
            "type": "object",
        }
        logger.debug(f"Generated schema for function '{func_name}'")
        return processed_schema
    except Exception as schema_error:
        logger.warning(f"Failed to generate schema for '{func_name}': {schema_error}")
        return None


def wrap_tool_function(
    mcp_instance: Any,
    func: Callable[..., Any],
    func_name: str,
    file_path: pathlib.Path,
    docstring: str,
    tool_call_cache: Optional[SessionToolCallCache] = None,
) -> bool:
    """
    Wraps a function as an MCP tool with optional schema and caching.

    Args:
        mcp_instance: The FastMCP instance to add the tool to
        func: The function to wrap
        func_name: The name of the function
        file_path: The path to the file containing the function
        docstring: The function's docstring to use as description
        schema: Optional JSON schema for the function parameters
        tool_call_cache: Optional cache for tool call results

    Returns:
        True if wrapping was successful, False otherwise
    """
    try:
        # Handle callable classes
        original_func = func
        if not inspect.isroutine(func):
            logger.info(
                f"Detected callable class for '{func_name}', extracting __call__ method"
            )
            # Use proper type checking for callable objects
            if hasattr(func, "__call__"):
                func = func.__call__

        # Apply tool call caching if provided
        target_func = original_func if original_func != func else func
        if tool_call_cache is not None:
            target_func = tool_call_cache.create_cached_tool(target_func)

        mcp_instance.tool(name=func_name, description=docstring)(target_func)

        logger.info(
            f"Successfully wrapped function '{func_name}' from '{file_path}' as an MCP tool."
        )

        return True
    except Exception as e:
        logger.error(
            f"Failed to wrap function '{func_name}' from '{file_path}' as an MCP tool: {e}",
            exc_info=True,
        )
        return False


def validate_and_wrap_tool(
    mcp_instance: Any,  # Use Any instead of FastMCP to avoid type errors
    func: Callable[..., Any],
    func_name: str,
    file_path: pathlib.Path,
    tool_call_cache: Optional[SessionToolCallCache] = None,
) -> bool:
    """
    Validates function signature and docstring, then wraps it as an MCP tool.
    Logs warnings for missing type hints or docstrings.

    Args:
        mcp_instance: The FastMCP instance to add the tool to.
        func: The function to wrap as a tool.
        func_name: The name of the function.
        file_path: The path to the file containing the function.
        tool_call_cache: Optional cache for tool call results.

    Returns:
        True if validation and wrapping were successful, False otherwise
    """
    # Step 1: Validate the function
    docstring = validate_tool_meta(func, func_name, file_path)

    # Step 2: Generate schema for the function
    # schema = generate_tool_schema(func, func_name)

    # Step 3: Wrap the function as a tool (even if validation found issues)
    return wrap_tool_function(
        mcp_instance=mcp_instance,
        func=func,
        func_name=func_name,
        file_path=file_path,
        docstring=docstring,
        tool_call_cache=tool_call_cache,
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
