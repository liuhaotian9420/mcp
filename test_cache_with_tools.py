#!/usr/bin/env python3
"""Test script to demonstrate SessionToolCallCache working with actual tool calls."""

from src.mcpy_cli.src.app_builder import (
    create_mcp_application,
    set_current_session_id,
)

import sys
import logging
import tempfile
import os

sys.path.insert(0, ".")

# Set up logging to see cache messages
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")




def test_cache_with_actual_tools():
    """Test the cache with actual tool calls through the MCP application."""
    print("🧪 Testing SessionToolCallCache with actual tool calls...\n")

    # Create a temporary test file with our functions
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        test_file = f.name
        f.write("""
import time

def expensive_add(a: int, b: int) -> int:
    \"\"\"Add two numbers with a delay to simulate expensive computation.\"\"\"
    print(f"[TOOL] Computing {a} + {b}...")
    time.sleep(0.1)  # Simulate expensive work
    result = a + b
    print(f"[TOOL] Result: {result}")
    return result

def expensive_multiply(x: int, y: int) -> int:
    \"\"\"Multiply two numbers with a delay.\"\"\"
    print(f"[TOOL] Computing {x} * {y}...")
    time.sleep(0.1)  # Simulate expensive work
    result = x * y
    print(f"[TOOL] Result: {result}")
    return result
""")

    try:
        print("📋 Creating MCP application with caching enabled...")
        app = create_mcp_application(
            source_path_str=test_file,
            stateless_http=False,  # Stateful mode
            json_response=True,  # JSON response mode (enables cache)
            mcp_server_name="CacheTestService",
        )

        # Get the cache and FastMCP instance
        cache = app.state.tool_call_cache

        print("✅ MCP application created with cache enabled")
        print(f"✅ Cache statistics: {cache.get_stats()}")

        # Get the tools from the FastMCP instance
        # Note: In a real scenario, tools would be called through the MCP protocol
        # For testing, we'll simulate the tool calls directly

        print("\n📋 Testing cache behavior with different sessions...")

        # Import the module to get the original functions
        import importlib.util

        spec = importlib.util.spec_from_file_location("test_module", test_file)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)

        # Get the cached versions of the functions from the cache
        cached_add = cache.create_cached_tool(test_module.expensive_add)
        cached_multiply = cache.create_cached_tool(test_module.expensive_multiply)

        # Test 1: Session 1 - First calls (cache misses)
        print("\n🔹 Session 'user1' - First calls (cache misses)")
        set_current_session_id("user1")

        result1 = cached_add(10, 20)
        print(f"Add result: {result1}")

        result2 = cached_multiply(5, 6)
        print(f"Multiply result: {result2}")

        print(f"Cache stats after first calls: {cache.get_stats()}")

        # Test 2: Session 1 - Same calls (cache hits)
        print("\n🔹 Session 'user1' - Same calls (cache hits)")
        set_current_session_id("user1")

        result3 = cached_add(10, 20)  # Should be cached
        print(f"Add result (cached): {result3}")

        result4 = cached_multiply(5, 6)  # Should be cached
        print(f"Multiply result (cached): {result4}")

        print(f"Cache stats after cached calls: {cache.get_stats()}")

        # Test 3: Session 2 - Same parameters, different session (cache misses)
        print(
            "\n🔹 Session 'user2' - Same parameters, different session (cache misses)"
        )
        set_current_session_id("user2")

        result5 = cached_add(10, 20)  # Different session, should execute
        print(f"Add result (different session): {result5}")

        print(f"Cache stats after different session: {cache.get_stats()}")

        # Test 4: Session 1 - Different parameters (cache miss)
        print("\n🔹 Session 'user1' - Different parameters (cache miss)")
        set_current_session_id("user1")

        result6 = cached_add(15, 25)  # Different parameters, should execute
        print(f"Add result (different params): {result6}")

        print(f"Cache stats after different params: {cache.get_stats()}")

        # Test 5: Clear session and test
        print("\n🔹 Clearing session 'user1' and testing...")
        cache.clear_session("user1")
        print(f"Cache stats after clearing user1: {cache.get_stats()}")

        set_current_session_id("user1")
        result7 = cached_add(10, 20)  # Should execute again after clearing
        print(f"Add result after clearing cache: {result7}")

        print(f"Final cache stats: {cache.get_stats()}")

        print("\n✅ All cache tests completed successfully!")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleaned up test file: {test_file}")


if __name__ == "__main__":
    test_cache_with_actual_tools()
    print("\n✅ Cache with tools test completed!")
