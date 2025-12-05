"""
Proxy module for hosting and forwarding to multiple MCP servers.

This module enables ChukMCPServer to act as a proxy/gateway to multiple
backend MCP servers (stdio, HTTP, SSE), exposing their tools under a
unified namespace.
"""

from .manager import ProxyManager

__all__ = ["ProxyManager"]
