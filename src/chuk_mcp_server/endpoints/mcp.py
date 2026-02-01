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
from .constants import (
    BEARER_PREFIX,
    CACHE_NO_CACHE,
    CONNECTION_KEEP_ALIVE,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_SSE,
    CORS_ALLOW_ALL,
    ERROR_METHOD_NOT_ALLOWED,
    FRAMEWORK_DESCRIPTION,
    HEADER_ACCEPT,
    HEADER_AUTHORIZATION,
    HEADER_CACHE_CONTROL,
    HEADER_CONNECTION,
    HEADER_CORS_HEADERS,
    HEADER_CORS_METHODS,
    HEADER_CORS_ORIGIN,
    HEADER_MCP_SESSION_ID,
    HEADERS_CORS_ONLY,
    JSONRPC_VERSION,
    MCP_PROTOCOL_FULL,
    MCP_PROTOCOL_VERSION,
    SSE_EVENT_ERROR,
    SSE_EVENT_MESSAGE,
    SSE_LINE_END,
    STATUS_READY,
    HttpStatus,
    JsonRpcErrorCode,
)

# logger
logger = logging.getLogger(__name__)

# JSON-RPC response key name
JSONRPC_VERSION_KEY = "jsonrpc"


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

        return Response(ERROR_METHOD_NOT_ALLOWED, status_code=HttpStatus.METHOD_NOT_ALLOWED)

    def _cors_response(self) -> Response:
        """Return CORS preflight response."""
        return Response(
            "",
            headers={
                HEADER_CORS_ORIGIN: CORS_ALLOW_ALL,
                HEADER_CORS_METHODS: "GET, POST, OPTIONS",
                HEADER_CORS_HEADERS: CORS_ALLOW_ALL,
            },
        )

    async def _handle_get(self, request: Request) -> Response:  # noqa: ARG002
        """Handle GET request - return server information."""
        server_info = {
            "name": self.protocol.server_info.name,
            "version": self.protocol.server_info.version,
            "protocol": MCP_PROTOCOL_FULL,
            "status": STATUS_READY,
            "tools": len(self.protocol.tools),
            "resources": len(self.protocol.resources),
            "powered_by": FRAMEWORK_DESCRIPTION,
        }

        return Response(orjson.dumps(server_info), media_type=CONTENT_TYPE_JSON, headers=HEADERS_CORS_ONLY)

    async def _handle_post(self, request: Request) -> Response:
        """Handle POST request - process MCP protocol messages."""
        accept_header = request.headers.get(HEADER_ACCEPT, "")
        session_id = request.headers.get(HEADER_MCP_SESSION_ID.lower())

        # Extract OAuth token from Authorization header (case-insensitive)
        auth_header = request.headers.get(HEADER_AUTHORIZATION, "")
        oauth_token = None

        # Check for Bearer token (case-insensitive)
        if auth_header.lower().startswith(BEARER_PREFIX):
            # Find where "bearer " ends (handle any casing)
            bearer_prefix_len = len(BEARER_PREFIX)
            oauth_token = auth_header[bearer_prefix_len:]  # Remove first "Bearer " prefix

            # Handle double-Bearer bug in some MCP clients (e.g., "Bearer Bearer token")
            # This happens when clients incorrectly store "Bearer token" as the access_token value
            if oauth_token.lower().startswith(BEARER_PREFIX):
                logger.warning("Double-Bearer prefix detected in Authorization header, stripping again")
                oauth_token = oauth_token[len(BEARER_PREFIX) :]  # Strip second "Bearer " prefix

            logger.debug(
                f"Extracted OAuth token: {oauth_token[:16] if oauth_token else 'None'}... (original header: {auth_header[:30]}...)"
            )
        elif auth_header:
            logger.warning(f"Authorization header present but doesn't start with 'Bearer ': {auth_header[:30]}...")

        try:
            # Parse request body
            body = await request.body()
            request_data = orjson.loads(body) if body else {}
            method = request_data.get("method")

            logger.debug(f"Processing {method} request")

            # Route based on Accept header
            if CONTENT_TYPE_SSE in accept_header:
                # SSE streaming
                return await self._handle_sse_request(request_data, session_id, oauth_token)
            else:
                # Regular JSON-RPC request
                return await self._handle_json_request(request_data, session_id, method, oauth_token)

        except orjson.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return self._error_response(None, JsonRpcErrorCode.PARSE_ERROR, f"Parse error: {str(e)}")
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            return self._error_response(None, JsonRpcErrorCode.INTERNAL_ERROR, f"Internal error: {str(e)}")

    async def _handle_json_request(
        self, request_data: dict[str, Any], session_id: str | None, method: str, oauth_token: str | None = None
    ) -> Response:
        """Handle regular JSON-RPC request."""

        # Validate session ID for non-initialize requests
        if method != "initialize" and not session_id:
            return self._error_response(
                request_data.get("id", "server-error"),
                JsonRpcErrorCode.INVALID_REQUEST,
                "Bad Request: Missing session ID",
            )

        # Process the request through protocol handler
        response, new_session_id = await self.protocol.handle_request(request_data, session_id, oauth_token)

        # Handle notifications (no response)
        if response is None:
            return Response("", status_code=HttpStatus.ACCEPTED, headers=HEADERS_CORS_ONLY)

        # Build response headers
        headers: dict[str, str] = {HEADER_CORS_ORIGIN: CORS_ALLOW_ALL}
        if new_session_id:
            headers[HEADER_MCP_SESSION_ID] = new_session_id

        return Response(orjson.dumps(response), media_type=CONTENT_TYPE_JSON, headers=headers)

    async def _handle_sse_request(
        self, request_data: dict[str, Any], session_id: str | None, oauth_token: str | None = None
    ) -> StreamingResponse:
        """Handle SSE request for Inspector compatibility."""

        created_session_id = None
        method = request_data.get("method")

        # Create session ID for initialize requests
        if method == "initialize":
            client_info = request_data.get("params", {}).get("clientInfo", {})
            protocol_version = request_data.get("params", {}).get("protocolVersion", MCP_PROTOCOL_VERSION)
            created_session_id = self.protocol.session_manager.create_session(client_info, protocol_version)
            logger.info(f"Created SSE session: {created_session_id[:8]}...")

        return StreamingResponse(
            self._sse_stream_generator(request_data, created_session_id or session_id, method, oauth_token),
            media_type=CONTENT_TYPE_SSE,
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
                logger.debug(f"Streaming SSE response for {method}")

                # Send complete SSE event in proper format
                # CRITICAL: Must send all 3 parts as separate yields for Inspector compatibility
                yield SSE_EVENT_MESSAGE
                yield f"data: {orjson.dumps(response).decode()}\r\n"
                yield SSE_LINE_END

                logger.debug(f"SSE response sent for {method}")

            # For notifications, we don't send anything (which is correct)

        except Exception as e:
            logger.error(f"SSE stream error: {e}")

            # Send error event
            error_response = {
                JSONRPC_VERSION_KEY: JSONRPC_VERSION,
                "id": request_data.get("id"),
                "error": {"code": JsonRpcErrorCode.INTERNAL_ERROR, "message": str(e)},
            }
            yield SSE_EVENT_ERROR
            yield f"data: {orjson.dumps(error_response).decode()}\r\n"
            yield SSE_LINE_END

    def _sse_headers(self, session_id: str | None) -> dict[str, str]:
        """Build SSE response headers."""
        headers = {
            HEADER_CORS_ORIGIN: CORS_ALLOW_ALL,
            HEADER_CACHE_CONTROL: CACHE_NO_CACHE,
            HEADER_CONNECTION: CONNECTION_KEEP_ALIVE,
        }

        if session_id:
            headers[HEADER_MCP_SESSION_ID] = session_id

        return headers

    def _error_response(self, msg_id: Any, code: int, message: str) -> Response:
        """Create error response."""
        error_response = {
            JSONRPC_VERSION_KEY: JSONRPC_VERSION,
            "id": msg_id,
            "error": {"code": code, "message": message},
        }

        status_code = (
            HttpStatus.BAD_REQUEST
            if code in [JsonRpcErrorCode.PARSE_ERROR, JsonRpcErrorCode.INVALID_REQUEST]
            else HttpStatus.INTERNAL_SERVER_ERROR
        )

        return Response(
            orjson.dumps(error_response),
            status_code=status_code,
            media_type=CONTENT_TYPE_JSON,
            headers=HEADERS_CORS_ONLY,
        )
