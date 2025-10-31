#!/usr/bin/env python3
# src/chuk_mcp_server/endpoints/mcp.py
"""
MCP Endpoint - Handles core MCP protocol requests with SSE support
"""

import logging
from typing import Any

import orjson

# starlette
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

# chuk_mcp_server - Fix import path
from ..protocol import MCPProtocolHandler

# logger
logger = logging.getLogger(__name__)


class MCPEndpoint:
    """Core MCP endpoint handler with SSE support for Inspector compatibility."""

    def __init__(self, protocol_handler: MCPProtocolHandler):
        self.protocol = protocol_handler

    async def handle_request(self, request: Request) -> Response:
        """Main MCP endpoint handler."""

        # Handle CORS preflight
        if request.method == "OPTIONS":
            return self._cors_response()

        # Handle GET - return server info
        if request.method == "GET":
            return await self._handle_get(request)

        # Handle POST - process MCP requests
        if request.method == "POST":
            return await self._handle_post(request)

        return Response("Method not allowed", status_code=405)

    def _cors_response(self) -> Response:
        """Return CORS preflight response."""
        return Response(
            "",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            },
        )

    async def _handle_get(self, request: Request) -> Response:  # noqa: ARG002
        """Handle GET request - return server information."""
        server_info = {
            "name": self.protocol.server_info.name,
            "version": self.protocol.server_info.version,
            "protocol": "MCP 2025-03-26",
            "status": "ready",
            "tools": len(self.protocol.tools),
            "resources": len(self.protocol.resources),
            "powered_by": "ChukMCPServer with chuk_mcp",
        }

        return Response(
            orjson.dumps(server_info), media_type="application/json", headers={"Access-Control-Allow-Origin": "*"}
        )

    async def _handle_post(self, request: Request) -> Response:
        """Handle POST request - process MCP protocol messages."""
        accept_header = request.headers.get("accept", "")
        session_id = request.headers.get("mcp-session-id")

        # Extract OAuth token from Authorization header (case-insensitive)
        auth_header = request.headers.get("authorization", "")
        oauth_token = None

        # Check for Bearer token (case-insensitive)
        if auth_header.lower().startswith("bearer "):
            # Find where "bearer " ends (handle any casing)
            bearer_prefix_len = len("bearer ")
            oauth_token = auth_header[bearer_prefix_len:]  # Remove first "Bearer " prefix

            # Handle double-Bearer bug in some MCP clients (e.g., "Bearer Bearer token")
            # This happens when clients incorrectly store "Bearer token" as the access_token value
            if oauth_token.lower().startswith("bearer "):
                logger.warning("⚠️  Double-Bearer prefix detected in Authorization header, stripping again")
                oauth_token = oauth_token[len("bearer ") :]  # Strip second "Bearer " prefix

            logger.info(
                f"📋 Extracted OAuth token: {oauth_token[:16] if oauth_token else 'None'}... (original header: {auth_header[:30]}...)"
            )
        elif auth_header:
            logger.warning(f"⚠️  Authorization header present but doesn't start with 'Bearer ': {auth_header[:30]}...")

        try:
            # Parse request body
            body = await request.body()
            request_data = orjson.loads(body) if body else {}
            method = request_data.get("method")

            logger.debug(f"Processing {method} request")

            # Route based on Accept header
            if "text/event-stream" in accept_header:
                # SSE streaming
                return await self._handle_sse_request(request_data, session_id, oauth_token)
            else:
                # Regular JSON-RPC request
                return await self._handle_json_request(request_data, session_id, method, oauth_token)

        except orjson.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return self._error_response(None, -32700, f"Parse error: {str(e)}")
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            return self._error_response(None, -32603, f"Internal error: {str(e)}")

    async def _handle_json_request(
        self, request_data: dict[str, Any], session_id: str | None, method: str, oauth_token: str | None = None
    ) -> Response:
        """Handle regular JSON-RPC request."""

        # Validate session ID for non-initialize requests
        if method != "initialize" and not session_id:
            return self._error_response(
                request_data.get("id", "server-error"), -32600, "Bad Request: Missing session ID"
            )

        # Process the request through protocol handler
        response, new_session_id = await self.protocol.handle_request(request_data, session_id, oauth_token)

        # Handle notifications (no response)
        if response is None:
            return Response("", status_code=202, headers={"Access-Control-Allow-Origin": "*"})

        # Build response headers
        headers = {"Access-Control-Allow-Origin": "*"}
        if new_session_id:
            headers["Mcp-Session-Id"] = new_session_id

        return Response(orjson.dumps(response), media_type="application/json", headers=headers)

    async def _handle_sse_request(
        self, request_data: dict[str, Any], session_id: str | None, oauth_token: str | None = None
    ) -> StreamingResponse:
        """Handle SSE request for Inspector compatibility."""

        created_session_id = None
        method = request_data.get("method")

        # Create session ID for initialize requests
        if method == "initialize":
            client_info = request_data.get("params", {}).get("clientInfo", {})
            protocol_version = request_data.get("params", {}).get("protocolVersion", "2025-03-26")
            created_session_id = self.protocol.session_manager.create_session(client_info, protocol_version)
            logger.info(f"🔑 Created SSE session: {created_session_id[:8]}...")

        return StreamingResponse(
            self._sse_stream_generator(request_data, created_session_id or session_id, method, oauth_token),
            media_type="text/event-stream",
            headers=self._sse_headers(created_session_id),
        )

    async def _sse_stream_generator(
        self, request_data: dict[str, Any], session_id: str | None, method: str, oauth_token: str | None = None
    ):
        """Generate SSE stream response."""
        try:
            # Process the request through protocol handler
            response, _ = await self.protocol.handle_request(request_data, session_id, oauth_token)

            if response:
                logger.debug(f"📡 Streaming SSE response for {method}")

                # Send complete SSE event in proper format
                # CRITICAL: Must send all 3 parts as separate yields for Inspector compatibility
                yield "event: message\r\n"
                yield f"data: {orjson.dumps(response).decode()}\r\n"
                yield "\r\n"

                logger.debug(f"✅ SSE response sent for {method}")

            # For notifications, we don't send anything (which is correct)

        except Exception as e:
            logger.error(f"SSE stream error: {e}")

            # Send error event
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {"code": -32603, "message": str(e)},
            }
            yield "event: error\r\n"
            yield f"data: {orjson.dumps(error_response).decode()}\r\n"
            yield "\r\n"

    def _sse_headers(self, session_id: str | None) -> dict[str, str]:
        """Build SSE response headers."""
        headers = {"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache", "Connection": "keep-alive"}

        if session_id:
            headers["Mcp-Session-Id"] = session_id

        return headers

    def _error_response(self, msg_id: Any, code: int, message: str) -> Response:
        """Create error response."""
        error_response = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}

        status_code = 400 if code in [-32700, -32600] else 500

        return Response(
            orjson.dumps(error_response),
            status_code=status_code,
            media_type="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )
