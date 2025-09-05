#!/usr/bin/env python3
# tests/types/test_content.py
"""
Unit tests for chuk_mcp_server.types.content module

Tests content formatting functions with orjson optimization.
"""

import orjson
import pytest


def test_format_content_string():
    """Test formatting string content."""
    from chuk_mcp_server.types.content import format_content

    result = format_content("Hello, world!")

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["type"] == "text"
    assert result[0]["text"] == "Hello, world!"


def test_format_content_dict():
    """Test formatting dictionary content."""
    from chuk_mcp_server.types.content import format_content

    test_dict = {"key": "value", "number": 42, "nested": {"inner": "data"}}
    result = format_content(test_dict)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["type"] == "text"

    # Should be JSON-formatted text
    text_content = result[0]["text"]
    assert "{\n" in text_content  # Should be indented
    assert '"key": "value"' in text_content
    assert '"number": 42' in text_content

    # Should be valid JSON
    parsed = orjson.loads(text_content)
    assert parsed == test_dict


def test_format_content_list():
    """Test formatting list content."""
    from chuk_mcp_server.types.content import format_content

    test_list = ["item1", "item2", {"nested": "object"}]
    result = format_content(test_list)

    # List should be flattened - each item formatted separately
    assert isinstance(result, list)
    assert len(result) == 3  # Three items in the list

    # First two should be text content
    assert result[0]["type"] == "text"
    assert result[0]["text"] == "item1"
    assert result[1]["type"] == "text"
    assert result[1]["text"] == "item2"

    # Third should be JSON-formatted object
    assert result[2]["type"] == "text"
    parsed = orjson.loads(result[2]["text"])
    assert parsed == {"nested": "object"}


def test_format_content_existing_content_objects():
    """Test formatting with existing content objects."""
    from chuk_mcp_server.types.base import create_text_content
    from chuk_mcp_server.types.content import format_content

    # Test with TextContent
    text_content = create_text_content("Existing text content")
    result = format_content(text_content)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["type"] == "text"
    assert result[0]["text"] == "Existing text content"


def test_format_content_mixed_list():
    """Test formatting list with mixed content types."""
    from chuk_mcp_server.types.base import create_text_content
    from chuk_mcp_server.types.content import format_content

    mixed_list = [
        "plain string",
        {"dict": "object"},
        create_text_content("text content object"),
        42,
        ["nested", "list"],
    ]

    result = format_content(mixed_list)

    assert isinstance(result, list)
    assert len(result) >= 5  # At least 5 items (nested list will be flattened)

    # Check some specific items
    assert any(item["text"] == "plain string" for item in result)
    assert any("dict" in item["text"] for item in result)
    assert any(item["text"] == "text content object" for item in result)
    assert any(item["text"] == "42" for item in result)


def test_format_content_fallback():
    """Test formatting fallback for unknown types."""
    from chuk_mcp_server.types.content import format_content

    class CustomObject:
        def __str__(self):
            return "custom object string"

    custom_obj = CustomObject()
    result = format_content(custom_obj)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["type"] == "text"
    assert result[0]["text"] == "custom object string"


def test_format_content_as_text_string():
    """Test format_content_as_text with string input."""
    from chuk_mcp_server.types.content import format_content_as_text

    result = format_content_as_text("Simple string")
    assert result == "Simple string"


def test_format_content_as_text_dict():
    """Test format_content_as_text with dictionary input."""
    from chuk_mcp_server.types.content import format_content_as_text

    test_dict = {"key": "value", "number": 42}
    result = format_content_as_text(test_dict)

    # Should be JSON string with indentation
    assert "{\n" in result
    assert '"key": "value"' in result
    assert '"number": 42' in result

    # Should be valid JSON
    parsed = orjson.loads(result)
    assert parsed == test_dict


def test_format_content_as_text_list():
    """Test format_content_as_text with list input."""
    from chuk_mcp_server.types.content import format_content_as_text

    test_list = ["item1", "item2", 42]
    result = format_content_as_text(test_list)

    # Should be JSON string
    parsed = orjson.loads(result)
    assert parsed == test_list


def test_format_content_as_text_other():
    """Test format_content_as_text with other types."""
    from chuk_mcp_server.types.content import format_content_as_text

    # Test with number
    assert format_content_as_text(42) == "42"

    # Test with boolean
    assert format_content_as_text(True) == "True"

    # Test with None
    assert format_content_as_text(None) == "None"


def test_format_content_as_json_string():
    """Test format_content_as_json with string input."""
    from chuk_mcp_server.types.content import format_content_as_json

    # Test with valid JSON string
    json_string = '{"key": "value"}'
    result = format_content_as_json(json_string)

    # Should be re-formatted with indentation
    assert "{\n" in result
    assert '"key": "value"' in result

    # Test with non-JSON string
    plain_string = "not json"
    result2 = format_content_as_json(plain_string)

    # Should be wrapped in quotes
    assert result2 == '"not json"'


def test_format_content_as_json_dict():
    """Test format_content_as_json with dictionary input."""
    from chuk_mcp_server.types.content import format_content_as_json

    test_dict = {"nested": {"key": "value"}, "array": [1, 2, 3]}
    result = format_content_as_json(test_dict)

    # Should be indented JSON
    assert "{\n" in result
    parsed = orjson.loads(result)
    assert parsed == test_dict


def test_format_content_as_json_other_types():
    """Test format_content_as_json with various types."""
    from chuk_mcp_server.types.content import format_content_as_json

    # Test with list
    test_list = [1, 2, {"key": "value"}]
    result = format_content_as_json(test_list)
    parsed = orjson.loads(result)
    assert parsed == test_list

    # Test with number
    result2 = format_content_as_json(42)
    assert result2 == "42"

    # Test with boolean
    result3 = format_content_as_json(True)
    assert result3 == "true"  # JSON boolean

    # Test with None
    result4 = format_content_as_json(None)
    assert result4 == "null"  # JSON null


def test_orjson_optimization():
    """Test that orjson is being used for performance."""
    from chuk_mcp_server.types.content import format_content_as_json

    # Create a large data structure
    large_data = {"items": list(range(1000)), "nested": {"deep": {"structure": ["a"] * 100}}}

    result = format_content_as_json(large_data)

    # Should be valid JSON (orjson produces valid JSON)
    parsed = orjson.loads(result)
    assert len(parsed["items"]) == 1000
    assert len(parsed["nested"]["deep"]["structure"]) == 100


def test_content_formatting_edge_cases():
    """Test edge cases in content formatting."""
    from chuk_mcp_server.types.content import format_content, format_content_as_json, format_content_as_text

    # Test with empty string
    assert format_content("") == [{"type": "text", "text": ""}]
    assert format_content_as_text("") == ""
    assert format_content_as_json("") == '""'

    # Test with empty dict
    empty_dict_result = format_content({})
    assert len(empty_dict_result) == 1
    assert empty_dict_result[0]["type"] == "text"
    parsed = orjson.loads(empty_dict_result[0]["text"])
    assert parsed == {}

    # Test with empty list
    empty_list_result = format_content([])
    assert empty_list_result == []  # Empty list should produce empty result

    # Test with special characters
    special_chars = "Special chars: àáâãäåæçèéêë 中文 🚀"
    result = format_content(special_chars)
    assert result[0]["text"] == special_chars


def test_content_type_consistency():
    """Test that content formatting produces consistent types."""
    from chuk_mcp_server.types.content import format_content

    test_inputs = ["string", {"dict": "value"}, ["list", "items"], 42, True, None]

    for input_data in test_inputs:
        result = format_content(input_data)

        # All results should be lists
        assert isinstance(result, list)

        # All items in results should have 'type' and 'text' fields
        for item in result:
            assert isinstance(item, dict)
            assert "type" in item
            assert "text" in item
            assert item["type"] == "text"
            assert isinstance(item["text"], str)


def test_module_exports():
    """Test that all expected exports are available."""
    from chuk_mcp_server.types import content

    assert hasattr(content, "__all__")
    assert isinstance(content.__all__, list)

    expected_exports = ["format_content", "format_content_as_text", "format_content_as_json"]

    for export in expected_exports:
        assert export in content.__all__
        assert hasattr(content, export)


def test_content_orjson_json_compatibility():
    """Test that orjson output is compatible with standard JSON."""
    import json

    from chuk_mcp_server.types.content import format_content_as_json

    test_data = {
        "string": "test",
        "number": 42,
        "boolean": True,
        "null": None,
        "array": [1, 2, 3],
        "object": {"nested": "value"},
    }

    orjson_result = format_content_as_json(test_data)

    # Should be parseable by standard json module
    parsed_by_json = json.loads(orjson_result)
    assert parsed_by_json == test_data

    # Should also be parseable by orjson
    parsed_by_orjson = orjson.loads(orjson_result)
    assert parsed_by_orjson == test_data


if __name__ == "__main__":
    pytest.main([__file__])
