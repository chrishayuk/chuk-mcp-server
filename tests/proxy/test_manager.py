"""Tests for proxy manager."""

import json
import subprocess
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from chuk_mcp_server.proxy.manager import ProxyManager, StdioServerClient


class TestStdioServerClient:
    """Test StdioServerClient class."""

    def test_init(self):
        """Test client initialization."""
        process = Mock(spec=subprocess.Popen)
        client = StdioServerClient("test-server", process)

        assert client.server_name == "test-server"
        assert client.process == process
        assert client.request_id == 0

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool call."""
        # Create mock process
        process = Mock(spec=subprocess.Popen)
        process.stdin = Mock()
        process.stdout = Mock()

        # Mock response
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"output": "test result"},
        }
        process.stdout.readline.return_value = (json.dumps(response) + "\n").encode()

        client = StdioServerClient("test-server", process)

        result = await client.call_tool("test_tool", {"arg": "value"})

        assert result["isError"] is False
        assert result["content"]["output"] == "test result"
        assert client.request_id == 1

    @pytest.mark.asyncio
    async def test_call_tool_error_response(self):
        """Test tool call with error response."""
        process = Mock(spec=subprocess.Popen)
        process.stdin = Mock()
        process.stdout = Mock()

        # Mock error response
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found"},
        }
        process.stdout.readline.return_value = (json.dumps(response) + "\n").encode()

        client = StdioServerClient("test-server", process)

        result = await client.call_tool("unknown_tool", {})

        assert result["isError"] is True
        assert "Method not found" in result["error"]

    @pytest.mark.asyncio
    async def test_call_tool_stdin_none(self):
        """Test tool call when stdin is None."""
        process = Mock(spec=subprocess.Popen)
        process.stdin = None

        client = StdioServerClient("test-server", process)

        with pytest.raises(RuntimeError, match="stdin is not available"):
            await client.call_tool("test_tool", {})

    @pytest.mark.asyncio
    async def test_call_tool_stdout_none(self):
        """Test tool call when stdout is None."""
        process = Mock(spec=subprocess.Popen)
        process.stdin = Mock()
        process.stdout = None

        client = StdioServerClient("test-server", process)

        with pytest.raises(RuntimeError, match="stdout is not available"):
            await client.call_tool("test_tool", {})

    @pytest.mark.asyncio
    async def test_list_tools_success(self):
        """Test successful tool listing."""
        process = Mock(spec=subprocess.Popen)
        process.stdin = Mock()
        process.stdout = Mock()

        # Mock response
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {"name": "tool1", "description": "First tool"},
                    {"name": "tool2", "description": "Second tool"},
                ]
            },
        }
        process.stdout.readline.return_value = (json.dumps(response) + "\n").encode()

        client = StdioServerClient("test-server", process)

        tools = await client.list_tools()

        assert len(tools) == 2
        assert tools[0]["name"] == "tool1"
        assert tools[1]["name"] == "tool2"

    @pytest.mark.asyncio
    async def test_list_tools_error(self):
        """Test tool listing with error."""
        process = Mock(spec=subprocess.Popen)
        process.stdin = Mock()
        process.stdout = Mock()

        # Mock error response
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32603, "message": "Internal error"},
        }
        process.stdout.readline.return_value = (json.dumps(response) + "\n").encode()

        client = StdioServerClient("test-server", process)

        tools = await client.list_tools()

        assert tools == []

    @pytest.mark.asyncio
    async def test_list_tools_stdin_none(self):
        """Test list tools when stdin is None."""
        process = Mock(spec=subprocess.Popen)
        process.stdin = None

        client = StdioServerClient("test-server", process)

        with pytest.raises(RuntimeError, match="stdin is not available"):
            await client.list_tools()

    @pytest.mark.asyncio
    async def test_list_tools_stdout_none(self):
        """Test list tools when stdout is None."""
        process = Mock(spec=subprocess.Popen)
        process.stdin = Mock()
        process.stdout = None

        client = StdioServerClient("test-server", process)

        with pytest.raises(RuntimeError, match="stdout is not available"):
            await client.list_tools()

    @pytest.mark.asyncio
    async def test_close_running_process(self):
        """Test closing a running process."""
        process = Mock(spec=subprocess.Popen)
        process.poll.return_value = None  # Process is running
        process.wait.return_value = 0

        client = StdioServerClient("test-server", process)

        await client.close()

        process.terminate.assert_called_once()
        process.wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_already_terminated(self):
        """Test closing an already terminated process."""
        process = Mock(spec=subprocess.Popen)
        process.poll.return_value = 0  # Process already terminated

        client = StdioServerClient("test-server", process)

        await client.close()

        process.terminate.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_timeout_kill(self):
        """Test closing process that doesn't terminate gracefully."""
        process = Mock(spec=subprocess.Popen)
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("test", 5), 0]

        client = StdioServerClient("test-server", process)

        await client.close()

        process.terminate.assert_called_once()
        process.kill.assert_called_once()
        assert process.wait.call_count == 2


class TestProxyManager:
    """Test ProxyManager class."""

    def test_init_disabled(self):
        """Test initialization with proxy disabled."""
        config = {"proxy": {"enabled": False}}

        manager = ProxyManager(config)

        assert manager.enabled is False
        assert manager.namespace == "proxy"
        assert len(manager.running_servers) == 0

    def test_init_enabled(self):
        """Test initialization with proxy enabled."""
        config = {
            "proxy": {"enabled": True, "namespace": "custom"},
            "servers": {"backend": {"type": "stdio", "command": "python"}},
        }

        manager = ProxyManager(config)

        assert manager.enabled is True
        assert manager.namespace == "custom"
        assert "backend" in manager.servers_config

    def test_init_with_protocol_handler(self):
        """Test initialization with protocol handler."""
        config = {"proxy": {"enabled": True}}
        protocol = Mock()

        manager = ProxyManager(config, protocol)

        assert manager.protocol_handler == protocol

    @pytest.mark.asyncio
    async def test_start_servers_disabled(self):
        """Test starting servers when disabled."""
        config = {"proxy": {"enabled": False}}
        manager = ProxyManager(config)

        await manager.start_servers()

        assert len(manager.running_servers) == 0

    @pytest.mark.asyncio
    async def test_start_servers_no_config(self):
        """Test starting servers with no server config."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)

        await manager.start_servers()

        assert len(manager.running_servers) == 0

    @pytest.mark.asyncio
    async def test_start_servers_unsupported_type(self):
        """Test starting server with unsupported type."""
        config = {
            "proxy": {"enabled": True},
            "servers": {"test": {"type": "http", "url": "http://example.com"}},
        }
        manager = ProxyManager(config)

        await manager.start_servers()

        assert len(manager.running_servers) == 0

    @pytest.mark.asyncio
    async def test_start_server_error(self):
        """Test error during server startup."""
        config = {
            "proxy": {"enabled": True},
            "servers": {"test": {"type": "stdio", "command": "invalid_command"}},
        }
        manager = ProxyManager(config)

        # Should not raise, just log error
        await manager.start_servers()

        assert len(manager.running_servers) == 0

    @pytest.mark.asyncio
    async def test_stop_servers(self):
        """Test stopping servers."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)

        # Add mock client
        client = Mock(spec=StdioServerClient)
        client.close = AsyncMock()
        manager.running_servers["test"] = client

        await manager.stop_servers()

        client.close.assert_called_once()
        assert len(manager.running_servers) == 0

    @pytest.mark.asyncio
    async def test_stop_servers_with_error(self):
        """Test stopping servers with error."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)

        # Add mock client that raises error on close
        client = Mock(spec=StdioServerClient)
        client.close = AsyncMock(side_effect=Exception("Close failed"))
        manager.running_servers["test"] = client

        # Should not raise, just log error
        await manager.stop_servers()

        assert len(manager.running_servers) == 0

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test calling a proxied tool successfully."""
        config = {"proxy": {"enabled": True, "namespace": "proxy"}}
        manager = ProxyManager(config)

        # Add mock client
        client = Mock(spec=StdioServerClient)
        client.call_tool = AsyncMock(return_value={"isError": False, "content": {"result": "success"}})
        manager.running_servers["backend"] = client

        result = await manager.call_tool("proxy.backend.test_tool", arg="value")

        assert result == {"result": "success"}
        client.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_invalid_name(self):
        """Test calling tool with invalid name."""
        config = {"proxy": {"enabled": True, "namespace": "proxy"}}
        manager = ProxyManager(config)

        with pytest.raises(ValueError, match="must start with"):
            await manager.call_tool("invalid_tool")

    @pytest.mark.asyncio
    async def test_call_tool_invalid_format(self):
        """Test calling tool with invalid format."""
        config = {"proxy": {"enabled": True, "namespace": "proxy"}}
        manager = ProxyManager(config)

        with pytest.raises(ValueError, match="Invalid tool name format"):
            await manager.call_tool("proxy.invalid")

    @pytest.mark.asyncio
    async def test_call_tool_server_not_found(self):
        """Test calling tool on non-existent server."""
        config = {"proxy": {"enabled": True, "namespace": "proxy"}}
        manager = ProxyManager(config)

        with pytest.raises(ValueError, match="Server not found"):
            await manager.call_tool("proxy.unknown.test_tool")

    @pytest.mark.asyncio
    async def test_call_tool_error_response(self):
        """Test calling tool with error response."""
        config = {"proxy": {"enabled": True, "namespace": "proxy"}}
        manager = ProxyManager(config)

        # Add mock client that returns error
        client = Mock(spec=StdioServerClient)
        client.call_tool = AsyncMock(return_value={"isError": True, "error": "Tool failed"})
        manager.running_servers["backend"] = client

        with pytest.raises(RuntimeError, match="Tool failed"):
            await manager.call_tool("proxy.backend.test_tool")

    def test_get_all_tools(self):
        """Test getting all proxied tools."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)

        # Add some mock tools
        manager.proxied_tools = {
            "proxy.backend.tool1": Mock(),
            "proxy.backend.tool2": Mock(),
        }

        tools = manager.get_all_tools()

        assert len(tools) == 2
        assert "proxy.backend.tool1" in tools
        assert "proxy.backend.tool2" in tools

    def test_get_stats(self):
        """Test getting proxy statistics."""
        config = {"proxy": {"enabled": True, "namespace": "custom"}}
        manager = ProxyManager(config)

        # Add mock data
        manager.running_servers = {"backend": Mock()}
        manager.proxied_tools = {"custom.backend.tool1": Mock()}

        stats = manager.get_stats()

        assert stats["enabled"] is True
        assert stats["namespace"] == "custom"
        assert stats["servers"] == 1
        assert stats["tools"] == 1
        assert stats["server_names"] == ["backend"]

    @pytest.mark.asyncio
    async def test_initialize_server_success(self):
        """Test successful server initialization."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)

        # Create mock client
        process = Mock(spec=subprocess.Popen)
        process.stdin = Mock()
        process.stdout = Mock()

        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"protocolVersion": "2024-11-05"},
        }
        process.stdout.readline.return_value = (json.dumps(response) + "\n").encode()

        client = StdioServerClient("test", process)

        # Should not raise
        await manager._initialize_server(client)

        assert client.request_id == 1

    @pytest.mark.asyncio
    async def test_initialize_server_error(self):
        """Test server initialization with error."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)

        # Create mock client
        process = Mock(spec=subprocess.Popen)
        process.stdin = Mock()
        process.stdout = Mock()

        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32600, "message": "Init failed"},
        }
        process.stdout.readline.return_value = (json.dumps(response) + "\n").encode()

        client = StdioServerClient("test", process)

        with pytest.raises(RuntimeError, match="Failed to initialize"):
            await manager._initialize_server(client)

    @pytest.mark.asyncio
    async def test_initialize_server_stdin_none(self):
        """Test server initialization when stdin is None."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)

        process = Mock(spec=subprocess.Popen)
        process.stdin = None

        client = StdioServerClient("test", process)

        with pytest.raises(RuntimeError, match="stdin is not available"):
            await manager._initialize_server(client)

    @pytest.mark.asyncio
    async def test_initialize_server_stdout_none(self):
        """Test server initialization when stdout is None."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)

        process = Mock(spec=subprocess.Popen)
        process.stdin = Mock()
        process.stdout = None

        client = StdioServerClient("test", process)

        with pytest.raises(RuntimeError, match="stdout is not available"):
            await manager._initialize_server(client)

    @pytest.mark.asyncio
    @patch("chuk_mcp_server.proxy.manager.subprocess.Popen")
    async def test_start_server_stdio(self, mock_popen):
        """Test starting a stdio server successfully."""
        config = {
            "proxy": {"enabled": True},
            "servers": {
                "test": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "test_server"],
                    "cwd": "/tmp",
                }
            },
        }
        manager = ProxyManager(config)

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()

        # Mock initialization response
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"protocolVersion": "2024-11-05"},
        }

        # Mock tools list response
        tools_response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {"tools": [{"name": "test_tool", "description": "Test"}]},
        }

        mock_process.stdout.readline.side_effect = [
            (json.dumps(init_response) + "\n").encode(),
            (json.dumps(tools_response) + "\n").encode(),
        ]

        mock_popen.return_value = mock_process

        # Mock protocol handler
        protocol = MagicMock()
        protocol.register_tool = MagicMock()
        manager.protocol_handler = protocol

        await manager.start_servers()

        assert len(manager.running_servers) == 1
        assert "test" in manager.running_servers

    @pytest.mark.asyncio
    async def test_discover_and_wrap_tools_error(self):
        """Test tool discovery with error."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)

        # Add mock client that raises error
        client = Mock(spec=StdioServerClient)
        client.list_tools = AsyncMock(side_effect=Exception("List failed"))
        manager.running_servers["test"] = client

        # Should not raise, just log error
        await manager._discover_and_wrap_tools()

        assert len(manager.proxied_tools) == 0

    @pytest.mark.asyncio
    async def test_discover_and_wrap_tools_no_name(self):
        """Test tool discovery with tool missing name."""
        config = {"proxy": {"enabled": True}}
        manager = ProxyManager(config)

        # Add mock client that returns tool without name
        client = Mock(spec=StdioServerClient)
        client.list_tools = AsyncMock(return_value=[{"description": "No name"}])
        manager.running_servers["test"] = client

        await manager._discover_and_wrap_tools()

        assert len(manager.proxied_tools) == 0
