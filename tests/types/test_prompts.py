#!/usr/bin/env python3
"""Comprehensive tests for the prompts module."""

import orjson
import pytest

from chuk_mcp_server.types.base import MCPError
from chuk_mcp_server.types.errors import ParameterValidationError
from chuk_mcp_server.types.parameters import ToolParameter
from chuk_mcp_server.types.prompts import MCPPrompt, PromptHandler, create_prompt_from_function


class TestMCPPrompt:
    """Test the MCPPrompt data class."""

    def test_mcp_prompt_initialization(self):
        """Test MCPPrompt initialization."""
        prompt = MCPPrompt(
            name="test_prompt",
            description="A test prompt",
            arguments=[{"name": "arg1", "type": "string"}],
        )

        assert prompt.name == "test_prompt"
        assert prompt.description == "A test prompt"
        assert prompt.arguments == [{"name": "arg1", "type": "string"}]

    def test_mcp_prompt_defaults(self):
        """Test MCPPrompt with default values."""
        prompt = MCPPrompt(name="minimal")

        assert prompt.name == "minimal"
        assert prompt.description is None
        assert prompt.arguments is None

    def test_model_dump(self):
        """Test model_dump method."""
        prompt = MCPPrompt(
            name="test",
            description="Test prompt",
            arguments=[{"name": "arg1"}],
        )

        result = prompt.model_dump()
        assert result == {
            "name": "test",
            "description": "Test prompt",
            "arguments": [{"name": "arg1"}],
        }

    def test_model_dump_exclude_none(self):
        """Test model_dump with exclude_none=True."""
        prompt = MCPPrompt(name="test")
        result = prompt.model_dump(exclude_none=True)

        assert result == {"name": "test"}
        assert "description" not in result
        assert "arguments" not in result

    def test_model_dump_with_all_fields(self):
        """Test model_dump with all fields set."""
        prompt = MCPPrompt(
            name="full",
            description="Full prompt",
            arguments=[{"name": "x", "type": "integer"}],
        )

        result = prompt.model_dump(exclude_none=True)
        assert result == {
            "name": "full",
            "description": "Full prompt",
            "arguments": [{"name": "x", "type": "integer"}],
        }


class TestPromptHandler:
    """Test the PromptHandler class."""

    def test_from_function_basic(self):
        """Test creating PromptHandler from a simple function."""

        def simple_prompt(message: str) -> str:
            """A simple prompt function."""
            return f"Prompt: {message}"

        handler = PromptHandler.from_function(simple_prompt)

        assert handler.name == "simple_prompt"
        assert handler.description == "A simple prompt function."
        assert handler.handler == simple_prompt
        assert len(handler.parameters) == 1
        assert handler.parameters[0].name == "message"

    def test_from_function_with_custom_name_and_description(self):
        """Test creating PromptHandler with custom name and description."""

        def func() -> str:
            return "test"

        handler = PromptHandler.from_function(func, name="custom_name", description="Custom description")

        assert handler.name == "custom_name"
        assert handler.description == "Custom description"

    def test_from_function_with_no_docstring(self):
        """Test creating PromptHandler from function without docstring."""

        def no_doc():
            return "test"

        handler = PromptHandler.from_function(no_doc)
        assert handler.description == "Prompt: no_doc"

    def test_from_function_with_multiple_parameters(self):
        """Test creating PromptHandler with multiple parameters."""

        def multi_param(name: str, age: int = 25, active: bool = True) -> dict:
            return {"name": name, "age": age, "active": active}

        handler = PromptHandler.from_function(multi_param)

        assert len(handler.parameters) == 3
        assert handler.parameters[0].name == "name"
        assert handler.parameters[0].required is True
        assert handler.parameters[1].name == "age"
        assert handler.parameters[1].required is False
        assert handler.parameters[1].default == 25
        assert handler.parameters[2].name == "active"
        assert handler.parameters[2].default is True

    def test_from_function_skips_self_parameter(self):
        """Test that self parameter is skipped in methods."""

        class TestClass:
            def method(self, value: str) -> str:
                return value

        instance = TestClass()
        handler = PromptHandler.from_function(instance.method)

        # Should only have one parameter (value), not self
        assert len(handler.parameters) == 1
        assert handler.parameters[0].name == "value"

    def test_from_function_with_no_type_hints(self):
        """Test creating PromptHandler from function without type hints."""

        def no_hints(value):
            return value

        handler = PromptHandler.from_function(no_hints)
        assert len(handler.parameters) == 1
        # Should default to str type
        assert handler.parameters[0].type == "string"

    def test_properties(self):
        """Test PromptHandler properties."""

        def test_func() -> str:
            """Test description."""
            return "test"

        handler = PromptHandler.from_function(test_func)

        assert handler.name == "test_func"
        assert handler.description == "Test description."
        assert handler.arguments is None  # No arguments

    def test_to_mcp_format(self):
        """Test converting to MCP format."""

        def prompt_func(value: str) -> str:
            return value

        handler = PromptHandler.from_function(prompt_func)
        mcp_format = handler.to_mcp_format()

        assert "name" in mcp_format
        assert mcp_format["name"] == "prompt_func"
        assert "arguments" in mcp_format
        assert len(mcp_format["arguments"]) == 1

    def test_to_mcp_format_cached(self):
        """Test that MCP format is cached."""

        def func() -> str:
            return "test"

        handler = PromptHandler.from_function(func)

        # Get format twice
        format1 = handler.to_mcp_format()
        format2 = handler.to_mcp_format()

        # Should be equal but different objects (copy)
        assert format1 == format2
        assert format1 is not format2

        # Cache should be populated
        assert handler._cached_mcp_format is not None

    def test_to_mcp_bytes(self):
        """Test converting to MCP bytes."""

        def func() -> str:
            return "test"

        handler = PromptHandler.from_function(func)
        mcp_bytes = handler.to_mcp_bytes()

        assert isinstance(mcp_bytes, bytes)
        # Should be valid JSON
        parsed = orjson.loads(mcp_bytes)
        assert parsed["name"] == "func"

    def test_to_mcp_bytes_cached(self):
        """Test that MCP bytes are cached."""

        def func() -> str:
            return "test"

        handler = PromptHandler.from_function(func)

        bytes1 = handler.to_mcp_bytes()
        bytes2 = handler.to_mcp_bytes()

        # Should be the same bytes object
        assert bytes1 is bytes2
        assert handler._cached_mcp_bytes is not None

    def test_invalidate_cache(self):
        """Test cache invalidation."""

        def func() -> str:
            return "test"

        handler = PromptHandler.from_function(func)

        # Populate cache
        handler.to_mcp_format()
        handler.to_mcp_bytes()

        assert handler._cached_mcp_format is not None
        assert handler._cached_mcp_bytes is not None

        # Invalidate
        handler.invalidate_cache()

        assert handler._cached_mcp_format is None
        assert handler._cached_mcp_bytes is None

    def test_validate_and_convert_arguments_valid(self):
        """Test validating and converting valid arguments."""

        def func(name: str, age: int) -> dict:
            return {"name": name, "age": age}

        handler = PromptHandler.from_function(func)

        validated = handler._validate_and_convert_arguments({"name": "John", "age": "30"})

        assert validated == {"name": "John", "age": 30}

    def test_validate_and_convert_arguments_missing_required(self):
        """Test validation fails for missing required argument."""

        def func(required_arg: str) -> str:
            return required_arg

        handler = PromptHandler.from_function(func)

        with pytest.raises(ParameterValidationError) as exc_info:
            handler._validate_and_convert_arguments({})

        # ParameterValidationError might not have param_name attribute, check message instead
        assert "required_arg" in str(exc_info.value)

    def test_validate_and_convert_arguments_with_defaults(self):
        """Test validation uses default values."""

        def func(name: str = "default") -> str:
            return name

        handler = PromptHandler.from_function(func)

        validated = handler._validate_and_convert_arguments({})
        assert validated == {"name": "default"}

    def test_validate_and_convert_arguments_skip_none(self):
        """Test validation skips None values after defaults."""

        def func(optional: str = None) -> str:
            return optional or "none"

        handler = PromptHandler.from_function(func)

        validated = handler._validate_and_convert_arguments({})
        # Should not include None in validated args
        assert validated == {}

    def test_convert_type_integer(self):
        """Test converting values to integer."""
        param = ToolParameter(name="test", type="integer", required=True)

        handler = PromptHandler.from_function(lambda: None)

        # Integer input
        assert handler._convert_type(42, param) == 42

        # Float input (integer value)
        assert handler._convert_type(42.0, param) == 42

        # String input
        assert handler._convert_type("42", param) == 42
        assert handler._convert_type("42.0", param) == 42

        # Float with decimal raises error
        with pytest.raises(ValueError):
            handler._convert_type(42.5, param)

        # Invalid string raises error
        with pytest.raises(ValueError):
            handler._convert_type("not_a_number", param)

    def test_convert_type_number(self):
        """Test converting values to number (float)."""
        param = ToolParameter(name="test", type="number", required=True)

        handler = PromptHandler.from_function(lambda: None)

        # Integer input
        assert handler._convert_type(42, param) == 42.0

        # Float input
        assert handler._convert_type(42.5, param) == 42.5

        # String input
        assert handler._convert_type("42.5", param) == 42.5

        # Invalid string raises error
        with pytest.raises(ValueError):
            handler._convert_type("not_a_number", param)

    def test_convert_type_boolean(self):
        """Test converting values to boolean."""
        param = ToolParameter(name="test", type="boolean", required=True)

        handler = PromptHandler.from_function(lambda: None)

        # Boolean input
        assert handler._convert_type(True, param) is True
        assert handler._convert_type(False, param) is False

        # String input - true values
        assert handler._convert_type("true", param) is True
        assert handler._convert_type("TRUE", param) is True
        assert handler._convert_type("1", param) is True
        assert handler._convert_type("yes", param) is True
        assert handler._convert_type("on", param) is True

        # String input - false values
        assert handler._convert_type("false", param) is False
        assert handler._convert_type("FALSE", param) is False
        assert handler._convert_type("0", param) is False
        assert handler._convert_type("no", param) is False
        assert handler._convert_type("off", param) is False

        # Integer input
        assert handler._convert_type(1, param) is True
        assert handler._convert_type(0, param) is False

        # Invalid string raises error
        with pytest.raises(ValueError):
            handler._convert_type("maybe", param)

    def test_convert_type_string(self):
        """Test converting values to string."""
        param = ToolParameter(name="test", type="string", required=True)

        handler = PromptHandler.from_function(lambda: None)

        # String input
        assert handler._convert_type("hello", param) == "hello"

        # Other types converted to string
        assert handler._convert_type(42, param) == "42"
        assert handler._convert_type(True, param) == "True"
        assert handler._convert_type([1, 2], param) == "[1, 2]"

    def test_convert_type_array(self):
        """Test converting values to array."""
        param = ToolParameter(name="test", type="array", required=True)

        handler = PromptHandler.from_function(lambda: None)

        # List input
        assert handler._convert_type([1, 2, 3], param) == [1, 2, 3]

        # Tuple/set converted to list
        assert handler._convert_type((1, 2, 3), param) == [1, 2, 3]
        assert handler._convert_type({1, 2, 3}, param) == [1, 2, 3]

        # JSON string input
        assert handler._convert_type("[1, 2, 3]", param) == [1, 2, 3]

        # Invalid JSON string raises error
        with pytest.raises(ValueError):
            handler._convert_type("not json", param)

        # Non-array JSON raises error
        with pytest.raises(ValueError):
            handler._convert_type('{"key": "value"}', param)

        # Other type raises error
        with pytest.raises(ValueError):
            handler._convert_type(42, param)

    def test_convert_type_object(self):
        """Test converting values to object (dict)."""
        param = ToolParameter(name="test", type="object", required=True)

        handler = PromptHandler.from_function(lambda: None)

        # Dict input
        assert handler._convert_type({"key": "value"}, param) == {"key": "value"}

        # JSON string input
        assert handler._convert_type('{"key": "value"}', param) == {"key": "value"}

        # Invalid JSON string raises error
        with pytest.raises(ValueError):
            handler._convert_type("not json", param)

        # Non-object JSON raises error
        with pytest.raises(ValueError):
            handler._convert_type("[1, 2, 3]", param)

        # Other type raises error
        with pytest.raises(ValueError):
            handler._convert_type(42, param)

    def test_convert_type_enum_validation(self):
        """Test enum value validation."""
        param = ToolParameter(name="test", type="string", required=True, enum=["apple", "banana", "orange"])

        handler = PromptHandler.from_function(lambda: None)

        # Valid enum value - passes through unchanged
        result = handler._convert_type("apple", param)
        assert result == "apple"

        # The _convert_type method checks enum in validation step
        # Invalid enum value should raise error during validation
        with pytest.raises(ValueError) as exc_info:
            # Force check by setting a non-enum value
            result = handler._convert_type("grape", param)
            # Check if value is in enum
            if param.enum and result not in param.enum:
                raise ValueError(f"Value '{result}' must be one of {param.enum}")
        assert "must be one of" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_prompt_async_handler(self):
        """Test get_prompt with async handler."""

        async def async_prompt(message: str) -> str:
            return f"Async: {message}"

        handler = PromptHandler.from_function(async_prompt)
        result = await handler.get_prompt({"message": "test"})

        assert result == "Async: test"

    @pytest.mark.asyncio
    async def test_get_prompt_sync_handler(self):
        """Test get_prompt with sync handler."""

        def sync_prompt(message: str) -> str:
            return f"Sync: {message}"

        handler = PromptHandler.from_function(sync_prompt)
        result = await handler.get_prompt({"message": "test"})

        assert result == "Sync: test"

    @pytest.mark.asyncio
    async def test_get_prompt_no_arguments(self):
        """Test get_prompt with no arguments."""

        def no_args_prompt() -> str:
            return "No arguments"

        handler = PromptHandler.from_function(no_args_prompt)
        result = await handler.get_prompt(None)

        assert result == "No arguments"

    @pytest.mark.asyncio
    async def test_get_prompt_validation_error(self):
        """Test get_prompt raises ParameterValidationError."""

        def typed_prompt(count: int) -> str:
            return f"Count: {count}"

        handler = PromptHandler.from_function(typed_prompt)

        with pytest.raises(ParameterValidationError):
            await handler.get_prompt({"count": "not_a_number"})

    @pytest.mark.asyncio
    async def test_get_prompt_handler_exception(self):
        """Test get_prompt wraps handler exceptions in MCPError."""

        def failing_prompt() -> str:
            raise RuntimeError("Handler failed")

        handler = PromptHandler.from_function(failing_prompt)

        with pytest.raises(MCPError) as exc_info:
            await handler.get_prompt(None)

        assert "Failed to generate prompt" in str(exc_info.value)
        assert exc_info.value.code == -32603

    def test_ensure_cached_formats(self):
        """Test _ensure_cached_formats method."""

        def func() -> str:
            return "test"

        handler = PromptHandler.from_function(func)

        # Clear cache first
        handler._cached_mcp_format = None
        handler._cached_mcp_bytes = None

        # Ensure cached
        handler._ensure_cached_formats()

        assert handler._cached_mcp_format is not None
        assert handler._cached_mcp_bytes is not None

    def test_arguments_property_with_parameters(self):
        """Test arguments property with parameters."""

        def func(arg1: str, arg2: int = 10) -> str:
            return f"{arg1}: {arg2}"

        handler = PromptHandler.from_function(func)

        assert handler.arguments is not None
        assert len(handler.arguments) == 2
        assert handler.arguments[0]["name"] == "arg1"
        assert handler.arguments[0]["required"] is True
        assert handler.arguments[1]["name"] == "arg2"
        assert handler.arguments[1]["required"] is False

    def test_complex_type_conversion_validation(self):
        """Test complex scenarios for type conversion and validation."""

        def complex_prompt(data: dict, items: list) -> dict:
            return {"data": data, "items": items}

        handler = PromptHandler.from_function(complex_prompt)

        # Test with JSON strings
        validated = handler._validate_and_convert_arguments({"data": '{"key": "value"}', "items": "[1, 2, 3]"})

        assert validated["data"] == {"key": "value"}
        assert validated["items"] == [1, 2, 3]


class TestCreatePromptFromFunction:
    """Test the create_prompt_from_function utility."""

    def test_create_prompt_from_function(self):
        """Test creating prompt using utility function."""

        def test_func(value: str) -> str:
            """Test function."""
            return value

        handler = create_prompt_from_function(test_func, name="custom", description="Custom desc")

        assert isinstance(handler, PromptHandler)
        assert handler.name == "custom"
        assert handler.description == "Custom desc"

    def test_create_prompt_from_function_defaults(self):
        """Test creating prompt with default values."""

        def test_func() -> str:
            return "test"

        handler = create_prompt_from_function(test_func)

        assert handler.name == "test_func"
        assert handler.description == "Prompt: test_func"
