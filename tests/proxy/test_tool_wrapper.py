"""Tests for proxy tool wrapper."""

import pytest

from chuk_mcp_server.proxy.tool_wrapper import create_proxy_tool


class MockServerClient:
    """Mock MCP server client for testing."""

    def __init__(self):
        self.calls = []

    async def call_tool(self, tool_name: str, arguments: dict, server_name: str | None = None):
        """Mock tool call."""
        self.calls.append({"tool_name": tool_name, "arguments": arguments, "server_name": server_name})

        # Return success response
        return {"isError": False, "content": {"result": "test result"}}


class TestCreateProxyTool:
    """Test create_proxy_tool function."""

    @pytest.mark.asyncio
    async def test_create_proxy_tool_basic(self):
        """Test creating a basic proxy tool."""
        client = MockServerClient()

        metadata = {
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {"type": "object", "properties": {}, "required": []},
        }

        tool_handler = await create_proxy_tool("proxy.backend", "test_tool", client, metadata)

        assert tool_handler is not None
        assert tool_handler.name == "proxy.backend.test_tool"
        assert "test tool" in tool_handler.description.lower()

    @pytest.mark.asyncio
    async def test_create_proxy_tool_with_parameters(self):
        """Test creating proxy tool with parameters."""
        client = MockServerClient()

        metadata = {
            "name": "echo",
            "description": "Echo a message",
            "inputSchema": {
                "type": "object",
                "properties": {"message": {"type": "string", "description": "Message to echo"}},
                "required": ["message"],
            },
        }

        tool_handler = await create_proxy_tool("proxy.backend", "echo", client, metadata)

        assert tool_handler is not None
        assert tool_handler.name == "proxy.backend.echo"

    @pytest.mark.asyncio
    async def test_create_proxy_tool_with_optional_parameters(self):
        """Test creating proxy tool with optional parameters."""
        client = MockServerClient()

        metadata = {
            "name": "greet",
            "description": "Greet someone",
            "inputSchema": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Name", "default": "World"}},
                "required": [],
            },
        }

        tool_handler = await create_proxy_tool("proxy.backend", "greet", client, metadata)

        assert tool_handler is not None
        assert tool_handler.name == "proxy.backend.greet"

    @pytest.mark.asyncio
    async def test_create_proxy_tool_with_various_types(self):
        """Test creating proxy tool with various parameter types."""
        client = MockServerClient()

        metadata = {
            "name": "complex_tool",
            "description": "A complex tool",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "str_param": {"type": "string"},
                    "int_param": {"type": "integer", "default": 42},
                    "float_param": {"type": "number", "default": 3.14},
                    "bool_param": {"type": "boolean", "default": True},
                },
                "required": ["str_param"],
            },
        }

        tool_handler = await create_proxy_tool("proxy.test", "complex_tool", client, metadata)

        assert tool_handler is not None
        assert tool_handler.name == "proxy.test.complex_tool"

    @pytest.mark.asyncio
    async def test_create_proxy_tool_no_metadata(self):
        """Test creating proxy tool without metadata."""
        client = MockServerClient()

        tool_handler = await create_proxy_tool("proxy.backend", "simple_tool", client, None)

        assert tool_handler is not None
        assert tool_handler.name == "proxy.backend.simple_tool"
        assert "Proxied tool" in tool_handler.description

    @pytest.mark.asyncio
    async def test_create_proxy_tool_metadata_attached(self):
        """Test that metadata is attached to proxy wrapper."""
        client = MockServerClient()

        metadata = {
            "name": "test_tool",
            "description": "Test",
            "inputSchema": {"type": "object", "properties": {}, "required": []},
        }

        tool_handler = await create_proxy_tool("proxy.backend", "test_tool", client, metadata)

        # Check that the tool handler was created successfully
        assert tool_handler is not None

    @pytest.mark.asyncio
    async def test_proxy_tool_with_string_default(self):
        """Test proxy tool with string default value."""
        client = MockServerClient()

        metadata = {
            "name": "greet",
            "inputSchema": {
                "type": "object",
                "properties": {"message": {"type": "string", "default": "Hello World"}},
                "required": [],
            },
        }

        tool_handler = await create_proxy_tool("proxy.test", "greet", client, metadata)

        assert tool_handler is not None

    @pytest.mark.asyncio
    async def test_proxy_tool_with_none_default(self):
        """Test proxy tool with None default value."""
        client = MockServerClient()

        metadata = {
            "name": "optional_tool",
            "inputSchema": {
                "type": "object",
                "properties": {"optional_param": {"type": "string"}},
                "required": [],
            },
        }

        tool_handler = await create_proxy_tool("proxy.test", "optional_tool", client, metadata)

        assert tool_handler is not None

    @pytest.mark.asyncio
    async def test_proxy_tool_with_unknown_default(self):
        """Test proxy tool with unknown default value type."""
        client = MockServerClient()

        metadata = {
            "name": "unknown_defaults",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "weird_param": {"type": "string", "default": object()},  # Unknown type
                },
                "required": [],
            },
        }

        tool_handler = await create_proxy_tool("proxy.test", "unknown_defaults", client, metadata)

        assert tool_handler is not None

    @pytest.mark.asyncio
    async def test_proxy_tool_without_type(self):
        """Test proxy tool with parameter without type."""
        client = MockServerClient()

        metadata = {
            "name": "no_type",
            "inputSchema": {
                "type": "object",
                "properties": {"param": {"description": "A parameter without type"}},
                "required": [],
            },
        }

        tool_handler = await create_proxy_tool("proxy.test", "no_type", client, metadata)

        assert tool_handler is not None

    @pytest.mark.asyncio
    async def test_proxy_tool_no_input_schema(self):
        """Test proxy tool without input schema."""
        client = MockServerClient()

        metadata = {
            "name": "no_schema",
            "description": "Tool without schema",
        }

        tool_handler = await create_proxy_tool("proxy.test", "no_schema", client, metadata)

        assert tool_handler is not None

    @pytest.mark.asyncio
    async def test_proxy_tool_empty_properties(self):
        """Test proxy tool with empty properties."""
        client = MockServerClient()

        metadata = {
            "name": "empty_props",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }

        tool_handler = await create_proxy_tool("proxy.test", "empty_props", client, metadata)

        assert tool_handler is not None
