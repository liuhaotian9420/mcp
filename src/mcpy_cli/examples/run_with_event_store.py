"""
Example script for running an MCP application with the SQLite event store.

Usage:
    python run_with_event_store.py --source-path /path/to/tools --event-store
"""

from mcpy_cli.src.app_builder import create_mcp_application
from mcpy_cli.src.cli import run_app_with_args


import sys
import logging
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("event_store_example")


def main():
    """Run the MCP application with event store enabled."""
    logger.info("Starting MCP application with SQLite event store")

    # Call the run_app_with_args function to create and run the application
    run_app_with_args(create_mcp_application)


if __name__ == "__main__":
    main()
