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

class _FilteredServerCapabilities(ServerCapabilities):
    """ServerCapabilities subclass with filtered model_dump method"""
    
    def __init__(self, *args, _filter_kwargs=None, _experimental=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._filter_kwargs = _filter_kwargs or {}
        self._experimental = _experimental
    
    def model_dump(self, **dump_kwargs):
        """Filter out unwanted fields from model_dump"""
        result = super().model_dump(**dump_kwargs)
        # Remove None fields and unwanted default fields
        filtered = {}
        for key, value in result.items():
            # Only include fields we explicitly set
            if key in self._filter_kwargs:
                filtered[key] = value
            elif key == "experimental" and self._experimental is not None:
                filtered[key] = value
        return filtered


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
                caps = _FilteredServerCapabilities(
                    _filter_kwargs=kwargs, 
                    _experimental=experimental,
                    **kwargs
                )
            except Exception:
                # Create without experimental first, then set it manually
                caps = _FilteredServerCapabilities(
                    _filter_kwargs={k: v for k, v in kwargs.items() if k != "experimental"},
                    _experimental=experimental,
                    **{k: v for k, v in kwargs.items() if k != "experimental"}
                )
                object.__setattr__(caps, 'experimental', experimental)
                return caps
    
    # Create the capabilities object with our subclass
    caps = _FilteredServerCapabilities(
        _filter_kwargs=kwargs,
        _experimental=experimental,
        **kwargs
    )
    
    return caps

__all__ = ["create_server_capabilities"]