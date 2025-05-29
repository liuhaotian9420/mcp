"""
Main CLI module that orchestrates all commands and configuration.
"""

import typer
import logging
import pathlib
from typing_extensions import Annotated
from typing import Optional, List

from ..utils import setup_logging, validate_log_level
from .config import CommonOptions, process_optional_list_str_option
from .commands import run_command, package_command, example_command

app = typer.Typer(
    help="""MCP-CLI: Create, run, and package MCP services from your Python code using a lightweight CLI-based approach.
    The CLI supports two modes (via the '--mode' flag):
    - 'composed': Default mode. Mounts each Python file as a separate FastMCP instance under a route derived from its directory structure.
    - 'routed': Mounts all Python files under a single FastMCP instance at a single route.
    """,
    add_completion=False,
)

# Configure a logger for the CLI itself
cli_logger = logging.getLogger("mcp_sdk_cli")
if not cli_logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    cli_logger.setLevel(logging.INFO)


# Add commands to the app
app.command(name="run")(run_command)
app.command(name="package")(package_command)
app.command(name="example")(example_command)


@app.callback()
def main(
    ctx: typer.Context,
    source_path: Annotated[
        Optional[str],
        typer.Option(
            "--source-path",
            help="Path to the Python file or directory containing functions.",
            rich_help_panel="Source Configuration",
        ),
    ] = "./",
    log_level: Annotated[
        str,
        typer.Option(
            help="Logging level for the SDK and server (e.g., info, debug).",
            rich_help_panel="Service Configuration",
        ),
    ] = "info",
    functions: Annotated[
        Optional[List[str]],
        typer.Option(
            "--functions",
            "-f",
            help="Comma-separated list of specific function names to expose. If not provided, all discoverable functions are exposed.",
            rich_help_panel="Service Configuration",
        ),
    ] = None,
    mcp_name: Annotated[
        str,
        typer.Option(
            help="Name for the FastMCP server.", rich_help_panel="Service Configuration"
        ),
    ] = "MCPY-CLI",
    server_root: Annotated[
        str,
        typer.Option(
            help="Root path for the MCP service group in Starlette (e.g., /api).",
            rich_help_panel="Service Configuration",
        ),
    ] = "/mcp-server",
    mcp_base: Annotated[
        str,
        typer.Option(
            help="Base path for MCP protocol endpoints (e.g., /mcp).",
            rich_help_panel="Service Configuration",
        ),
    ] = "/mcp",
    cors_enabled: Annotated[
        bool,
        typer.Option(
            help="Enable CORS middleware.", rich_help_panel="Network Configuration"
        ),
    ] = True,
    cors_allow_origins: Annotated[
        Optional[List[str]],
        typer.Option(
            help='Comma-separated list of allowed CORS origins (e.g. "*", "http://localhost:3000"). Default allows all if CORS is enabled.',
            rich_help_panel="Network Configuration",
        ),
    ] = None,
    mode: Annotated[
        str,
        typer.Option(
            help="Mode for the MCP application. Currently supports 'composed' and 'routes'.",
            rich_help_panel="Service Configuration",
        ),
    ] = "composed",
    enable_event_store: Annotated[
        bool,
        typer.Option(
            help="Enable SQLite-based event store for resumability support in FastMCP HTTP transport. Only applicable when json_response is False (SSE mode).",
            rich_help_panel="Event Store Configuration",
        ),
    ] = False,
    event_store_path: Annotated[
        Optional[str],
        typer.Option(
            help="Custom path for the SQLite event store database file. If not specified, defaults to './mcp_event_store.db'.",
            rich_help_panel="Event Store Configuration",
        ),
    ] = None,
    stateless_http: Annotated[
        bool,
        typer.Option(
            help="Enable stateless HTTP mode where each request creates a fresh transport with no session tracking. Default is stateful mode.",
            rich_help_panel="Transport Configuration",
        ),
    ] = False,
    json_response: Annotated[
        bool,
        typer.Option(
            help="Use JSON response format instead of Server-Sent Events (SSE) streaming. Default is SSE mode.",
            rich_help_panel="Transport Configuration",
        ),
    ] = False,
    legacy_sse: Annotated[
        bool,
        typer.Option(
            "--legacy-sse",
            help="Use legacy SSE transport instead of modern streamable HTTP (deprecated).",
            rich_help_panel="Transport Configuration",
        ),
    ] = False,
):
    """
    MCP-CLI CLI

    This CLI provides commands to create, run, and package MCP services from your Python code
    using a lightweight CLI-based approach. The CLI-based approach simplifies the packaging process
    by generating only a start.sh script that directly uses the CLI to run the service, eliminating
    the need for generating additional Python files.
    """
    processed_functions = process_optional_list_str_option(functions)
    processed_cors_origins = process_optional_list_str_option(cors_allow_origins)

    # If CORS is enabled and no specific origins are provided by the user, default to allowing all.
    if cors_enabled and processed_cors_origins is None:
        processed_cors_origins = ["*"]

    # Create CommonOptions instance with values from callback parameters
    common_obj = CommonOptions(
        source_path=source_path,
        log_level=log_level,
        functions=processed_functions,
        mcp_name=mcp_name,
        server_root=server_root,
        mcp_base=mcp_base,
        cors_enabled=cors_enabled,
        cors_allow_origins=processed_cors_origins,
        mode=mode,
        enable_event_store=enable_event_store,
        event_store_path=event_store_path,
        stateless_http=stateless_http,
        json_response=json_response,
        legacy_sse=legacy_sse,
    )
    ctx.obj = common_obj

    # Setup logging using the determined log level from common options
    normalized_log_level = validate_log_level(common_obj.log_level, cli_logger)
    setup_logging(normalized_log_level)
    cli_logger.setLevel(normalized_log_level.upper())

    # Log the effective source path that will be used
    if common_obj.source_path:
        try:
            # Attempt to resolve to an absolute path for clearer logging
            resolved_path = pathlib.Path(common_obj.source_path).resolve()
            cli_logger.info(f"Effective source path: {resolved_path}")
        except Exception:
            # Fallback if path resolution fails for some reason
            cli_logger.info(f"Effective source path: {common_obj.source_path}")
    else:
        cli_logger.warning(
            "Source path is not configured. Defaulting may occur or errors might follow."
        )


if __name__ == "__main__":
    app()
