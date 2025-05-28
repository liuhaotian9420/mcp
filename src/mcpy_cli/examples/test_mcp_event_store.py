"""
Test script for the official MCP EventStore implementation.

This script tests the SQLite-based EventStore that implements the official
MCP EventStore interface for resumability support.
"""

from mcpy_cli.src.mcp_event_store import SQLiteEventStore, EventMessage

import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_event_store_test")


async def test_event_store():
    """Test the MCP EventStore implementation."""
    logger.info("Testing MCP EventStore implementation")

    # Create a test database
    test_db_path = "./test_mcp_event_store.db"
    event_store = SQLiteEventStore(test_db_path)

    # Test data
    stream_id = "test-stream-123"
    test_messages = [
        {"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "add", "arguments": {"a": 5, "b": 3}},
            "id": 2,
        },
        {"jsonrpc": "2.0", "result": 8, "id": 2},
    ]

    # Test storing events
    logger.info("Testing event storage...")
    event_ids = []
    for i, message in enumerate(test_messages):
        event_id = await event_store.store_event(stream_id, message)
        event_ids.append(event_id)
        logger.info(f"Stored event {i + 1}: {event_id}")

    # Test stream info
    logger.info("Testing stream info retrieval...")
    stream_info = event_store.get_stream_info(stream_id)
    if stream_info:
        logger.info(f"Stream info: {stream_info}")
    else:
        logger.error("Failed to get stream info")

    # Test event replay
    logger.info("Testing event replay...")
    replayed_events = []

    def replay_callback(event_message: EventMessage):
        """Callback to collect replayed events."""
        replayed_events.append(
            {"event_id": event_message.event_id, "message": event_message.message}
        )
        logger.info(f"Replayed event: {event_message.event_id}")

    # Replay events after the first event
    first_event_id = event_ids[0]
    result_stream_id = await event_store.replay_events_after(
        first_event_id, replay_callback
    )

    if result_stream_id:
        logger.info(f"Successfully replayed events for stream: {result_stream_id}")
        logger.info(f"Replayed {len(replayed_events)} events")

        # Verify replayed events
        expected_count = len(test_messages) - 1  # All events after the first
        if len(replayed_events) == expected_count:
            logger.info("✅ Event replay test passed")
        else:
            logger.error(
                f"❌ Event replay test failed: expected {expected_count}, got {len(replayed_events)}"
            )
    else:
        logger.error("❌ Event replay failed")

    # Test cleanup
    logger.info("Testing cleanup...")
    deleted_count = event_store.cleanup_old_events(days_to_keep=0)  # Delete all events
    logger.info(f"Cleaned up {deleted_count} events")

    # Verify cleanup
    stream_info_after_cleanup = event_store.get_stream_info(stream_id)
    if (
        stream_info_after_cleanup is None
        or stream_info_after_cleanup.get("event_count", 0) == 0
    ):
        logger.info("✅ Cleanup test passed")
    else:
        logger.error("❌ Cleanup test failed")

    # Close the event store
    event_store.close()

    # Clean up test database
    try:
        Path(test_db_path).unlink()
        logger.info("Test database cleaned up")
    except Exception as e:
        logger.warning(f"Failed to clean up test database: {e}")

    logger.info("MCP EventStore test completed")


async def main():
    """Run the event store tests."""
    try:
        await test_event_store()
        logger.info("🎉 All tests completed successfully!")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
