"""
Tool call caching functionality for MCP applications.
"""

import functools
import logging
from typing import Any, Callable, Dict, Optional

from .middleware import get_current_session_id

logger = logging.getLogger(__name__)


class SessionToolCallCache:
    """
    Simple in-memory cache for tool call results per session.
    Used in stateful + JSON response mode to cache tool call results.
    """

    def __init__(self):
        self._cache: Dict[
            str, Dict[str, Any]
        ] = {}  # session_id -> {tool_call_key -> result}
        logger.info("Initialized SessionToolCallCache for stateful JSON response mode")

    def get_cache_key(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Generate a cache key from tool name and arguments."""
        import json
        import hashlib

        # Create a deterministic key from tool name and sorted args
        args_str = json.dumps(tool_args, sort_keys=True, default=str)
        key_data = f"{tool_name}:{args_str}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(
        self, session_id: str, tool_name: str, tool_args: Dict[str, Any]
    ) -> Optional[Any]:
        """Get cached result for a tool call in a specific session."""
        if session_id not in self._cache:
            return None

        cache_key = self.get_cache_key(tool_name, tool_args)
        result = self._cache[session_id].get(cache_key)

        if result is not None:
            logger.info(f"Cache hit for session {session_id}, tool {tool_name}")

        return result

    def set(
        self, session_id: str, tool_name: str, tool_args: Dict[str, Any], result: Any
    ) -> None:
        """Cache a tool call result for a specific session."""
        if session_id not in self._cache:
            self._cache[session_id] = {}

        cache_key = self.get_cache_key(tool_name, tool_args)
        self._cache[session_id][cache_key] = result

        logger.info(f"Cached result for session {session_id}, tool {tool_name}")

    def clear_session(self, session_id: str) -> None:
        """Clear all cached results for a specific session."""
        if session_id in self._cache:
            del self._cache[session_id]
            logger.debug(f"Cleared cache for session {session_id}")

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        total_sessions = len(self._cache)
        total_entries = sum(
            len(session_cache) for session_cache in self._cache.values()
        )
        return {"total_sessions": total_sessions, "total_cached_entries": total_entries}

    def create_cached_tool(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Create a cached version of a tool function."""

        @functools.wraps(func)
        def cached_wrapper(*args, **kwargs):
            # Get current session ID
            session_id = get_current_session_id()

            if session_id is None:
                # No session context, execute function directly
                logger.info(
                    f"No session context for {func.__name__}, executing directly"
                )
                return func(*args, **kwargs)

            # Check cache first
            cached_result = self.get(session_id, func.__name__, kwargs)
            if cached_result is not None:
                logger.info(f"Cache hit for {func.__name__} in session {session_id}")
                return cached_result

            # Execute function and cache result
            logger.info(
                f"Cache miss for {func.__name__} in session {session_id}, executing function"
            )
            result = func(*args, **kwargs)

            # Cache the result
            self.set(session_id, func.__name__, kwargs, result)
            logger.info(f"Cached result for {func.__name__} in session {session_id}")

            return result

        return cached_wrapper
