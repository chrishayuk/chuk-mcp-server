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
    # Build only enabled capabilities
    kwargs = {}
    
    if tools:
        kwargs["tools"] = ToolsCapability(listChanged=True)
    
    if resources:
        kwargs["resources"] = ResourcesCapability(
            listChanged=True, 
            subscribe=False
        )
    
    if prompts:
        kwargs["prompts"] = PromptsCapability(listChanged=True)
    
    if logging:
        kwargs["logging"] = LoggingCapability()
    
    # Handle experimental features
    if experimental is not None:
        if experimental == {}:
            kwargs["experimental"] = experimental
        else:
            # Try to include experimental features
            try:
                kwargs["experimental"] = experimental
                caps = ServerCapabilities(**kwargs)
            except Exception:
                # Create without experimental first, then set it manually
                caps = ServerCapabilities(**{k: v for k, v in kwargs.items() if k != "experimental"})
                object.__setattr__(caps, 'experimental', experimental)
                return caps
    
    # Create the capabilities object
    caps = ServerCapabilities(**kwargs)
    
    # Override model_dump to filter out unwanted fields
    original_model_dump = caps.model_dump
    
    def filtered_model_dump(**dump_kwargs):
        result = original_model_dump(**dump_kwargs)
        # Remove None fields and unwanted default fields
        filtered = {}
        for key, value in result.items():
            # Only include fields we explicitly set
            if key in kwargs:
                filtered[key] = value
            elif key == "experimental" and experimental is not None:
                filtered[key] = value
        return filtered
    
    caps.model_dump = filtered_model_dump
    return caps

__all__ = ["create_server_capabilities"]