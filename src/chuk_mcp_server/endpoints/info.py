#!/usr/bin/env python3
# chuk_mcp_server/endpoints/info.py
"""
Info Endpoint - Provides comprehensive server information and documentation
"""

import logging
from typing import Dict, Any

import orjson
from starlette.requests import Request
from starlette.responses import Response

from ..protocol import MCPProtocolHandler

logger = logging.getLogger(__name__)


class InfoEndpoint:
    """Server information endpoint with comprehensive documentation."""
    
    def __init__(self, protocol_handler: MCPProtocolHandler):
        self.protocol = protocol_handler
    
    async def handle_request(self, request: Request) -> Response:
        """Handle server information request."""
        
        if request.method == "GET":
            return await self._handle_info_request(request)
        else:
            return Response("Method not allowed", status_code=405)
    
    async def _handle_info_request(self, request: Request) -> Response:
        """Return comprehensive server information."""
        
        base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost')}"
        
        # Build comprehensive server information
        info = {
            "server": self.protocol.server_info.to_dict(),
            "capabilities": self.protocol.capabilities.to_dict(),
            "protocol": {
                "version": "MCP 2025-03-26",
                "transport": "HTTP with SSE",
                "inspector_compatible": True
            },
            "framework": {
                "name": "CleanMCP",
                "powered_by": "chuk_mcp",
                "features": [
                    "Type-safe tools with automatic schema generation",
                    "Rich resources with multiple MIME types", 
                    "Perfect Inspector compatibility",
                    "SSE streaming support",
                    "Robust session management",
                    "Comprehensive error handling",
                    "Modular architecture"
                ]
            },
            "endpoints": {
                "mcp": f"{base_url}/mcp",
                "health": f"{base_url}/health",
                "info": f"{base_url}/",
                "documentation": f"{base_url}/?format=docs"
            },
            "tools": {
                "count": len(self.protocol.tools),
                "available": list(self.protocol.tools.keys()),
                "details": self._get_tools_details()
            },
            "resources": {
                "count": len(self.protocol.resources),
                "available": list(self.protocol.resources.keys()),
                "details": self._get_resources_details()
            },
            "quick_start": {
                "health_check": f"curl {base_url}/health",
                "mcp_initialize": self._get_initialize_example(base_url),
                "inspector_setup": {
                    "transport": "Streamable HTTP",
                    "url": "Use proxy pointing to this server",
                    "note": "Fully compatible with MCP Inspector"
                }
            },
            "examples": self._get_usage_examples()
        }
        
        # Return different formats based on query parameter
        format_type = request.query_params.get("format", "json").lower()
        
        if format_type == "docs":
            return self._render_documentation(info, base_url)
        else:
            return Response(
                orjson.dumps(info, option=orjson.OPT_INDENT_2),
                media_type="application/json",
                headers={
                    "Cache-Control": "public, max-age=300",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    
    def _get_tools_details(self) -> Dict[str, Any]:
        """Get detailed information about all tools."""
        tools_details = {}
        
        for tool_name, tool in self.protocol.tools.items():
            tools_details[tool_name] = {
                "name": tool.name,
                "description": tool.description,
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type,
                        "required": param.required,
                        "description": param.description,
                        "default": param.default
                    }
                    for param in tool.parameters
                ],
                "schema": tool.to_mcp_format()["inputSchema"]
            }
        
        return tools_details
    
    def _get_resources_details(self) -> Dict[str, Any]:
        """Get detailed information about all resources."""
        resources_details = {}
        
        for resource_uri, resource in self.protocol.resources.items():
            resources_details[resource_uri] = {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mime_type,
                "schema": resource.to_mcp_format()
            }
        
        return resources_details
    
    def _get_initialize_example(self, base_url: str) -> str:
        """Get MCP initialize example command."""
        return (
            f'curl -X POST {base_url}/mcp '
            f'-H "Content-Type: application/json" '
            f'-d \'{{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{{\"protocolVersion\":\"2025-03-26\",\"clientInfo\":{{\"name\":\"test\",\"version\":\"1.0\"}}}}}}\''
        )
    
    def _get_usage_examples(self) -> Dict[str, Any]:
        """Get usage examples for tools and resources."""
        return {
            "tool_calls": [
                {
                    "description": "Call a tool",
                    "method": "tools/call",
                    "example": {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": "hello" if "hello" in self.protocol.tools else list(self.protocol.tools.keys())[0] if self.protocol.tools else "example_tool",
                            "arguments": {"name": "World"} if "hello" in self.protocol.tools else {}
                        }
                    }
                }
            ],
            "resource_reads": [
                {
                    "description": "Read a resource",
                    "method": "resources/read", 
                    "example": {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "resources/read",
                        "params": {
                            "uri": list(self.protocol.resources.keys())[0] if self.protocol.resources else "example://resource"
                        }
                    }
                }
            ],
            "basic_flow": [
                "1. Initialize connection with server",
                "2. List available tools and resources",
                "3. Call tools or read resources as needed",
                "4. Handle responses and errors appropriately"
            ]
        }
    
    def _render_documentation(self, info: Dict[str, Any], base_url: str) -> Response:
        """Render human-readable documentation."""
        
        docs = f"""# {info['server']['name']} - CleanMCP Server

**Version:** {info['server']['version']}  
**Protocol:** {info['protocol']['version']}  
**Framework:** {info['framework']['name']} powered by {info['framework']['powered_by']}

## 🚀 Features

"""
        
        for feature in info['framework']['features']:
            docs += f"- {feature}\n"
        
        docs += f"""
## 🔧 Available Tools ({info['tools']['count']})

"""
        
        for tool_name in info['tools']['available']:
            tool_details = info['tools']['details'][tool_name]
            docs += f"### {tool_name}\n\n"
            docs += f"{tool_details['description']}\n\n"
            
            if tool_details['parameters']:
                docs += "**Parameters:**\n"
                for param in tool_details['parameters']:
                    required = "required" if param['required'] else "optional"
                    docs += f"- `{param['name']}` ({param['type']}, {required}): {param.get('description', 'No description')}\n"
                docs += "\n"
        
        docs += f"""
## 📂 Available Resources ({info['resources']['count']})

"""
        
        for resource_uri in info['resources']['available']:
            resource_details = info['resources']['details'][resource_uri]
            docs += f"### {resource_details['name']}\n\n"
            docs += f"**URI:** `{resource_details['uri']}`  \n"
            docs += f"**MIME Type:** `{resource_details['mimeType']}`  \n"
            docs += f"**Description:** {resource_details['description']}\n\n"
        
        docs += f"""
## 🔗 Endpoints

- **MCP Protocol:** `{info['endpoints']['mcp']}`
- **Health Check:** `{info['endpoints']['health']}`
- **Server Info:** `{info['endpoints']['info']}`

## 🔍 MCP Inspector Setup

1. **Transport Type:** Streamable HTTP
2. **URL:** Use proxy pointing to `{info['endpoints']['mcp']}`
3. **Compatibility:** Fully supported with SSE streaming

## 🚀 Quick Start

```bash
# Health check
{info['quick_start']['health_check']}

# Initialize MCP connection
{info['quick_start']['mcp_initialize']}
```

## 📖 Example Tool Call

```json
{orjson.dumps(info['examples']['tool_calls'][0]['example'], option=orjson.OPT_INDENT_2).decode()}
```

## 📖 Example Resource Read

```json
{orjson.dumps(info['examples']['resource_reads'][0]['example'], option=orjson.OPT_INDENT_2).decode()}
```

---

**Powered by CleanMCP with chuk_mcp integration** 🚀
"""
        
        return Response(
            docs,
            media_type="text/markdown",
            headers={
                "Cache-Control": "public, max-age=300",
                "Access-Control-Allow-Origin": "*"
            }
        )