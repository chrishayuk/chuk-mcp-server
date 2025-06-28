#!/usr/bin/env python3
"""
handlers.py - HTTP Request Handlers

Fast, optimized HTTP handlers for the MCP server endpoints.
Handles request parsing, response generation, and error handling.
"""

import orjson
from typing import Any, Dict, Optional
from starlette.requests import Request
from starlette.responses import Response

from .models import get_state
from .protocol import (
    route_method, 
    validate_jsonrpc_message, 
    is_notification,
    PARSE_ERROR, 
    INVALID_REQUEST, 
    METHOD_NOT_FOUND, 
    INVALID_PARAMS, 
    INTERNAL_ERROR
)


# ============================================================================
# Core MCP Endpoint
# ============================================================================

async def mcp_endpoint(request: Request) -> Response:
    """
    Main MCP protocol endpoint - handles all JSON-RPC requests
    
    Optimized for maximum performance with minimal allocations
    """
    state = get_state()
    state.increment_requests()
    
    try:
        # Fast body parsing
        body = await request.body()
        if not body:
            return create_error_response(None, PARSE_ERROR, "Parse error: Empty body")
        
        # Parse JSON with orjson for speed
        try:
            message = orjson.loads(body)
        except orjson.JSONDecodeError as e:
            return create_error_response(None, PARSE_ERROR, f"Parse error: {str(e)}")
        
        # Extract message components
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        # Validate JSON-RPC structure
        is_valid, error_msg = validate_jsonrpc_message(message)
        if not is_valid:
            return create_error_response(msg_id, INVALID_REQUEST, error_msg)
        
        # Handle notifications (no response needed)
        if is_notification(message):
            if method == "notifications/initialized":
                return Response("", status_code=204)
            else:
                # Unknown notification - silently ignore per JSON-RPC spec
                return Response("", status_code=204)
        
        # Get session for non-initialize requests
        session = None
        if method != "initialize":
            session_id = request.headers.get("Mcp-Session-Id")
            session = state.get_session(session_id)
            # Note: We allow requests without session for compatibility
        
        # Route to method handler
        try:
            result, new_session_id = route_method(method, params, session)
            response = create_success_response(msg_id, result)
            
            # Add session header for initialize
            if new_session_id:
                response.headers["Mcp-Session-Id"] = new_session_id
            
            return response
            
        except ValueError as e:
            # Invalid parameters or method not found
            if "not found" in str(e).lower():
                return create_error_response(msg_id, METHOD_NOT_FOUND, str(e))
            else:
                return create_error_response(msg_id, INVALID_PARAMS, str(e))
        
        except Exception as e:
            # Internal server error
            state.increment_errors()
            return create_error_response(msg_id, INTERNAL_ERROR, f"Internal error: {str(e)}")
    
    except Exception as e:
        # Catch-all for unexpected errors
        state.increment_errors()
        return create_error_response(None, INTERNAL_ERROR, f"Server error: {str(e)}")


# ============================================================================
# Health and Monitoring Endpoints
# ============================================================================

async def health_endpoint(request: Request) -> Response:
    """Fast health check endpoint"""
    state = get_state()
    
    # Pre-computed health response for speed
    health_data = {
        "status": "healthy",
        "uptime_seconds": state.metrics.uptime(),
        "total_requests": state.metrics.total_requests,
        "requests_per_second": state.metrics.rps(),
        "active_sessions": len(state.sessions),
        "timestamp": state.metrics.start_time + state.metrics.uptime()
    }
    
    return Response(
        orjson.dumps(health_data),
        media_type="application/json",
        headers={
            "cache-control": "no-cache",
            "server": "fast-mcp-server"
        }
    )


async def metrics_endpoint(request: Request) -> Response:
    """Detailed metrics endpoint"""
    state = get_state()
    
    metrics_data = {
        "server": {
            "name": "fast-mcp-server",
            "version": "1.0.0",
            "uptime_seconds": state.metrics.uptime(),
            "start_time": state.metrics.start_time
        },
        "requests": {
            "total": state.metrics.total_requests,
            "per_second": state.metrics.rps(),
            "errors": state.metrics.errors
        },
        "mcp": {
            "active_sessions": len(state.sessions),
            "tool_calls": state.metrics.tool_calls,
            "resource_reads": state.metrics.resource_reads
        },
        "capabilities": {
            "tools_count": len(state.get_tools()),
            "resources_count": len(state.get_resources())
        },
        "timestamp": state.metrics.start_time + state.metrics.uptime()
    }
    
    return Response(
        orjson.dumps(metrics_data),
        media_type="application/json",
        headers={
            "cache-control": "no-cache",
            "server": "fast-mcp-server"
        }
    )


async def root_endpoint(request: Request) -> Response:
    """Root endpoint with server information"""
    state = get_state()
    
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
            "Real-time metrics",
            "Sub-millisecond response times"
        ],
        "performance": {
            "target_rps": "10,000+",
            "uptime_seconds": state.metrics.uptime(),
            "current_rps": state.metrics.rps(),
            "total_requests": state.metrics.total_requests
        },
        "capabilities": {
            "tools": len(state.get_tools()),
            "resources": len(state.get_resources()),
            "sessions": len(state.sessions)
        }
    }
    
    return Response(
        orjson.dumps(info, option=orjson.OPT_INDENT_2),
        media_type="application/json",
        headers={
            "cache-control": "public, max-age=300",  # Cache for 5 minutes
            "server": "fast-mcp-server"
        }
    )


# ============================================================================
# Response Helpers
# ============================================================================

def create_success_response(msg_id: Any, result: Any) -> Response:
    """Create optimized JSON-RPC success response"""
    response_data = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": result
    }
    
    # Use orjson for fastest serialization
    body = orjson.dumps(response_data)
    
    return Response(
        body,
        media_type="application/json",
        headers={
            "cache-control": "no-cache",
            "server": "fast-mcp-server",
            "content-length": str(len(body))
        }
    )


def create_error_response(msg_id: Any, code: int, message: str, data: Any = None) -> Response:
    """Create optimized JSON-RPC error response"""
    error_obj = {
        "code": code,
        "message": message
    }
    if data is not None:
        error_obj["data"] = data
    
    response_data = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": error_obj
    }
    
    # Use orjson for fastest serialization
    body = orjson.dumps(response_data)
    
    # HTTP status code based on JSON-RPC error
    if code == PARSE_ERROR:
        status_code = 400  # Bad Request
    elif code == INVALID_REQUEST:
        status_code = 400  # Bad Request
    elif code == METHOD_NOT_FOUND:
        status_code = 404  # Not Found (optional, could be 200)
    elif code == INVALID_PARAMS:
        status_code = 422  # Unprocessable Entity
    else:
        status_code = 500  # Internal Server Error
    
    return Response(
        body,
        status_code=status_code,
        media_type="application/json",
        headers={
            "cache-control": "no-cache",
            "server": "fast-mcp-server",
            "content-length": str(len(body))
        }
    )


# ============================================================================
# Middleware and Utilities
# ============================================================================

async def cleanup_middleware(request: Request, call_next):
    """Middleware to cleanup expired sessions periodically"""
    response = await call_next(request)
    
    # Cleanup expired sessions every 100 requests
    state = get_state()
    if state.metrics.total_requests % 100 == 0:
        expired_count = state.cleanup_expired_sessions()
        if expired_count > 0:
            # Could log this if needed
            pass
    
    return response


def get_client_info(request: Request) -> Dict[str, Any]:
    """Extract client information from request headers"""
    user_agent = request.headers.get("user-agent", "unknown")
    client_ip = request.client.host if request.client else "unknown"
    
    return {
        "user_agent": user_agent,
        "client_ip": client_ip,
        "headers": dict(request.headers)
    }