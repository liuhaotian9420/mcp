"""
Example script for running an MCP application with the official MCP EventStore implementation.

This demonstrates how to use the SQLite-based EventStore that implements the official
MCP EventStore interface for resumability support in FastMCP HTTP transport.

Usage:
    python run_with_mcp_event_store.py
"""

from mcpy_cli.src.app_builder import create_mcp_application

import sys
import logging
import uvicorn
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_event_store_example")


def main():
    """Run the MCP application with the official MCP EventStore enabled."""
    logger.info(
        "Starting MCP application with official MCP EventStore (SQLite backend)"
    )

    # Create a simple example function to demonstrate the event store
    example_functions_dir = Path(__file__).parent / "example_functions"
    example_functions_dir.mkdir(exist_ok=True)

    # Create a simple example function file
    example_file = example_functions_dir / "math_tools.py"
    if not example_file.exists():
        example_file.write_text('''
"""Math utility functions for MCP EventStore demonstration."""

def add(a: int, b: int) -> int:
    """Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The sum of a and b
    """
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The product of a and b
    """
    return a * b
''')

    # Create the MCP application with event store enabled
    app = create_mcp_application(
        source_path_str=str(example_functions_dir),
        mcp_server_name="EventStoreDemo",
        enable_event_store=True,  # Enable the official MCP EventStore
        event_store_path="./mcp_event_store_demo.db",  # Custom database path
    )

    logger.info("MCP application created with EventStore enabled")
    logger.info("Event store database: ./mcp_event_store_demo.db")
    logger.info("Starting server on http://127.0.0.1:8080/mcp-server/mcp")

    # Run the application
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")


if __name__ == "__main__":
    main()
