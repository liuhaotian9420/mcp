"""
Native FastMCP example: Arithmetic MCP server using streamable HTTP transport.

- Tools: add, subtract, multiply, divide
- Run with: python native_streamable_http_mcp_example.py (serves on HTTP at http://127.0.0.1:8002/mcp)
- Production-grade structure, docstrings, and type hints
"""

from fastmcp import FastMCP
from typing import Dict

mcp = FastMCP("Native Arithmetic MCP (Streamable HTTP)")


@mcp.tool()
def add(a: float, b: float) -> Dict[str, float]:
    """Add two numbers."""
    return {"result": a + b}


@mcp.tool()
def subtract(a: float, b: float) -> Dict[str, float]:
    """Subtract b from a."""
    return {"result": a - b}


@mcp.tool()
def multiply(a: float, b: float) -> Dict[str, float]:
    """Multiply two numbers."""
    return {"result": a * b}


@mcp.tool()
def divide(a: float, b: float) -> Dict[str, float]:
    """Divide a by b. Raises ValueError if b is zero."""
    if b == 0:
        raise ValueError("Divisor 'b' must not be zero.")
    return {"result": a / b}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8002, path="/mcp")
