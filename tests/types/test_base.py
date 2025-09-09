#!/usr/bin/env python3
# tests/types/test_base.py
"""
Unit tests for chuk_mcp_server.types.base module

Tests direct chuk_mcp imports and framework-specific enums.
"""

from enum import Enum

import pytest


def test_transport_type_enum():
    """Test TransportType enum values and behavior."""
    from chuk_mcp_server.types.base import TransportType

    # Test enum values
    assert TransportType.HTTP.value == "http"
    assert TransportType.STDIO.value == "stdio"
    assert TransportType.SSE.value == "sse"

    # Test enum membership
    assert TransportType.HTTP in TransportType
    assert TransportType.STDIO in TransportType
    assert TransportType.SSE in TransportType

    # Test enum count
    assert len(TransportType) == 3

    # Test enum inheritance
    assert issubclass(TransportType, Enum)


def test_chuk_mcp_imports():
    """Test that all required chuk_mcp types are properly imported."""
    from chuk_mcp_server.types.base import (
        ClientCapabilities,
        ClientInfo,
        LoggingCapability,
        MCPResource,
        MCPTool,
        MCPToolInputSchema,
        PromptsCapability,
        ResourcesCapability,
        ServerCapabilities,
        ServerInfo,
        ToolsCapability,
    )

    # Test that imports are successful (no ImportError)
    assert ServerInfo is not None
    assert ClientInfo is not None
    assert ServerCapabilities is not None
    assert ClientCapabilities is not None
    assert ToolsCapability is not None
    assert ResourcesCapability is not None
    assert PromptsCapability is not None
    assert LoggingCapability is not None
    assert MCPResource is not None
    assert MCPTool is not None
    assert MCPToolInputSchema is not None


def test_content_type_imports():
    """Test that content type imports are working."""
    from chuk_mcp_server.types.base import (
        Annotations,
        AudioContent,
        Content,
        EmbeddedResource,
        ImageContent,
        TextContent,
    )

    # Test content type imports
    assert TextContent is not None
    assert ImageContent is not None
    assert AudioContent is not None
    assert EmbeddedResource is not None
    assert Content is not None
    assert Annotations is not None


def test_content_helper_imports():
    """Test that content helper functions are imported."""
    from chuk_mcp_server.types.base import (
        content_to_dict,
        create_audio_content,
        create_embedded_resource,
        create_image_content,
        create_text_content,
        parse_content,
    )

    # Test helper function imports
    assert callable(create_text_content)
    assert callable(create_image_content)
    assert callable(create_audio_content)
    assert callable(create_embedded_resource)
    assert callable(content_to_dict)
    assert callable(parse_content)


def test_error_type_imports():
    """Test that error types are properly imported."""
    from chuk_mcp_server.types.base import MCPError, ProtocolError, ValidationError

    # Test error type imports
    assert MCPError is not None
    assert ProtocolError is not None
    assert ValidationError is not None

    # Test that they are exception classes
    assert issubclass(MCPError, Exception)
    assert issubclass(ProtocolError, Exception)
    assert issubclass(ValidationError, Exception)


def test_versioning_imports():
    """Test that versioning constants are imported."""
    from chuk_mcp_server.types.base import CURRENT_VERSION, SUPPORTED_VERSIONS, ProtocolVersion

    # Test versioning imports
    assert CURRENT_VERSION is not None
    assert SUPPORTED_VERSIONS is not None
    assert ProtocolVersion is not None

    # Test version format
    assert isinstance(CURRENT_VERSION, str)
    assert isinstance(SUPPORTED_VERSIONS, list | tuple)


def test_server_info_creation():
    """Test ServerInfo object creation."""
    from chuk_mcp_server.types.base import ServerInfo

    # Test basic creation
    server_info = ServerInfo(name="Test Server", version="1.0.0")

    assert server_info.name == "Test Server"
    assert server_info.version == "1.0.0"

    # Test with optional title
    server_info_with_title = ServerInfo(name="Test Server", version="1.0.0", title="Test Server Title")

    assert server_info_with_title.title == "Test Server Title"


def test_capabilities_creation():
    """Test capability objects can be created."""
    from chuk_mcp_server.types.base import LoggingCapability, PromptsCapability, ResourcesCapability, ToolsCapability

    # Test tools capability
    tools_cap = ToolsCapability(listChanged=True)
    assert tools_cap.listChanged is True

    # Test resources capability
    resources_cap = ResourcesCapability(listChanged=True, subscribe=False)
    assert resources_cap.listChanged is True
    assert resources_cap.subscribe is False

    # Test prompts capability
    prompts_cap = PromptsCapability(listChanged=True)
    assert prompts_cap.listChanged is True

    # Test logging capability
    logging_cap = LoggingCapability()
    assert logging_cap is not None


def test_content_creation():
    """Test content creation functions work."""
    from chuk_mcp_server.types.base import content_to_dict, create_text_content

    # Test text content creation
    text_content = create_text_content("Hello, world!")
    assert text_content is not None

    # Test content to dict conversion
    content_dict = content_to_dict(text_content)
    assert isinstance(content_dict, dict)
    assert "type" in content_dict
    assert content_dict["type"] == "text"


def test_mcp_resource_creation():
    """Test MCPResource object creation."""
    from chuk_mcp_server.types.base import MCPResource

    resource = MCPResource(
        uri="test://resource", name="Test Resource", description="A test resource", mimeType="text/plain"
    )

    assert resource.uri == "test://resource"
    assert resource.name == "Test Resource"
    assert resource.description == "A test resource"
    assert resource.mimeType == "text/plain"


def test_mcp_tool_creation():
    """Test MCPTool object creation."""
    from chuk_mcp_server.types.base import MCPTool

    tool = MCPTool(
        name="test_tool",
        description="A test tool",
        inputSchema={"type": "object", "properties": {"param1": {"type": "string"}}},
    )

    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert tool.inputSchema["type"] == "object"


def test_module_exports():
    """Test that __all__ exports are complete and correct."""
    from chuk_mcp_server.types import base

    # Test that __all__ exists
    assert hasattr(base, "__all__")
    assert isinstance(base.__all__, list)

    # Test key exports are included
    expected_exports = [
        "TransportType",
        "ServerInfo",
        "ClientInfo",
        "ServerCapabilities",
        "MCPResource",
        "MCPTool",
        "TextContent",
        "MCPError",
        "CURRENT_VERSION",
    ]

    for export in expected_exports:
        assert export in base.__all__, f"Missing export: {export}"
        assert hasattr(base, export), f"Export {export} not available"


def test_no_unexpected_dependencies():
    """Test that base module has minimal dependencies."""

    from chuk_mcp_server.types import base

    # Get module's imported modules
    module_dict = vars(base)

    # Should not import any internal chuk_mcp_server modules except chuk_mcp
    for _name, obj in module_dict.items():
        if hasattr(obj, "__module__"):
            module_name = obj.__module__
            if module_name and "chuk_mcp_server" in module_name:
                # Only chuk_mcp_server.types.base itself should be allowed
                assert module_name == "chuk_mcp_server.types.base", f"Unexpected internal dependency: {module_name}"


if __name__ == "__main__":
    pytest.main([__file__])
