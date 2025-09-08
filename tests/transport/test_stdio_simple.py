#!/usr/bin/env python3
"""Simple stdio transport test."""

import sys
import json
import asyncio
from chuk_mcp_server.transport.stdio import StdioTransport
from chuk_mcp_server.protocol import MCPProtocolHandler
from chuk_mcp_server.types import ServerInfo, create_server_capabilities

def test_stdio_directly():
    """Test stdio transport directly without subprocess."""
    print("Testing STDIO transport directly...")
    
    # Create server components
    server_info = ServerInfo(name="test-server", version="1.0.0")
    capabilities = create_server_capabilities(tools=True, resources=True)
    protocol = MCPProtocolHandler(server_info, capabilities)
    transport = StdioTransport(protocol)
    
    print("Components created successfully")
    
    # Test message handling directly
    test_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
            "protocolVersion": "2025-06-18"
        }
    }
    
    async def test_message_handling():
        """Test message handling."""
        try:
            response, session_id = await protocol.handle_request(test_message)
            print(f"Response: {json.dumps(response, indent=2)}")
            print(f"Session ID: {session_id}")
            return True
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Run the test
    result = asyncio.run(test_message_handling())
    print(f"Test result: {'PASSED' if result else 'FAILED'}")
    
    return result

if __name__ == "__main__":
    test_stdio_directly()