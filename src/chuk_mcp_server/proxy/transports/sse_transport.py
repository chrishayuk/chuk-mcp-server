#!/usr/bin/env python3
# src/chuk_mcp_server/proxy/transports/sse_transport.py
"""
SSE Proxy Transport - Connect to MCP servers over Server-Sent Events
"""

import asyncio
import logging
import uuid
from typing import Any

try:
    import httpx
    import httpx_sse
except ImportError:
    httpx = None  # type: ignore
    httpx_sse = None  # type: ignore

from .base import ProxyTransport

logger = logging.getLogger(__name__)


class SseProxyTransport(ProxyTransport):
    """SSE (Server-Sent Events) transport for connecting to remote MCP servers."""

    def __init__(self, server_name: str, config: dict[str, Any]):
        """
        Initialize SSE proxy transport.

        Config keys:
            - url: Backend SSE URL (required)
            - sse_path: Path for SSE endpoint (default: "/sse")
            - message_path: Path for posting messages (default: "/message")
            - timeout: Request timeout in seconds (default: 30)
            - headers: Additional headers to send
        """
        super().__init__(server_name, config)

        if httpx is None or httpx_sse is None:
            raise ImportError(
                "httpx and httpx-sse are required for SSE proxy transport. "
                "Install them with: pip install httpx httpx-sse"
            )

        self.base_url = config.get("url")
        if not self.base_url:
            raise ValueError(f"SSE transport for '{server_name}' requires 'url' in config")

        self.sse_path = config.get("sse_path", "/sse")
        self.message_path = config.get("message_path", "/message")
        self.timeout = config.get("timeout", 30.0)
        self.headers = config.get("headers", {})

        self.client: httpx.AsyncClient | None = None
        self.sse_connection = None
        self.request_id = 0
        self.pending_responses: dict[int, asyncio.Future] = {}

    async def connect(self) -> bool:
        """Connect to the SSE backend."""
        try:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
            )

            # Start SSE connection
            sse_url = f"{self.base_url}{self.sse_path}"
            self.sse_connection = self.client.stream("GET", sse_url)

            logger.info(f"SSE transport connected to {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect SSE transport: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from the SSE backend."""
        if self.sse_connection:
            await self.sse_connection.aclose()
            self.sse_connection = None

        if self.client:
            await self.client.aclose()
            self.client = None

        self.session_id = None
        logger.info(f"SSE transport disconnected from {self.base_url}")

    async def initialize(self) -> dict[str, Any]:
        """Initialize MCP session with backend server."""
        if not self.client:
            raise RuntimeError("SSE client not connected")

        # Generate session ID
        self.session_id = str(uuid.uuid4())

        # Send initialize request
        response = await self.send_request(
            "initialize",
            {
                "clientInfo": {
                    "name": "chuk-mcp-server-proxy",
                    "version": "1.0.0",
                },
                "protocolVersion": "2024-11-05",
            },
        )

        logger.info(f"SSE transport initialized session: {self.session_id}")
        return response

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the backend server via SSE."""
        response = await self.send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )
        return response

    async def list_tools(self) -> dict[str, Any]:
        """List available tools from backend server via SSE."""
        response = await self.send_request("tools/list")
        return response

    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a JSON-RPC request via POST, receive response via SSE."""
        if not self.client:
            raise RuntimeError("SSE client not connected")

        self.request_id += 1
        current_request_id = self.request_id

        # Build JSON-RPC request
        request_data = {
            "jsonrpc": "2.0",
            "id": current_request_id,
            "method": method,
        }

        if params is not None:
            request_data["params"] = params

        # Create future for response
        response_future: asyncio.Future = asyncio.Future()
        self.pending_responses[current_request_id] = response_future

        try:
            # Send HTTP POST request to message endpoint
            message_url = f"{self.base_url}{self.message_path}"
            headers = self.headers.copy()
            if self.session_id:
                headers["Mcp-Session-Id"] = self.session_id

            await self.client.post(
                message_url,
                json=request_data,
                headers=headers,
            )

            # Wait for response from SSE stream (with timeout)
            result = await asyncio.wait_for(response_future, timeout=self.timeout)
            return result

        except TimeoutError:
            logger.error(f"SSE request timeout for method: {method}")
            self.pending_responses.pop(current_request_id, None)
            raise RuntimeError(f"SSE request timeout: {method}")
        except Exception as e:
            logger.error(f"Error sending SSE request: {e}")
            self.pending_responses.pop(current_request_id, None)
            raise

    async def _process_sse_events(self):
        """Process incoming SSE events (background task)."""
        # This would need to be run as a background task
        # to continuously read from the SSE stream and match
        # responses to pending requests
        if not self.sse_connection:
            return

        try:
            async with self.sse_connection as response:
                async for sse_event in httpx_sse.aconnect_sse(response):
                    # Parse SSE event and match to pending request
                    # event.data contains the JSON response
                    # event.id might contain the request ID
                    logger.debug(f"SSE event received: {sse_event.event}")
                    # TODO: Implement response matching
        except Exception as e:
            logger.error(f"Error processing SSE events: {e}")
