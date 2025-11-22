#!/usr/bin/env python3
"""
ChukMCPServer Proxy Example with Time Server

This example shows how to proxy the official mcp-server-time package.

Prerequisites:
    pip install mcp-server-time
    # or
    uvx mcp-server-time

Usage:
    python examples/proxy_time_example.py
"""

from chuk_mcp_server import ChukMCPServer

# Configure proxy to connect to mcp-server-time
proxy_config = {
    "proxy": {
        "enabled": True,
        "namespace": "proxy",
    },
    "servers": {
        "time": {
            "type": "stdio",
            "command": "uvx",
            "args": ["mcp-server-time", "--local-timezone", "UTC"],
        },
    },
}

# Create server
mcp = ChukMCPServer(
    name="Time Proxy Server",
    version="1.0.0",
    proxy_config=proxy_config,
)


# Add a local tool that uses the proxied time tool
@mcp.tool
async def get_time_with_greeting(name: str = "World") -> dict:
    """Get current time with a personalized greeting."""
    # Note: In a real implementation, you would call the proxied tool here
    # For now, this is just a demonstration of combining local and proxied tools

    return {
        "greeting": f"Hello, {name}!",
        "message": "Use proxy.time.get_current_time to get the actual time",
    }


if __name__ == "__main__":
    print("⏰ ChukMCPServer - Time Server Proxy Example")
    print("=" * 60)
    print()
    print("This server proxies the official mcp-server-time package.")
    print()
    print("Available tools:")
    print("  - proxy.time.get_current_time - Get current time (proxied)")
    print("  - get_time_with_greeting - Local tool with greeting")
    print()
    print("Test with MCP Inspector:")
    print("  1. Start this server: python examples/proxy_time_example.py")
    print("  2. Open MCP Inspector")
    print("  3. Connect to http://localhost:8000/mcp")
    print("  4. Call proxy.time.get_current_time")
    print()
    print("Starting server on http://localhost:8000...")
    print("=" * 60)

    mcp.run(port=8000)
