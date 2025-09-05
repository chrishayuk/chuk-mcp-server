#!/usr/bin/env python3
# tests/types/test_serialization.py
"""
Unit tests for chuk_mcp_server.types.serialization module

Tests orjson optimization utilities for maximum performance.
"""

from unittest.mock import MagicMock

import orjson
import pytest


def create_mock_tool_handler(name: str, description: str = None) -> MagicMock:
    """Create a mock ToolHandler for testing."""
    mock_tool = MagicMock()
    mock_tool.name = name
    mock_tool.description = description or f"Mock tool: {name}"
    mock_tool.to_mcp_format.return_value = {
        "name": name,
        "description": mock_tool.description,
        "inputSchema": {"type": "object", "properties": {"param1": {"type": "string"}}},
    }
    mock_tool.to_mcp_bytes.return_value = orjson.dumps(mock_tool.to_mcp_format.return_value)
    return mock_tool


def create_mock_resource_handler(uri: str, name: str = None) -> MagicMock:
    """Create a mock ResourceHandler for testing."""
    mock_resource = MagicMock()
    mock_resource.uri = uri
    mock_resource.name = name or f"Mock resource: {uri}"
    mock_resource.to_mcp_format.return_value = {
        "uri": uri,
        "name": mock_resource.name,
        "description": f"Description for {uri}",
        "mimeType": "text/plain",
    }
    mock_resource.to_mcp_bytes.return_value = orjson.dumps(mock_resource.to_mcp_format.return_value)
    return mock_resource


def test_serialize_tools_list():
    """Test serializing tools list with orjson."""
    from chuk_mcp_server.types.serialization import serialize_tools_list

    # Create mock tools
    tool1 = create_mock_tool_handler("tool1", "First tool")
    tool2 = create_mock_tool_handler("tool2", "Second tool")
    tools = [tool1, tool2]

    result = serialize_tools_list(tools)

    # Should return bytes
    assert isinstance(result, bytes)

    # Should be valid JSON
    data = orjson.loads(result)
    assert isinstance(data, dict)
    assert "tools" in data
    assert len(data["tools"]) == 2

    # Check tool data
    assert data["tools"][0]["name"] == "tool1"
    assert data["tools"][0]["description"] == "First tool"
    assert data["tools"][1]["name"] == "tool2"
    assert data["tools"][1]["description"] == "Second tool"

    # Verify that to_mcp_format was called on each tool
    tool1.to_mcp_format.assert_called_once()
    tool2.to_mcp_format.assert_called_once()


def test_serialize_tools_list_empty():
    """Test serializing empty tools list."""
    from chuk_mcp_server.types.serialization import serialize_tools_list

    result = serialize_tools_list([])

    assert isinstance(result, bytes)
    data = orjson.loads(result)
    assert data == {"tools": []}


def test_serialize_resources_list():
    """Test serializing resources list with orjson."""
    from chuk_mcp_server.types.serialization import serialize_resources_list

    # Create mock resources
    resource1 = create_mock_resource_handler("test://resource1", "First Resource")
    resource2 = create_mock_resource_handler("test://resource2", "Second Resource")
    resources = [resource1, resource2]

    result = serialize_resources_list(resources)

    # Should return bytes
    assert isinstance(result, bytes)

    # Should be valid JSON
    data = orjson.loads(result)
    assert isinstance(data, dict)
    assert "resources" in data
    assert len(data["resources"]) == 2

    # Check resource data
    assert data["resources"][0]["uri"] == "test://resource1"
    assert data["resources"][0]["name"] == "First Resource"
    assert data["resources"][1]["uri"] == "test://resource2"
    assert data["resources"][1]["name"] == "Second Resource"

    # Verify that to_mcp_format was called on each resource
    resource1.to_mcp_format.assert_called_once()
    resource2.to_mcp_format.assert_called_once()


def test_serialize_resources_list_empty():
    """Test serializing empty resources list."""
    from chuk_mcp_server.types.serialization import serialize_resources_list

    result = serialize_resources_list([])

    assert isinstance(result, bytes)
    data = orjson.loads(result)
    assert data == {"resources": []}


def test_serialize_tools_list_from_bytes():
    """Test serializing tools list using pre-serialized bytes for maximum performance."""
    from chuk_mcp_server.types.serialization import serialize_tools_list_from_bytes

    # Create mock tools
    tool1 = create_mock_tool_handler("tool1")
    tool2 = create_mock_tool_handler("tool2")
    tools = [tool1, tool2]

    result = serialize_tools_list_from_bytes(tools)

    # Should return bytes
    assert isinstance(result, bytes)

    # Should be valid JSON
    data = orjson.loads(result)
    assert isinstance(data, dict)
    assert "tools" in data
    assert len(data["tools"]) == 2

    # Check that data matches expected format
    assert data["tools"][0]["name"] == "tool1"
    assert data["tools"][1]["name"] == "tool2"

    # Verify that to_mcp_bytes was called (performance optimization)
    tool1.to_mcp_bytes.assert_called_once()
    tool2.to_mcp_bytes.assert_called_once()


def test_serialize_mcp_response():
    """Test serializing MCP response data."""
    from chuk_mcp_server.types.serialization import serialize_mcp_response

    response_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"tools": [{"name": "test_tool", "description": "A test tool"}]},
    }

    result = serialize_mcp_response(response_data)

    # Should return bytes
    assert isinstance(result, bytes)

    # Should be valid JSON
    data = orjson.loads(result)
    assert data == response_data
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1


def test_deserialize_mcp_request():
    """Test deserializing MCP request data."""
    from chuk_mcp_server.types.serialization import deserialize_mcp_request

    request_data = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

    # Serialize then deserialize
    request_bytes = orjson.dumps(request_data)
    result = deserialize_mcp_request(request_bytes)

    # Should return original data
    assert isinstance(result, dict)
    assert result == request_data
    assert result["method"] == "tools/list"


def test_serialization_performance_with_large_data():
    """Test serialization performance with large datasets."""
    from chuk_mcp_server.types.serialization import serialize_tools_list

    # Create many mock tools
    tools = []
    for i in range(100):
        tool = create_mock_tool_handler(f"tool_{i}", f"Description for tool {i}")
        # Add complex schema to test performance
        tool.to_mcp_format.return_value = {
            "name": f"tool_{i}",
            "description": f"Description for tool {i}",
            "inputSchema": {
                "type": "object",
                "properties": {
                    f"param_{j}": {"type": "string", "description": f"Parameter {j}"}
                    for j in range(10)  # 10 parameters per tool
                },
                "required": [f"param_{j}" for j in range(5)],  # 5 required params
            },
        }
        tools.append(tool)

    result = serialize_tools_list(tools)

    # Should handle large data efficiently
    assert isinstance(result, bytes)
    data = orjson.loads(result)
    assert len(data["tools"]) == 100

    # Spot check some data
    assert data["tools"][0]["name"] == "tool_0"
    assert data["tools"][99]["name"] == "tool_99"
    assert len(data["tools"][0]["inputSchema"]["properties"]) == 10


def test_serialization_with_complex_data_types():
    """Test serialization with complex data types."""
    from chuk_mcp_server.types.serialization import serialize_mcp_response

    complex_response = {
        "jsonrpc": "2.0",
        "id": "complex_id",
        "result": {
            "content": [{"type": "text", "text": "Response with unicode: 🚀 中文 àáâãäåæçèéêë"}],
            "metadata": {
                "numbers": [1, 2, 3.14, -42],
                "booleans": [True, False],
                "null_value": None,
                "nested": {"deep": {"structure": ["a", "b", "c"]}},
            },
            "timestamp": 1234567890.123,
        },
    }

    result = serialize_mcp_response(complex_response)

    # Should handle complex data
    assert isinstance(result, bytes)
    data = orjson.loads(result)
    assert data == complex_response

    # Check specific complex elements
    assert "🚀" in data["result"]["content"][0]["text"]
    assert data["result"]["metadata"]["numbers"] == [1, 2, 3.14, -42]
    assert data["result"]["metadata"]["null_value"] is None


def test_serialization_error_handling():
    """Test error handling in serialization functions."""
    from chuk_mcp_server.types.serialization import deserialize_mcp_request

    # Test invalid JSON
    with pytest.raises(orjson.JSONDecodeError):
        deserialize_mcp_request(b"invalid json")

    # Test empty bytes
    with pytest.raises(orjson.JSONDecodeError):
        deserialize_mcp_request(b"")


def test_serialization_consistency():
    """Test that serialization is consistent and deterministic."""
    from chuk_mcp_server.types.serialization import serialize_mcp_response

    test_data = {"jsonrpc": "2.0", "id": 1, "result": {"test": "data"}}

    # Multiple serializations should produce identical results
    result1 = serialize_mcp_response(test_data)
    result2 = serialize_mcp_response(test_data)

    assert result1 == result2

    # Both should deserialize to same data
    data1 = orjson.loads(result1)
    data2 = orjson.loads(result2)
    assert data1 == data2 == test_data


def test_serialization_bytes_vs_string():
    """Test that serialization produces bytes, not strings."""
    from chuk_mcp_server.types.serialization import (
        serialize_mcp_response,
        serialize_resources_list,
        serialize_tools_list,
    )

    tool = create_mock_tool_handler("test_tool")
    resource = create_mock_resource_handler("test://resource")

    tools_result = serialize_tools_list([tool])
    resources_result = serialize_resources_list([resource])
    response_result = serialize_mcp_response({"test": "data"})

    # All should be bytes
    assert isinstance(tools_result, bytes)
    assert isinstance(resources_result, bytes)
    assert isinstance(response_result, bytes)

    # Should not be strings
    assert not isinstance(tools_result, str)
    assert not isinstance(resources_result, str)
    assert not isinstance(response_result, str)


def test_orjson_optimization_features():
    """Test that orjson-specific optimizations are working."""
    from chuk_mcp_server.types.serialization import serialize_mcp_response

    # Test data with features that benefit from orjson
    data_with_datetime_like = {
        "timestamp": 1704067200,  # Unix timestamp
        "large_number": 9223372036854775807,  # Large int
        "unicode": "🚀 Unicode test 中文",
        "float": 3.141592653589793,
    }

    result = serialize_mcp_response(data_with_datetime_like)

    # Should handle efficiently
    assert isinstance(result, bytes)
    parsed = orjson.loads(result)
    assert parsed == data_with_datetime_like


def test_module_exports():
    """Test that all expected exports are available."""
    from chuk_mcp_server.types import serialization

    assert hasattr(serialization, "__all__")
    assert isinstance(serialization.__all__, list)

    expected_exports = [
        "serialize_tools_list",
        "serialize_resources_list",
        "serialize_tools_list_from_bytes",
        "serialize_mcp_response",
        "deserialize_mcp_request",
    ]

    for export in expected_exports:
        assert export in serialization.__all__
        assert hasattr(serialization, export)


def test_serialization_with_mock_verification():
    """Test that mocks are called correctly in serialization functions."""
    from chuk_mcp_server.types.serialization import serialize_tools_list, serialize_tools_list_from_bytes

    tool1 = create_mock_tool_handler("verify_tool1")
    tool2 = create_mock_tool_handler("verify_tool2")
    tools = [tool1, tool2]

    # Test regular serialization
    serialize_tools_list(tools)

    # Each tool should have to_mcp_format called exactly once
    tool1.to_mcp_format.assert_called_once()
    tool2.to_mcp_format.assert_called_once()

    # Reset mocks
    tool1.reset_mock()
    tool2.reset_mock()

    # Test bytes serialization
    serialize_tools_list_from_bytes(tools)

    # Each tool should have to_mcp_bytes called exactly once
    tool1.to_mcp_bytes.assert_called_once()
    tool2.to_mcp_bytes.assert_called_once()

    # to_mcp_format should not be called in bytes version
    tool1.to_mcp_format.assert_not_called()
    tool2.to_mcp_format.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
