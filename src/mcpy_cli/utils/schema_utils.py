"""Utilities for schema generation and type handling."""

from functools import lru_cache
from typing import TypeVar

from pydantic import TypeAdapter

T = TypeVar("T")


@lru_cache(maxsize=5000)
def get_cached_typeadapter(cls: T) -> TypeAdapter[T]:
    """
    Returns a cached TypeAdapter for the given class or callable.

    TypeAdapters are heavy objects, and in an application context we'd typically
    create them once in a global scope and reuse them as often as possible.
    However, this isn't feasible for user-generated functions. Instead, we use a
    cache to minimize the cost of creating them as much as possible.

    Args:
        cls: The class or callable to create a TypeAdapter for

    Returns:
        A cached TypeAdapter instance
    """
    return TypeAdapter(cls)
