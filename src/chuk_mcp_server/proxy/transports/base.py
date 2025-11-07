#!/usr/bin/env python3
# src/chuk_mcp_server/proxy/transports/base.py
"""
Base Proxy Transport - Abstract base class for all proxy transports
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class ProxyTransport(ABC):
    """Abstract base class for proxy transports."""

    def __init__(self, server_name: str, config: dict[str, Any]):
        """
        Initialize the proxy transport.

        Args:
            server_name: Name of the backend server
            config: Configuration for this transport
        """
        self.server_name = server_name
        self.config = config
        self.session_id: str | None = None

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the backend server.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the backend server."""
        pass

    @abstractmethod
    async def initialize(self) -> dict[str, Any]:
        """
        Initialize MCP session with backend server.

        Returns:
            Initialization response from backend
        """
        pass

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Call a tool on the backend server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool call response
        """
        pass

    @abstractmethod
    async def list_tools(self) -> dict[str, Any]:
        """
        List available tools from backend server.

        Returns:
            List of tools response
        """
        pass

    async def send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Send a JSON-RPC request to the backend.

        Args:
            method: MCP method name
            params: Method parameters

        Returns:
            Response from backend
        """
        # Default implementation - subclasses can override
        raise NotImplementedError(f"send_request not implemented for {self.__class__.__name__}")

    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self.session_id is not None
