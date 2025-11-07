#!/usr/bin/env python3
"""
Simplified proxy test to debug the issue.
"""

import asyncio
import logging
import sys

from chuk_mcp_server import ChukMCPServer

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Simple proxy config
proxy_config = {
    "proxy": {
        "enabled": True,
        "namespace": "proxy",
    },
    "servers": {
        "backend": {
            "type": "stdio",
            "command": sys.executable,
            "args": ["examples/simple_backend_server.py"],
        },
    },
}

print("Creating server...")
mcp = ChukMCPServer(proxy_config=proxy_config)

print("Starting proxy...")


async def test_proxy():
    """Test proxy startup."""
    if mcp.proxy_manager:
        print("Proxy manager exists")
        try:
            print("Calling start_servers()...")
            await mcp.proxy_manager.start_servers()
            print(f"Proxy started: {mcp.proxy_manager.get_stats()}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("No proxy manager")


if __name__ == "__main__":
    asyncio.run(test_proxy())
