"""
Tests for ProxyManager using chuk-tool-processor StreamManager.

This tests the refactored v2 implementation that uses StreamManager
instead of custom transport classes.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from chuk_mcp_server.proxy.manager import ProxyManager


class TestProxyManagerInit:
    """Test ProxyManager initialization."""

    def test_init_default(self):
        """Test initialization with default config."""
        config = {}
        manager = ProxyManager(config)

        assert manager.enabled is False
        assert manager.namespace == "proxy"
        assert manager.servers_config == {}
        assert manager.stream_managers == {}
        assert manager.registered_tools == {}

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = {
            "proxy": {
                "enabled": True,
                "namespace": "remote",
            },
            "servers": {
                "test": {"type": "stdio"},
            },
        }
        manager = ProxyManager(config)

        assert manager.enabled is True
        assert manager.namespace == "remote"
        assert "test" in manager.servers_config

    def test_init_with_protocol_handler(self):
        """Test initialization with protocol handler."""
        config = {}
        protocol_handler = Mock()
        manager = ProxyManager(config, protocol_handler)

        assert manager.protocol_handler == protocol_handler


class TestProxyManagerStartServers:
    """Test ProxyManager.start_servers()."""

    @pytest.mark.asyncio
    async def test_start_servers_disabled(self):
        """Test starting servers when proxy is disabled."""
        config = {"proxy": {"enabled": False}}
        manager = ProxyManager(config)

        await manager.start_servers()

        assert len(manager.stream_managers) == 0
        assert len(manager.registered_tools) == 0

    @pytest.mark.asyncio
    async def test_start_servers_no_servers_configured(self):
        """Test starting servers with no servers configured."""
        config = {"proxy": {"enabled": True}, "servers": {}}
        manager = ProxyManager(config)

        await manager.start_servers()

        assert len(manager.stream_managers) == 0

    @pytest.mark.asyncio
    async def test_start_stdio_server_success(self):
        """Test successfully starting STDIO server."""
        config = {
            "proxy": {"enabled": True, "namespace": "test"},
            "servers": {
                "echo": {
                    "type": "stdio",
                    "command": "uvx",
                    "args": ["mcp-server-echo"],
                }
            },
        }

        mock_stream_manager = AsyncMock()
        mock_stream_manager.get_all_tools.return_value = [
            {
                "name": "echo",
                "description": "Echo tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            }
        ]

        with patch("chuk_mcp_server.proxy.manager.StreamManager") as MockStreamManager:
            MockStreamManager.create_with_stdio = AsyncMock(return_value=mock_stream_manager)

            with patch("chuk_mcp_server.proxy.manager.register_mcp_tools") as mock_register:
                mock_register.return_value = ["echo"]

                manager = ProxyManager(config)
                await manager.start_servers()

                # Verify stream manager created
                MockStreamManager.create_with_stdio.assert_called_once()
                call_args = MockStreamManager.create_with_stdio.call_args
                assert call_args[1]["servers"][0]["command"] == "uvx"
                assert call_args[1]["servers"][0]["args"] == ["mcp-server-echo"]

                # Verify tools registered
                mock_register.assert_called_once()
                assert mock_register.call_args[1]["namespace"] == "test"

                # Verify state
                assert "echo" in manager.stream_managers
                assert manager.stream_managers["echo"] == mock_stream_manager
                assert "echo" in manager.registered_tools
                assert manager.registered_tools["echo"] == ["echo"]

    @pytest.mark.asyncio
    async def test_start_http_server_success(self):
        """Test successfully starting HTTP server."""
        config = {
            "proxy": {"enabled": True, "namespace": "api"},
            "servers": {
                "weather": {
                    "type": "http",
                    "url": "https://api.weather.com/mcp",
                }
            },
        }

        mock_stream_manager = AsyncMock()
        mock_stream_manager.get_all_tools.return_value = []

        with patch("chuk_mcp_server.proxy.manager.StreamManager") as MockStreamManager:
            MockStreamManager.create_with_http_streamable = AsyncMock(return_value=mock_stream_manager)

            with patch("chuk_mcp_server.proxy.manager.register_mcp_tools") as mock_register:
                mock_register.return_value = []

                manager = ProxyManager(config)
                await manager.start_servers()

                # Verify HTTP stream manager created
                MockStreamManager.create_with_http_streamable.assert_called_once()
                call_args = MockStreamManager.create_with_http_streamable.call_args
                assert call_args[1]["servers"][0]["url"] == "https://api.weather.com/mcp"

    @pytest.mark.asyncio
    async def test_start_sse_server_success(self):
        """Test successfully starting SSE server."""
        config = {
            "proxy": {"enabled": True},
            "servers": {
                "events": {
                    "type": "sse",
                    "url": "https://events.example.com/mcp",
                }
            },
        }

        mock_stream_manager = AsyncMock()
        mock_stream_manager.get_all_tools.return_value = []

        with patch("chuk_mcp_server.proxy.manager.StreamManager") as MockStreamManager:
            MockStreamManager.create_with_sse = AsyncMock(return_value=mock_stream_manager)

            with patch("chuk_mcp_server.proxy.manager.register_mcp_tools") as mock_register:
                mock_register.return_value = []

                manager = ProxyManager(config)
                await manager.start_servers()

                # Verify SSE stream manager created
                MockStreamManager.create_with_sse.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_server_missing_command(self):
        """Test starting STDIO server with missing command."""
        config = {
            "proxy": {"enabled": True},
            "servers": {
                "bad": {
                    "type": "stdio",
                    # Missing 'command'
                }
            },
        }

        manager = ProxyManager(config)
        await manager.start_servers()

        # Should not crash, just log error and skip
        assert len(manager.stream_managers) == 0

    @pytest.mark.asyncio
    async def test_start_server_unknown_type(self):
        """Test starting server with unknown type."""
        config = {
            "proxy": {"enabled": True},
            "servers": {
                "unknown": {
                    "type": "unknown_transport",
                }
            },
        }

        manager = ProxyManager(config)
        await manager.start_servers()

        # Should skip unknown types
        assert len(manager.stream_managers) == 0


class TestProxyManagerRegisterWithProtocolHandler:
    """Test _register_with_protocol_handler method."""

    @pytest.mark.asyncio
    async def test_register_with_no_handler(self):
        """Test registration when no protocol handler provided."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)  # No protocol_handler

        mock_stream_manager = Mock()
        mock_stream_manager.get_all_tools.return_value = []

        # Should not crash
        await manager._register_with_protocol_handler("test", mock_stream_manager)

    @pytest.mark.asyncio
    async def test_register_with_handler(self):
        """Test successful registration with protocol handler."""
        protocol_handler = Mock()
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config, protocol_handler)

        mock_stream_manager = Mock()
        mock_stream_manager.get_all_tools.return_value = [
            {
                "name": "test_tool",
                "description": "Test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {"x": {"type": "integer"}},
                    "required": ["x"],
                },
            }
        ]

        with patch("chuk_mcp_server.proxy.manager.MCPTool") as MockMCPTool:
            mock_mcp_tool = Mock()
            MockMCPTool.return_value = mock_mcp_tool

            with patch("chuk_mcp_server.proxy.mcp_tool_wrapper.create_mcp_tool_handler") as mock_create:
                mock_handler = Mock()
                mock_create.return_value = mock_handler

                await manager._register_with_protocol_handler("ns", mock_stream_manager)

                # Verify MCPTool created
                MockMCPTool.assert_called_once_with(
                    tool_name="test_tool",
                    stream_manager=mock_stream_manager,
                    default_timeout=30.0,
                    enable_resilience=True,
                )

                # Verify handler created and registered
                mock_create.assert_called_once()
                protocol_handler.register_tool.assert_called_once_with(mock_handler)


class TestProxyManagerStopServers:
    """Test ProxyManager.stop_servers()."""

    @pytest.mark.asyncio
    async def test_stop_servers_empty(self):
        """Test stopping when no servers running."""
        config = {}
        manager = ProxyManager(config)

        await manager.stop_servers()

        assert len(manager.stream_managers) == 0

    @pytest.mark.asyncio
    async def test_stop_servers_success(self):
        """Test successfully stopping servers."""
        config = {}
        manager = ProxyManager(config)

        # Add mock stream managers
        mock_sm1 = AsyncMock()
        mock_sm2 = AsyncMock()

        manager.stream_managers = {
            "server1": mock_sm1,
            "server2": mock_sm2,
        }
        manager.registered_tools = {
            "server1": ["tool1"],
            "server2": ["tool2"],
        }

        await manager.stop_servers()

        # Verify all managers closed
        mock_sm1.close.assert_called_once()
        mock_sm2.close.assert_called_once()

        # Verify state cleared
        assert len(manager.stream_managers) == 0
        assert len(manager.registered_tools) == 0

    @pytest.mark.asyncio
    async def test_stop_servers_with_error(self):
        """Test stopping servers when one fails."""
        config = {}
        manager = ProxyManager(config)

        mock_sm1 = AsyncMock()
        mock_sm2 = AsyncMock()
        mock_sm2.close.side_effect = Exception("Close failed")

        manager.stream_managers = {
            "server1": mock_sm1,
            "server2": mock_sm2,
        }

        await manager.stop_servers()

        # Both should be attempted
        mock_sm1.close.assert_called_once()
        mock_sm2.close.assert_called_once()

        # State should still be cleared
        assert len(manager.stream_managers) == 0


class TestProxyManagerGetServerInfo:
    """Test ProxyManager.get_server_info()."""

    def test_get_server_info_empty(self):
        """Test getting server info when empty."""
        config = {"proxy": {"enabled": True, "namespace": "test"}}
        manager = ProxyManager(config)

        info = manager.get_server_info()

        assert info["enabled"] is True
        assert info["namespace"] == "test"
        assert info["servers"] == []
        assert info["tools_count"] == 0
        assert info["tools_by_server"] == {}

    def test_get_server_info_with_servers(self):
        """Test getting server info with servers."""
        config = {"proxy": {"enabled": True, "namespace": "api"}}
        manager = ProxyManager(config)

        manager.stream_managers = {
            "server1": Mock(),
            "server2": Mock(),
        }
        manager.registered_tools = {
            "server1": ["tool1", "tool2"],
            "server2": ["tool3"],
        }

        info = manager.get_server_info()

        assert info["enabled"] is True
        assert info["namespace"] == "api"
        assert set(info["servers"]) == {"server1", "server2"}
        assert info["tools_count"] == 3
        assert info["tools_by_server"]["server1"] == 2
        assert info["tools_by_server"]["server2"] == 1
