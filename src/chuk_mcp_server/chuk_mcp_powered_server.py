#!/usr/bin/env python3
"""
chuk_mcp Powered HTTP MCP Server - Inspector Compatible

Key fixes for MCP Inspector v0.14.3:
1. Proper Accept header handling for Streamable HTTP
2. Protocol version compatibility (2025-03-26 -> 2025-06-18)
3. Correct SSE event formatting
4. Inspector endpoint behavior matching specification
"""

import asyncio
import json
import time
import uuid
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass

from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.websockets import WebSocket

import orjson
import uvicorn

# chuk_mcp imports for protocol handling
try:
    from chuk_mcp.mcp_client.messages.json_rpc_message import JSONRPCMessage
    from chuk_mcp.mcp_client.messages.initialize.mcp_server_info import MCPServerInfo
    from chuk_mcp.mcp_client.messages.initialize.mcp_server_capabilities import (
        MCPServerCapabilities, ToolsCapability, ResourcesCapability
    )
    from chuk_mcp.mcp_client.messages.tools.tool import Tool
    from chuk_mcp.mcp_client.messages.resources.resource import Resource
    from chuk_mcp.mcp_client.messages.resources.resource_content import ResourceContent
    CHUK_MCP_AVAILABLE = True
    print("✅ chuk_mcp protocol handling loaded successfully")
except ImportError as e:
    print(f"❌ chuk_mcp not available: {e}")
    exit(1)

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
        session_id = str(uuid.uuid4())
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
# chuk_mcp Powered MCP Server Core
# ============================================================================

class ChukMCPHTTPServer:
    """HTTP MCP Server powered by chuk_mcp protocol handling."""
    
    def __init__(self):
        # Server info using chuk_mcp classes
        self.server_info = MCPServerInfo(
            name="chuk-mcp-http-server",
            version="1.0.0",
            title="chuk_mcp Powered HTTP MCP Server"
        )
        
        # Server capabilities using chuk_mcp classes
        self.capabilities = MCPServerCapabilities(
            tools=ToolsCapability(listChanged=True),
            resources=ResourcesCapability(listChanged=True, subscribe=False)
        )
        
        # Tool and resource storage
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.resources: Dict[str, Dict[str, Any]] = {}
        
        # Register built-in capabilities
        self._register_builtin_tools()
        self._register_builtin_resources()
        
        logger.info(f"🚀 {self.server_info.name} initialized with chuk_mcp")
        logger.info(f"📋 Tools: {len(self.tools)}, Resources: {len(self.resources)}")
    
    def _register_builtin_tools(self):
        """Register built-in tools using chuk_mcp Tool class."""
        
        # Calculator tool
        calculator_tool = Tool(
            name="calculate",
            description="Perform mathematical calculations with support for basic operations",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sqrt(16)', 'sin(3.14/2)')"
                    }
                },
                "required": ["expression"]
            }
        )
        
        async def calculate_handler(expression: str) -> str:
            """Safe math expression evaluator with extended functions."""
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
        
        self.tools["calculate"] = {
            "tool": calculator_tool,
            "handler": calculate_handler
        }
        
        # Text processing tool
        text_tool = Tool(
            name="text_process",
            description="Process and transform text with various operations",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to process"},
                    "operation": {
                        "type": "string",
                        "enum": ["uppercase", "lowercase", "title", "reverse", "word_count", "char_count", "lines", "encode_base64", "hash_md5"],
                        "description": "Operation to perform on the text"
                    }
                },
                "required": ["text", "operation"]
            }
        )
        
        async def text_handler(text: str, operation: str) -> str:
            """Advanced text processing operations."""
            import base64
            import hashlib
            
            operations = {
                "uppercase": lambda t: t.upper(),
                "lowercase": lambda t: t.lower(),
                "title": lambda t: t.title(),
                "reverse": lambda t: t[::-1],
                "word_count": lambda t: f"Words: {len(t.split())}",
                "char_count": lambda t: f"Characters: {len(t)}",
                "lines": lambda t: f"Lines: {len(t.splitlines())}",
                "encode_base64": lambda t: base64.b64encode(t.encode()).decode(),
                "hash_md5": lambda t: hashlib.md5(t.encode()).hexdigest()
            }
            
            if operation not in operations:
                return f"Unknown operation: {operation}"
            
            return operations[operation](text)
        
        self.tools["text_process"] = {
            "tool": text_tool,
            "handler": text_handler
        }
        
        # System info tool
        system_tool = Tool(
            name="system_info",
            description="Get detailed server and system information",
            inputSchema={
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
        )
        
        async def system_handler(category: str) -> Dict[str, Any]:
            """Get comprehensive system information."""
            import platform
            
            if category == "server":
                return {
                    "name": self.server_info.name,
                    "version": self.server_info.version,
                    "protocol": "MCP 2025-06-18",
                    "powered_by": "chuk_mcp",
                    "transport": "HTTP multi-transport",
                    "uptime": server_state.metrics.uptime(),
                    "requests": server_state.metrics.total_requests,
                    "rps": round(server_state.metrics.rps(), 2)
                }
            elif category == "system":
                return {
                    "platform": platform.system(),
                    "release": platform.release(),
                    "python_version": platform.python_version(),
                    "architecture": platform.architecture()[0]
                }
            elif category == "performance":
                return {
                    "uptime_seconds": server_state.metrics.uptime(),
                    "total_requests": server_state.metrics.total_requests,
                    "requests_per_second": round(server_state.metrics.rps(), 2),
                    "tool_calls": server_state.metrics.tool_calls,
                    "resource_reads": server_state.metrics.resource_reads,
                    "errors": server_state.metrics.errors,
                    "active_sessions": len(server_state.sessions)
                }
            elif category == "tools":
                return {
                    "count": len(self.tools),
                    "available": list(self.tools.keys()),
                    "details": {name: info["tool"].model_dump() for name, info in self.tools.items()}
                }
            elif category == "capabilities":
                return self.capabilities.model_dump(exclude_none=True)
            else:
                return {"error": f"Unknown category: {category}"}
        
        self.tools["system_info"] = {
            "tool": system_tool,
            "handler": system_handler
        }
        
        # Random generator tool
        random_tool = Tool(
            name="random_generate",
            description="Generate random data (numbers, strings, UUIDs)",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["number", "string", "uuid", "password"],
                        "description": "Type of random data to generate"
                    },
                    "min": {"type": "integer", "description": "Minimum value (for numbers)"},
                    "max": {"type": "integer", "description": "Maximum value (for numbers)"},
                    "length": {"type": "integer", "description": "Length (for strings/passwords)"}
                },
                "required": ["type"]
            }
        )
        
        async def random_handler(type: str, min: int = 1, max: int = 100, length: int = 10) -> str:
            """Generate various types of random data."""
            import random
            import string
            import uuid
            
            if type == "number":
                result = random.randint(min, max)
                return f"Random number between {min} and {max}: {result}"
            elif type == "string":
                chars = string.ascii_letters + string.digits
                result = ''.join(random.choice(chars) for _ in range(length))
                return f"Random string ({length} chars): {result}"
            elif type == "uuid":
                result = str(uuid.uuid4())
                return f"Random UUID: {result}"
            elif type == "password":
                chars = string.ascii_letters + string.digits + "!@#$%^&*"
                result = ''.join(random.choice(chars) for _ in range(length))
                return f"Random password ({length} chars): {result}"
            else:
                return f"Unknown type: {type}"
        
        self.tools["random_generate"] = {
            "tool": random_tool,
            "handler": random_handler
        }
        
        logger.info(f"🔧 Registered {len(self.tools)} tools with chuk_mcp")
    
    def _register_builtin_resources(self):
        """Register built-in resources using chuk_mcp Resource class."""
        
        # Live server status
        status_resource = Resource(
            uri="server://status",
            name="Live Server Status",
            description="Real-time server status and performance metrics",
            mimeType="application/json"
        )
        
        async def status_handler() -> str:
            """Get comprehensive server status."""
            status = {
                "server": self.server_info.model_dump(),
                "capabilities": self.capabilities.model_dump(exclude_none=True),
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
                "timestamp": time.time(),
                "powered_by": "chuk_mcp"
            }
            return json.dumps(status, indent=2)
        
        self.resources["server://status"] = {
            "resource": status_resource,
            "handler": status_handler
        }
        
        # API documentation
        docs_resource = Resource(
            uri="server://docs",
            name="API Documentation",
            description="Complete API documentation with examples",
            mimeType="text/markdown"
        )
        
        async def docs_handler() -> str:
            """Generate comprehensive API documentation."""
            docs = f"# {self.server_info.name} API Documentation\n\n"
            docs += f"**Version:** {self.server_info.version}  \n"
            docs += f"**Protocol:** MCP 2025-06-18  \n"
            docs += f"**Powered by:** chuk_mcp  \n\n"
            
            docs += "## Available Tools\n\n"
            for tool_name, tool_info in self.tools.items():
                tool = tool_info["tool"]
                docs += f"### {tool.name}\n\n"
                docs += f"{tool.description}\n\n"
                docs += f"**Input Schema:**\n```json\n{json.dumps(tool.inputSchema, indent=2)}\n```\n\n"
            
            docs += "## Available Resources\n\n"
            for uri, resource_info in self.resources.items():
                resource = resource_info["resource"]
                docs += f"### {resource.name}\n\n"
                docs += f"**URI:** `{resource.uri}`  \n"
                docs += f"**Description:** {resource.description}  \n"
                docs += f"**MIME Type:** {resource.mimeType}  \n\n"
            
            docs += "## Transport Endpoints\n\n"
            docs += "- **HTTP JSON-RPC:** `POST /mcp`\n"
            docs += "- **Streamable HTTP:** `GET /mcp/stream`\n"
            docs += "- **MCP Inspector:** `/mcp/inspector`\n\n"
            
            docs += "## Quick Start\n\n"
            docs += "```bash\n"
            docs += "# Test the server\n"
            docs += "curl http://localhost:8000/health\n\n"
            docs += "# Initialize MCP connection\n"
            docs += 'curl -X POST http://localhost:8000/mcp \\\n'
            docs += '  -H "Content-Type: application/json" \\\n'
            docs += '  -d \'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","clientInfo":{"name":"test","version":"1.0"}}}\'\n'
            docs += "```\n\n"
            
            return docs
        
        self.resources["server://docs"] = {
            "resource": docs_resource,
            "handler": docs_handler
        }
        
        # Live metrics stream
        metrics_resource = Resource(
            uri="server://metrics/live",
            name="Live Metrics Stream",
            description="Real-time streaming server metrics",
            mimeType="application/json"
        )
        
        async def metrics_handler() -> str:
            """Get current metrics snapshot."""
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
        
        self.resources["server://metrics/live"] = {
            "resource": metrics_resource,
            "handler": metrics_handler
        }
        
        # Tool examples resource
        examples_resource = Resource(
            uri="server://examples",
            name="Tool Usage Examples",
            description="Example requests for all available tools",
            mimeType="application/json"
        )
        
        async def examples_handler() -> str:
            """Generate tool usage examples."""
            examples = {
                "description": "Example tool calls for this MCP server",
                "base_url": "http://localhost:8000/mcp",
                "examples": []
            }
            
            tool_examples = {
                "calculate": {
                    "description": "Calculate mathematical expressions",
                    "examples": [
                        {"expression": "2 + 3 * 4"},
                        {"expression": "sqrt(16)"},
                        {"expression": "sin(pi/2)"},
                        {"expression": "log(100)"}
                    ]
                },
                "text_process": {
                    "description": "Process and transform text",
                    "examples": [
                        {"text": "Hello World", "operation": "uppercase"},
                        {"text": "PYTHON PROGRAMMING", "operation": "lowercase"},
                        {"text": "test message", "operation": "word_count"},
                        {"text": "encode this", "operation": "encode_base64"}
                    ]
                },
                "system_info": {
                    "description": "Get system information",
                    "examples": [
                        {"category": "server"},
                        {"category": "system"},
                        {"category": "performance"},
                        {"category": "tools"}
                    ]
                },
                "random_generate": {
                    "description": "Generate random data",
                    "examples": [
                        {"type": "number", "min": 1, "max": 100},
                        {"type": "string", "length": 8},
                        {"type": "uuid"},
                        {"type": "password", "length": 12}
                    ]
                }
            }
            
            for tool_name, tool_data in tool_examples.items():
                for example_args in tool_data["examples"]:
                    examples["examples"].append({
                        "tool": tool_name,
                        "description": tool_data["description"],
                        "request": {
                            "jsonrpc": "2.0",
                            "id": len(examples["examples"]) + 1,
                            "method": "tools/call",
                            "params": {
                                "name": tool_name,
                                "arguments": example_args
                            }
                        }
                    })
            
            return json.dumps(examples, indent=2)
        
        self.resources["server://examples"] = {
            "resource": examples_resource,
            "handler": examples_handler
        }
        
        logger.info(f"📂 Registered {len(self.resources)} resources with chuk_mcp")
    
    def _normalize_protocol_version(self, requested_version: str) -> str:
        """Normalize protocol version for Inspector compatibility."""
        # Inspector uses 2025-03-26, but we support 2025-06-18
        version_map = {
            "2025-03-26": "2025-06-18",  # Inspector version
            "2024-11-05": "2025-06-18",
            "2024-10-07": "2025-06-18"
        }
        return version_map.get(requested_version, requested_version)
    
    async def handle_mcp_request(self, message_data: Dict[str, Any], session_id: Optional[str] = None) -> tuple[Dict[str, Any], Optional[str]]:
        """Handle MCP request using chuk_mcp protocol classes."""
        server_state.increment_requests()
        
        try:
            method = message_data.get("method")
            params = message_data.get("params", {})
            msg_id = message_data.get("id")
            
            logger.debug(f"Handling: {method} (ID: {msg_id})")
            
            # Route to appropriate handler
            if method == "initialize":
                return await self._handle_initialize(params, msg_id)
            elif method == "notifications/initialized":
                return {}, None
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
        """Handle initialize request with version compatibility."""
        client_info = params.get("clientInfo", {})
        requested_version = params.get("protocolVersion", "2025-06-18")
        
        # Normalize version for compatibility
        protocol_version = self._normalize_protocol_version(requested_version)
        
        # Create session
        session_id = server_state.create_session(client_info, protocol_version)
        
        # Create response manually to ensure clean JSON-RPC format
        result = {
            "protocolVersion": protocol_version,
            "serverInfo": self.server_info.model_dump(),
            "capabilities": self.capabilities.model_dump(exclude_none=True),
            "instructions": f"Welcome to {self.server_info.name}! Powered by chuk_mcp for robust MCP protocol handling."
        }
        
        # Create clean JSON-RPC response without extra fields
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        
        client_name = client_info.get('name', 'unknown')
        logger.info(f"🤝 Initialized session {session_id[:8]}... for {client_name} (v{requested_version}→{protocol_version})")
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
        """Handle tools/list request."""
        tools_list = [tool_info["tool"].model_dump() for tool_info in self.tools.values()]
        result = {"tools": tools_list}
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        return response, None
    
    async def _handle_tools_call(self, params: Dict[str, Any], msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle tools/call request."""
        server_state.increment_tool_calls()
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            error_response = self._create_error_response(msg_id, -32602, f"Unknown tool: {tool_name}")
            return error_response, None
        
        try:
            tool_info = self.tools[tool_name]
            handler = tool_info["handler"]
            
            # Execute tool
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)
            
            # Format result using chuk_mcp patterns
            if isinstance(result, str):
                content = [{"type": "text", "text": result}]
            elif isinstance(result, dict):
                content = [{"type": "text", "text": json.dumps(result, indent=2)}]
            else:
                content = [{"type": "text", "text": str(result)}]
            
            response_result = {"content": content}
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": response_result
            }
            return response, None
            
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            server_state.increment_errors()
            error_response = self._create_error_response(msg_id, -32603, f"Tool execution error: {str(e)}")
            return error_response, None
    
    async def _handle_resources_list(self, msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle resources/list request."""
        resources_list = [resource_info["resource"].model_dump() for resource_info in self.resources.values()]
        result = {"resources": resources_list}
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        return response, None
    
    async def _handle_resources_read(self, params: Dict[str, Any], msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle resources/read request."""
        server_state.increment_resource_reads()
        
        uri = params.get("uri")
        if uri not in self.resources:
            error_response = self._create_error_response(msg_id, -32602, f"Unknown resource: {uri}")
            return error_response, None
        
        try:
            resource_info = self.resources[uri]
            handler = resource_info["handler"]
            
            # Execute resource handler
            if asyncio.iscoroutinefunction(handler):
                content = await handler()
            else:
                content = handler()
            
            # Create ResourceContent using chuk_mcp
            resource_content = ResourceContent(
                uri=uri,
                mimeType=resource_info["resource"].mimeType,
                text=content
            )
            
            result = {"contents": [resource_content.model_dump()]}
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
chuk_mcp_server = ChukMCPHTTPServer()


# ============================================================================
# Fixed HTTP Transport Endpoints for Inspector
# ============================================================================

def _wants_sse_response(request: Request) -> bool:
    """Check if client wants SSE response based on Accept header."""
    accept_header = request.headers.get("accept", "")
    return "text/event-stream" in accept_header

async def http_mcp_endpoint(request: Request) -> Response:
    """Standard HTTP JSON-RPC MCP endpoint."""
    server_state.increment_requests()
    
    try:
        body = await request.body()
        if not body:
            return _create_http_error_response(None, -32700, "Parse error: Empty body")
        
        try:
            message = orjson.loads(body)
        except orjson.JSONDecodeError as e:
            return _create_http_error_response(None, -32700, f"Parse error: {str(e)}")
        
        # Validate JSON-RPC structure
        if message.get("jsonrpc") != "2.0":
            return _create_http_error_response(message.get("id"), -32600, "Must be JSON-RPC 2.0")
        
        # Get session ID from headers
        session_id = request.headers.get("Mcp-Session-Id")
        
        # Handle notifications
        if "id" not in message:
            method = message.get("method")
            if method == "notifications/initialized":
                return Response("", status_code=204)
            return Response("", status_code=204)
        
        # Process request
        response_data, new_session_id = await chuk_mcp_server.handle_mcp_request(message, session_id)
        
        # Create HTTP response
        body = orjson.dumps(response_data)
        response = Response(
            body,
            media_type="application/json",
            headers={
                "Cache-Control": "no-cache",
                "MCP-Protocol-Version": "2025-06-18",
                "X-Powered-By": "chuk_mcp"
            }
        )
        
        if new_session_id:
            response.headers["Mcp-Session-Id"] = new_session_id
        
        return response
        
    except Exception as e:
        logger.error(f"HTTP endpoint error: {e}")
        server_state.increment_errors()
        return _create_http_error_response(None, -32603, f"Server error: {str(e)}")


async def streamable_http_endpoint(request: Request) -> StreamingResponse:
    """Streamable HTTP endpoint for MCP Inspector compatibility."""
    
    async def stream_handler():
        try:
            # Send connection event
            connection_event = {
                "type": "connection",
                "status": "established", 
                "protocol": "streamable-http",
                "version": "2025-06-18",
                "server": chuk_mcp_server.server_info.name,
                "powered_by": "chuk_mcp",
                "timestamp": time.time()
            }
            yield f"data: {orjson.dumps(connection_event).decode()}\n\n"
            
            # Send server info
            server_info_event = {
                "type": "server_info",
                "server": chuk_mcp_server.server_info.model_dump(),
                "capabilities": chuk_mcp_server.capabilities.model_dump(exclude_none=True),
                "tools_count": len(chuk_mcp_server.tools),
                "resources_count": len(chuk_mcp_server.resources),
                "timestamp": time.time()
            }
            yield f"data: {orjson.dumps(server_info_event).decode()}\n\n"
            
            # Handle initial message if present
            body = await request.body()
            if body:
                try:
                    initial_message = orjson.loads(body)
                    response_data, session_id = await chuk_mcp_server.handle_mcp_request(initial_message)
                    
                    response_event = {
                        "type": "response",
                        "id": initial_message.get("id"),
                        "data": response_data,
                        "timestamp": time.time()
                    }
                    yield f"data: {orjson.dumps(response_event).decode()}\n\n"
                    
                except Exception as e:
                    error_event = {
                        "type": "error",
                        "error": {"code": -32603, "message": str(e)},
                        "timestamp": time.time()
                    }
                    yield f"data: {orjson.dumps(error_event).decode()}\n\n"
            
            # Heartbeat loop
            counter = 0
            while True:
                await asyncio.sleep(5)
                counter += 1
                
                heartbeat = {
                    "type": "heartbeat", 
                    "counter": counter,
                    "timestamp": time.time(),
                    "server_status": {
                        "uptime": server_state.metrics.uptime(),
                        "requests": server_state.metrics.total_requests,
                        "rps": round(server_state.metrics.rps(), 2)
                    }
                }
                yield f"data: {orjson.dumps(heartbeat).decode()}\n\n"
                
        except asyncio.CancelledError:
            disconnect_event = {
                "type": "disconnect",
                "reason": "client_disconnect",
                "timestamp": time.time()
            }
            yield f"data: {orjson.dumps(disconnect_event).decode()}\n\n"
    
    return StreamingResponse(
        stream_handler(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, MCP-Protocol-Version",
            "MCP-Protocol-Version": "2025-06-18",
            "X-Powered-By": "chuk_mcp",
            "X-Inspector-Compatible": "true"
        }
    )


async def inspector_endpoint(request: Request) -> Response:
    """Fixed MCP Inspector endpoint with proper Accept header handling."""
    
    # Handle OPTIONS for CORS preflight
    if request.method == "OPTIONS":
        return Response("", headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, MCP-Protocol-Version",
            "Access-Control-Max-Age": "3600"
        })
    
    # Handle GET - Inspector discovery
    if request.method == "GET":
        inspector_info = {
            "server": chuk_mcp_server.server_info.model_dump(),
            "capabilities": chuk_mcp_server.capabilities.model_dump(exclude_none=True),
            "tools": {
                "count": len(chuk_mcp_server.tools),
                "available": list(chuk_mcp_server.tools.keys())
            },
            "resources": {
                "count": len(chuk_mcp_server.resources),
                "available": list(chuk_mcp_server.resources.keys())
            },
            "powered_by": "chuk_mcp",
            "inspector_compatible": True,
            "timestamp": time.time()
        }
        
        return Response(
            orjson.dumps(inspector_info, option=orjson.OPT_INDENT_2),
            media_type="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",
                "MCP-Protocol-Version": "2025-06-18",
                "X-Inspector-Compatible": "true"
            }
        )
    
    # Handle POST - Inspector requests (JSON or SSE based on Accept header)
    elif request.method == "POST":
        try:
            # Log the request for debugging
            logger.info(f"🔍 Inspector POST: Accept={request.headers.get('accept', 'none')}")
            
            # Read the body ONCE here, before deciding on response type
            try:
                body_bytes = await request.body()
                logger.info(f"📦 Read body: {len(body_bytes) if body_bytes else 0} bytes")
            except Exception as e:
                logger.error(f"Failed to read request body: {e}")
                return _create_http_error_response(None, -32700, "Failed to read request body")
            
            # Check if client wants SSE response
            if _wants_sse_response(request):
                logger.info("📡 Returning SSE response for Inspector")
                return await _create_inspector_sse_response(request, body_bytes)
            else:
                logger.info("📄 Returning JSON response for Inspector")
                return await _create_inspector_json_response(request, body_bytes)
                
        except Exception as e:
            logger.error(f"Inspector endpoint error: {e}", exc_info=True)
            return _create_http_error_response(None, -32603, f"Inspector endpoint error: {str(e)}")


async def _create_inspector_json_response(request: Request, body_bytes: bytes) -> Response:
    """Create standard JSON response for Inspector."""
    try:
        if not body_bytes:
            return _create_http_error_response(None, -32700, "Empty request body")
        
        message = orjson.loads(body_bytes)
        session_id = request.headers.get("Mcp-Session-Id")
        
        # Process the request
        response_data, new_session_id = await chuk_mcp_server.handle_mcp_request(message, session_id)
        
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
            "MCP-Protocol-Version": "2025-06-18"
        }
        
        if new_session_id:
            headers["Mcp-Session-Id"] = new_session_id
        
        return Response(
            orjson.dumps(response_data),
            media_type="application/json",
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Inspector JSON response error: {e}")
        return _create_http_error_response(None, -32603, f"Server error: {str(e)}")


async def _create_inspector_sse_response(request: Request, body_bytes: bytes) -> StreamingResponse:
    """Create SSE response for Inspector according to Streamable HTTP spec."""
    
    async def sse_generator():
        try:
            logger.info("🌊 Starting SSE stream for Inspector")
            
            session_id = request.headers.get("Mcp-Session-Id")
            logger.info(f"📦 Processing {len(body_bytes) if body_bytes else 0} bytes of body data")
            
            if body_bytes:
                try:
                    initial_message = orjson.loads(body_bytes)
                    logger.info(f"📨 Processing initial message: {initial_message.get('method', 'unknown')} (ID: {initial_message.get('id')})")
                    
                    # Handle the initial request
                    response_data, new_session_id = await chuk_mcp_server.handle_mcp_request(initial_message, session_id)
                    
                    logger.info(f"✅ Generated response for {initial_message.get('method')}")
                    logger.info(f"📤 Response data: {response_data}")
                    
                    # Send ONLY the JSON-RPC response, no wrapping
                    # According to MCP spec, Streamable HTTP should send raw JSON-RPC messages
                    yield f"data: {orjson.dumps(response_data).decode()}\n\n"
                    
                    # Use the new session ID if created
                    if new_session_id:
                        session_id = new_session_id
                    
                except orjson.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                    }
                    yield f"data: {orjson.dumps(error_response).decode()}\n\n"
                    return
                    
                except Exception as e:
                    logger.error(f"Error processing initial message: {e}", exc_info=True)
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": initial_message.get('id') if 'initial_message' in locals() else None,
                        "error": {"code": -32603, "message": str(e)}
                    }
                    yield f"data: {orjson.dumps(error_response).decode()}\n\n"
                    return
            
            # Keep the stream alive with periodic heartbeats
            # Use a simple comment-based heartbeat to avoid confusing the Inspector
            logger.info("💓 Starting heartbeat to keep Inspector connected")
            counter = 0
            while True:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                counter += 1
                
                try:
                    # Send a comment-based heartbeat instead of data event
                    yield f": heartbeat {counter} at {time.time()}\n\n"
                    logger.debug(f"💓 Sent heartbeat #{counter}")
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}")
                    break
                
        except asyncio.CancelledError:
            logger.info("🔌 Inspector SSE stream cancelled by client")
        except Exception as e:
            logger.error(f"SSE generator error: {e}", exc_info=True)
            try:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)}
                }
                yield f"data: {orjson.dumps(error_response).decode()}\n\n"
            except:
                logger.error("Failed to send error event in SSE stream")
        finally:
            logger.info("🏁 Inspector SSE stream ending")
    
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, Accept, Mcp-Session-Id",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "MCP-Protocol-Version": "2025-06-18",
            "X-Inspector-Compatible": "true"
        }
    )


async def health_endpoint(request: Request) -> Response:
    """Fast health check endpoint."""
    health_data = {
        "status": "healthy",
        "uptime": server_state.metrics.uptime(),
        "powered_by": "chuk_mcp",
        "timestamp": time.time()
    }
    
    return Response(
        orjson.dumps(health_data),
        media_type="application/json",
        headers={"Cache-Control": "no-cache"}
    )


async def metrics_endpoint(request: Request) -> Response:
    """Performance metrics endpoint."""
    metrics_data = {
        "server": chuk_mcp_server.server_info.model_dump(),
        "performance": {
            "uptime_seconds": server_state.metrics.uptime(),
            "total_requests": server_state.metrics.total_requests,
            "requests_per_second": round(server_state.metrics.rps(), 2),
            "tool_calls": server_state.metrics.tool_calls,
            "resource_reads": server_state.metrics.resource_reads,
            "errors": server_state.metrics.errors
        },
        "capabilities": {
            "tools_count": len(chuk_mcp_server.tools),
            "resources_count": len(chuk_mcp_server.resources),
            "active_sessions": len(server_state.sessions)
        },
        "powered_by": "chuk_mcp",
        "timestamp": time.time()
    }
    
    return Response(
        orjson.dumps(metrics_data),
        media_type="application/json",
        headers={"Cache-Control": "no-cache"}
    )


async def root_endpoint(request: Request) -> Response:
    """Root endpoint with server information."""
    base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost')}"
    
    info = {
        "server": chuk_mcp_server.server_info.model_dump(),
        "capabilities": chuk_mcp_server.capabilities.model_dump(exclude_none=True),
        "powered_by": "chuk_mcp",
        "protocol": "MCP 2025-06-18",
        "inspector_compatible": True,
        "endpoints": {
            "mcp": f"{base_url}/mcp",
            "streamable": f"{base_url}/mcp/stream", 
            "inspector": f"{base_url}/mcp/inspector",
            "health": f"{base_url}/health",
            "metrics": f"{base_url}/metrics"
        },
        "performance": {
            "uptime": server_state.metrics.uptime(),
            "requests": server_state.metrics.total_requests,
            "rps": round(server_state.metrics.rps(), 2)
        },
        "quick_start": {
            "health_check": f"curl {base_url}/health",
            "mcp_initialize": f"curl -X POST {base_url}/mcp -H 'Content-Type: application/json' -d '{{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{{\"protocolVersion\":\"2025-06-18\",\"clientInfo\":{{\"name\":\"test\",\"version\":\"1.0\"}}}}}}'",
            "inspector_url": f"{base_url}/mcp/inspector"
        },
        "timestamp": time.time()
    }
    
    return Response(
        orjson.dumps(info, option=orjson.OPT_INDENT_2),
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=300"}
    )


def _create_http_error_response(msg_id: Any, code: int, message: str) -> Response:
    """Create HTTP error response."""
    error_response = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": code, "message": message}
    }
    
    status_code = 400 if code in [-32700, -32600] else 200
    
    return Response(
        orjson.dumps(error_response),
        status_code=status_code,
        media_type="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
            "MCP-Protocol-Version": "2025-06-18"
        }
    )


# ============================================================================
# Application Factory
# ============================================================================

def create_app(debug: bool = False) -> Starlette:
    """Create Starlette application with chuk_mcp powered endpoints."""
    
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["Mcp-Session-Id", "MCP-Protocol-Version"],
            max_age=3600
        ),
        Middleware(GZipMiddleware, minimum_size=1000)
    ]
    
    routes = [
        # Core MCP endpoints
        Route("/mcp", http_mcp_endpoint, methods=["POST"]),
        Route("/mcp/stream", streamable_http_endpoint, methods=["GET", "POST"]),
        Route("/mcp/inspector", inspector_endpoint, methods=["GET", "POST", "OPTIONS"]),
        
        # Health and monitoring
        Route("/health", health_endpoint, methods=["GET"]),
        Route("/metrics", metrics_endpoint, methods=["GET"]),
        
        # Information
        Route("/", root_endpoint, methods=["GET"]),
    ]
    
    app = Starlette(debug=debug, routes=routes, middleware=middleware)
    
    @app.on_event("startup")
    async def startup():
        logger.info(f"🚀 {chuk_mcp_server.server_info.name} starting...")
        logger.info("📡 Powered by chuk_mcp for robust MCP protocol handling")
        logger.info(f"🔧 {len(chuk_mcp_server.tools)} tools available")
        logger.info(f"📂 {len(chuk_mcp_server.resources)} resources available")
        logger.info("🔍 MCP Inspector compatibility enabled")
        logger.info("⚡ Ready for high-performance MCP requests!")
    
    @app.on_event("shutdown")
    async def shutdown():
        uptime = server_state.metrics.uptime()
        logger.info(f"📊 Shutdown stats: {server_state.metrics.total_requests} requests in {uptime:.1f}s")
        logger.info("👋 chuk_mcp powered server shutting down")
    
    return app


# ============================================================================
# Main Runner
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="chuk_mcp Powered HTTP MCP Server - Inspector Compatible")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8011, help="Port to bind to") 
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    print("🚀 chuk_mcp Powered HTTP MCP Server - Inspector Compatible")
    print("=" * 60)
    print(f"Server: {chuk_mcp_server.server_info.name}")
    print(f"Version: {chuk_mcp_server.server_info.version}")
    print(f"Protocol: MCP 2025-06-18 (compatible with 2025-03-26)")
    print(f"Powered by: chuk_mcp")
    print()
    print(f"Endpoints:")
    print(f"  HTTP MCP:         http://{args.host}:{args.port}/mcp")
    print(f"  Streamable HTTP:  http://{args.host}:{args.port}/mcp/stream")
    print(f"  🔍 MCP Inspector: http://{args.host}:{args.port}/mcp/inspector") 
    print(f"  Health:           http://{args.host}:{args.port}/health")
    print(f"  Metrics:          http://{args.host}:{args.port}/metrics")
    print()
    print(f"🔧 Features: {len(chuk_mcp_server.tools)} tools, {len(chuk_mcp_server.resources)} resources")
    print("Tools: calculate, text_process, system_info, random_generate")
    print("Resources: server://status, server://docs, server://metrics/live, server://examples")
    print()
    print("🔍 MCP Inspector Instructions:")
    print(f"   1. Set Transport Type: Streamable HTTP")
    print(f"   2. Set URL: http://{args.host}:{args.port}/mcp/inspector")
    print(f"   3. Click Connect")
    print("=" * 60)
    
    app = create_app(debug=args.debug)
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers if not args.debug else 1,
        log_level="info" if args.debug else "warning",
        access_log=args.debug
    )


if __name__ == "__main__":
    main()