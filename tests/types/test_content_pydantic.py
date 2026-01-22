#!/usr/bin/env python3
"""Tests for Pydantic BaseModel handling in content.py to achieve 90%+ coverage."""

import orjson
import pytest


def test_format_content_with_pydantic_model():
    """Test format_content with Pydantic BaseModel to hit lines 33-35."""
    try:
        from pydantic import BaseModel

        class UserModel(BaseModel):
            name: str
            age: int
            email: str

        from chuk_mcp_server.types.content import format_content

        user = UserModel(name="Alice", age=30, email="alice@example.com")

        result = format_content(user)

        # Should format as JSON text content
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "text"

        # Should be JSON formatted with indentation
        text = result[0]["text"]
        assert "{\n" in text
        assert '"name": "Alice"' in text
        assert '"age": 30' in text
        assert '"email": "alice@example.com"' in text

        # Should be valid JSON
        parsed = orjson.loads(text)
        assert parsed["name"] == "Alice"
        assert parsed["age"] == 30
        assert parsed["email"] == "alice@example.com"
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_format_content_as_text_with_pydantic_model():
    """Test format_content_as_text with Pydantic BaseModel to hit line 51."""
    try:
        from pydantic import BaseModel

        class ProductModel(BaseModel):
            id: int
            name: str
            price: float
            in_stock: bool

        from chuk_mcp_server.types.content import format_content_as_text

        product = ProductModel(id=123, name="Widget", price=29.99, in_stock=True)

        result = format_content_as_text(product)

        # Should be JSON formatted
        assert "{\n" in result
        assert '"id": 123' in result
        assert '"name": "Widget"' in result
        assert '"price": 29.99' in result
        assert '"in_stock": true' in result

        # Should be valid JSON
        parsed = orjson.loads(result)
        assert parsed["id"] == 123
        assert parsed["name"] == "Widget"
        assert parsed["price"] == 29.99
        assert parsed["in_stock"] is True
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_format_content_as_json_with_pydantic_model():
    """Test format_content_as_json with Pydantic BaseModel to hit line 69."""
    try:
        from pydantic import BaseModel

        class ConfigModel(BaseModel):
            setting1: str
            setting2: int
            nested: dict[str, str]

        from chuk_mcp_server.types.content import format_content_as_json

        config = ConfigModel(setting1="enabled", setting2=42, nested={"key": "value"})

        result = format_content_as_json(config)

        # Should be JSON formatted with indentation
        assert "{\n" in result
        assert '"setting1": "enabled"' in result
        assert '"setting2": 42' in result

        # Should be valid JSON
        parsed = orjson.loads(result)
        assert parsed["setting1"] == "enabled"
        assert parsed["setting2"] == 42
        assert parsed["nested"]["key"] == "value"
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_model_in_list():
    """Test Pydantic model within a list."""
    try:
        from pydantic import BaseModel

        class ItemModel(BaseModel):
            id: int
            name: str

        from chuk_mcp_server.types.content import format_content

        items = [
            ItemModel(id=1, name="First"),
            "plain string",
            ItemModel(id=2, name="Second"),
        ]

        result = format_content(items)

        # Should have 3 formatted items
        assert len(result) == 3

        # First item should be formatted Pydantic model
        assert result[0]["type"] == "text"
        parsed_first = orjson.loads(result[0]["text"])
        assert parsed_first["id"] == 1
        assert parsed_first["name"] == "First"

        # Second item is plain string
        assert result[1]["text"] == "plain string"

        # Third item should be formatted Pydantic model
        parsed_third = orjson.loads(result[2]["text"])
        assert parsed_third["id"] == 2
        assert parsed_third["name"] == "Second"
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_nested_pydantic_models():
    """Test nested Pydantic models."""
    try:
        from pydantic import BaseModel

        class AddressModel(BaseModel):
            street: str
            city: str
            zip_code: str

        class PersonModel(BaseModel):
            name: str
            age: int
            address: AddressModel

        from chuk_mcp_server.types.content import format_content, format_content_as_json, format_content_as_text

        person = PersonModel(
            name="Bob", age=35, address=AddressModel(street="123 Main St", city="Springfield", zip_code="12345")
        )

        # Test format_content
        result = format_content(person)
        assert len(result) == 1
        parsed = orjson.loads(result[0]["text"])
        assert parsed["name"] == "Bob"
        assert parsed["address"]["city"] == "Springfield"

        # Test format_content_as_text
        text_result = format_content_as_text(person)
        parsed_text = orjson.loads(text_result)
        assert parsed_text["address"]["zip_code"] == "12345"

        # Test format_content_as_json
        json_result = format_content_as_json(person)
        parsed_json = orjson.loads(json_result)
        assert parsed_json["age"] == 35
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_pydantic_model_with_special_types():
    """Test Pydantic model with various field types."""
    try:
        from pydantic import BaseModel

        class ComplexModel(BaseModel):
            string_field: str
            int_field: int
            float_field: float
            bool_field: bool
            list_field: list[str]
            dict_field: dict[str, int]

        from chuk_mcp_server.types.content import format_content

        model = ComplexModel(
            string_field="test",
            int_field=42,
            float_field=3.14,
            bool_field=True,
            list_field=["a", "b", "c"],
            dict_field={"x": 1, "y": 2},
        )

        result = format_content(model)

        assert len(result) == 1
        parsed = orjson.loads(result[0]["text"])
        assert parsed["string_field"] == "test"
        assert parsed["int_field"] == 42
        assert parsed["float_field"] == 3.14
        assert parsed["bool_field"] is True
        assert parsed["list_field"] == ["a", "b", "c"]
        assert parsed["dict_field"] == {"x": 1, "y": 2}
    except ImportError:
        pytest.skip("Pydantic not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
