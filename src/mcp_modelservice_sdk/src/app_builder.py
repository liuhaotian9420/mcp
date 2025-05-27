"""
Module for building the MCP Starlette application with multi-mount architecture.
Each Python file will be mounted as a separate FastMCP instance under a route
derived from its directory structure.
"""
from pydantic import AnyUrl
import pydantic
from .discovery import discover_py_files, discover_functions, _load_module_from_path  # Added _load_module_from_path import

import inspect
import logging
import os
import pathlib
import re
import sys
import threading
import functools
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING, Union
from contextlib import asynccontextmanager, AsyncExitStack
from fastmcp.server.http import create_streamable_http_app 
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Mock FastMCP class for testing when the library is not installed
class MockFastMCP:
    """Mock FastMCP class for use when real FastMCP is not available."""
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "MockFastMCP")
        self.instructions = kwargs.get("instructions", None)
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

# Thread-local storage for session context
_session_context = threading.local()


class SessionMiddleware:
    """
    Middleware to extract MCP session ID from request headers and store it in thread-local storage.
    This enables tools to access the current session ID during request processing.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract headers from the ASGI scope
            headers = dict(scope.get("headers", []))
            
            # Look for the mcp-session-id header (headers are byte strings in ASGI)
            session_id = None
            for name, value in headers.items():
                if name == b"mcp-session-id":
                    session_id = value.decode("utf-8")
                    break
            
            if session_id:
                # Set the session ID in thread-local storage
                set_current_session_id(session_id)
                logger.debug(f"SessionMiddleware: Set session ID {session_id} for request")
            else:
                logger.debug("SessionMiddleware: No mcp-session-id header found in request")
            
            try:
                # Process the request
                await self.app(scope, receive, send)
            finally:
                # Clean up thread-local storage after request processing
                if hasattr(_session_context, 'session_id'):
                    delattr(_session_context, 'session_id')
                    logger.debug("SessionMiddleware: Cleaned up session ID from thread-local storage")
        else:
            # For non-HTTP requests (like WebSocket), just pass through
            await self.app(scope, receive, send)


def get_current_session_id() -> Optional[str]:
    """
    Get the current session ID from thread-local storage.
    
    Returns:
        The session ID if available, None otherwise.
    """
    session_id = getattr(_session_context, 'session_id', None)
    if session_id:
        logger.debug(f"Retrieved session ID from thread-local storage: {session_id}")
    else:
        logger.debug("No session ID found in thread-local storage")
    return session_id


def set_current_session_id(session_id: str) -> None:
    """
    Set the current session ID in thread-local storage.
    
    Args:
        session_id: The session ID to store.
    """
    logger.debug(f"Setting session ID in thread-local storage: {session_id}")
    _session_context.session_id = session_id


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
    tool_call_cache: Optional['SessionToolCallCache'] = None,
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


class SessionToolCallCache:
    """
    Simple in-memory cache for tool call results per session.
    Used in stateful + JSON response mode to cache tool call results.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}  # session_id -> {tool_call_key -> result}
        logger.info("Initialized SessionToolCallCache for stateful JSON response mode")
    
    def get_cache_key(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Generate a cache key from tool name and arguments."""
        import json
        import hashlib
        
        # Create a deterministic key from tool name and sorted args
        args_str = json.dumps(tool_args, sort_keys=True, default=str)
        key_data = f"{tool_name}:{args_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, session_id: str, tool_name: str, tool_args: Dict[str, Any]) -> Optional[Any]:
        """Get cached result for a tool call in a specific session."""
        if session_id not in self._cache:
            return None
        
        cache_key = self.get_cache_key(tool_name, tool_args)
        result = self._cache[session_id].get(cache_key)
        
        if result is not None:
            logger.info(f"Cache hit for session {session_id}, tool {tool_name}")
        
        return result
    
    def set(self, session_id: str, tool_name: str, tool_args: Dict[str, Any], result: Any) -> None:
        """Cache a tool call result for a specific session."""
        if session_id not in self._cache:
            self._cache[session_id] = {}
        
        cache_key = self.get_cache_key(tool_name, tool_args)
        self._cache[session_id][cache_key] = result
        
        logger.info(f"Cached result for session {session_id}, tool {tool_name}")
    
    def clear_session(self, session_id: str) -> None:
        """Clear all cached results for a specific session."""
        if session_id in self._cache:
            del self._cache[session_id]
            logger.debug(f"Cleared cache for session {session_id}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        total_sessions = len(self._cache)
        total_entries = sum(len(session_cache) for session_cache in self._cache.values())
        return {
            "total_sessions": total_sessions,
            "total_cached_entries": total_entries
        }
    
    def create_cached_tool(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Create a cached version of a tool function."""
        @functools.wraps(func)
        def cached_wrapper(*args, **kwargs):
            # Get current session ID
            session_id = get_current_session_id()
            
            if session_id is None:
                # No session context, execute function directly
                logger.info(f"No session context for {func.__name__}, executing directly")
                return func(*args, **kwargs)
            
            # Check cache first
            cached_result = self.get(session_id, func.__name__, kwargs)
            if cached_result is not None:
                logger.info(f"Cache hit for {func.__name__} in session {session_id}")
                return cached_result
            
            # Execute function and cache result
            logger.info(f"Cache miss for {func.__name__} in session {session_id}, executing function")
            result = func(*args, **kwargs)
            
            # Cache the result
            self.set(session_id, func.__name__, kwargs, result)
            logger.info(f"Cached result for {func.__name__} in session {session_id}")
            
            return result
        
        return cached_wrapper


def _get_module_docstring(file_path: pathlib.Path) -> Optional[str]:
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



def create_mcp_instances(
    functions_by_file: Dict[pathlib.Path, List[Tuple[Callable[..., Any], str]]],
    base_dir: pathlib.Path,
    mcp_server_name: str,
    tool_call_cache: Optional[SessionToolCallCache] = None
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

        # Extract the module docstring to use as instructions
        instructions = _get_module_docstring(file_path)
        if instructions:
            logger.info(f"Using module docstring as instructions for FastMCP instance '{instance_name}'")
        else:
            logger.info(f"No module docstring found for '{instance_name}', using default instructions")
            # Default instructions based on the file path
            instructions = f"MCP server for {relative_path} functionality"

        logger.info(f"Creating FastMCP instance '{instance_name}' for {file_path}")
        file_mcp: FastMCPType = FastMCP(name=instance_name, instructions=instructions)

        # Register all functions from this file as tools
        tools_registered = 0
        for func, func_name in funcs:
            logger.info(f"Processing function '{func_name}' from {file_path}...")
            try:
                _validate_and_wrap_tool(file_mcp, func, func_name, file_path, tool_call_cache)
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
    mode: Optional[str] = "composed",
    enable_event_store: bool = False,
    event_store_path: Optional[str] = None,
    stateless_http: bool = False,
    json_response: bool = False
) -> Starlette:
    """
    Creates a Starlette application with multiple FastMCP instances based on directory structure.
    Each Python file will be given its own FastMCP instance mounted at a path derived from its location.
    Module docstrings from each file will be used as instructions for the corresponding FastMCP instance.
    
    There are two modes of operation:
    1. "composed" - Uses FastMCP's server composition feature for cleaner mounting.
    2. "routed" - Mount each file to a different route
    
    Args:
        source_path_str: Path to the Python file or directory containing functions.
        target_function_names: Optional list of function names to expose. If None, all are exposed.
        mcp_server_name: Base name for FastMCP servers (will be suffixed with file/dir name).
        mcp_server_root_path: Root path prefix for all MCP services in Starlette.
        mcp_service_base_path: Base path for MCP protocol endpoints within each FastMCP app.
        cors_enabled: Whether to enable CORS middleware.
        cors_allow_origins: List of origins to allow for CORS. Defaults to ["*"] if None.
        mode: whether to give each FastMCP instance its own route or compose them all under a single route. Default is "composed".
        enable_event_store: If True, creates and uses a SQLite event store for tracking interactions.
                           Only applicable when json_response=False (SSE mode).
        event_store_path: Optional custom path for the SQLite database file. If None, defaults to a file
                         in the current working directory.
        stateless_http: If True, enables stateless HTTP mode where each request creates a fresh transport
                       with no session tracking. Default is stateful mode.
        json_response: If True, uses JSON response format instead of Server-Sent Events (SSE) streaming.
                      Default is SSE mode.
        
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
    
    # Validate configuration combinations
    if enable_event_store and json_response:
        raise TransformationError(
            "Event store can only be used with SSE mode (json_response=False). "
            "Please disable either event store or JSON response mode."
        )
    
    # Log transport configuration
    transport_mode = "stateless" if stateless_http else "stateful"
    response_format = "JSON" if json_response else "SSE"
    logger.info(f"Transport mode: {transport_mode}, Response format: {response_format}")

    # Discover and group functions by file
    functions_by_file, base_dir = discover_and_group_functions(source_path_str, target_function_names)
        
    # Set up middleware stack
    middleware = []
    
    # Add session middleware first to extract session ID from headers
    middleware.append(Middleware(SessionMiddleware))
    
    # Add CORS middleware if enabled
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

    # Create an event store if enabled (only for stateful + SSE mode)
    event_store = None
    if enable_event_store and not json_response and not stateless_http:
        from .mcp_event_store import SQLiteEventStore
        try:
            event_store = SQLiteEventStore(event_store_path)
            logger.info(f"SQLite MCP event store initialized at: {event_store.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize MCP event store: {e}")
            logger.warning("Continuing without event store functionality")
    
    # Create a cache for stateful + JSON response mode
    tool_call_cache = None
    if not stateless_http and json_response:
        tool_call_cache = SessionToolCallCache()
        logger.info("Tool call cache initialized for stateful JSON response mode")
    
    # Create MCP instances for each file with its functions
    mcp_instances = create_mcp_instances(functions_by_file, base_dir, mcp_server_name, tool_call_cache)
    
    if not mcp_instances:
        logger.error("No FastMCP instances could be created with valid tools.")
        raise TransformationError(
            "No FastMCP instances could be created with valid tools. Check logs for details."
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
            # Create the main ASGI app with streamable HTTP transport
            from fastmcp.server.http import create_streamable_http_app
            main_asgi_app = create_streamable_http_app(
                server=main_mcp,  # type: ignore
                streamable_http_path=mcp_service_base_path,
                event_store=event_store,  # type: ignore (None if not enabled)
                json_response=json_response,
                stateless_http=stateless_http,
                middleware=middleware if middleware else None
            )
            
            # Log the transport configuration
            transport_info = []
            if stateless_http:
                transport_info.append("stateless")
            else:
                transport_info.append("stateful")
            
            if json_response:
                transport_info.append("JSON response")
            else:
                transport_info.append("SSE streaming")
            
            if event_store:
                transport_info.append("with SQLite event store")
            elif tool_call_cache:
                transport_info.append("with tool call cache")
            
            logger.info(f"Using streamable HTTP transport: {', '.join(transport_info)}")
            
            # Apply the root path by wrapping the ASGI app with a Starlette Mount
            routes = [Mount(mcp_server_root_path, app=main_asgi_app)]
            
            # Create app with properly typed parameters
            app = Starlette(
                debug=False,
                routes=routes,
                middleware=middleware if middleware else None,
                lifespan=main_asgi_app.router.lifespan_context
            )
            
            # Store the main FastMCP instance and related objects in the app state for reference
            app.state.fastmcp_instance = main_mcp  # type: ignore[attr-defined]
            if event_store:
                app.state.event_store = event_store  # type: ignore[attr-defined]
            if tool_call_cache:
                app.state.tool_call_cache = tool_call_cache  # type: ignore[attr-defined]
            
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
            # Create the file app with appropriate transport configuration
            from fastmcp.server.http import create_streamable_http_app
            file_app = create_streamable_http_app(
                server=file_mcp,  # type: ignore
                streamable_http_path=mcp_service_base_path,
                event_store=event_store,  # type: ignore (None if not enabled)
                json_response=json_response,
                stateless_http=stateless_http
            )
            logger.info(f"Created app for {file_path} with transport configuration")
                
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
            if event_store:
                app.state.event_store = event_store  # type: ignore[attr-defined]
            if tool_call_cache:
                app.state.tool_call_cache = tool_call_cache  # type: ignore[attr-defined]
            return app
        except Exception as e:
            logger.error(f"Error creating Starlette application: {e}")
            raise TransformationError(f"Failed to create Starlette application: {e}")
    else:
        raise TransformationError(f"Invalid mode: {mode}")

