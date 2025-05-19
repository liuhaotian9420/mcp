import asyncio
import logging
import httpx
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
import mcp.types as mcp_types  # Renamed to avoid conflict if types is used locally

# Configure logging to see debug messages from the SDK and our script
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Optionally, set mcp client's logger to DEBUG for more verbose output
# logging.getLogger("mcp.client").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_mcp_sse_server(url: str, headers: dict | None = None):
    logger.info(f"Attempting to connect to MCP SSE server at {url}")
    if headers:
        logger.info(f"Using headers: {headers}")

    try:
        async with sse_client(
            url, headers=headers or {}, timeout=10, sse_read_timeout=60
        ) as (read_stream, write_stream):
            logger.info("SSE transport connected. Initializing ClientSession...")
            async with ClientSession(read_stream, write_stream) as session:
                try:
                    init_response = await session.initialize(
                        # You can specify capabilities your client supports if needed
                        # capabilities=mcp_types.ClientCapabilities(...)
                    )
                    logger.info(
                        f"ClientSession initialized successfully. Server capabilities: {init_response.capabilities}"
                    )

                    logger.info("Attempting to list available tools...")
                    tools_result = await session.list_tools()
                    if tools_result and tools_result.tools:
                        logger.info(f"Available tools ({len(tools_result.tools)}):")
                        for tool in tools_result.tools:
                            logger.info(
                                f"  - Name: {tool.name}, Description: {tool.description}"
                            )
                    else:
                        logger.info(
                            "No tools reported by the server or tools list is empty."
                        )

                    # Add other test interactions here if needed:
                    # e.g., list prompts, get a specific prompt, call a tool
                    # logger.info("Attempting to list available prompts...")
                    # prompts = await session.list_prompts()
                    # logger.info(f"Available prompts: {prompts}")

                except httpx.HTTPStatusError as e:
                    logger.error(
                        f"HTTP error during SSE connection or request: {e.response.status_code} - {e.response.text}",
                        exc_info=True,
                    )
                except httpx.RequestError as e:
                    logger.error(f"HTTP request error: {e}", exc_info=True)
                except Exception as e:
                    logger.error(
                        f"An error occurred during client session of type {type(e).__name__}: {e}",
                        exc_info=True,
                    )
                    if hasattr(e, "error") and isinstance(e.error, mcp_types.ErrorData):
                        logger.error(
                            f"MCP error details: Code: {e.error.code}, Message: {e.error.message}, Data: {e.error.data}"
                        )
                    elif hasattr(e, "data") and isinstance(e.data, mcp_types.ErrorData):
                        logger.error(
                            f"MCP error details (from e.data): Code: {e.data.code}, Message: {e.data.message}, Data: {e.data.data}"
                        )
            logger.info("ClientSession closed.")
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to establish SSE connection (HTTP status): {e.response.status_code} - {e.response.text}",
            exc_info=True,
        )
        logger.error(
            "Check if the server URL is correct, accessible, and returns a successful status for SSE setup."
        )
    except httpx.RequestError as e:  # Catches ConnectError, ReadTimeout, etc.
        logger.error(
            f"Failed to establish SSE connection (Request error): {e}", exc_info=True
        )
        logger.error(
            "Check network connectivity, server availability, and if the URL is correct."
        )
    except ConnectionRefusedError as e:
        logger.error(f"Connection refused by the server at {url}: {e}", exc_info=True)
        logger.error(
            "Ensure the server is running and listening on the specified port, and not blocked by a firewall."
        )
    except ValueError as e:  # Can be raised by sse_client for origin mismatch
        logger.error(f"ValueError during SSE client setup: {e}", exc_info=True)
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while setting up or running the SSE client: {e}",
            exc_info=True,
        )
    finally:
        logger.info(f"Finished test attempt for {url}")


if __name__ == "__main__":
    # Replace with your problematic URL
    URL = "https://www.heywhale.com/api/model/services/681ae2dea013f76c73fed13e/app/mcp"
    # If your server expects custom headers (e.g. auth), add them here:
    HEADERS = {
        "Accept": "text/event-stream",  # Standard for SSE
        # "Authorization": "Bearer your_token_here",
        # "X-Custom-Header": "value"
    }

    # To test a local server (replace port if different)
    # URL = "http://localhost:8000/sse" # Example for a local server if you have one running
    # HEADERS = {"Accept": "text/event-stream"}

    asyncio.run(test_mcp_sse_server(URL, headers=HEADERS))
