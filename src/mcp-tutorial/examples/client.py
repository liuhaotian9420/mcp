"""
Client examples for connecting to native FastMCP servers.

This script demonstrates how to use the fastmcp.Client to connect to:
1. The stdio arithmetic server (native_stdio_mcp_example.py)
2. The SSE arithmetic server (native_sse_mcp_example.py)
3. The Streamable HTTP arithmetic server (native_streamable_http_mcp_example.py)

To run these examples:
- Ensure the respective server script is running in a separate terminal.
  - For stdio, no separate server run is needed if it's in the same directory or correct path.
- This client script can then be executed.
"""

import asyncio
from fastmcp import Client
from mcp.types import TextContent
from fastmcp.client.transports import SSETransport  # For explicit SSE


async def run_stdio_client():
    """Connects to the native_stdio_mcp_example.py server."""
    print("--- Running Stdio Client Example ---")
    # Assumes native_stdio_mcp_example.py is in the same directory or accessible in PATH
    # If it's in a different relative path, adjust the path string.
    # For example: Client("src/mcp_project/examples/native_stdio_mcp_example.py")
    # For simplicity, this example assumes it's discoverable as 'native_stdio_mcp_example.py'
    try:
        async with Client("native_stdio_mcp_example.py") as client:
            print(f"Connected to Stdio server: {client}")
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")

            # Test add tool
            add_result = await client.call_tool("add", {"a": 10, "b": 5})
            if add_result and isinstance(add_result[0], TextContent):
                print(f"add(10, 5) = {add_result[0].text}")
            else:
                print(f"add(10, 5) expected TextContent, got: {add_result}")

            # Test divide tool
            divide_result = await client.call_tool("divide", {"a": 10, "b": 2})
            if divide_result and isinstance(divide_result[0], TextContent):
                print(f"divide(10, 2) = {divide_result[0].text}")
            else:
                print(f"divide(10, 2) expected TextContent, got: {divide_result}")

            # Test division by zero
            try:
                await client.call_tool("divide", {"a": 10, "b": 0})
            except Exception as e:
                print(f"divide(10, 0) correctly raised: {type(e).__name__} - {e}")
        print("Stdio client finished.")
    except Exception as e:
        print(f"Error connecting to or using stdio server: {e}")
        print(
            "Ensure 'native_stdio_mcp_example.py' is executable and in the correct path."
        )


async def run_sse_client():
    """Connects to the native_sse_mcp_example.py server (must be running)."""
    print("\n--- Running SSE Client Example ---")
    # Server runs at http://127.0.0.1:8001/sse
    sse_url = "http://127.0.0.1:8001/sse"
    try:
        # FastMCP client defaults to StreamableHttpTransport for http/https URLs.
        # For SSE, we must explicitly use SSETransport.
        async with Client(transport=SSETransport(sse_url)) as client:
            print(f"Connected to SSE server: {client}")
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")

            add_result = await client.call_tool("add", {"a": 20, "b": 5})
            if add_result and isinstance(add_result[0], TextContent):
                print(f"add(20, 5) = {add_result[0].text}")
            else:
                print(f"add(20, 5) expected TextContent, got: {add_result}")
        print("SSE client finished.")
    except Exception as e:
        print(f"Error connecting to or using SSE server: {e}")
        print(f"Ensure 'native_sse_mcp_example.py' is running on {sse_url}.")


async def run_streamable_http_client():
    """Connects to the native_streamable_http_mcp_example.py server (must be running)."""
    print("\n--- Running Streamable HTTP Client Example ---")
    # Server runs at http://127.0.0.1:8002/mcp
    http_url = "http://127.0.0.1:8002/mcp"
    try:
        # For streamable-http, Client infers StreamableHttpTransport from the URL
        async with Client(http_url) as client:
            print(f"Connected to Streamable HTTP server: {client}")
            tools = await client.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")

            multiply_result = await client.call_tool("multiply", {"a": 7, "b": 6})
            if multiply_result and isinstance(multiply_result[0], TextContent):
                print(f"multiply(7, 6) = {multiply_result[0].text}")
            else:
                print(f"multiply(7, 6) expected TextContent, got: {multiply_result}")
        print("Streamable HTTP client finished.")
    except Exception as e:
        print(f"Error connecting to or using Streamable HTTP server: {e}")
        print(
            f"Ensure 'native_streamable_http_mcp_example.py' is running on {http_url}."
        )


async def main():
    # Run stdio client first as it doesn't require a separate server process to be manually started
    # (if the script is in the right place)
    await run_stdio_client()

    print(
        "\nNOTE: For SSE and Streamable HTTP examples, ensure the corresponding servers are running."
    )
    print("You can run them with:")
    print("  python src/mcp_project/examples/native_sse_mcp_example.py")
    print("  python src/mcp_project/examples/native_streamable_http_mcp_example.py")
    input("Press Enter to continue after starting SSE and HTTP servers...")

    await run_sse_client()
    await run_streamable_http_client()


if __name__ == "__main__":
    asyncio.run(main())
