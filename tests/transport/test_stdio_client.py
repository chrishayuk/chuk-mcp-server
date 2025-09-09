#!/usr/bin/env python3
"""Test client for STDIO transport."""

import json
import subprocess
import sys
import time


def send_request(proc, method, params=None, msg_id=1):
    """Send a JSON-RPC request to the server."""
    request = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params:
        request["params"] = params

    request_line = json.dumps(request) + "\n"
    print(f"→ Sending: {request_line.strip()}")

    proc.stdin.write(request_line.encode())
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline()
    if response_line:
        response = json.loads(response_line.decode().strip())
        print(f"← Received: {json.dumps(response, indent=2)}")
        return response
    return None


def test_stdio_transport():
    """Test the STDIO transport implementation."""
    print("🧪 Testing STDIO Transport")
    print("=" * 50)

    # Start the server as a subprocess
    print("🚀 Starting server...")
    proc = subprocess.Popen(
        [sys.executable, "test_stdio_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )

    try:
        # Give server time to start
        time.sleep(1)

        print("\n1. Testing initialization...")
        response = send_request(
            proc,
            "initialize",
            {"clientInfo": {"name": "test-client", "version": "1.0.0"}, "protocolVersion": "2025-06-18"},
        )

        if response and "result" in response:
            print("✅ Initialization successful!")
        else:
            print("❌ Initialization failed!")
            return False

        print("\n2. Testing ping...")
        response = send_request(proc, "ping", msg_id=2)

        if response and "result" in response:
            print("✅ Ping successful!")
        else:
            print("❌ Ping failed!")
            return False

        print("\n3. Testing tools/list...")
        response = send_request(proc, "tools/list", msg_id=3)

        if response and "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools: {[t['name'] for t in tools]}")
        else:
            print("❌ tools/list failed!")
            return False

        print("\n4. Testing tool call (hello)...")
        response = send_request(proc, "tools/call", {"name": "hello", "arguments": {"name": "STDIO"}}, msg_id=4)

        if response and "result" in response:
            print("✅ Tool call successful!")
        else:
            print("❌ Tool call failed!")
            return False

        print("\n5. Testing tool call (add)...")
        response = send_request(proc, "tools/call", {"name": "add", "arguments": {"x": 10, "y": 5}}, msg_id=5)

        if response and "result" in response:
            print("✅ Add tool call successful!")
        else:
            print("❌ Add tool call failed!")
            return False

        print("\n6. Testing resources/list...")
        response = send_request(proc, "resources/list", msg_id=6)

        if response and "result" in response and "resources" in response["result"]:
            resources = response["result"]["resources"]
            print(f"✅ Found {len(resources)} resources: {[r['uri'] for r in resources]}")
        else:
            print("❌ resources/list failed!")
            return False

        print("\n7. Testing resource read...")
        response = send_request(proc, "resources/read", {"uri": "config://test"}, msg_id=7)

        if response and "result" in response:
            print("✅ Resource read successful!")
        else:
            print("❌ Resource read failed!")
            return False

        print("\n🎉 All tests passed! STDIO transport is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

    finally:
        # Clean up
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    success = test_stdio_transport()
    sys.exit(0 if success else 1)
