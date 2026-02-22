#!/usr/bin/env python3
# src/chuk_mcp_server/protocol/__init__.py
"""
MCP protocol package.

Re-exports MCPProtocolHandler and SessionManager for backward compatibility.
All existing imports from ``chuk_mcp_server.protocol`` continue to work.
"""

from .handler import MCPProtocolHandler
from .session_manager import SessionManager

__all__ = [
    "MCPProtocolHandler",
    "SessionManager",
]
