import unittest
import os
import sys
import tempfile
import pathlib
import sqlite3

# Ensure the src directory is discoverable for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "src"))

try:
    from mcp_modelservice_sdk.mcp_event_store import (
        MCPEventStore,
        EventType,
        ToolCallEvent,
        ResourceEvent,
        PromptEvent,
    )

    imports_successful = True
except ImportError as e:
    print(f"Could not import event store modules: {e}. Tests will be skipped.")
    imports_successful = False


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestMCPEventStore(unittest.TestCase):
    """Tests for the MCP Event Store functionality."""

    def setUp(self):
        """Set up test environment with temporary database."""
        self.temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_event_store_"))
        self.db_path = self.temp_dir / "test_events.db"
        self.event_store = MCPEventStore(str(self.db_path))

    def tearDown(self):
        """Clean up temporary files."""
        self.event_store.close()
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_event_store_initialization(self):
        """Test that the event store initializes correctly."""
        self.assertTrue(self.db_path.exists())

        # Check that tables are created
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn("events", tables)

    def test_log_tool_call_event(self):
        """Test logging a tool call event."""
        event = ToolCallEvent(
            session_id="test_session",
            tool_name="test_tool",
            arguments={"x": 1, "y": 2},
            result={"sum": 3},
            execution_time_ms=100.5,
        )

        # Log the event
        self.event_store.log_event(event)

        # Verify it was stored
        events = self.event_store.get_events(session_id="test_session")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["tool_name"], "test_tool")

    def test_log_resource_event(self):
        """Test logging a resource event."""
        event = ResourceEvent(
            session_id="test_session",
            resource_uri="file://test.txt",
            operation="read",
            content_preview="Hello, world!",
        )

        # Log the event
        self.event_store.log_event(event)

        # Verify it was stored
        events = self.event_store.get_events(session_id="test_session")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["resource_uri"], "file://test.txt")

    def test_log_prompt_event(self):
        """Test logging a prompt event."""
        event = PromptEvent(
            session_id="test_session",
            prompt_name="test_prompt",
            arguments={"name": "Alice"},
            response="Hello, Alice!",
        )

        # Log the event
        self.event_store.log_event(event)

        # Verify it was stored
        events = self.event_store.get_events(session_id="test_session")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["prompt_name"], "test_prompt")

    def test_get_events_by_session(self):
        """Test retrieving events by session ID."""
        # Log events for different sessions
        event1 = ToolCallEvent(
            session_id="session1", tool_name="tool1", arguments={}, result={}
        )
        event2 = ToolCallEvent(
            session_id="session2", tool_name="tool2", arguments={}, result={}
        )

        self.event_store.log_event(event1)
        self.event_store.log_event(event2)

        # Get events for session1
        session1_events = self.event_store.get_events(session_id="session1")
        self.assertEqual(len(session1_events), 1)
        self.assertEqual(session1_events[0]["tool_name"], "tool1")

        # Get events for session2
        session2_events = self.event_store.get_events(session_id="session2")
        self.assertEqual(len(session2_events), 1)
        self.assertEqual(session2_events[0]["tool_name"], "tool2")

    def test_get_events_by_type(self):
        """Test retrieving events by event type."""
        # Log different types of events
        tool_event = ToolCallEvent(
            session_id="test_session", tool_name="test_tool", arguments={}, result={}
        )
        resource_event = ResourceEvent(
            session_id="test_session", resource_uri="file://test.txt", operation="read"
        )

        self.event_store.log_event(tool_event)
        self.event_store.log_event(resource_event)

        # Get only tool call events
        tool_events = self.event_store.get_events(
            session_id="test_session", event_type=EventType.TOOL_CALL
        )
        self.assertEqual(len(tool_events), 1)
        self.assertEqual(tool_events[0]["event_type"], EventType.TOOL_CALL.value)

        # Get only resource events
        resource_events = self.event_store.get_events(
            session_id="test_session", event_type=EventType.RESOURCE
        )
        self.assertEqual(len(resource_events), 1)
        self.assertEqual(resource_events[0]["event_type"], EventType.RESOURCE.value)

    def test_get_events_with_limit(self):
        """Test retrieving events with a limit."""
        # Log multiple events
        for i in range(5):
            event = ToolCallEvent(
                session_id="test_session",
                tool_name=f"tool_{i}",
                arguments={},
                result={},
            )
            self.event_store.log_event(event)

        # Get events with limit
        events = self.event_store.get_events(session_id="test_session", limit=3)
        self.assertEqual(len(events), 3)

    def test_clear_session_events(self):
        """Test clearing events for a specific session."""
        # Log events for different sessions
        event1 = ToolCallEvent(
            session_id="session1", tool_name="tool1", arguments={}, result={}
        )
        event2 = ToolCallEvent(
            session_id="session2", tool_name="tool2", arguments={}, result={}
        )

        self.event_store.log_event(event1)
        self.event_store.log_event(event2)

        # Clear session1 events
        self.event_store.clear_session_events("session1")

        # Verify session1 events are cleared but session2 events remain
        session1_events = self.event_store.get_events(session_id="session1")
        session2_events = self.event_store.get_events(session_id="session2")

        self.assertEqual(len(session1_events), 0)
        self.assertEqual(len(session2_events), 1)

    def test_event_serialization(self):
        """Test that events are properly serialized and deserialized."""
        complex_args = {"nested": {"key": "value"}, "list": [1, 2, 3], "string": "test"}

        event = ToolCallEvent(
            session_id="test_session",
            tool_name="complex_tool",
            arguments=complex_args,
            result={"status": "success"},
            execution_time_ms=250.75,
        )

        self.event_store.log_event(event)

        # Retrieve and verify
        events = self.event_store.get_events(session_id="test_session")
        self.assertEqual(len(events), 1)

        retrieved_event = events[0]
        self.assertEqual(retrieved_event["arguments"], complex_args)
        self.assertEqual(retrieved_event["execution_time_ms"], 250.75)


if __name__ == "__main__":
    unittest.main()
