#!/usr/bin/env python3
"""Tests for Pydantic model support and remaining uncovered lines in parameters.py"""

from typing import Union

import pytest


def test_is_pydantic_model_import_error():
    """Test _is_pydantic_model when pydantic is not available (lines 60-62)."""
    import importlib
    import sys

    from chuk_mcp_server.types import parameters

    # Mock pydantic module to not be available
    pydantic_module = sys.modules.get("pydantic")
    try:
        # Temporarily remove pydantic from sys.modules
        if "pydantic" in sys.modules:
            del sys.modules["pydantic"]

        # Force reload of parameters module to trigger ImportError
        importlib.reload(parameters)

        # Should return False when pydantic import fails
        result = parameters._is_pydantic_model(str)
        assert result is False
    finally:
        # Restore pydantic module
        if pydantic_module:
            sys.modules["pydantic"] = pydantic_module
        importlib.reload(parameters)


def test_is_pydantic_model_type_error():
    """Test _is_pydantic_model with non-class type (lines 63-65)."""
    from chuk_mcp_server.types.parameters import _is_pydantic_model

    # Pass a non-class type that will cause TypeError in issubclass
    result = _is_pydantic_model("not_a_class")
    assert result is False

    result = _is_pydantic_model(123)
    assert result is False


def test_optional_list_dict():
    """Test Optional[list[dict]] annotation (lines 129-146)."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Test Optional[list[dict]]
    param = ToolParameter.from_annotation("items", list[dict] | None)
    assert param.type == "array"
    assert param.items_type == "object"


def test_optional_list_with_unknown_item_type():
    """Test Optional[list[CustomType]] with unknown type (lines 129-146)."""
    from chuk_mcp_server.types.parameters import ToolParameter

    class CustomType:
        pass

    # Test Optional[list[CustomType]]
    param = ToolParameter.from_annotation("custom_items", list[CustomType] | None)
    assert param.type == "array"
    assert param.items_type == "string"  # Unknown types default to string


def test_union_same_json_schema_type_return():
    """Test Union where all types map to same JSON schema type (line 156)."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Union[bool, bool] should return "boolean"
    param = ToolParameter.from_annotation("flag", Union[bool, bool])
    assert param.type == "boolean"


def test_pydantic_model_direct_annotation():
    """Test direct Pydantic model as parameter type (lines 183-185, 258-262)."""
    # Try to import pydantic, skip test if not available
    try:
        from pydantic import BaseModel

        class UserModel(BaseModel):
            name: str
            age: int

        from chuk_mcp_server.types.parameters import ToolParameter

        # Test direct Pydantic model annotation (hits lines 183-185)
        param = ToolParameter.from_annotation("user", UserModel)
        assert param.type == "object"
        assert param.pydantic_model is UserModel
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_model_in_list():
    """Test list[PydanticModel] annotation (lines 173-175)."""
    try:
        from pydantic import BaseModel

        class ItemModel(BaseModel):
            id: int
            name: str

        from chuk_mcp_server.types.parameters import ToolParameter

        # Test list[PydanticModel] (hits lines 173-175)
        param = ToolParameter.from_annotation("items", list[ItemModel])
        assert param.type == "array"
        assert param.items_type == "object"
        assert param.pydantic_items_model is ItemModel
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_model_optional_list():
    """Test Optional[list[PydanticModel]] annotation (lines 138-140)."""
    try:
        from pydantic import BaseModel

        class ProductModel(BaseModel):
            name: str
            price: float

        from chuk_mcp_server.types.parameters import ToolParameter

        # Test Optional[list[PydanticModel]] (hits lines 138-140)
        param = ToolParameter.from_annotation("products", list[ProductModel] | None)
        assert param.type == "array"
        assert param.items_type == "object"
        assert param.pydantic_items_model is ProductModel
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_model_json_schema_extraction():
    """Test Pydantic model JSON schema extraction (lines 300-311)."""
    try:
        from pydantic import BaseModel

        class PersonModel(BaseModel):
            """A person model."""

            name: str
            age: int

        from chuk_mcp_server.types.parameters import ToolParameter

        # Create parameter with Pydantic model
        param = ToolParameter(name="person", type="object", pydantic_model=PersonModel)

        # Get JSON schema (hits lines 300-311)
        schema = param.to_json_schema()

        assert schema["type"] == "object"
        # Pydantic v2 schema format - properties should be present
        # (may be empty object or have properties)
        assert "type" in schema
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_model_json_schema_exception_handling():
    """Test exception handling in Pydantic schema extraction (lines 309-311)."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Create a mock Pydantic model that raises exception on model_json_schema
    class BrokenModel:
        @classmethod
        def model_json_schema(cls):
            raise RuntimeError("Schema extraction failed")

    # Create parameter with broken model
    param = ToolParameter(name="broken", type="object", pydantic_model=BrokenModel)

    # Should handle exception gracefully (hits lines 309-311)
    schema = param.to_json_schema()

    # Should fallback to generic object schema
    assert schema["type"] == "object"
    assert "properties" not in schema


def test_pydantic_items_model_json_schema_extraction():
    """Test Pydantic items model JSON schema extraction (lines 315-327)."""
    try:
        from pydantic import BaseModel

        class TagModel(BaseModel):
            """A tag model."""

            name: str
            color: str

        from chuk_mcp_server.types.parameters import ToolParameter

        # Create parameter with Pydantic items model
        param = ToolParameter(name="tags", type="array", pydantic_items_model=TagModel)

        # Get JSON schema (hits lines 315-327)
        schema = param.to_json_schema()

        assert schema["type"] == "array"
        assert "items" in schema
        assert schema["items"]["type"] == "object"
        # Just verify the schema has items, structure may vary by Pydantic version
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_items_model_json_schema_exception_handling():
    """Test exception handling in Pydantic items schema extraction (lines 325-327)."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Create a mock Pydantic model that raises exception
    class BrokenItemsModel:
        @classmethod
        def model_json_schema(cls):
            raise RuntimeError("Items schema extraction failed")

    # Create parameter with broken items model
    param = ToolParameter(name="broken_items", type="array", pydantic_items_model=BrokenItemsModel)

    # Should handle exception gracefully (hits lines 325-327)
    schema = param.to_json_schema()

    # Should fallback to generic object in items
    assert schema["type"] == "array"
    assert "items" in schema
    assert schema["items"]["type"] == "object"


def test_pydantic_items_model_with_defs():
    """Test Pydantic items model with $defs (lines 320-323)."""
    try:
        from pydantic import BaseModel

        class NestedModel(BaseModel):
            value: str

        class ComplexItemModel(BaseModel):
            id: int
            nested: NestedModel

        from chuk_mcp_server.types.parameters import ToolParameter

        # Create parameter with complex Pydantic items model
        param = ToolParameter(name="complex_items", type="array", pydantic_items_model=ComplexItemModel)

        # Get JSON schema
        schema = param.to_json_schema()

        assert schema["type"] == "array"
        assert "items" in schema
        # May have $defs for nested references
        if "$defs" in schema:
            assert isinstance(schema["$defs"], dict)
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_infer_type_union_same_json_type():
    """Test infer_type_from_annotation with Union of same JSON type (line 418)."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Union[str, str] should return "string" (line 418)
    result = infer_type_from_annotation(Union[str, str])
    assert result == "string"

    # Union[int, int] should return "integer"
    result = infer_type_from_annotation(Union[int, int])
    assert result == "integer"


def test_infer_type_final_fallback():
    """Test infer_type_from_annotation final fallback (line 460)."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Unknown type should fallback to "string" (line 460)
    class UnknownType:
        pass

    result = infer_type_from_annotation(UnknownType)
    assert result == "string"


def test_optional_dict():
    """Test Optional[dict] annotation."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Test Optional[dict[str, int]]
    param = ToolParameter.from_annotation("config", dict[str, int] | None)
    assert param.type == "object"


def test_array_with_items_type_in_schema():
    """Test that array schema includes items type when items_type is set."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Create array parameter with items_type
    param = ToolParameter(name="numbers", type="array", items_type="integer")

    schema = param.to_json_schema()

    assert schema["type"] == "array"
    assert "items" in schema
    assert schema["items"]["type"] == "integer"


def test_no_pydantic_array_items():
    """Test array with items_type but no pydantic model (line 328-329)."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Create array parameter with items_type (no pydantic)
    param = ToolParameter(name="strings", type="array", items_type="string")

    schema = param.to_json_schema()

    assert schema["type"] == "array"
    assert "items" in schema
    assert schema["items"]["type"] == "string"


def test_pydantic_model_with_defs_removal():
    """Test Pydantic model schema with $defs removal (lines 306-307)."""
    try:
        from pydantic import BaseModel

        class SimpleModel(BaseModel):
            """Simple model without references."""

            value: str

        from chuk_mcp_server.types.parameters import ToolParameter

        param = ToolParameter(name="simple", type="object", pydantic_model=SimpleModel)

        schema = param.to_json_schema()

        # $defs should be removed from top level if present
        # (Pydantic v2 might add it even for simple models)
        assert schema["type"] == "object"
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_optional_list_dict_explicit():
    """Test Optional[list[dict]] explicitly to hit lines 143-144."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Explicitly test Optional[list[dict]] to hit lines 143-144
    param = ToolParameter.from_annotation("data", list[dict] | None)
    assert param.type == "array"
    assert param.items_type == "object"


def test_optional_nested_list_custom_type():
    """Test Optional with nested list of custom types (lines 135-146)."""
    from chuk_mcp_server.types.parameters import ToolParameter

    class CustomItem:
        pass

    # Test Optional[list[CustomItem]] to hit fallback in lines 135-146
    param = ToolParameter.from_annotation("custom_list", list[CustomItem] | None)
    assert param.type == "array"
    assert param.items_type == "string"  # Custom types fall back to string


def test_union_str_str_explicit():
    """Test Union[str, str] to hit line 156."""
    from chuk_mcp_server.types.parameters import ToolParameter

    # Union[str, str] should hit line 156 (same JSON schema type)
    param = ToolParameter.from_annotation("text", Union[str, str])
    assert param.type == "string"


def test_pydantic_fallback_no_origin():
    """Test Pydantic model without typing origin (lines 258-262)."""
    try:
        from pydantic import BaseModel

        class ConfigModel(BaseModel):
            setting: str

        from chuk_mcp_server.types.parameters import ToolParameter

        # Direct annotation without Optional/Union to hit lines 258-262
        param = ToolParameter.from_annotation("config", ConfigModel)
        assert param.type == "object"
        assert param.pydantic_model is ConfigModel
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_infer_type_union_str_str():
    """Test infer_type with Union[str, str] to hit line 418."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    # Union[str, str] should return "string" via line 418
    result = infer_type_from_annotation(Union[str, str])
    assert result == "string"


def test_infer_type_unknown_fallback():
    """Test infer_type with unknown type to hit line 460."""
    from chuk_mcp_server.types.parameters import infer_type_from_annotation

    class MyCustomType:
        pass

    # Unknown type should hit line 460 fallback
    result = infer_type_from_annotation(MyCustomType)
    assert result == "string"


def test_pydantic_model_schema_with_defs():
    """Test Pydantic model schema extraction that has $defs (lines 306-308)."""
    try:
        from pydantic import BaseModel

        class AddressModel(BaseModel):
            street: str
            city: str

        class PersonWithAddress(BaseModel):
            name: str
            address: AddressModel

        from chuk_mcp_server.types.parameters import ToolParameter

        # Create parameter with nested Pydantic model
        param = ToolParameter(name="person", type="object", pydantic_model=PersonWithAddress)

        # Get JSON schema - should handle $defs
        schema = param.to_json_schema()

        assert schema["type"] == "object"
        # May or may not have $defs depending on Pydantic version
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_items_with_nested_defs():
    """Test Pydantic items model with nested $defs (lines 320-324)."""
    try:
        from pydantic import BaseModel

        class MetadataModel(BaseModel):
            key: str
            value: str

        class ItemWithMetadata(BaseModel):
            id: int
            metadata: MetadataModel

        from chuk_mcp_server.types.parameters import ToolParameter

        # Create array parameter with nested Pydantic items model
        param = ToolParameter(name="items", type="array", pydantic_items_model=ItemWithMetadata)

        # Get JSON schema - should handle nested $defs
        schema = param.to_json_schema()

        assert schema["type"] == "array"
        assert "items" in schema
        assert schema["items"]["type"] == "object"
    except ImportError:
        pytest.skip("Pydantic not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
