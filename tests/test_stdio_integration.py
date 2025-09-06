#!/usr/bin/env python3
"""
Integration tests for stdio transport mode.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from chuk_mcp_server.core import ChukMCPServer
from chuk_mcp_server.protocol import MCPProtocolHandler
from chuk_mcp_server.stdio_transport import StdioTransport


class TestStdioIntegration:
    """Integration tests for stdio transport with full server."""

    @pytest.fixture
    def server(self):
        """Create a test server with tools."""
        server = ChukMCPServer(name="test-server", version="1.0.0", description="Test server for stdio integration")

        @server.tool("echo")
        def echo(message: str) -> str:
            """Echo the message."""
            return f"Echo: {message}"

        @server.tool("add")
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        @server.resource("test://data")
        def test_data() -> dict:
            """Get test data."""
            return {"test": "data", "value": 123}

        return server

    @pytest.mark.asyncio
    async def test_full_stdio_communication(self, server):
        """Test full stdio communication flow."""
        # Use the server's protocol directly
        protocol = server.protocol
        transport = StdioTransport(protocol)

        # Mock stdin and stdout
        stdin_data = [
            b'{"jsonrpc":"2.0","method":"initialize","params":{"clientInfo":{"name":"test"}},"id":1}\n',
            b'{"jsonrpc":"2.0","method":"tools/list","id":2}\n',
            b'{"jsonrpc":"2.0","method":"tools/call","params":{"name":"echo","arguments":{"message":"hello"}},"id":3}\n',
            b"",  # EOF
        ]

        responses = []

        # Capture stdout writes
        def capture_write(data):
            responses.append(json.loads(data.rstrip("\n")))

        # Mock the writer for capturing output
        transport.writer = MagicMock()
        transport.writer.write = capture_write
        transport.writer.flush = MagicMock()

        # Process messages directly without starting the transport
        await transport._handle_message(stdin_data[0].decode().strip())
        await transport._handle_message(stdin_data[1].decode().strip())
        await transport._handle_message(stdin_data[2].decode().strip())

        # Verify responses
        assert len(responses) == 3

        # Check initialize response
        assert responses[0]["id"] == 1
        assert "result" in responses[0]
        assert "capabilities" in responses[0]["result"]

        # Check tools/list response
        assert responses[1]["id"] == 2
        assert "result" in responses[1]
        tools = responses[1]["result"]["tools"]
        # Filter out only the tools we expect from this test
        tool_names = [t["name"] for t in tools]
        assert "echo" in tool_names
        assert "add" in tool_names

        # Check tool call response
        assert responses[2]["id"] == 3
        assert "result" in responses[2]
        assert responses[2]["result"]["content"][0]["text"] == "Echo: hello"

    @pytest.mark.asyncio
    async def test_stdio_with_resources(self, server):
        """Test stdio communication with resource requests."""
        # Use the server's protocol directly
        protocol = server.protocol
        transport = StdioTransport(protocol)

        responses = []

        def capture_write(data):
            responses.append(json.loads(data.rstrip("\n")))

        with patch.object(transport, "writer") as mock_writer:
            mock_writer.write = capture_write
            mock_writer.flush = MagicMock()

            # Initialize session
            await transport._handle_message(
                json.dumps(
                    {"jsonrpc": "2.0", "method": "initialize", "params": {"clientInfo": {"name": "test"}}, "id": 1}
                )
            )

            # List resources
            await transport._handle_message(json.dumps({"jsonrpc": "2.0", "method": "resources/list", "id": 2}))

            # Read resource
            await transport._handle_message(
                json.dumps({"jsonrpc": "2.0", "method": "resources/read", "params": {"uri": "test://data"}, "id": 3})
            )

        # Check resources/list response
        assert responses[1]["id"] == 2
        resources = responses[1]["result"]["resources"]
        assert len(resources) == 1
        assert resources[0]["uri"] == "test://data"

        # Check resource read response
        assert responses[2]["id"] == 3
        content = responses[2]["result"]["contents"][0]
        data = json.loads(content["text"])
        assert data["test"] == "data"
        assert data["value"] == 123

    @pytest.mark.asyncio
    async def test_stdio_error_handling(self, server):
        """Test error handling in stdio mode."""
        # Use the server's protocol directly
        protocol = server.protocol
        transport = StdioTransport(protocol)

        responses = []

        def capture_write(data):
            responses.append(json.loads(data.rstrip("\n")))

        with patch.object(transport, "writer") as mock_writer:
            mock_writer.write = capture_write
            mock_writer.flush = MagicMock()

            # Send invalid JSON
            await transport._handle_message("not valid json {")

            # Send unknown method
            await transport._handle_message(json.dumps({"jsonrpc": "2.0", "method": "unknown/method", "id": 2}))

            # Send tool call with missing arguments
            await transport._handle_message(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {"name": "add"},  # Missing arguments
                        "id": 3,
                    }
                )
            )

        # Check parse error
        assert responses[0]["error"]["code"] == -32700
        assert "Parse error" in responses[0]["error"]["message"]

        # Additional error checks would depend on protocol implementation

    @pytest.mark.asyncio
    async def test_stdio_concurrent_requests(self, server):
        """Test handling multiple concurrent requests."""
        # Use the server's protocol directly
        protocol = server.protocol
        transport = StdioTransport(protocol)

        responses = []

        def capture_write(data):
            responses.append(json.loads(data.rstrip("\n")))

        with patch.object(transport, "writer") as mock_writer:
            mock_writer.write = capture_write
            mock_writer.flush = MagicMock()

            # Initialize
            await transport._handle_message(
                json.dumps(
                    {"jsonrpc": "2.0", "method": "initialize", "params": {"clientInfo": {"name": "test"}}, "id": 1}
                )
            )

            # Send multiple requests
            messages = [
                json.dumps({"jsonrpc": "2.0", "method": "tools/list", "id": 2}),
                json.dumps({"jsonrpc": "2.0", "method": "resources/list", "id": 3}),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {"name": "add", "arguments": {"a": 5, "b": 3}},
                        "id": 4,
                    }
                ),
            ]

            # Process all messages
            for msg in messages:
                await transport._handle_message(msg)

        # Verify all responses received
        assert len(responses) == 4  # init + 3 requests

        # Check response IDs match requests
        response_ids = [r["id"] for r in responses]
        assert 1 in response_ids
        assert 2 in response_ids
        assert 3 in response_ids
        assert 4 in response_ids

    @pytest.mark.asyncio
    async def test_stdio_notification_handling(self, server):
        """Test handling of notifications (no response expected)."""
        # Use the server's protocol directly
        protocol = server.protocol
        transport = StdioTransport(protocol)

        responses = []

        def capture_write(data):
            responses.append(json.loads(data.rstrip("\n")))

        with patch.object(transport, "writer") as mock_writer:
            mock_writer.write = capture_write
            mock_writer.flush = MagicMock()

            # Send notification (no id field)
            await transport._handle_message(
                json.dumps({"jsonrpc": "2.0", "method": "notifications/progress", "params": {"progress": 50}})
            )

            # Send request with id
            await transport._handle_message(json.dumps({"jsonrpc": "2.0", "method": "tools/list", "id": 1}))

        # Should only have one response (for the request, not the notification)
        assert len(responses) == 1
        assert responses[0]["id"] == 1

    def test_server_stdio_mode_run(self, server):
        """Test running server in stdio mode."""

        with patch("chuk_mcp_server.stdio_transport.run_stdio_server") as mock_run_stdio:
            # Patch the import in core module
            with patch.dict(
                "sys.modules", {"chuk_mcp_server.stdio_transport": MagicMock(run_stdio_server=mock_run_stdio)}
            ):
                server.run(stdio=True)

                mock_run_stdio.assert_called_once()
                # Verify protocol handler was passed
                protocol_arg = mock_run_stdio.call_args[0][0]
                assert isinstance(protocol_arg, MCPProtocolHandler)
