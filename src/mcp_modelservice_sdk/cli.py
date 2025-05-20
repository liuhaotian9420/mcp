import typer
from typing_extensions import Annotated
from typing import Optional, List
import uvicorn
import logging
import sys
import pathlib


# Import core modules using a helper function to avoid duplicate imports
def _import_core_modules():
    # Try to import from the main package path first
    try:
        import mcp_modelservice_sdk.src.core as core_module

        return core_module
    except ImportError as e:
        # If that fails, try the fallback path
        try:
            from .src import core as core_module

            return core_module
        except ImportError:
            # Both import attempts failed
            sys.stderr.write(
                "Failed to import core modules. Ensure the package is installed correctly or PYTHONPATH is set up.\n"
            )
            sys.stderr.write(f"Error details: {e}\n")
            raise  # Re-raise the error if both imports fail


# Import the core module
core = _import_core_modules()

# Get the required functions and classes from the module
create_mcp_application = core.create_mcp_application
build_mcp_package = core.build_mcp_package
TransformationError = core.TransformationError
_setup_logging = core._setup_logging

app = typer.Typer(
    help="MCP Modelservice SDK CLI: Create, run, and package MCP services from your Python code using a lightweight CLI-based approach.",
    add_completion=False,
)

# Configure a logger for the CLI itself
cli_logger = logging.getLogger("mcp_sdk_cli")  # More specific logger name
# Basic configuration for cli_logger; _setup_logging from core will handle SDK module logging.
if not cli_logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )  # Ensures basicConfig is called once
    cli_logger.setLevel(logging.INFO)  # Set level for this specific logger


# Common options group
class CommonOptions:
    def __init__(
        self,
        source_path: Annotated[
            str,
            typer.Option(
                help="Path to the Python file or directory containing functions.",
                rich_help_panel="Source Configuration",
            ),
        ],
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
                help="Name for the FastMCP server.",
                rich_help_panel="Service Configuration",
            ),
        ] = "MCPModelService",
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
                help='Comma-separated list of allowed CORS origins (e.g. "*", "http://localhost:3000"). Default allows all.',
                rich_help_panel="Network Configuration",
            ),
        ] = None,
    ):
        self.source_path = source_path
        self.log_level = log_level
        self.functions = functions
        self.mcp_name = mcp_name
        self.server_root = server_root
        self.mcp_base = mcp_base
        self.cors_enabled = cors_enabled
        self.cors_allow_origins = cors_allow_origins


def _validate_source_path(source_path: str, logger: logging.Logger) -> bool:
    """
    Validate that the source path exists and contains valid Python files.

    Args:
        source_path: Path to validate
        logger: Logger to use for messages

    Returns:
        True if the path is valid, False otherwise
    """
    path_obj = pathlib.Path(source_path)

    # Check if the path exists
    if not path_obj.exists():
        logger.error(f"Source path does not exist: {path_obj.absolute()}")
        logger.error(f"Current working directory: {pathlib.Path.cwd()}")
        return False

    # If it's a file, check if it's a Python file
    if path_obj.is_file() and path_obj.suffix.lower() != ".py":
        logger.error(f"Source path is not a Python file: {path_obj.absolute()}")
        return False

    # If it's a directory, check if it contains any Python files
    if path_obj.is_dir():
        py_files = list(path_obj.glob("**/*.py"))
        if not py_files:
            logger.error(f"No Python files found in directory: {path_obj.absolute()}")
            return False

    return True


def _validate_log_level(log_level: str, logger: logging.Logger) -> str:
    """
    Validate and normalize the log level string.

    Args:
        log_level: Log level string to validate
        logger: Logger to use for messages

    Returns:
        Normalized log level string (lowercase) if valid, or 'info' as fallback
    """
    valid_levels = ["critical", "error", "warning", "info", "debug", "trace"]
    normalized = log_level.lower()

    if normalized not in valid_levels:
        logger.warning(
            f"Invalid log level '{log_level}'. Valid options are: {', '.join(valid_levels)}"
        )
        logger.warning("Defaulting to 'info'.")
        return "info"

    return normalized


def _process_optional_list_str_option(
    opt_list: Optional[List[str]],
):
    if not opt_list:
        return None
    if len(opt_list) == 1 and "," in opt_list[0]:
        return [item.strip() for item in opt_list[0].split(",") if item.strip()]
    return [item.strip() for item in opt_list if item.strip()]


@app.command()
def run(
    ctx: typer.Context,  # To access common options
    host: Annotated[
        str,
        typer.Option(
            help="Host to bind the server to.", rich_help_panel="Network Configuration"
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            help="Port to bind the server to.", rich_help_panel="Network Configuration"
        ),
    ] = 8000,
    reload: Annotated[
        bool,
        typer.Option(
            help="Enable auto-reload for development.", rich_help_panel="Development"
        ),
    ] = False,
    workers: Annotated[
        Optional[int],
        typer.Option(
            help="Number of worker processes for uvicorn.",
            rich_help_panel="Development",
        ),
    ] = None,
):
    """
    Run an MCP service locally using Uvicorn.

    This command creates and runs an MCP service from your Python code. It's also used
    by the start.sh script generated by the 'package' command in the CLI-based approach.
    All configuration parameters can be passed via CLI options.
    """
    common_opts: CommonOptions = (
        ctx.obj
    )  # CommonOptions object is stored in ctx.obj by the callback

    _setup_logging(common_opts.log_level)  # Setup SDK logging
    cli_logger.setLevel(common_opts.log_level.upper())  # Also set CLI logger level

    cli_logger.info(f"Attempting to run service from source: {common_opts.source_path}")

    # Validate the source path before proceeding
    if not _validate_source_path(common_opts.source_path, cli_logger):
        cli_logger.error(
            "Source path validation failed. Please check the path and ensure it contains valid Python files."
        )
        sys.exit(1)

    processed_functions = _process_optional_list_str_option(common_opts.functions)
    if processed_functions:
        cli_logger.info(f"Targeting specific functions: {processed_functions}")

    processed_cors_origins = _process_optional_list_str_option(
        common_opts.cors_allow_origins
    )
    if (
        processed_cors_origins is None
    ):  # Typer default for list is [], we want ["*"] if user provides nothing
        processed_cors_origins = ["*"]

    if common_opts.cors_enabled:
        cli_logger.info(
            f"CORS will be enabled. Allowing origins: {processed_cors_origins}"
        )
    else:
        cli_logger.info("CORS will be disabled.")

    try:
        mcp_app = create_mcp_application(
            source_path_str=common_opts.source_path,
            target_function_names=processed_functions,
            mcp_server_name=common_opts.mcp_name,
            mcp_server_root_path=common_opts.server_root,
            mcp_service_base_path=common_opts.mcp_base,
            # log_level is NOT passed here; _setup_logging handles SDK logging
            cors_enabled=common_opts.cors_enabled,
            cors_allow_origins=processed_cors_origins,
        )
        cli_logger.info(
            f"MCP application '{common_opts.mcp_name}' created successfully."
        )
        cli_logger.info(
            f"Starting server on {host}:{port} with log level {common_opts.log_level}..."
        )

        # Validate and normalize the log level
        uvicorn_log_level = _validate_log_level(common_opts.log_level, cli_logger)

        uvicorn.run(
            mcp_app,
            host=host,
            port=port,
            log_level=uvicorn_log_level,
            reload=reload,
            workers=workers if workers is not None and workers > 0 else None,
        )
    except TransformationError as e:
        cli_logger.error(f"Failed to create MCP application: {e}")
        cli_logger.error("Please check the source path and function definitions.")
        sys.exit(1)
    except FileNotFoundError as e:  # From discover_py_files if path is wrong
        cli_logger.error(f"Source path error: {e}. Please ensure the path is correct.")
        cli_logger.error(f"Current working directory: {pathlib.Path.cwd()}")
        cli_logger.error(
            f"Attempted to access: {pathlib.Path(common_opts.source_path).absolute()}"
        )
        sys.exit(1)
    except ImportError as e:  # If there are issues importing user modules
        cli_logger.error(f"Import error: {e}")
        cli_logger.error(
            "This may be due to missing dependencies or Python path issues."
        )
        cli_logger.error(
            "Ensure all required packages are installed and your PYTHONPATH is set correctly."
        )
        sys.exit(1)
    except Exception as e:
        cli_logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def package(
    ctx: typer.Context,  # To access common options
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

    _setup_logging(common_opts.log_level)  # Setup SDK logging
    cli_logger.setLevel(common_opts.log_level.upper())  # Also set CLI logger level

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

    # Validate the source path before proceeding
    if not _validate_source_path(common_opts.source_path, cli_logger):
        cli_logger.error(
            "Source path validation failed. Please check the path and ensure it contains valid Python files."
        )
        sys.exit(1)

    processed_functions = _process_optional_list_str_option(common_opts.functions)
    if processed_functions:
        cli_logger.info(f"Targeting specific functions: {processed_functions}")

    processed_cors_origins = _process_optional_list_str_option(
        common_opts.cors_allow_origins
    )
    if processed_cors_origins is None:
        processed_cors_origins = ["*"]

    if common_opts.cors_enabled:
        cli_logger.info(
            f"CORS will be enabled in package. Allowing origins: {processed_cors_origins}"
        )
    else:
        cli_logger.info("CORS will be disabled in package.")

    try:
        build_mcp_package(
            package_name_from_cli=package_name,
            source_path_str=common_opts.source_path,
            target_function_names=processed_functions,
            mcp_server_name=common_opts.mcp_name,
            mcp_server_root_path=common_opts.server_root,
            mcp_service_base_path=common_opts.mcp_base,
            log_level=common_opts.log_level,  # Used for logging during packaging
            cors_enabled=common_opts.cors_enabled,
            cors_allow_origins=processed_cors_origins,
            effective_host=effective_package_host,  # Use package specific host/port
            effective_port=effective_package_port,
            reload_dev_mode=package_reload,
            workers_uvicorn=package_workers,
            cli_logger=cli_logger,  # Pass the CLI logger for build_mcp_package to use
        )
        cli_logger.info(
            f"Successfully packaged MCP service into '{package_name}.zip' using the CLI-based approach."
        )
        project_dir_info = pathlib.Path(package_name) / "project"
        cli_logger.info(f"The project files are located in '{project_dir_info}'.")
        cli_logger.info(
            "The package contains a start.sh script that uses the MCP CLI to run your service."
        )
        cli_logger.info(
            "To run the service, execute the start.sh script in the project directory."
        )
        cli_logger.info(
            "You can customize the requirements.txt file to include any additional dependencies."
        )

    except TransformationError as e:
        cli_logger.error(f"Failed to package MCP application: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        cli_logger.error(
            f"Packaging error (file not found): {e}. Please check paths and permissions."
        )
        cli_logger.error(f"Current working directory: {pathlib.Path.cwd()}")
        cli_logger.error(
            f"Attempted to access: {pathlib.Path(common_opts.source_path).absolute()}"
        )
        sys.exit(1)
    except ImportError as e:  # If there are issues importing user modules
        cli_logger.error(f"Import error during packaging: {e}")
        cli_logger.error(
            "This may be due to missing dependencies or Python path issues."
        )
        cli_logger.error(
            "Ensure all required packages are installed and your PYTHONPATH is set correctly."
        )
        sys.exit(1)
    except PermissionError as e:
        cli_logger.error(f"Permission error during packaging: {e}")
        cli_logger.error(
            "Please check that you have write permissions to the target directory."
        )
        sys.exit(1)
    except Exception as e:
        cli_logger.error(
            f"An unexpected error occurred during packaging: {e}", exc_info=True
        )
        sys.exit(1)


# Callback to create and store the CommonOptions instance
@app.callback()
def main(
    ctx: typer.Context,
    source_path: Annotated[
        str,
        typer.Option(
            help="Path to the Python file or directory containing functions.",
            rich_help_panel="Source Configuration",
        ),
    ] = "./",  # Default source path
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
    ] = "MCPModelService",
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
            help='Comma-separated list of allowed CORS origins (e.g. "*", "http://localhost:3000"). Default allows all.',
            rich_help_panel="Network Configuration",
        ),
    ] = None,  # Default is None, handled in commands
):
    """
    MCP Modelservice SDK CLI

    This CLI provides commands to create, run, and package MCP services from your Python code
    using a lightweight CLI-based approach. The CLI-based approach simplifies the packaging process
    by generating only a start.sh script that directly uses the CLI to run the service, eliminating
    the need for generating additional Python files.
    """
    # Store common options in context to be accessed by subcommands
    ctx.obj = CommonOptions(
        source_path=source_path,
        log_level=log_level,
        functions=functions,
        mcp_name=mcp_name,
        server_root=server_root,
        mcp_base=mcp_base,
        cors_enabled=cors_enabled,
        cors_allow_origins=cors_allow_origins,
    )
    # Initial logging setup can also be done here if desired globally for all commands
    # _setup_logging(log_level)
    # cli_logger.setLevel(log_level.upper())


if __name__ == "__main__":
    app()
