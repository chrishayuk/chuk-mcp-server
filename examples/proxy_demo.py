#!/usr/bin/env python3
"""
Complete Proxy Demo

This script demonstrates the proxy functionality by:
1. Starting a proxy server that connects to a simple backend
2. Showing how tools are namespaced
3. Running the server for testing with MCP Inspector
"""

import os
import sys

from chuk_mcp_server import ChukMCPServer

# Get the path to the backend server
backend_path = os.path.join(os.path.dirname(__file__), "simple_backend_server.py")

# Configure the proxy to connect to our simple backend
proxy_config = {
    "proxy": {
        "enabled": True,
        "namespace": "proxy",
    },
    "servers": {
        # Connect to our simple backend server
        "backend": {
            "type": "stdio",
            "command": sys.executable,  # Use current Python interpreter
            "args": [backend_path],
        },
    },
}

# Create the proxy server
mcp = ChukMCPServer(
    name="Proxy Demo Server",
    version="1.0.0",
    description="Demonstrates multi-server proxy functionality",
    proxy_config=proxy_config,
)


# Add some local tools to show mixing local + proxied
@mcp.tool
def proxy_status() -> dict:
    """Get the status of the proxy manager."""
    stats = mcp.get_proxy_stats()
    return {
        "status": "running" if stats else "not enabled",
        "details": stats,
    }


@mcp.tool
def list_servers() -> dict:
    """List all proxied servers."""
    stats = mcp.get_proxy_stats()
    if not stats:
        return {"error": "Proxy not enabled"}

    return {
        "total_servers": stats.get("servers", 0),
        "server_names": stats.get("server_names", []),
        "total_tools": stats.get("tools", 0),
        "namespace": stats.get("namespace", ""),
    }


@mcp.resource("config://proxy")
def proxy_configuration() -> dict:
    """Get the current proxy configuration."""
    return proxy_config


if __name__ == "__main__":
    print("🌐 ChukMCPServer Proxy Demo")
    print("=" * 70)
    print()
    print("This server proxies a simple backend MCP server and adds local tools.")
    print()
    print("🔧 Available Tools:")
    print()
    print("  LOCAL TOOLS (run on proxy server):")
    print("    - proxy_status: Check proxy manager status")
    print("    - list_servers: List all proxied servers")
    print()
    print("  PROXIED TOOLS (forwarded to backend):")
    print("    - proxy.backend.echo: Echo back a message")
    print("    - proxy.backend.greet: Greet someone by name")
    print("    - proxy.backend.add: Add two numbers")
    print("    - proxy.backend.uppercase: Convert text to uppercase")
    print()
    print("📚 Resources:")
    print("    - config://proxy: View proxy configuration")
    print()
    print("🧪 Test with MCP Inspector:")
    print("    1. Keep this server running")
    print("    2. Open MCP Inspector at https://inspector.anthropic.com")
    print("    3. Connect to: http://localhost:8000/mcp")
    print("    4. Try calling: proxy.backend.echo with message='Hello!'")
    print()
    print("📡 Server starting on http://localhost:8000")
    print("=" * 70)
    print()

    try:
        mcp.run(port=8000, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down proxy server...")
