#!/usr/bin/env python3
"""
CleanMCP Protocol Handler - Core MCP protocol implementation with chuk_mcp
"""

import asyncio
import json
import time
import uuid
import logging
from typing import Dict, Any, Optional, List

from .types import Tool, Resource, ServerInfo, Capabilities, format_content

# chuk_mcp imports (always available as dependency)
from chuk_mcp.mcp_client.messages.initialize.mcp_server_info import MCPServerInfo
from chuk_mcp.mcp_client.messages.initialize.mcp_server_capabilities import (
    MCPServerCapabilities, ToolsCapability, ResourcesCapability, PromptsCapability
)
from chuk_mcp.mcp_client.messages.tools.tool import Tool as ChukTool
from chuk_mcp.mcp_client.messages.resources.resource import Resource as ChukResource
from chuk_mcp.mcp_client.messages.resources.resource_content import ResourceContent

logger = logging.getLogger(__name__)


# ============================================================================
# Session Management
# ============================================================================

class SessionManager:
    """Manage MCP sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
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
        logger.info(f"Created session {session_id[:8]}... for {client_info.get('name', 'unknown')}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def update_activity(self, session_id: str):
        """Update session last activity."""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = time.time()
    
    def cleanup_expired(self, max_age: int = 3600):
        """Remove expired sessions."""
        now = time.time()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session["last_activity"] > max_age
        ]
        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Cleaned up expired session {sid[:8]}...")


# ============================================================================
# Protocol Handler with chuk_mcp Integration
# ============================================================================

class MCPProtocolHandler:
    """Core MCP protocol handler powered by chuk_mcp."""
    
    def __init__(self, server_info: ServerInfo, capabilities: Capabilities):
        self.server_info = server_info
        self.capabilities = capabilities
        self.session_manager = SessionManager()
        
        # Tool and resource registries
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        
        # Setup chuk_mcp components
        self._setup_chuk_mcp()
        
        logger.info("✅ MCP protocol handler initialized with chuk_mcp")
    
    def _setup_chuk_mcp(self):
        """Setup chuk_mcp components."""
        # Create chuk_mcp server info
        self.chuk_server_info = MCPServerInfo(
            name=self.server_info.name,
            version=self.server_info.version,
            title=self.server_info.title or self.server_info.name
        )
        
        # Create chuk_mcp capabilities
        caps_dict = {}
        
        if self.capabilities.tools:
            caps_dict["tools"] = ToolsCapability(listChanged=True)
        
        if self.capabilities.resources:
            caps_dict["resources"] = ResourcesCapability(
                listChanged=True, 
                subscribe=False
            )
        
        if self.capabilities.prompts:
            caps_dict["prompts"] = PromptsCapability(listChanged=True)
        
        self.chuk_capabilities = MCPServerCapabilities(**caps_dict)
        
        logger.debug("chuk_mcp components initialized")
    
    def register_tool(self, tool: Tool):
        """Register a tool."""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def register_resource(self, resource: Resource):
        """Register a resource."""
        self.resources[resource.uri] = resource
        logger.debug(f"Registered resource: {resource.uri}")
    
    def get_tools_list(self) -> List[Dict[str, Any]]:
        """Get list of tools in MCP format using chuk_mcp."""
        tools_list = []
        
        for tool in self.tools.values():
            # Use chuk_mcp Tool class for robust serialization
            chuk_tool = ChukTool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.to_mcp_format()["inputSchema"]
            )
            tools_list.append(chuk_tool.model_dump())
        
        return tools_list
    
    def get_resources_list(self) -> List[Dict[str, Any]]:
        """Get list of resources in MCP format using chuk_mcp."""
        resources_list = []
        
        for resource in self.resources.values():
            # Use chuk_mcp Resource class for robust serialization
            chuk_resource = ChukResource(
                uri=resource.uri,
                name=resource.name,
                description=resource.description,
                mimeType=resource.mime_type
            )
            resources_list.append(chuk_resource.model_dump())
        
        return resources_list
    
    async def handle_request(self, message: Dict[str, Any], session_id: Optional[str] = None) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Handle an MCP request."""
        try:
            method = message.get("method")
            params = message.get("params", {})
            msg_id = message.get("id")
            
            logger.debug(f"Handling {method} (ID: {msg_id})")
            
            # Update session activity
            if session_id:
                self.session_manager.update_activity(session_id)
            
            # Route to appropriate handler
            if method == "initialize":
                return await self._handle_initialize(params, msg_id)
            elif method == "notifications/initialized":
                logger.info("✅ Initialized notification received")
                return None, None  # Notifications don't return responses
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
                return self._create_error_response(msg_id, -32601, f"Method not found: {method}"), None
        
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return self._create_error_response(msg_id, -32603, f"Internal error: {str(e)}"), None
    
    async def _handle_initialize(self, params: Dict[str, Any], msg_id: Any) -> tuple[Dict[str, Any], str]:
        """Handle initialize request using chuk_mcp."""
        client_info = params.get("clientInfo", {})
        protocol_version = params.get("protocolVersion", "2025-03-26")
        
        # Create session
        session_id = self.session_manager.create_session(client_info, protocol_version)
        
        # Build response using chuk_mcp
        result = {
            "protocolVersion": protocol_version,
            "serverInfo": self.chuk_server_info.model_dump(),
            "capabilities": self.chuk_capabilities.model_dump(exclude_none=True)
        }
        
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        
        client_name = client_info.get('name', 'unknown')
        logger.info(f"🤝 Initialized session {session_id[:8]}... for {client_name} (v{protocol_version})")
        return response, session_id
    
    async def _handle_ping(self, msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle ping request."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {}
        }, None
    
    async def _handle_tools_list(self, msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle tools/list request."""
        tools_list = self.get_tools_list()
        result = {"tools": tools_list}
        
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        
        logger.info(f"📋 Returning {len(tools_list)} tools")
        return response, None
    
    async def _handle_tools_call(self, params: Dict[str, Any], msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return self._create_error_response(msg_id, -32602, f"Unknown tool: {tool_name}"), None
        
        try:
            tool = self.tools[tool_name]
            result = await tool.execute(arguments)
            
            # Format response content
            content = format_content(result)
            
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": content}
            }
            
            logger.info(f"🔧 Executed tool {tool_name}")
            return response, None
            
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            return self._create_error_response(msg_id, -32603, f"Tool execution error: {str(e)}"), None
    
    async def _handle_resources_list(self, msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle resources/list request."""
        resources_list = self.get_resources_list()
        result = {"resources": resources_list}
        
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        
        logger.info(f"📂 Returning {len(resources_list)} resources")
        return response, None
    
    async def _handle_resources_read(self, params: Dict[str, Any], msg_id: Any) -> tuple[Dict[str, Any], None]:
        """Handle resources/read request using chuk_mcp."""
        uri = params.get("uri")
        
        if uri not in self.resources:
            return self._create_error_response(msg_id, -32602, f"Unknown resource: {uri}"), None
        
        try:
            resource = self.resources[uri]
            content = await resource.read()
            
            # Use chuk_mcp ResourceContent for robust serialization
            resource_content = ResourceContent(
                uri=uri,
                mimeType=resource.mime_type,
                text=content
            )
            
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"contents": [resource_content.model_dump()]}
            }
            
            logger.info(f"📖 Read resource {uri}")
            return response, None
            
        except Exception as e:
            logger.error(f"Resource read error for {uri}: {e}")
            return self._create_error_response(msg_id, -32603, f"Resource read error: {str(e)}"), None
    
    def _create_error_response(self, msg_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message}
        }