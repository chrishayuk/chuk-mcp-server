#!/usr/bin/env python3
# tests/types/test_prompts_coverage.py
"""
Additional tests for prompts.py to achieve 90%+ coverage.
Focuses on edge cases, error paths, and uncovered lines.
"""

import pytest


def test_prompt_handler_from_function_with_enum_parameters():
    """Test PromptHandler.from_function with enum parameters (lines 90-91)."""
    from typing import Literal

    from chuk_mcp_server.types.prompts import PromptHandler

    def prompt_with_enum(level: Literal["low", "medium", "high"]) -> str:
        return f"Level: {level}"

    handler = PromptHandler.from_function(prompt_with_enum)

    # Check that enum was properly set in arguments
    assert len(handler.arguments) == 1
    assert handler.arguments[0]["name"] == "level"
    assert "enum" in handler.arguments[0]
    assert handler.arguments[0]["enum"] == ["low", "medium", "high"]


def test_prompt_handler_from_function_skips_self_parameter():
    """Test that self parameter is skipped (line 72-73)."""
    from chuk_mcp_server.types.prompts import PromptHandler

    class TestClass:
        def method_prompt(self, message: str) -> str:
            return f"Method: {message}"

    instance = TestClass()
    handler = PromptHandler.from_function(instance.method_prompt)

    # Should only have one parameter, not self
    assert len(handler.parameters) == 1
    assert handler.parameters[0].name == "message"


def test_prompt_handler_ensure_cached_formats():
    """Test _ensure_cached_formats is called properly (lines 116-122)."""
    from chuk_mcp_server.types.prompts import PromptHandler

    def simple_prompt() -> str:
        return "test"

    handler = PromptHandler.from_function(simple_prompt)

    # Clear caches
    handler._cached_mcp_format = None
    handler._cached_mcp_bytes = None

    # Call ensure cached formats
    handler._ensure_cached_formats()

    # Both should be populated
    assert handler._cached_mcp_format is not None
    assert handler._cached_mcp_bytes is not None


def test_prompt_handler_to_mcp_format_ensures_cache():
    """Test to_mcp_format calls _ensure_cached_formats when cache is None (line 141-142)."""
    from chuk_mcp_server.types.prompts import PromptHandler

    def test_prompt() -> str:
        return "test"

    handler = PromptHandler.from_function(test_prompt)

    # Manually clear cache
    handler._cached_mcp_format = None

    # This should trigger _ensure_cached_formats
    result = handler.to_mcp_format()

    assert result is not None
    assert handler._cached_mcp_format is not None


def test_prompt_handler_to_mcp_bytes_ensures_cache():
    """Test to_mcp_bytes calls _ensure_cached_formats when cache is None (line 148-149)."""
    from chuk_mcp_server.types.prompts import PromptHandler

    def test_prompt() -> str:
        return "test"

    handler = PromptHandler.from_function(test_prompt)

    # Manually clear cache
    handler._cached_mcp_bytes = None

    # This should trigger _ensure_cached_formats
    result = handler.to_mcp_bytes()

    assert result is not None
    assert handler._cached_mcp_bytes is not None


@pytest.mark.asyncio
async def test_prompt_handler_convert_type_integer_precision_loss():
    """Test _convert_type integer with precision loss (lines 189-200)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.prompts import PromptHandler

    handler = PromptHandler.from_function(lambda: None)
    param = ToolParameter(name="count", type="integer", required=True)

    # Test float with precision loss
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type(42.7, param)

    assert "precision loss" in str(exc_info.value).lower() or "cannot convert" in str(exc_info.value).lower()

    # Test string float with precision loss
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type("42.7", param)

    # Just check that error was raised and contains relevant text
    assert "cannot convert" in str(exc_info.value).lower() or "precision" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_prompt_handler_convert_type_integer_invalid_string():
    """Test _convert_type integer with invalid string (lines 202-204)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.prompts import PromptHandler

    handler = PromptHandler.from_function(lambda: None)
    param = ToolParameter(name="count", type="integer", required=True)

    # Test invalid string
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type("not_a_number", param)

    assert "Cannot convert string" in str(exc_info.value)


@pytest.mark.asyncio
async def test_prompt_handler_convert_type_number_error():
    """Test _convert_type number conversion error (lines 211-215)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.prompts import PromptHandler

    handler = PromptHandler.from_function(lambda: None)
    param = ToolParameter(name="ratio", type="number", required=True)

    # Test invalid string to number
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type("not_a_number", param)

    assert "Cannot convert string" in str(exc_info.value)


@pytest.mark.asyncio
async def test_prompt_handler_convert_type_boolean_empty_null():
    """Test _convert_type boolean with empty/null strings (lines 224-226)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.prompts import PromptHandler

    handler = PromptHandler.from_function(lambda: None)
    param = ToolParameter(name="enabled", type="boolean", required=False, default=True)

    # Test empty string uses default
    result1 = handler._convert_type("", param)
    assert result1 is True

    # Test "null" string uses default
    result2 = handler._convert_type("null", param)
    assert result2 is True

    # Test with no default
    param_no_default = ToolParameter(name="enabled", type="boolean", required=True)
    result3 = handler._convert_type("", param_no_default)
    assert result3 is False


@pytest.mark.asyncio
async def test_prompt_handler_convert_type_boolean_unrecognized():
    """Test _convert_type boolean with unrecognized string (lines 231-233)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.prompts import PromptHandler

    handler = PromptHandler.from_function(lambda: None)
    param = ToolParameter(name="enabled", type="boolean", required=True)

    # Test unrecognized string raises error
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type("maybe", param)

    assert "Cannot convert string" in str(exc_info.value)


@pytest.mark.asyncio
async def test_prompt_handler_convert_type_boolean_none():
    """Test _convert_type boolean with None value (lines 236-238)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.prompts import PromptHandler

    handler = PromptHandler.from_function(lambda: None)
    param = ToolParameter(name="enabled", type="boolean", required=False, default=True)

    # Test None returns False by default (line 238)
    result = handler._convert_type(None, param)
    assert result is False


@pytest.mark.asyncio
async def test_prompt_handler_convert_type_boolean_exception():
    """Test _convert_type boolean with conversion exception (lines 240-244)."""
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.prompts import PromptHandler

    handler = PromptHandler.from_function(lambda: None)
    param = ToolParameter(name="enabled", type="boolean", required=True)

    # Create an object that can't be converted to bool
    class UnconvertibleType:
        def __bool__(self):
            raise RuntimeError("Cannot convert")

    with pytest.raises(ValueError) as exc_info:
        handler._convert_type(UnconvertibleType(), param)

    assert "Cannot convert" in str(exc_info.value)


@pytest.mark.asyncio
async def test_prompt_handler_convert_type_enum_validation():
    """Test enum validation in execute path (lines 285-288).

    Note: Lines 285-288 contain enum validation code, but it's unreachable in practice
    because all type handlers (string, integer, etc.) return early. The enum check
    would only execute for unknown types. This test verifies the code exists but
    acknowledges it's currently dead code that should be refactored.
    """
    from chuk_mcp_server.types.parameters import ToolParameter
    from chuk_mcp_server.types.prompts import PromptHandler

    handler = PromptHandler.from_function(lambda: None)

    # Create a parameter with an unknown type to reach the enum check
    param = ToolParameter(name="level", type="unknown_type", required=True, enum=["low", "medium", "high"])

    # For unknown types, the code falls through to the enum check
    # Test valid enum value
    result = handler._convert_type("low", param)
    assert result == "low"

    # Test invalid enum value - should trigger the enum check at lines 285-286
    with pytest.raises(ValueError) as exc_info:
        handler._convert_type("invalid", param)

    assert "must be one of" in str(exc_info.value)


@pytest.mark.asyncio
async def test_prompt_handler_get_prompt_with_none_arguments():
    """Test get_prompt with None arguments (line 297)."""
    from chuk_mcp_server.types.prompts import PromptHandler

    def no_args_prompt() -> str:
        return "No arguments needed"

    handler = PromptHandler.from_function(no_args_prompt)

    # Call with None arguments
    result = await handler.get_prompt(None)
    assert result == "No arguments needed"


@pytest.mark.asyncio
async def test_prompt_handler_get_prompt_reraises_validation_error():
    """Test get_prompt re-raises ParameterValidationError (lines 307-309)."""
    from chuk_mcp_server.types.errors import ParameterValidationError
    from chuk_mcp_server.types.prompts import PromptHandler

    def typed_prompt(count: int) -> str:
        return f"Count: {count}"

    handler = PromptHandler.from_function(typed_prompt)

    # Should re-raise ParameterValidationError
    with pytest.raises(ParameterValidationError):
        await handler.get_prompt({"count": "not_a_number"})


@pytest.mark.asyncio
async def test_prompt_handler_get_prompt_wraps_other_errors():
    """Test get_prompt wraps other exceptions in MCPError (lines 310-312)."""
    from chuk_mcp_server.types.base import MCPError
    from chuk_mcp_server.types.prompts import PromptHandler

    def failing_prompt(value: str) -> str:
        raise RuntimeError("Handler failed")

    handler = PromptHandler.from_function(failing_prompt)

    # Should wrap in MCPError
    with pytest.raises(MCPError) as exc_info:
        await handler.get_prompt({"value": "test"})

    assert "Failed to generate prompt" in str(exc_info.value)
    assert exc_info.value.code == -32603


def test_prompt_handler_from_function_no_arguments():
    """Test PromptHandler with function that has no arguments."""
    from chuk_mcp_server.types.prompts import PromptHandler

    def no_args_prompt() -> str:
        """A prompt with no arguments."""
        return "Static prompt"

    handler = PromptHandler.from_function(no_args_prompt)

    # Should have no parameters and arguments should be None
    assert len(handler.parameters) == 0
    assert handler.arguments is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
