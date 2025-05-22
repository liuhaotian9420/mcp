"""
The core module for the MCP Modelservice SDK.
This module re-exports key functionalities for application building and packaging,
and provides a centralized logging setup for the SDK.
"""

import logging
import os
import pathlib

# Import the required modules upfront to avoid E402 errors
from .app_builder import create_mcp_application, TransformationError
from .packaging import build_mcp_package


# Function to normalize file paths to handle both relative and absolute paths
def _normalize_path(path_str):
    """Normalize a path string to handle both relative and absolute paths.

    Args:
        path_str: The path string to normalize

    Returns:
        A normalized absolute path
    """
    path_obj = pathlib.Path(path_str)

    # If it's already absolute, return it
    if path_obj.is_absolute():
        return str(path_obj)

    # Otherwise, make it absolute relative to the current working directory
    return str(pathlib.Path(os.getcwd()) / path_obj)


# The .discovery and .packaging_utils modules are primarily internal helpers for the above,
# but can be imported directly if advanced users need to extend the SDK's capabilities.

# Logger for messages originating from this core.py module itself.
sdk_core_logger = logging.getLogger(__name__)

# Get the root logger for the entire SDK namespace for configuration.
sdk_namespace_root_logger = logging.getLogger("mcp_modelservice_sdk")

# Initial basic configuration for the SDK's root logger.
# This ensures that if _setup_logging is not called, or called late,
# SDK logs still have a chance to be output with a default INFO level.
# _setup_logging provides more fine-grained control.
if not sdk_namespace_root_logger.hasHandlers():
    console_handler = logging.StreamHandler()  # Defaults to sys.stderr
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    sdk_namespace_root_logger.addHandler(console_handler)
    sdk_namespace_root_logger.setLevel(logging.INFO)  # Default level
    # Prevent messages from propagating to the Python root logger
    # if we are adding our own handler to the SDK's namespace logger.
    sdk_namespace_root_logger.propagate = False


def _setup_logging(log_level_str: str = "info"):
    """Configures logging for all modules under the 'mcp_modelservice_sdk' namespace.

    This function sets the logging level for the SDK's root logger and ensures
    that a handler is configured to output messages. It is typically called by the
    CLI or at the beginning of a script using the SDK to standardize log output.

    Args:
        log_level_str: The desired logging level as a string (e.g., "info", "debug").
    """
    level = getattr(logging, log_level_str.upper(), logging.INFO)

    sdk_namespace_root_logger.setLevel(level)

    # Ensure existing handlers (if any) on the SDK's root logger are also set to the new level.
    # This primarily targets the console_handler added above or any other handlers
    # that might have been added before this call.
    for handler in sdk_namespace_root_logger.handlers:
        handler.setLevel(level)
        # Optionally, could re-apply a standard formatter here if needed:
        # formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        # handler.setFormatter(formatter)

    # If, for some reason, no handlers exist after the initial setup (e.g., they were removed),
    # add a new one. This ensures logging output is always available after calling _setup_logging.
    if not sdk_namespace_root_logger.hasHandlers():
        fallback_handler = logging.StreamHandler()
        fallback_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        fallback_handler.setFormatter(fallback_formatter)
        fallback_handler.setLevel(level)
        sdk_namespace_root_logger.addHandler(fallback_handler)
        sdk_namespace_root_logger.propagate = (
            False  # Ensure no duplicate logs to root logger
        )

    sdk_core_logger.info(
        f"MCP Modelservice SDK logging initialized. Level: {log_level_str.upper()} for all loggers in 'mcp_modelservice_sdk' namespace."
    )


# Explicitly define what is exported when 'from mcp_modelservice_sdk.src.core import *' is used.
__all__ = [
    "create_mcp_application",  # Re-exported from .app_builder
    "build_mcp_package",  # Re-exported from .packaging
    "TransformationError",  # Re-exported from .app_builder
    "_setup_logging",  # Defined in this module, exposed for CLI and advanced usage.
]
