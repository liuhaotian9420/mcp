"""
SQLite implementation of the official MCP EventStore interface.
This provides resumability support for FastMCP HTTP transport using SQLite persistence.
"""

import json
import logging
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
from abc import ABC, abstractmethod

# Type aliases matching the official MCP interface
StreamId = str
EventId = str

logger = logging.getLogger(__name__)


class EventMessage:
    """
    A JSONRPCMessage with an optional event ID for stream resumability.
    This matches the EventMessage from the official MCP SDK.
    """

    def __init__(self, message: Dict[str, Any], event_id: Optional[str] = None):
        self.message = message
        self.event_id = event_id


# Type alias for the callback function
EventCallback = Callable[
    [EventMessage], Any
]  # Made non-async for now, can be updated if needed


class EventStore(ABC):
    """
    Interface for resumability support via event storage.
    This matches the official MCP EventStore interface.
    """

    @abstractmethod
    async def store_event(self, stream_id: StreamId, message: Any) -> EventId:
        """
        Stores an event for later retrieval.

        Args:
            stream_id: ID of the stream the event belongs to
            message: The JSON-RPC message to store

        Returns:
            The generated event ID for the stored event
        """
        pass

    @abstractmethod
    async def replay_events_after(
        self,
        last_event_id: EventId,
        send_callback: EventCallback,
    ) -> Optional[StreamId]:
        """
        Replays events that occurred after the specified event ID.

        Args:
            last_event_id: The ID of the last event the client received
            send_callback: A callback function to send events to the client

        Returns:
            The stream ID of the replayed events, or None if no events found
        """
        pass


class SQLiteEventStore(EventStore):
    """
    SQLite implementation of the official MCP EventStore interface.

    This provides resumability support for FastMCP HTTP transport by storing
    JSON-RPC messages with event IDs and allowing replay from a specific point.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        """
        Initialize a SQLite event store.

        Args:
            db_path: Path to the SQLite database file. If None, a default
                    path will be used in the current working directory.
        """
        if db_path is None:
            # Use default path in current working directory
            db_path = Path.cwd() / "mcp_event_store.db"
        else:
            db_path = Path(db_path)

        # Create directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = str(db_path)
        logger.info(f"Initializing SQLite MCP event store at: {self.db_path}")

        # Initialize database
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize the SQLite database schema for MCP event storage."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Create streams table to track active streams
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS streams (
                stream_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_event_id TEXT,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create events table for JSON-RPC message storage
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcp_events (
                event_id TEXT PRIMARY KEY,
                stream_id TEXT NOT NULL,
                message_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sequence_number INTEGER,
                FOREIGN KEY (stream_id) REFERENCES streams(stream_id)
            )
            """)

            # Create index for efficient event ordering and lookup
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_stream_sequence 
            ON mcp_events(stream_id, sequence_number)
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_created_at 
            ON mcp_events(created_at)
            """)

            conn.commit()
            logger.debug("SQLite MCP event store schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing SQLite MCP event store: {e}")
            raise
        finally:
            conn.close()

    async def store_event(self, stream_id: StreamId, message: Any) -> EventId:
        """
        Stores a JSON-RPC message event for later retrieval.

        Args:
            stream_id: ID of the stream the event belongs to
            message: The JSON-RPC message to store (can be dict or JSONRPCMessage object)

        Returns:
            The generated event ID for the stored event
        """
        # Generate a unique event ID
        event_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Ensure stream exists
            cursor.execute(
                "INSERT OR IGNORE INTO streams (stream_id) VALUES (?)", (stream_id,)
            )

            # Get the next sequence number for this stream
            cursor.execute(
                "SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM mcp_events WHERE stream_id = ?",
                (stream_id,),
            )
            sequence_number = cursor.fetchone()[0]

            # Serialize the message - handle both dict and JSONRPCMessage objects
            try:
                if hasattr(message, "model_dump"):
                    # Pydantic model (JSONRPCMessage) - use model_dump()
                    message_data = json.dumps(message.model_dump())
                elif hasattr(message, "dict"):
                    # Pydantic model (older version) - use dict()
                    message_data = json.dumps(message.dict())
                elif isinstance(message, dict):
                    # Already a dictionary
                    message_data = json.dumps(message)
                else:
                    # Try to convert to dict if it has __dict__
                    if hasattr(message, "__dict__"):
                        message_data = json.dumps(message.__dict__)
                    else:
                        # Last resort - convert to string representation
                        message_data = json.dumps(str(message))
            except Exception as serialize_error:
                logger.error(f"Failed to serialize message: {serialize_error}")
                # Fallback to string representation
                message_data = json.dumps(
                    {"error": "serialization_failed", "message": str(message)}
                )

            # Store the event
            cursor.execute(
                """
                INSERT INTO mcp_events (event_id, stream_id, message_data, sequence_number)
                VALUES (?, ?, ?, ?)
                """,
                (event_id, stream_id, message_data, sequence_number),
            )

            # Update stream's last event ID and activity
            cursor.execute(
                """
                UPDATE streams 
                SET last_event_id = ?, last_activity = CURRENT_TIMESTAMP 
                WHERE stream_id = ?
                """,
                (event_id, stream_id),
            )

            conn.commit()
            logger.debug(
                f"Stored event {event_id} for stream {stream_id} (seq: {sequence_number})"
            )
            return event_id

        except Exception as e:
            logger.error(f"Error storing event: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    async def replay_events_after(
        self,
        last_event_id: EventId,
        send_callback: EventCallback,
    ) -> Optional[StreamId]:
        """
        Replays events that occurred after the specified event ID.

        Args:
            last_event_id: The ID of the last event the client received
            send_callback: A callback function to send events to the client

        Returns:
            The stream ID of the replayed events, or None if no events found
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Find the stream and sequence number for the last event ID
            cursor.execute(
                "SELECT stream_id, sequence_number FROM mcp_events WHERE event_id = ?",
                (last_event_id,),
            )
            result = cursor.fetchone()

            if not result:
                logger.warning(f"Event ID {last_event_id} not found")
                return None

            stream_id: str = result[0]
            last_sequence: int = result[1]

            # Get all events after the last sequence number for this stream
            cursor.execute(
                """
                SELECT event_id, message_data 
                FROM mcp_events 
                WHERE stream_id = ? AND sequence_number > ?
                ORDER BY sequence_number ASC
                """,
                (stream_id, last_sequence),
            )

            events_to_replay = cursor.fetchall()

            if not events_to_replay:
                logger.debug(f"No events to replay after {last_event_id}")
                return stream_id

            # Replay events by calling the callback
            replayed_count = 0
            for event_id, message_data in events_to_replay:
                try:
                    message = json.loads(message_data)
                    event_message = EventMessage(message=message, event_id=event_id)

                    # Call the callback - handle both sync and async callbacks
                    if hasattr(send_callback, "__call__"):
                        result = send_callback(event_message)
                        # If it's a coroutine, await it
                        if hasattr(result, "__await__"):
                            await result

                    replayed_count += 1
                    logger.debug(f"Replayed event {event_id}")

                except Exception as e:
                    logger.error(f"Error replaying event {event_id}: {e}")
                    # Continue with other events
                    continue

            logger.info(f"Replayed {replayed_count} events for stream {stream_id}")
            return stream_id

        except Exception as e:
            logger.error(f"Error replaying events: {e}")
            return None
        finally:
            conn.close()

    def get_stream_info(self, stream_id: StreamId) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific stream.

        Args:
            stream_id: The stream ID to get info for

        Returns:
            Dictionary with stream information or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT stream_id, created_at, last_event_id, last_activity,
                       (SELECT COUNT(*) FROM mcp_events WHERE stream_id = ?) as event_count
                FROM streams 
                WHERE stream_id = ?
                """,
                (stream_id, stream_id),
            )
            result = cursor.fetchone()

            if result:
                return {
                    "stream_id": result[0],
                    "created_at": result[1],
                    "last_event_id": result[2],
                    "last_activity": result[3],
                    "event_count": result[4],
                }
            return None

        except Exception as e:
            logger.error(f"Error getting stream info: {e}")
            return None
        finally:
            conn.close()

    def cleanup_old_events(self, days_to_keep: int = 30) -> int:
        """
        Clean up old events to prevent database growth.

        Args:
            days_to_keep: Number of days of events to keep

        Returns:
            Number of events deleted
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Delete old events
            cursor.execute(
                """
                DELETE FROM mcp_events 
                WHERE created_at < datetime('now', '-{} days')
                """.format(days_to_keep)
            )
            deleted_events = cursor.rowcount

            # Clean up streams that have no events
            cursor.execute(
                """
                DELETE FROM streams 
                WHERE stream_id NOT IN (SELECT DISTINCT stream_id FROM mcp_events)
                """
            )
            deleted_streams = cursor.rowcount

            conn.commit()
            logger.info(
                f"Cleaned up {deleted_events} old events and {deleted_streams} empty streams"
            )
            return deleted_events

        except Exception as e:
            logger.error(f"Error cleaning up old events: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

    def close(self) -> None:
        """Close any open resources."""
        # SQLite connections are created per method, so no cleanup needed
        logger.debug("SQLite MCP event store closed")
