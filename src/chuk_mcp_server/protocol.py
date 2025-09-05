#!/usr/bin/env python3
# src/chuk_mcp_server/protocol.py
"""
ChukMCPServer Protocol Handler - Core MCP protocol implementation with chuk_mcp
"""

import logging
import time
import uuid
from typing import Any

from .types import (
    ResourceHandler,
    ServerCapabilities,
    # Direct chuk_mcp types (no conversion needed)
    ServerInfo,
    # Framework handlers
    ToolHandler,
    format_content,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Session Management
# ============================================================================


class SessionManager:
    """Manage MCP sessions."""

    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}

    def create_session(self, client_info: dict[str, Any], protocol_version: str) -> str:
        """Create a new session."""
        session_id = str(uuid.uuid4()).replace("-", "")
        self.sessions[session_id] = {
            "id": session_id,
            "client_info": client_info,
            "protocol_version": protocol_version,
            "created_at": time.time(),
            "last_activity": time.time(),
        }
        logger.info(f"Created session {session_id[:8]}... for {client_info.get('name', 'unknown')}")
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def update_activity(self, session_id: str):
        """Update session last activity."""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = time.time()

    def cleanup_expired(self, max_age: int = 3600):
        """Remove expired sessions."""
        now = time.time()
        expired = [sid for sid, session in self.sessions.items() if now - session["last_activity"] > max_age]
        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Cleaned up expired session {sid[:8]}...")


# ============================================================================
# Protocol Handler with chuk_mcp Integration
# ============================================================================


class MCPProtocolHandler:
    """Core MCP protocol handler powered by chuk_mcp."""

    def __init__(self, server_info: ServerInfo, capabilities: ServerCapabilities):
        # Use chuk_mcp types directly - no conversion needed
        self.server_info = server_info
        self.capabilities = capabilities
        self.session_manager = SessionManager()

        # Tool and resource registries (now use handlers)
        self.tools: dict[str, ToolHandler] = {}
        self.resources: dict[str, ResourceHandler] = {}

        logger.info("✅ MCP protocol handler initialized with chuk_mcp")

    def register_tool(self, tool: ToolHandler):
        """Register a tool handler."""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def register_resource(self, resource: ResourceHandler):
        """Register a resource handler."""
        self.resources[resource.uri] = resource
        logger.debug(f"Registered resource: {resource.uri}")

    def get_tools_list(self) -> list[dict[str, Any]]:
        """Get list of tools in MCP format."""
        tools_list = []

        for tool_handler in self.tools.values():
            tools_list.append(tool_handler.to_mcp_format())

        return tools_list

    def get_resources_list(self) -> list[dict[str, Any]]:
        """Get list of resources in MCP format."""
        resources_list = []

        for resource_handler in self.resources.values():
            resources_list.append(resource_handler.to_mcp_format())

        return resources_list

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics for monitoring."""

        return {
            "tools": {
                "count": len(self.tools),
                "cache_hit_ratio": 1.0,  # Placeholder for now
            },
            "resources": {
                "count": len(self.resources),
                "cache_hit_ratio": 1.0,  # Placeholder for now
            },
            "sessions": {"active": len(self.session_manager.sessions), "total": len(self.session_manager.sessions)},
            "cache": {
                "tools_cached": True,  # Placeholder
                "resources_cached": True,  # Placeholder
                "cache_age": 0,  # Placeholder
            },
            "status": "operational",
        }

    async def handle_request(
        self, message: dict[str, Any], session_id: str | None = None
    ) -> tuple[dict[str, Any] | None, str | None]:
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

    async def _handle_initialize(self, params: dict[str, Any], msg_id: Any) -> tuple[dict[str, Any], str]:
        """Handle initialize request using chuk_mcp."""
        client_info = params.get("clientInfo", {})
        protocol_version = params.get("protocolVersion", "2025-06-18")

        # Create session
        session_id = self.session_manager.create_session(client_info, protocol_version)

        # Build response using chuk_mcp types directly
        result = {
            "protocolVersion": protocol_version,
            "serverInfo": self.server_info.model_dump(exclude_none=True),
            "capabilities": self.capabilities.model_dump(exclude_none=True),
        }

        response = {"jsonrpc": "2.0", "id": msg_id, "result": result}

        client_name = client_info.get("name", "unknown")
        logger.info(f"🤝 Initialized session {session_id[:8]}... for {client_name} (v{protocol_version})")
        return response, session_id

    async def _handle_ping(self, msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle ping request."""
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}, None

    async def _handle_tools_list(self, msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle tools/list request."""
        tools_list = self.get_tools_list()
        result = {"tools": tools_list}

        response = {"jsonrpc": "2.0", "id": msg_id, "result": result}

        logger.info(f"📋 Returning {len(tools_list)} tools")
        return response, None

    async def _handle_tools_call(self, params: dict[str, Any], msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            return self._create_error_response(msg_id, -32602, f"Unknown tool: {tool_name}"), None

        try:
            tool_handler = self.tools[tool_name]
            result = await tool_handler.execute(arguments)

            # Format response content using chuk_mcp content formatting
            content = format_content(result)

            response = {"jsonrpc": "2.0", "id": msg_id, "result": {"content": content}}

            logger.info(f"🔧 Executed tool {tool_name}")
            return response, None

        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            return self._create_error_response(msg_id, -32603, f"Tool execution error: {str(e)}"), None

    async def _handle_resources_list(self, msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle resources/list request."""
        resources_list = self.get_resources_list()
        result = {"resources": resources_list}

        response = {"jsonrpc": "2.0", "id": msg_id, "result": result}

        logger.info(f"📂 Returning {len(resources_list)} resources")
        return response, None

    async def _handle_resources_read(self, params: dict[str, Any], msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle resources/read request."""
        uri = params.get("uri")

        if uri not in self.resources:
            return self._create_error_response(msg_id, -32602, f"Unknown resource: {uri}"), None

        try:
            resource_handler = self.resources[uri]
            content = await resource_handler.read()

            # Build resource content response
            resource_content = {"uri": uri, "mimeType": resource_handler.mime_type, "text": content}

            response = {"jsonrpc": "2.0", "id": msg_id, "result": {"contents": [resource_content]}}

            logger.info(f"📖 Read resource {uri}")
            return response, None

        except Exception as e:
            logger.error(f"Resource read error for {uri}: {e}")
            return self._create_error_response(msg_id, -32603, f"Resource read error: {str(e)}"), None

    def _create_error_response(self, msg_id: Any, code: int, message: str) -> dict[str, Any]:
        """Create error response."""
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}
