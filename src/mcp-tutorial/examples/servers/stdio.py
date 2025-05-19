"""
Native FastMCP example: Arithmetic MCP server using stdio transport.

- Tools: add, subtract, multiply, divide
- Run with: python native_stdio_mcp_example.py (uses stdio transport by default)
- Production-grade structure, docstrings, and type hints
"""

from fastmcp import FastMCP
from typing import Dict

mcp = FastMCP("Native Arithmetic MCP (stdio)")


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
    mcp.run(transport="stdio")
