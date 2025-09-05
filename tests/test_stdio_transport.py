#!/usr/bin/env python3
"""
Tests for stdio transport functionality.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chuk_mcp_server.protocol import MCPProtocolHandler
from chuk_mcp_server.stdio_transport import StdioTransport


@pytest.fixture
def mock_protocol():
    """Create a mock protocol handler."""
    protocol = MagicMock(spec=MCPProtocolHandler)
    protocol.session_manager = MagicMock()
    protocol.session_manager.create_session = MagicMock(return_value="test-session-123")
    protocol.handle_request = AsyncMock(
        return_value=({"jsonrpc": "2.0", "id": 1, "result": {"test": "response"}}, None)
    )
    return protocol


@pytest.fixture
def stdio_transport(mock_protocol):
    """Create a stdio transport instance."""
    return StdioTransport(mock_protocol)


class TestStdioTransport:
    """Test stdio transport functionality."""

    def test_initialization(self, stdio_transport, mock_protocol):
        """Test transport initialization."""
        assert stdio_transport.protocol == mock_protocol
        assert stdio_transport.reader is None
        assert stdio_transport.writer is None
        assert stdio_transport.running is False
        assert stdio_transport.session_id is None

    @pytest.mark.asyncio
    async def test_handle_initialize_message(self, stdio_transport, mock_protocol):
        """Test handling of initialize message."""
        message = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {"clientInfo": {"name": "test-client"}, "protocolVersion": "2025-03-26"},
                "id": 1,
            }
        )

        # Mock stdout
        with patch.object(stdio_transport, "writer") as mock_writer:
            mock_writer.write = MagicMock()
            mock_writer.flush = MagicMock()

            await stdio_transport._handle_message(message)

            # Verify session creation
            mock_protocol.session_manager.create_session.assert_called_once_with({"name": "test-client"}, "2025-03-26")

            # Verify request handling
            mock_protocol.handle_request.assert_called_once()

            # Verify response sent
            mock_writer.write.assert_called_once()
            response_data = mock_writer.write.call_args[0][0]
            assert '"result"' in response_data
            assert response_data.endswith("\n")

    @pytest.mark.asyncio
    async def test_handle_tool_call(self, stdio_transport, mock_protocol):
        """Test handling of tool call message."""
        message = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "echo", "arguments": {"message": "hello"}},
                "id": 2,
            }
        )

        with patch.object(stdio_transport, "writer") as mock_writer:
            mock_writer.write = MagicMock()
            mock_writer.flush = MagicMock()

            await stdio_transport._handle_message(message)

            # Verify request handling
            mock_protocol.handle_request.assert_called_once()
            call_args = mock_protocol.handle_request.call_args[0][0]
            assert call_args["method"] == "tools/call"
            assert call_args["params"]["name"] == "echo"

    @pytest.mark.asyncio
    async def test_handle_notification(self, stdio_transport, mock_protocol):
        """Test handling of notification (no id, no response expected)."""
        message = json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/log", "params": {"level": "info", "message": "test log"}}
        )

        # For notifications, handle_request returns (None, None)
        mock_protocol.handle_request.return_value = (None, None)

        with patch.object(stdio_transport, "writer") as mock_writer:
            mock_writer.write = MagicMock()

            await stdio_transport._handle_message(message)

            # Verify request was handled
            mock_protocol.handle_request.assert_called_once()

            # Verify no response sent for notification
            mock_writer.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_invalid_json(self, stdio_transport):
        """Test handling of invalid JSON."""
        message = "not valid json {"

        with patch.object(stdio_transport, "_send_error") as mock_send_error:
            await stdio_transport._handle_message(message)

            # Verify error response sent
            mock_send_error.assert_called_once()
            error_args = mock_send_error.call_args[0]
            assert error_args[0] is None  # no request id
            assert error_args[1] == -32700  # Parse error code
            assert "Parse error" in error_args[2]

    @pytest.mark.asyncio
    async def test_send_error(self, stdio_transport):
        """Test sending error response."""
        with patch.object(stdio_transport, "writer") as mock_writer:
            mock_writer.write = MagicMock()
            mock_writer.flush = MagicMock()

            await stdio_transport._send_error(123, -32603, "Internal error")

            # Verify error response format
            mock_writer.write.assert_called_once()
            response = mock_writer.write.call_args[0][0]
            data = json.loads(response.rstrip("\n"))

            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 123
            assert data["error"]["code"] == -32603
            assert data["error"]["message"] == "Internal error"

    def test_context_manager(self, stdio_transport):
        """Test context manager interface."""
        with stdio_transport as transport:
            assert transport == stdio_transport
