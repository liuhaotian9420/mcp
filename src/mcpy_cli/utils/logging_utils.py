"""
Logging utilities for the MCP Modelservice SDK.
"""

import logging
from typing import List


def setup_logging(log_level: str) -> None:
    """
    Set up logging configuration for the SDK.

    Args:
        log_level: Log level string (e.g., 'info', 'debug')
    """
    # This would typically import from core._setup_logging
    # For now, we'll implement basic logging setup
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def validate_log_level(log_level: str, logger: logging.Logger) -> str:
    """
    Validate and normalize the log level string.

    Args:
        log_level: Log level string to validate
        logger: Logger to use for messages

    Returns:
        Normalized log level string (lowercase) if valid, or 'info' as fallback
    """
    valid_levels: List[str] = ["critical", "error", "warning", "info", "debug", "trace"]
    normalized = log_level.lower()

    if normalized not in valid_levels:
        logger.warning(
            f"Invalid log level '{log_level}'. Valid options are: {', '.join(valid_levels)}"
        )
        logger.warning("Defaulting to 'info'.")
        return "info"

    return normalized
