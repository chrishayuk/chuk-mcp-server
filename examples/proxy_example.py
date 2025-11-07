#!/usr/bin/env python3
"""
ChukMCPServer Proxy Example

This example demonstrates how to use ChukMCPServer as a proxy/gateway
to multiple backend MCP servers.

Usage:
    python examples/proxy_example.py
"""

from chuk_mcp_server import ChukMCPServer

# Define proxy configuration
proxy_config = {
    "proxy": {
        "enabled": True,
        "namespace": "proxy",  # Tools will be exposed as proxy.<server>.<tool>
    },
    "servers": {
        # Example stdio server - you would replace this with actual servers
        "echo": {
            "type": "stdio",
            "command": "python",
            "args": ["-c", "import sys; sys.stdout.write(sys.stdin.read())"],
        },
        # Add more servers here:
        # "time": {
        #     "type": "stdio",
        #     "command": "uvx",
        #     "args": ["mcp-server-time"],
        # },
    },
}

# Create server with proxy configuration
mcp = ChukMCPServer(
    name="Proxy Gateway",
    version="1.0.0",
    proxy_config=proxy_config,
)


# You can still add local tools to the proxy server
@mcp.tool
def local_tool(message: str) -> str:
    """A local tool that runs on the proxy server itself."""
    return f"Local: {message}"


if __name__ == "__main__":
    print("🌐 Starting ChukMCPServer in Proxy Mode")
    print("=" * 60)
    print("Proxy configuration:")
    print(f"  - Namespace: {proxy_config['proxy']['namespace']}")
    print(f"  - Backend servers: {len(proxy_config['servers'])}")
    print()
    print("Tools will be exposed as:")
    for server_name in proxy_config["servers"]:
        print(f"  - proxy.{server_name}.<tool_name>")
    print()
    print("Starting server on http://localhost:8000")
    print("=" * 60)

    mcp.run(port=8000)
