#!/usr/bin/env python3
"""Extended tests for parameters module to improve coverage."""

import inspect
import typing
from typing import Any, Literal, Optional, Union

import orjson

from chuk_mcp_server.types.parameters import (
    ToolParameter,
    build_input_schema,
    build_input_schema_bytes,
    extract_parameters_from_function,
    infer_type_from_annotation,
)


class TestToolParameterExtended:
    """Extended tests for ToolParameter class."""

    def test_from_annotation_with_literal_type(self):
        """Test from_annotation with Literal type for enum values."""
        if hasattr(typing, "Literal"):
            param = ToolParameter.from_annotation(
                name="status", annotation=Literal["active", "inactive", "pending"], default=inspect.Parameter.empty
            )

            assert param.name == "status"
            assert param.type == "string"
            assert param.enum == ["active", "inactive", "pending"]
            assert param.required is True

    def test_from_annotation_with_old_typing_union(self):
        """Test from_annotation with Union type using __origin__ attribute."""
        from typing import Union

        # Create a type that only has __origin__, not __module__
        class OldUnion:
            __origin__ = Union
            __args__ = (str, type(None))

        param = ToolParameter.from_annotation(name="old_union", annotation=OldUnion(), default=inspect.Parameter.empty)

        assert param.type == "string"
        assert param.required is True

    def test_from_annotation_with_list_origin(self):
        """Test from_annotation with actual typing.List."""

        param = ToolParameter.from_annotation(name="typed_list", annotation=list[str], default=inspect.Parameter.empty)

        assert param.type == "array"

    def test_from_annotation_with_dict_origin(self):
        """Test from_annotation with actual typing.Dict."""

        param = ToolParameter.from_annotation(
            name="typed_dict", annotation=dict[str, Any], default=inspect.Parameter.empty
        )

        assert param.type == "object"

    def test_from_annotation_with_multiple_union_types(self):
        """Test from_annotation with Union of multiple non-None types."""
        param = ToolParameter.from_annotation(
            name="multi_union", annotation=Union[str, int, bool], default=inspect.Parameter.empty
        )

        # Should default to string for multi-type unions
        assert param.type == "string"

    def test_from_annotation_with_unknown_origin(self):
        """Test from_annotation with unknown origin type."""

        class CustomType:
            __origin__ = object  # Unknown origin

        param = ToolParameter.from_annotation(name="custom", annotation=CustomType(), default=inspect.Parameter.empty)

        # Should default to string for unknown types
        assert param.type == "string"


class TestInferTypeExtended:
    """Extended tests for infer_type_from_annotation function."""

    def test_infer_type_with_literal(self):
        """Test infer_type_from_annotation with Literal type."""
        if hasattr(typing, "Literal"):
            result = infer_type_from_annotation(Literal["a", "b", "c"])
            assert result == "string"

    def test_infer_type_with_old_typing_union(self):
        """Test infer_type_from_annotation with Union using __origin__."""
        from typing import Union

        class OldUnion:
            __origin__ = Union
            __args__ = (str, type(None))

        result = infer_type_from_annotation(OldUnion())
        assert result == "string"

    def test_infer_type_with_typing_list(self):
        """Test infer_type_from_annotation with typing.List."""

        result = infer_type_from_annotation(list[int])
        assert result == "array"

    def test_infer_type_with_typing_dict(self):
        """Test infer_type_from_annotation with typing.Dict."""

        result = infer_type_from_annotation(dict[str, str])
        assert result == "object"

    def test_infer_type_with_multi_union(self):
        """Test infer_type_from_annotation with multi-type Union."""
        from typing import Union

        class OldUnion:
            __origin__ = Union
            __args__ = (str, int, bool)

        result = infer_type_from_annotation(OldUnion())
        assert result == "string"

    def test_infer_type_with_unknown_origin(self):
        """Test infer_type_from_annotation with unknown origin."""

        class UnknownType:
            __origin__ = object

        result = infer_type_from_annotation(UnknownType())
        assert result == "string"

    def test_infer_type_with_no_module_no_origin(self):
        """Test infer_type_from_annotation with type having neither __module__ nor __origin__."""

        class SimpleType:
            pass

        result = infer_type_from_annotation(SimpleType)
        assert result == "string"  # Default fallback


class TestExtractParametersExtended:
    """Extended tests for extract_parameters_from_function."""

    def test_extract_parameters_basic(self):
        """Test extracting parameters from a simple function."""

        def simple_func(name: str, age: int = 25):
            pass

        params = extract_parameters_from_function(simple_func)

        assert len(params) == 2
        assert params[0].name == "name"
        assert params[0].type == "string"
        assert params[0].required is True
        assert params[1].name == "age"
        assert params[1].type == "integer"
        assert params[1].required is False
        assert params[1].default == 25

    def test_extract_parameters_skip_self(self):
        """Test that self parameter is skipped."""

        class TestClass:
            def method(self, value: str):
                pass

        instance = TestClass()
        params = extract_parameters_from_function(instance.method)

        assert len(params) == 1
        assert params[0].name == "value"

    def test_extract_parameters_with_optional(self):
        """Test extracting parameters with Optional types."""

        def optional_func(value: Optional[str] = None):
            pass

        params = extract_parameters_from_function(optional_func)

        assert len(params) == 1
        assert params[0].name == "value"
        assert params[0].type == "string"
        assert params[0].required is False
        assert params[0].default is None

    def test_extract_parameters_with_literal(self):
        """Test extracting parameters with Literal types."""
        if hasattr(typing, "Literal"):

            def literal_func(status: Literal["on", "off"]):
                pass

            params = extract_parameters_from_function(literal_func)

            assert len(params) == 1
            assert params[0].name == "status"
            assert params[0].type == "string"
            assert params[0].enum == ["on", "off"]

    def test_extract_parameters_with_containers(self):
        """Test extracting parameters with container types."""

        def container_func(items: list[str], data: dict[str, Any]):
            pass

        params = extract_parameters_from_function(container_func)

        assert len(params) == 2
        assert params[0].name == "items"
        assert params[0].type == "array"
        assert params[1].name == "data"
        assert params[1].type == "object"

    def test_extract_parameters_no_annotations(self):
        """Test extracting parameters without type annotations."""

        def no_annotations(value):
            pass

        params = extract_parameters_from_function(no_annotations)

        assert len(params) == 1
        assert params[0].name == "value"
        assert params[0].type == "string"  # Default type


class TestBuildInputSchemaExtended:
    """Extended tests for build_input_schema functions."""

    def test_build_input_schema_with_literal_enum(self):
        """Test building schema with Literal enum parameter."""
        if hasattr(typing, "Literal"):
            param = ToolParameter(name="mode", type="string", required=True, enum=["read", "write", "execute"])

            schema = build_input_schema([param])

            assert "properties" in schema
            assert "mode" in schema["properties"]
            assert schema["properties"]["mode"]["enum"] == ["read", "write", "execute"]

    def test_build_input_schema_bytes_with_enum(self):
        """Test building schema bytes with enum parameter."""
        param = ToolParameter(name="color", type="string", required=False, enum=["red", "green", "blue"], default="red")

        schema_bytes = build_input_schema_bytes([param])

        assert isinstance(schema_bytes, bytes)
        # Parse to verify content
        schema = orjson.loads(schema_bytes)
        assert "properties" in schema
        assert "color" in schema["properties"]
        assert schema["properties"]["color"]["enum"] == ["red", "green", "blue"]
        # Check that required field is either absent, None, or empty list
        assert "required" not in schema or schema["required"] in (None, [])

    def test_build_input_schema_mixed_parameters(self):
        """Test building schema with mixed parameter types."""
        params = [
            ToolParameter(name="required_str", type="string", required=True),
            ToolParameter(name="optional_int", type="integer", required=False, default=0),
            ToolParameter(name="array_param", type="array", required=True),
            ToolParameter(name="object_param", type="object", required=False),
        ]

        schema = build_input_schema(params)

        assert schema["type"] == "object"
        assert len(schema["properties"]) == 4
        assert schema["required"] == ["required_str", "array_param"]
        assert schema["properties"]["optional_int"]["type"] == "integer"
        assert schema["properties"]["array_param"]["type"] == "array"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_tool_parameter_with_none_type(self):
        """Test ToolParameter with None as type annotation."""
        param = ToolParameter.from_annotation(name="none_param", annotation=None, default=inspect.Parameter.empty)

        assert param.type == "string"  # Should default to string

    def test_extract_parameters_from_lambda(self):
        """Test extracting parameters from lambda function."""

        def add_func(x, y=10):
            return x + y

        params = extract_parameters_from_function(add_func)

        assert len(params) == 2
        assert params[0].name == "x"
        assert params[0].required is True
        assert params[1].name == "y"
        assert params[1].required is False
        assert params[1].default == 10

    def test_extract_parameters_from_empty_function(self):
        """Test extracting parameters from function with no parameters."""

        def no_params():
            pass

        params = extract_parameters_from_function(no_params)

        assert len(params) == 0

    def test_build_input_schema_empty_parameters(self):
        """Test building schema with empty parameter list."""
        schema = build_input_schema([])

        assert schema["type"] == "object"
        assert schema["properties"] == {}
        # May have None or empty required list
        if "required" in schema:
            assert schema["required"] in (None, [])

    def test_build_input_schema_bytes_empty_parameters(self):
        """Test building schema bytes with empty parameter list."""
        schema_bytes = build_input_schema_bytes([])

        assert isinstance(schema_bytes, bytes)
        schema = orjson.loads(schema_bytes)
        assert schema["type"] == "object"
        assert schema["properties"] == {}
        # May have None or empty required list
        if "required" in schema:
            assert schema["required"] in (None, [])
