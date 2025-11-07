#!/usr/bin/env python3
# src/chuk_mcp_server/proxy/transports/stdio_transport.py
"""
Stdio Proxy Transport - Wrapper for existing stdio proxy functionality
"""

import asyncio
import json
import logging
import subprocess
import uuid
from typing import Any

from .base import ProxyTransport

logger = logging.getLogger(__name__)


class StdioProxyTransport(ProxyTransport):
    """Stdio transport for connecting to local MCP server processes."""

    def __init__(self, server_name: str, config: dict[str, Any]):
        """
        Initialize stdio proxy transport.

        Config keys:
            - command: Command to run (required)
            - args: Command arguments (optional)
            - cwd: Working directory (optional)
            - env: Environment variables (optional)
        """
        super().__init__(server_name, config)

        self.command = config.get("command")
        if not self.command:
            raise ValueError(f"Stdio transport for '{server_name}' requires 'command' in config")

        self.args = config.get("args", [])
        self.cwd = config.get("cwd")
        self.env = config.get("env")
        self.process: subprocess.Popen[bytes] | None = None
        self.request_id = 0

    async def connect(self) -> bool:
        """Start the subprocess."""
        try:
            cmd = [self.command] + self.args
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.cwd,
                env=self.env,
            )

            # Give the process a moment to start
            await asyncio.sleep(0.1)

            # Check if process is still running
            if self.process.poll() is not None:
                stderr = self.process.stderr.read() if self.process.stderr else b""
                raise RuntimeError(f"Process exited immediately: {stderr.decode()}")

            logger.info(f"Stdio transport started process: {self.command}")
            return True

        except Exception as e:
            logger.error(f"Failed to start stdio transport: {e}")
            return False

    async def disconnect(self) -> None:
        """Stop the subprocess."""
        if self.process:
            try:
                # Try graceful termination
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    self.process.kill()
                    self.process.wait()
            except Exception as e:
                logger.error(f"Error stopping stdio process: {e}")
            finally:
                self.process = None
                self.session_id = None

            logger.info(f"Stdio transport stopped process: {self.command}")

    async def initialize(self) -> dict[str, Any]:
        """Initialize MCP session with backend server."""
        if not self.process or not self.process.stdin:
            raise RuntimeError("Stdio process not started")

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

        logger.debug(f"Stdio transport initialized session: {self.session_id}")
        return response

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the backend server via stdio."""
        response = await self.send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )
        return response

    async def list_tools(self) -> dict[str, Any]:
        """List available tools from backend server via stdio."""
        response = await self.send_request("tools/list")
        return response

    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a JSON-RPC request over stdio."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("Stdio process not available")

        self.request_id += 1

        # Build JSON-RPC request
        request_data = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
        }

        if params is not None:
            request_data["params"] = params

        try:
            # Send request
            request_json = json.dumps(request_data) + "\n"
            self.process.stdin.write(request_json.encode())
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("No response from stdio process")

            response_data = json.loads(response_line.decode())

            # Check for JSON-RPC error
            if "error" in response_data:
                error = response_data["error"]
                raise RuntimeError(f"MCP error: {error.get('message', 'Unknown error')}")

            return response_data.get("result", {})

        except Exception as e:
            logger.error(f"Error communicating with stdio process: {e}")
            raise
