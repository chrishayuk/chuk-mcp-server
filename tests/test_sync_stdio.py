#!/usr/bin/env python3
"""Test synchronous STDIO transport."""

import contextlib
import json
import os
import select
import subprocess
import sys
import tempfile
import time
from io import StringIO
from unittest.mock import AsyncMock, Mock, patch

import pytest

from chuk_mcp_server.stdio_transport import StdioSyncTransport


@pytest.mark.skipif(sys.platform == "win32", reason="select.select() doesn't work with pipes on Windows")
@pytest.mark.timeout(10)
def test_sync_stdio():
    """Test synchronous stdio transport."""
    print("🧪 Testing Synchronous STDIO Transport")
    print("=" * 50)

    # Create server script
    server_script = '''#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from chuk_mcp_server import tool, run

@tool
def hello(name: str = "World") -> str:
    """Say hello."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    run(transport="stdio", debug=False)
'''

    # Write server script to temp directory (cross-platform)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        server_path = f.name
        f.write(server_script)

    print("🚀 Starting sync stdio server...")

    # Start server
    proc = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,
    )

    try:
        time.sleep(0.5)  # Give server time to start

        print("1. Testing initialization...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"clientInfo": {"name": "test-client", "version": "1.0.0"}, "protocolVersion": "2025-06-18"},
        }

        # Send request
        request_line = json.dumps(init_request) + "\n"
        print(f"→ Sending: {request_line.strip()}")
        proc.stdin.write(request_line)
        proc.stdin.flush()

        # Read response with timeout using select
        ready, _, _ = select.select([proc.stdout], [], [], 5)
        if ready:
            response_line = proc.stdout.readline()
            if response_line:
                print(f"← Received: {response_line.strip()}")
                response = json.loads(response_line.strip())
                if "result" in response:
                    print("✅ Initialize successful!")

                    # Test tool call
                    print("\\n2. Testing tool call...")
                    tool_request = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {"name": "hello", "arguments": {"name": "STDIO"}},
                    }

                    request_line = json.dumps(tool_request) + "\n"
                    print(f"→ Sending: {request_line.strip()}")
                    proc.stdin.write(request_line)
                    proc.stdin.flush()

                    response_line = proc.stdout.readline()
                    if response_line:
                        print(f"← Received: {response_line.strip()}")
                        response = json.loads(response_line.strip())
                        if "result" in response:
                            print("✅ Tool call successful!")
                            print("🎉 All tests passed!")
                            return True
                        else:
                            print("❌ Tool call failed")
                            return False
                    else:
                        print("❌ No tool response")
                        return False
                else:
                    print("❌ Initialize failed")
                    return False
            else:
                print("❌ No response")
                return False
        else:
            print("❌ Timeout waiting for response")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        stderr_output = proc.stderr.read()
        print(f"Server stderr: {stderr_output}")
        return False

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        # Clean up temporary file
        with contextlib.suppress(Exception):
            os.unlink(server_path)


# ---------------------------------------------------------------------------
# Fixtures and unit tests for StdioSyncTransport coverage
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_protocol():
    """Create a mock protocol handler."""
    protocol = Mock()
    protocol.handle_request = AsyncMock(return_value=({}, None))
    return protocol


@pytest.fixture
def transport(mock_protocol):
    """Create a StdioSyncTransport instance."""
    return StdioSyncTransport(mock_protocol)


class TestStdioSyncTransportCoverage:
    """Test uncovered lines in StdioSyncTransport."""

    def test_run_with_empty_line(self, transport, mock_protocol):
        """Test run() with empty line (lines 32-34)."""
        # Mock stdin to return empty line then EOF
        stdin_data = "\n\n"

        with patch("sys.stdin", StringIO(stdin_data)):
            transport.run()

        # Empty lines should be skipped, no handle_request called
        mock_protocol.handle_request.assert_not_called()

    def test_run_with_keyboard_interrupt(self, transport, mock_protocol):
        """Test run() with KeyboardInterrupt (lines 39-40)."""
        # Mock stdin.readline to raise KeyboardInterrupt
        with patch("sys.stdin.readline", side_effect=KeyboardInterrupt):
            transport.run()

        # Should exit cleanly without calling handle_request
        mock_protocol.handle_request.assert_not_called()

    def test_run_with_exception_in_loop(self, transport, mock_protocol):
        """Test run() with exception in main loop (lines 41-48)."""
        # Mock stdin to raise exception, then return EOF
        call_count = [0]

        def readline_with_exception():
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Test exception in loop")
            return ""  # EOF on second call

        with patch("sys.stdin.readline", side_effect=readline_with_exception):
            with patch("sys.stdout.write") as mock_write:
                transport.run()

                # Should have sent error response
                assert mock_write.called
                written = "".join(call.args[0] for call in mock_write.call_args_list)
                assert "Transport error" in written

    @pytest.mark.asyncio
    async def test_handle_message_json_decode_error(self, transport, mock_protocol):
        """Test _handle_message with invalid JSON (lines 71-73)."""
        invalid_json = "{invalid json}"

        with patch.object(transport, "_send_error") as mock_send_error:
            await transport._handle_message(invalid_json)

            # Should call _send_error with parse error
            mock_send_error.assert_called_once()
            assert mock_send_error.call_args[0][0] == -32700
            assert "Parse error" in mock_send_error.call_args[0][1]

    @pytest.mark.asyncio
    async def test_handle_message_exception(self, transport, mock_protocol):
        """Test _handle_message with exception during handling (lines 74-76)."""
        # Mock protocol.handle_request to raise exception
        mock_protocol.handle_request = AsyncMock(side_effect=RuntimeError("Handler error"))

        valid_json = json.dumps({"jsonrpc": "2.0", "method": "test", "id": 1})

        with patch.object(transport, "_send_error") as mock_send_error:
            await transport._handle_message(valid_json)

            # Should call _send_error with internal error
            mock_send_error.assert_called_once()
            assert mock_send_error.call_args[0][0] == -32603
            assert mock_send_error.call_args[0][1] == "Internal error"

    def test_send_response_with_exception(self, transport):
        """Test _send_response with exception during send (lines 84-85)."""
        response = {"test": "data"}

        # Mock print to raise exception
        with patch("builtins.print", side_effect=RuntimeError("Send error")):
            # Should not raise, just log error
            transport._send_response(response)

    def test_send_error(self, transport):
        """Test _send_error method (lines 87-90)."""
        with patch.object(transport, "_send_response") as mock_send_response:
            transport._send_error(-32700, "Test error", request_id=123)

            mock_send_response.assert_called_once()
            error_response = mock_send_response.call_args[0][0]

            assert error_response["jsonrpc"] == "2.0"
            assert error_response["id"] == 123
            assert error_response["error"]["code"] == -32700
            assert error_response["error"]["message"] == "Test error"


if __name__ == "__main__":
    success = test_sync_stdio()
    sys.exit(0 if success else 1)
