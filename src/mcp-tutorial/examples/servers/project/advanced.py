import uvicorn
import os
import logging
# Import our custom middleware
import re
from typing import Optional

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from fastmcp.server.http import create_sse_app
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class SSEURLRewriteMiddleware:
    """
    Middleware to rewrite URLs in SSE event streams.
    Fixes path issues where clients receive relative URLs that need to be absolute.
    """
    
    def __init__(self, app, base_url: Optional[str] = None, root_path: Optional[str] = None):
        self.app = app
        # Get base URL from environment or parameter
        self.base_url = base_url or os.getenv('PUBLIC_BASE_URL', '')
        # Get base url's existing root_path
        self.root_path = root_path or os.getenv('root_path', '')
        # Pattern to match SSE data lines with relative URLs
        self.url_pattern = re.compile(r'(data:\s*)(/[^/][^\r\n]*)', re.MULTILINE)
        logger.info(f"SSEURLRewriteMiddleware initialized with root_path: {self.root_path}")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # Only process SSE responses
        request_path = scope.get("path", "")
        logger.info(f"Current request_path: {request_path}")
        if not ("/sse" in request_path or "/mcp" in request_path):
            await self.app(scope, receive, send)
            return
            
        logger.info(f"SSEURLRewriteMiddleware processing request: {request_path}")
            
        # Wrap the send function to intercept and modify SSE responses
        async def rewrite_send(message):
            logger.info(f"Current message: {message}")
            if message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    try:
                        text = body.decode("utf-8")
                        # Check if this looks like SSE data
                        if "data:" in text and self.root_path:
                            logger.info(f"**Current text: {text}")
                            # Rewrite relative URLs to absolute URLs
                            modified_text = self.url_pattern.sub(
                                rf'\1{self.root_path}\2', text
                            )
                            logger.info(f"**Current modified_text: {modified_text}")
                            if modified_text != text:
                                logger.info(f"URL rewrite applied: {text.strip()[:100]}... -> {modified_text.strip()[:100]}...")
                                logger.info(f"The next post request will be sent to: {modified_text}")
                            message = {
                                **message,
                                "body": modified_text.encode("utf-8")
                            }
                    except UnicodeDecodeError:
                        # If we can't decode, pass through unchanged
                        pass
            
            await send(message)
        
        await self.app(scope, receive, rewrite_send)

mcp = FastMCP()

@mcp.tool()
async def hello() -> str:
    return "Hello, world!"

@mcp.tool()
async def get_weather(city: str) -> str:
    """Get weather information for a city."""
    return f"The weather in {city} is sunny and 72°F"

# Health check endpoint
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "advanced-mcp-with-middleware"})

# Configuration
PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', '')

# APP_ROOT_PATH looks like '/app/random_id/v1'
APP_ROOT_PATH = os.getenv('root_path', '/app/v1')
PUBLIC_BASE_URL = PUBLIC_BASE_URL + APP_ROOT_PATH 

logger.info(f"Using PUBLIC_BASE_URL: {PUBLIC_BASE_URL}")

# Create SSE app
sse_app = create_sse_app(
    server=mcp,
    message_path='/random_id/v1/messages',
    sse_path='/random_id/v1/sse',
    middleware=[]
)

# Set up middleware
middleware = []
if PUBLIC_BASE_URL:
    middleware.append(Middleware(SSEURLRewriteMiddleware, 
                                 base_url=PUBLIC_BASE_URL,
                                 root_path=APP_ROOT_PATH))
    logger.info("Added SSEURLRewriteMiddleware to middleware stack")

# Create main app with middleware and proper mount path
main_app = Starlette(
    routes=[
        Route("/health", endpoint=health_check),
        Mount('/mcp-server', app=sse_app)
    ],
    middleware=middleware,
    lifespan=sse_app.router.lifespan_context
)

# create main app with root path
# main_app_with_root_path = Starlette(
#     routes=[
#         Route("/health", endpoint=health_check),
#         Mount(APP_ROOT_PATH, app=main_app)
#     ],
#     # middleware=middleware,
#     lifespan=sse_app.router.lifespan_context
# )

if __name__ == "__main__":
    port = 8080
    logger.info("Starting Advanced MCP service with SSE URL rewrite middleware")
    logger.info(f"Health check: http://127.0.0.1:{port}/health")
    logger.info(f"MCP SSE endpoint: http://127.0.0.1:{port}/mcp-server/sse")
    logger.info(f"MCP messages endpoint: http://127.0.0.1:{port}/mcp-server/messages")
    logger.info(f"URLs will be rewritten with base: {PUBLIC_BASE_URL}")
    
    uvicorn.run(main_app, host="0.0.0.0", port=8080)