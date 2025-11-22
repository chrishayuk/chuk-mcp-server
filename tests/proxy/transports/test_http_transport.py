"""Tests for HTTP proxy transport - with proper mocking."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestHttpProxyTransport:
    """Test HTTP proxy transport."""

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    def test_init_with_url(self, mock_httpx):
        """Test initialization with URL."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        config = {
            "url": "http://example.com",
            "timeout": 60,
            "headers": {"X-Custom": "value"},
            "verify_ssl": False,
        }

        transport = HttpProxyTransport("test_server", config)

        assert transport.server_name == "test_server"
        assert transport.url == "http://example.com"
        assert transport.timeout == 60
        assert transport.headers == {"X-Custom": "value"}
        assert transport.verify_ssl is False

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    def test_init_without_url(self, mock_httpx):
        """Test initialization without URL raises error."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        with pytest.raises(ValueError, match="requires 'url'"):
            HttpProxyTransport("test", {})

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_httpx):
        """Test successful connection."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        mock_client = AsyncMock()
        mock_httpx.AsyncClient.return_value = mock_client

        transport = HttpProxyTransport("test", {"url": "http://test.com"})
        result = await transport.connect()

        assert result is True
        assert transport.client == mock_client

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_httpx):
        """Test connection failure."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        mock_httpx.AsyncClient.side_effect = Exception("Failed")

        transport = HttpProxyTransport("test", {"url": "http://test.com"})
        result = await transport.connect()

        assert result is False

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_disconnect(self, mock_httpx):
        """Test disconnection."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        mock_client = AsyncMock()
        mock_httpx.AsyncClient.return_value = mock_client

        transport = HttpProxyTransport("test", {"url": "http://test.com"})
        await transport.connect()

        transport.session_id = "test-session"
        await transport.disconnect()

        assert transport.client is None
        assert transport.session_id is None
        mock_client.aclose.assert_called_once()

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_initialize(self, mock_httpx):
        """Test session initialization."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {"status": "ok"}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client

        transport = HttpProxyTransport("test", {"url": "http://test.com"})
        await transport.connect()

        result = await transport.initialize()

        assert transport.session_id is not None
        assert result == {"status": "ok"}

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_send_request_with_error(self, mock_httpx):
        """Test send_request with error response."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        # Create a proper exception class
        class MockHTTPError(Exception):
            pass

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": {"message": "Test error"}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client
        mock_httpx.HTTPError = MockHTTPError

        transport = HttpProxyTransport("test", {"url": "http://test.com"})
        await transport.connect()

        with pytest.raises(RuntimeError, match="Test error"):
            await transport.send_request("test_method")

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_call_tool(self, mock_httpx):
        """Test calling a tool."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {"output": "test"}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client

        transport = HttpProxyTransport("test", {"url": "http://test.com"})
        await transport.connect()
        transport.session_id = "test-session"

        result = await transport.call_tool("test_tool", {"arg": "value"})

        assert result == {"output": "test"}

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_list_tools(self, mock_httpx):
        """Test listing tools."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {"tools": []}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client

        transport = HttpProxyTransport("test", {"url": "http://test.com"})
        await transport.connect()

        result = await transport.list_tools()

        assert result == {"tools": []}

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_http_error_handling(self, mock_httpx):
        """Test HTTP error handling."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        # Create a proper exception class
        class MockHTTPError(Exception):
            pass

        mock_client = AsyncMock()
        mock_httpx.HTTPError = MockHTTPError
        mock_client.post = AsyncMock(side_effect=MockHTTPError("HTTP Error"))
        mock_httpx.AsyncClient.return_value = mock_client

        transport = HttpProxyTransport("test", {"url": "http://test.com"})
        await transport.connect()

        with pytest.raises(RuntimeError, match="HTTP request failed"):
            await transport.send_request("test_method")

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_send_request_increments_id(self, mock_httpx):
        """Test request ID increments."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value = mock_client

        transport = HttpProxyTransport("test", {"url": "http://test.com"})
        await transport.connect()

        await transport.send_request("method1")
        await transport.send_request("method2")

        assert transport.request_id == 2

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self, mock_httpx):
        """Test call_tool when not connected."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        transport = HttpProxyTransport("test", {"url": "http://test.com"})

        with pytest.raises(RuntimeError, match="not connected"):
            await transport.call_tool("test_tool", {})

    @patch("chuk_mcp_server.proxy.transports.http_transport.httpx")
    @pytest.mark.asyncio
    async def test_list_tools_not_connected(self, mock_httpx):
        """Test list_tools when not connected."""
        from chuk_mcp_server.proxy.transports.http_transport import HttpProxyTransport

        transport = HttpProxyTransport("test", {"url": "http://test.com"})

        with pytest.raises(RuntimeError, match="not connected"):
            await transport.list_tools()
