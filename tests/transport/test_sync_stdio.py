#!/usr/bin/env python3
"""Test synchronous STDIO transport."""

import json
import subprocess
import sys
import time


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

    # Write server script
    server_path = "/tmp/sync_stdio_server.py"
    with open(server_path, "w") as f:
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
        request_line = json.dumps(init_request) + "\\n"
        print(f"→ Sending: {request_line.strip()}")
        proc.stdin.write(request_line)
        proc.stdin.flush()

        # Read response with timeout
        proc.stdout.settimeout(5)
        try:
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

                    request_line = json.dumps(tool_request) + "\\n"
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

        except Exception as e:
            print(f"❌ Error reading response: {e}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        stderr_output = proc.stderr.read()
        print(f"Server stderr: {stderr_output}")
        return False

    finally:
        proc.terminate()
        proc.wait()

    return False


if __name__ == "__main__":
    success = test_sync_stdio()
    sys.exit(0 if success else 1)
