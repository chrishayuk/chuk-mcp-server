#!/usr/bin/env python3
"""
protocol.py - MCP Protocol Implementation

Handles all MCP protocol operations including:
- Session management and initialization
- Tool discovery and execution
- Resource listing and reading
- Protocol validation and error handling
"""

import json
import time
from typing import Dict, Any, Optional, Tuple

from .models import get_state, MCPSession


# ============================================================================
# Protocol Constants
# ============================================================================

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "fast-mcp-server"
SERVER_VERSION = "1.0.0"

# JSON-RPC Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


# ============================================================================
# Core Protocol Handlers
# ============================================================================

def handle_initialize(params: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Handle MCP initialize request
    
    Returns:
        Tuple of (result_dict, session_id)
    """
    state = get_state()
    
    # Extract client information
    client_info = params.get("clientInfo", {"name": "unknown", "version": "0.0.0"})
    protocol_version = params.get("protocolVersion", PROTOCOL_VERSION)
    
    # Create new session
    session = state.create_session(client_info, protocol_version)
    
    # Build capabilities response
    capabilities = {
        "tools": {"listChanged": True},
        "resources": {"listChanged": True},
        "logging": {}
    }
    
    # Build server info
    server_info = {
        "name": SERVER_NAME,
        "version": SERVER_VERSION
    }
    
    result = {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": capabilities,
        "serverInfo": server_info
    }
    
    return result, session.session_id


def handle_ping(params: Dict[str, Any], session: Optional[MCPSession] = None) -> Dict[str, Any]:
    """Handle ping request - simple heartbeat"""
    return {}


def handle_tools_list(params: Dict[str, Any], session: Optional[MCPSession] = None) -> Dict[str, Any]:
    """Handle tools/list request"""
    state = get_state()
    state.increment_tool_calls()
    
    tools = state.get_tools()
    return {"tools": tools}


def handle_tools_call(params: Dict[str, Any], session: Optional[MCPSession] = None) -> Dict[str, Any]:
    """Handle tools/call request"""
    state = get_state()
    state.increment_tool_calls()
    
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if not tool_name:
        raise ValueError("Tool name is required")
    
    # Get tool definition
    tool = state.get_tool_by_name(tool_name)
    if not tool:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    # Execute the tool
    result = execute_tool(tool_name, arguments)
    
    return {
        "content": [
            {"type": "text", "text": result}
        ]
    }


def handle_resources_list(params: Dict[str, Any], session: Optional[MCPSession] = None) -> Dict[str, Any]:
    """Handle resources/list request"""
    state = get_state()
    
    resources = state.get_resources()
    return {"resources": resources}


def handle_resources_read(params: Dict[str, Any], session: Optional[MCPSession] = None) -> Dict[str, Any]:
    """Handle resources/read request"""
    state = get_state()
    state.increment_resource_reads()
    
    uri = params.get("uri")
    if not uri:
        raise ValueError("Resource URI is required")
    
    # Get resource definition
    resource = state.get_resource_by_uri(uri)
    if not resource:
        raise ValueError(f"Unknown resource: {uri}")
    
    # Read the resource content
    content = read_resource(uri)
    
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": resource.mime_type,
                "text": content
            }
        ]
    }


# ============================================================================
# Tool Execution Engine
# ============================================================================

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a tool with given arguments
    
    This is where you'd integrate with chuk-tool-processor
    For now, we have demo implementations
    """
    
    if tool_name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        
        # Validate inputs
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValueError("Both 'a' and 'b' must be numbers")
        
        result = a + b
        return f"The sum of {a} and {b} is {result}"
    
    elif tool_name == "hello":
        name = arguments.get("name", "World")
        
        # Validate input
        if not isinstance(name, str):
            raise ValueError("Name must be a string")
        
        return f"Hello, {name}! 👋 Greetings from {SERVER_NAME}!"
    
    elif tool_name == "time":
        current_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        timestamp = time.time()
        return f"Current time: {current_time} (timestamp: {timestamp})"
    
    else:
        raise ValueError(f"Tool '{tool_name}' is not implemented")


# ============================================================================
# Resource Reading Engine
# ============================================================================

def read_resource(uri: str) -> str:
    """
    Read resource content by URI
    
    This is where you'd integrate with your resource providers
    For now, we have demo implementations
    """
    state = get_state()
    
    if uri == "demo://server-info":
        content = state.get_server_info()
        return json.dumps(content, indent=2)
    
    elif uri == "demo://metrics":
        metrics = state.metrics.to_dict()
        return json.dumps(metrics, indent=2)
    
    elif uri == "demo://tools":
        tools = state.get_tools()
        return json.dumps(tools, indent=2)
    
    else:
        raise ValueError(f"Resource '{uri}' is not implemented")


# ============================================================================
# Protocol Message Routing
# ============================================================================

# Method routing table
METHOD_HANDLERS = {
    "initialize": handle_initialize,
    "ping": handle_ping,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
    "resources/list": handle_resources_list,
    "resources/read": handle_resources_read,
}


def route_method(method: str, params: Dict[str, Any], session: Optional[MCPSession] = None) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Route MCP method to appropriate handler
    
    Returns:
        Tuple of (result, session_id) - session_id only for initialize
    """
    
    if method not in METHOD_HANDLERS:
        raise ValueError(f"Method not found: {method}")
    
    handler = METHOD_HANDLERS[method]
    
    # Special case for initialize which returns session_id
    if method == "initialize":
        return handler(params)
    else:
        result = handler(params, session)
        return result, None


def validate_jsonrpc_message(message: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate basic JSON-RPC 2.0 message structure
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Check JSON-RPC version
    if message.get("jsonrpc") != "2.0":
        return False, "Invalid Request: Must be JSON-RPC 2.0"
    
    # Check method exists
    if "method" not in message:
        return False, "Invalid Request: Missing method"
    
    # Check method is string
    if not isinstance(message["method"], str):
        return False, "Invalid Request: Method must be string"
    
    # Check params if present
    if "params" in message and not isinstance(message["params"], dict):
        return False, "Invalid Request: Params must be object"
    
    return True, ""


def is_notification(message: Dict[str, Any]) -> bool:
    """Check if message is a notification (no 'id' field)"""
    return "id" not in message


# ============================================================================
# Error Handling
# ============================================================================

class MCPProtocolError(Exception):
    """Custom exception for MCP protocol errors"""
    
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error {code}: {message}")


def create_error_dict(code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """Create JSON-RPC error object"""
    error = {
        "code": code,
        "message": message
    }
    if data is not None:
        error["data"] = data
    return error