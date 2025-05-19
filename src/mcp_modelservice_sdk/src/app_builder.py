"""
Module for building the MCP Starlette application.
"""
import inspect
import logging
import pathlib
from typing import Any, Callable, List, Optional, Tuple, Dict # Added Dict

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "FastMCP is not installed. Please install it to use this SDK. "
        "You can typically install it using: pip install fastmcp"
    )

from .discovery import discover_py_files, discover_functions # Relative import

logger = logging.getLogger(__name__)

class TransformationError(Exception):
    """Custom exception for errors during the transformation process."""
    pass

def _validate_and_wrap_tool(
    mcp_instance: FastMCP, func: Callable[..., Any], func_name: str, file_path: pathlib.Path
):
    """
    Validates function signature and docstring, then wraps it as an MCP tool.
    Logs warnings for missing type hints or docstrings.
    """
    if not inspect.getdoc(func):
        logger.warning(
            f"Function '{func_name}' in '{file_path}' is missing a docstring."
        )
    else:
        docstring = inspect.getdoc(func) or ""
        sig = inspect.signature(func)
        missing_param_docs = []
        for p_name in sig.parameters:
            if not (f":param {p_name}:" in docstring or f"Args:\n    {p_name} (" in docstring or f"{p_name} (" in docstring):
                 missing_param_docs.append(p_name)
        if missing_param_docs:
             logger.warning(
                f"Docstring for function '{func_name}' in '{file_path}' may be missing descriptions for parameters: {', '.join(missing_param_docs)}."
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
        mcp_instance.tool(name=func_name)(func)
        logger.info(f"Successfully wrapped function '{func_name}' from '{file_path}' as an MCP tool.")
    except Exception as e:
        logger.error(f"Failed to wrap function '{func_name}' from '{file_path}' as an MCP tool: {e}", exc_info=True)

def create_mcp_application(
    source_path_str: str,
    target_function_names: Optional[List[str]] = None,
    mcp_server_name: str = "MCPModelService",
    mcp_server_root_path: str = "/mcp-server",
    mcp_service_base_path: str = "/mcp",
    # log_level: str = "info", # Logging setup will be handled by _setup_logging from core or a new utils module
    cors_enabled: bool = True,
    cors_allow_origins: Optional[List[str]] = None,
) -> Starlette:
    """
    Creates a Starlette application with FastMCP tools generated from discovered functions.

    Args:
        source_path_str: Path to the Python file or directory containing functions.
        target_function_names: Optional list of function names to expose. If None, all are exposed.
        mcp_server_name: Name for the FastMCP server.
        mcp_server_root_path: Root path for mounting the MCP service in Starlette.
        mcp_service_base_path: Base path for MCP protocol endpoints within the FastMCP app.
        cors_enabled: Whether to enable CORS middleware.
        cors_allow_origins: List of origins to allow for CORS. Defaults to ["*"] if None.

    Returns:
        A configured Starlette application.
        
    Raises:
        TransformationError: If no tools could be created or other critical errors occur.
    """
    # _setup_logging(log_level) # This will be called externally if needed

    logger.info(f"Initializing {mcp_server_name}...")
    logger.info(f"Source path for tools: {source_path_str}")
    if target_function_names:
        logger.info(f"Target functions: {target_function_names}")

    mcp_instance = FastMCP(name=mcp_server_name)

    try:
        py_files = discover_py_files(source_path_str)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Error discovering Python files: {e}")
        raise TransformationError(f"Failed to discover Python files: {e}")

    if not py_files:
        logger.error("No Python files found to process. Cannot create any MCP tools.")
        raise TransformationError("No Python files found to process. Ensure the path is correct and contains Python files.")

    functions_to_wrap = discover_functions(py_files, target_function_names)

    if not functions_to_wrap:
        message = "No functions found to wrap as MCP tools."
        if target_function_names:
            message += f" (Specified functions: {target_function_names} not found, or no functions in source matching criteria)."
        else:
            message += " (No functions discovered in the source path matching criteria)."
        logger.error(message)
        raise TransformationError(message)
    
    for func, func_name, file_path in functions_to_wrap:
        logger.info(f"Processing function '{func_name}' from {file_path}...")
        _validate_and_wrap_tool(mcp_instance, func, func_name, file_path)

    if not mcp_instance.tools: # type: ignore[attr-defined]
        logger.error("No tools were successfully created and registered with FastMCP instance.")
        raise TransformationError("No tools were successfully created and registered. Check logs for function-specific errors.")
    logger.info(f"Successfully created and registered {len(mcp_instance.tools)} MCP tool(s).") # type: ignore[attr-defined]

    mcp_asgi_app = mcp_instance.http_app(path=mcp_service_base_path)
    
    current_middleware = []
    if cors_enabled:
        effective_cors_origins = cors_allow_origins if cors_allow_origins is not None else ["*"]
        current_middleware.append(
            Middleware(
                CORSMiddleware,
                allow_origins=effective_cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        )

    app_lifespan = None
    if hasattr(mcp_asgi_app, 'router') and hasattr(mcp_asgi_app.router, 'lifespan_context'):
        app_lifespan = mcp_asgi_app.router.lifespan_context
    elif hasattr(mcp_asgi_app, 'lifespan'):
        app_lifespan = mcp_asgi_app.lifespan # type: ignore[attr-defined]
    else:
        logger.warning("Could not determine lifespan context for FastMCP ASGI app. Lifespan features may not work correctly.")

    class AppState:
        fastmcp_instance: FastMCP

    state = AppState()
    state.fastmcp_instance = mcp_instance # type: ignore

    app = Starlette(
        routes=[
            Mount(mcp_server_root_path, app=mcp_asgi_app),
        ],
        lifespan=app_lifespan, 
        middleware=current_middleware if current_middleware else None,
    )
    app.state = state # type: ignore[attr-defined]

    logger.info(
        f"Starlette application created. MCP service '{mcp_server_name}' "
        f"will be mounted at '{mcp_server_root_path}{mcp_service_base_path}'."
    )
    return app 