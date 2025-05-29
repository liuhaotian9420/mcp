"""
Example command implementation for the CLI.
"""

import typer
import logging
import sys
import os
import tempfile
import subprocess
import time
import threading
import webbrowser
from typing_extensions import Annotated
from pathlib import Path

# Configure a logger for the CLI
cli_logger = logging.getLogger("mcp_sdk_cli.example")


def example_command(
    ctx: typer.Context,
    with_inspector: Annotated[
        bool,
        typer.Option(
            "--with-inspector",
            help="Launch MCP Inspector alongside the example service for visualization and testing.",
            rich_help_panel="Example Configuration",
        ),
    ] = False,
    inspector_port: Annotated[
        int,
        typer.Option(
            "--inspector-port",
            help="Port for the MCP Inspector UI.",
            rich_help_panel="Example Configuration",
        ),
    ] = 6274,
):
    """
    Run an introductory example MCP service with arithmetic operations.

    This command creates and runs a simple MCP service that demonstrates:
    - Basic arithmetic tools (add, subtract, multiply, divide)
    - Streamable HTTP transport
    - Optional MCP Inspector integration for visualization

    The service runs on localhost:8080 and optionally launches the MCP Inspector
    for interactive testing and debugging.
    """
    cli_logger.info("🚀 Starting MCP-CLI Example")
    cli_logger.info("This example demonstrates a simple arithmetic MCP service")

    # Print information about command line arguments
    cli_logger.info("\n📋 Command Line Arguments:")
    cli_logger.info("  --with-inspector: Launch the MCP Inspector UI alongside the service")
    cli_logger.info("                   This provides a visual interface for testing your MCP tools")
    cli_logger.info("  --inspector-port: Set the port for the MCP Inspector UI (default: 6274)")
    cli_logger.info("                   Change this if the default port is already in use")
    
    # Add information about the MCP Inspector
    cli_logger.info("\n🔍 About MCP Inspector:")
    cli_logger.info("  The MCP Inspector is a web-based UI tool for testing and debugging MCP services")
    cli_logger.info("  It allows you to:")
    cli_logger.info("    • Discover available tools in your MCP service")
    cli_logger.info("    • Test tools with different parameters")
    cli_logger.info("    • View request/response history")
    cli_logger.info("    • Debug your MCP service interactively")
    
    # Add installation instructions for MCP Inspector
    cli_logger.info("\n⚙️ Installing MCP Inspector:")
    cli_logger.info("  The MCP Inspector requires Node.js to be installed on your system")
    cli_logger.info("  1. Install Node.js from https://nodejs.org/ (version 14 or later)")
    cli_logger.info("  2. The Inspector will be automatically installed via npx when needed")
    cli_logger.info("  3. You can also install it globally with: npm install -g @modelcontextprotocol/inspector")

    # Create temporary directory for example files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        example_file = temp_path / "arithmetic_example.py"

        # Create the example server file
        example_content = '''"""
Example MCP service with arithmetic operations using streamable HTTP transport.
This demonstrates the basic functionality of the MCP-CLI.
"""

from fastmcp import FastMCP
from typing import Dict

# Create FastMCP instance for streamable HTTP
mcp = FastMCP("Arithmetic Example Service")


@mcp.tool()
def add(a: float, b: float) -> Dict[str, float]:
    """Add two numbers together.
    
    Args:
        a: First number to add
        b: Second number to add
        
    Returns:
        Dictionary containing the sum of a and b
    """
    return {"result": a + b}


@mcp.tool()
def subtract(a: float, b: float) -> Dict[str, float]:
    """Subtract the second number from the first.
    
    Args:
        a: Number to subtract from (minuend)
        b: Number to subtract (subtrahend)
        
    Returns:
        Dictionary containing the result of a - b
    """
    return {"result": a - b}


@mcp.tool()
def multiply(a: float, b: float) -> Dict[str, float]:
    """Multiply two numbers together.
    
    Args:
        a: First number to multiply
        b: Second number to multiply
        
    Returns:
        Dictionary containing the product of a and b
    """
    return {"result": a * b}


@mcp.tool()
def divide(a: float, b: float) -> Dict[str, float]:
    """Divide the first number by the second.
    
    Args:
        a: Dividend (number to be divided)
        b: Divisor (number to divide by, must not be zero)
        
    Returns:
        Dictionary containing the result of a / b
        
    Raises:
        ValueError: If b is zero (division by zero)
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return {"result": a / b}


if __name__ == "__main__":
    # Run with streamable HTTP transport on port 8080
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8081, path="/mcp")
'''

        # Write the example file
        with open(example_file, "w", encoding="utf-8") as f:
            f.write(example_content)

        cli_logger.info(f"📝 Created example service at: {example_file}")

        # Print the example file content in a nicely formatted way
        cli_logger.info("\n📄 Example Service Code:")
        cli_logger.info("=" * 80)
        
        # Split the content by lines and print with line numbers
        for i, line in enumerate(example_content.split('\n'), 1):
            # Add line numbers for better readability
            cli_logger.info(f"{i:3d} | {line}")
            
        cli_logger.info("=" * 80)

        # Function to run the MCP service
        def run_mcp_service():
            try:
                cli_logger.info("🔧 Starting MCP service on localhost:8081...")
                result = subprocess.run(
                    [sys.executable, str(example_file)],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    cli_logger.error(f"MCP service failed: {result.stderr}")
            except Exception as e:
                cli_logger.error(f"Error running MCP service: {e}")

        # Function to run the MCP Inspector
        def run_mcp_inspector():
            if not with_inspector:
                return

            try:
                cli_logger.info(
                    f"🔍 Starting MCP Inspector on port {inspector_port}..."
                )
                # Wait a moment for the MCP service to start
                time.sleep(3)

                # Set up environment variables for the inspector
                inspector_env = os.environ.copy()
                inspector_env["CLIENT_PORT"] = str(inspector_port)
                inspector_env["MCP_SERVICE_URL"] = "http://localhost:8081/mcp"

                # Set up the direct URL with query parameters for automatic connection
                inspector_url_with_params = (
                    f"http://localhost:{inspector_port}/"
                    f"?transport=streamable-http"
                    f"&serverUrl=http://localhost:8081/mcp"
                )

                # Open the browser with the parameterized URL
                cli_logger.info(
                    f"🌐 Opening browser to MCP Inspector with direct connection at: {inspector_url_with_params}"
                )
                try:
                    webbrowser.open(inspector_url_with_params)
                except Exception as e:
                    cli_logger.warning(f"Could not open browser automatically: {e}")

                # Launch the inspector process
                if os.name == "nt":  # Windows
                    result = subprocess.run(
                        "npx @modelcontextprotocol/inspector",
                        env=inspector_env,
                        cwd=temp_dir,
                        shell=True,
                    )
                else:  # macOS, Linux, etc.
                    result = subprocess.run(
                        ["npx", "@modelcontextprotocol/inspector"],
                        env=inspector_env,
                        cwd=temp_dir,
                    )

                if result.returncode != 0:
                    cli_logger.warning(
                        f"MCP Inspector exited with non-zero code: {result.returncode}"
                    )

            except FileNotFoundError:
                cli_logger.error(
                    "❌ npx not found. Please install Node.js to use the MCP Inspector."
                )
                cli_logger.info(
                    "You can still test the service directly at http://localhost:8081/mcp"
                )
                # Add detailed installation instructions when npx is not found
                cli_logger.info("\n📥 To install Node.js and npm:")
                cli_logger.info("  1. Download from https://nodejs.org/ (LTS version recommended)")
                cli_logger.info("  2. Follow the installation instructions for your operating system")
                cli_logger.info("  3. Restart your terminal/command prompt after installation")
                cli_logger.info("  4. Verify installation with: node --version && npm --version")
                cli_logger.info("  5. Run this command again with --with-inspector")
                cli_logger.info("\n🔄 Alternative installation methods:")
                cli_logger.info("  • Windows: Use winget install OpenJS.NodeJS.LTS")
                cli_logger.info("  • macOS: Use brew install node")
                cli_logger.info("  • Linux: Use your distribution's package manager")
            except Exception as e:
                cli_logger.error(f"Error running MCP Inspector: {e}")

        try:
            # Start MCP service in a separate thread
            service_thread = threading.Thread(target=run_mcp_service, daemon=True)
            service_thread.start()

            # Give the service a moment to start
            time.sleep(2)

            cli_logger.info("\n✅ MCP service is running!")
            
            # Provide detailed information about accessing the service
            cli_logger.info("\n🔍 Service Information:")
            cli_logger.info("  🌐 Service URL: http://localhost:8081/mcp")
            cli_logger.info("  📚 Available tools: add, subtract, multiply, divide")
            cli_logger.info("\n💡 Ways to interact with your service:")
            cli_logger.info("  1. Use the MCP Inspector UI (with --with-inspector flag)")
            cli_logger.info("  2. Send HTTP requests directly to http://localhost:8081/mcp")
            cli_logger.info("  3. Use the MCP client library in your code")
            
            # Add more detailed information about using the MCP Inspector
            cli_logger.info("\n🔍 Using the MCP Inspector:")
            cli_logger.info("  • The Inspector provides a user-friendly interface at http://localhost:" + str(inspector_port))
            cli_logger.info("  • It automatically connects to your MCP service at http://localhost:8081/mcp")
            cli_logger.info("  • You can manually connect to any MCP service by entering its URL")
            cli_logger.info("  • The Inspector works with any MCP-compatible service, not just this example")
            cli_logger.info("  • For advanced usage, see the Inspector documentation at:")
            cli_logger.info("    https://github.com/modelcontextprotocol/inspector")
            
            # Example curl commands for direct testing
            cli_logger.info("\n🧪 Example curl command to test the add tool:")
            cli_logger.info('  curl -X POST http://localhost:8081/mcp \\')
            cli_logger.info('    -H "Content-Type: application/json" \\')
            cli_logger.info('    -d \'{\'"tool_name\'": "add", "parameters": {"a": 5, "b": 3}}\'')

            if with_inspector:
                cli_logger.info(
                    f"🔍 MCP Inspector will be launched on port {inspector_port}"
                )
                cli_logger.info(
                    "💡 The inspector provides a visual interface to test your MCP tools"
                )
                cli_logger.info(
                    "💡 It will automatically connect to your MCP service at http://localhost:8081/mcp"
                )
                
                # Add more detailed information about the Inspector features
                cli_logger.info("\n🎮 MCP Inspector Features:")
                cli_logger.info("  • Interactive UI for testing MCP tools without writing code")
                cli_logger.info("  • Real-time request and response monitoring")
                cli_logger.info("  • Parameter validation and type checking")
                cli_logger.info("  • History of all tool calls for debugging")
                cli_logger.info("  • Support for various MCP transport protocols")
                cli_logger.info("  • Customizable connection settings")
                
                cli_logger.info("\n🔗 Inspector will be available at:")
                cli_logger.info(f"  http://localhost:{inspector_port}/?transport=streamable-http&serverUrl=http://localhost:8081/mcp")

                # Start inspector in main thread (blocking)
                run_mcp_inspector()
            else:
                cli_logger.info("\n🚀 Example service is running. Press Ctrl+C to stop.")
                cli_logger.info("\n💡 Tips:")
                cli_logger.info("  • Add --with-inspector to launch the visual testing interface")
                cli_logger.info("  • Change the inspector port with --inspector-port if needed")
                cli_logger.info("  • The example service demonstrates basic MCP functionality")
                cli_logger.info("  • Study the example code to learn how to create your own MCP services")
                
                # Add troubleshooting tips for the MCP Inspector
                cli_logger.info("\n🔧 Troubleshooting MCP Inspector:")
                cli_logger.info("  • If the Inspector fails to start, ensure Node.js is installed correctly")
                cli_logger.info("  • You may need to run 'npm install -g @modelcontextprotocol/inspector' manually")
                cli_logger.info("  • Check if port " + str(inspector_port) + " is already in use by another application")
                cli_logger.info("  • For network issues, ensure your firewall allows connections to the service")
                cli_logger.info("  • For more help, visit: https://github.com/modelcontextprotocol/inspector/issues")

                # Keep the main thread alive
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    cli_logger.info("👋 Stopping example service...")

        except KeyboardInterrupt:
            cli_logger.info("👋 Stopping example service...")
        except Exception as e:
            cli_logger.error(f"❌ Error running example: {e}")
            sys.exit(1)
