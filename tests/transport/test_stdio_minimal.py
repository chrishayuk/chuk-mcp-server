#!/usr/bin/env python3
"""Minimal stdio transport test."""

import json
import subprocess
import sys

# First create a minimal server script
server_script = """#!/usr/bin/env python3
import sys
import json
import asyncio
import logging

# Set logging to stderr so stdout is clean
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

from chuk_mcp_server.transport.stdio import StdioTransport
from chuk_mcp_server.protocol import MCPProtocolHandler
from chuk_mcp_server.types import ServerInfo, create_server_capabilities

# Create server components
server_info = ServerInfo(name="minimal-test", version="1.0.0")
capabilities = create_server_capabilities(tools=True)
protocol = MCPProtocolHandler(server_info, capabilities)
transport = StdioTransport(protocol)

print("🔌 Minimal STDIO server starting...", file=sys.stderr)
asyncio.run(transport.run())
"""


def test_minimal_stdio():
    """Test minimal stdio functionality."""
    print("🧪 Testing Minimal STDIO Transport")
    print("=" * 50)

    # Write the server script
    with open("/tmp/minimal_stdio_server.py", "w") as f:
        f.write(server_script)

    # Start server
    proc = subprocess.Popen(
        [sys.executable, "/tmp/minimal_stdio_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,
    )

    try:
        print("🚀 Server started, sending initialize...")

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"clientInfo": {"name": "test-client", "version": "1.0.0"}, "protocolVersion": "2025-06-18"},
        }

        request_line = json.dumps(init_request) + "\\n"
        print(f"→ Sending: {request_line.strip()}")

        proc.stdin.write(request_line)
        proc.stdin.flush()

        # Wait for response with timeout
        import select

        ready, _, _ = select.select([proc.stdout], [], [], 5)

        if ready:
            response_line = proc.stdout.readline()
            if response_line:
                print(f"← Received: {response_line.strip()}")
                try:
                    response = json.loads(response_line.strip())
                    if "result" in response:
                        print("✅ Initialize successful!")
                        return True
                    else:
                        print("❌ No result in response")
                        return False
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {e}")
                    return False
            else:
                print("❌ No response received")
                return False
        else:
            print("❌ Timeout waiting for response")
            stderr_output = proc.stderr.read()
            print(f"Server stderr: {stderr_output}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        stderr_output = proc.stderr.read()
        print(f"Server stderr: {stderr_output}")
        return False

    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    success = test_minimal_stdio()
    sys.exit(0 if success else 1)
