#!/usr/bin/env python3
"""Final tests to push coverage above 90%"""

from typing import Union

import orjson
import pytest


def test_is_pydantic_model_with_various_non_classes():
    """Test _is_pydantic_model with many non-class types to hit TypeError (lines 63-65)."""
    from chuk_mcp_server.types.parameters import _is_pydantic_model

    # Test with many different non-class types
    non_class_values = [
        None,
        "",
        "string",
        0,
        42,
        3.14,
        [],
        [1, 2, 3],
        {},
        {"key": "value"},
        (),
        (1, 2),
        set(),
        {1, 2},
        lambda x: x,
        True,
        False,
    ]

    for value in non_class_values:
        result = _is_pydantic_model(value)
        assert result is False, f"Expected False for {value!r}"


def test_union_three_same_type():
    """Test Union[int, int, int] to hit line 156."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Union with 3 identical types
    param = ToolParameter.from_annotation("triple_int", Union[int, int, int])
    assert param.type == "integer"

    # Union with 3 identical bool types
    param_bool = ToolParameter.from_annotation("triple_bool", Union[bool, bool, bool])
    assert param_bool.type == "boolean"


def test_infer_union_four_same_type():
    """Test infer_type with Union[str, str, str, str] to hit line 418."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Union with 4 identical types
    result = infer_type_from_annotation(Union[str, str, str, str])
    assert result == "string"

    # Union with 4 identical float types
    result_float = infer_type_from_annotation(Union[float, float, float, float])
    assert result_float == "number"


def test_infer_type_with_bare_object():
    """Test infer_type with plain object to hit line 460."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Plain object instance (not a class)
    class EmptyClass:
        pass

    obj = EmptyClass()

    # Should default to string
    result = infer_type_from_annotation(type(obj))
    assert result == "string"


def test_pydantic_simple_model_direct():
    """Test simple Pydantic model direct annotation to hit lines 258-262."""
    try:
        from pydantic import BaseModel

        class VerySimpleModel(BaseModel):
            x: int

        from chuk_mcp_server.types.parameters import ToolParameter

        # Direct, non-Union, non-list annotation
        param = ToolParameter.from_annotation("simple", VerySimpleModel)
        assert param.type == "object"
        assert param.pydantic_model is VerySimpleModel
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_schema_extraction_simple():
    """Test Pydantic schema extraction for simple model to hit lines 300-311."""
    try:
        from pydantic import BaseModel

        class BasicModel(BaseModel):
            name: str
            value: int

        from chuk_mcp_server.types.parameters import ToolParameter

        param = ToolParameter(name="basic", type="object", pydantic_model=BasicModel)
        schema = param.to_json_schema()

        assert schema["type"] == "object"
        # Pydantic v2 should include schema info
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_schema_with_references():
    """Test Pydantic schema with nested references to hit lines 306-308."""
    try:
        from pydantic import BaseModel

        class Inner(BaseModel):
            value: str

        class Outer(BaseModel):
            inner: Inner
            name: str

        from chuk_mcp_server.types.parameters import ToolParameter

        param = ToolParameter(name="outer", type="object", pydantic_model=Outer)
        schema = param.to_json_schema()

        assert schema["type"] == "object"
        # May have $defs that get processed (lines 306-308)
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_array_items_simple():
    """Test Pydantic array items for simple model to hit lines 315-327."""
    try:
        from pydantic import BaseModel

        class Item(BaseModel):
            id: int
            name: str

        from chuk_mcp_server.types.parameters import ToolParameter

        param = ToolParameter(name="items", type="array", pydantic_items_model=Item)
        schema = param.to_json_schema()

        assert schema["type"] == "array"
        assert "items" in schema
        assert schema["items"]["type"] == "object"
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_array_items_with_nested():
    """Test Pydantic array items with nested model to hit lines 320-324."""
    try:
        from pydantic import BaseModel

        class Nested(BaseModel):
            field: str

        class ItemWithNested(BaseModel):
            id: int
            nested: Nested

        from chuk_mcp_server.types.parameters import ToolParameter

        param = ToolParameter(name="complex_items", type="array", pydantic_items_model=ItemWithNested)
        schema = param.to_json_schema()

        assert schema["type"] == "array"
        assert "items" in schema
        # May have $defs at top level (lines 320-324)
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_with_actual_model_validation():
    """Test with actual Pydantic model validation to ensure schema correctness."""
    try:
        from pydantic import BaseModel, Field

        class ValidatedModel(BaseModel):
            name: str = Field(..., min_length=1)
            age: int = Field(..., ge=0, le=150)

        from chuk_mcp_server.types.parameters import ToolParameter

        param = ToolParameter(name="validated", type="object", pydantic_model=ValidatedModel)
        schema = param.to_json_schema()

        assert schema["type"] == "object"

        # Test orjson serialization works
        schema_bytes = param.to_json_schema_bytes()
        assert isinstance(schema_bytes, bytes)

        # Deserialize and verify
        deserialized = orjson.loads(schema_bytes)
        assert deserialized["type"] == "object"
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_complete_workflow_with_pydantic():
    """Test complete workflow from function to schema with Pydantic models."""
    try:
        from pydantic import BaseModel

        class User(BaseModel):
            username: str
            email: str

        from chuk_mcp_server.types.parameters import build_input_schema, extract_parameters_from_function

        def create_user(user: User, notify: bool = True):
            """Create a user."""
            pass

        # Extract parameters
        params = extract_parameters_from_function(create_user)

        assert len(params) == 2
        assert params[0].name == "user"
        assert params[0].type == "object"
        assert params[0].pydantic_model is User

        # Build schema
        schema = build_input_schema(params)

        assert schema["type"] == "object"
        assert "user" in schema["properties"]
        assert "notify" in schema["properties"]
    except ImportError:
        pytest.skip("Pydantic not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
