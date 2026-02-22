#!/usr/bin/env python3
"""Tests for pre-initialize enforcement (strict_init=True)."""

import pytest

from chuk_mcp_server.constants import JsonRpcError, McpMethod
from chuk_mcp_server.protocol import MCPProtocolHandler
from chuk_mcp_server.types.base import ServerCapabilities, ServerInfo


@pytest.fixture
def strict_handler():
    """Create a handler with strict_init=True."""
    info = ServerInfo(name="test", version="1.0")
    caps = ServerCapabilities()
    return MCPProtocolHandler(info, caps, strict_init=True)


@pytest.fixture
def handler():
    """Create a handler with strict_init=False (default)."""
    info = ServerInfo(name="test", version="1.0")
    caps = ServerCapabilities()
    return MCPProtocolHandler(info, caps)


class TestStrictInitEnforcement:
    """Tests that strict_init=True rejects requests on invalid sessions."""

    @pytest.mark.asyncio
    async def test_initialize_allowed_without_session(self, strict_handler):
        """Initialize should work without a session (it creates one)."""
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.INITIALIZE,
            "params": {
                "protocolVersion": "2025-11-25",
                "clientInfo": {"name": "test-client", "version": "1.0"},
                "capabilities": {},
            },
        }
        response, session_id = await strict_handler.handle_request(msg)
        assert "result" in response
        assert session_id is not None

    @pytest.mark.asyncio
    async def test_ping_allowed_without_session(self, strict_handler):
        """Ping should work without a valid session."""
        msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.PING}
        response, _ = await strict_handler.handle_request(msg, session_id="invalid-session")
        assert "result" in response

    @pytest.mark.asyncio
    async def test_tools_list_rejected_with_invalid_session(self, strict_handler):
        """tools/list should be rejected with invalid session when strict."""
        msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.TOOLS_LIST, "params": {}}
        response, _ = await strict_handler.handle_request(msg, session_id="invalid-session")
        assert "error" in response
        assert response["error"]["code"] == JsonRpcError.INVALID_REQUEST
        assert "not initialized" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_tools_call_rejected_with_invalid_session(self, strict_handler):
        """tools/call should be rejected with invalid session when strict."""
        msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": McpMethod.TOOLS_CALL,
            "params": {"name": "test", "arguments": {}},
        }
        response, _ = await strict_handler.handle_request(msg, session_id="invalid-session")
        assert "error" in response
        assert response["error"]["code"] == JsonRpcError.INVALID_REQUEST

    @pytest.mark.asyncio
    async def test_notification_allowed_with_invalid_session(self, strict_handler):
        """Notifications (no msg_id) should pass through even with invalid session."""
        msg = {
            "jsonrpc": "2.0",
            "method": McpMethod.NOTIFICATIONS_CANCELLED,
            "params": {"requestId": "req-999"},
        }
        result, _ = await strict_handler.handle_request(msg, session_id="invalid-session")
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_session_allows_requests(self, strict_handler):
        """After initialize, requests with valid session should work."""
        # First, initialize
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.INITIALIZE,
            "params": {
                "protocolVersion": "2025-11-25",
                "clientInfo": {"name": "test-client", "version": "1.0"},
                "capabilities": {},
            },
        }
        _, session_id = await strict_handler.handle_request(init_msg)
        assert session_id is not None

        # Now tools/list should work with the valid session
        list_msg = {"jsonrpc": "2.0", "id": 2, "method": McpMethod.TOOLS_LIST, "params": {}}
        response, _ = await strict_handler.handle_request(list_msg, session_id=session_id)
        assert "result" in response

    @pytest.mark.asyncio
    async def test_no_session_id_passes_through_strict(self, strict_handler):
        """When session_id is None, strict mode does not block (STDIO compat)."""
        msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.TOOLS_LIST, "params": {}}
        response, _ = await strict_handler.handle_request(msg)
        assert "result" in response


class TestDefaultNonStrict:
    """Tests that strict_init=False (default) does not enforce."""

    @pytest.mark.asyncio
    async def test_tools_list_allowed_with_invalid_session(self, handler):
        """With default strict_init=False, invalid sessions are not rejected."""
        msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.TOOLS_LIST, "params": {}}
        response, _ = await handler.handle_request(msg, session_id="invalid-session")
        assert "result" in response
