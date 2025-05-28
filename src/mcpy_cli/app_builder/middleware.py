"""
Middleware for session management in MCP applications.
"""

import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# Thread-local storage for session context
_session_context = threading.local()


class SessionMiddleware:
    """
    Middleware to extract MCP session ID from request headers and store it in thread-local storage.
    This enables tools to access the current session ID during request processing.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract headers from the ASGI scope
            headers = dict(scope.get("headers", []))

            # Look for the mcp-session-id header (headers are byte strings in ASGI)
            session_id = None
            for name, value in headers.items():
                if name == b"mcp-session-id":
                    session_id = value.decode("utf-8")
                    break

            if session_id:
                # Set the session ID in thread-local storage
                set_current_session_id(session_id)
                logger.debug(
                    f"SessionMiddleware: Set session ID {session_id} for request"
                )
            else:
                logger.debug(
                    "SessionMiddleware: No mcp-session-id header found in request"
                )

            try:
                # Process the request
                await self.app(scope, receive, send)
            finally:
                # Clean up thread-local storage after request processing
                if hasattr(_session_context, "session_id"):
                    delattr(_session_context, "session_id")
                    logger.debug(
                        "SessionMiddleware: Cleaned up session ID from thread-local storage"
                    )
        else:
            # For non-HTTP requests (like WebSocket), just pass through
            await self.app(scope, receive, send)


def get_current_session_id() -> Optional[str]:
    """
    Get the current session ID from thread-local storage.

    Returns:
        The session ID if available, None otherwise.
    """
    session_id = getattr(_session_context, "session_id", None)
    if session_id:
        logger.debug(f"Retrieved session ID from thread-local storage: {session_id}")
    else:
        logger.debug("No session ID found in thread-local storage")
    return session_id


def set_current_session_id(session_id: str) -> None:
    """
    Set the current session ID in thread-local storage.

    Args:
        session_id: The session ID to store.
    """
    logger.debug(f"Setting session ID in thread-local storage: {session_id}")
    _session_context.session_id = session_id
