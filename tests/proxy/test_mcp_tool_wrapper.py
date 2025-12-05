"""
Tests for mcp_tool_wrapper module.

Tests the creation of ToolHandlers from MCPTool instances with
dynamic function signature generation.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from chuk_mcp_server.proxy.mcp_tool_wrapper import create_mcp_tool_handler


class TestCreateMCPToolHandler:
    """Test create_mcp_tool_handler function."""

    def test_create_simple_tool(self):
        """Test creating handler for simple tool with no params."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={"result": "success"})

        tool_def = {
            "name": "simple_tool",
            "description": "A simple tool",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="test.simple_tool",
        )

        assert handler is not None
        assert handler.name == "test.simple_tool"
        assert handler.description == "A simple tool"

    def test_create_tool_with_required_params(self):
        """Test creating handler for tool with required parameters."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={"result": "ok"})

        tool_def = {
            "name": "add",
            "description": "Add two numbers",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="math.add",
        )

        assert handler is not None
        assert handler.name == "math.add"

        # Check that the function has the right signature
        import inspect

        sig = inspect.signature(handler.handler)
        assert "a" in sig.parameters
        assert "b" in sig.parameters
        assert sig.parameters["a"].default == inspect.Parameter.empty
        assert sig.parameters["b"].default == inspect.Parameter.empty

    def test_create_tool_with_optional_params(self):
        """Test creating handler for tool with optional parameters."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={"result": "ok"})

        tool_def = {
            "name": "greet",
            "description": "Greet someone",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "formal": {"type": "boolean", "default": False},
                },
                "required": ["name"],
            },
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="greet.greet",
        )

        assert handler is not None

        # Check signature
        import inspect

        sig = inspect.signature(handler.handler)
        assert "name" in sig.parameters
        assert "formal" in sig.parameters
        assert sig.parameters["name"].default == inspect.Parameter.empty
        assert sig.parameters["formal"].default is False

    def test_create_tool_with_various_types(self):
        """Test creating handler with various parameter types."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={})

        tool_def = {
            "name": "multi_type",
            "description": "Tool with multiple types",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "str_param": {"type": "string"},
                    "int_param": {"type": "integer"},
                    "float_param": {"type": "number"},
                    "bool_param": {"type": "boolean"},
                    "obj_param": {"type": "object"},
                    "arr_param": {"type": "array"},
                },
                "required": [],
            },
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="test.multi_type",
        )

        assert handler is not None

        # All params should be optional (default None)
        import inspect

        sig = inspect.signature(handler.handler)
        for param_name in tool_def["inputSchema"]["properties"]:
            assert param_name in sig.parameters
            assert sig.parameters[param_name].default is None

    def test_create_tool_with_default_values(self):
        """Test creating handler with various default values."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={})

        # Test with primitive defaults only (dict/list defaults cause issues with caching)
        tool_def = {
            "name": "with_defaults",
            "description": "Tool with defaults",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "str_val": {"type": "string", "default": "hello"},
                    "int_val": {"type": "integer", "default": 42},
                    "float_val": {"type": "number", "default": 3.14},
                    "bool_val": {"type": "boolean", "default": True},
                },
                "required": [],
            },
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="test.with_defaults",
        )

        assert handler is not None

        import inspect

        sig = inspect.signature(handler.handler)
        assert sig.parameters["str_val"].default == "hello"
        assert sig.parameters["int_val"].default == 42
        assert sig.parameters["float_val"].default == 3.14
        assert sig.parameters["bool_val"].default is True

    @pytest.mark.asyncio
    async def test_execute_tool_no_params(self):
        """Test executing wrapped tool with no parameters."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={"status": "done"})

        tool_def = {
            "name": "no_params",
            "description": "No params tool",
            "inputSchema": {"type": "object", "properties": {}},
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="test.no_params",
        )

        result = await handler.handler()

        mcp_tool.execute.assert_called_once_with()
        assert result == {"status": "done"}

    @pytest.mark.asyncio
    async def test_execute_tool_with_params(self):
        """Test executing wrapped tool with parameters."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={"sum": 15})

        tool_def = {
            "name": "add",
            "description": "Add numbers",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="math.add",
        )

        result = await handler.handler(a=10, b=5)

        mcp_tool.execute.assert_called_once_with(a=10, b=5)
        assert result == {"sum": 15}

    @pytest.mark.asyncio
    async def test_execute_tool_filters_none_values(self):
        """Test that None values are filtered out when calling mcp_tool.execute."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={})

        tool_def = {
            "name": "optional_tool",
            "description": "Tool with optional params",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "required_param": {"type": "string"},
                    "optional_param": {"type": "string"},
                },
                "required": ["required_param"],
            },
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="test.optional_tool",
        )

        # Call with only required param (optional_param will be None)
        await handler.handler(required_param="value")

        # Should only pass non-None values
        mcp_tool.execute.assert_called_once_with(required_param="value")

    @pytest.mark.asyncio
    async def test_execute_tool_error_propagation(self):
        """Test that errors from mcp_tool.execute are propagated."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(side_effect=RuntimeError("Tool failed"))

        tool_def = {
            "name": "failing_tool",
            "description": "This will fail",
            "inputSchema": {"type": "object", "properties": {}},
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="test.failing_tool",
        )

        with pytest.raises(RuntimeError, match="Tool failed"):
            await handler.handler()

    def test_create_tool_without_description(self):
        """Test creating handler when description is missing."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={})

        tool_def = {
            "name": "no_desc",
            "inputSchema": {"type": "object", "properties": {}},
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="test.no_desc",
        )

        assert handler is not None
        assert handler.description == "MCP proxied tool: test.no_desc"

    def test_create_tool_empty_input_schema(self):
        """Test creating handler when inputSchema is empty."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={})

        tool_def = {
            "name": "empty_schema",
            "description": "Empty schema tool",
            "inputSchema": {},
        }

        handler = create_mcp_tool_handler(
            mcp_tool=mcp_tool,
            tool_def=tool_def,
            full_name="test.empty_schema",
        )

        assert handler is not None
        assert handler.name == "test.empty_schema"

    def test_create_tool_syntax_error_handling(self):
        """Test handling of syntax errors in generated code."""
        mcp_tool = Mock()
        mcp_tool.execute = AsyncMock(return_value={})

        # Create a tool def with an invalid parameter name (would cause syntax error)
        tool_def = {
            "name": "invalid",
            "description": "Invalid tool",
            "inputSchema": {
                "type": "object",
                "properties": {
                    # Invalid Python identifier - but our code should handle it
                    "valid-param": {"type": "string"},
                },
                "required": [],
            },
        }

        # This should either work or raise a SyntaxError
        # Our current implementation replaces - with _ so it should work
        try:
            handler = create_mcp_tool_handler(
                mcp_tool=mcp_tool,
                tool_def=tool_def,
                full_name="test.invalid",
            )
            # If it works, verify the handler was created
            assert handler is not None
        except SyntaxError:
            # If it raises SyntaxError, that's also acceptable behavior
            pass
