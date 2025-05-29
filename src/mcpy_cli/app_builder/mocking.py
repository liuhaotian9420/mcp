"""
Mock FastMCP implementation for testing purposes.
"""

import sys
from typing import Any, TYPE_CHECKING, Union
from starlette.applications import Starlette


# Mock FastMCP class for testing when the library is not installed
class MockFastMCP:
    """Mock FastMCP class for use when real FastMCP is not available."""

    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "MockFastMCP")
        self.instructions = kwargs.get("instructions", None)
        self.tools = {}

    def tool(self, name=None):
        """Mock decorator that simply returns the function unchanged."""

        def decorator(func):
            self.tools[name or func.__name__] = func
            return func

        return decorator

    def http_app(self, path=None, transport=None, middleware=None):
        """Return a mock app."""
        return Starlette()

    def mount(self, prefix, app, **kwargs):
        """Mock mount method."""
        return None


# For type checking, always create a FastMCP type
if TYPE_CHECKING:
    # Only imported for type checking
    from fastmcp import FastMCP as RealFastMCP

    FastMCPType = Union[RealFastMCP, MockFastMCP]
else:
    FastMCPType = Any


# Try to import FastMCP, use MockFastMCP if not available
def get_fastmcp_class():
    """Get the FastMCP class, using mock if real one is not available."""
    try:
        from fastmcp import FastMCP

        return FastMCP
    except ImportError:
        # Only for testing purposes - real code needs fastmcp installed
        if "unittest" not in sys.modules and "pytest" not in sys.modules:
            raise ImportError(
                "FastMCP is not installed. Please install it to use this SDK. "
                "You can typically install it using: pip install fastmcp"
            )
        return MockFastMCP
