#!/usr/bin/env python3
# src/chuk_mcp_server/types/capabilities.py
"""
Capabilities - Server capability creation and management

This module provides helpers for creating and managing MCP server capabilities
with clean APIs and backward compatibility.
"""

from typing import Dict, Any, Optional
from .base import (
    ServerCapabilities,
    ToolsCapability, 
    ResourcesCapability,
    PromptsCapability,
    LoggingCapability
)

def create_server_capabilities(
    tools: bool = True,
    resources: bool = True,
    prompts: bool = False,
    logging: bool = False,
    experimental: Optional[Dict[str, Any]] = None
) -> ServerCapabilities:
    """Create server capabilities using chuk_mcp types directly."""
    capabilities = {}
    
    if tools:
        capabilities["tools"] = ToolsCapability(listChanged=True)
    if resources:
        capabilities["resources"] = ResourcesCapability(
            listChanged=True, 
            subscribe=False
        )
    if prompts:
        capabilities["prompts"] = PromptsCapability(listChanged=True)
    if logging:
        capabilities["logging"] = LoggingCapability()
    if experimental:
        capabilities["experimental"] = experimental
    
    return ServerCapabilities(**capabilities)

__all__ = ["create_server_capabilities"]