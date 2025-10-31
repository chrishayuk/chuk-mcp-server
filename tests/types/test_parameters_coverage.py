#!/usr/bin/env python3
# tests/types/test_parameters_coverage.py
"""
Additional tests for parameters.py to achieve 90%+ coverage.
Focuses on testing uncovered lines and edge cases.
"""

from typing import Literal, Union

import pytest


def test_from_annotation_literal_type():
    """Test ToolParameter.from_annotation with Literal types (lines 97-99)."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Test Literal type for enum values
    param = ToolParameter.from_annotation("status", Literal["active", "inactive", "pending"])
    assert param.type == "string"
    assert param.enum == ["active", "inactive", "pending"]


def test_from_annotation_fallback_old_typing_union():
    """Test ToolParameter.from_annotation with old-style typing Union (lines 110-127)."""
    from unittest.mock import patch

    from chuk_mcp_server.types.parameters import ToolParameter

    # Create a mock annotation that has __origin__ but would fail typing.get_origin
    class OldStyleUnion:
        __origin__ = Union
        __args__ = (str, type(None))

    # Temporarily make typing.get_origin return None to force fallback
    with patch("typing.get_origin", return_value=None):
        param = ToolParameter.from_annotation("old_union", OldStyleUnion())
        # Should handle Optional-style union via the fallback path
        assert param.type == "string"


# NOTE: Tests for lines 119-122 (old-style list/dict fallback) are not included
# because they require Python <3.8 where typing.get_origin() doesn't exist.
# These are defensive fallback paths that are unreachable in Python 3.8+.


def test_from_annotation_fallback_old_typing_multi_union():
    """Test ToolParameter.from_annotation with multi-type Union (lines 117-118)."""
    from unittest.mock import patch

    from chuk_mcp_server.types.parameters import ToolParameter

    # Create multi-type union
    class OldStyleMultiUnion:
        __origin__ = Union
        __args__ = (str, int, float)

    # Temporarily make typing.get_origin return None to force fallback
    with patch("typing.get_origin", return_value=None):
        param = ToolParameter.from_annotation("multi_union", OldStyleMultiUnion())
        # Should default to string for complex unions
        assert param.type == "string"


def test_from_annotation_fallback_old_typing_unknown_origin():
    """Test ToolParameter.from_annotation with unknown origin (lines 123-124)."""
    from unittest.mock import patch

    from chuk_mcp_server.types.parameters import ToolParameter

    class CustomOrigin:
        pass

    class OldStyleUnknown:
        __origin__ = CustomOrigin
        __args__ = ()

    # Temporarily make typing.get_origin return None to force fallback
    with patch("typing.get_origin", return_value=None):
        param = ToolParameter.from_annotation("unknown", OldStyleUnknown())
        # Should default to string for unknown origins
        assert param.type == "string"


def test_from_annotation_no_origin_fallback():
    """Test ToolParameter.from_annotation with no __origin__ (lines 125-127)."""
    from unittest.mock import patch

    from chuk_mcp_server.types.parameters import ToolParameter

    # Create annotation without __origin__ that isn't in type_map
    class CustomType:
        pass

    # Temporarily make typing.get_origin return None and ensure no __origin__ attr
    with patch("typing.get_origin", return_value=None):
        param = ToolParameter.from_annotation("custom", CustomType)
        # Should default to string for unknown types
        assert param.type == "string"


def test_infer_type_from_annotation_old_typing_union():
    """Test infer_type_from_annotation with old-style Union (lines 244-261)."""
    from unittest.mock import patch

    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Test old-style Union with __origin__ attribute
    class OldStyleUnion:
        __origin__ = Union
        __args__ = (str, type(None))

    # Temporarily make typing.get_origin return None to force fallback
    with patch("typing.get_origin", return_value=None):
        result = infer_type_from_annotation(OldStyleUnion())
        assert result == "string"


def test_infer_type_from_annotation_old_typing_multi_union():
    """Test infer_type_from_annotation with old multi-type Union (lines 247-252)."""
    from unittest.mock import patch

    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    class OldStyleMultiUnion:
        __origin__ = Union
        __args__ = (str, int, float)

    # Temporarily make typing.get_origin return None to force fallback
    with patch("typing.get_origin", return_value=None):
        result = infer_type_from_annotation(OldStyleMultiUnion())
        assert result == "string"  # Defaults to string for complex unions


# NOTE: Test for line 253-254 (old-style list fallback) is not included
# because it requires Python <3.8 where typing.get_origin() doesn't exist.
# This is a defensive fallback path that is unreachable in Python 3.8+.


def test_infer_type_from_annotation_old_typing_dict():
    """Test infer_type_from_annotation with old-style dict (lines 255-256)."""

    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Use real typing.Dict for old-style annotation
    result = infer_type_from_annotation(dict[str, int])
    assert result == "object"


def test_infer_type_from_annotation_old_typing_unknown():
    """Test infer_type_from_annotation with unknown old-style type (lines 257-258)."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    class CustomType:
        pass

    class MockUnknownOld:
        __origin__ = CustomType
        __args__ = ()

    result = infer_type_from_annotation(MockUnknownOld())
    assert result == "string"  # Should default to string


def test_extract_parameters_from_function_with_self():
    """Test extract_parameters_from_function skips self (line 270-271)."""
    from chuk_mcp_server.types.parameters import extract_parameters_from_function

    class TestClass:
        def method(self, name: str, count: int = 5):
            return f"{name}: {count}"

    instance = TestClass()
    params = extract_parameters_from_function(instance.method)

    # Should skip 'self' parameter
    assert len(params) == 2
    assert params[0].name == "name"
    assert params[1].name == "count"


def test_extract_parameters_from_function_no_annotation():
    """Test extract_parameters_from_function with missing annotations."""
    from chuk_mcp_server.types.parameters import extract_parameters_from_function

    def func_no_annotation(arg1, arg2=10):
        return arg1 + arg2

    params = extract_parameters_from_function(func_no_annotation)

    # Should default to str type for missing annotations
    assert len(params) == 2
    assert params[0].type == "string"
    assert params[1].type == "string"
    assert params[1].default == 10


def test_build_input_schema_no_required():
    """Test build_input_schema when no parameters are required."""
    from chuk_mcp_server.types.parameters import ToolParameter, build_input_schema

    params = [
        ToolParameter("optional1", "string", required=False, default="default1"),
        ToolParameter("optional2", "integer", required=False, default=42),
    ]

    schema = build_input_schema(params)

    assert schema["type"] == "object"
    assert "properties" in schema
    # Required field should be None when no required params
    assert schema["required"] is None


def test_tool_parameter_to_json_schema_with_enum_and_default():
    """Test to_json_schema with both enum and default."""
    from chuk_mcp_server.types.parameters import ToolParameter

    param = ToolParameter(
        name="level",
        type="string",
        description="Log level",
        enum=["debug", "info", "warning", "error"],
        default="info",
    )

    schema = param.to_json_schema()

    assert schema["type"] == "string"
    assert schema["description"] == "Log level"
    assert schema["enum"] == ["debug", "info", "warning", "error"]
    assert schema["default"] == "info"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
