#!/usr/bin/env python3
"""Test script to demonstrate SessionToolCallCache functionality."""

import sys
import time

sys.path.insert(0, ".")

from src.mcpy_cli.src.app_builder import (
    SessionToolCallCache,
    set_current_session_id,
)


def expensive_calculation(x: int, y: int) -> int:
    """A function that simulates an expensive calculation."""
    print(f"  🔄 Performing expensive calculation: {x} + {y}")
    time.sleep(0.1)  # Simulate work
    result = x + y
    print(f"  ✅ Calculation complete: {result}")
    return result


def test_cache_functionality():
    """Test the SessionToolCallCache functionality."""
    print("🧪 Testing SessionToolCallCache functionality...\n")

    # Create a cache instance
    cache = SessionToolCallCache()

    # Create a cached version of our function
    cached_expensive_calculation = cache.create_cached_tool(expensive_calculation)

    # Test 1: No session context (should execute directly)
    print("📋 Test 1: No session context")
    result1 = cached_expensive_calculation(5, 3)
    print(f"Result: {result1}\n")

    # Test 2: With session context - first call (cache miss)
    print("📋 Test 2: Session 'user123' - First call (cache miss)")
    set_current_session_id("user123")
    result2 = cached_expensive_calculation(10, 20)
    print(f"Result: {result2}\n")

    # Test 3: Same session, same parameters (cache hit)
    print("📋 Test 3: Session 'user123' - Same parameters (cache hit)")
    result3 = cached_expensive_calculation(10, 20)
    print(f"Result: {result3}\n")

    # Test 4: Same session, different parameters (cache miss)
    print("📋 Test 4: Session 'user123' - Different parameters (cache miss)")
    result4 = cached_expensive_calculation(15, 25)
    print(f"Result: {result4}\n")

    # Test 5: Different session, same parameters (cache miss)
    print("📋 Test 5: Session 'user456' - Same parameters as Test 2 (cache miss)")
    set_current_session_id("user456")
    result5 = cached_expensive_calculation(10, 20)
    print(f"Result: {result5}\n")

    # Test 6: Back to first session, same parameters (cache hit)
    print(
        "📋 Test 6: Back to session 'user123' - Same parameters as Test 2 (cache hit)"
    )
    set_current_session_id("user123")
    result6 = cached_expensive_calculation(10, 20)
    print(f"Result: {result6}\n")

    # Show cache statistics
    stats = cache.get_stats()
    print("📊 Cache Statistics:")
    print(f"  Total sessions: {stats['total_sessions']}")
    print(f"  Total cached entries: {stats['total_cached_entries']}")

    # Test cache clearing
    print("\n🧹 Testing cache clearing...")
    cache.clear_session("user123")
    print("Cleared session 'user123'")

    print("📋 Test 7: Session 'user123' after clearing (cache miss)")
    result7 = cached_expensive_calculation(10, 20)
    print(f"Result: {result7}\n")

    # Final statistics
    final_stats = cache.get_stats()
    print("📊 Final Cache Statistics:")
    print(f"  Total sessions: {final_stats['total_sessions']}")
    print(f"  Total cached entries: {final_stats['total_cached_entries']}")


if __name__ == "__main__":
    test_cache_functionality()
    print("\n✅ Cache functionality test completed!")
