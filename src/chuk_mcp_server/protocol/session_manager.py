#!/usr/bin/env python3
# src/chuk_mcp_server/protocol/session_manager.py
"""
MCP session lifecycle management.

Manages creation, eviction, and cleanup of MCP protocol sessions.
"""

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage MCP sessions."""

    def __init__(
        self,
        max_sessions: int = 1000,
        cleanup_interval: int = 100,
        on_evict: Callable[[str], None] | None = None,
        protected_sessions: Callable[[], set[str]] | None = None,
    ):
        self.sessions: dict[str, dict[str, Any]] = {}
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        self._creation_count = 0
        self._on_evict = on_evict
        self._protected_sessions = protected_sessions

    def _evict_session(self, session_id: str) -> None:
        """Evict a session, calling the on_evict callback first."""
        if self._on_evict is not None:
            self._on_evict(session_id)
        del self.sessions[session_id]

    def create_session(self, client_info: dict[str, Any], protocol_version: str) -> str:
        """Create a new session."""
        self._creation_count += 1

        # Periodic cleanup of expired sessions
        if self._creation_count % self.cleanup_interval == 0:
            self.cleanup_expired()

        # Evict oldest session if at capacity
        if len(self.sessions) >= self.max_sessions:
            protected = self._protected_sessions() if self._protected_sessions else set()
            candidates = [sid for sid in self.sessions if sid not in protected]
            if candidates:
                oldest_sid = min(candidates, key=lambda sid: self.sessions[sid]["last_activity"])
                self._evict_session(oldest_sid)
                logger.debug(f"Evicted oldest session {oldest_sid[:8]}... (max_sessions reached)")

        session_id = str(uuid.uuid4()).replace("-", "")
        self.sessions[session_id] = {
            "id": session_id,
            "client_info": client_info,
            "protocol_version": protocol_version,
            "created_at": time.time(),
            "last_activity": time.time(),
        }
        logger.debug(f"Created session {session_id[:8]}... for {client_info.get('name', 'unknown')}")
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def update_activity(self, session_id: str) -> None:
        """Update session last activity."""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = time.time()

    def cleanup_expired(self, max_age: int = 3600) -> None:
        """Remove expired sessions."""
        now = time.time()
        expired = [sid for sid, session in self.sessions.items() if now - session["last_activity"] > max_age]
        for sid in expired:
            self._evict_session(sid)
            logger.debug(f"Cleaned up expired session {sid[:8]}...")
