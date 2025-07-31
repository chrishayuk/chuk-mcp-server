#!/usr/bin/env python3
# src/chuk_mcp_server/types/__init__.py
"""
Types - Modular type system with clean public API

This package provides a modular type system built on chuk_mcp with performance optimizations.
All components are organized into focused modules while maintaining a clean public API.
"""

# Base types and direct chuk_mcp imports
from .base import (
    # Framework-specific types
    TransportType,
    
    # Direct chuk_mcp types (no conversion needed)
    ServerInfo,
    ClientInfo,
    ServerCapabilities,
    ClientCapabilities,
    ToolsCapability,
    ResourcesCapability,
    PromptsCapability,
    LoggingCapability,
    MCPResource,
    
    # Content types (direct from chuk_mcp)
    TextContent,
    ImageContent,
    AudioContent,
    EmbeddedResource,
    Content,
    Annotations,
    
    # Content helpers (direct from chuk_mcp)
    create_text_content,
    create_image_content,
    create_audio_content,
    create_embedded_resource,
    content_to_dict,
    parse_content,
    
    # Error types (direct from chuk_mcp)
    MCPError,
    ProtocolError,
    ValidationError,
    
    # Versioning (direct from chuk_mcp)
    CURRENT_VERSION,
    SUPPORTED_VERSIONS,
    ProtocolVersion,
)

# Parameter types and schema generation
from .parameters import ToolParameter

# Tool and resource handlers
from .tools import ToolHandler
from .resources import ResourceHandler

# Capabilities helpers
from .capabilities import create_server_capabilities

# Content formatting
from .content import format_content

# Custom errors
from .errors import (
    ParameterValidationError,
    ToolExecutionError,
)

# Serialization utilities
from .serialization import (
    serialize_tools_list,
    serialize_resources_list,
    serialize_tools_list_from_bytes,
)

# ============================================================================
# Clean Public API - Everything available from single import
# ============================================================================

__all__ = [
    # Framework-specific types
    "TransportType",
    "ToolParameter",
    "ToolHandler",
    "ResourceHandler",
    
    # Framework helpers
    "create_server_capabilities",
    "format_content",
    
    # Serialization utilities
    "serialize_tools_list",
    "serialize_resources_list",
    "serialize_tools_list_from_bytes",
    
    # Exception types
    "ParameterValidationError",
    "ToolExecutionError",
    
    # Direct chuk_mcp types (no conversion needed)
    "ServerInfo",
    "ClientInfo",
    "ServerCapabilities",
    "ClientCapabilities",
    "ToolsCapability",
    "ResourcesCapability",
    "PromptsCapability",
    "LoggingCapability",
    "MCPResource",  # chuk_mcp's Resource type
    
    # Content types (direct from chuk_mcp)
    "TextContent",
    "ImageContent",
    "AudioContent",
    "EmbeddedResource",
    "Content",
    "Annotations",
    
    # Content helpers (direct from chuk_mcp)
    "create_text_content",
    "create_image_content",
    "create_audio_content",
    "create_embedded_resource",
    "content_to_dict",
    "parse_content",
    
    # Error types (direct from chuk_mcp)
    "MCPError",
    "ProtocolError",
    "ValidationError",
    
    # Versioning (direct from chuk_mcp)
    "CURRENT_VERSION",
    "SUPPORTED_VERSIONS",
    "ProtocolVersion",
]