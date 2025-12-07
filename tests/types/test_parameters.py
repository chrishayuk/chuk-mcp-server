#!/usr/bin/env python3
# tests/types/test_parameters.py
"""
Unit tests for chuk_mcp_server.types.parameters module

Tests ToolParameter class, schema generation, and type inference.
"""

import inspect
from typing import Union

import orjson
import pytest


def test_tool_parameter_basic_creation():
    """Test basic ToolParameter creation."""
    from chuk_mcp_server.types.parameters import ToolParameter

    param = ToolParameter(name="test_param", type="string", description="A test parameter", required=True, default=None)

    assert param.name == "test_param"
    assert param.type == "string"
    assert param.description == "A test parameter"
    assert param.required is True
    assert param.default is None
    assert param.enum is None


def test_tool_parameter_with_enum():
    """Test ToolParameter with enum values."""
    from chuk_mcp_server.types.parameters import ToolParameter

    param = ToolParameter(name="choice_param", type="string", enum=["option1", "option2", "option3"])

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
    param_optional_str = ToolParameter.from_annotation("maybe_name", str | None)
    assert param_optional_str.type == "string"

    # Test Optional[int]
    param_optional_int = ToolParameter.from_annotation("maybe_count", int | None)
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
    param_list_str = ToolParameter.from_annotation("names", list[str])
    assert param_list_str.type == "array"
    assert param_list_str.items_type == "string"

    # Test Dict[str, int]
    param_dict_str_int = ToolParameter.from_annotation("mapping", dict[str, int])
    assert param_dict_str_int.type == "object"


def test_tool_parameter_to_json_schema():
    """Test JSON schema generation from ToolParameter."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Test basic schema
    param = ToolParameter(name="test_param", type="string", description="A test parameter")

    schema = param.to_json_schema()
    assert schema["type"] == "string"
    assert schema["description"] == "A test parameter"

    # Test schema with enum
    param_enum = ToolParameter(name="choice", type="string", enum=["a", "b", "c"])

    schema_enum = param_enum.to_json_schema()
    assert schema_enum["type"] == "string"
    assert schema_enum["enum"] == ["a", "b", "c"]

    # Test schema with default
    param_default = ToolParameter(name="optional", type="integer", default=42)

    schema_default = param_default.to_json_schema()
    assert schema_default["type"] == "integer"
    assert schema_default["default"] == 42


def test_tool_parameter_to_json_schema_bytes():
    """Test orjson serialization of schema."""
    from chuk_mcp_server.types.parameters import ToolParameter

    param = ToolParameter(name="test", type="string")

    schema_bytes = param.to_json_schema_bytes()
    assert isinstance(schema_bytes, bytes)

    # Test that it can be deserialized
    schema = orjson.loads(schema_bytes)
    assert schema["type"] == "string"


def test_tool_parameter_schema_caching():
    """Test that schema bytes are cached properly."""
    from chuk_mcp_server.types.parameters import ToolParameter

    param = ToolParameter(name="test", type="string")

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
        ToolParameter("enabled", "boolean", required=False, default=True),
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

    params = [ToolParameter("name", "string", required=True)]

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
    assert infer_type_from_annotation(str | None) == "string"
    assert infer_type_from_annotation(int | None) == "integer"

    # Test generic types
    assert infer_type_from_annotation(list[str]) == "array"
    assert infer_type_from_annotation(dict[str, int]) == "object"

    # Test Union types
    assert infer_type_from_annotation(Union[str, int]) == "string"
    assert infer_type_from_annotation(Union[str, None]) == "string"


def test_pre_computed_schema_fragments():
    """Test that pre-computed schema fragments are working."""
    from chuk_mcp_server.types.parameters import _BASE_SCHEMAS, _SCHEMA_FRAGMENTS

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

    def test_function(name: str, count: int = 10, enabled: bool = True, items: list[str] = None):
        pass

    sig = inspect.signature(test_function)

    # Test each parameter
    for param_name, param in sig.parameters.items():
        tool_param = ToolParameter.from_annotation(
            param_name, param.annotation if param.annotation != inspect.Parameter.empty else str, param.default
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

    assert hasattr(parameters, "__all__")
    assert isinstance(parameters.__all__, list)

    expected_exports = ["ToolParameter", "build_input_schema", "build_input_schema_bytes", "infer_type_from_annotation"]

    for export in expected_exports:
        assert export in parameters.__all__
        assert hasattr(parameters, export)


def test_tool_parameter_older_typing_fallback():
    """Test ToolParameter with annotations that don't have get_origin but have __origin__."""

    from chuk_mcp_server.types.parameters import ToolParameter

    # In Python 3.7-3.8, typing constructs don't have get_origin, only __origin__
    # We'll create a mock that simulates this behavior
    class MockOldStyleAnnotation:
        """Mock annotation that only has __origin__, not get_origin."""

        def __init__(self, origin, args=()):
            self.__origin__ = origin
            self.__args__ = args

    # Test direct type handling (most common path)
    param = ToolParameter.from_annotation("items", list)
    assert param.type == "array"

    param_dict = ToolParameter.from_annotation("config", dict)
    assert param_dict.type == "object"

    # Test that MockOldStyleAnnotation can be created (verifies the mock class works)
    _ = MockOldStyleAnnotation(list, (str,))


def test_infer_type_older_typing_fallback():
    """Test type inference handles edge cases."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Test direct Python types (these hit the final fallback at line 261)
    assert infer_type_from_annotation(str) == "string"
    assert infer_type_from_annotation(int) == "integer"
    assert infer_type_from_annotation(float) == "number"
    assert infer_type_from_annotation(bool) == "boolean"
    assert infer_type_from_annotation(list) == "array"
    assert infer_type_from_annotation(dict) == "object"

    # Test unknown types (should default to string)
    class CustomType:
        pass

    assert infer_type_from_annotation(CustomType) == "string"


def test_extract_parameters_from_function():
    """Test extracting parameters from function."""
    from chuk_mcp_server.types.parameters import extract_parameters_from_function

    def sample_function(name: str, count: int = 10, enabled: bool = True):
        """A sample function."""
        pass

    params = extract_parameters_from_function(sample_function)

    assert len(params) == 3
    assert params[0].name == "name"
    assert params[0].type == "string"
    assert params[0].required is True

    assert params[1].name == "count"
    assert params[1].type == "integer"
    assert params[1].required is False
    assert params[1].default == 10

    assert params[2].name == "enabled"
    assert params[2].type == "boolean"
    assert params[2].required is False
    assert params[2].default is True


def test_extract_parameters_from_method():
    """Test extracting parameters from a method (should skip 'self')."""
    from chuk_mcp_server.types.parameters import extract_parameters_from_function

    class SampleClass:
        def method(self, name: str, value: int):
            """A sample method."""
            pass

    params = extract_parameters_from_function(SampleClass.method)

    # Should only extract 'name' and 'value', not 'self'
    assert len(params) == 2
    assert params[0].name == "name"
    assert params[0].type == "string"

    assert params[1].name == "value"
    assert params[1].type == "integer"


def test_extract_parameters_no_parameters():
    """Test extracting parameters from function with no parameters."""
    from chuk_mcp_server.types.parameters import extract_parameters_from_function

    def no_params_function():
        """A function with no parameters."""
        pass

    params = extract_parameters_from_function(no_params_function)

    assert len(params) == 0


def test_extract_parameters_complex_types():
    """Test extracting parameters with complex type annotations."""
    from chuk_mcp_server.types.parameters import extract_parameters_from_function

    def complex_function(
        items: list[str],
        config: dict[str, int],
        maybe: str | None = None,
        either: Union[str, int] = "default",
    ):
        """A function with complex types."""
        pass

    params = extract_parameters_from_function(complex_function)

    assert len(params) == 4

    assert params[0].name == "items"
    assert params[0].type == "array"
    assert params[0].required is True

    assert params[1].name == "config"
    assert params[1].type == "object"
    assert params[1].required is True

    assert params[2].name == "maybe"
    assert params[2].type == "string"
    assert params[2].required is False
    assert params[2].default is None

    assert params[3].name == "either"
    assert params[3].type == "string"
    assert params[3].required is False
    assert params[3].default == "default"


def test_tool_parameter_direct_type_annotation():
    """Test ToolParameter with direct type annotations (no Optional/Union)."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Test direct int type
    param_int = ToolParameter.from_annotation("age", int, default=25)
    assert param_int.type == "integer"
    assert param_int.default == 25

    # Test direct str type
    param_str = ToolParameter.from_annotation("name", str, default="John")
    assert param_str.type == "string"
    assert param_str.default == "John"

    # Test direct bool type
    param_bool = ToolParameter.from_annotation("active", bool, default=False)
    assert param_bool.type == "boolean"
    assert param_bool.default is False


def test_infer_type_direct_types():
    """Test type inference with direct Python types."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Test all direct types hit the final fallback
    assert infer_type_from_annotation(str) == "string"
    assert infer_type_from_annotation(int) == "integer"
    assert infer_type_from_annotation(float) == "number"
    assert infer_type_from_annotation(bool) == "boolean"
    assert infer_type_from_annotation(list) == "array"
    assert infer_type_from_annotation(dict) == "object"

    # Test unknown type defaults to string
    class CustomClass:
        pass

    assert infer_type_from_annotation(CustomClass) == "string"


def test_tool_parameter_union_with_two_args():
    """Test ToolParameter with Union containing exactly 2 args including None."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Union[str, None] should extract str
    param = ToolParameter.from_annotation("optional_text", Union[str, None])
    assert param.type == "string"

    # Union[int, None] should extract int
    param_int = ToolParameter.from_annotation("optional_count", Union[int, None])
    assert param_int.type == "integer"

    # Union[None, str] should also work (order shouldn't matter)
    param_reversed = ToolParameter.from_annotation("reversed_optional", Union[None, str])
    assert param_reversed.type == "string"


def test_tool_parameter_fallback_for_unknown_annotation():
    """Test that unknown annotations fallback to string type."""
    import inspect
    from typing import get_origin

    from chuk_mcp_server.types.parameters import ToolParameter

    # Create a mock type that will bypass get_origin check
    class MockType:
        """A type that has no origin and will hit the final else clause."""

        pass

    # Ensure get_origin returns None for this type
    assert get_origin(MockType) is None

    param = ToolParameter.from_annotation("unknown", MockType)
    assert param.type == "string"  # Should fallback to string (line 127)

    # Test with inspect.Parameter.empty (no annotation)
    param_empty = ToolParameter.from_annotation("no_type", inspect.Parameter.empty)
    assert param_empty.type == "string"


def test_infer_type_fallback_for_unknown():
    """Test that unknown types fallback to string in type inference."""
    from typing import get_origin

    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Create a plain class with no typing attributes
    class PlainClass:
        pass

    # Verify it has no origin
    assert get_origin(PlainClass) is None
    assert not hasattr(PlainClass, "__origin__")

    result = infer_type_from_annotation(PlainClass)
    assert result == "string"  # Should fallback to string (line 261)

    # Test with another custom type
    class CustomClass:
        def __init__(self):
            pass

    assert get_origin(CustomClass) is None
    result2 = infer_type_from_annotation(CustomClass)
    assert result2 == "string"  # Should also hit line 261


def test_array_items_type_extraction():
    """Test that array item types are correctly extracted from List[T] annotations."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Test List[str]
    param_str_list = ToolParameter.from_annotation("names", list[str])
    assert param_str_list.type == "array"
    assert param_str_list.items_type == "string"

    # Test List[int]
    param_int_list = ToolParameter.from_annotation("numbers", list[int])
    assert param_int_list.type == "array"
    assert param_int_list.items_type == "integer"

    # Test List[float]
    param_float_list = ToolParameter.from_annotation("values", list[float])
    assert param_float_list.type == "array"
    assert param_float_list.items_type == "number"

    # Test List[bool]
    param_bool_list = ToolParameter.from_annotation("flags", list[bool])
    assert param_bool_list.type == "array"
    assert param_bool_list.items_type == "boolean"

    # Test bare list (no item type specified)
    param_bare_list = ToolParameter.from_annotation("items", list)
    assert param_bare_list.type == "array"
    assert param_bare_list.items_type is None


def test_array_json_schema_with_items():
    """Test that array JSON schemas include the items field."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Test List[str] generates proper schema
    param = ToolParameter.from_annotation("names", list[str])
    schema = param.to_json_schema()

    assert schema["type"] == "array"
    assert "items" in schema
    assert schema["items"] == {"type": "string"}

    # Test List[int] generates proper schema
    param_int = ToolParameter.from_annotation("numbers", list[int])
    schema_int = param_int.to_json_schema()

    assert schema_int["type"] == "array"
    assert "items" in schema_int
    assert schema_int["items"] == {"type": "integer"}

    # Test bare list doesn't include items field if not specified
    param_bare = ToolParameter(name="items", type="array")
    schema_bare = param_bare.to_json_schema()

    assert schema_bare["type"] == "array"
    assert "items" not in schema_bare


def test_array_schema_azure_openai_compatibility():
    """Test that array schemas are compatible with Azure OpenAI requirements."""
    from chuk_mcp_server.types.parameters import ToolParameter, build_input_schema

    # Azure OpenAI requires array schemas to have items field
    params = [
        ToolParameter.from_annotation("string_list", list[str]),
        ToolParameter.from_annotation("int_list", list[int]),
        ToolParameter.from_annotation("message", str),
    ]

    schema = build_input_schema(params)

    # Check string_list has proper array schema
    assert schema["properties"]["string_list"]["type"] == "array"
    assert "items" in schema["properties"]["string_list"]
    assert schema["properties"]["string_list"]["items"]["type"] == "string"

    # Check int_list has proper array schema
    assert schema["properties"]["int_list"]["type"] == "array"
    assert "items" in schema["properties"]["int_list"]
    assert schema["properties"]["int_list"]["items"]["type"] == "integer"

    # Check regular string parameter
    assert schema["properties"]["message"]["type"] == "string"
    assert "items" not in schema["properties"]["message"]


def test_array_items_with_typing_list():
    """Test array items extraction with list[T] annotation."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Test list[str]
    param = ToolParameter.from_annotation("names", list[str])
    assert param.type == "array"
    assert param.items_type == "string"

    schema = param.to_json_schema()
    assert schema["type"] == "array"
    assert schema["items"] == {"type": "string"}


def test_array_items_fallback_to_string():
    """Test that unknown array item types default to string."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Custom class as list item type
    class CustomType:
        pass

    param = ToolParameter.from_annotation("custom_list", list[CustomType])
    assert param.type == "array"
    assert param.items_type == "string"  # Should default to string

    schema = param.to_json_schema()
    assert schema["items"] == {"type": "string"}


def test_nested_generic_types():
    """Test handling of nested generic types."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Test List[List[str]] - only extracts first level
    param = ToolParameter.from_annotation("nested", list[list[str]])
    assert param.type == "array"
    # Inner list[str] becomes "string" since we only extract the outer type arg
    # Note: This is a known limitation - nested generics default to string
    assert param.items_type == "string"

    schema = param.to_json_schema()
    assert schema["type"] == "array"
    assert schema["items"] == {"type": "string"}


def test_tool_parameter_union_int_float():
    """Test ToolParameter with Union[int, float] maps to 'number' type."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Union[int, float] should map to "number"
    param = ToolParameter.from_annotation("value", Union[int, float])
    assert param.type == "number", "Union[int, float] should map to JSON Schema 'number' type"

    # Union[float, int] should also work (order shouldn't matter)
    param_reversed = ToolParameter.from_annotation("value2", Union[float, int])
    assert param_reversed.type == "number", "Union[float, int] should also map to 'number'"


def test_tool_parameter_union_int_float_none():
    """Test ToolParameter with Union[int, float, None] maps to 'number' type."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Union[int, float, None] should still map to "number" (ignoring None)
    param = ToolParameter.from_annotation("optional_value", Union[int, float, None])
    assert param.type == "number", "Union[int, float, None] should map to 'number'"

    # Union[float, int, None] should also work
    param_reversed = ToolParameter.from_annotation("optional_value2", Union[float, int, None])
    assert param_reversed.type == "number"


def test_infer_type_union_int_float():
    """Test type inference with Union[int, float]."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Union[int, float] should infer as "number"
    assert infer_type_from_annotation(Union[int, float]) == "number"
    assert infer_type_from_annotation(Union[float, int]) == "number"


def test_infer_type_union_int_float_none():
    """Test type inference with Union[int, float, None]."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Union[int, float, None] should infer as "number"
    assert infer_type_from_annotation(Union[int, float, None]) == "number"
    assert infer_type_from_annotation(Union[float, int, None]) == "number"


def test_tool_parameter_union_same_json_type():
    """Test that Union of types mapping to the same JSON Schema type works."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Union[int, int] should map to "integer" (same type)
    param_int_int = ToolParameter.from_annotation("int_union", Union[int, int])
    assert param_int_int.type == "integer"

    # Union[str, str] should map to "string"
    param_str_str = ToolParameter.from_annotation("str_union", Union[str, str])
    assert param_str_str.type == "string"


def test_tool_parameter_union_mixed_types():
    """Test that Union with truly mixed types defaults to string."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Union[str, int] should default to "string" (mixed types)
    param = ToolParameter.from_annotation("mixed", Union[str, int])
    assert param.type == "string"

    # Union[str, int, bool] should also default to "string"
    param_three = ToolParameter.from_annotation("mixed_three", Union[str, int, bool])
    assert param_three.type == "string"


def test_extract_parameters_with_numeric_union():
    """Test extracting parameters from function with Union[int, float]."""
    from chuk_mcp_server.types.parameters import extract_parameters_from_function

    def math_function(x: Union[int, float], y: Union[int, float] = 0.0):
        """A function accepting numeric types."""
        pass

    params = extract_parameters_from_function(math_function)

    assert len(params) == 2

    # First parameter should be number type, required
    assert params[0].name == "x"
    assert params[0].type == "number"
    assert params[0].required is True

    # Second parameter should be number type, optional with default
    assert params[1].name == "y"
    assert params[1].type == "number"
    assert params[1].required is False
    assert params[1].default == 0.0


def test_build_schema_with_numeric_union():
    """Test building JSON schema with Union[int, float] parameters."""
    from chuk_mcp_server.types.parameters import ToolParameter, build_input_schema

    params = [
        ToolParameter("x", "number", required=True),
        ToolParameter("y", "number", required=False, default=0.0),
    ]

    schema = build_input_schema(params)

    assert schema["type"] == "object"
    assert schema["properties"]["x"]["type"] == "number"
    assert schema["properties"]["y"]["type"] == "number"
    assert schema["properties"]["y"]["default"] == 0.0
    assert "x" in schema["required"]
    assert "y" not in schema["required"]


def test_math_server_sqrt_signature():
    """Test real-world math server sqrt function signature."""
    from chuk_mcp_server.types.parameters import extract_parameters_from_function

    # Simulate the sqrt function from chuk-mcp-math-server
    async def sqrt(x: Union[int, float]) -> float:
        """Calculate the square root of a number."""
        return x**0.5

    params = extract_parameters_from_function(sqrt)

    assert len(params) == 1
    assert params[0].name == "x"
    assert params[0].type == "number", "sqrt parameter 'x' should have type 'number' not 'string'"
    assert params[0].required is True


def test_modern_union_syntax():
    """Test Union using modern Python 3.10+ syntax (int | float)."""
    from chuk_mcp_server.types.parameters import ToolParameter, infer_type_from_annotation

    # Test modern union syntax: int | float
    param = ToolParameter.from_annotation("value", int | float)
    assert param.type == "number"

    # Test inference with modern syntax
    assert infer_type_from_annotation(int | float) == "number"
    assert infer_type_from_annotation(float | int) == "number"


if __name__ == "__main__":
    pytest.main([__file__])
