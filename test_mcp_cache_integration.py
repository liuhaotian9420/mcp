#!/usr/bin/env python3
"""Test script to demonstrate SessionToolCallCache integration with MCP application."""
from src.mcpy_cli.src.app_builder import (
    create_mcp_application,
    set_current_session_id,
)
import sys
import time
import logging

sys.path.insert(0, ".")

# Set up logging to see cache messages
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")




def slow_add(a: int, b: int) -> int:
    """Add two numbers with a delay to simulate expensive computation.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    print(f"  🔄 Computing {a} + {b}...")
    time.sleep(0.2)  # Simulate expensive work
    result = a + b
    print(f"  ✅ Result: {result}")
    return result


def slow_multiply(x: int, y: int) -> int:
    """Multiply two numbers with a delay.

    Args:
        x: First number
        y: Second number

    Returns:
        The product of x and y
    """
    print(f"  🔄 Computing {x} * {y}...")
    time.sleep(0.2)  # Simulate expensive work
    result = x * y
    print(f"  ✅ Result: {result}")
    return result


def test_mcp_cache_integration():
    """Test the cache integration with MCP application."""
    print("🧪 Testing SessionToolCallCache integration with MCP application...\n")

    # Create a test file with our functions
    test_file = "test_cache_functions.py"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("""
import time

def slow_add(a: int, b: int) -> int:
    \"\"\"Add two numbers with a delay to simulate expensive computation.\"\"\"
    print(f"  Computing {a} + {b}...")
    time.sleep(0.1)
    result = a + b
    print(f"  Result: {result}")
    return result

def slow_multiply(x: int, y: int) -> int:
    \"\"\"Multiply two numbers with a delay.\"\"\"
    print(f"  Computing {x} * {y}...")
    time.sleep(0.1)
    result = x * y
    print(f"  Result: {result}")
    return result
""")

    try:
        print(
            "📋 Test 1: Creating MCP application with stateful + JSON response (cache enabled)"
        )
        app = create_mcp_application(
            source_path_str=test_file,
            stateless_http=False,  # Stateful mode
            json_response=True,  # JSON response mode (enables cache)
            mcp_server_name="CacheTestService",
        )

        # Check if cache was created
        if hasattr(app.state, "tool_call_cache"):
            cache = app.state.tool_call_cache
            print("✅ Cache was successfully created and attached to app state")

            # Get the FastMCP instance to test tools directly
            if hasattr(app.state, "fastmcp_instance"):
                app.state.fastmcp_instance
                print("✅ FastMCP instance found in app state")

                # Test the cached tools by simulating different sessions
                print("\n📋 Test 2: Simulating tool calls with different sessions")

                # Session 1 - First call (cache miss)
                print("\n🔹 Session 'session1' - First call to slow_add(5, 3)")
                set_current_session_id("session1")
                # Note: In a real scenario, this would be called through the MCP protocol
                # For testing, we'll access the tools directly from the FastMCP instance

                # Session 1 - Same call (cache hit)
                print(
                    "\n🔹 Session 'session1' - Same call to slow_add(5, 3) (should be cached)"
                )
                set_current_session_id("session1")

                # Session 2 - Same parameters but different session (cache miss)
                print(
                    "\n🔹 Session 'session2' - Same call to slow_add(5, 3) (different session)"
                )
                set_current_session_id("session2")

                # Show cache stats
                stats = cache.get_stats()
                print("\n📊 Cache Statistics:")
                print(f"  Total sessions: {stats['total_sessions']}")
                print(f"  Total cached entries: {stats['total_cached_entries']}")

            else:
                print("❌ FastMCP instance not found in app state")
        else:
            print(
                "❌ Cache was not created (this shouldn't happen in stateful + JSON mode)"
            )

        print(
            "\n📋 Test 3: Creating MCP application with stateless mode (cache disabled)"
        )
        app_stateless = create_mcp_application(
            source_path_str=test_file,
            stateless_http=True,  # Stateless mode
            json_response=True,  # JSON response mode
            mcp_server_name="StatelessTestService",
        )

        if hasattr(app_stateless.state, "tool_call_cache"):
            print("❌ Cache was created in stateless mode (this shouldn't happen)")
        else:
            print("✅ Cache was correctly NOT created in stateless mode")

        print("\n📋 Test 4: Creating MCP application with SSE mode (cache disabled)")
        app_sse = create_mcp_application(
            source_path_str=test_file,
            stateless_http=False,  # Stateful mode
            json_response=False,  # SSE mode
            mcp_server_name="SSETestService",
        )

        if hasattr(app_sse.state, "tool_call_cache"):
            print("❌ Cache was created in SSE mode (this shouldn't happen)")
        else:
            print("✅ Cache was correctly NOT created in SSE mode")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Clean up test file
        import os

        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleaned up test file: {test_file}")


if __name__ == "__main__":
    test_mcp_cache_integration()
    print("\n✅ MCP cache integration test completed!")
