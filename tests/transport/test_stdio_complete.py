#!/usr/bin/env python3
"""Complete STDIO transport test suite."""

import json
import subprocess
import sys
import tempfile


def test_stdio_transport_initialization():
    """Test STDIO transport initialization."""
    server_code = """#!/usr/bin/env python3
from chuk_mcp_server import tool, run

@tool
def test_tool() -> str:
    return "working"

if __name__ == "__main__":
    run(transport="stdio", debug=False)
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(server_code)
        server_path = f.name

    try:
        # Test initialization request
        init_request = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"pytest","version":"1.0"},"protocolVersion":"2025-06-18"}}'

        result = subprocess.run(
            [sys.executable, server_path], input=init_request + "\n", text=True, capture_output=True, timeout=5
        )

        assert result.returncode == 0

        # Parse JSON response
        json_lines = [line for line in result.stdout.split("\n") if line.startswith("{")]
        assert len(json_lines) >= 1

        response = json.loads(json_lines[0])
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert "serverInfo" in response["result"]
        assert "capabilities" in response["result"]

    finally:
        import os

        os.unlink(server_path)


def test_stdio_transport_tools():
    """Test STDIO transport tool functionality."""
    server_code = '''#!/usr/bin/env python3
from chuk_mcp_server import tool, run

@tool
def echo(message: str) -> str:
    """Echo a message."""
    return f"Echo: {message}"

@tool
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

if __name__ == "__main__":
    run(transport="stdio", debug=False)
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(server_code)
        server_path = f.name

    try:
        # Test tools/list and tools/call
        requests = [
            '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test","version":"1.0"},"protocolVersion":"2025-06-18"}}',
            '{"jsonrpc":"2.0","id":2,"method":"tools/list"}',
            '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"echo","arguments":{"message":"Hello STDIO"}}}',
            '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"add","arguments":{"x":10,"y":5}}}',
        ]

        input_text = "\n".join(requests) + "\n"

        result = subprocess.run(
            [sys.executable, server_path], input=input_text, text=True, capture_output=True, timeout=10
        )

        assert result.returncode == 0

        # Parse responses
        json_lines = [line for line in result.stdout.split("\n") if line.startswith("{")]
        assert len(json_lines) >= 3  # At least init, tools/list, and one tool call

        # Check tools/list response
        tools_response = None
        for line in json_lines:
            response = json.loads(line)
            if response.get("id") == 2:
                tools_response = response
                break

        assert tools_response is not None
        assert "result" in tools_response
        assert "tools" in tools_response["result"]
        tools = tools_response["result"]["tools"]
        assert len(tools) == 2
        tool_names = [tool["name"] for tool in tools]
        assert "echo" in tool_names
        assert "add" in tool_names

    finally:
        import os

        os.unlink(server_path)


def test_stdio_transport_resources():
    """Test STDIO transport resource functionality."""
    server_code = '''#!/usr/bin/env python3
from chuk_mcp_server import tool, resource, run

@resource("test://config")
def get_config() -> dict:
    """Get test configuration."""
    return {"test": True, "transport": "stdio"}

if __name__ == "__main__":
    run(transport="stdio", debug=False)
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(server_code)
        server_path = f.name

    try:
        requests = [
            '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test","version":"1.0"},"protocolVersion":"2025-06-18"}}',
            '{"jsonrpc":"2.0","id":2,"method":"resources/list"}',
            '{"jsonrpc":"2.0","id":3,"method":"resources/read","params":{"uri":"test://config"}}',
        ]

        input_text = "\n".join(requests) + "\n"

        result = subprocess.run(
            [sys.executable, server_path], input=input_text, text=True, capture_output=True, timeout=10
        )

        assert result.returncode == 0

        # Parse responses
        json_lines = [line for line in result.stdout.split("\n") if line.startswith("{")]
        assert len(json_lines) >= 2

        # Check resources/list response
        resources_response = None
        for line in json_lines:
            response = json.loads(line)
            if response.get("id") == 2:
                resources_response = response
                break

        assert resources_response is not None
        assert "result" in resources_response
        assert "resources" in resources_response["result"]
        resources = resources_response["result"]["resources"]
        assert len(resources) == 1
        assert resources[0]["uri"] == "test://config"

    finally:
        import os

        os.unlink(server_path)


if __name__ == "__main__":
    print("🧪 Running Complete STDIO Transport Tests")
    print("=" * 50)

    try:
        print("1. Testing initialization...")
        test_stdio_transport_initialization()
        print("   ✅ PASSED")

        print("2. Testing tools...")
        test_stdio_transport_tools()
        print("   ✅ PASSED")

        print("3. Testing resources...")
        test_stdio_transport_resources()
        print("   ✅ PASSED")

        print("\\n🎉 ALL TESTS PASSED!")
        print("✅ STDIO transport is fully functional and MCP-compliant!")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
