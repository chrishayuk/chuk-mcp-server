#!/usr/bin/env python3
# src/chuk_mcp_server/types/base.py
"""
Base Types - Direct chuk_mcp imports with no conversion layers

This module provides direct access to chuk_mcp types without unnecessary conversion layers,
ensuring maximum performance and compatibility with the underlying MCP protocol implementation.
"""

from enum import Enum

# ============================================================================
# Direct chuk_mcp imports - No Conversion Layer
# ============================================================================

# Use chuk_mcp types directly
from chuk_mcp.protocol.types import (
    # Server/Client info (use directly)
    ServerInfo,
    ClientInfo,
    
    # Capabilities (use directly)
    ServerCapabilities,
    ClientCapabilities,
    ToolsCapability,
    ResourcesCapability,
    PromptsCapability,
    LoggingCapability,
    
    # Content types (use directly)
    TextContent,
    ImageContent,
    AudioContent,
    EmbeddedResource,
    Content,
    Annotations,
    create_text_content,
    create_image_content,
    create_audio_content,
    create_embedded_resource,
    content_to_dict,
    parse_content,
    
    # Error handling
    MCPError,
    ProtocolError,
    ValidationError,
    
    # Versioning
    CURRENT_VERSION,
    SUPPORTED_VERSIONS,
    ProtocolVersion,
)

# Import chuk_mcp's Resource, Tool, and ToolInputSchema types separately to avoid naming conflicts
from chuk_mcp.protocol.messages.resources.resource import Resource as MCPResource
from chuk_mcp.protocol.messages.tools.tool import Tool as MCPTool
from chuk_mcp.protocol.messages.tools.tool_input_schema import ToolInputSchema as MCPToolInputSchema

# ============================================================================
# Framework-Specific Enums
# ============================================================================

class TransportType(Enum):
    """Supported transport types for ChukMCPServer."""
    HTTP = "http"
    STDIO = "stdio"
    SSE = "sse"

# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Framework enums
    "TransportType",
    
    # Direct chuk_mcp types
    "ServerInfo",
    "ClientInfo",
    "ServerCapabilities", 
    "ClientCapabilities",
    "ToolsCapability",
    "ResourcesCapability",
    "PromptsCapability",
    "LoggingCapability",
    "MCPResource",
    "MCPTool",
    "MCPToolInputSchema",
    
    # Content types
    "TextContent",
    "ImageContent", 
    "AudioContent",
    "EmbeddedResource",
    "Content",
    "Annotations",
    
    # Content helpers
    "create_text_content",
    "create_image_content",
    "create_audio_content", 
    "create_embedded_resource",
    "content_to_dict",
    "parse_content",
    
    # Error types
    "MCPError",
    "ProtocolError",
    "ValidationError",
    
    # Versioning
    "CURRENT_VERSION",
    "SUPPORTED_VERSIONS", 
    "ProtocolVersion",
]