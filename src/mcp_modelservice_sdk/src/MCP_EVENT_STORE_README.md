# Official MCP EventStore Implementation

This module provides a SQLite-based implementation of the official MCP EventStore interface for resumability support in FastMCP HTTP transport.

## Overview

The `SQLiteEventStore` class implements the official MCP EventStore interface defined in the MCP Python SDK, providing:

- **Resumability**: Clients can reconnect and resume from where they left off
- **Event Storage**: JSON-RPC messages are stored with unique event IDs
- **Stream Management**: Events are organized by stream IDs for efficient replay
- **SQLite Persistence**: Reliable, file-based storage with ACID properties

## Key Differences from Legacy EventStore

| Feature | Legacy EventStore (`event_store.py`) | Official EventStore (`mcp_event_store.py`) |
|---------|--------------------------------------|---------------------------------------------|
| **Purpose** | MCP server analytics and tracking | HTTP transport resumability |
| **Interface** | Custom API for tool calls, sessions | Official MCP EventStore interface |
| **Methods** | Synchronous | Asynchronous |
| **Data Model** | Domain-specific tables (tool_calls, sessions) | Simple event streams with JSON-RPC messages |
| **Use Case** | Analytics, history tracking | Client reconnection and message replay |

## Usage

### Basic Setup

```python
from mcp_modelservice_sdk.src.mcp_event_store import SQLiteEventStore

# Create event store with default database path
event_store = SQLiteEventStore()

# Or specify custom database path
event_store = SQLiteEventStore("./my_events.db")
```

### With FastMCP Application

```python
from mcp_modelservice_sdk.src.app_builder import create_mcp_application

app = create_mcp_application(
    source_path_str="./my_functions",
    enable_event_store=True,  # Enable the official MCP EventStore
    event_store_path="./mcp_events.db"  # Optional custom path
)
```

### Manual Event Storage and Replay

```python
import asyncio
from mcp_modelservice_sdk.src.mcp_event_store import SQLiteEventStore, EventMessage

async def example():
    event_store = SQLiteEventStore()
    
    # Store an event
    message = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
    event_id = await event_store.store_event("stream-123", message)
    
    # Replay events after a specific event ID
    def replay_callback(event_message: EventMessage):
        print(f"Replayed: {event_message.message}")
    
    stream_id = await event_store.replay_events_after(event_id, replay_callback)
```

## API Reference

### SQLiteEventStore Class

#### Constructor

```python
SQLiteEventStore(db_path: Optional[Union[str, Path]] = None)
```

- `db_path`: Path to SQLite database file. Defaults to `./mcp_event_store.db`

#### Core Methods (Official Interface)

```python
async def store_event(self, stream_id: StreamId, message: Dict[str, Any]) -> EventId
```
Stores a JSON-RPC message event for later retrieval.

```python
async def replay_events_after(
    self, 
    last_event_id: EventId, 
    send_callback: EventCallback
) -> Optional[StreamId]
```
Replays events that occurred after the specified event ID.

#### Utility Methods

```python
def get_stream_info(self, stream_id: StreamId) -> Optional[Dict[str, Any]]
```
Get information about a specific stream (event count, timestamps, etc.).

```python
def cleanup_old_events(self, days_to_keep: int = 30) -> int
```
Clean up old events to prevent database growth.

```python
def close(self) -> None
```
Close any open resources.

## Database Schema

The SQLite database uses two main tables:

### streams
- `stream_id` (TEXT PRIMARY KEY): Unique identifier for the stream
- `created_at` (TIMESTAMP): When the stream was first created
- `last_event_id` (TEXT): ID of the most recent event in this stream
- `last_activity` (TIMESTAMP): When the stream was last active

### mcp_events
- `event_id` (TEXT PRIMARY KEY): Unique identifier for the event
- `stream_id` (TEXT): Stream this event belongs to
- `message_data` (TEXT): JSON-serialized message content
- `created_at` (TIMESTAMP): When the event was stored
- `sequence_number` (INTEGER): Sequential number within the stream

## Examples

### Running the Demo

```bash
# Run the example application with event store
python src/mcp_modelservice_sdk/src/examples/run_with_mcp_event_store.py
```

### Testing the Implementation

```bash
# Run the test script
python src/mcp_modelservice_sdk/src/examples/test_mcp_event_store.py
```

## Integration with FastMCP

When `enable_event_store=True` is set in `create_mcp_application()`, the system:

1. Creates a `SQLiteEventStore` instance
2. Passes it to `create_streamable_http_app()` from FastMCP
3. Enables resumable HTTP transport with automatic event storage
4. Allows clients to reconnect and resume from their last received event

## Performance Considerations

- **Indexing**: Database includes indexes on `(stream_id, sequence_number)` and `created_at`
- **Cleanup**: Use `cleanup_old_events()` periodically to prevent unlimited growth
- **Connection Pooling**: Each method creates its own SQLite connection (suitable for moderate load)
- **Async Support**: All core methods are async-compatible

## Error Handling

The implementation includes comprehensive error handling:

- Database connection failures are logged and re-raised
- Invalid event IDs in replay operations return `None`
- Callback errors during replay are logged but don't stop the process
- Transaction rollbacks on database errors

## Migration from Legacy EventStore

If you're currently using the legacy `event_store.py`:

1. **Keep both**: The legacy store is for analytics, the new one is for resumability
2. **Rename legacy**: Consider renaming to `MCPAnalyticsStore` to avoid confusion
3. **Update imports**: Change imports from `event_store` to `mcp_event_store` for resumability features

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're importing from `mcp_event_store`, not `event_store`
2. **Database Permissions**: Check write permissions for the database directory
3. **Async Context**: Remember to use `await` with `store_event()` and `replay_events_after()`

### Logging

Enable debug logging to see detailed event store operations:

```python
import logging
logging.getLogger("mcp_event_store").setLevel(logging.DEBUG)
``` 