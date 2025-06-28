#!/usr/bin/env python3
"""
test_fast_server.py - Test script for the Fast MCP Server

Simple test to verify the server works correctly with the MCP protocol
and performs well with the quick_benchmark.py script.
"""

import asyncio
import aiohttp
import json
import time


async def test_mcp_server(base_url: str = "http://localhost:8000"):
    """Test the Fast MCP Server"""
    
    mcp_url = f"{base_url}/mcp"
    
    print("🧪 Testing Fast MCP Server")
    print(f"🔗 URL: {mcp_url}")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health check
        print("1️⃣  Testing health endpoint...")
        async with session.get(f"{base_url}/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ Health: {data['status']}")
                print(f"   📊 RPS: {data.get('requests_per_second', 0):.1f}")
            else:
                print(f"   ❌ Health check failed: {resp.status}")
        
        # Test 2: Server info
        print("\n2️⃣  Testing root endpoint...")
        async with session.get(base_url) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ Server: {data['server']} v{data['version']}")
                print(f"   📋 Protocol: {data['protocol']}")
            else:
                print(f"   ❌ Root endpoint failed: {resp.status}")
        
        # Test 3: MCP Initialize
        print("\n3️⃣  Testing MCP initialization...")
        headers = {"Content-Type": "application/json"}
        
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        session_id = None
        async with session.post(mcp_url, json=init_message, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ Initialized: {data['result']['serverInfo']['name']}")
                print(f"   📋 Protocol: {data['result']['protocolVersion']}")
                
                # Get session ID
                session_id = resp.headers.get('Mcp-Session-Id')
                if session_id:
                    headers['Mcp-Session-Id'] = session_id
                    print(f"   🔑 Session: {session_id[:8]}...")
            else:
                print(f"   ❌ Initialize failed: {resp.status}")
                text = await resp.text()
                print(f"   📄 Response: {text}")
                return
        
        # Test 4: Send initialized notification
        print("\n4️⃣  Sending initialized notification...")
        init_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        async with session.post(mcp_url, json=init_notif, headers=headers) as resp:
            if resp.status == 204:
                print("   ✅ Notification sent")
            else:
                print(f"   ⚠️  Notification response: {resp.status}")
        
        # Test 5: List tools
        print("\n5️⃣  Testing tools/list...")
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        async with session.post(mcp_url, json=tools_message, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                tools = data['result']['tools']
                print(f"   ✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"      • {tool['name']}: {tool['description']}")
            else:
                print(f"   ❌ Tools list failed: {resp.status}")
        
        # Test 6: List resources
        print("\n6️⃣  Testing resources/list...")
        resources_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {}
        }
        
        async with session.post(mcp_url, json=resources_message, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                resources = data['result']['resources']
                print(f"   ✅ Found {len(resources)} resources:")
                for resource in resources:
                    print(f"      • {resource['name']}: {resource['description']}")
            else:
                print(f"   ❌ Resources list failed: {resp.status}")
        
        # Test 7: Call a tool
        print("\n7️⃣  Testing tool execution...")
        call_message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {"a": 5, "b": 3}
            }
        }
        
        async with session.post(mcp_url, json=call_message, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                result = data['result']['content'][0]['text']
                print(f"   ✅ Tool result: {result}")
            else:
                print(f"   ❌ Tool call failed: {resp.status}")
        
        # Test 8: Read a resource
        print("\n8️⃣  Testing resource reading...")
        read_message = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/read",
            "params": {
                "uri": "demo://server-info"
            }
        }
        
        async with session.post(mcp_url, json=read_message, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                content = data['result']['contents'][0]
                print(f"   ✅ Resource read: {content['mimeType']}")
                print(f"   📄 Content preview: {content['text'][:100]}...")
            else:
                print(f"   ❌ Resource read failed: {resp.status}")
        
        # Test 9: Performance test
        print("\n9️⃣  Quick performance test...")
        start_time = time.time()
        
        ping_message = {"jsonrpc": "2.0", "id": 6, "method": "ping", "params": {}}
        
        # Send 10 ping requests
        for i in range(10):
            async with session.post(mcp_url, json=ping_message, headers=headers) as resp:
                if resp.status != 200:
                    print(f"   ❌ Ping {i+1} failed: {resp.status}")
                    break
        
        elapsed = time.time() - start_time
        rps = 10 / elapsed
        print(f"   ⚡ 10 pings in {elapsed:.3f}s = {rps:.1f} RPS")
        
        # Test 10: Metrics
        print("\n🔟 Testing metrics endpoint...")
        async with session.get(f"{base_url}/metrics") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ Total requests: {data['requests']['total']}")
                print(f"   📊 Current RPS: {data['requests']['per_second']:.1f}")
                print(f"   🔧 Tool calls: {data['mcp']['tool_calls']}")
                print(f"   📖 Resource reads: {data['mcp']['resource_reads']}")
            else:
                print(f"   ❌ Metrics failed: {resp.status}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")
    print("\nNext steps:")
    print("  • Run the server: python fast_mcp_server.py")
    print("  • Benchmark it: python quick_benchmark.py http://localhost:8000/mcp")
    print("  • Scale it up: python fast_mcp_server.py --workers 4")


async def benchmark_comparison():
    """Compare with your quick_benchmark.py if available"""
    print("\n🏁 Running benchmark comparison...")
    
    try:
        # Try to import and run the benchmark
        from quick_benchmark import QuickBenchmark
        
        benchmark = QuickBenchmark("http://localhost:8000/mcp", "Fast MCP Server")
        await benchmark.run_benchmark()
        
    except ImportError:
        print("💡 To run full benchmark:")
        print("   python quick_benchmark.py http://localhost:8000/mcp 'Fast MCP Server'")
    except Exception as e:
        print(f"⚠️  Benchmark error: {e}")


if __name__ == "__main__":
    import sys
    
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print("🚀 Fast MCP Server Test Suite")
    print("=" * 60)
    
    try:
        asyncio.run(test_mcp_server(base_url))
        
        # Optionally run benchmark
        if len(sys.argv) > 1 and sys.argv[1] == "--benchmark":
            asyncio.run(benchmark_comparison())
            
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")