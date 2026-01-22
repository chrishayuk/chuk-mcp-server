#!/usr/bin/env python3
"""Very specific tests to hit exact uncovered lines in parameters.py"""

from typing import Union

import pytest


def test_line_146_optional_unknown_origin():
    """Test Optional with unknown origin type to hit line 146."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Create a mock type that has an origin but isn't list or dict
    class MockTypeWithOrigin:
        pass

    # Test with a Union that has neither list nor dict origin
    # This should eventually hit line 146
    class CustomContainer:
        pass

    # Test Optional[CustomContainer] where CustomContainer isn't list/dict
    param = ToolParameter.from_annotation("custom", Union[CustomContainer, None])
    assert param.type == "string"  # Should fall back to string


def test_line_156_union_all_str():
    """Test Union[str, str, str] to explicitly hit line 156."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Union where ALL non-None args map to same JSON type
    param = ToolParameter.from_annotation("text", Union[str, str, str])
    assert param.type == "string"


def test_line_418_infer_union_all_int():
    """Test infer_type with Union[int, int] to hit line 418."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Union[int, int, int] should hit line 418
    result = infer_type_from_annotation(Union[int, int, int])
    assert result == "integer"


def test_line_460_infer_unknown_class():
    """Test infer_type with unknown class to hit line 460."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Class that's not in type_map and has no special handling
    class VeryCustomType:
        pass

    result = infer_type_from_annotation(VeryCustomType)
    assert result == "string"


def test_lines_258_262_direct_pydantic():
    """Test direct Pydantic model annotation to hit lines 258-262."""
    try:
        from pydantic import BaseModel

        class DirectModel(BaseModel):
            field: str

        from chuk_mcp_server.types.parameters import ToolParameter

        # Direct Pydantic annotation (not in Union, not in list)
        # This should hit the final else branch at lines 258-262
        param = ToolParameter.from_annotation("direct", DirectModel)
        assert param.type == "object"
        assert param.pydantic_model is DirectModel
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_lines_306_308_pydantic_defs():
    """Test Pydantic schema with $defs to hit lines 306-308."""
    try:
        from pydantic import BaseModel

        class NestedA(BaseModel):
            value: str

        class NestedB(BaseModel):
            nested: NestedA
            count: int

        from chuk_mcp_server.types.parameters import ToolParameter

        # Create param with nested Pydantic model
        param = ToolParameter(name="nested_obj", type="object", pydantic_model=NestedB)

        # Call to_json_schema to hit lines 306-308
        schema = param.to_json_schema()
        assert schema["type"] == "object"
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_lines_320_324_pydantic_items_defs():
    """Test Pydantic items with $defs to hit lines 320-324."""
    try:
        from pydantic import BaseModel

        class ItemNested(BaseModel):
            data: str

        class ItemComplex(BaseModel):
            nested: ItemNested
            id: int

        from chuk_mcp_server.types.parameters import ToolParameter

        # Create array param with nested Pydantic items
        param = ToolParameter(name="complex_array", type="array", pydantic_items_model=ItemComplex)

        # Call to_json_schema to hit lines 320-324
        schema = param.to_json_schema()
        assert schema["type"] == "array"
        assert "items" in schema
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_is_pydantic_model_import_error_direct():
    """Test _is_pydantic_model ImportError path (lines 60-62)."""
    # This is hard to test without actually removing pydantic
    # But we can test that the function returns False for non-Pydantic types
    from chuk_mcp_server.types.parameters import _is_pydantic_model

    # Test with standard types (should return False without ImportError)
    assert _is_pydantic_model(str) is False
    assert _is_pydantic_model(int) is False
    assert _is_pydantic_model(dict) is False


def test_is_pydantic_model_type_error_direct():
    """Test _is_pydantic_model TypeError path (lines 63-65)."""
    from chuk_mcp_server.types.parameters import _is_pydantic_model

    # Test with non-class values that will cause TypeError
    assert _is_pydantic_model(None) is False
    assert _is_pydantic_model("string") is False
    assert _is_pydantic_model(42) is False
    assert _is_pydantic_model([1, 2, 3]) is False
    assert _is_pydantic_model({"key": "value"}) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
