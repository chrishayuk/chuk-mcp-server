"""Tests for Stdio proxy transport - with proper mocking."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestStdioProxyTransport:
    """Test Stdio proxy transport."""

    def test_init_with_command(self):
        """Test initialization with command."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        config = {
            "command": "python",
            "args": ["server.py", "--debug"],
            "cwd": "/tmp/test",
            "env": {"DEBUG": "1"},
        }

        transport = StdioProxyTransport("test_server", config)

        assert transport.server_name == "test_server"
        assert transport.command == "python"
        assert transport.args == ["server.py", "--debug"]
        assert transport.cwd == "/tmp/test"
        assert transport.env == {"DEBUG": "1"}

    def test_init_without_command(self):
        """Test initialization without command raises error."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        with pytest.raises(ValueError, match="requires 'command'"):
            StdioProxyTransport("test", {})

    def test_init_defaults(self):
        """Test initialization with default values."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        transport = StdioProxyTransport("test", {"command": "python"})

        assert transport.args == []
        assert transport.cwd is None
        assert transport.env is None

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_asyncio, mock_subprocess):
        """Test successful connection."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        result = await transport.connect()

        assert result is True
        assert transport.process == mock_process

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_connect_process_exits_immediately(self, mock_asyncio, mock_subprocess):
        """Test connection when process exits immediately."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process exited
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"Error message"
        mock_process.stderr = mock_stderr
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        result = await transport.connect()

        assert result is False

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_asyncio, mock_subprocess):
        """Test connection failure."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_subprocess.Popen.side_effect = Exception("Process start failed")
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        result = await transport.connect()

        assert result is False

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_disconnect_graceful(self, mock_asyncio, mock_subprocess):
        """Test graceful disconnection."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        await transport.connect()

        transport.session_id = "test-session"
        await transport.disconnect()

        assert transport.process is None
        assert transport.session_id is None
        mock_process.terminate.assert_called_once()

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_disconnect_forced_kill(self, mock_asyncio, mock_subprocess):
        """Test forced kill on timeout."""
        from subprocess import TimeoutExpired

        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_process.terminate = MagicMock()
        mock_process.wait = MagicMock(side_effect=[TimeoutExpired("cmd", 5), None])
        mock_process.kill = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_subprocess.TimeoutExpired = TimeoutExpired
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        await transport.connect()

        await transport.disconnect()

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_handles_none(self):
        """Test disconnection when not connected."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        transport = StdioProxyTransport("test", {"command": "python"})
        # Should not raise
        await transport.disconnect()

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_initialize(self, mock_asyncio, mock_subprocess):
        """Test session initialization."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readline.return_value = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "result": {"status": "initialized"}}
        ).encode()

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        await transport.connect()

        result = await transport.initialize()

        assert transport.session_id is not None
        assert result == {"status": "initialized"}

    @pytest.mark.asyncio
    async def test_initialize_not_connected(self):
        """Test initialization when not connected."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        transport = StdioProxyTransport("test", {"command": "python"})

        with pytest.raises(RuntimeError, match="not started"):
            await transport.initialize()

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_call_tool(self, mock_asyncio, mock_subprocess):
        """Test calling a tool."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readline.return_value = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "result": {"output": "test"}}
        ).encode()

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        await transport.connect()
        transport.session_id = "test-session"

        result = await transport.call_tool("test_tool", {"arg": "value"})

        assert result == {"output": "test"}

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_list_tools(self, mock_asyncio, mock_subprocess):
        """Test listing tools."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readline.return_value = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}).encode()

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        await transport.connect()

        result = await transport.list_tools()

        assert result == {"tools": []}

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_send_request_with_params(self, mock_asyncio, mock_subprocess):
        """Test send_request with parameters."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readline.return_value = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"data": "test"}}).encode()

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        await transport.connect()

        result = await transport.send_request("test_method", {"param": "value"})

        assert result == {"data": "test"}

        # Verify request was made correctly
        written_data = mock_stdin.write.call_args[0][0].decode()
        request_data = json.loads(written_data)
        assert request_data["method"] == "test_method"
        assert request_data["params"] == {"param": "value"}

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_send_request_without_params(self, mock_asyncio, mock_subprocess):
        """Test send_request without parameters."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readline.return_value = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode()

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        await transport.connect()

        result = await transport.send_request("test_method")

        assert result == {}

        # Verify params not included when None
        written_data = mock_stdin.write.call_args[0][0].decode()
        request_data = json.loads(written_data)
        assert "params" not in request_data

    @pytest.mark.asyncio
    async def test_send_request_not_connected(self):
        """Test send_request when not connected."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        transport = StdioProxyTransport("test", {"command": "python"})

        with pytest.raises(RuntimeError, match="not available"):
            await transport.send_request("test_method")

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_send_request_with_error_response(self, mock_asyncio, mock_subprocess):
        """Test send_request with error in response."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readline.return_value = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "error": {"message": "Test error"}}
        ).encode()

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        await transport.connect()

        with pytest.raises(RuntimeError, match="Test error"):
            await transport.send_request("test_method")

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_send_request_no_response(self, mock_asyncio, mock_subprocess):
        """Test send_request with no response."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readline.return_value = b""  # Empty response

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        await transport.connect()

        with pytest.raises(RuntimeError, match="No response"):
            await transport.send_request("test_method")

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_send_request_increments_id(self, mock_asyncio, mock_subprocess):
        """Test that send_request increments request ID."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readline.return_value = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode()

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport("test", {"command": "python"})
        await transport.connect()

        await transport.send_request("method1")
        await transport.send_request("method2")

        assert transport.request_id == 2

    @patch("chuk_mcp_server.proxy.transports.stdio_transport.subprocess")
    @patch("chuk_mcp_server.proxy.transports.stdio_transport.asyncio")
    @pytest.mark.asyncio
    async def test_connect_with_cwd_and_env(self, mock_asyncio, mock_subprocess):
        """Test connection with custom cwd and env."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_subprocess.PIPE = "PIPE"
        mock_asyncio.sleep = AsyncMock()

        transport = StdioProxyTransport(
            "test",
            {
                "command": "python",
                "args": ["server.py"],
                "cwd": "/custom/dir",
                "env": {"VAR": "value"},
            },
        )
        await transport.connect()

        # Verify Popen was called with correct parameters
        call_kwargs = mock_subprocess.Popen.call_args[1]
        assert call_kwargs["cwd"] == "/custom/dir"
        assert call_kwargs["env"] == {"VAR": "value"}

    def test_is_connected_false(self):
        """Test is_connected when not connected."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        transport = StdioProxyTransport("test", {"command": "python"})
        assert transport.is_connected() is False

    def test_is_connected_true(self):
        """Test is_connected when connected."""
        from chuk_mcp_server.proxy.transports.stdio_transport import StdioProxyTransport

        transport = StdioProxyTransport("test", {"command": "python"})
        transport.session_id = "test-session"
        assert transport.is_connected() is True
