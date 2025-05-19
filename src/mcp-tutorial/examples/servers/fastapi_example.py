"""
A FastAPI-MCP example service exposing simple arithmetic operations as MCP tools.

- Endpoints: /add, /subtract, /multiply, /divide
- Each endpoint is ready for LLM integration and TDD
- Production-grade structure, docstrings, and type hints
"""
import os

from fastapi import FastAPI, Query
from pydantic import BaseModel
from pydantic.networks import AnyUrl
from fastapi_mcp import FastApiMCP
from typing import Any, Dict, List, AsyncIterable
from mcp.types import (
    GetPromptResult,
    PromptMessage,
    TextContent,
    Resource,
    ResourceTemplate,
    Prompt,
    TextResourceContents,
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create logger for this module
logger = logging.getLogger(__name__)




class Log(BaseModel):
    mime_type: str = "text/plain"
    content: str


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application with arithmetic endpoints.
    Returns:
        FastAPI: The configured FastAPI app instance.
    """
    root_path = os.getenv("root_path", "")
    app = FastAPI(
        title="MCP Arithmetic Service",
        description="A FastAPI-MCP example for arithmetic operations.",
        root_path=root_path,
    )

    @app.get("/", response_model=Dict[str, Any], operation_id="root", tags=["health"])
    async def root() -> Dict[str, Any]:
        """
        Root endpoint listing available routes for verification.
        Returns:
            dict: Service status and list of mounted route paths
        """
        routes = [
            getattr(route, "path") for route in app.routes if hasattr(route, "path")
        ]
        return {"status": "running", "routes": routes}

    @app.post(
        "/add", response_model=Dict[str, float], operation_id="add", tags=["arithmetic"]
    )
    async def add(
        a: float = Query(..., description="First operand"),
        b: float = Query(..., description="Second operand"),
    ) -> Dict[str, float]:
        """
        Add two numbers.
        Args:
            a (float): First operand
            b (float): Second operand
        Returns:
            dict: The sum of a and b
        """
        logger.info(f"Adding {a} and {b}")
        return {"result": a + b}

    @app.get(
        "/subtract",
        response_model=Dict[str, float],
        operation_id="subtract",
        tags=["arithmetic"],
    )
    async def subtract(
        a: float = Query(..., description="Minuend"),
        b: float = Query(..., description="Subtrahend"),
    ) -> Dict[str, float]:
        """
        Subtract b from a.
        Args:
            a (float): Minuend
            b (float): Subtrahend
        Returns:
            dict: The result of a - b
        """
        logger.info(f"Subtracting {b} from {a}")
        return {"result": a - b}

    @app.get(
        "/multiply",
        response_model=Dict[str, float],
        operation_id="multiply",
        tags=["arithmetic"],
    )
    async def multiply(
        a: float = Query(..., description="First operand"),
        b: float = Query(..., description="Second operand"),
    ) -> Dict[str, float]:
        """
        Multiply two numbers.
        Args:
            a (float): First operand
            b (float): Second operand
        Returns:
            dict: The product of a and b
        """
        logger.info(f"Multiplying {a} and {b}")
        return {"result": a * b}

    @app.get(
        "/divide",
        response_model=Dict[str, float],
        operation_id="divide",
        tags=["arithmetic"],
    )
    async def divide(
        a: float = Query(..., description="Dividend"),
        b: float = Query(..., description="Divisor, must not be zero"),
    ) -> Dict[str, float]:
        """
        Divide a by b.
        Args:
            a (float): Dividend
            b (float): Divisor (must not be zero)
        Returns:
            dict: The result of a / b
        Raises:
            ValueError: If b is zero
        """
        if b == 0:
            logger.error("Attempted division by zero.")
            raise ValueError("Divisor 'b' must not be zero.")
        logger.info(f"Dividing {a} by {b}")
        return {"result": a / b}

    return app


def configure_mcp(app: FastAPI) -> FastApiMCP:
    """
    Configure and mount the FastApiMCP server on the given FastAPI app.
    Args:
        app (FastAPI): The FastAPI app instance.
    Returns:
        FastApiMCP: The configured and mounted MCP server.
    """
    mcp = FastApiMCP(
        app,
        name="MCP Arithmetic Service",
        description="A FastAPI-MCP example exposing arithmetic operations.",
        describe_all_responses=True,
        describe_full_response_schema=True,
    )

    @mcp.server.list_prompts()
    async def list_prompts() -> List[Prompt]:
        return [Prompt(name="summarize", description="Summarize a block of text")]

    @mcp.server.list_resources()
    async def list_resources() -> List[Resource]:
        return [
            Resource(
                uri=AnyUrl("http://localhost:8080/logs"),  # type: ignore
                name="logs",
            ),
            Resource(
                uri=AnyUrl("file:///logs/app.log"),  # type: ignore
                name="app.log",
            ),
        ]

    @mcp.server.read_resource()
    async def read_resource(uri: AnyUrl) -> AsyncIterable[TextResourceContents]:
        if str(uri) == "file:///logs/app.log":
            yield TextResourceContents(uri=uri, text="logs!!!!!!!!!", mimeType="text/plain")
            yield TextResourceContents(uri=uri, text="logs!?!!!", mimeType="text/plain")
            return
        raise ValueError(f"Unknown resource: {uri}")

    @mcp.server.list_resource_templates()
    async def list_resource_templates() -> List[ResourceTemplate]:
        return [
            ResourceTemplate(
                uriTemplate=str(AnyUrl("http://localhost:8080/logs")),  # type: ignore
                name="logs",
                description="The logs file",
            ),
            ResourceTemplate(
                uriTemplate=str(AnyUrl("file:///logs/app.log")),  # type: ignore
                name="app.log",
                description="The application log file",
            ),
        ]

    @mcp.server.get_prompt()
    async def get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> GetPromptResult:
        if name == "summarize":
            text = arguments or {}
            return GetPromptResult(
                messages=[
                    PromptMessage(
                        role="assistant",
                        content=TextContent(
                            type="text", text="You are a helpful assistant."
                        ),
                    ),
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=text.get("text", "")),
                    ),
                ]
            )
        raise ValueError(f"Unknown prompt: {name}")

    mcp.mount()
    return mcp


app = create_app()
mcp = configure_mcp(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fastapi_mcp_example:app", host="0.0.0.0", port=8080)
