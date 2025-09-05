#!/usr/bin/env python3
# tests/types/test_tools.py
"""
Unit tests for chuk_mcp_server.types.tools module

Tests ToolHandler class, tool creation, execution, and optimization features.
"""

import asyncio

import orjson
import pytest


def test_tool_handler_from_function_basic():
    """Test creating ToolHandler from a basic function."""
    from chuk_mcp_server.types.tools import ToolHandler

    def simple_tool(name: str) -> str:
        """A simple tool that greets someone."""
        return f"Hello, {name}!"

    handler = ToolHandler.from_function(simple_tool)

    assert handler.name == "simple_tool"
    assert handler.description == "A simple tool that greets someone."
    assert len(handler.parameters) == 1
    assert handler.parameters[0].name == "name"
    assert handler.parameters[0].type == "string"
    assert handler.parameters[0].required is True


def test_tool_handler_from_function_with_custom_name():
    """Test creating ToolHandler with custom name and description."""
    from chuk_mcp_server.types.tools import ToolHandler

    def my_function(x: int) -> int:
        return x * 2

    handler = ToolHandler.from_function(my_function, name="double_number", description="Doubles a number")

    assert handler.name == "double_number"
    assert handler.description == "Doubles a number"


def test_tool_handler_from_function_complex_params():
    """Test creating ToolHandler from function with complex parameters."""
    from chuk_mcp_server.types.tools import ToolHandler

    def complex_tool(
        name: str,
        count: int = 10,
        enabled: bool = True,
        items: list[str] = None,  # noqa: ARG001
        config: dict[str, str | int] = None,  # noqa: ARG001
    ) -> dict:
        return {"name": name, "count": count, "enabled": enabled}

    handler = ToolHandler.from_function(complex_tool)

    assert len(handler.parameters) == 5

    # Check name parameter
    name_param = handler.parameters[0]
    assert name_param.name == "name"
    assert name_param.type == "string"
    assert name_param.required is True

    # Check count parameter
    count_param = handler.parameters[1]
    assert count_param.name == "count"
    assert count_param.type == "integer"
    assert count_param.required is False
    assert count_param.default == 10

    # Check enabled parameter
    enabled_param = handler.parameters[2]
    assert enabled_param.name == "enabled"
    assert enabled_param.type == "boolean"
    assert enabled_param.required is False
    assert enabled_param.default is True

    # Check items parameter
    items_param = handler.parameters[3]
    assert items_param.name == "items"
    assert items_param.type == "array"
    assert items_param.required is False

    # Check config parameter
    config_param = handler.parameters[4]
    assert config_param.name == "config"
    assert config_param.type == "object"
    assert config_param.required is False


def test_tool_handler_to_mcp_format():
    """Test ToolHandler MCP format conversion."""
    from chuk_mcp_server.types.tools import ToolHandler

    def test_tool(name: str, count: int = 5) -> str:
        """A test tool."""
        return f"Hello {name} x{count}"

    handler = ToolHandler.from_function(test_tool)
    mcp_format = handler.to_mcp_format()

    assert isinstance(mcp_format, dict)
    assert mcp_format["name"] == "test_tool"
    assert mcp_format["description"] == "A test tool."
    assert "inputSchema" in mcp_format

    schema = mcp_format["inputSchema"]
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "count" in schema["properties"]
    assert schema["required"] == ["name"]


def test_tool_handler_to_mcp_bytes():
    """Test ToolHandler orjson bytes conversion."""
    from chuk_mcp_server.types.tools import ToolHandler

    def test_tool(name: str) -> str:
        return f"Hello, {name}!"

    handler = ToolHandler.from_function(test_tool)
    mcp_bytes = handler.to_mcp_bytes()

    assert isinstance(mcp_bytes, bytes)

    # Test that it can be deserialized
    mcp_data = orjson.loads(mcp_bytes)
    assert mcp_data["name"] == "test_tool"
    assert "inputSchema" in mcp_data


def test_tool_handler_caching():
    """Test that ToolHandler caches MCP format properly."""
    from chuk_mcp_server.types.tools import ToolHandler

    def test_tool(name: str) -> str:
        return f"Hello, {name}!"

    handler = ToolHandler.from_function(test_tool)

    # First calls should cache
    format1 = handler.to_mcp_format()
    bytes1 = handler.to_mcp_bytes()

    # Second calls should return cached versions
    format2 = handler.to_mcp_format()
    bytes2 = handler.to_mcp_bytes()

    # Should be different objects (copies) for format
    assert format1 is not format2
    assert format1 == format2

    # Should be same object for bytes (immutable)
    assert bytes1 is bytes2

    # Test cache invalidation
    handler.invalidate_cache()
    handler.to_mcp_format()
    bytes3 = handler.to_mcp_bytes()

    # Should be new objects after invalidation
    assert bytes1 is not bytes3
    assert bytes1 == bytes3  # But content should be same


@pytest.mark.asyncio
async def test_tool_handler_execute_sync():
    """Test executing synchronous tool."""
    from chuk_mcp_server.types.tools import ToolHandler

    def sync_tool(name: str, multiplier: int = 2) -> str:
        return f"Hello {name}" * multiplier

    handler = ToolHandler.from_function(sync_tool)

    result = await handler.execute({"name": "World", "multiplier": 3})
    assert result == "Hello WorldHello WorldHello World"


@pytest.mark.asyncio
async def test_tool_handler_execute_async():
    """Test executing asynchronous tool."""
    from chuk_mcp_server.types.tools import ToolHandler

    async def async_tool(name: str, delay: float = 0.01) -> str:
        await asyncio.sleep(delay)
        return f"Async hello, {name}!"

    handler = ToolHandler.from_function(async_tool)

    result = await handler.execute({"name": "World", "delay": 0.01})
    assert result == "Async hello, World!"


@pytest.mark.asyncio
async def test_tool_handler_parameter_validation():
    """Test parameter validation and conversion."""
    from chuk_mcp_server.types.errors import ParameterValidationError
    from chuk_mcp_server.types.tools import ToolHandler

    def typed_tool(name: str, count: int, ratio: float, enabled: bool) -> dict:
        return {"name": name, "count": count, "ratio": ratio, "enabled": enabled}

    handler = ToolHandler.from_function(typed_tool)

    # Test valid arguments
    result = await handler.execute({"name": "test", "count": 5, "ratio": 3.14, "enabled": True})

    assert result["name"] == "test"
    assert result["count"] == 5
    assert result["ratio"] == 3.14
    assert result["enabled"] is True

    # Test missing required parameter
    with pytest.raises(ParameterValidationError) as exc_info:
        await handler.execute({"name": "test"})  # Missing count, ratio, enabled

    assert "count" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tool_handler_type_conversion():
    """Test automatic type conversion."""
    from chuk_mcp_server.types.tools import ToolHandler

    def conversion_tool(count: int, ratio: float, enabled: bool, items: list, config: dict) -> dict:
        return {
            "count": count,
            "count_type": type(count).__name__,
            "ratio": ratio,
            "ratio_type": type(ratio).__name__,
            "enabled": enabled,
            "enabled_type": type(enabled).__name__,
            "items": items,
            "config": config,
        }

    handler = ToolHandler.from_function(conversion_tool)

    # Test string to number conversion
    result = await handler.execute(
        {
            "count": "42",  # string -> int
            "ratio": "3.14",  # string -> float
            "enabled": "true",  # string -> bool
            "items": '["a", "b"]',  # JSON string -> list
            "config": '{"key": "value"}',  # JSON string -> dict
        }
    )

    assert result["count"] == 42
    assert result["count_type"] == "int"
    assert result["ratio"] == 3.14
    assert result["ratio_type"] == "float"
    assert result["enabled"] is True
    assert result["enabled_type"] == "bool"
    assert result["items"] == ["a", "b"]
    assert result["config"] == {"key": "value"}


@pytest.mark.asyncio
async def test_tool_handler_type_conversion_edge_cases():
    """Test edge cases in type conversion."""
    from chuk_mcp_server.types.tools import ToolHandler

    def edge_case_tool(count: int, enabled: bool) -> dict:
        return {"count": count, "enabled": enabled}

    handler = ToolHandler.from_function(edge_case_tool)

    # Test float to int conversion
    result = await handler.execute({"count": 5.0, "enabled": 1})
    assert result["count"] == 5
    assert result["enabled"] is True

    # Test various boolean string formats
    result2 = await handler.execute({"count": 10, "enabled": "false"})
    assert result2["enabled"] is False

    result3 = await handler.execute({"count": 10, "enabled": "0"})
    assert result3["enabled"] is False

    result4 = await handler.execute({"count": 10, "enabled": "yes"})
    assert result4["enabled"] is True


@pytest.mark.asyncio
async def test_tool_handler_invalid_conversion():
    """Test invalid type conversion handling."""
    from chuk_mcp_server.types.errors import ParameterValidationError
    from chuk_mcp_server.types.tools import ToolHandler

    def strict_tool(count: int) -> int:
        return count * 2

    handler = ToolHandler.from_function(strict_tool)

    # Test invalid integer conversion
    with pytest.raises(ParameterValidationError):
        await handler.execute({"count": "not_a_number"})

    # Test float that can't be converted to int without precision loss
    with pytest.raises(ParameterValidationError):
        await handler.execute({"count": 3.7})


@pytest.mark.asyncio
async def test_tool_handler_execution_error():
    """Test handling of tool execution errors."""
    from chuk_mcp_server.types.errors import ToolExecutionError
    from chuk_mcp_server.types.tools import ToolHandler

    def failing_tool(x: int) -> int:
        if x == 0:
            raise ValueError("Division by zero!")
        return 10 / x

    handler = ToolHandler.from_function(failing_tool)

    # Test successful execution
    result = await handler.execute({"x": 2})
    assert result == 5.0

    # Test execution error
    with pytest.raises(ToolExecutionError) as exc_info:
        await handler.execute({"x": 0})

    assert "failing_tool" in str(exc_info.value)
    assert "Division by zero!" in str(exc_info.value)


def test_tool_handler_with_method():
    """Test creating ToolHandler from a class method."""
    from chuk_mcp_server.types.tools import ToolHandler

    class TestClass:
        def method_tool(self, name: str) -> str:
            """A method tool."""
            return f"Method says hello to {name}"

    instance = TestClass()
    handler = ToolHandler.from_function(instance.method_tool)

    # Should skip 'self' parameter
    assert len(handler.parameters) == 1
    assert handler.parameters[0].name == "name"


def test_create_tool_from_function_utility():
    """Test the convenience function for creating tools."""
    from chuk_mcp_server.types.tools import ToolHandler, create_tool_from_function

    def utility_tool(data: str) -> str:
        return data.upper()

    handler = create_tool_from_function(utility_tool, name="uppercase", description="Convert to uppercase")

    assert handler.name == "uppercase"
    assert handler.description == "Convert to uppercase"
    assert isinstance(handler, ToolHandler)


def test_tool_handler_with_orjson_optimization():
    """Test that orjson optimization is working in type conversion."""
    from chuk_mcp_server.types.tools import ToolHandler

    def json_tool(data: list, config: dict) -> dict:
        return {"data_length": len(data), "config_keys": list(config.keys())}

    handler = ToolHandler.from_function(json_tool)

    # This should use orjson.loads internally for better performance
    result = asyncio.run(
        handler.execute(
            {"data": '["item1", "item2", "item3"]', "config": '{"setting1": "value1", "setting2": "value2"}'}
        )
    )

    assert result["data_length"] == 3
    assert set(result["config_keys"]) == {"setting1", "setting2"}


def test_tool_handler_properties():
    """Test ToolHandler properties."""
    from chuk_mcp_server.types.tools import ToolHandler

    def prop_tool() -> str:
        """Property test tool."""
        return "test"

    handler = ToolHandler.from_function(prop_tool, name="custom_name", description="Custom description")

    assert handler.name == "custom_name"
    assert handler.description == "Custom description"

    # Test fallback to function name/docstring
    handler2 = ToolHandler.from_function(prop_tool)
    assert handler2.name == "prop_tool"
    assert handler2.description == "Property test tool."


def test_module_exports():
    """Test that all expected exports are available."""
    from chuk_mcp_server.types import tools

    assert hasattr(tools, "__all__")
    assert isinstance(tools.__all__, list)

    expected_exports = ["ToolHandler", "create_tool_from_function"]

    for export in expected_exports:
        assert export in tools.__all__
        assert hasattr(tools, export)


if __name__ == "__main__":
    pytest.main([__file__])
