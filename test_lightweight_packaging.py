#!/usr/bin/env python
"""
Test script for the lightweight packaging approach.

This script creates a sample Python file with MCP tools and packages it using
the lightweight approach.
"""

# Import the packaging module
from src.mcp_modelservice_sdk.src.packaging import build_mcp_package
import pathlib
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("test_packaging")


def create_test_file():
    """Create a test Python file with MCP tools."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file_path = pathlib.Path(temp_dir) / "test_tools.py"
        with open(test_file_path, "w") as f:
            f.write("""
# Test file with MCP tools

def add(a: int, b: int) -> int:
    \"\"\"Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The sum of a and b
    \"\"\"
    return a + b

def multiply(a: int, b: int) -> int:
    \"\"\"Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The product of a and b
    \"\"\"
    return a * b
""")
        logger.info(f"Created test file at {test_file_path}")
        return test_file_path


def test_lightweight_packaging():
    """Test the lightweight packaging approach."""
    # Create a test file
    test_file_path = create_test_file()

    # Package it using the lightweight approach
    build_mcp_package(
        package_name_from_cli="test_lightweight_package",
        source_path_str=str(test_file_path),
        target_function_names=None,  # Include all functions
        mcp_server_name="TestMCPService",
        mcp_server_root_path="/api",
        mcp_service_base_path="/mcp",
        log_level="info",
        cors_enabled=True,
        cors_allow_origins=["*"],
        effective_host="0.0.0.0",
        effective_port=8080,
        reload_dev_mode=False,
        workers_uvicorn=None,
        cli_logger=logger,
        lightweight_mode=True,  # Use the lightweight approach
    )

    logger.info("Packaging completed successfully!")
    logger.info("Check the test_lightweight_package directory for the results.")


if __name__ == "__main__":
    test_lightweight_packaging()
