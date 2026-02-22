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


def test_tool_handler_from_function_with_oauth_metadata():
    """Test ToolHandler.from_function with OAuth metadata (lines 46-48)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def oauth_tool(name: str) -> str:
        """A tool that requires OAuth."""
        return f"Hello, {name}!"

    # Set OAuth metadata on the function (simulating @requires_auth decorator)
    oauth_tool._requires_auth = True
    oauth_tool._auth_scopes = ["read", "write"]

    handler = ToolHandler.from_function(oauth_tool)

    assert handler.requires_auth is True
    assert handler.auth_scopes == ["read", "write"]


def test_tool_handler_from_function_skips_external_access_token():
    """Test that _external_access_token parameter is skipped (line 59-60)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def oauth_aware_tool(name: str, _external_access_token: str = None) -> str:
        """A tool with OAuth token parameter that should be skipped."""
        return f"Hello, {name}!"

    handler = ToolHandler.from_function(oauth_aware_tool)

    # Should only have 'name' parameter, not '_external_access_token'
    assert len(handler.parameters) == 1
    assert handler.parameters[0].name == "name"


def test_tool_handler_from_function_no_oauth_metadata():
    """Test ToolHandler.from_function without OAuth metadata (defaults)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def simple_tool(value: str) -> str:
        return value

    handler = ToolHandler.from_function(simple_tool)

    # Should default to no auth required
    assert handler.requires_auth is False
    assert handler.auth_scopes is None


@pytest.mark.asyncio
async def test_tool_handler_execute_with_default_none_values():
    """Test execute with None default values (line 149)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def tool_with_optional(name: str, metadata: dict = None) -> dict:
        return {"name": name, "metadata": metadata}

    handler = ToolHandler.from_function(tool_with_optional)

    # Execute without providing optional parameter
    result = await handler.execute({"name": "test"})

    assert result["name"] == "test"
    assert result["metadata"] is None


@pytest.mark.asyncio
async def test_tool_handler_convert_type_integer_from_string_float():
    """Test _convert_type integer conversion from float string (lines 178-186)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def int_tool(count: int) -> int:
        return count * 2

    handler = ToolHandler.from_function(int_tool)

    # Test conversion from float string like "42.0"
    result = await handler.execute({"count": "42.0"})
    assert result == 84

    # Test invalid float string conversion
    from chuk_mcp_server.types.errors import ParameterValidationError

    with pytest.raises(ParameterValidationError):
        await handler.execute({"count": "42.7"})


@pytest.mark.asyncio
async def test_tool_handler_convert_type_integer_from_other_type():
    """Test _convert_type integer conversion fallback (line 189-190)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def int_tool(value: int) -> int:
        return value

    handler = ToolHandler.from_function(int_tool)

    # Test direct int conversion from bool
    result = await handler.execute({"value": True})
    assert result == 1


@pytest.mark.asyncio
async def test_tool_handler_convert_type_number_from_string_error():
    """Test _convert_type number conversion error (lines 195-199)."""
    from chuk_mcp_server.types.errors import ParameterValidationError
    from chuk_mcp_server.types.tools import ToolHandler

    def number_tool(ratio: float) -> float:
        return ratio * 2

    handler = ToolHandler.from_function(number_tool)

    # Test invalid string to float conversion
    with pytest.raises(ParameterValidationError):
        await handler.execute({"ratio": "not_a_number"})


@pytest.mark.asyncio
async def test_tool_handler_convert_type_number_from_other_type():
    """Test _convert_type number conversion fallback (line 200-201)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def number_tool(value: float) -> float:
        return value

    handler = ToolHandler.from_function(number_tool)

    # Test direct float conversion
    result = await handler.execute({"value": True})
    assert result == 1.0


@pytest.mark.asyncio
async def test_tool_handler_convert_type_boolean_empty_string():
    """Test _convert_type boolean conversion from empty string (lines 210-212)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def bool_tool(enabled: bool = True) -> bool:
        return enabled

    handler = ToolHandler.from_function(bool_tool)

    # Test empty string uses default
    result = await handler.execute({"enabled": ""})
    assert result is True

    # Test "null" string uses default
    result2 = await handler.execute({"enabled": "null"})
    assert result2 is True


@pytest.mark.asyncio
async def test_tool_handler_convert_type_boolean_unrecognized_string():
    """Test _convert_type boolean conversion from unrecognized string (lines 217-220)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def bool_tool(enabled: bool = False) -> bool:
        return enabled

    handler = ToolHandler.from_function(bool_tool)

    # Test unrecognized string uses default
    result = await handler.execute({"enabled": "maybe"})
    assert result is False


@pytest.mark.asyncio
async def test_tool_handler_convert_type_boolean_none_value():
    """Test _convert_type boolean conversion from None (lines 224-226)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.tools import ToolHandler

    def bool_tool(enabled: bool = True) -> bool:
        return enabled

    handler = ToolHandler.from_function(bool_tool)

    # Create a parameter with None value and explicit default
    param = ToolParameter(name="enabled", type="boolean", required=False, default=True)

    # Test conversion with None value
    result = handler._convert_type(None, param)
    assert result is True


@pytest.mark.asyncio
async def test_tool_handler_convert_type_boolean_exception():
    """Test _convert_type boolean conversion exception (lines 229-232)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.tools import ToolHandler

    def dummy_fn():
        return None

    handler = ToolHandler.from_function(dummy_fn)
    param = ToolParameter(name="enabled", type="boolean", required=True)

    # Create an object that can't be converted to bool
    class UnconvertibleType:
        def __bool__(self):
            raise RuntimeError("Cannot convert")

    with pytest.raises(ValueError) as exc_info:
        handler._convert_type(UnconvertibleType(), param)

    assert "Cannot convert" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tool_handler_convert_type_string_from_other_types():
    """Test _convert_type string conversion (lines 234-239)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def string_tool(value: str) -> str:
        return value

    handler = ToolHandler.from_function(string_tool)

    # Test conversion from various types
    result1 = await handler.execute({"value": 42})
    assert result1 == "42"

    result2 = await handler.execute({"value": True})
    assert result2 == "True"

    result3 = await handler.execute({"value": [1, 2, 3]})
    assert result3 == "[1, 2, 3]"


@pytest.mark.asyncio
async def test_tool_handler_convert_type_array_from_tuple_set():
    """Test _convert_type array conversion from tuple/set (lines 244-245)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.tools import ToolHandler

    handler = ToolHandler.from_function(lambda: None, name="dummy")
    param = ToolParameter(name="items", type="array", required=True)

    # Test tuple conversion
    result1 = handler._convert_type((1, 2, 3), param)
    assert result1 == [1, 2, 3]

    # Test set conversion
    result2 = handler._convert_type({1, 2, 3}, param)
    assert set(result2) == {1, 2, 3}


@pytest.mark.asyncio
async def test_tool_handler_convert_type_array_invalid_json():
    """Test _convert_type array conversion with invalid JSON (lines 252-255)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.tools import ToolHandler

    handler = ToolHandler.from_function(lambda: None, name="dummy")
    param = ToolParameter(name="items", type="array", required=True)

    # Test invalid JSON string
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type("not valid json", param)

    assert "Cannot convert string" in str(exc_info.value)

    # Test non-array JSON
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type('{"key": "value"}', param)

    assert "does not represent an array" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tool_handler_convert_type_array_invalid_type():
    """Test _convert_type array conversion with invalid type (line 256-257)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.tools import ToolHandler

    handler = ToolHandler.from_function(lambda: None, name="dummy")
    param = ToolParameter(name="items", type="array", required=True)

    # Test invalid type
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type(42, param)

    assert "Cannot convert" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tool_handler_convert_type_object_invalid_json():
    """Test _convert_type object conversion with invalid JSON (lines 268-271)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.tools import ToolHandler

    handler = ToolHandler.from_function(lambda: None, name="dummy")
    param = ToolParameter(name="config", type="object", required=True)

    # Test invalid JSON string
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type("not valid json", param)

    assert "Cannot convert string" in str(exc_info.value)

    # Test non-object JSON
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type("[1, 2, 3]", param)

    assert "does not represent an object" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tool_handler_convert_type_object_invalid_type():
    """Test _convert_type object conversion with invalid type (lines 272-273)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.tools import ToolHandler

    handler = ToolHandler.from_function(lambda: None, name="dummy")
    param = ToolParameter(name="config", type="object", required=True)

    # Test invalid type
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type(42, param)

    assert "Cannot convert" in str(exc_info.value)


def test_tool_handler_convert_type_enum_invalid():
    """Test _convert_type enum validation (lines 276-277).

    Note: Lines 276-277 contain enum validation code, but it's unreachable in practice
    because all type handlers (string, integer, etc.) return early. The enum check
    would only execute for unknown types. This test verifies the code exists but
    acknowledges it's currently dead code that should be refactored.
    """
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.tools import ToolHandler

    handler = ToolHandler.from_function(lambda: None, name="dummy")

    # Create a parameter with an unknown type to reach the enum check
    param = ToolParameter(name="level", type="unknown_type", required=True, enum=["low", "medium", "high"])

    # For unknown types, the code falls through to the enum check
    # Test valid enum value
    result = handler._convert_type("low", param)
    assert result == "low"

    # Test invalid enum value - should trigger the enum check at lines 276-277
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type("invalid", param)

    assert "must be one of" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tool_handler_execute_validation_error_reraise():
    """Test execute re-raises ValidationError (line 291-293)."""
    from chuk_mcp_server.types.tools import ToolHandler

    def strict_tool(count: int) -> int:
        return count

    handler = ToolHandler.from_function(strict_tool)

    # ValidationError should be re-raised as-is
    from chuk_mcp_server.types.errors import ParameterValidationError

    with pytest.raises(ParameterValidationError):
        await handler.execute({"count": None})


if __name__ == "__main__":
    pytest.main([__file__])
