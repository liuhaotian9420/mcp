#!/usr/bin/env python
"""
Direct execution script for MCP ModelService SDK

This script directly runs the sample tools without complex arguments or imports.
Simply run it with: python run_mcp.py
"""

import sys
import os

# Set up proper paths
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "src")
sample_path = os.path.join(project_root, "tests", "test_mcp_package", "sample_tools.py")

sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# Import FastMCP directly
try:
    from fastmcp import FastMCP

    print("FastMCP successfully imported")
except ImportError as e:
    print(f"ERROR: FastMCP not available: {e}")
    print("Please install FastMCP with: pip install fastmcp")
    sys.exit(1)


# Run MCP application directly with uvicorn
def run_mcp_server():
    try:
        import uvicorn
        import importlib.util

        # Load the sample tools directly
        print(f"Loading sample tools from {sample_path}")
        spec = importlib.util.spec_from_file_location("sample_tools", sample_path)
        sample_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sample_module)

        # Create a simple FastMCP instance directly
        mcp = FastMCP(name="DirectMCPService")

        # Register all functions in the module
        import inspect

        for name, func in inspect.getmembers(sample_module, inspect.isfunction):
            if not name.startswith("_"):  # Skip private functions
                print(f"Registering function: {name}")
                mcp.tool(name=name)(func)

        # Create an ASGI app
        app = mcp.http_app(path="/mcp")

        # Run with uvicorn
        print(f"Starting MCP server with sample tools at {sample_path}")
        print("Server will be available at http://127.0.0.1:8080")
        uvicorn.run(app, host="127.0.0.1", port=8080)
    except Exception as e:
        print(f"ERROR: Failed to start MCP server: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_mcp_server()
