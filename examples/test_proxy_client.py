#!/usr/bin/env python3
"""
Test Proxy Client

This script demonstrates how to call proxied tools using the MCP protocol.
It connects to a running proxy server and calls both local and proxied tools.

Usage:
    1. Start the proxy server: python examples/proxy_demo.py
    2. In another terminal: python examples/test_proxy_client.py
"""

import asyncio
import json

import aiohttp


async def call_tool(session: aiohttp.ClientSession, tool_name: str, arguments: dict) -> dict:
    """Call a tool via MCP HTTP endpoint."""
    url = "http://localhost:8000/mcp"

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }

    async with session.post(url, json=request) as response:
        result = await response.json()
        return result


async def list_tools(session: aiohttp.ClientSession) -> dict:
    """List all available tools."""
    url = "http://localhost:8000/mcp"

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }

    async with session.post(url, json=request) as response:
        result = await response.json()
        return result


async def main():
    """Run the test client."""
    print("🧪 Testing Proxy Server")
    print("=" * 70)
    print()

    async with aiohttp.ClientSession() as session:
        # 1. List all tools
        print("1️⃣  Listing all available tools...")
        tools_response = await list_tools(session)

        if "result" in tools_response:
            tools = tools_response["result"]["tools"]
            print(f"   Found {len(tools)} tools:")
            for tool in tools:
                name = tool.get("name", "unknown")
                desc = tool.get("description", "")[:50]
                print(f"     - {name}: {desc}")
        print()

        # 2. Call a local tool
        print("2️⃣  Calling local tool: proxy_status")
        result = await call_tool(session, "proxy_status", {})
        print(f"   Result: {json.dumps(result.get('result', {}), indent=2)}")
        print()

        # 3. Call a proxied tool - echo
        print("3️⃣  Calling proxied tool: proxy.backend.echo")
        result = await call_tool(session, "proxy.backend.echo", {"message": "Hello from proxy!"})
        print(f"   Result: {json.dumps(result.get('result', {}), indent=2)}")
        print()

        # 4. Call a proxied tool - greet
        print("4️⃣  Calling proxied tool: proxy.backend.greet")
        result = await call_tool(session, "proxy.backend.greet", {"name": "Alice"})
        print(f"   Result: {json.dumps(result.get('result', {}), indent=2)}")
        print()

        # 5. Call a proxied tool - add
        print("5️⃣  Calling proxied tool: proxy.backend.add")
        result = await call_tool(session, "proxy.backend.add", {"a": 42, "b": 58})
        print(f"   Result: {json.dumps(result.get('result', {}), indent=2)}")
        print()

        # 6. Call a proxied tool - uppercase
        print("6️⃣  Calling proxied tool: proxy.backend.uppercase")
        result = await call_tool(session, "proxy.backend.uppercase", {"text": "proxy works!"})
        print(f"   Result: {json.dumps(result.get('result', {}), indent=2)}")
        print()

        # 7. Call list_servers
        print("7️⃣  Calling local tool: list_servers")
        result = await call_tool(session, "list_servers", {})
        print(f"   Result: {json.dumps(result.get('result', {}), indent=2)}")
        print()

    print("=" * 70)
    print("✅ All tests completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the proxy server is running:")
        print("  python examples/proxy_demo.py")
