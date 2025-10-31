#!/usr/bin/env python3
# tests/types/test_resources_coverage.py
"""
Additional tests for resources.py to achieve 90%+ coverage.
Focuses on missing lines 100, 147, 155.
"""

import pytest


def test_resource_handler_to_mcp_bytes_with_none_format_cache():
    """Test to_mcp_bytes when format cache is None (line 100)."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def test_resource() -> str:
        return "test"

    handler = ResourceHandler.from_function(uri="test://resource", func=test_resource)

    # Clear both caches
    handler._cached_mcp_format = None
    handler._cached_mcp_bytes = None

    # This should populate both caches
    result = handler.to_mcp_bytes()

    assert result is not None
    assert handler._cached_mcp_format is not None
    assert handler._cached_mcp_bytes is not None


@pytest.mark.asyncio
async def test_resource_handler_format_content_json_primitive():
    """Test _format_content with non-dict/list JSON (line 147)."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def json_primitive_resource() -> str:
        return "just a string"

    handler = ResourceHandler.from_function(
        uri="test://json_primitive", func=json_primitive_resource, mime_type="application/json"
    )

    content = await handler.read()

    # Should serialize as JSON (without indent for primitives)
    assert content == '"just a string"'


@pytest.mark.asyncio
async def test_resource_handler_format_content_unknown_mime_primitive():
    """Test _format_content with unknown MIME type and primitive (line 155)."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def unknown_primitive_resource() -> str:
        return "plain text"

    handler = ResourceHandler.from_function(
        uri="test://unknown_primitive", func=unknown_primitive_resource, mime_type="application/x-unknown"
    )

    content = await handler.read()

    # Should convert to string for primitive types with unknown MIME
    assert content == "plain text"


@pytest.mark.asyncio
async def test_resource_handler_format_content_unknown_mime_dict():
    """Test _format_content with unknown MIME type and dict (line 152-153)."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def unknown_dict_resource() -> dict:
        return {"key": "value", "number": 42}

    handler = ResourceHandler.from_function(
        uri="test://unknown_dict", func=unknown_dict_resource, mime_type="application/x-custom"
    )

    content = await handler.read()

    # Should format as indented JSON for dict/list with unknown MIME
    import orjson

    parsed = orjson.loads(content)
    assert parsed == {"key": "value", "number": 42}
    assert "{\n" in content  # Check for indentation


@pytest.mark.asyncio
async def test_resource_handler_format_content_unknown_mime_list():
    """Test _format_content with unknown MIME type and list."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def unknown_list_resource() -> list:
        return [1, 2, 3, 4, 5]

    handler = ResourceHandler.from_function(
        uri="test://unknown_list", func=unknown_list_resource, mime_type="application/x-custom"
    )

    content = await handler.read()

    # Should format as indented JSON for list with unknown MIME
    import orjson

    parsed = orjson.loads(content)
    assert parsed == [1, 2, 3, 4, 5]
    assert "[\n" in content  # Check for indentation


def test_resource_handler_get_cache_info_with_timestamp():
    """Test get_cache_info with valid timestamp."""
    import time

    from chuk_mcp_server.types.resources import ResourceHandler

    def test_resource() -> str:
        return "test"

    handler = ResourceHandler.from_function(uri="test://cache_info", func=test_resource, cache_ttl=60)

    # Manually set cache
    handler._cached_content = "test content"
    handler._cache_timestamp = time.time()

    cache_info = handler.get_cache_info()

    assert cache_info["caching"] is True
    assert cache_info["status"] == "cached"
    assert cache_info["ttl"] == 60
    assert "age_seconds" in cache_info
    assert "remaining_seconds" in cache_info
    assert cache_info["content_length"] == len("test content")


def test_resource_handler_get_cache_info_expired():
    """Test get_cache_info with expired cache."""
    import time

    from chuk_mcp_server.types.resources import ResourceHandler

    def test_resource() -> str:
        return "test"

    handler = ResourceHandler.from_function(uri="test://expired", func=test_resource, cache_ttl=1)

    # Set cache with old timestamp
    handler._cached_content = "test content"
    handler._cache_timestamp = time.time() - 2  # 2 seconds ago

    cache_info = handler.get_cache_info()

    assert cache_info["caching"] is True
    assert cache_info["status"] == "expired"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
