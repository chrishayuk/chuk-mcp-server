#!/usr/bin/env python3
"""Final targeted tests to achieve 90%+ coverage for parameters.py"""

from typing import Union

import pytest


def test_union_all_same_type_branch():
    """Test Union with all same types to hit line 156."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Create Union[int, int, int] to hit line 156
    param = ToolParameter.from_annotation("value", Union[int, int, int])
    assert param.type == "integer"


def test_infer_type_union_all_same():
    """Test infer_type with Union of all same type to hit line 418."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Union[bool, bool, bool] should hit line 418
    result = infer_type_from_annotation(Union[bool, bool, bool])
    assert result == "boolean"


def test_infer_type_unknown_type_fallback():
    """Test infer_type with completely unknown type to hit line 460."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Create a type with no __origin__ and not in type_map
    class CompletelyUnknownType:
        pass

    result = infer_type_from_annotation(CompletelyUnknownType)
    assert result == "string"


def test_optional_list_dict_non_none_fallback():
    """Test Optional[list[dict]] to hit lines 143-146."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # This should hit the non_none_origin == dict path
    param = ToolParameter.from_annotation("config_list", list[dict] | None)
    assert param.type == "array"
    assert param.items_type == "object"


def test_pydantic_model_direct_else_branch():
    """Test direct Pydantic model to hit lines 258-262 (final else branch)."""
    try:
        from pydantic import BaseModel

        # Create a simple Pydantic model
        class SimpleConfig(BaseModel):
            value: str

        from chuk_mcp_server.types.parameters import ToolParameter

        # Direct annotation (not Union, not list, etc.)
        param = ToolParameter.from_annotation("simple_config", SimpleConfig)
        assert param.type == "object"
        assert param.pydantic_model is SimpleConfig
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_schema_defs_removal():
    """Test Pydantic schema with $defs removal to hit lines 306-308."""
    try:
        from pydantic import BaseModel

        class InnerModel(BaseModel):
            data: str

        class OuterModel(BaseModel):
            inner: InnerModel

        from chuk_mcp_server.types.parameters import ToolParameter

        param = ToolParameter(name="outer", type="object", pydantic_model=OuterModel)
        schema = param.to_json_schema()

        # Should handle $defs properly
        assert schema["type"] == "object"
        # $defs might be removed from top level (lines 306-308)
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_items_defs_handling():
    """Test Pydantic items with $defs to hit lines 320-324."""
    try:
        from pydantic import BaseModel

        class ItemInner(BaseModel):
            name: str

        class ItemOuter(BaseModel):
            inner: ItemInner
            count: int

        from chuk_mcp_server.types.parameters import ToolParameter

        param = ToolParameter(name="items", type="array", pydantic_items_model=ItemOuter)
        schema = param.to_json_schema()

        # Should handle nested $defs (lines 320-324)
        assert schema["type"] == "array"
        assert "items" in schema
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_is_pydantic_model_with_non_class():
    """Test _is_pydantic_model with non-class to hit TypeError (lines 63-65)."""
    from chuk_mcp_server.types.parameters import _is_pydantic_model

    # Test with non-class types that will cause TypeError in issubclass
    assert _is_pydantic_model("string") is False
    assert _is_pydantic_model(123) is False
    assert _is_pydantic_model(None) is False
    assert _is_pydantic_model([1, 2, 3]) is False


def test_optional_union_with_non_none_dict():
    """Test Optional with dict to hit line 146."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Optional[dict[str, str]] should hit line 146
    param = ToolParameter.from_annotation("mapping", Union[dict[str, str], None])
    assert param.type == "object"


def test_list_without_typing_module():
    """Test list type directly to ensure no typing module dependency."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Plain list annotation
    param = ToolParameter.from_annotation("items", list)
    assert param.type == "array"
    assert param.items_type is None


def test_dict_without_typing_module():
    """Test dict type directly to ensure no typing module dependency."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Plain dict annotation
    param = ToolParameter.from_annotation("config", dict)
    assert param.type == "object"


def test_typing_get_args_with_list():
    """Test typing.get_args path with list[T]."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Explicitly use list[int] to hit typing.get_args path
    param = ToolParameter.from_annotation("numbers", list[int])
    assert param.type == "array"
    assert param.items_type == "integer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
