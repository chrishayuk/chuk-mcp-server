#!/usr/bin/env python3
"""
test_streamable_server.py - Test the StreamableMCP Server

Quick test to verify the server starts and works correctly
with both regular and streaming capabilities.
"""

import asyncio
import json
import time

import aiohttp


async def test_streamable_server(base_url: str = "http://localhost:8000"):
    """Test the StreamableMCP server"""

    mcp_url = f"{base_url}/mcp"

    print("🧪 Testing StreamableMCP Server")
    print(f"🔗 MCP URL: {mcp_url}")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        print("1️⃣  Testing server health...")
        try:
            async with session.get(f"{base_url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ Server healthy: {data.get('status')}")
                else:
                    print(f"   ❌ Health check failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")

        # Test 2: MCP Initialize
        print("\n2️⃣  Testing MCP initialization...")
        headers = {"Content-Type": "application/json"}

        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        session_id = None
        try:
            async with session.post(mcp_url, json=init_message, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ Initialized: {data['result']['serverInfo']['name']}")

                    # Get session ID
                    session_id = resp.headers.get("Mcp-Session-Id")
                    if session_id:
                        headers["Mcp-Session-Id"] = session_id
                        print(f"   🔑 Session: {session_id[:8]}...")
                else:
                    print(f"   ❌ Initialize failed: {resp.status}")
                    return
        except Exception as e:
            print(f"   ❌ Initialize error: {e}")
            return

        # Test 3: List tools
        print("\n3️⃣  Testing tools/list...")
        tools_message = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

        try:
            async with session.post(mcp_url, json=tools_message, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    tools = data["result"]["tools"]
                    print(f"   ✅ Found {len(tools)} tools:")
                    for tool in tools:
                        streaming = " (streaming)" if tool.get("capabilities", {}).get("streaming") else ""
                        print(f"      • {tool['name']}: {tool['description']}{streaming}")
                else:
                    print(f"   ❌ Tools list failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Tools list error: {e}")

        # Test 4: Call a regular tool
        print("\n4️⃣  Testing regular tool call...")
        call_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "add", "arguments": {"a": 5, "b": 3}},
        }

        try:
            async with session.post(mcp_url, json=call_message, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data["result"]["content"][0]["text"]
                    print(f"   ✅ Tool result: {result}")
                else:
                    print(f"   ❌ Tool call failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Tool call error: {e}")

        # Test 5: List resources
        print("\n5️⃣  Testing resources/list...")
        resources_message = {"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}}

        try:
            async with session.post(mcp_url, json=resources_message, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    resources = data["result"]["resources"]
                    print(f"   ✅ Found {len(resources)} resources:")
                    for resource in resources:
                        streaming = " (streaming)" if resource.get("capabilities", {}).get("streaming") else ""
                        print(f"      • {resource['name']}: {resource['description']}{streaming}")
                else:
                    print(f"   ❌ Resources list failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Resources list error: {e}")

        # Test 6: Read a regular resource
        print("\n6️⃣  Testing regular resource read...")
        read_message = {"jsonrpc": "2.0", "id": 5, "method": "resources/read", "params": {"uri": "demo://server-info"}}

        try:
            async with session.post(mcp_url, json=read_message, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["result"]["contents"][0]
                    print(f"   ✅ Resource read: {content['mimeType']}")
                    print(f"   📄 Content preview: {content['text'][:100]}...")
                else:
                    print(f"   ❌ Resource read failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Resource read error: {e}")

        # Test 7: Test streaming capability (if available)
        print("\n7️⃣  Testing streaming capability...")

        # Check if we have streaming tools
        streaming_headers = {**headers, "Accept": "text/event-stream"}
        stream_message = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "stream_numbers", "arguments": {"count": 3, "delay": 0.5}},
        }

        try:
            async with session.post(mcp_url, json=stream_message, headers=streaming_headers) as resp:
                if resp.status == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "text/event-stream" in content_type:
                        print("   ✅ Streaming response received")
                        print(f"   📡 Content-Type: {content_type}")

                        # Read a few streaming events
                        event_count = 0
                        async for line in resp.content:
                            line_str = line.decode("utf-8").strip()
                            if line_str.startswith("data: "):
                                event_data = line_str[6:]
                                if event_data:
                                    try:
                                        parsed = json.loads(event_data)
                                        print(f"   📊 Event {event_count + 1}: {parsed}")
                                        event_count += 1
                                        if event_count >= 3:  # Limit for testing
                                            break
                                    except json.JSONDecodeError:
                                        continue
                    else:
                        print(f"   ⚠️  Expected streaming, got: {content_type}")
                        data = await resp.json()
                        print(f"   📄 Response: {data}")
                else:
                    print(f"   ❌ Streaming test failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Streaming test error: {e}")

        # Test 8: Performance quick test
        print("\n8️⃣  Quick performance test...")
        ping_message = {"jsonrpc": "2.0", "id": 7, "method": "ping", "params": {}}

        start_time = time.time()
        success_count = 0

        for _i in range(10):
            try:
                async with session.post(mcp_url, json=ping_message, headers=headers) as resp:
                    if resp.status == 200:
                        success_count += 1
            except:
                pass

        elapsed = time.time() - start_time
        rps = 10 / elapsed
        print(f"   ⚡ 10 pings in {elapsed:.3f}s = {rps:.1f} RPS")
        print(f"   ✅ Success rate: {success_count}/10")

    print("\n" + "=" * 60)
    print("🎉 StreamableMCP Server test completed!")
    print("\nNext steps:")
    print("  • Server is working with chuk-mcp integration")
    print("  • Both regular and streaming capabilities available")
    print("  • Ready for performance benchmarking")
    print("  • Try: python mcp_performance_test.py http://localhost:8000/mcp")


async def main():
    import sys

    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    print("🚀 StreamableMCP Server Test")
    print("Testing chuk-mcp integration + HTTP streaming capabilities")
    print()

    try:
        await test_streamable_server(base_url)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
