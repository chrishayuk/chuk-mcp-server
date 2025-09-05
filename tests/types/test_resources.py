#!/usr/bin/env python3
# tests/types/test_resources.py
"""
Unit tests for chuk_mcp_server.types.resources module

Tests ResourceHandler class, resource creation, caching, and content formatting.
"""

import asyncio

import orjson
import pytest


def test_resource_handler_from_function_basic():
    """Test creating ResourceHandler from a basic function."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def simple_resource() -> str:
        """A simple resource that returns text."""
        return "Hello, world!"

    handler = ResourceHandler.from_function(uri="test://simple", func=simple_resource)

    assert handler.uri == "test://simple"
    assert handler.name == "Simple Resource"  # Auto-generated from function name
    assert handler.description == "A simple resource that returns text."
    assert handler.mime_type == "text/plain"


def test_resource_handler_from_function_with_custom_params():
    """Test creating ResourceHandler with custom parameters."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def my_resource() -> dict:
        return {"key": "value"}

    handler = ResourceHandler.from_function(
        uri="custom://resource",
        func=my_resource,
        name="Custom Resource",
        description="A custom resource",
        mime_type="application/json",
    )

    assert handler.uri == "custom://resource"
    assert handler.name == "Custom Resource"
    assert handler.description == "A custom resource"
    assert handler.mime_type == "application/json"


def test_resource_handler_properties():
    """Test ResourceHandler properties."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def test_resource() -> str:
        return "test"

    handler = ResourceHandler.from_function(
        uri="test://uri",
        func=test_resource,
        name="Test Name",
        description="Test Description",
        mime_type="text/markdown",
    )

    assert handler.uri == "test://uri"
    assert handler.name == "Test Name"
    assert handler.description == "Test Description"
    assert handler.mime_type == "text/markdown"


def test_resource_handler_to_mcp_format():
    """Test ResourceHandler MCP format conversion."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def test_resource() -> str:
        """Test resource docstring."""
        return "test content"

    handler = ResourceHandler.from_function(
        uri="test://resource",
        func=test_resource,
        name="Test Resource",
        description="A test resource",
        mime_type="text/plain",
    )

    mcp_format = handler.to_mcp_format()

    assert isinstance(mcp_format, dict)
    assert mcp_format["uri"] == "test://resource"
    assert mcp_format["name"] == "Test Resource"
    assert mcp_format["description"] == "A test resource"
    assert mcp_format["mimeType"] == "text/plain"


def test_resource_handler_to_mcp_bytes():
    """Test ResourceHandler orjson bytes conversion."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def test_resource() -> str:
        return "test"

    handler = ResourceHandler.from_function(uri="test://bytes", func=test_resource)

    mcp_bytes = handler.to_mcp_bytes()

    assert isinstance(mcp_bytes, bytes)

    # Test that it can be deserialized
    mcp_data = orjson.loads(mcp_bytes)
    assert mcp_data["uri"] == "test://bytes"


def test_resource_handler_caching():
    """Test that ResourceHandler caches MCP format properly."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def test_resource() -> str:
        return "test"

    handler = ResourceHandler.from_function(uri="test://cache", func=test_resource)

    # First calls should cache
    format1 = handler.to_mcp_format()
    bytes1 = handler.to_mcp_bytes()

    # Second calls should return cached versions
    format2 = handler.to_mcp_format()
    bytes2 = handler.to_mcp_bytes()

    # Should be different objects (copies) for format
    assert format1 is not format2
    assert format1 == format2

    # Should be same object for bytes (immutable)
    assert bytes1 is bytes2

    # Test cache invalidation
    handler.invalidate_mcp_cache()
    handler.to_mcp_format()
    bytes3 = handler.to_mcp_bytes()

    # Should be new objects after invalidation
    assert bytes1 is not bytes3
    assert bytes1 == bytes3  # But content should be same


@pytest.mark.asyncio
async def test_resource_handler_read_sync():
    """Test reading synchronous resource."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def sync_resource() -> str:
        return "Synchronous content"

    handler = ResourceHandler.from_function(uri="test://sync", func=sync_resource)

    content = await handler.read()
    assert content == "Synchronous content"


@pytest.mark.asyncio
async def test_resource_handler_read_async():
    """Test reading asynchronous resource."""
    from chuk_mcp_server.types.resources import ResourceHandler

    async def async_resource() -> str:
        await asyncio.sleep(0.01)
        return "Asynchronous content"

    handler = ResourceHandler.from_function(uri="test://async", func=async_resource)

    content = await handler.read()
    assert content == "Asynchronous content"


@pytest.mark.asyncio
async def test_resource_handler_content_formatting_text():
    """Test content formatting for text/plain."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def text_resource() -> str:
        return "Plain text content"

    handler = ResourceHandler.from_function(uri="test://text", func=text_resource, mime_type="text/plain")

    content = await handler.read()
    assert content == "Plain text content"


@pytest.mark.asyncio
async def test_resource_handler_content_formatting_json():
    """Test content formatting for application/json."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def json_resource() -> dict:
        return {"key": "value", "number": 42, "nested": {"inner": "data"}}

    handler = ResourceHandler.from_function(uri="test://json", func=json_resource, mime_type="application/json")

    content = await handler.read()

    # Should be formatted JSON with indentation
    assert "{\n" in content  # Indented JSON
    assert '"key": "value"' in content
    assert '"number": 42' in content

    # Should be valid JSON
    parsed = orjson.loads(content)
    assert parsed["key"] == "value"
    assert parsed["number"] == 42


@pytest.mark.asyncio
async def test_resource_handler_content_formatting_markdown():
    """Test content formatting for text/markdown."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def markdown_resource() -> str:
        return "# Markdown Title\n\nSome **bold** text."

    handler = ResourceHandler.from_function(uri="test://markdown", func=markdown_resource, mime_type="text/markdown")

    content = await handler.read()
    assert content == "# Markdown Title\n\nSome **bold** text."


@pytest.mark.asyncio
async def test_resource_handler_content_formatting_unknown():
    """Test content formatting for unknown MIME type."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def unknown_resource() -> dict:
        return {"data": "test"}

    handler = ResourceHandler.from_function(
        uri="test://unknown", func=unknown_resource, mime_type="application/unknown"
    )

    content = await handler.read()

    # Should default to JSON formatting for dict
    parsed = orjson.loads(content)
    assert parsed["data"] == "test"


@pytest.mark.asyncio
async def test_resource_handler_content_caching():
    """Test content caching functionality."""
    from chuk_mcp_server.types.resources import ResourceHandler

    call_count = 0

    def counting_resource() -> str:
        nonlocal call_count
        call_count += 1
        return f"Content #{call_count}"

    handler = ResourceHandler.from_function(
        uri="test://cached",
        func=counting_resource,
        cache_ttl=1,  # 1 second cache
    )

    # First read should call function
    content1 = await handler.read()
    assert content1 == "Content #1"
    assert call_count == 1

    # Second read should use cache
    content2 = await handler.read()
    assert content2 == "Content #1"  # Same content
    assert call_count == 1  # Function not called again

    # Wait for cache to expire
    await asyncio.sleep(1.1)

    # Third read should call function again
    content3 = await handler.read()
    assert content3 == "Content #2"
    assert call_count == 2


@pytest.mark.asyncio
async def test_resource_handler_cache_invalidation():
    """Test manual cache invalidation."""
    from chuk_mcp_server.types.resources import ResourceHandler

    call_count = 0

    def counting_resource() -> str:
        nonlocal call_count
        call_count += 1
        return f"Content #{call_count}"

    handler = ResourceHandler.from_function(
        uri="test://invalidate",
        func=counting_resource,
        cache_ttl=10,  # Long cache
    )

    # First read
    content1 = await handler.read()
    assert content1 == "Content #1"
    assert call_count == 1

    # Second read should use cache
    content2 = await handler.read()
    assert content2 == "Content #1"
    assert call_count == 1

    # Invalidate cache
    handler.invalidate_cache()

    # Third read should call function again
    content3 = await handler.read()
    assert content3 == "Content #2"
    assert call_count == 2


def test_resource_handler_cache_info():
    """Test cache information functionality."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def test_resource() -> str:
        return "test"

    # Handler without caching
    handler_no_cache = ResourceHandler.from_function(uri="test://no_cache", func=test_resource)

    cache_info = handler_no_cache.get_cache_info()
    assert cache_info["caching"] is False
    assert cache_info["reason"] == "no_ttl_set"

    # Handler with caching
    handler_with_cache = ResourceHandler.from_function(uri="test://with_cache", func=test_resource, cache_ttl=60)

    cache_info = handler_with_cache.get_cache_info()
    assert cache_info["caching"] is True
    assert cache_info["status"] == "empty"
    assert cache_info["ttl"] == 60


def test_resource_handler_is_cached():
    """Test is_cached functionality."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def test_resource() -> str:
        return "test"

    handler = ResourceHandler.from_function(uri="test://cached_check", func=test_resource, cache_ttl=1)

    # Initially not cached
    assert handler.is_cached() is False

    # After reading, should be cached (but this requires async execution)
    # We'll test this indirectly through cache_info


@pytest.mark.asyncio
async def test_resource_handler_read_error():
    """Test error handling during resource read."""
    from chuk_mcp_server.types.base import MCPError
    from chuk_mcp_server.types.resources import ResourceHandler

    def failing_resource() -> str:
        raise ValueError("Resource failed!")

    handler = ResourceHandler.from_function(uri="test://failing", func=failing_resource)

    with pytest.raises(MCPError) as exc_info:
        await handler.read()

    assert "test://failing" in str(exc_info.value)
    assert "Resource failed!" in str(exc_info.value)


def test_create_resource_from_function_utility():
    """Test the convenience function for creating resources."""
    from chuk_mcp_server.types.resources import create_resource_from_function

    def utility_resource() -> str:
        return "utility content"

    handler = create_resource_from_function(
        uri="test://utility", func=utility_resource, name="Utility Resource", description="A utility resource"
    )

    assert handler.uri == "test://utility"
    assert handler.name == "Utility Resource"
    assert handler.description == "A utility resource"


def test_create_json_resource_utility():
    """Test the JSON resource convenience function."""
    from chuk_mcp_server.types.resources import create_json_resource

    def json_data() -> dict:
        return {"test": "data"}

    handler = create_json_resource(uri="test://json_util", func=json_data, name="JSON Utility")

    assert handler.uri == "test://json_util"
    assert handler.name == "JSON Utility"
    assert handler.mime_type == "application/json"


def test_create_markdown_resource_utility():
    """Test the Markdown resource convenience function."""
    from chuk_mcp_server.types.resources import create_markdown_resource

    def markdown_content() -> str:
        return "# Test Markdown"

    handler = create_markdown_resource(uri="test://md_util", func=markdown_content, name="Markdown Utility")

    assert handler.uri == "test://md_util"
    assert handler.name == "Markdown Utility"
    assert handler.mime_type == "text/markdown"


def test_resource_handler_orjson_optimization():
    """Test that orjson optimization is working in content formatting."""
    from chuk_mcp_server.types.resources import ResourceHandler

    def json_resource() -> dict:
        return {"large_data": list(range(100)), "nested": {"deep": {"structure": "value"}}}

    handler = ResourceHandler.from_function(uri="test://orjson", func=json_resource, mime_type="application/json")

    # This should use orjson.dumps internally for better performance
    content = asyncio.run(handler.read())

    # Should be valid JSON with proper formatting
    parsed = orjson.loads(content)
    assert len(parsed["large_data"]) == 100
    assert parsed["nested"]["deep"]["structure"] == "value"


def test_module_exports():
    """Test that all expected exports are available."""
    from chuk_mcp_server.types import resources

    assert hasattr(resources, "__all__")
    assert isinstance(resources.__all__, list)

    expected_exports = [
        "ResourceHandler",
        "create_resource_from_function",
        "create_json_resource",
        "create_markdown_resource",
    ]

    for export in expected_exports:
        assert export in resources.__all__
        assert hasattr(resources, export)


if __name__ == "__main__":
    pytest.main([__file__])
