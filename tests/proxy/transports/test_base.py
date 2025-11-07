"""Tests for proxy transport base class."""

import pytest

from chuk_mcp_server.proxy.transports.base import ProxyTransport


class ConcreteTransport(ProxyTransport):
    """Concrete implementation for testing."""

    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        pass

    async def initialize(self) -> dict:
        return {"status": "initialized"}

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        return {"tool": tool_name, "args": arguments}

    async def list_tools(self) -> dict:
        return {"tools": []}


class TestProxyTransportBase:
    """Test ProxyTransport base class."""

    def test_init(self):
        """Test transport initialization."""
        config = {"url": "http://example.com"}
        transport = ConcreteTransport("test_server", config)

        assert transport.server_name == "test_server"
        assert transport.config == config
        assert transport.session_id is None

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connect method."""
        transport = ConcreteTransport("test", {})
        result = await transport.connect()
        assert result is True

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnect method."""
        transport = ConcreteTransport("test", {})
        # Should not raise
        await transport.disconnect()

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test initialize method."""
        transport = ConcreteTransport("test", {})
        result = await transport.initialize()
        assert result == {"status": "initialized"}

    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test call_tool method."""
        transport = ConcreteTransport("test", {})
        result = await transport.call_tool("test_tool", {"arg": "value"})
        assert result == {"tool": "test_tool", "args": {"arg": "value"}}

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test list_tools method."""
        transport = ConcreteTransport("test", {})
        result = await transport.list_tools()
        assert result == {"tools": []}

    @pytest.mark.asyncio
    async def test_send_request_not_implemented(self):
        """Test that send_request raises NotImplementedError by default."""
        transport = ConcreteTransport("test", {})
        with pytest.raises(NotImplementedError):
            await transport.send_request("test_method")

    def test_is_connected_false(self):
        """Test is_connected when not connected."""
        transport = ConcreteTransport("test", {})
        assert transport.is_connected() is False

    def test_is_connected_true(self):
        """Test is_connected when connected."""
        transport = ConcreteTransport("test", {})
        transport.session_id = "test-session"
        assert transport.is_connected() is True
