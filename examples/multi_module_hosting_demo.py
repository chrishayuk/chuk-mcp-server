#!/usr/bin/env python3
"""
Multi-Module Hosting Demo

This example demonstrates hosting multiple tool modules within a single
ChukMCPServer instance. The server will load and expose tools from multiple
Python modules, each in its own namespace.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_mcp_server import ChukMCPServer

# Configuration for tool modules
tool_modules_config = {
    # Math tools module
    "math": {
        "enabled": True,
        "location": str(Path(__file__).parent / "tool_modules"),  # Path to modules directory
        "module": "math_tools.tools",  # Python module path
        "namespace": "math",  # Namespace for tools (tools will be math.add, math.multiply, etc.)
        "tools": {
            # Optional: can selectively enable/disable individual tools
            "add": {"enabled": True},
            "multiply": {"enabled": True},
            "power": {"enabled": True},
        },
    },
    # Text tools module
    "text": {
        "enabled": True,
        "location": str(Path(__file__).parent / "tool_modules"),
        "module": "text_tools.tools",
        "namespace": "text",
        "tools": {
            "uppercase": {"enabled": True},
            "lowercase": {"enabled": True},
            "reverse": {"enabled": True},
            "word_count": {"enabled": True},
        },
    },
}

# Create MCP server with tool modules
mcp = ChukMCPServer(
    name="Multi-Module Demo", version="1.0.0", tool_modules_config=tool_modules_config, debug=True, port=8001
)


# You can still add local tools alongside the loaded modules
@mcp.tool
def local_hello(name: str = "World") -> str:
    """A local tool defined directly in this file."""
    return f"Hello from local tool, {name}!"


if __name__ == "__main__":
    print("🚀 Multi-Module Hosting Demo")
    print("=" * 60)
    print("This server hosts multiple tool modules:")
    print("  • math.* - Math operations (add, multiply, power)")
    print("  • text.* - Text operations (uppercase, lowercase, reverse, word_count)")
    print("  • local_hello - Local tool")
    print("")
    print("Example requests:")
    print("  curl -X POST http://localhost:8001/mcp \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -H "Mcp-Session-Id: demo-session" \\')
    print('    -d \'{"jsonrpc":"2.0","id":1,"method":"tools/list"}\'')
    print("")
    print("  curl -X POST http://localhost:8001/mcp \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -H "Mcp-Session-Id: demo-session" \\')
    print('    -d \'{"jsonrpc":"2.0","id":2,"method":"tools/call",')
    print('         "params":{"name":"math.add","arguments":{"a":5,"b":3}}}\'')
    print("=" * 60)
    print("")

    # Run the server
    mcp.run(log_level="info")
