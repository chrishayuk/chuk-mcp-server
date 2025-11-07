"""Tests for proxy transports module initialization."""


class TestTransportsInit:
    """Test transports module initialization."""

    def test_imports(self):
        """Test that all transport classes can be imported."""
        from chuk_mcp_server.proxy.transports import (
            HttpProxyTransport,
            ProxyTransport,
            SseProxyTransport,
            StdioProxyTransport,
        )

        assert ProxyTransport is not None
        assert HttpProxyTransport is not None
        assert SseProxyTransport is not None
        assert StdioProxyTransport is not None

    def test_all_exports(self):
        """Test that __all__ is defined correctly."""
        import chuk_mcp_server.proxy.transports as transports

        assert hasattr(transports, "__all__")
        assert "ProxyTransport" in transports.__all__
        assert "HttpProxyTransport" in transports.__all__
        assert "SseProxyTransport" in transports.__all__
        assert "StdioProxyTransport" in transports.__all__
        assert len(transports.__all__) == 4

    def test_base_transport_accessible(self):
        """Test that base ProxyTransport is accessible."""
        from chuk_mcp_server.proxy.transports import ProxyTransport

        # Verify it's an abstract class
        assert hasattr(ProxyTransport, "__abstractmethods__")

    def test_http_transport_accessible(self):
        """Test that HttpProxyTransport is accessible."""
        from chuk_mcp_server.proxy.transports import HttpProxyTransport

        # Verify it's a class
        assert isinstance(HttpProxyTransport, type)

    def test_sse_transport_accessible(self):
        """Test that SseProxyTransport is accessible."""
        from chuk_mcp_server.proxy.transports import SseProxyTransport

        # Verify it's a class
        assert isinstance(SseProxyTransport, type)

    def test_stdio_transport_accessible(self):
        """Test that StdioProxyTransport is accessible."""
        from chuk_mcp_server.proxy.transports import StdioProxyTransport

        # Verify it's a class
        assert isinstance(StdioProxyTransport, type)

    def test_transport_inheritance(self):
        """Test that all concrete transports inherit from ProxyTransport."""
        from chuk_mcp_server.proxy.transports import (
            HttpProxyTransport,
            ProxyTransport,
            SseProxyTransport,
            StdioProxyTransport,
        )

        assert issubclass(HttpProxyTransport, ProxyTransport)
        assert issubclass(SseProxyTransport, ProxyTransport)
        assert issubclass(StdioProxyTransport, ProxyTransport)
