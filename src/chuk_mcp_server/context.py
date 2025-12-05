"""
Request context management for MCP servers.

Provides thread-safe, async-safe context storage for request-scoped data including:
- Session ID (MCP session identifier)
- User ID (OAuth user identifier)
- Progress token (for progress notifications)
- Custom metadata

Inspired by chuk-mcp-runtime's MCPRequestContext pattern.

Usage:
    # In protocol handler (server framework)
    from chuk_mcp_server.context import RequestContext, set_session_id, set_user_id

    async with RequestContext(session_id="abc123", user_id="user456"):
        # Context is available throughout request lifecycle
        await handle_tool_call()

    # In application code (tools, resources, etc.)
    from chuk_mcp_server.context import get_session_id, get_user_id, require_user_id

    @mcp.tool()
    async def my_tool():
        user_id = require_user_id()  # Raises if not authenticated
        session_id = get_session_id()  # Returns None if not in session
        ...
"""

from contextvars import ContextVar
from typing import Any

from starlette.types import Scope

# ============================================================================
# Context Variables
# ============================================================================

_session_id: ContextVar[str | None] = ContextVar("session_id", default=None)
_user_id: ContextVar[str | None] = ContextVar("user_id", default=None)
_progress_token: ContextVar[str | int | None] = ContextVar("progress_token", default=None)
_metadata: ContextVar[dict[str, Any] | None] = ContextVar("metadata", default=None)
_http_request: ContextVar[Scope | None] = ContextVar("http_request", default=None)


# ============================================================================
# Context Manager
# ============================================================================


class RequestContext:
    """
    Async context manager for MCP request context lifecycle.

    Automatically manages context setup and cleanup for request handling.
    Supports nested contexts (inner context takes precedence).

    Example:
        async with RequestContext(session_id="abc123", user_id="user456"):
            # Context is set for this block
            user_id = get_user_id()  # Returns "user456"
            ...
        # Context is restored to previous state
    """

    def __init__(
        self,
        session_id: str | None = None,
        user_id: str | None = None,
        progress_token: str | int | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize request context.

        Args:
            session_id: MCP session identifier
            user_id: OAuth user identifier
            progress_token: Progress notification token
            metadata: Additional request metadata
        """
        self.session_id = session_id
        self.user_id = user_id
        self.progress_token = progress_token
        self.metadata = metadata or {}

        # Store previous context for restoration
        self._previous_session_id: str | None = None
        self._previous_user_id: str | None = None
        self._previous_progress_token: str | int | None = None
        self._previous_metadata: dict[str, Any] | None = None

    async def __aenter__(self) -> "RequestContext":
        """Enter context - save previous and set new values."""
        # Save previous context
        self._previous_session_id = _session_id.get()
        self._previous_user_id = _user_id.get()
        self._previous_progress_token = _progress_token.get()
        prev_metadata = _metadata.get()
        self._previous_metadata = prev_metadata.copy() if prev_metadata is not None else None

        # Set new context
        if self.session_id is not None:
            _session_id.set(self.session_id)
        if self.user_id is not None:
            _user_id.set(self.user_id)
        if self.progress_token is not None:
            _progress_token.set(self.progress_token)
        if self.metadata:
            _metadata.set(self.metadata)

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Exit context - restore previous values."""
        # Restore previous context
        _session_id.set(self._previous_session_id)
        _user_id.set(self._previous_user_id)
        _progress_token.set(self._previous_progress_token)
        _metadata.set(self._previous_metadata)

        return False  # Don't suppress exceptions


# ============================================================================
# Session Context Functions
# ============================================================================


def get_session_id() -> str | None:
    """
    Get current MCP session ID.

    Returns:
        Session ID if set, None otherwise
    """
    return _session_id.get()


def set_session_id(session_id: str | None) -> None:
    """
    Set current MCP session ID.

    Args:
        session_id: Session identifier
    """
    _session_id.set(session_id)


def require_session_id() -> str:
    """
    Require a session ID to be set in context.

    Returns:
        Session ID string

    Raises:
        RuntimeError: If no session is active
    """
    session_id = _session_id.get()
    if not session_id:
        raise RuntimeError("Session context required. This function must be called within an active MCP session.")
    return session_id


# ============================================================================
# User Context Functions
# ============================================================================


def get_user_id() -> str | None:
    """
    Get current OAuth user ID.

    Returns:
        User ID if authenticated, None otherwise
    """
    return _user_id.get()


def set_user_id(user_id: str | None) -> None:
    """
    Set current OAuth user ID.

    Args:
        user_id: User identifier from OAuth
    """
    _user_id.set(user_id)


def require_user_id() -> str:
    """
    Require a user ID to be set in context.

    Useful for tools/resources that require authentication.

    Returns:
        User ID string

    Raises:
        PermissionError: If no user is authenticated
    """
    user_id = _user_id.get()
    if not user_id:
        raise PermissionError(
            "User authentication required. "
            "This operation requires an authenticated user context. "
            "Ensure OAuth authentication is configured and the user is logged in."
        )
    return user_id


# ============================================================================
# Progress Token Functions
# ============================================================================


def get_progress_token() -> str | int | None:
    """
    Get current progress token for notifications.

    Returns:
        Progress token if set, None otherwise
    """
    return _progress_token.get()


def set_progress_token(token: str | int | None) -> None:
    """
    Set current progress token.

    Args:
        token: Progress notification token
    """
    _progress_token.set(token)


# ============================================================================
# Metadata Functions
# ============================================================================


def get_metadata() -> dict[str, Any]:
    """
    Get current request metadata.

    Returns:
        Metadata dictionary (copy to prevent mutation)
    """
    metadata = _metadata.get()
    return metadata.copy() if metadata is not None else {}


def set_metadata(metadata: dict[str, Any]) -> None:
    """
    Set current request metadata.

    Args:
        metadata: Request metadata dictionary
    """
    _metadata.set(metadata.copy())


def update_metadata(key: str, value: Any) -> None:
    """
    Update a single metadata key.

    Args:
        key: Metadata key
        value: Metadata value
    """
    current_meta = _metadata.get()
    current = current_meta.copy() if current_meta is not None else {}
    current[key] = value
    _metadata.set(current)


def clear_metadata() -> None:
    """Clear all metadata."""
    _metadata.set(None)


# ============================================================================
# Context Utilities
# ============================================================================


def clear_all() -> None:
    """
    Clear all context variables.

    Useful for testing or cleanup.
    """
    _session_id.set(None)
    _user_id.set(None)
    _progress_token.set(None)
    _metadata.set(None)
    _http_request.set(None)


def get_current_context() -> dict[str, Any]:
    """
    Get all current context values.

    Returns:
        Dictionary with all context values
    """
    current_meta = _metadata.get()
    return {
        "session_id": _session_id.get(),
        "user_id": _user_id.get(),
        "progress_token": _progress_token.get(),
        "metadata": current_meta.copy() if current_meta is not None else {},
    }


# ============================================================================
# HTTP Request Context Functions
# ============================================================================


def get_http_request() -> Scope | None:
    """
    Get current http request

    Returns:
        HTTP Request object
    """
    return _http_request.get()


def set_http_request(request: Scope) -> None:
    """
    Set current http request

    Args:
        request: HTTP Request object
    """
    _http_request.set(request)


# ============================================================================
# Convenience Aliases (for backward compatibility)
# ============================================================================

# These aliases maintain compatibility with existing code
set_current_user = set_user_id
get_current_user_id = require_user_id  # Note: This raises if not set, matching old behavior
