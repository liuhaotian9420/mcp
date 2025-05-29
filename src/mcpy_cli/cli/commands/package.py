"""
Package command implementation for the CLI.
"""

import typer
import logging
import sys
from typing_extensions import Annotated
from typing import Optional

from ...utils import TransformationError
from ..config import CommonOptions

# Configure a logger for the CLI
cli_logger = logging.getLogger("mcp_sdk_cli.package")


def package_command(
    ctx: typer.Context,
    package_name: Annotated[
        str,
        typer.Option(
            "--package-name",
            "-pn",
            help="Base name for the output package (e.g., 'my_service_pkg'). Required.",
            rich_help_panel="Packaging Configuration",
        ),
    ],
    package_host: Annotated[
        str,
        typer.Option(
            help="Host to configure in the packaged start.sh script.",
            rich_help_panel="Packaging Configuration",
        ),
    ] = "0.0.0.0",
    package_port: Annotated[
        int,
        typer.Option(
            help="Port to configure in the packaged start.sh script.",
            rich_help_panel="Packaging Configuration",
        ),
    ] = 8080,
    package_reload: Annotated[
        bool,
        typer.Option(
            help="Enable auto-reload in the packaged start script (for dev packages).",
            rich_help_panel="Packaging Configuration",
        ),
    ] = False,
    package_workers: Annotated[
        Optional[int],
        typer.Option(
            help="Number of uvicorn workers in the packaged start script.",
            rich_help_panel="Packaging Configuration",
        ),
    ] = None,
    mw_service: Annotated[
        bool,
        typer.Option(
            help="ModelWhale service mode defaults for package (host 0.0.0.0, port 8080). Overrides package-host/port if they are at default.",
            rich_help_panel="Packaging Configuration",
        ),
    ] = True,
):
    """
    Package an MCP service into a zip file for deployment using a lightweight CLI-based approach.

    This command packages user Python files into a deployable service by generating a start.sh script
    that directly uses the MCP CLI to run the service. This approach eliminates the need for generating
    additional Python files, making the package simpler and more maintainable.
    """
    common_opts: CommonOptions = ctx.obj

    if common_opts.source_path is None:
        cli_logger.error("Source path is required for packaging.")
        sys.exit(1)

    if not package_name or not package_name.strip():
        cli_logger.error("A valid --package-name must be provided for packaging.")
        sys.exit(1)

    effective_package_host = package_host
    effective_package_port = package_port

    if mw_service:
        cli_logger.info("ModelWhale service mode active for packaging.")
        # Only override if user hasn't specified non-default host/port for package
        if package_host == "0.0.0.0":  # Default of package_host option
            effective_package_host = "0.0.0.0"
        else:
            cli_logger.info(
                f"Package host overridden to: {package_host} (mw_service active but package_host was specified)."
            )

        if package_port == 8080:  # Default of package_port option
            effective_package_port = 8080
        else:
            cli_logger.info(
                f"Package port overridden to: {package_port} (mw_service active but package_port was specified)."
            )

    cli_logger.info(
        f"Packaging MCP service using CLI-based approach into '{package_name}.zip' from source: {common_opts.source_path}"
    )

    if common_opts.functions:
        cli_logger.info(
            f"Targeting specific functions for package: {common_opts.functions}"
        )

    if common_opts.cors_enabled:
        cli_logger.info(
            f"CORS will be enabled in package. Allowing origins: {common_opts.cors_allow_origins}"
        )
    else:
        cli_logger.info("CORS will be disabled in package.")

    # Validate configuration combinations for packaging
    if common_opts.enable_event_store and common_opts.json_response:
        cli_logger.error(
            "Event store can only be used with SSE mode (json_response=False). Please disable either event store or JSON response mode."
        )
        sys.exit(1)

    # Validate legacy SSE mode compatibility for packaging
    if common_opts.legacy_sse:
        if common_opts.json_response:
            cli_logger.error(
                "Legacy SSE mode is incompatible with JSON response mode. Please disable --json-response when using --legacy-sse."
            )
            sys.exit(1)
        if common_opts.stateless_http:
            cli_logger.error(
                "Legacy SSE mode is incompatible with stateless HTTP mode. Please disable --stateless-http when using --legacy-sse."
            )
            sys.exit(1)

    # Log transport configuration for packaging
    transport_mode = "stateless" if common_opts.stateless_http else "stateful"
    response_format = "JSON" if common_opts.json_response else "SSE"
    if common_opts.legacy_sse:
        response_format = "Legacy SSE"
    cli_logger.info(
        f"Package will use transport mode: {transport_mode}, Response format: {response_format}"
    )

    # Log event store configuration for packaging
    if common_opts.enable_event_store:
        event_store_path_info = common_opts.event_store_path or "./mcp_event_store.db"
        cli_logger.info(
            f"Event store will be enabled in package using SQLite database: {event_store_path_info}"
        )
    else:
        cli_logger.info("Event store will be disabled in package.")

    try:
        # Import the build_mcp_package function
        from ..imports import import_core_modules

        core = import_core_modules()
        build_mcp_package = core.build_mcp_package

        build_mcp_package(
            package_name_from_cli=package_name,
            source_path_str=common_opts.source_path,
            target_function_names=common_opts.functions,
            mcp_server_name=common_opts.mcp_name,
            mcp_server_root_path=common_opts.server_root,
            mcp_service_base_path=common_opts.mcp_base,
            log_level=common_opts.log_level,
            cors_enabled=common_opts.cors_enabled,
            cors_allow_origins=common_opts.cors_allow_origins
            if common_opts.cors_allow_origins is not None
            else [],
            effective_host=effective_package_host,
            effective_port=effective_package_port,
            reload_dev_mode=package_reload,
            workers_uvicorn=package_workers,
            cli_logger=cli_logger,
            mode=common_opts.mode.lower(),
            enable_event_store=common_opts.enable_event_store,
            event_store_path=common_opts.event_store_path,
            stateless_http=common_opts.stateless_http,
            json_response=common_opts.json_response,
            legacy_sse=common_opts.legacy_sse,
        )
        cli_logger.info(
            f"Successfully packaged MCP service into '{package_name}.zip' using the CLI-based approach."
        )

    except TransformationError as e:
        cli_logger.error(f"Failed to package MCP application: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        cli_logger.error(
            f"Packaging error (file not found): {e}. Please check paths and permissions."
        )
        sys.exit(1)
    except ImportError as e:
        cli_logger.error(f"Import error during packaging: {e}")
        sys.exit(1)
    except PermissionError as e:
        cli_logger.error(f"Permission error during packaging: {e}")
        sys.exit(1)
    except Exception as e:
        cli_logger.error(
            f"An unexpected error occurred during packaging: {e}", exc_info=True
        )
        sys.exit(1)
