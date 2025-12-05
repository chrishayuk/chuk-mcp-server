#!/usr/bin/env python3
# src/chuk_mcp_server/proxy/transports/http_transport.py
"""
HTTP Proxy Transport - Connect to MCP servers over HTTP
"""

import logging
import uuid
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

from .base import ProxyTransport

logger = logging.getLogger(__name__)


class HttpProxyTransport(ProxyTransport):
    """HTTP transport for connecting to remote MCP servers."""

    def __init__(self, server_name: str, config: dict[str, Any]):
        """
        Initialize HTTP proxy transport.

        Config keys:
            - url: Backend HTTP URL (required)
            - timeout: Request timeout in seconds (default: 30)
            - headers: Additional headers to send
            - verify_ssl: Whether to verify SSL certificates (default: True)
        """
        super().__init__(server_name, config)

        if httpx is None:
            raise ImportError("httpx is required for HTTP proxy transport. Install it with: pip install httpx")

        self.url = config.get("url")
        if not self.url:
            raise ValueError(f"HTTP transport for '{server_name}' requires 'url' in config")

        self.timeout = config.get("timeout", 30.0)
        self.headers = config.get("headers", {})
        self.verify_ssl = config.get("verify_ssl", True)
        self.client: httpx.AsyncClient | None = None
        self.request_id = 0

    async def connect(self) -> bool:
        """Connect to the HTTP backend."""
        try:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                verify=self.verify_ssl,
            )
            logger.info(f"HTTP transport connected to {self.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect HTTP transport: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from the HTTP backend."""
        if self.client:
            await self.client.aclose()
            self.client = None
            self.session_id = None
            logger.info(f"HTTP transport disconnected from {self.url}")

    async def initialize(self) -> dict[str, Any]:
        """Initialize MCP session with backend server."""
        if not self.client:
            raise RuntimeError("HTTP client not connected")

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

        logger.info(f"HTTP transport initialized session: {self.session_id}")
        return response

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the backend server via HTTP."""
        response = await self.send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )
        return response

    async def list_tools(self) -> dict[str, Any]:
        """List available tools from backend server via HTTP."""
        response = await self.send_request("tools/list")
        return response

    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a JSON-RPC request over HTTP."""
        # Ensure we have a valid client (recreate if needed)
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                verify=self.verify_ssl,
            )

        self.request_id += 1

        # Build JSON-RPC request
        request_data = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
        }

        if params is not None:
            request_data["params"] = params

        # Add session ID header if we have one
        headers = self.headers.copy()
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        try:
            # Send HTTP POST request
            response = await self.client.post(
                self.url,
                json=request_data,
                headers=headers,
            )

            response.raise_for_status()

            # Parse JSON response
            result = response.json()

            # Check for JSON-RPC error
            if "error" in result:
                error = result["error"]
                raise RuntimeError(f"MCP error: {error.get('message', 'Unknown error')}")

            return result.get("result", {})

        except httpx.HTTPError as e:
            logger.error(f"HTTP request failed: {e}")
            raise RuntimeError(f"HTTP request failed: {e}") from e
        except Exception as e:
            logger.error(f"Error sending HTTP request: {e}")
            # On error, close and clear the client so it will be recreated next time
            if self.client:
                try:
                    await self.client.aclose()
                except:
                    pass
                self.client = None
            raise
