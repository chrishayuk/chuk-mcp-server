"""Tests for SSE proxy transport - with proper mocking."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSseProxyTransport:
    """Test SSE proxy transport."""

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    def test_init_with_url(self, mock_sse, mock_httpx):
        """Test initialization with URL."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        config = {
            "url": "http://example.com",
            "sse_path": "/events",
            "message_path": "/msg",
            "timeout": 60,
            "headers": {"X-Custom": "value"},
        }

        transport = SseProxyTransport("test_server", config)

        assert transport.server_name == "test_server"
        assert transport.base_url == "http://example.com"
        assert transport.sse_path == "/events"
        assert transport.message_path == "/msg"
        assert transport.timeout == 60

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    def test_init_without_url(self, mock_sse, mock_httpx):
        """Test initialization without URL raises error."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        with pytest.raises(ValueError, match="requires 'url'"):
            SseProxyTransport("test", {})

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    def test_init_defaults(self, mock_sse, mock_httpx):
        """Test initialization with defaults."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        transport = SseProxyTransport("test", {"url": "http://test.com"})

        assert transport.sse_path == "/sse"
        assert transport.message_path == "/message"
        assert transport.timeout == 30.0

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_sse, mock_httpx):
        """Test successful connection."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_client.stream.return_value = mock_stream
        mock_httpx.AsyncClient.return_value = mock_client

        transport = SseProxyTransport("test", {"url": "http://test.com"})
        result = await transport.connect()

        assert result is True
        assert transport.client == mock_client

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_sse, mock_httpx):
        """Test connection failure."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_httpx.AsyncClient.side_effect = Exception("Failed")

        transport = SseProxyTransport("test", {"url": "http://test.com"})
        result = await transport.connect()

        assert result is False

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_disconnect(self, mock_sse, mock_httpx):
        """Test disconnection."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.aclose = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_stream)
        mock_httpx.AsyncClient.return_value = mock_client

        transport = SseProxyTransport("test", {"url": "http://test.com"})
        await transport.connect()

        transport.session_id = "test-session"
        await transport.disconnect()

        assert transport.client is None
        assert transport.session_id is None
        mock_client.aclose.assert_called_once()

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_initialize(self, mock_sse, mock_httpx):
        """Test session initialization."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_client.stream.return_value = mock_stream
        mock_client.post = AsyncMock()
        mock_httpx.AsyncClient.return_value = mock_client

        with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = {"status": "ok"}

            transport = SseProxyTransport("test", {"url": "http://test.com"})
            await transport.connect()

            result = await transport.initialize()

            assert transport.session_id is not None
            assert result == {"status": "ok"}

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_initialize_not_connected(self, mock_sse, mock_httpx):
        """Test initialize when not connected."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        transport = SseProxyTransport("test", {"url": "http://test.com"})

        with pytest.raises(RuntimeError, match="not connected"):
            await transport.initialize()

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_call_tool(self, mock_sse, mock_httpx):
        """Test calling a tool."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_client.stream.return_value = mock_stream
        mock_client.post = AsyncMock()
        mock_httpx.AsyncClient.return_value = mock_client

        with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = {"output": "test"}

            transport = SseProxyTransport("test", {"url": "http://test.com"})
            await transport.connect()
            transport.session_id = "test-session"

            result = await transport.call_tool("test_tool", {"arg": "value"})

            assert result == {"output": "test"}

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_list_tools(self, mock_sse, mock_httpx):
        """Test listing tools."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_client.stream.return_value = mock_stream
        mock_client.post = AsyncMock()
        mock_httpx.AsyncClient.return_value = mock_client

        with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = {"tools": []}

            transport = SseProxyTransport("test", {"url": "http://test.com"})
            await transport.connect()

            result = await transport.list_tools()

            assert result == {"tools": []}

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_send_request_timeout(self, mock_sse, mock_httpx):
        """Test send_request with timeout."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_client.stream.return_value = mock_stream
        mock_client.post = AsyncMock()
        mock_httpx.AsyncClient.return_value = mock_client

        with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
            mock_wait.side_effect = TimeoutError()

            transport = SseProxyTransport("test", {"url": "http://test.com"})
            await transport.connect()

            with pytest.raises(RuntimeError, match="timeout"):
                await transport.send_request("test_method")

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self, mock_httpx):
        """Test call_tool when not connected."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        transport = SseProxyTransport("test", {"url": "http://test.com"})

        with pytest.raises(RuntimeError, match="not connected"):
            await transport.call_tool("test_tool", {})

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @pytest.mark.asyncio
    async def test_list_tools_not_connected(self, mock_httpx):
        """Test list_tools when not connected."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        transport = SseProxyTransport("test", {"url": "http://test.com"})

        with pytest.raises(RuntimeError, match="not connected"):
            await transport.list_tools()

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_send_request_error_handling(self, mock_sse, mock_httpx):
        """Test send_request error handling."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_stream)
        mock_client.post = AsyncMock(side_effect=Exception("Test error"))
        mock_httpx.AsyncClient.return_value = mock_client

        transport = SseProxyTransport("test", {"url": "http://test.com"})
        await transport.connect()

        with pytest.raises(Exception, match="Test error"):
            await transport.send_request("test_method")

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_disconnect_handles_none(self, mock_sse, mock_httpx):
        """Test disconnect when not connected."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        transport = SseProxyTransport("test", {"url": "http://test.com"})
        # Should not raise
        await transport.disconnect()

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_send_request_with_session_id(self, mock_sse, mock_httpx):
        """Test send_request includes session ID."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_stream)
        mock_client.post = AsyncMock()
        mock_httpx.AsyncClient.return_value = mock_client

        with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = {"result": "ok"}

            transport = SseProxyTransport("test", {"url": "http://test.com"})
            await transport.connect()
            transport.session_id = "test-session"

            await transport.send_request("test_method")

            # Verify session ID header
            call_args = mock_client.post.call_args
            assert call_args[1]["headers"]["Mcp-Session-Id"] == "test-session"

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_disconnect_with_stream(self, mock_sse, mock_httpx):
        """Test disconnect with active stream."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.aclose = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_stream)
        mock_httpx.AsyncClient.return_value = mock_client

        transport = SseProxyTransport("test", {"url": "http://test.com"})
        await transport.connect()

        # Manually set sse_connection to test disconnect
        transport.sse_connection = mock_stream
        transport.session_id = "test-session"

        await transport.disconnect()

        assert transport.sse_connection is None
        mock_stream.aclose.assert_called_once()

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_send_request_increments_id(self, mock_sse, mock_httpx):
        """Test request ID increments."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_stream)
        mock_client.post = AsyncMock()
        mock_httpx.AsyncClient.return_value = mock_client

        with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = {"result": "ok"}

            transport = SseProxyTransport("test", {"url": "http://test.com"})
            await transport.connect()
            transport.session_id = "test-session"

            await transport.send_request("method1")
            await transport.send_request("method2")

            assert transport.request_id == 2

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx_sse")
    @pytest.mark.asyncio
    async def test_connect_with_custom_paths(self, mock_sse, mock_httpx):
        """Test connection with custom SSE and message paths."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        mock_client = AsyncMock()
        mock_stream = AsyncMock()
        mock_client.stream.return_value = mock_stream
        mock_httpx.AsyncClient.return_value = mock_client

        config = {
            "url": "http://test.com",
            "sse_path": "/custom/sse",
            "message_path": "/custom/message",
        }

        transport = SseProxyTransport("test", config)
        assert transport.sse_path == "/custom/sse"
        assert transport.message_path == "/custom/message"

        result = await transport.connect()
        assert result is True

    @patch("chuk_mcp_server.proxy.transports.sse_transport.httpx")
    @pytest.mark.asyncio
    async def test_send_request_not_connected(self, mock_httpx):
        """Test send_request when not connected."""
        from chuk_mcp_server.proxy.transports.sse_transport import SseProxyTransport

        transport = SseProxyTransport("test", {"url": "http://test.com"})

        with pytest.raises(RuntimeError, match="not connected"):
            await transport.send_request("test_method")
