"""
Native FastMCP advanced example: MCP server integrated into a Starlette ASGI application.

- Demonstrates mounting FastMCP within a larger Starlette app.
- Includes an asynchronous tool that yields progress updates (streaming).
- MCP endpoint typically at /mcp-server/mcp (configurable).
- Run with: python native_advanced_asgi_mcp_example.py
- Production-grade structure, docstrings, and type hints
"""

import uvicorn
import time
import asyncio
from typing import Dict, Any, AsyncIterator  # Changed Iterator to AsyncIterator
from fastmcp import FastMCP

from starlette.applications import Starlette
from starlette.routing import Mount

import logging

# Configure basic logging for the example
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)  # Use current module name for logger
fastmcp_logger = logging.getLogger("fastmcp")  # Access fastmcp's logger if needed
fastmcp_logger.setLevel(logging.INFO)  # Or DEBUG for more verbosity from fastmcp


# Create your FastMCP server
# The name is for identification, e.g., in logs or client server_info
mcp = FastMCP("AdvancedASGI_MCP_Server")

# Define the root path where the MCP server will be mounted within Starlette
# and the path for the MCP app itself. Endpoint: server_root_path + mcp_base_path
server_root_path = "/mcp-server"  # Root for the MCP service group
mcp_base_path = "/mcp"  # Base path for MCP protocol endpoints (tools, resources etc)




@mcp.tool()
def hello(name: str) -> str:
    """A simple synchronous tool that returns a greeting."""
    logger.info(f"Tool 'hello' called with name={name!r}")
    return f"Hello, {name}! This is your Advanced ASGI MCP Server speaking."


@mcp.tool()
async def a_long_tool_call(seconds: int = 5) -> AsyncIterator[Dict[str, Any]]:
    """
    A long-running asynchronous tool that yields progress updates.

    Args:
        seconds (int): Approximate number of seconds the tool will run for.

    Yields:
        Dict[str, Any]: A dictionary containing progress information at each step.
    """
    logger.info(f"Tool 'a_long_tool_call' started with duration: {seconds}s")

    total_steps = max(1, seconds * 2)  # Ensure at least 1 step, 2 steps per second
    for step in range(1, total_steps + 1):
        await asyncio.sleep(0.5)  # Simulate work for half a second

        progress_percentage = (step / total_steps) * 100
        yield {
            "step": step,
            "total_steps": total_steps,
            "progress_percentage": round(progress_percentage, 2),
            "status": "in_progress" if step < total_steps else "complete",
            "message": f"Processing step {step} of {total_steps}...",
        }

    logger.info("Tool 'a_long_tool_call' completed")


@mcp.tool()
def get_server_time() -> Dict[str, Any]:
    """
    A tool that returns the current server time and a static message.

    Returns:
        Dict[str, Any]: A dictionary with server time information.
    """
    logger.info("Tool 'get_server_time' called")
    return {
        "success": True,
        "timestamp_utc": time.time(),
        "readable_time_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "message": "Time from the Advanced ASGI MCP server.",
    }

# Create the ASGI app from FastMCP, specifying its internal base path
mcp_asgi_app = mcp.http_app(path="",transport="sse")


# Create the main Starlette application
app = Starlette(
    routes=[
        # Mount the FastMCP ASGI application under the defined server_root_path
        Mount(server_root_path, app=mcp_asgi_app),
        # You can add other Starlette routes, Mounts, or WebSockets here
        # e.g., Route("/health", endpoint=health_check_function)
    ],
    # The lifespan context from mcp_asgi_app handles setup/teardown for FastMCP components
    lifespan=mcp_asgi_app.router.lifespan_context,
)

if __name__ == "__main__":
    port = 8080
    logger.info("Starting Advanced ASGI MCP service.")
    logger.info(
        f"MCP tools will be available under: http://127.0.0.1:{port}{server_root_path}{mcp_base_path}"
    )
    logger.info(
        f"  e.g., list_tools might be POST to http://127.0.0.1:{port}{server_root_path}{mcp_base_path}/list_tools"
    )

    uvicorn.run(
        mcp_asgi_app,  # Run the main Starlette app
        host="0.0.0.0",
        port=port,
        log_level="info",  # Uvicorn's log level, can be different from app loggers
    )
