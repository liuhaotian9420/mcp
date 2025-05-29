"""
Factory for creating complete MCP applications with multiple FastMCP instances.
"""

import logging
from typing import List, Optional, Any, cast
from contextlib import asynccontextmanager, AsyncExitStack
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from ..utils import TransformationError
from .mocking import get_fastmcp_class, FastMCPType
from .middleware import SessionMiddleware
from .caching import SessionToolCallCache
from .instance_factory import discover_and_group_functions, create_mcp_instances

logger = logging.getLogger(__name__)


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


def create_mcp_application(
    source_path_str: str,
    target_function_names: Optional[List[str]] = None,
    mcp_server_name: str = "MCPY-CLI",
    mcp_server_root_path: str = "/mcp-server",
    mcp_service_base_path: str = "/mcp",
    cors_enabled: bool = True,
    cors_allow_origins: Optional[List[str]] = None,
    mode: Optional[str] = "composed",
    enable_event_store: bool = False,
    event_store_path: Optional[str] = None,
    stateless_http: bool = False,
    json_response: bool = False,
    legacy_sse: bool = False,
) -> Starlette:
    """
    Creates a Starlette application with multiple FastMCP instances.
    """
    logger.info(
        f"Initializing multi-mount MCP application with base name {mcp_server_name}"
    )

    # Validate configuration combinations
    if enable_event_store and json_response:
        raise TransformationError(
            "Event store can only be used with SSE mode (json_response=False)."
        )

    # Validate legacy SSE mode compatibility
    if legacy_sse:
        if json_response:
            raise TransformationError(
                "Legacy SSE mode is incompatible with JSON response mode. Please disable --json-response when using --legacy-sse."
            )
        if stateless_http:
            raise TransformationError(
                "Legacy SSE mode is incompatible with stateless HTTP mode. Please disable --stateless-http when using --legacy-sse."
            )

    # Discover and group functions by file
    functions_by_file, base_dir = discover_and_group_functions(
        source_path_str, target_function_names
    )

    # Set up middleware stack
    middleware = []
    middleware.append(Middleware(SessionMiddleware))

    if cors_enabled:
        effective_cors_origins = (
            cors_allow_origins if cors_allow_origins is not None else ["*"]
        )
        middleware.append(
            Middleware(
                CORSMiddleware,
                allow_origins=effective_cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        )

    # Create event store and cache as needed
    event_store = None
    tool_call_cache = None

    if enable_event_store and not json_response and not stateless_http:
        from ..mcp_event_store import SQLiteEventStore

        try:
            event_store = SQLiteEventStore(event_store_path)
            logger.info(f"SQLite MCP event store initialized at: {event_store.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize MCP event store: {e}")

    if not stateless_http and json_response:
        tool_call_cache = SessionToolCallCache()
        logger.info("Tool call cache initialized for stateful JSON response mode")

    # Create MCP instances
    mcp_instances = create_mcp_instances(
        functions_by_file, base_dir, mcp_server_name, tool_call_cache
    )

    if not mcp_instances:
        raise TransformationError(
            "No FastMCP instances could be created with valid tools."
        )
    starlette_app: Starlette = Starlette()
    if mode == "composed":
        starlette_app = _create_composed_application(
            mcp_instances,
            mcp_server_name,
            mcp_server_root_path,
            mcp_service_base_path,
            middleware,
            event_store,
            json_response,
            stateless_http,
            tool_call_cache,
            legacy_sse,
        )
        return starlette_app
    elif mode == "routed":
        starlette_app = _create_routed_application(
            mcp_instances,
            mcp_service_base_path,
            middleware,
            event_store,
            json_response,
            stateless_http,
            tool_call_cache,
            legacy_sse,
        )
        return starlette_app
    else:
        raise TransformationError(f"Invalid mode: {mode}")


def _create_composed_application(
    mcp_instances,
    mcp_server_name,
    mcp_server_root_path,
    mcp_service_base_path,
    middleware,
    event_store,
    json_response,
    stateless_http,
    tool_call_cache,
    legacy_sse,
):
    """Create a composed application."""
    FastMCP = get_fastmcp_class()
    main_mcp: FastMCPType = FastMCP(name=mcp_server_name)

    # Mount each file's FastMCP instance
    for file_path, (file_mcp, route_path, tools_registered) in mcp_instances.items():
        try:
            main_mcp.mount(
                route_path,
                file_mcp,
                as_proxy=False,
                resource_separator="+",
                tool_separator="_",
                prompt_separator=".",
            )
            logger.info(f"Mounted FastMCP instance '{file_mcp.name}' at '{route_path}'")
        except Exception as e:
            logger.error(f"Failed to mount FastMCP instance '{file_mcp.name}': {e}")

    # Create the ASGI app
    if legacy_sse:
        # Use legacy SSE transport via FastMCP's http_app method
        main_asgi_app = main_mcp.http_app(
            transport="sse",
            path=mcp_service_base_path
        )
        logger.info("Using legacy SSE transport via FastMCP.http_app")
    else:
        # Use modern streamable HTTP transport
        from fastmcp.server.http import create_streamable_http_app

        # Cast to Any to avoid type issues with MockFastMCP vs FastMCP
        main_asgi_app = create_streamable_http_app(
            server=cast(Any, main_mcp),
            streamable_http_path=mcp_service_base_path,
            event_store=event_store,
            json_response=json_response,
            stateless_http=stateless_http,
            middleware=middleware if middleware else None,
        )

    routes = [Mount(mcp_server_root_path, app=main_asgi_app)]
    app = Starlette(
        debug=False,
        routes=routes,
        middleware=middleware if middleware else None,
        lifespan=main_asgi_app.router.lifespan_context,
    )

    # Store references in app state
    app.state.fastmcp_instance = main_mcp
    if event_store:
        app.state.event_store = event_store
    if tool_call_cache:
        app.state.tool_call_cache = tool_call_cache

    return app


def _create_routed_application(
    mcp_instances,
    mcp_service_base_path,
    middleware,
    event_store,
    json_response,
    stateless_http,
    tool_call_cache,
    legacy_sse,
):
    """Create a routed application."""
    routes = []
    apps = []

    for file_path, (file_mcp, route_path, tools_registered) in mcp_instances.items():
        if legacy_sse:
            # Use legacy SSE transport via FastMCP's http_app method
            file_app = file_mcp.http_app(
                transport="sse",
                path=mcp_service_base_path
            )
            logger.info(f"Using legacy SSE transport for '{file_mcp.name}' via FastMCP.http_app")
        else:
            # Use modern streamable HTTP transport
            from fastmcp.server.http import create_streamable_http_app

            file_app = create_streamable_http_app(
                server=cast(Any, file_mcp),
                streamable_http_path=mcp_service_base_path,
                event_store=event_store,
                json_response=json_response,
                stateless_http=stateless_http,
            )
        routes.append(Mount("/" + route_path, app=file_app))
        apps.append(file_app)

    app = Starlette(
        debug=False,
        routes=routes,
        middleware=middleware if middleware else None,
        lifespan=make_combined_lifespan(*apps),
    )

    app.state.mcp_instances = mcp_instances
    if event_store:
        app.state.event_store = event_store
    if tool_call_cache:
        app.state.tool_call_cache = tool_call_cache

    return app
