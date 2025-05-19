"""
Native FastMCP example: Arithmetic MCP server using SSE transport.

- Tools: add, subtract, multiply, divide
- Run with: python native_sse_mcp_example.py (serves on SSE transport at http://127.0.0.1:8001/sse)
- Production-grade structure, docstrings, and type hints
"""

from fastmcp import FastMCP
from typing import Dict

mcp = FastMCP("Native Arithmetic MCP (SSE)")


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
    mcp.run(transport="sse", host="127.0.0.1", port=8001, path="/sse")
