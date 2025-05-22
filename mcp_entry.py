#!/usr/bin/env python
"""
UVX entry point for MCP SDK

This script allows users to run MCP tools with UVX:

uvx -m mcp_entry sample_tools.py
"""

import sys
import importlib.util
from pathlib import Path


def main():
    # Check if we have enough arguments
    if len(sys.argv) < 2:
        print("Usage: uvx -m mcp_entry <path_to_tools_file> [options]")
        print("Options:")
        print("  --port PORT      Port to run the server on (default: 8080)")
        print("  --host HOST      Host to run the server on (default: 127.0.0.1)")
        print("  --name NAME      Name for the MCP service (default: MCPService)")
        sys.exit(1)

    # Get the tools file from arguments
    tools_file = sys.argv[1]
    port = 8080
    host = "127.0.0.1"
    name = "MCPService"

    # Parse additional options
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--name" and i + 1 < len(sys.argv):
            name = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # Ensure the tools file exists
    tools_path = Path(tools_file)
    if not tools_path.exists():
        print(f"Error: Tools file '{tools_file}' does not exist")
        sys.exit(1)

    # Import FastMCP
    try:
        from fastmcp import FastMCP

        print("FastMCP successfully imported")
    except ImportError as e:
        print(f"Error: FastMCP not available: {e}")
        print("Please install FastMCP with: pip install fastmcp")
        sys.exit(1)

    # Load the tools file
    print(f"Loading tools from {tools_path}")
    tools_module_name = tools_path.stem
    spec = importlib.util.spec_from_file_location(tools_module_name, str(tools_path))
    tools_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tools_module)

    # Create FastMCP instance
    mcp = FastMCP(name=name)

    # Register all functions in the module
    import inspect

    registered_tools = 0
    for fn_name, fn in inspect.getmembers(tools_module, inspect.isfunction):
        if not fn_name.startswith("_"):  # Skip private functions
            print(f"Registering function: {fn_name}")
            mcp.tool(name=fn_name)(fn)
            registered_tools += 1

    print(f"Registered {registered_tools} tools from {tools_path}")

    # Run server
    try:
        import uvicorn

        print(f"Starting MCP server on {host}:{port}")
        app = mcp.http_app(path="/mcp")
        uvicorn.run(app, host=host, port=port)
    except ImportError:
        print("Error: uvicorn not available. Please install with: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
