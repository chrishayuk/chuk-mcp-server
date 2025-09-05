#!/usr/bin/env python3
# src/chuk_mcp_server/types/serialization.py
"""
Serialization - orjson optimization utilities for maximum performance

This module provides high-performance serialization utilities using orjson
for tools list, resources list, and other MCP protocol operations.
"""

# Import type annotations only
from typing import TYPE_CHECKING, Any

import orjson

if TYPE_CHECKING:
    from .resources import ResourceHandler
    from .tools import ToolHandler


def serialize_tools_list(tools: list["ToolHandler"]) -> bytes:
    """🚀 Ultra-fast tools list serialization with orjson."""
    tools_data = [tool.to_mcp_format() for tool in tools]
    return orjson.dumps({"tools": tools_data})


def serialize_resources_list(resources: list["ResourceHandler"]) -> bytes:
    """🚀 Ultra-fast resources list serialization with orjson."""
    resources_data = [resource.to_mcp_format() for resource in resources]
    return orjson.dumps({"resources": resources_data})


def serialize_tools_list_from_bytes(tools: list["ToolHandler"]) -> bytes:
    """🚀 Maximum performance tools list using pre-serialized bytes."""
    # Combine pre-serialized tool bytes directly
    tool_bytes = [tool.to_mcp_bytes() for tool in tools]

    # Build the final structure
    tools_list = []
    for tool_byte in tool_bytes:
        tools_list.append(orjson.loads(tool_byte))

    return orjson.dumps({"tools": tools_list})


def serialize_mcp_response(response_data: dict[str, Any]) -> bytes:
    """Serialize MCP response with orjson for maximum performance."""
    return orjson.dumps(response_data)


def deserialize_mcp_request(request_bytes: bytes) -> dict[str, Any]:
    """Deserialize MCP request with orjson for maximum performance."""
    return orjson.loads(request_bytes)  # type: ignore[no-any-return]


__all__ = [
    "serialize_tools_list",
    "serialize_resources_list",
    "serialize_tools_list_from_bytes",
    "serialize_mcp_response",
    "deserialize_mcp_request",
]
