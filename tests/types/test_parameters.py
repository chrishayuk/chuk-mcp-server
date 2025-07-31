#!/usr/bin/env python3
# tests/types/test_parameters.py
"""
Unit tests for chuk_mcp_server.types.parameters module

Tests ToolParameter class, schema generation, and type inference.
"""

import pytest
import orjson
import inspect
from typing import Union, List, Dict, Optional
from dataclasses import dataclass


def test_tool_parameter_basic_creation():
    """Test basic ToolParameter creation."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    param = ToolParameter(
        name="test_param",
        type="string",
        description="A test parameter",
        required=True,
        default=None
    )
    
    assert param.name == "test_param"
    assert param.type == "string"
    assert param.description == "A test parameter"
    assert param.required is True
    assert param.default is None
    assert param.enum is None


def test_tool_parameter_with_enum():
    """Test ToolParameter with enum values."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    param = ToolParameter(
        name="choice_param",
        type="string",
        enum=["option1", "option2", "option3"]
    )
    
    assert param.enum == ["option1", "option2", "option3"]


def test_tool_parameter_from_annotation_basic_types():
    """Test creating ToolParameter from basic type annotations."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    # Test string type
    param_str = ToolParameter.from_annotation("name", str)
    assert param_str.type == "string"
    assert param_str.required is True
    
    # Test int type
    param_int = ToolParameter.from_annotation("count", int)
    assert param_int.type == "integer"
    assert param_int.required is True
    
    # Test float type
    param_float = ToolParameter.from_annotation("ratio", float)
    assert param_float.type == "number"
    assert param_float.required is True
    
    # Test bool type
    param_bool = ToolParameter.from_annotation("enabled", bool)
    assert param_bool.type == "boolean"
    assert param_bool.required is True
    
    # Test list type
    param_list = ToolParameter.from_annotation("items", list)
    assert param_list.type == "array"
    assert param_list.required is True
    
    # Test dict type
    param_dict = ToolParameter.from_annotation("config", dict)
    assert param_dict.type == "object"
    assert param_dict.required is True


def test_tool_parameter_from_annotation_with_defaults():
    """Test ToolParameter creation with default values."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    # Test with default value
    param = ToolParameter.from_annotation("timeout", int, default=30)
    assert param.type == "integer"
    assert param.required is False
    assert param.default == 30
    
    # Test with None default
    param_none = ToolParameter.from_annotation("optional", str, default=None)
    assert param_none.type == "string"
    assert param_none.required is False
    assert param_none.default is None


def test_tool_parameter_from_annotation_optional_types():
    """Test ToolParameter creation with Optional types."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    # Test Optional[str]
    param_optional_str = ToolParameter.from_annotation("maybe_name", Optional[str])
    assert param_optional_str.type == "string"
    
    # Test Optional[int]
    param_optional_int = ToolParameter.from_annotation("maybe_count", Optional[int])
    assert param_optional_int.type == "integer"


def test_tool_parameter_from_annotation_union_types():
    """Test ToolParameter creation with Union types."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    # Test Union[str, int] -> defaults to string
    param_union = ToolParameter.from_annotation("flexible", Union[str, int])
    assert param_union.type == "string"
    
    # Test Union with None (same as Optional)
    param_union_none = ToolParameter.from_annotation("maybe", Union[str, None])
    assert param_union_none.type == "string"


def test_tool_parameter_from_annotation_generic_types():
    """Test ToolParameter creation with generic types."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    # Test List[str]
    param_list_str = ToolParameter.from_annotation("names", List[str])
    assert param_list_str.type == "array"
    
    # Test Dict[str, int]
    param_dict_str_int = ToolParameter.from_annotation("mapping", Dict[str, int])
    assert param_dict_str_int.type == "object"


def test_tool_parameter_to_json_schema():
    """Test JSON schema generation from ToolParameter."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    # Test basic schema
    param = ToolParameter(
        name="test_param",
        type="string",
        description="A test parameter"
    )
    
    schema = param.to_json_schema()
    assert schema["type"] == "string"
    assert schema["description"] == "A test parameter"
    
    # Test schema with enum
    param_enum = ToolParameter(
        name="choice",
        type="string",
        enum=["a", "b", "c"]
    )
    
    schema_enum = param_enum.to_json_schema()
    assert schema_enum["type"] == "string"
    assert schema_enum["enum"] == ["a", "b", "c"]
    
    # Test schema with default
    param_default = ToolParameter(
        name="optional",
        type="integer",
        default=42
    )
    
    schema_default = param_default.to_json_schema()
    assert schema_default["type"] == "integer"
    assert schema_default["default"] == 42


def test_tool_parameter_to_json_schema_bytes():
    """Test orjson serialization of schema."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    param = ToolParameter(
        name="test",
        type="string"
    )
    
    schema_bytes = param.to_json_schema_bytes()
    assert isinstance(schema_bytes, bytes)
    
    # Test that it can be deserialized
    schema = orjson.loads(schema_bytes)
    assert schema["type"] == "string"


def test_tool_parameter_schema_caching():
    """Test that schema bytes are cached properly."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    param = ToolParameter(
        name="test",
        type="string"
    )
    
    # First call should cache
    schema_bytes1 = param.to_json_schema_bytes()
    
    # Second call should return cached version
    schema_bytes2 = param.to_json_schema_bytes()
    
    # Should be the same object (cached)
    assert schema_bytes1 is schema_bytes2
    
    # Test cache invalidation
    param.invalidate_cache()
    schema_bytes3 = param.to_json_schema_bytes()
    
    # Should be different object after invalidation
    assert schema_bytes1 is not schema_bytes3
    
    # But content should be the same
    assert schema_bytes1 == schema_bytes3


def test_build_input_schema():
    """Test building input schema from parameters list."""
    from chuk_mcp_server.types.parameters import ToolParameter, build_input_schema
    
    params = [
        ToolParameter("name", "string", required=True),
        ToolParameter("count", "integer", required=True),
        ToolParameter("enabled", "boolean", required=False, default=True)
    ]
    
    schema = build_input_schema(params)
    
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "required" in schema
    
    # Check properties
    assert "name" in schema["properties"]
    assert "count" in schema["properties"]
    assert "enabled" in schema["properties"]
    
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["count"]["type"] == "integer"
    assert schema["properties"]["enabled"]["type"] == "boolean"
    
    # Check required fields
    assert "name" in schema["required"]
    assert "count" in schema["required"]
    assert "enabled" not in schema["required"]


def test_build_input_schema_bytes():
    """Test orjson serialization of input schema."""
    from chuk_mcp_server.types.parameters import ToolParameter, build_input_schema_bytes
    
    params = [
        ToolParameter("name", "string", required=True)
    ]
    
    schema_bytes = build_input_schema_bytes(params)
    assert isinstance(schema_bytes, bytes)
    
    # Test that it can be deserialized
    schema = orjson.loads(schema_bytes)
    assert schema["type"] == "object"
    assert "name" in schema["properties"]


def test_infer_type_from_annotation():
    """Test type inference utility function."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation
    
    # Test basic types
    assert infer_type_from_annotation(str) == "string"
    assert infer_type_from_annotation(int) == "integer"
    assert infer_type_from_annotation(float) == "number"
    assert infer_type_from_annotation(bool) == "boolean"
    assert infer_type_from_annotation(list) == "array"
    assert infer_type_from_annotation(dict) == "object"
    
    # Test Optional types
    assert infer_type_from_annotation(Optional[str]) == "string"
    assert infer_type_from_annotation(Optional[int]) == "integer"
    
    # Test generic types
    assert infer_type_from_annotation(List[str]) == "array"
    assert infer_type_from_annotation(Dict[str, int]) == "object"
    
    # Test Union types
    assert infer_type_from_annotation(Union[str, int]) == "string"
    assert infer_type_from_annotation(Union[str, None]) == "string"


def test_pre_computed_schema_fragments():
    """Test that pre-computed schema fragments are working."""
    from chuk_mcp_server.types.parameters import _SCHEMA_FRAGMENTS, _BASE_SCHEMAS
    
    # Test schema fragments exist
    assert "string" in _SCHEMA_FRAGMENTS
    assert "integer" in _SCHEMA_FRAGMENTS
    assert "number" in _SCHEMA_FRAGMENTS
    assert "boolean" in _SCHEMA_FRAGMENTS
    assert "array" in _SCHEMA_FRAGMENTS
    assert "object" in _SCHEMA_FRAGMENTS
    
    # Test that they are orjson bytes
    for fragment in _SCHEMA_FRAGMENTS.values():
        assert isinstance(fragment, bytes)
        # Test they can be deserialized
        schema = orjson.loads(fragment)
        assert "type" in schema
    
    # Test base schemas exist
    assert len(_BASE_SCHEMAS) > 0
    
    # Test a specific base schema
    key = ("string", True, None)
    if key in _BASE_SCHEMAS:
        schema_bytes = _BASE_SCHEMAS[key]
        assert isinstance(schema_bytes, bytes)
        schema = orjson.loads(schema_bytes)
        assert schema["type"] == "string"


def test_tool_parameter_from_function_signature():
    """Test creating ToolParameter from real function signatures."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    def test_function(name: str, count: int = 10, enabled: bool = True, items: List[str] = None):
        pass
    
    sig = inspect.signature(test_function)
    
    # Test each parameter
    for param_name, param in sig.parameters.items():
        tool_param = ToolParameter.from_annotation(
            param_name,
            param.annotation if param.annotation != inspect.Parameter.empty else str,
            param.default
        )
        
        if param_name == "name":
            assert tool_param.type == "string"
            assert tool_param.required is True
        elif param_name == "count":
            assert tool_param.type == "integer"
            assert tool_param.required is False
            assert tool_param.default == 10
        elif param_name == "enabled":
            assert tool_param.type == "boolean"
            assert tool_param.required is False
            assert tool_param.default is True
        elif param_name == "items":
            assert tool_param.type == "array"
            assert tool_param.required is False
            assert tool_param.default is None


def test_tool_parameter_edge_cases():
    """Test edge cases for ToolParameter."""
    from chuk_mcp_server.types.parameters import ToolParameter
    
    # Test with no annotation (defaults to string)
    param_no_annotation = ToolParameter.from_annotation("param", inspect.Parameter.empty)
    assert param_no_annotation.type == "string"
    
    # Test with unknown type
    class CustomType:
        pass
    
    param_custom = ToolParameter.from_annotation("custom", CustomType)
    assert param_custom.type == "string"  # Should default to string
    
    # Test with complex Union
    param_complex_union = ToolParameter.from_annotation("complex", Union[str, int, float])
    assert param_complex_union.type == "string"  # Should default to string for complex unions


def test_module_exports():
    """Test that all expected exports are available."""
    from chuk_mcp_server.types import parameters
    
    assert hasattr(parameters, '__all__')
    assert isinstance(parameters.__all__, list)
    
    expected_exports = [
        "ToolParameter",
        "build_input_schema",
        "build_input_schema_bytes",
        "infer_type_from_annotation"
    ]
    
    for export in expected_exports:
        assert export in parameters.__all__
        assert hasattr(parameters, export)


if __name__ == "__main__":
    pytest.main([__file__])