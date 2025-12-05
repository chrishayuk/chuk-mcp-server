"""
Proxy Manager v2 - Using chuk-tool-processor StreamManager for MCP integration.

This version replaces custom transport classes with chuk-tool-processor's
production-grade MCP handling (timeouts, retries, circuit breakers, etc).
"""

import logging
from typing import Any

from chuk_tool_processor.mcp import MCPTool, StreamManager, register_mcp_tools

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Manages MCP servers using chuk-tool-processor StreamManager.

    Simpler and more reliable than custom transport implementation.
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

        self.stream_managers: dict[str, StreamManager] = {}
        self.registered_tools: dict[str, list[str]] = {}

        logger.info(f"ProxyManager initialized (enabled={self.enabled}, namespace={self.namespace})")

    async def start_servers(self) -> None:
        """Start all configured MCP servers and register their tools."""
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

        total_tools = sum(len(tools) for tools in self.registered_tools.values())
        logger.info(f"Proxy started with {len(self.stream_managers)} servers, {total_tools} tools")

    async def _start_server(self, name: str, config: dict[str, Any]) -> None:
        """Start a single MCP server using StreamManager."""
        server_type = config.get("type", "stdio")

        stream_manager: StreamManager | None = None

        try:
            if server_type == "stdio":
                # STDIO transport
                command = config.get("command")
                args = config.get("args", [])
                env = config.get("env")

                if not command:
                    raise ValueError(f"STDIO server '{name}' requires 'command' in config")

                stream_manager = await StreamManager.create_with_stdio(
                    servers=[
                        {
                            "name": name,
                            "command": command,
                            "args": args,
                            "env": env or {},
                        }
                    ],
                    server_names={0: name},
                    default_timeout=config.get("timeout", 30.0),
                )

            elif server_type == "http":
                # HTTP Streamable transport
                url = config.get("url")
                if not url:
                    raise ValueError(f"HTTP server '{name}' requires 'url' in config")

                stream_manager = await StreamManager.create_with_http_streamable(
                    servers=[
                        {
                            "url": url,
                            "headers": config.get("headers", {}),
                        }
                    ],
                    server_names={0: name},
                    default_timeout=config.get("timeout", 30.0),
                )

            elif server_type == "sse":
                # SSE transport
                url = config.get("url")
                if not url:
                    raise ValueError(f"SSE server '{name}' requires 'url' in config")

                stream_manager = await StreamManager.create_with_sse(
                    servers=[
                        {
                            "url": url,
                            "headers": config.get("headers", {}),
                        }
                    ],
                    server_names={0: name},
                    default_timeout=config.get("timeout", 30.0),
                )
            else:
                logger.warning(f"Unknown server type '{server_type}', skipping {name}")
                return

            # Store stream manager
            self.stream_managers[name] = stream_manager

            # Register tools using chuk-tool-processor's register_mcp_tools
            # This creates MCPTool wrappers with built-in resilience
            # Use the namespace directly (which comes from the prefix in config)
            namespace = self.namespace
            registered = await register_mcp_tools(
                stream_manager=stream_manager,
                namespace=namespace,
                default_timeout=config.get("timeout", 30.0),
                enable_resilience=True,
            )

            self.registered_tools[name] = registered

            # Also register with our protocol handler if provided
            if self.protocol_handler:
                await self._register_with_protocol_handler(namespace, stream_manager)

            logger.info(f"Started server '{name}' with {len(registered)} tools")

        except Exception as e:
            logger.error(f"Failed to start server '{name}': {e}")
            if stream_manager:
                await stream_manager.close()
            raise

    async def _register_with_protocol_handler(self, namespace: str, stream_manager: StreamManager) -> None:
        """Register tools with the protocol handler."""
        if not self.protocol_handler:
            return

        from .mcp_tool_wrapper import create_mcp_tool_handler

        # Get tools from stream manager
        tools = stream_manager.get_all_tools()

        for tool_def in tools:
            tool_name = tool_def.get("name")
            if not tool_name:
                continue

            # Create MCPTool wrapper
            mcp_tool = MCPTool(
                tool_name=tool_name,
                stream_manager=stream_manager,
                default_timeout=30.0,
                enable_resilience=True,
            )

            full_name = f"{namespace}.{tool_name}"

            # Create ToolHandler with proper signature from inputSchema
            tool_handler = create_mcp_tool_handler(
                mcp_tool=mcp_tool,
                tool_def=tool_def,
                full_name=full_name,
            )

            self.protocol_handler.register_tool(tool_handler)

    async def stop_servers(self) -> None:
        """Stop all running MCP servers."""
        logger.info(f"Stopping {len(self.stream_managers)} proxy servers...")

        for name, stream_manager in self.stream_managers.items():
            try:
                await stream_manager.close()
                logger.info(f"Stopped server: {name}")
            except Exception as e:
                logger.error(f"Error stopping server {name}: {e}")

        self.stream_managers.clear()
        self.registered_tools.clear()

        logger.info("All proxy servers stopped")

    def get_server_info(self) -> dict[str, Any]:
        """Get information about running servers."""
        return {
            "enabled": self.enabled,
            "namespace": self.namespace,
            "servers": list(self.stream_managers.keys()),
            "tools_count": sum(len(tools) for tools in self.registered_tools.values()),
            "tools_by_server": {name: len(tools) for name, tools in self.registered_tools.items()},
        }
