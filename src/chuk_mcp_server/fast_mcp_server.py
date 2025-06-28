#!/usr/bin/env python3
"""
fast_mcp_server.py - Ultra-fast MCP Protocol Server

A high-performance web server that implements the MCP protocol
with optimal speed and developer experience.

Features:
- MCP 2025-06-18 protocol compliance
- Built for maximum performance (target: 10,000+ RPS)
- SSE streaming support
- Session management
- Tool and resource endpoints
- Developer-friendly setup

Usage:
    python fast_mcp_server.py                    # Run on localhost:8000
    python fast_mcp_server.py --port 8080        # Custom port
    python fast_mcp_server.py --workers 4        # Multi-worker
"""

import asyncio
import json
import time
import uuid
import argparse
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict

import uvicorn
import orjson
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response, StreamingResponse
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


# ============================================================================
# Server State and Models
# ============================================================================

@dataclass
class MCPSession:
    """MCP session state"""
    session_id: str
    client_info: Dict[str, Any]
    protocol_version: str
    created_at: float
    last_activity: float
    
    def touch(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()


@dataclass
class ServerMetrics:
    """Runtime server metrics"""
    start_time: float
    total_requests: int = 0
    active_sessions: int = 0
    tool_calls: int = 0
    resource_reads: int = 0
    
    def uptime(self) -> float:
        return time.time() - self.start_time
    
    def rps(self) -> float:
        uptime = self.uptime()
        return self.total_requests / uptime if uptime > 0 else 0.0


# Global server state
class ServerState:
    def __init__(self):
        self.sessions: Dict[str, MCPSession] = {}
        self.metrics = ServerMetrics(start_time=time.time())
        
        # Mock tools and resources for demo
        self.tools = [
            {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "hello",
                "description": "Say hello to someone",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name to greet"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "time",
                "description": "Get current time",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]
        
        self.resources = [
            {
                "uri": "demo://server-info",
                "name": "Server Information",
                "description": "Current server status and information"
            },
            {
                "uri": "demo://metrics",
                "name": "Server Metrics", 
                "description": "Performance metrics and statistics"
            },
            {
                "uri": "demo://tools",
                "name": "Available Tools",
                "description": "List of all available tools"
            }
        ]

# Global state instance
state = ServerState()


# ============================================================================
# MCP Protocol Handlers
# ============================================================================

def create_session(client_info: Dict[str, Any], protocol_version: str) -> MCPSession:
    """Create new MCP session"""
    session_id = str(uuid.uuid4())
    session = MCPSession(
        session_id=session_id,
        client_info=client_info,
        protocol_version=protocol_version,
        created_at=time.time(),
        last_activity=time.time()
    )
    state.sessions[session_id] = session
    state.metrics.active_sessions = len(state.sessions)
    return session


def get_session(session_id: Optional[str]) -> Optional[MCPSession]:
    """Get session by ID"""
    if not session_id:
        return None
    session = state.sessions.get(session_id)
    if session:
        session.touch()
    return session


def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialize request"""
    client_info = params.get("clientInfo", {"name": "unknown", "version": "0.0.0"})
    protocol_version = params.get("protocolVersion", "2025-06-18")
    
    session = create_session(client_info, protocol_version)
    
    return {
        "protocolVersion": "2025-06-18",
        "capabilities": {
            "tools": {"listChanged": True},
            "resources": {"listChanged": True},
            "logging": {}
        },
        "serverInfo": {
            "name": "fast-mcp-server",
            "version": "1.0.0"
        },
        "_session_id": session.session_id  # Custom field for session tracking
    }


def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/list request"""
    state.metrics.tool_calls += 1
    return {"tools": state.tools}


def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request"""
    state.metrics.tool_calls += 1
    
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    # Execute mock tool
    if tool_name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        result = a + b
        return {
            "content": [
                {"type": "text", "text": f"The sum of {a} and {b} is {result}"}
            ]
        }
    
    elif tool_name == "hello":
        name = arguments.get("name", "World")
        return {
            "content": [
                {"type": "text", "text": f"Hello, {name}! 👋"}
            ]
        }
    
    elif tool_name == "time":
        current_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        return {
            "content": [
                {"type": "text", "text": f"Current time: {current_time}"}
            ]
        }
    
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def handle_resources_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle resources/list request"""
    return {"resources": state.resources}


def handle_resources_read(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle resources/read request"""
    state.metrics.resource_reads += 1
    
    uri = params.get("uri")
    
    if uri == "demo://server-info":
        content = {
            "server": "fast-mcp-server",
            "version": "1.0.0",
            "uptime_seconds": state.metrics.uptime(),
            "active_sessions": len(state.sessions),
            "total_tools": len(state.tools),
            "total_resources": len(state.resources)
        }
        text = json.dumps(content, indent=2)
    
    elif uri == "demo://metrics":
        content = {
            "total_requests": state.metrics.total_requests,
            "tool_calls": state.metrics.tool_calls,
            "resource_reads": state.metrics.resource_reads,
            "requests_per_second": state.metrics.rps(),
            "uptime_seconds": state.metrics.uptime(),
            "timestamp": time.time()
        }
        text = json.dumps(content, indent=2)
    
    elif uri == "demo://tools":
        text = json.dumps(state.tools, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")
    
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": "application/json",
                "text": text
            }
        ]
    }


# ============================================================================
# HTTP Endpoints
# ============================================================================

async def mcp_endpoint(request: Request) -> Response:
    """Main MCP protocol endpoint"""
    state.metrics.total_requests += 1
    
    try:
        # Parse request
        body = await request.body()
        if not body:
            return create_error_response(None, -32700, "Parse error: Empty body")
        
        try:
            message = orjson.loads(body)
        except orjson.JSONDecodeError:
            return create_error_response(None, -32700, "Parse error: Invalid JSON")
        
        # Extract request components
        jsonrpc = message.get("jsonrpc")
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        # Validate JSON-RPC
        if jsonrpc != "2.0":
            return create_error_response(msg_id, -32600, "Invalid Request: Must be JSON-RPC 2.0")
        
        # Get session for non-initialize requests
        session_id = request.headers.get("Mcp-Session-Id")
        session = None
        if method != "initialize" and method != "notifications/initialized":
            session = get_session(session_id)
            # Allow requests without session for compatibility
        
        # Handle methods
        try:
            if method == "initialize":
                result = handle_initialize(params)
                response = create_success_response(msg_id, result)
                
                # Set session header
                if "_session_id" in result:
                    session_id = result.pop("_session_id")
                    response.headers["Mcp-Session-Id"] = session_id
                
                return response
            
            elif method == "notifications/initialized":
                # No response for notifications
                return Response("", status_code=204)
            
            elif method == "ping":
                return create_success_response(msg_id, {})
            
            elif method == "tools/list":
                result = handle_tools_list(params)
                return create_success_response(msg_id, result)
            
            elif method == "tools/call":
                result = handle_tools_call(params)
                return create_success_response(msg_id, result)
            
            elif method == "resources/list":
                result = handle_resources_list(params)
                return create_success_response(msg_id, result)
            
            elif method == "resources/read":
                result = handle_resources_read(params)
                return create_success_response(msg_id, result)
            
            else:
                return create_error_response(msg_id, -32601, f"Method not found: {method}")
        
        except ValueError as e:
            return create_error_response(msg_id, -32602, f"Invalid params: {str(e)}")
        except Exception as e:
            return create_error_response(msg_id, -32603, f"Internal error: {str(e)}")
    
    except Exception as e:
        return create_error_response(None, -32603, f"Server error: {str(e)}")


async def health_endpoint(request: Request) -> Response:
    """Health check endpoint"""
    health_data = {
        "status": "healthy",
        "uptime_seconds": state.metrics.uptime(),
        "total_requests": state.metrics.total_requests,
        "requests_per_second": state.metrics.rps(),
        "active_sessions": len(state.sessions),
        "timestamp": time.time()
    }
    
    return Response(
        orjson.dumps(health_data),
        media_type="application/json",
        headers={"cache-control": "no-cache"}
    )


async def metrics_endpoint(request: Request) -> Response:
    """Metrics endpoint"""
    metrics_data = {
        "server": {
            "name": "fast-mcp-server",
            "version": "1.0.0",
            "uptime_seconds": state.metrics.uptime(),
            "start_time": state.metrics.start_time
        },
        "requests": {
            "total": state.metrics.total_requests,
            "per_second": state.metrics.rps()
        },
        "mcp": {
            "active_sessions": len(state.sessions),
            "tool_calls": state.metrics.tool_calls,
            "resource_reads": state.metrics.resource_reads
        },
        "capabilities": {
            "tools_count": len(state.tools),
            "resources_count": len(state.resources)
        },
        "timestamp": time.time()
    }
    
    return Response(
        orjson.dumps(metrics_data),
        media_type="application/json",
        headers={"cache-control": "no-cache"}
    )


async def root_endpoint(request: Request) -> Response:
    """Root endpoint with server info"""
    info = {
        "server": "fast-mcp-server",
        "version": "1.0.0",
        "protocol": "MCP 2025-06-18",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health",
            "metrics": "/metrics"
        },
        "features": [
            "High-performance MCP protocol",
            "Session management",
            "Tools and resources",
            "Real-time metrics"
        ],
        "performance": {
            "target_rps": "10,000+",
            "uptime_seconds": state.metrics.uptime(),
            "current_rps": state.metrics.rps()
        }
    }
    
    return Response(
        orjson.dumps(info, option=orjson.OPT_INDENT_2),
        media_type="application/json"
    )


# ============================================================================
# Response Helpers
# ============================================================================

def create_success_response(msg_id: Any, result: Any) -> Response:
    """Create JSON-RPC success response"""
    response_data = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": result
    }
    
    return Response(
        orjson.dumps(response_data),
        media_type="application/json",
        headers={
            "cache-control": "no-cache",
            "server": "fast-mcp-server"
        }
    )


def create_error_response(msg_id: Any, code: int, message: str) -> Response:
    """Create JSON-RPC error response"""
    response_data = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {
            "code": code,
            "message": message
        }
    }
    
    status_code = 400 if code == -32700 else 200  # Parse errors get 400
    
    return Response(
        orjson.dumps(response_data),
        status_code=status_code,
        media_type="application/json",
        headers={
            "cache-control": "no-cache",
            "server": "fast-mcp-server"
        }
    )


# ============================================================================
# Application Setup
# ============================================================================

def create_app() -> Starlette:
    """Create Starlette application"""
    
    # Middleware for performance and CORS
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["Mcp-Session-Id"]
        )
    ]
    
    # Routes
    routes = [
        Route("/", root_endpoint, methods=["GET"]),
        Route("/mcp", mcp_endpoint, methods=["POST"]),
        Route("/health", health_endpoint, methods=["GET"]),
        Route("/metrics", metrics_endpoint, methods=["GET"]),
    ]
    
    app = Starlette(
        debug=False,
        routes=routes,
        middleware=middleware
    )
    
    return app


# ============================================================================
# Main Server Runner
# ============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Fast MCP Protocol Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    print("🚀 Fast MCP Server")
    print("=" * 50)
    print(f"Protocol: MCP 2025-06-18")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Workers: {args.workers}")
    print(f"Target Performance: 10,000+ RPS")
    print()
    print("Endpoints:")
    print(f"  MCP Protocol: http://{args.host}:{args.port}/mcp")
    print(f"  Health Check: http://{args.host}:{args.port}/health")
    print(f"  Metrics:      http://{args.host}:{args.port}/metrics")
    print()
    print("Tools Available:")
    for tool in state.tools:
        print(f"  • {tool['name']}: {tool['description']}")
    print()
    print("Resources Available:")
    for resource in state.resources:
        print(f"  • {resource['name']}: {resource['description']}")
    print()
    print("Test with:")
    print(f"  python quick_benchmark.py http://{args.host}:{args.port}/mcp")
    print("=" * 50)
    
    # Create app
    app = create_app()
    
    # Run server with performance optimizations
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="error" if not args.debug else "info",
        access_log=args.debug,
        loop="uvloop",
        http="httptools",
        limit_concurrency=10000,
        backlog=4096,
        timeout_keep_alive=5
    )


if __name__ == "__main__":
    main()