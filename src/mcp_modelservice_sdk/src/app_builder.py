"""
Module for building the MCP Starlette application with multi-mount architecture.
Each Python file will be mounted as a separate FastMCP instance under a route
derived from its directory structure.

This module now imports from the new modular structure for better maintainability.
"""

# Import from the new modular app_builder structure
from ..app_builder import (
    create_mcp_application,
    SessionMiddleware,
    get_current_session_id,
    set_current_session_id,
    SessionToolCallCache,
)

# Import utilities
from ..utils import TransformationError

# Re-export for backward compatibility
__all__ = [
    "create_mcp_application",
    "SessionMiddleware", 
    "get_current_session_id",
    "set_current_session_id",
    "SessionToolCallCache",
    "TransformationError",
] 