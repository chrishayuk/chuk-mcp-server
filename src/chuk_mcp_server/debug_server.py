#!/usr/bin/env python3
"""
Updated MCP HTTP Server - Full Inspector Compatible

Key fixes based on debug output:
1. Server was returning empty tools[] - now has proper tools
2. Improved SSE response formatting for Inspector
3. Better session handling
4. Fixed notification responses (should be empty, not missing)
5. Enhanced protocol compatibility
"""

import asyncio
import json
import time
import uuid
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

import orjson
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Server State Management
# ============================================================================

@dataclass
class ServerMetrics:
    """Server performance metrics."""
    start_time: float
    total_requests: int = 0
    tool_calls: int = 0
    resource_reads: int = 0
    errors: int = 0
    
    def uptime(self) -> float:
        return time.time() - self.start_time
    
    def rps(self) -> float:
        uptime = self.uptime()
        return self.total_requests / max(uptime, 0.1)


@dataclass
class ServerState:
    """Centralized server state management."""
    metrics: ServerMetrics
    sessions: Dict[str, Dict[str, Any]]
    
    def create_session(self, client_info: Dict[str, Any], protocol_version: str) -> str:
        """Create a new session."""
        session_id = str(uuid.uuid4()).replace("-", "")
        self.sessions[session_id] = {
            "id": session_id,
            "client_info": client_info,
            "protocol_version": protocol_version,
            "created_at": time.time(),
            "last_activity": time.time()
        }
        return session_id
    
    def update_session_activity(self, session_id: str):
        """Update session last activity."""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = time.time()
    
    def increment_requests(self):
        self.metrics.total_requests += 1
    
    def increment_tool_calls(self):
        self.metrics.tool_calls += 1
    
    def increment_resource_reads(self):
        self.metrics.resource_reads += 1
    
    def increment_errors(self):
        self.metrics.errors += 1


# Global server state
server_state = ServerState(
    metrics=ServerMetrics(start_time=time.time()),
    sessions={}
)


# ============================================================================
# Enhanced MCP Server Core
# ============================================================================

class EnhancedMCPHTTPServer:
    """Enhanced HTTP MCP Server with full Inspector compatibility."""
    
    def __init__(self):
        # Server info - matches your working chuk_mcp server
        self.server_info = {
            "name": "FastMCP",
            "version": "1.9.4",
            "title": "Enhanced MCP HTTP Server - Inspector Compatible"
        }
        
        # Server capabilities - exactly what Inspector expects
        self.capabilities = {
            "experimental": {},
            "prompts": {"listChanged": True},
            "resources": {"subscribe": False, "listChanged": True},
            "tools": {"listChanged": True}
        }
        
        # Tool and resource storage
        self.tools: List[Dict[str, Any]] = []
        self.resources: List[Dict[str, Any]] = []
        
        # Register built-in capabilities
        self._register_builtin_tools()
        self._register_builtin_resources()
        
        logger.info(f"🚀 {self.server_info['name']} initialized")
        logger.info(f"🔧 Tools: {len(self.tools)}, Resources: {len(self.resources)}")
    
    def _register_builtin_tools(self):
        """Register comprehensive set of tools for Inspector."""
        
        # Calculator tool
        calculator_tool = {
            "name": "calculate",
            "description": "Perform mathematical calculations with support for basic operations",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sqrt(16)', 'sin(3.14/2)')"
                    }
                },
                "required": ["expression"]
            }
        }
        self.tools.append(calculator_tool)
        
        # Text processing tool
        text_tool = {
            "name": "text_process",
            "description": "Process and transform text with various operations",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to process"},
                    "operation": {
                        "type": "string",
                        "enum": ["uppercase", "lowercase", "title", "reverse", "word_count", "char_count", "lines"],
                        "description": "Operation to perform on the text"
                    }
                },
                "required": ["text", "operation"]
            }
        }
        self.tools.append(text_tool)
        
        # System info tool
        system_tool = {
            "name": "system_info",
            "description": "Get detailed server and system information",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["server", "system", "performance", "tools", "capabilities"],
                        "description": "Category of information to retrieve"
                    }
                },
                "required": ["category"]
            }
        }
        self.tools.append(system_tool)
        
        # Echo tool for testing
        echo_tool = {
            "name": "echo",
            "description": "Echo back the input for testing purposes",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to echo back"
                    }
                },
                "required": ["message"]
            }
        }
        self.tools.append(echo_tool)
        
        # Random generator tool
        random_tool = {
            "name": "random_generate",
            "description": "Generate random data (numbers, strings, UUIDs)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["number", "string", "uuid"],
                        "description": "Type of random data to generate"
                    },
                    "min": {"type": "integer", "description": "Minimum value (for numbers)", "default": 1},
                    "max": {"type": "integer", "description": "Maximum value (for numbers)", "default": 100},
                    "length": {"type": "integer", "description": "Length (for strings)", "default": 10}
                },
                "required": ["type"]
            }
        }
        self.tools.append(random_tool)
        
        logger.info(f"🔧 Registered {len(self.tools)} tools")
    
    def _register_builtin_resources(self):
        """Register resources for Inspector."""
        
        # Server status resource
        status_resource = {
            "uri": "server://status",
            "name": "Live Server Status",
            "description": "Real-time server status and performance metrics",
            "mimeType": "application/json"
        }
        self.resources.append(status_resource)
        
        # API documentation
        docs_resource = {
            "uri": "server://docs",
            "name": "API Documentation",
            "description": "Complete API documentation with examples",
            "mimeType": "text/markdown"
        }
        self.resources.append(docs_resource)
        
        # Live metrics
        metrics_resource = {
            "uri": "server://metrics",
            "name": "Live Metrics",
            "description": "Real-time server metrics",
            "mimeType": "application/json"
        }
        self.resources.append(metrics_resource)
        
        logger.info(f"📂 Registered {len(self.resources)} resources")
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return result."""
        server_state.increment_tool_calls()
        
        try:
            if name == "calculate":
                expression = arguments.get("expression", "")
                return await self._calculate(expression)
            elif name == "text_process":
                text = arguments.get("text", "")
                operation = arguments.get("operation", "")
                return await self._text_process(text, operation)
            elif name == "system_info":
                category = arguments.get("category", "server")
                return await self._system_info(category)
            elif name == "echo":
                message = arguments.get("message", "")
                return f"Echo: {message}"
            elif name == "random_generate":
                type_val = arguments.get("type", "number")
                return await self._random_generate(type_val, arguments)
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            logger.error(f"Tool execution error for {name}: {e}")
            return f"Error executing {name}: {str(e)}"
    
    async def _calculate(self, expression: str) -> str:
        """Safe math expression evaluator."""
        import math
        import re
        
        try:
            # Allow mathematical functions and constants
            safe_dict = {
                "__builtins__": {},
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow,
                "math": math, "pi": math.pi, "e": math.e,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "exp": math.exp, "floor": math.floor, "ceil": math.ceil
            }
            
            # Basic safety check
            if re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s*\(', expression):
                # Contains function calls, check if they're allowed
                allowed_funcs = set(safe_dict.keys()) | {"math"}
                used_funcs = set(re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', expression))
                
                disallowed = used_funcs - allowed_funcs
                if disallowed:
                    return f"Error: Disallowed functions: {', '.join(disallowed)}"
            
            result = eval(expression, safe_dict, {})
            return f"{expression} = {result}"
            
        except Exception as e:
            return f"Error evaluating '{expression}': {str(e)}"
    
    async def _text_process(self, text: str, operation: str) -> str:
        """Text processing operations."""
        operations = {
            "uppercase": lambda t: t.upper(),
            "lowercase": lambda t: t.lower(),
            "title": lambda t: t.title(),
            "reverse": lambda t: t[::-1],
            "word_count": lambda t: f"Words: {len(t.split())}",
            "char_count": lambda t: f"Characters: {len(t)}",
            "lines": lambda t: f"Lines: {len(t.splitlines())}"
        }
        
        if operation not in operations:
            return f"Unknown operation: {operation}"
        
        return operations[operation](text)
    
    async def _system_info(self, category: str) -> str:
        """Get system information."""
        import platform
        
        if category == "server":
            info = {
                "name": self.server_info["name"],
                "version": self.server_info["version"],
                "protocol": "MCP 2025-03-26",
                "transport": "HTTP/SSE",
                "uptime": server_state.metrics.uptime(),
                "requests": server_state.metrics.total_requests,
                "rps": round(server_state.metrics.rps(), 2)
            }
        elif category == "system":
            info = {
                "platform": platform.system(),
                "release": platform.release(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0]
            }
        elif category == "performance":
            info = {
                "uptime_seconds": server_state.metrics.uptime(),
                "total_requests": server_state.metrics.total_requests,
                "requests_per_second": round(server_state.metrics.rps(), 2),
                "tool_calls": server_state.metrics.tool_calls,
                "resource_reads": server_state.metrics.resource_reads,
                "errors": server_state.metrics.errors,
                "active_sessions": len(server_state.sessions)
            }
        elif category == "tools":
            info = {
                "count": len(self.tools),
                "available": [tool["name"] for tool in self.tools]
            }
        elif category == "capabilities":
            info = self.capabilities
        else:
            info = {"error": f"Unknown category: {category}"}
        
        return json.dumps(info, indent=2)
    
    async def _random_generate(self, type_val: str, arguments: Dict[str, Any]) -> str:
        """Generate random data."""
        import random
        import string
        import uuid
        
        if type_val == "number":
            min_val = arguments.get("min", 1)
            max_val = arguments.get("max", 100)
            result = random.randint(min_val, max_val)
            return f"Random number between {min_val} and {max_val}: {result}"
        elif type_val == "string":
            length = arguments.get("length", 10)
            chars = string.ascii_letters + string.digits
            result = ''.join(random.choice(chars) for _ in range(length))
            return f"Random string ({length} chars): {result}"
        elif type_val == "uuid":
            result = str(uuid.uuid4())
            return f"Random UUID: {result}"
        else:
            return f"Unknown type: {type_val}"
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource and return content."""
        server_state.increment_resource_reads()
        
        try:
            if uri == "server://status":
                status = {
                    "server": self.server_info,
                    "capabilities": self.capabilities,
                    "performance": {
                        "uptime_seconds": server_state.metrics.uptime(),
                        "total_requests": server_state.metrics.total_requests,
                        "requests_per_second": round(server_state.metrics.rps(), 2),
                        "tool_calls": server_state.metrics.tool_calls,
                        "resource_reads": server_state.metrics.resource_reads,
                        "errors": server_state.metrics.errors
                    },
                    "sessions": {
                        "active": len(server_state.sessions),
                        "list": list(server_state.sessions.keys())
                    },
                    "timestamp": time.time()
                }
                return json.dumps(status, indent=2)
            elif uri == "server://docs":
                docs = f"# {self.server_info['name']} API Documentation\n\n"
                docs += f"**Version:** {self.server_info['version']}  \n"
                docs += f"**Protocol:** MCP 2025-03-26  \n\n"
                
                docs += "## Available Tools\n\n"
                for tool in self.tools:
                    docs += f"### {tool['name']}\n\n"
                    docs += f"{tool['description']}\n\n"
                    docs += f"**Input Schema:**\n```json\n{json.dumps(tool['inputSchema'], indent=2)}\n```\n\n"
                
                docs += "## Available Resources\n\n"
                for resource in self.resources:
                    docs += f"### {resource['name']}\n\n"
                    docs += f"**URI:** `{resource['uri']}`  \n"
                    docs += f"**Description:** {resource['description']}  \n"
                    docs += f"**MIME Type:** {resource['mimeType']}  \n\n"
                
                return docs
            elif uri == "server://metrics":
                metrics = {
                    "timestamp": time.time(),
                    "uptime": server_state.metrics.uptime(),
                    "requests": {
                        "total": server_state.metrics.total_requests,
                        "per_second": round(server_state.metrics.rps(), 2)
                    },
                    "operations": {
                        "tool_calls": server_state.metrics.tool_calls,
                        "resource_reads": server_state.metrics.resource_reads,
                        "errors": server_state.metrics.errors
                    },
                    "resources": {
                        "active_sessions": len(server_state.sessions),
                        "tools_available": len(self.tools),
                        "resources_available": len(self.resources)
                    }
                }
                return json.dumps(metrics, indent=2)
            else:
                return f"Resource not found: {uri}"
        except Exception as e:
            logger.error(f"Resource read error for {uri}: {e}")
            return f"Error reading resource {uri}: {str(e)}"
    
    async def handle_mcp_request(self, message_data: Dict[str, Any], session_id: Optional[str] = None) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Handle MCP request with proper Inspector compatibility."""
        server_state.increment_requests()
        
        try:
            method = message_data.get("method")
            params = message_data.get("params", {})
            msg_id = message_data.get("id")
            
            logger.info(f"🔄 {method} (ID: {msg_id}) [Session: {session_id[:8] if session_id else 'None'}...]")
            
            # Route to appropriate handler
            if method == "initialize":
                return await self._handle_initialize(params, msg_id)
            elif method == "notifications/initialized":
                # Notifications don't return responses - this is correct for Inspector
                logger.info("✅ Initialized notification received")
                return None, None
            elif method == "ping":
                return await self._handle_ping(msg_id)
            elif method == "tools/list":
                return await self._handle_tools_list(msg_id)
            elif method == "tools/call":
                return await self._handle_tools_call(params, msg_id)
            elif method == "resources/list":
                return await self._handle_resources_list(msg_id)
            elif method == "resources/read":
                return await self._handle_resources_read(params, msg_id)
            else:
                error_response = self._create_error_response(msg_id, -32601, f"Method not found: {method}")
                return error_response, None
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            server_state.increment_errors()
            error_response = self._create_error_response(msg_id, -32603, f"Internal error: {str(e)}")
            return error_response, None
    
    async def _handle_initialize(self, params: Dict[str, Any], msg_id: Any) -> tuple[Dict[str, Any], str]:
        """Handle initialize request with Inspector compatibility."""
        client_info = params.get("clientInfo", {})
        requested_version = params.get("protocolVersion", "2025-03-26")
        
        # Create session
        session_id = server_state.create_session(client_info, requested_version)
        
        # Create response exactly matching what Inspector expects
        result = {
            "protocolVersion": "2025-03-26",  # Return the version Inspector sent
            "capabilities": self.capabilities,
            "serverInfo": self.server_info
        }
        
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        
        client_name = client_info.get('name', 'unknown')
        logger.info(f"🤝 Initialized session {session_id[:8]}... for {client_name} (v{requested_version})")
        return response, session_id
    
    async def _handle_ping(self, msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle ping request."""
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {}
        }
        return response, None
    
    async def _handle_tools_list(self, msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle tools/list request - Inspector expects this exact format."""
        result = {"tools": self.tools}  # Return the actual tools list
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        logger.info(f"📋 Returning {len(self.tools)} tools to Inspector")
        return response, None
    
    async def _handle_tools_call(self, params: Dict[str, Any], msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not any(tool["name"] == tool_name for tool in self.tools):
            error_response = self._create_error_response(msg_id, -32602, f"Unknown tool: {tool_name}")
            return error_response, None
        
        try:
            result_text = await self.execute_tool(tool_name, arguments)
            
            # Format result for Inspector
            content = [{"type": "text", "text": result_text}]
            response_result = {"content": content}
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": response_result
            }
            logger.info(f"🔧 Executed tool {tool_name}")
            return response, None
            
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            server_state.increment_errors()
            error_response = self._create_error_response(msg_id, -32603, f"Tool execution error: {str(e)}")
            return error_response, None
    
    async def _handle_resources_list(self, msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle resources/list request."""
        result = {"resources": self.resources}
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        return response, None
    
    async def _handle_resources_read(self, params: Dict[str, Any], msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle resources/read request."""
        uri = params.get("uri")
        if not any(resource["uri"] == uri for resource in self.resources):
            error_response = self._create_error_response(msg_id, -32602, f"Unknown resource: {uri}")
            return error_response, None
        
        try:
            content = await self.read_resource(uri)
            
            # Find the resource to get its MIME type
            resource_info = next((r for r in self.resources if r["uri"] == uri), None)
            mime_type = resource_info["mimeType"] if resource_info else "text/plain"
            
            resource_content = {
                "uri": uri,
                "mimeType": mime_type,
                "text": content
            }
            
            result = {"contents": [resource_content]}
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
            return response, None
            
        except Exception as e:
            logger.error(f"Resource read error for {uri}: {e}")
            server_state.increment_errors()
            error_response = self._create_error_response(msg_id, -32603, f"Resource read error: {str(e)}")
            return error_response, None
    
    def _create_error_response(self, msg_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create clean error response."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message}
        }


# Global server instance
mcp_server = EnhancedMCPHTTPServer()


# ============================================================================
# HTTP Transport Endpoints - Inspector Compatible
# ============================================================================

async def mcp_endpoint(request: Request) -> Response:
    """Main MCP endpoint with SSE support for Inspector."""
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return Response("", headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        })
    
    # Handle GET - return server info
    if request.method == "GET":
        return Response(
            orjson.dumps({
                "name": mcp_server.server_info["name"],
                "version": mcp_server.server_info["version"],
                "protocol": "MCP 2025-03-26",
                "status": "ready",
                "tools": len(mcp_server.tools),
                "resources": len(mcp_server.resources)
            }),
            media_type="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    
    # Handle POST
    if request.method == "POST":
        accept_header = request.headers.get("accept", "")
        session_id = request.headers.get("mcp-session-id")
        
        try:
            body = await request.body()
            request_data = orjson.loads(body) if body else {}
            method = request_data.get("method")
            
            # For SSE requests (what Inspector uses)
            if "text/event-stream" in accept_header:
                return await handle_sse_request(request_data, session_id)
            
            # For regular JSON requests
            else:
                # Initialize doesn't need session ID, but others do
                if method != "initialize" and not session_id:
                    return Response(
                        orjson.dumps({
                            "jsonrpc": "2.0",
                            "id": request_data.get("id", "server-error"),
                            "error": {"code": -32600, "message": "Bad Request: Missing session ID"}
                        }),
                        status_code=400,
                        media_type="application/json",
                        headers={"Access-Control-Allow-Origin": "*"}
                    )
                
                # Handle regular JSON request
                response, new_session_id = await mcp_server.handle_mcp_request(request_data, session_id)
                
                if response is None:
                    # For notifications
                    return Response("", status_code=202, headers={"Access-Control-Allow-Origin": "*"})
                
                headers = {"Access-Control-Allow-Origin": "*"}
                if new_session_id:
                    headers["Mcp-Session-Id"] = new_session_id
                
                return Response(
                    orjson.dumps(response),
                    media_type="application/json",
                    headers=headers
                )
                
        except Exception as e:
            logger.error(f"❌ Request processing error: {e}")
            return Response(
                orjson.dumps({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)}
                }),
                status_code=500,
                media_type="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
    
    return Response("Method not allowed", status_code=405)


async def handle_sse_request(request_data: Dict[str, Any], session_id: Optional[str]) -> StreamingResponse:
    """Handle SSE request exactly as Inspector expects."""
    
    created_session_id = None
    method = request_data.get("method")
    
    # Create session ID for initialize requests
    if method == "initialize":
        client_info = request_data.get("params", {}).get("clientInfo", {})
        protocol_version = request_data.get("params", {}).get("protocolVersion", "2025-03-26")
        created_session_id = server_state.create_session(client_info, protocol_version)
        logger.info(f"🔑 Created session ID: {created_session_id}")
    
    async def stream_response():
        try:
            # Use the session ID we created, or the one from headers
            effective_session_id = created_session_id or session_id
            
            # Handle the request
            response, _ = await mcp_server.handle_mcp_request(request_data, effective_session_id)
            
            if response:
                # Send complete SSE event exactly like your working server
                logger.info(f"📤 Sending SSE event for {method}")
                
                # CRITICAL: Must send all 3 parts as separate yields
                yield f"event: message\r\n"
                yield f"data: {orjson.dumps(response).decode()}\r\n"
                yield f"\r\n"
                
                logger.info(f"✅ Complete SSE response sent for {method}")
            
            # For notifications, we don't send anything (which is correct)
            
        except Exception as e:
            logger.error(f"❌ SSE error: {e}")
            import traceback
            traceback.print_exc()
            
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {"code": -32603, "message": str(e)}
            }
            yield f"event: error\r\n"
            yield f"data: {orjson.dumps(error_response).decode()}\r\n"
            yield f"\r\n"
    
    # Set up response headers
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }
    
    # Add session ID to headers if we created one
    if created_session_id:
        headers["Mcp-Session-Id"] = created_session_id
    
    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers=headers
    )


async def health_endpoint(request: Request) -> Response:
    """Health check endpoint."""
    health_data = {
        "status": "healthy",
        "server": mcp_server.server_info["name"],
        "version": mcp_server.server_info["version"],
        "uptime": server_state.metrics.uptime(),
        "tools": len(mcp_server.tools),
        "resources": len(mcp_server.resources),
        "requests": server_state.metrics.total_requests,
        "timestamp": time.time()
    }
    
    return Response(
        orjson.dumps(health_data),
        media_type="application/json",
        headers={"Cache-Control": "no-cache"}
    )


async def root_endpoint(request: Request) -> Response:
    """Root endpoint with server information."""
    base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost')}"
    
    info = {
        "server": mcp_server.server_info,
        "capabilities": mcp_server.capabilities,
        "protocol": "MCP 2025-03-26",
        "inspector_compatible": True,
        "endpoints": {
            "mcp": f"{base_url}/mcp",
            "health": f"{base_url}/health"
        },
        "tools": {
            "count": len(mcp_server.tools),
            "available": [tool["name"] for tool in mcp_server.tools]
        },
        "resources": {
            "count": len(mcp_server.resources),
            "available": [resource["uri"] for resource in mcp_server.resources]
        },
        "performance": {
            "uptime": server_state.metrics.uptime(),
            "requests": server_state.metrics.total_requests,
            "rps": round(server_state.metrics.rps(), 2)
        },
        "quick_start": {
            "health_check": f"curl {base_url}/health",
            "mcp_initialize": f"curl -X POST {base_url}/mcp -H 'Content-Type: application/json' -d '{{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{{\"protocolVersion\":\"2025-03-26\",\"clientInfo\":{{\"name\":\"test\",\"version\":\"1.0\"}}}}}}'",
            "inspector_note": "Use with MCP Inspector via proxy on port 8011"
        },
        "timestamp": time.time()
    }
    
    return Response(
        orjson.dumps(info, option=orjson.OPT_INDENT_2),
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=300"}
    )


# ============================================================================
# Application Factory
# ============================================================================

def create_app(debug: bool = False) -> Starlette:
    """Create Starlette application."""
    
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["Mcp-Session-Id"],
            max_age=3600
        )
    ]
    
    routes = [
        Route("/mcp", mcp_endpoint, methods=["GET", "POST", "OPTIONS"]),
        Route("/health", health_endpoint, methods=["GET"]),
        Route("/", root_endpoint, methods=["GET"]),
    ]
    
    app = Starlette(debug=debug, routes=routes, middleware=middleware)
    
    @app.on_event("startup")
    async def startup():
        logger.info(f"🚀 {mcp_server.server_info['name']} starting...")
        logger.info(f"🔧 {len(mcp_server.tools)} tools available")
        logger.info(f"📂 {len(mcp_server.resources)} resources available")
        logger.info("🔍 MCP Inspector compatibility enabled")
        logger.info("Tools: " + ", ".join([tool["name"] for tool in mcp_server.tools]))
        logger.info("⚡ Ready for MCP requests!")
    
    return app


# ============================================================================
# Main Runner
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced MCP HTTP Server - Inspector Compatible")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    print("🚀 Enhanced MCP HTTP Server - Inspector Compatible")
    print("=" * 60)
    print(f"Server: {mcp_server.server_info['name']}")
    print(f"Version: {mcp_server.server_info['version']}")
    print(f"Protocol: MCP 2025-03-26")
    print()
    print(f"Endpoints:")
    print(f"  Main MCP:         http://{args.host}:{args.port}/mcp")
    print(f"  Health:           http://{args.host}:{args.port}/health")
    print()
    print(f"🔧 Features: {len(mcp_server.tools)} tools, {len(mcp_server.resources)} resources")
    print("Tools: " + ", ".join([tool["name"] for tool in mcp_server.tools]))
    print("Resources: " + ", ".join([resource["uri"] for resource in mcp_server.resources]))
    print()
    print("🔍 MCP Inspector Instructions:")
    print(f"   1. Run your proxy on port 8011 pointing to this server")
    print(f"   2. Set Transport Type: Streamable HTTP")
    print(f"   3. Set URL: http://{args.host}:8011/mcp/inspector")
    print(f"   4. Click Connect")
    print("=" * 60)
    
    app = create_app(debug=args.debug)
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info" if args.debug else "warning",
        access_log=args.debug
    )


if __name__ == "__main__":
    main()