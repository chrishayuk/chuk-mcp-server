#!/usr/bin/env python3
"""
Python MCP Inspector Script

A simple Python script that connects to an MCP server and inspects its capabilities,
tools, and resources. This behaves like the MCP Inspector but without the proxy.
"""

import asyncio
import json
import time
import aiohttp
import argparse
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class MCPClient:
    """Simple MCP client for testing servers."""
    
    server_url: str
    session: Optional[aiohttp.ClientSession] = None
    session_id: Optional[str] = None
    message_id: int = 0
    
    def __post_init__(self):
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Clean up the client session."""
        if self.session:
            await self.session.close()
    
    def next_id(self) -> int:
        """Get next message ID."""
        self.message_id += 1
        return self.message_id
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        if params is None:
            params = {}
        
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": method,
            "params": params
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        print(f"📤 Sending {method} request...")
        print(f"   Request: {json.dumps(request, indent=2)}")
        
        try:
            async with self.session.post(
                self.server_url,
                json=request,
                headers=headers
            ) as response:
                
                print(f"📥 Response status: {response.status}")
                
                if response.status != 200:
                    print(f"❌ HTTP Error: {response.status}")
                    return {"error": f"HTTP {response.status}"}
                
                # Check if session ID was returned
                if "Mcp-Session-Id" in response.headers:
                    self.session_id = response.headers["Mcp-Session-Id"]
                    print(f"🔑 Session ID: {self.session_id}")
                
                response_data = await response.json()
                print(f"   Response: {json.dumps(response_data, indent=2)}")
                
                return response_data
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return {"error": str(e)}
    
    async def initialize(self) -> bool:
        """Initialize connection with the MCP server."""
        print("🚀 Initializing MCP connection...")
        
        response = await self.send_request("initialize", {
            "protocolVersion": "2025-06-18",
            "clientInfo": {
                "name": "python-mcp-inspector",
                "version": "1.0.0"
            },
            "capabilities": {
                "sampling": {},
                "roots": {
                    "listChanged": True
                }
            }
        })
        
        if "error" in response:
            print(f"❌ Initialize failed: {response['error']}")
            return False
        
        if "result" in response:
            result = response["result"]
            print("✅ Connection initialized successfully!")
            print(f"   Protocol Version: {result.get('protocolVersion')}")
            print(f"   Server: {result.get('serverInfo', {}).get('name')}")
            print(f"   Version: {result.get('serverInfo', {}).get('version')}")
            return True
        
        return False
    
    async def send_initialized(self):
        """Send initialized notification."""
        print("📨 Sending initialized notification...")
        # This is a notification, so no response expected
        request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            async with self.session.post(
                self.server_url,
                json=request,
                headers=headers
            ) as response:
                print(f"📥 Initialized notification status: {response.status}")
        except Exception as e:
            print(f"❌ Failed to send initialized: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        print("🔧 Fetching tools...")
        
        response = await self.send_request("tools/list")
        
        if "error" in response:
            print(f"❌ Tools list failed: {response['error']}")
            return []
        
        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools")
            return tools
        
        return []
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """Get list of available resources."""
        print("📂 Fetching resources...")
        
        response = await self.send_request("resources/list")
        
        if "error" in response:
            print(f"❌ Resources list failed: {response['error']}")
            return []
        
        if "result" in response and "resources" in response["result"]:
            resources = response["result"]["resources"]
            print(f"✅ Found {len(resources)} resources")
            return resources
        
        return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool."""
        print(f"🛠️  Calling tool: {tool_name}")
        
        response = await self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        if "error" in response:
            print(f"❌ Tool call failed: {response['error']}")
            return response
        
        if "result" in response:
            print(f"✅ Tool call successful")
            return response["result"]
        
        return {}
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource."""
        print(f"📖 Reading resource: {uri}")
        
        response = await self.send_request("resources/read", {
            "uri": uri
        })
        
        if "error" in response:
            print(f"❌ Resource read failed: {response['error']}")
            return response
        
        if "result" in response:
            print(f"✅ Resource read successful")
            return response["result"]
        
        return {}


def print_tools(tools: List[Dict[str, Any]]):
    """Pretty print tools information."""
    if not tools:
        print("   No tools available")
        return
    
    print("\n🔧 Available Tools:")
    print("=" * 50)
    
    for tool in tools:
        name = tool.get("name", "Unknown")
        description = tool.get("description", "No description")
        
        print(f"   📌 {name}")
        print(f"      Description: {description}")
        
        schema = tool.get("inputSchema", {})
        if "properties" in schema:
            print(f"      Parameters:")
            for prop, details in schema["properties"].items():
                prop_type = details.get("type", "unknown")
                prop_desc = details.get("description", "")
                required = prop in schema.get("required", [])
                req_marker = " (required)" if required else ""
                print(f"        - {prop} ({prop_type}){req_marker}: {prop_desc}")
        
        print()


def print_resources(resources: List[Dict[str, Any]]):
    """Pretty print resources information."""
    if not resources:
        print("   No resources available")
        return
    
    print("\n📂 Available Resources:")
    print("=" * 50)
    
    for resource in resources:
        name = resource.get("name", "Unknown")
        uri = resource.get("uri", "")
        description = resource.get("description", "No description")
        mime_type = resource.get("mimeType", "unknown")
        
        print(f"   📄 {name}")
        print(f"      URI: {uri}")
        print(f"      Description: {description}")
        print(f"      MIME Type: {mime_type}")
        print()


async def inspect_server(server_url: str, interactive: bool = False):
    """Main inspection function."""
    print(f"🔍 MCP Server Inspector")
    print(f"📡 Connecting to: {server_url}")
    print("=" * 60)
    
    client = MCPClient(server_url)
    
    try:
        # Initialize connection
        if not await client.initialize():
            print("❌ Failed to initialize connection")
            return
        
        # Send initialized notification
        await client.send_initialized()
        
        # Get tools and resources
        tools = await client.list_tools()
        resources = await client.list_resources()
        
        # Display information
        print_tools(tools)
        print_resources(resources)
        
        # Interactive mode
        if interactive:
            await interactive_mode(client, tools, resources)
    
    finally:
        await client.close()


async def interactive_mode(client: MCPClient, tools: List[Dict[str, Any]], resources: List[Dict[str, Any]]):
    """Interactive mode for testing tools and resources."""
    print("\n🎮 Interactive Mode")
    print("Commands:")
    print("  tool <name> - Call a tool")
    print("  resource <uri> - Read a resource") 
    print("  list - Show tools and resources again")
    print("  quit - Exit")
    print("=" * 40)
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == "quit" or command == "exit":
                break
            elif command == "list":
                print_tools(tools)
                print_resources(resources)
            elif command.startswith("tool "):
                tool_name = command[5:].strip()
                if any(t["name"] == tool_name for t in tools):
                    # For demo, use simple arguments
                    if tool_name == "echo":
                        result = await client.call_tool(tool_name, {"text": "Hello from inspector!"})
                    elif tool_name == "calculate":
                        result = await client.call_tool(tool_name, {"expression": "2 + 2"})
                    else:
                        result = await client.call_tool(tool_name, {})
                    
                    if "content" in result:
                        for content in result["content"]:
                            if content.get("type") == "text":
                                print(f"📝 Result: {content.get('text')}")
                else:
                    print(f"❌ Tool '{tool_name}' not found")
            elif command.startswith("resource "):
                uri = command[9:].strip()
                if any(r["uri"] == uri for r in resources):
                    result = await client.read_resource(uri)
                    if "contents" in result:
                        for content in result["contents"]:
                            text = content.get("text", "")
                            if len(text) > 500:
                                text = text[:500] + "..."
                            print(f"📄 Content: {text}")
                else:
                    print(f"❌ Resource '{uri}' not found")
            else:
                print("❌ Unknown command")
        
        except KeyboardInterrupt:
            break
        except EOFError:
            break


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Python MCP Inspector")
    parser.add_argument(
        "server_url", 
        nargs="?",
        default="http://localhost:8011/mcp/inspector",
        help="MCP server URL (default: http://localhost:8011/mcp/inspector)"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Enable interactive mode for testing tools and resources"
    )
    
    args = parser.parse_args()
    
    await inspect_server(args.server_url, args.interactive)


if __name__ == "__main__":
    asyncio.run(main())