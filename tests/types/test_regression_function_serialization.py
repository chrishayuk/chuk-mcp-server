"""Regression test for the function serialization bug in capabilities.

This test specifically checks for the bug where model_dump was assigned
a function directly, causing JSON serialization to fail with:
"Type is not JSON serializable: function"
"""

import json

import orjson
import pytest

from chuk_mcp_server.types.capabilities import create_server_capabilities


def test_no_function_assignment_to_model_dump():
    """Regression test: ensure model_dump is never assigned a raw function.

    The original bug was that capabilities.model_dump was being assigned
    a function directly like: caps.model_dump = filtered_model_dump
    This caused JSON serialization to fail when the capabilities object
    was included in any serializable structure.
    """
    capabilities = create_server_capabilities(tools=True, resources=True)

    # The model_dump should be a bound method, not a raw function
    assert hasattr(capabilities, "model_dump")
    assert callable(capabilities.model_dump)

    # When we call model_dump, it should return a dict
    result = capabilities.model_dump()
    assert isinstance(result, dict)

    # The critical test: the result should NOT contain any functions
    # or references to model_dump itself
    result_str = str(result)
    assert "function" not in result_str.lower()
    assert "model_dump" not in result_str

    # Most importantly: JSON serialization should work
    try:
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
    except TypeError as e:
        if "not JSON serializable" in str(e) and "function" in str(e):
            pytest.fail(f"Regression detected: function serialization bug has returned! Error: {e}")
        else:
            raise


def test_protocol_response_serialization_regression():
    """Regression test: ensure the full protocol response can be serialized.

    This simulates the exact scenario where the bug was discovered:
    when the MCP protocol tried to serialize the initialization response.
    """
    capabilities = create_server_capabilities(tools=True, resources=True, prompts=False, logging=False)

    # Simulate the exact protocol response that was failing
    protocol_response = {
        "jsonrpc": "2.0",
        "id": "1",
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "Plan Registry", "version": "1.0.0", "title": "Plan Registry MCP Server"},
            "capabilities": capabilities.model_dump(exclude_none=True),
        },
    }

    # This was the exact line that was failing with the bug
    try:
        # Test with standard json
        json_str = json.dumps(protocol_response)
        assert isinstance(json_str, str)

        # Test with orjson (which is used by the actual server)
        orjson_bytes = orjson.dumps(protocol_response)
        assert isinstance(orjson_bytes, bytes)

    except TypeError as e:
        if "Type is not JSON serializable: function" in str(e):
            pytest.fail(f"Regression detected: The exact bug has returned! Error: {e}")
        elif "not JSON serializable" in str(e) and "function" in str(e):
            pytest.fail(f"Regression detected: function serialization issue! Error: {e}")
        else:
            raise


def test_capabilities_object_not_in_dump():
    """Ensure the capabilities object itself doesn't leak into model_dump output.

    A variation of the bug could occur if the capabilities object or any
    of its methods accidentally get included in the model_dump output.
    """
    capabilities = create_server_capabilities(
        tools=True, resources=True, prompts=True, logging=True, experimental={"test": "value"}
    )

    result = capabilities.model_dump()

    # Check that the result doesn't contain the capabilities object itself
    def check_no_capabilities_object(obj, path="root"):
        """Recursively check for capabilities object references."""
        if obj is capabilities:
            pytest.fail(f"Found capabilities object reference at {path}")
        elif hasattr(obj, "model_dump") and obj is not result:
            pytest.fail(f"Found object with model_dump method at {path}: {type(obj)}")
        elif isinstance(obj, dict):
            for key, value in obj.items():
                check_no_capabilities_object(value, f"{path}.{key}")
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                check_no_capabilities_object(item, f"{path}[{i}]")

    check_no_capabilities_object(result)


def test_filtered_capabilities_inheritance():
    """Ensure our fix maintains proper inheritance from ServerCapabilities.

    The fix uses a subclass approach, so we need to ensure it properly
    inherits from ServerCapabilities and doesn't break isinstance checks.
    """
    from chuk_mcp_server.types.base import ServerCapabilities

    capabilities = create_server_capabilities()

    # Critical: must be an instance of ServerCapabilities
    assert isinstance(capabilities, ServerCapabilities)

    # Should have all the expected attributes
    assert hasattr(capabilities, "tools")
    assert hasattr(capabilities, "resources")

    # The internal attributes used for filtering should not be visible in dumps
    result = capabilities.model_dump()
    assert "_filter_kwargs" not in result
    assert "_experimental" not in result

    # JSON serialization should work
    json.dumps(result)  # Should not raise
