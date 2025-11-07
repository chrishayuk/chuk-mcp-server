#!/usr/bin/env python3
"""
ChukMCPServer Multi-Server Proxy Example

This example demonstrates proxying multiple backend MCP servers
through a single ChukMCPServer instance.

Prerequisites:
    pip install mcp-server-time
    # Any other MCP servers you want to proxy

Usage:
    python examples/proxy_multi_server_example.py
"""

from chuk_mcp_server import ChukMCPServer

# Configure multiple backend servers
proxy_config = {
    "proxy": {
        "enabled": True,
        "namespace": "proxy",
    },
    "servers": {
        # Time server
        "time": {
            "type": "stdio",
            "command": "uvx",
            "args": ["mcp-server-time"],
        },
        # Add more servers here:
        # "weather": {
        #     "type": "stdio",
        #     "command": "python",
        #     "args": ["-m", "weather_server"],
        # },
        # "database": {
        #     "type": "stdio",
        #     "command": "node",
        #     "args": ["database-mcp-server.js"],
        # },
    },
}

# Create the proxy server
mcp = ChukMCPServer(
    name="Multi-Server Gateway",
    version="1.0.0",
    description="A gateway that proxies multiple MCP servers",
    proxy_config=proxy_config,
)


# Add local orchestration tools
@mcp.tool
async def get_system_status() -> dict:
    """Get status of all proxied servers."""
    stats = mcp.get_proxy_stats()
    return {
        "status": "running" if stats else "no proxy",
        "proxy_stats": stats,
    }


@mcp.resource("config://proxy")
def get_proxy_config() -> dict:
    """Get current proxy configuration."""
    return proxy_config


if __name__ == "__main__":
    print("🌐 ChukMCPServer - Multi-Server Proxy")
    print("=" * 60)
    print()
    print(f"Proxying {len(proxy_config['servers'])} backend servers:")
    for name, config in proxy_config["servers"].items():
        cmd = config.get("command", "")
        print(f"  - {name}: {cmd} {' '.join(config.get('args', []))}")
    print()
    print("All tools will be namespaced as:")
    print("  proxy.<server_name>.<tool_name>")
    print()
    print("Local management tools:")
    print("  - get_system_status: Check proxy status")
    print()
    print("Resources:")
    print("  - config://proxy: View proxy configuration")
    print()
    print("Starting server on http://localhost:8000...")
    print("=" * 60)

    try:
        mcp.run(port=8000, debug=True)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down proxy server...")
