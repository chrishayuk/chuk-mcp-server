#!/usr/bin/env python3
"""
MCP Server Diagnostic Tool

Quick diagnostic to check MCP server availability and endpoints.
"""

import asyncio
import httpx
import json
import sys


async def diagnose_mcp_server(base_url: str = "http://localhost:8001"):
    """Diagnose MCP server availability and endpoints"""
    print("🔍 ChukMCPServer Diagnostic Tool")
    print("=" * 50)
    print(f"Testing server: {base_url}")
    print()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        # Test 1: Basic connectivity
        print("1. 🌐 Testing basic connectivity...")
        try:
            response = await client.get(f"{base_url}/ping")
            if response.status_code == 200:
                print(f"   ✅ Server responding on /ping ({response.status_code})")
                ping_data = response.json()
                print(f"   📊 Response: {ping_data}")
            else:
                print(f"   ❌ Ping failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False
        
        # Test 2: Health check
        print("\n2. 🏥 Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print(f"   ✅ Health endpoint working ({response.status_code})")
                health_data = response.json()
                print(f"   📊 Health: {health_data}")
            else:
                print(f"   ⚠️  Health endpoint issue: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
        
        # Test 3: MCP endpoint availability
        print("\n3. 🎯 Testing MCP endpoint...")
        try:
            response = await client.get(f"{base_url}/mcp")
            if response.status_code == 200:
                print(f"   ✅ MCP endpoint responding ({response.status_code})")
                mcp_data = response.json()
                print(f"   📊 MCP Info: {mcp_data.get('name', 'Unknown')} v{mcp_data.get('version', 'Unknown')}")
            else:
                print(f"   ❌ MCP endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ MCP endpoint error: {e}")
            return False
        
        # Test 4: MCP Initialize
        print("\n4. 🤝 Testing MCP initialize...")
        try:
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "diagnostic-tool", "version": "1.0.0"}
                }
            }
            
            response = await client.post(f"{base_url}/mcp", json=init_message)
            if response.status_code == 200:
                print(f"   ✅ MCP initialize successful ({response.status_code})")
                init_data = response.json()
                
                session_id = response.headers.get('Mcp-Session-Id')
                if session_id:
                    print(f"   🔑 Session ID: {session_id[:8]}...")
                else:
                    print("   ⚠️  No session ID returned")
                
                if 'result' in init_data:
                    server_info = init_data['result'].get('serverInfo', {})
                    capabilities = init_data['result'].get('capabilities', {})
                    print(f"   📋 Server: {server_info.get('name')} v{server_info.get('version')}")
                    print(f"   🔧 Capabilities: {list(capabilities.keys())}")
                    
                    # Test 5: Tools list
                    print("\n5. 🔧 Testing tools list...")
                    headers = {'Mcp-Session-Id': session_id} if session_id else {}
                    tools_message = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    }
                    
                    tools_response = await client.post(f"{base_url}/mcp", json=tools_message, headers=headers)
                    if tools_response.status_code == 200:
                        tools_data = tools_response.json()
                        if 'result' in tools_data and 'tools' in tools_data['result']:
                            tools = tools_data['result']['tools']
                            print(f"   ✅ Tools list successful ({len(tools)} tools)")
                            for tool in tools[:3]:  # Show first 3 tools
                                print(f"      - {tool['name']}: {tool.get('description', 'No description')[:50]}...")
                        else:
                            print(f"   ❌ Tools list failed: {tools_data}")
                    else:
                        print(f"   ❌ Tools list HTTP error: {tools_response.status_code}")
                    
                    # Test 6: Resources list
                    print("\n6. 📂 Testing resources list...")
                    resources_message = {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "resources/list",
                        "params": {}
                    }
                    
                    resources_response = await client.post(f"{base_url}/mcp", json=resources_message, headers=headers)
                    if resources_response.status_code == 200:
                        resources_data = resources_response.json()
                        if 'result' in resources_data and 'resources' in resources_data['result']:
                            resources = resources_data['result']['resources']
                            print(f"   ✅ Resources list successful ({len(resources)} resources)")
                            for resource in resources:
                                print(f"      - {resource['uri']}: {resource.get('name', 'No name')}")
                        else:
                            print(f"   ❌ Resources list failed: {resources_data}")
                    else:
                        print(f"   ❌ Resources list HTTP error: {resources_response.status_code}")
                    
                    # Test 7: Simple tool call
                    if tools and len(tools) > 0:
                        print("\n7. 🚀 Testing simple tool call...")
                        first_tool = tools[0]
                        tool_call_message = {
                            "jsonrpc": "2.0",
                            "id": 4,
                            "method": "tools/call",
                            "params": {
                                "name": first_tool['name'],
                                "arguments": {"name": "DiagnosticTest", "delay": 0.001} if first_tool['name'] == 'async_hello' else {}
                            }
                        }
                        
                        tool_response = await client.post(f"{base_url}/mcp", json=tool_call_message, headers=headers)
                        if tool_response.status_code == 200:
                            tool_data = tool_response.json()
                            if 'result' in tool_data:
                                print(f"   ✅ Tool call successful: {first_tool['name']}")
                                print(f"   📊 Response length: {len(str(tool_data['result']))} chars")
                            else:
                                print(f"   ❌ Tool call failed: {tool_data}")
                        else:
                            print(f"   ❌ Tool call HTTP error: {tool_response.status_code}")
                
                else:
                    print(f"   ❌ MCP initialize failed: {init_data}")
                    return False
            else:
                print(f"   ❌ MCP initialize HTTP error: {response.status_code}")
                response_text = await response.aread()
                print(f"   📄 Response: {response_text.decode()[:200]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ MCP initialize exception: {e}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 MCP server diagnostic completed successfully!")
        print("✅ Server is ready for performance testing")
        return True


async def main():
    """Main diagnostic entry point"""
    base_url = "http://localhost:8001"
    
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("http"):
            base_url = sys.argv[1]
        else:
            port = int(sys.argv[1])
            base_url = f"http://localhost:{port}"
    
    success = await diagnose_mcp_server(base_url)
    
    if not success:
        print("\n❌ Diagnostic failed. Check server logs and configuration.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())