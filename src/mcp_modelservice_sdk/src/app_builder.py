"""
Module for building the MCP Starlette application with multi-mount architecture.
Each Python file will be mounted as a separate FastMCP instance under a route
derived from its directory structure.
"""
from pydantic import AnyUrl
import pydantic
from .discovery import discover_py_files, discover_functions  # Relative import

import inspect
import logging
import os
import pathlib
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING, Union
from contextlib import asynccontextmanager, AsyncExitStack

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
        
    def mount(self, prefix, app, **kwargs):
        """Mock mount method."""
        return None

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
        Example: base_dir/subdir/module.py -> subdir/module
        Note: Does NOT include a leading slash to allow clean path joining later.
    """
    # Handle special case for __init__.py files
    if file_path.name == "__init__.py":
        # For __init__.py, use the parent directory name instead
        rel_path = file_path.parent.relative_to(base_dir)
        # Return empty string for root __init__.py to avoid extra slashes
        if str(rel_path) == '.':
            return ""
        return str(rel_path).replace(os.sep, '/')

    # Regular Python files
    rel_path = file_path.relative_to(base_dir)
    # Remove .py extension and convert path separators to route segments
    route_path = str(rel_path.with_suffix("")).replace(os.sep, "/")
    # Handle case where route_path is just "." (this happens for files directly in base_dir)
    if route_path == '.':
        return ""
    return route_path


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


def make_combined_lifespan(*subapps):
    """
    Returns an asynccontextmanager suitable for Starlette's `lifespan=…`
    that will run all of the given subapps' lifespans in sequence.
    """
    @asynccontextmanager
    async def lifespan(scope):
        async with AsyncExitStack() as stack:
            for sa in subapps:
                # each subapp has a .lifespan() async context manager
                await stack.enter_async_context(sa.router.lifespan_context(scope))
            yield
    return lifespan


# 1) Compile the "valid scheme" regex
_SCHEME_RE = re.compile(r'^[A-Za-z][A-Za-z0-9+.\-]*$')

def sanitize_prefix(raw: str, *, fallback: str = "x") -> str:
    """
    Turn `raw` into a valid URL scheme: must start with [A-Za-z],
    then contain only [A-Za-z0-9+.-].  If the result would be empty
    or start with a non-letter, we prepend `fallback` (default "x").
    """
    # 2) Drop any leading/trailing whitespace
    s = raw.strip()
    # 3) Replace invalid chars with hyphens (you could use '' instead)
    s = re.sub(r'[^A-Za-z0-9+.\-]', "-", s)
    # 4) Collapse multiple hyphens
    s = re.sub(r'-{2,}', "-", s)
    # 5) Trim hyphens/dots from ends (they're legal but ugly)
    s = s.strip("-.")
    # 6) If it doesn't start with a letter, prepend fallback
    if not s or not s[0].isalpha():
        s = fallback + s
    # 7) Final sanity-check: if it still doesn't match, fallback entirely
    if not _SCHEME_RE.match(s):
        return fallback
    return s

def _validate_resource_prefix(prefix: str) -> str:
    valid_resource = "resource://path/to/resource"
    test_case = f"{prefix}{valid_resource}"
    new_prefix = ''
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


def discover_and_group_functions(
    source_path_str: str,
    target_function_names: Optional[List[str]] = None
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
        
    return functions_by_file, base_dir


def create_mcp_instances(
    functions_by_file: Dict[pathlib.Path, List[Tuple[Callable[..., Any], str]]],
    base_dir: pathlib.Path,
    mcp_server_name: str
) -> Dict[pathlib.Path, Tuple[Any, str, int]]:
    """
    Creates FastMCP instances for each file and registers functions as tools.
    
    Args:
        functions_by_file: Dictionary mapping file paths to lists of (function, function_name) tuples
        base_dir: Base directory path for relative path calculations
        mcp_server_name: Base name for FastMCP servers
        
    Returns:
        Dictionary mapping file paths to tuples of (FastMCP instance, route path, tools count)
    """
    # Create the main FastMCP instance that will host all the mounted subservers
    logger.info(f"Created main FastMCP instance '{mcp_server_name}'")
    
    mcp_instances = {}
    
    # Create a FastMCP instance for each file and register its tools
    for file_path, funcs in functions_by_file.items():
        # Generate a unique name for this FastMCP instance based on file path
        relative_path = file_path.relative_to(base_dir)
        file_specific_name = str(relative_path).replace(os.sep, "_").replace(".py", "")
        instance_name = f"{file_specific_name}"

        logger.info(f"Creating FastMCP instance '{instance_name}' for {file_path}")
        file_mcp: FastMCPType = FastMCP(name=instance_name)

        # Register all functions from this file as tools
        tools_registered = 0
        for func, func_name in funcs:
            logger.info(f"Processing function '{func_name}' from {file_path}...")
            try:
                _validate_and_wrap_tool(file_mcp, func, func_name, file_path)
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
        route_path = _get_route_from_path(file_path, base_dir)
        route_path_verified = _validate_resource_prefix(f"{route_path}")
        
        # Store the instance, route path, and tools count
        mcp_instances[file_path] = (file_mcp, route_path_verified, tools_registered)
        
    return mcp_instances


def create_mcp_application(
    source_path_str: str,  # Will be normalized in the function
    target_function_names: Optional[List[str]] = None,
    mcp_server_name: str = "MCPModelService",
    mcp_server_root_path: str = "/mcp-server",
    mcp_service_base_path: str = "/mcp",
    # log_level: str = "info", # Logging setup will be handled by _setup_logging from core or a new utils module
    cors_enabled: bool = True,
    cors_allow_origins: Optional[List[str]] = None,
    mode: Optional[str] = "composed"
) -> Starlette:
    """
    Creates a Starlette application with multiple FastMCP instances based on directory structure.
    Each Python file will be given its own FastMCP instance mounted at a path derived from its location.
    Uses FastMCP's server composition feature for cleaner mounting.

    Args:
        source_path_str: Path to the Python file or directory containing functions.
        target_function_names: Optional list of function names to expose. If None, all are exposed.
        mcp_server_name: Base name for FastMCP servers (will be suffixed with file/dir name).
        mcp_server_root_path: Root path prefix for all MCP services in Starlette.
        mcp_service_base_path: Base path for MCP protocol endpoints within each FastMCP app.
        cors_enabled: Whether to enable CORS middleware.
        cors_allow_origins: List of origins to allow for CORS. Defaults to ["*"] if None.
        mode: whether to give each FastMCP instance its own route or compose them all under a single route. Default is "composed".
    Returns:
        A configured Starlette application with multiple mounted FastMCP instances.

    Raises:
        TransformationError: If no tools could be created or other critical errors occur.
    """
    logger.info(
        f"Initializing multi-mount MCP application with base name {mcp_server_name} using server composition..."
    )
    logger.info(f"Source path for tools: {source_path_str}")
    if target_function_names:
        logger.info(f"Target functions: {target_function_names}")

    # Discover and group functions by file
    functions_by_file, base_dir = discover_and_group_functions(source_path_str, target_function_names)
    
    # Create MCP instances for each file with its functions
    mcp_instances = create_mcp_instances(functions_by_file, base_dir, mcp_server_name)
    
    if not mcp_instances:
        logger.error("No FastMCP instances could be created with valid tools.")
        raise TransformationError(
            "No FastMCP instances could be created with valid tools. Check logs for details."
        )
        
    # Set up CORS middleware if enabled
    middleware = []
    if cors_enabled:
        effective_cors_origins = cors_allow_origins if cors_allow_origins is not None else ["*"]
        middleware.append(
            Middleware(
                CORSMiddleware,
                allow_origins=effective_cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        )

    if mode is None:
        raise TransformationError("Mode must be specified as 'composed' or 'routes'.")
    elif mode == "composed":
        # Create the main FastMCP instance that will host all the mounted subservers
        main_mcp: FastMCPType = FastMCP(name=mcp_server_name)
        logger.info(f"Created main FastMCP instance '{mcp_server_name}'")
        
        # Track if we actually mounted any subservers with tools
        MOUNTED_ANY_SERVERS = False
        
        # Mount each file's FastMCP instance to the main instance
        for file_path, (file_mcp, route_path, tools_registered) in mcp_instances.items():
            try:
                # Use direct mounting by default for better performance
                logger.info(f"==============Mounting {file_path} to {route_path}=======================")
                # Use custom separators for resources to avoid invalid URIs
                main_mcp.mount(
                    route_path, 
                    file_mcp, 
                    as_proxy=False,
                    resource_separator="+", # Use + for resource separation
                    tool_separator="_",     # Use underscore for tool name separation
                    prompt_separator="."    # Use dot for prompt name separation
                )
                logger.info(
                    f"Successfully mounted FastMCP instance '{file_mcp.name}' with {tools_registered} tools at prefix '{route_path}'"
                )
                MOUNTED_ANY_SERVERS = True
            except Exception as e:
                logger.error(f"Failed to mount FastMCP instance '{file_mcp.name}': {e}")
                continue

        if not MOUNTED_ANY_SERVERS:
            logger.error("No FastMCP instances could be mounted with valid tools.")
            raise TransformationError(
                "No FastMCP instances could be mounted with valid tools. Check logs for details."
            )

        # Create the final ASGI app from the main FastMCP instance with all subservers mounted
        try:
            # Create the main ASGI app with the basic path parameter
            main_asgi_app = main_mcp.http_app(path=mcp_service_base_path)
            
            # Log that we're using the default transport due to compatibility issues
            logger.info("Using default transport for FastMCP HTTP app.")
            
            # Apply the root path by wrapping the ASGI app with a Starlette Mount
            routes = [Mount(mcp_server_root_path, app=main_asgi_app)]
            # Create app with properly typed parameters
            app = Starlette(
            debug=False,
            routes=routes,
            middleware=middleware if middleware else None,
            lifespan=main_asgi_app.router.lifespan_context
        )
            
            # Store the main FastMCP instance in the app state for reference
            app.state.fastmcp_instance = main_mcp  # type: ignore[attr-defined]
            
            logger.info(
                f"Successfully created Starlette application with FastMCP server composition at '{mcp_server_root_path}'."
            )
            return app
            
        except Exception as e:
            logger.error(f"Error creating final ASGI app: {e}")
            raise TransformationError(f"Failed to create final ASGI app: {e}")

    elif mode == "routed":
        # Create a Starlette app with each FastMCP instance mounted at its own route
        routes = []
        apps = []
        for file_path, (file_mcp, route_path, tools_registered) in mcp_instances.items():
            file_app = file_mcp.http_app()
            logger.info(f"Mounting {file_path} to {route_path}")
            routes.append(Mount('/'+route_path, app=file_app))
            apps.append(file_app)
        try:    
            app = Starlette(
                debug=False,  # Explicitly set parameter
                routes=routes,
                middleware=middleware if middleware else None,
                lifespan=make_combined_lifespan(*apps)
            )
            app.state.mcp_instances = mcp_instances
            return app
        except Exception as e:
            logger.error(f"Error creating Starlette application: {e}")
            raise TransformationError(f"Failed to create Starlette application: {e}")
    else:
        raise TransformationError(f"Invalid mode: {mode}")

