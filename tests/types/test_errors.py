#!/usr/bin/env python3
# tests/types/test_errors.py
"""
Unit tests for chuk_mcp_server.types.errors module

Tests custom error classes and their functionality.
"""

import pytest


def test_parameter_validation_error_creation():
    """Test ParameterValidationError creation and properties."""
    from chuk_mcp_server.types.errors import ParameterValidationError
    
    error = ParameterValidationError(
        parameter="test_param",
        expected_type="string",
        received=42
    )
    
    # Test error message
    expected_message = "Invalid parameter 'test_param': expected string, got int"
    assert str(error) == expected_message
    
    # Test error data
    assert hasattr(error, 'data')
    assert error.data["parameter"] == "test_param"
    assert error.data["expected"] == "string"
    assert error.data["received"] == "int"


def test_parameter_validation_error_inheritance():
    """Test that ParameterValidationError inherits from ValidationError."""
    from chuk_mcp_server.types.errors import ParameterValidationError
    from chuk_mcp_server.types.base import ValidationError
    
    error = ParameterValidationError("param", "string", 123)
    
    assert isinstance(error, ValidationError)
    assert isinstance(error, Exception)


def test_parameter_validation_error_with_different_types():
    """Test ParameterValidationError with various received types."""
    from chuk_mcp_server.types.errors import ParameterValidationError
    
    # Test with different received types
    test_cases = [
        (None, "NoneType"),
        ([], "list"),
        ({}, "dict"),
        (True, "bool"),
        (3.14, "float"),
        ("string", "str")
    ]
    
    for received_value, expected_type_name in test_cases:
        error = ParameterValidationError("param", "string", received_value)
        assert error.data["received"] == expected_type_name


def test_tool_execution_error_creation():
    """Test ToolExecutionError creation and properties."""
    from chuk_mcp_server.types.errors import ToolExecutionError
    
    original_error = ValueError("Something went wrong")
    
    error = ToolExecutionError(
        tool_name="test_tool",
        error=original_error
    )
    
    # Test error message
    expected_message = "Tool 'test_tool' execution failed: Something went wrong"
    assert str(error) == expected_message
    
    # Test error data
    assert hasattr(error, 'data')
    assert error.data["tool"] == "test_tool"
    assert error.data["error_type"] == "ValueError"
    assert error.data["error_message"] == "Something went wrong"


def test_tool_execution_error_inheritance():
    """Test that ToolExecutionError inherits from MCPError."""
    from chuk_mcp_server.types.errors import ToolExecutionError
    from chuk_mcp_server.types.base import MCPError
    
    original_error = RuntimeError("Test error")
    error = ToolExecutionError("tool", original_error)
    
    assert isinstance(error, MCPError)
    assert isinstance(error, Exception)


def test_tool_execution_error_with_different_exceptions():
    """Test ToolExecutionError with various exception types."""
    from chuk_mcp_server.types.errors import ToolExecutionError
    
    # Test with different exception types
    test_cases = [
        (ValueError("value error"), "ValueError", "value error"),
        (TypeError("type error"), "TypeError", "type error"),
        (RuntimeError("runtime error"), "RuntimeError", "runtime error"),
        (KeyError("'missing_key'"), "KeyError", "'missing_key'"),
        (Exception("generic exception"), "Exception", "generic exception")
    ]
    
    for original_error, expected_type, expected_message in test_cases:
        error = ToolExecutionError("test_tool", original_error)
        
        assert error.data["error_type"] == expected_type
        assert error.data["error_message"] == expected_message
        assert f"Tool 'test_tool' execution failed: {expected_message}" in str(error)


def test_parameter_validation_error_with_none_received():
    """Test ParameterValidationError when None is received."""
    from chuk_mcp_server.types.errors import ParameterValidationError
    
    error = ParameterValidationError("required_param", "string", None)
    
    assert "expected string, got NoneType" in str(error)
    assert error.data["received"] == "NoneType"


def test_error_data_access():
    """Test that error data is accessible and correct."""
    from chuk_mcp_server.types.errors import ParameterValidationError, ToolExecutionError
    
    # Test ParameterValidationError data
    param_error = ParameterValidationError("test", "int", "wrong")
    assert param_error.data["parameter"] == "test"
    assert param_error.data["expected"] == "int"
    assert param_error.data["received"] == "str"
    
    # Test ToolExecutionError data
    original = ValueError("test error")
    tool_error = ToolExecutionError("my_tool", original)
    assert tool_error.data["tool"] == "my_tool"
    assert tool_error.data["error_type"] == "ValueError"
    assert tool_error.data["error_message"] == "test error"


def test_error_chaining():
    """Test that errors can be properly chained and traced."""
    from chuk_mcp_server.types.errors import ToolExecutionError
    
    # Create a chain of exceptions
    try:
        try:
            raise ValueError("Original error")
        except ValueError as e:
            raise RuntimeError("Wrapped error") from e
    except RuntimeError as e:
        tool_error = ToolExecutionError("test_tool", e)
        
        # The tool error should contain info about the immediate cause
        assert tool_error.data["error_type"] == "RuntimeError"
        assert tool_error.data["error_message"] == "Wrapped error"


def test_error_string_representation():
    """Test string representations of custom errors."""
    from chuk_mcp_server.types.errors import ParameterValidationError, ToolExecutionError
    
    # Test ParameterValidationError string
    param_error = ParameterValidationError("count", "integer", 3.14)
    error_str = str(param_error)
    assert "count" in error_str
    assert "integer" in error_str
    assert "float" in error_str
    
    # Test ToolExecutionError string
    original = ZeroDivisionError("division by zero")
    tool_error = ToolExecutionError("calculator", original)
    error_str = str(tool_error)
    assert "calculator" in error_str
    assert "division by zero" in error_str


def test_error_with_complex_received_types():
    """Test ParameterValidationError with complex received types."""
    from chuk_mcp_server.types.errors import ParameterValidationError
    
    # Test with custom class
    class CustomClass:
        pass
    
    custom_instance = CustomClass()
    error = ParameterValidationError("param", "string", custom_instance)
    assert error.data["received"] == "CustomClass"
    
    # Test with nested data structures
    complex_data = {"nested": [1, 2, {"deep": "value"}]}
    error2 = ParameterValidationError("param", "string", complex_data)
    assert error2.data["received"] == "dict"


def test_error_immutability():
    """Test that error data cannot be easily mutated."""
    from chuk_mcp_server.types.errors import ParameterValidationError
    
    error = ParameterValidationError("param", "string", 123)
    original_data = error.data.copy()
    
    # Try to modify data (this should not affect the original)
    error.data["parameter"] = "modified"
    
    # The error message should still contain the original parameter name
    assert "param" in str(error)


def test_errors_are_exceptions():
    """Test that custom errors can be raised and caught as exceptions."""
    from chuk_mcp_server.types.errors import ParameterValidationError, ToolExecutionError
    
    # Test ParameterValidationError
    with pytest.raises(ParameterValidationError) as exc_info:
        raise ParameterValidationError("test", "string", 42)
    
    assert exc_info.value.data["parameter"] == "test"
    
    # Test ToolExecutionError  
    with pytest.raises(ToolExecutionError) as exc_info:
        original = ValueError("test")
        raise ToolExecutionError("tool", original)
    
    assert exc_info.value.data["tool"] == "tool"
    
    # Test that they can be caught as base Exception
    with pytest.raises(Exception):
        raise ParameterValidationError("test", "string", 42)


def test_error_compatibility_with_base_classes():
    """Test that custom errors work with their base classes."""
    from chuk_mcp_server.types.errors import ParameterValidationError, ToolExecutionError
    from chuk_mcp_server.types.base import ValidationError, MCPError
    
    param_error = ParameterValidationError("test", "string", 42)
    tool_error = ToolExecutionError("tool", ValueError("test"))
    
    # Test isinstance checks
    assert isinstance(param_error, ValidationError)
    assert isinstance(param_error, Exception)
    assert isinstance(tool_error, MCPError)
    assert isinstance(tool_error, Exception)
    
    # Test that they can be caught by base class
    try:
        raise param_error
    except ValidationError as e:
        assert e is param_error
    
    try:
        raise tool_error
    except MCPError as e:
        assert e is tool_error


def test_module_exports():
    """Test that all expected exports are available."""
    from chuk_mcp_server.types import errors
    
    assert hasattr(errors, '__all__')
    assert isinstance(errors.__all__, list)
    
    expected_exports = [
        "ParameterValidationError",
        "ToolExecutionError"
    ]
    
    for export in expected_exports:
        assert export in errors.__all__
        assert hasattr(errors, export)


def test_error_creation_edge_cases():
    """Test error creation with edge cases."""
    from chuk_mcp_server.types.errors import ParameterValidationError, ToolExecutionError
    
    # Test with empty strings
    param_error = ParameterValidationError("", "", "")
    assert param_error.data["parameter"] == ""
    assert param_error.data["expected"] == ""
    assert param_error.data["received"] == "str"
    
    # Test with very long strings
    long_string = "x" * 1000
    param_error2 = ParameterValidationError(long_string, "string", 123)
    assert param_error2.data["parameter"] == long_string
    
    # Test ToolExecutionError with exception that has no message
    class SilentError(Exception):
        def __str__(self):
            return ""
    
    silent = SilentError()
    tool_error = ToolExecutionError("tool", silent)
    assert tool_error.data["error_message"] == ""
    assert tool_error.data["error_type"] == "SilentError"


if __name__ == "__main__":
    pytest.main([__file__])