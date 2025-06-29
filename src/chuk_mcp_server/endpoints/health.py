#!/usr/bin/env python3
# chuk_mcp_server/endpoints/health.py
"""
Health Endpoint - Provides health check and status information
"""

import time
import logging
from typing import Dict, Any

import orjson
from starlette.requests import Request
from starlette.responses import Response

from ..protocol import MCPProtocolHandler

logger = logging.getLogger(__name__)


class HealthEndpoint:
    """Health check endpoint for monitoring and diagnostics."""
    
    def __init__(self, protocol_handler: MCPProtocolHandler):
        self.protocol = protocol_handler
        self.start_time = time.time()
    
    async def handle_request(self, request: Request) -> Response:
        """Handle health check request."""
        
        if request.method == "GET":
            return await self._handle_health_check(request)
        else:
            return Response("Method not allowed", status_code=405)
    
    async def _handle_health_check(self, request: Request) -> Response:
        """Return comprehensive health status."""
        
        # Build health data
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime": time.time() - self.start_time,
            "server": {
                "name": self.protocol.server_info.name,
                "version": self.protocol.server_info.version,
                "protocol": "MCP 2025-03-26",
                "powered_by": "ChukMCPServer with chuk_mcp"
            },
            "capabilities": {
                "tools": len(self.protocol.tools),
                "resources": len(self.protocol.resources),
                "sessions": len(self.protocol.session_manager.sessions)
            },
            "features": [
                "Inspector compatible",
                "SSE streaming",
                "Session management", 
                "Type-safe tools",
                "Rich resources",
                "Error handling"
            ]
        }
        
        # Add detailed tool information if requested
        if request.query_params.get("include_tools", "").lower() == "true":
            health_data["tools"] = {
                "count": len(self.protocol.tools),
                "names": list(self.protocol.tools.keys())
            }
        
        # Add detailed resource information if requested  
        if request.query_params.get("include_resources", "").lower() == "true":
            health_data["resources"] = {
                "count": len(self.protocol.resources),
                "uris": list(self.protocol.resources.keys())
            }
        
        # Add session information if requested
        if request.query_params.get("include_sessions", "").lower() == "true":
            sessions_info = []
            for session_id, session_data in self.protocol.session_manager.sessions.items():
                sessions_info.append({
                    "id": session_id[:8] + "...",  # Truncated for privacy
                    "client": session_data.get("client_info", {}).get("name", "unknown"),
                    "protocol_version": session_data.get("protocol_version", "unknown"),
                    "created_at": session_data.get("created_at", 0),
                    "last_activity": session_data.get("last_activity", 0)
                })
            health_data["sessions_detail"] = sessions_info
        
        logger.debug("Health check completed")
        
        return Response(
            orjson.dumps(health_data, option=orjson.OPT_INDENT_2),
            media_type="application/json",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*"
            }
        )