#!/usr/bin/env python3
# src/chuk_mcp_server/protocol/events.py
"""
SSE event buffering for MCP Streamable HTTP resumability.

Manages per-session SSE event IDs and buffers for Last-Event-ID replay.
"""

from typing import Any


class SSEEventBuffer:
    """Manages SSE event IDs and buffering for session resumability."""

    def __init__(self, max_buffer_size: int = 100) -> None:
        self._buffers: dict[str, list[tuple[int, dict[str, Any]]]] = {}
        self._counters: dict[str, int] = {}
        self._max_buffer_size = max_buffer_size

    def next_event_id(self, session_id: str) -> int:
        """Get next SSE event ID for a session."""
        counter = self._counters.get(session_id, 0) + 1
        self._counters[session_id] = counter
        return counter

    def buffer_event(self, session_id: str, event_id: int, data: dict[str, Any]) -> None:
        """Buffer an SSE event for resumability."""
        buf = self._buffers.setdefault(session_id, [])
        buf.append((event_id, data))
        if len(buf) > self._max_buffer_size:
            self._buffers[session_id] = buf[-self._max_buffer_size :]

    def get_missed_events(self, session_id: str, last_event_id: int) -> list[tuple[int, dict[str, Any]]]:
        """Get events after the given event ID for resumability."""
        buf = self._buffers.get(session_id, [])
        return [(eid, data) for eid, data in buf if eid > last_event_id]

    def cleanup_session(self, session_id: str) -> None:
        """Remove all event data for a session."""
        self._buffers.pop(session_id, None)
        self._counters.pop(session_id, None)
