"""
Module for building the MCP Starlette application with multi-mount architecture.
Each Python file will be mounted as a separate FastMCP instance under a route
derived from its directory structure.
"""
from .discovery import discover_py_files, discover_functions  # Relative import

import inspect
import logging
import os
import pathlib
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING, Union

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Mock FastMCP class for testing when the library is not installed
class MockFastMCP:
    """Mock FastMCP class for use when real FastMCP is not available."""
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "MockFastMCP")
        self.tools = {}
    
    def tool(self, name=None):
        """Mock decorator that simply returns the function unchanged."""
        def decorator(func):
            self.tools[name or func.__name__] = func
            return func
        return decorator
    
    def http_app(self, path=None):
        """Return a mock app."""
        return Starlette()

# For type checking, always create a FastMCP type
if TYPE_CHECKING:
    # Only imported for type checking
    from fastmcp import FastMCP as RealFastMCP
    FastMCPType = Union[RealFastMCP, MockFastMCP]
else:
    FastMCPType = Any

# Try to import FastMCP, use MockFastMCP if not available
try:
    from fastmcp import FastMCP
except ImportError:
    # Only for testing purposes - real code needs fastmcp installed
    FastMCP = MockFastMCP  # type: ignore
    # Raise this error for actual runtime usage but not during test imports
    if "unittest" not in sys.modules and "pytest" not in sys.modules:
        raise ImportError(
            "FastMCP is not installed. Please install it to use this SDK. "
            "You can typically install it using: pip install fastmcp"
        )


logger = logging.getLogger(__name__)


class TransformationError(Exception):
    """Custom exception for errors during the transformation process."""

    pass


def _get_route_from_path(file_path: pathlib.Path, base_dir: pathlib.Path) -> str:
    """
    Converts a file path to a route path based on its directory structure.

    Args:
        file_path: Path to the Python file.
        base_dir: Base directory where all source files are located.

    Returns:
        A route path for the FastMCP instance derived from the file path.
        Example: base_dir/subdir/module.py -> /subdir/module
    """
    # Handle special case for __init__.py files
    if file_path.name == "__init__.py":
        # For __init__.py, use the parent directory name instead
        rel_path = file_path.parent.relative_to(base_dir)
        return f"/{'/' if str(rel_path) != '.' else ''}{str(rel_path).replace(os.sep, '/')}"

    # Regular Python files
    rel_path = file_path.relative_to(base_dir)
    # Remove .py extension and convert path separators to route segments
    route_path = str(rel_path.with_suffix("")).replace(os.sep, "/")
    return f"/{'/' if route_path != '.' else ''}{route_path}"


def _validate_and_wrap_tool(
    mcp_instance: Any,  # Use Any instead of FastMCP to avoid type errors
    func: Callable[..., Any],
    func_name: str,
    file_path: pathlib.Path,
):
    """
    Validates function signature and docstring, then wraps it as an MCP tool.
    Logs warnings for missing type hints or docstrings.

    Args:
        mcp_instance: The FastMCP instance to add the tool to.
        func: The function to wrap as a tool.
        func_name: The name of the function.
        file_path: The path to the file containing the function.
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
        mcp_instance.tool(name=func_name)(func)
        logger.info(
            f"Successfully wrapped function '{func_name}' from '{file_path}' as an MCP tool."
        )
    except Exception as e:
        logger.error(
            f"Failed to wrap function '{func_name}' from '{file_path}' as an MCP tool: {e}",
            exc_info=True,
        )


# Import the normalize path function from core
try:
    from .core import _normalize_path
except ImportError:
    # Define it here if import fails
    def _normalize_path(path_str):
        """Normalize a path string to handle both relative and absolute paths."""
        import os
        import pathlib

        path_obj = pathlib.Path(path_str)

        # If it's already absolute, return it
        if path_obj.is_absolute():
            return str(path_obj)

        # Otherwise, make it absolute relative to the current working directory
        return str(pathlib.Path(os.getcwd()) / path_obj)


def create_mcp_application(
    source_path_str: str,  # Will be normalized in the function
    target_function_names: Optional[List[str]] = None,
    mcp_server_name: str = "MCPModelService",
    mcp_server_root_path: str = "/mcp-server",
    mcp_service_base_path: str = "/mcp",
    # log_level: str = "info", # Logging setup will be handled by _setup_logging from core or a new utils module
    cors_enabled: bool = True,
    cors_allow_origins: Optional[List[str]] = None,
) -> Starlette:
    """
    Creates a Starlette application with multiple FastMCP instances based on directory structure.
    Each Python file will be given its own FastMCP instance mounted at a path derived from its location.

    Args:
        source_path_str: Path to the Python file or directory containing functions.
        target_function_names: Optional list of function names to expose. If None, all are exposed.
        mcp_server_name: Base name for FastMCP servers (will be suffixed with file/dir name).
        mcp_server_root_path: Root path prefix for all MCP services in Starlette.
        mcp_service_base_path: Base path for MCP protocol endpoints within each FastMCP app.
        cors_enabled: Whether to enable CORS middleware.
        cors_allow_origins: List of origins to allow for CORS. Defaults to ["*"] if None.

    Returns:
        A configured Starlette application with multiple mounted FastMCP instances.

    Raises:
        TransformationError: If no tools could be created or other critical errors occur.
    """
    # _setup_logging(log_level) # This will be called externally if needed

    logger.info(
        f"Initializing multi-mount MCP application with base name {mcp_server_name}..."
    )
    logger.info(f"Source path for tools: {source_path_str}")
    if target_function_names:
        logger.info(f"Target functions: {target_function_names}")

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
    normalized_path = _normalize_path(source_path_str)
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

    # Store FastMCP instances and their route paths
    mcp_instances: Dict[str, Tuple[Any, pathlib.Path]] = {}  # Use Any for FastMCP

    # Create a FastMCP instance for each file and register its tools
    for file_path, funcs in functions_by_file.items():
        # Generate a unique name for this FastMCP instance based on file path
        relative_path = file_path.relative_to(base_dir)
        file_specific_name = str(relative_path).replace(os.sep, "_").replace(".py", "")
        instance_name = f"{mcp_server_name}_{file_specific_name}"

        logger.info(f"Creating FastMCP instance '{instance_name}' for {file_path}")
        mcp_instance: Any = FastMCP(name=instance_name)  # Use Any for FastMCP

        # Register all functions from this file as tools
        for func, func_name in funcs:
            logger.info(f"Processing function '{func_name}' from {file_path}...")
            _validate_and_wrap_tool(mcp_instance, func, func_name, file_path)

        # Only keep instances that have at least one tool
        # Check if any tools were registered (implementation depends on FastMCP API)
        has_tools = (hasattr(mcp_instance, "_tools") and bool(
            getattr(mcp_instance, "_tools", None)
        )) or (hasattr(mcp_instance, "tools") and bool(
            getattr(mcp_instance, "tools", None)
        ))
        if not has_tools:
            logger.warning(
                f"No tools were successfully created and registered for {file_path}. Skipping."
            )
            continue

        # Determine the route path for this FastMCP instance
        route_path = _get_route_from_path(file_path, base_dir)

        # Get number of tools registered (implementation depends on FastMCP API)
        num_tools = 0
        if hasattr(mcp_instance, "_tools"):
            num_tools = len(getattr(mcp_instance, "_tools", []))
        elif hasattr(mcp_instance, "tools"):
            num_tools = len(getattr(mcp_instance, "tools", []))
        logger.info(
            f"Successfully created and registered {num_tools} MCP tool(s) for '{instance_name}' to be mounted at '{route_path}'"
        )

        # Store the instance with its route path
        mcp_instances[route_path] = (mcp_instance, file_path)

    if not mcp_instances:
        logger.error("No FastMCP instances could be created with valid tools.")
        raise TransformationError(
            "No FastMCP instances could be created with valid tools. Check logs for details."
        )

    # Set up CORS middleware if enabled
    current_middleware = []
    if cors_enabled:
        effective_cors_origins = (
            cors_allow_origins if cors_allow_origins is not None else ["*"]
        )
        current_middleware.append(
            Middleware(
                CORSMiddleware,
                allow_origins=effective_cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        )

    # Create mount routes for each FastMCP instance
    routes = []
    for route_path, (mcp_instance, file_path) in mcp_instances.items():
        # Create ASGI app from the FastMCP instance
        mcp_asgi_app = mcp_instance.http_app(path=mcp_service_base_path)

        # Full mount path combines the server root path with the route path derived from file location
        # Ensure we don't have double slashes by handling the paths carefully
        if mcp_server_root_path.endswith("/") and route_path.startswith("/"):
            full_mount_path = f"{mcp_server_root_path[:-1]}{route_path}"
        elif not (mcp_server_root_path.endswith("/") or route_path.startswith("/")):
            full_mount_path = f"{mcp_server_root_path}/{route_path}"
        else:
            full_mount_path = f"{mcp_server_root_path}{route_path}"

        logger.info(
            f"Mounting FastMCP instance for {file_path} at '{full_mount_path}'."
        )
        routes.append(Mount(full_mount_path, app=mcp_asgi_app))

    # Handle lifespans - use the first MCP instance's lifespan for simplicity
    # A more advanced implementation could combine lifespans
    app_lifespan = None
    if routes:
        example_asgi_app = routes[0].app  # First FastMCP ASGI app for lifespan
        if hasattr(example_asgi_app, "router") and hasattr(
            example_asgi_app.router, "lifespan_context"
        ):
            app_lifespan = example_asgi_app.router.lifespan_context
        elif hasattr(example_asgi_app, "lifespan"):
            app_lifespan = example_asgi_app.lifespan  # type: ignore[attr-defined]
        else:
            logger.warning(
                "Could not determine lifespan context for FastMCP ASGI apps. Lifespan features may not work correctly."
            )

    # Create state for storing all FastMCP instances
    class AppState:
        fastmcp_instances: Dict[str, Any]  # Use Any for FastMCP

    state = AppState()
    state.fastmcp_instances = {
        route: instance for route, (instance, _) in mcp_instances.items()
    }

    # Create the Starlette application with all the mounts
    app = Starlette(
        routes=routes,
        lifespan=app_lifespan,
        middleware=current_middleware if current_middleware else None,
    )
    app.state = state  # type: ignore[assignment]

    logger.info(
        f"Starlette application created with {len(routes)} FastMCP instances mounted under '{mcp_server_root_path}'."
    )
    return app
