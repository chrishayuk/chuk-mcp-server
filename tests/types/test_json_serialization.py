"""Test JSON serialization of capabilities to prevent regression of serialization bugs."""

import json

import orjson
import pytest

from chuk_mcp_server.types.base import ServerCapabilities
from chuk_mcp_server.types.capabilities import create_server_capabilities


def test_capabilities_json_dumps():
    """Test that capabilities can be serialized with standard json.dumps()."""
    capabilities = create_server_capabilities(
        tools=True, resources=True, prompts=True, logging=True, experimental={"feature": "test"}
    )

    # Get the model dump
    result = capabilities.model_dump()

    # Ensure it can be serialized with standard json
    json_str = json.dumps(result)
    assert isinstance(json_str, str)

    # Ensure it can be parsed back
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    assert "tools" in parsed
    assert "resources" in parsed
    assert parsed["tools"]["listChanged"] is True


def test_capabilities_orjson_dumps():
    """Test that capabilities can be serialized with orjson.dumps()."""
    capabilities = create_server_capabilities(tools=True, resources=False, prompts=True, logging=False)

    # Get the model dump
    result = capabilities.model_dump()

    # Ensure it can be serialized with orjson
    json_bytes = orjson.dumps(result)
    assert isinstance(json_bytes, bytes)

    # Ensure it can be parsed back
    parsed = orjson.loads(json_bytes)
    assert isinstance(parsed, dict)
    assert "tools" in parsed
    assert "prompts" in parsed
    assert "resources" not in parsed  # Should be filtered out when False
    assert "logging" not in parsed  # Should be filtered out when False


def test_capabilities_no_function_in_dump():
    """Test that model_dump output contains no function objects."""
    capabilities = create_server_capabilities(
        tools=True, resources=True, prompts=False, logging=False, experimental={"test": "value", "number": 123}
    )

    result = capabilities.model_dump()

    def check_no_functions(obj, path="root"):
        """Recursively check that no functions exist in the data structure."""
        if callable(obj):
            pytest.fail(f"Found callable object at {path}: {obj}")
        elif isinstance(obj, dict):
            for key, value in obj.items():
                check_no_functions(value, f"{path}.{key}")
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                check_no_functions(item, f"{path}[{i}]")

    check_no_functions(result)

    # Specifically check that 'model_dump' is not in the result
    assert "model_dump" not in str(result)
    assert "function" not in str(result).lower()


def test_capabilities_exclude_none_serialization():
    """Test serialization with exclude_none parameter."""
    capabilities = create_server_capabilities(tools=True, resources=False, prompts=False, logging=False)

    # Without exclude_none - should only have enabled features due to filtering
    result_normal = capabilities.model_dump()
    json_str_normal = json.dumps(result_normal)
    parsed_normal = json.loads(json_str_normal)

    # Only tools should be present since others are False
    assert "tools" in parsed_normal
    assert "resources" not in parsed_normal
    assert "prompts" not in parsed_normal
    assert "logging" not in parsed_normal

    # With exclude_none
    result_exclude = capabilities.model_dump(exclude_none=True)
    json_str_exclude = json.dumps(result_exclude)
    parsed_exclude = json.loads(json_str_exclude)

    assert "tools" in parsed_exclude


def test_capabilities_edge_case_serialization():
    """Test serialization edge cases."""
    # Empty experimental
    caps1 = create_server_capabilities(experimental={})
    result1 = caps1.model_dump()
    json.dumps(result1)  # Should not raise

    # None experimental
    caps2 = create_server_capabilities(experimental=None)
    result2 = caps2.model_dump()
    json.dumps(result2)  # Should not raise

    # Complex experimental
    caps3 = create_server_capabilities(
        experimental={"nested": {"deep": {"value": 123}}, "list": [1, 2, 3], "bool": True, "null": None}
    )
    result3 = caps3.model_dump()
    json_str3 = json.dumps(result3)
    parsed3 = json.loads(json_str3)
    assert parsed3["experimental"]["nested"]["deep"]["value"] == 123


def test_capabilities_protocol_serialization():
    """Test serialization as it would be used in the MCP protocol."""
    # Simulate how the protocol handler uses capabilities
    capabilities = create_server_capabilities(tools=True, resources=True, prompts=False, logging=False)

    # Simulate protocol response construction
    response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "Test Server", "version": "1.0.0"},
            "capabilities": capabilities.model_dump(exclude_none=True),
        },
    }

    # This should not raise any serialization errors
    json_str = json.dumps(response)
    assert isinstance(json_str, str)

    # Parse it back
    parsed = json.loads(json_str)
    assert parsed["result"]["capabilities"]["tools"]["listChanged"] is True
    assert parsed["result"]["capabilities"]["resources"]["listChanged"] is True

    # Ensure no functions leaked through
    assert "model_dump" not in json_str
    assert "<function" not in json_str


def test_capabilities_isinstance_check():
    """Ensure the returned object is still a ServerCapabilities instance for compatibility."""
    capabilities = create_server_capabilities()

    # This is critical for compatibility with existing code
    assert isinstance(capabilities, ServerCapabilities)

    # Should also have the expected methods
    assert hasattr(capabilities, "model_dump")
    assert callable(capabilities.model_dump)

    # Should have the expected attributes
    assert hasattr(capabilities, "tools")
    assert hasattr(capabilities, "resources")
