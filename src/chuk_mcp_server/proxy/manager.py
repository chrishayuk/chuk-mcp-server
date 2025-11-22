"""
Proxy Manager for hosting and managing multiple MCP servers.

This module provides the ProxyManager class which can connect to multiple
MCP servers (stdio, HTTP, SSE) and expose their tools under a unified namespace.
"""

import json
import logging
import subprocess
from typing import Any

from ..types import ToolHandler
from .tool_wrapper import create_proxy_tool

logger = logging.getLogger(__name__)


class StdioServerClient:
    """Client for communicating with a stdio MCP server."""

    def __init__(self, server_name: str, process: subprocess.Popen[bytes]):
        self.server_name = server_name
        self.process = process
        self.request_id = 0

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any], server_name: str | None = None
    ) -> dict[str, Any]:
        """Call a tool on the stdio server."""
        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        # Write request to stdin
        if self.process.stdin is None:
            raise RuntimeError("Process stdin is not available")

        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        self.process.stdin.flush()

        # Read response from stdout
        if self.process.stdout is None:
            raise RuntimeError("Process stdout is not available")

        response_line = self.process.stdout.readline().decode().strip()
        response = json.loads(response_line)

        # Handle JSON-RPC error
        if "error" in response:
            return {
                "isError": True,
                "error": response["error"].get("message", "Unknown error"),
            }

        # Return result
        return {"isError": False, "content": response.get("result", {})}

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the stdio server."""
        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/list",
            "params": {},
        }

        # Write request
        if self.process.stdin is None:
            raise RuntimeError("Process stdin is not available")

        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        self.process.stdin.flush()

        # Read response
        if self.process.stdout is None:
            raise RuntimeError("Process stdout is not available")

        response_line = self.process.stdout.readline().decode().strip()
        response = json.loads(response_line)

        if "error" in response:
            logger.error(f"Failed to list tools from {self.server_name}: {response['error']}")
            return []

        result = response.get("result", {})
        tools: list[dict[str, Any]] = result.get("tools", [])
        return tools

    async def close(self) -> None:
        """Close the stdio server connection."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


class ProxyManager:
    """
    Manages multiple MCP servers and exposes their tools under a unified namespace.

    Configuration example:
        {
            "proxy": {
                "enabled": true,
                "namespace": "proxy"
            },
            "servers": {
                "time": {
                    "type": "stdio",
                    "command": "uvx",
                    "args": ["mcp-server-time"],
                    "cwd": "/optional/working/dir"
                },
                "weather": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "weather_server"]
                }
            }
        }
    """

    def __init__(self, config: dict[str, Any], protocol_handler: Any = None):
        """
        Initialize the proxy manager.

        Args:
            config: Configuration dictionary with proxy and servers settings
            protocol_handler: Optional protocol handler to register proxied tools
        """
        proxy_config = config.get("proxy", {})
        self.enabled = proxy_config.get("enabled", False)
        self.namespace = proxy_config.get("namespace", "proxy")

        self.servers_config = config.get("servers", {})
        self.protocol_handler = protocol_handler

        self.running_servers: dict[str, StdioServerClient] = {}
        self.proxied_tools: dict[str, ToolHandler] = {}

        logger.info(f"ProxyManager initialized (enabled={self.enabled}, namespace={self.namespace})")

    async def start_servers(self) -> None:
        """Start all configured MCP servers."""
        if not self.enabled:
            logger.info("Proxy mode disabled, skipping server startup")
            return

        if not self.servers_config:
            logger.warning("No servers configured for proxy mode")
            return

        logger.info(f"Starting {len(self.servers_config)} proxy servers...")

        for server_name, server_config in self.servers_config.items():
            try:
                await self._start_server(server_name, server_config)
            except Exception as e:
                logger.error(f"Failed to start server {server_name}: {e}")

        # Discover and wrap tools from all servers
        await self._discover_and_wrap_tools()

        logger.info(f"Proxy started with {len(self.running_servers)} servers, {len(self.proxied_tools)} tools")

    async def _start_server(self, name: str, config: dict[str, Any]) -> None:
        """Start a single MCP server."""
        server_type = config.get("type", "stdio")

        if server_type != "stdio":
            logger.warning(f"Server type {server_type} not yet supported, skipping {name}")
            return

        # Start stdio server
        command = config.get("command", "python")
        args = config.get("args", [])
        cwd = config.get("cwd")

        full_command = [command] + args

        logger.debug(f"Starting stdio server {name}: {' '.join(full_command)}")

        # Start subprocess
        process = subprocess.Popen(
            full_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            bufsize=0,
        )

        # Create client
        client = StdioServerClient(name, process)

        # Send initialize request
        await self._initialize_server(client)

        self.running_servers[name] = client
        logger.info(f"Started server: {name}")

    async def _initialize_server(self, client: StdioServerClient) -> None:
        """Send MCP initialize request to a server."""
        client.request_id += 1

        init_request = {
            "jsonrpc": "2.0",
            "id": client.request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "chuk-mcp-server-proxy", "version": "0.5.2"},
            },
        }

        # Send request
        if client.process.stdin is None:
            raise RuntimeError("Process stdin is not available")

        request_json = json.dumps(init_request) + "\n"
        client.process.stdin.write(request_json.encode())
        client.process.stdin.flush()

        # Read response
        if client.process.stdout is None:
            raise RuntimeError("Process stdout is not available")

        response_line = client.process.stdout.readline().decode().strip()
        response = json.loads(response_line)

        if "error" in response:
            raise RuntimeError(f"Failed to initialize server: {response['error']}")

        logger.debug(f"Initialized server: {client.server_name}")

    async def _discover_and_wrap_tools(self) -> None:
        """Discover tools from all servers and create proxy wrappers."""
        for server_name, client in self.running_servers.items():
            try:
                # List tools from server
                tools = await client.list_tools()

                logger.debug(f"Discovered {len(tools)} tools from {server_name}")

                # Create proxy wrapper for each tool
                for tool_meta in tools:
                    tool_name = tool_meta.get("name")
                    if not tool_name:
                        continue

                    # Create namespaced name
                    namespace = f"{self.namespace}.{server_name}"
                    full_name = f"{namespace}.{tool_name}"

                    # Create proxy tool
                    tool_handler = await create_proxy_tool(namespace, tool_name, client, tool_meta)

                    # Register with protocol handler if available
                    if self.protocol_handler:
                        self.protocol_handler.register_tool(tool_handler)

                    self.proxied_tools[full_name] = tool_handler

                    logger.debug(f"Registered proxy tool: {full_name}")

            except Exception as e:
                logger.error(f"Failed to discover tools from {server_name}: {e}")

    async def stop_servers(self) -> None:
        """Stop all running MCP servers."""
        logger.info(f"Stopping {len(self.running_servers)} proxy servers...")

        for server_name, client in self.running_servers.items():
            try:
                await client.close()
                logger.info(f"Stopped server: {server_name}")
            except Exception as e:
                logger.error(f"Error stopping server {server_name}: {e}")

        self.running_servers.clear()
        self.proxied_tools.clear()

    async def call_tool(self, name: str, **kwargs: Any) -> Any:
        """
        Call a proxied tool by name.

        Args:
            name: Full tool name (e.g., "proxy.time.get_current_time")
            **kwargs: Tool arguments

        Returns:
            Tool result
        """
        # Extract server and tool name
        if not name.startswith(f"{self.namespace}."):
            raise ValueError(f"Tool name must start with {self.namespace}.")

        parts = name[len(self.namespace) + 1 :].split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid tool name format: {name}")

        server_name, tool_name = parts

        if server_name not in self.running_servers:
            raise ValueError(f"Server not found: {server_name}")

        client = self.running_servers[server_name]
        result = await client.call_tool(tool_name, kwargs, server_name)

        if result.get("isError"):
            raise RuntimeError(result.get("error", "Unknown error"))

        return result.get("content")

    def get_all_tools(self) -> dict[str, ToolHandler]:
        """Get all proxied tools."""
        return dict(self.proxied_tools)

    def get_stats(self) -> dict[str, Any]:
        """Get proxy statistics."""
        return {
            "enabled": self.enabled,
            "namespace": self.namespace,
            "servers": len(self.running_servers),
            "tools": len(self.proxied_tools),
            "server_names": list(self.running_servers.keys()),
        }
