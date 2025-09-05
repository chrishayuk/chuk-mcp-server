#!/usr/bin/env python3
"""Extended tests for resources module to improve coverage."""

import time
from unittest.mock import Mock

import pytest

from chuk_mcp_server.types.resources import ResourceHandler, create_resource_from_function


class TestResourceHandlerExtended:
    """Extended tests for ResourceHandler class."""

    def test_post_init_with_cached_formats(self):
        """Test __post_init__ when cached formats are already set."""

        # Create handler with pre-set cache
        def resource_func():
            return "test"

        # Create with cached values
        cached_format = {"test": "format"}
        cached_bytes = b"test_bytes"

        handler = ResourceHandler(
            mcp_resource=Mock(model_dump=Mock(return_value=cached_format)),
            handler=resource_func,
            cache_ttl=None,
            _cached_mcp_format=cached_format,
            _cached_mcp_bytes=cached_bytes,
        )

        # Should retain the pre-set cached values
        assert handler._cached_mcp_format == cached_format
        assert handler._cached_mcp_bytes == cached_bytes

    def test_post_init_without_cached_formats(self):
        """Test __post_init__ generates cache when not set."""

        def resource_func():
            return "test"

        mock_resource = Mock()
        mock_resource.model_dump.return_value = {"uri": "test://uri"}

        handler = ResourceHandler(
            mcp_resource=mock_resource,
            handler=resource_func,
            cache_ttl=None,
            _cached_mcp_format=None,
            _cached_mcp_bytes=None,
        )

        # Should have generated cache
        assert handler._cached_mcp_format is not None
        assert handler._cached_mcp_bytes is not None
        mock_resource.model_dump.assert_called_once_with(exclude_none=True)

    def test_mime_type_property(self):
        """Test mime_type property."""

        def resource_func():
            return "test"

        mock_resource = Mock(mimeType="application/json")
        handler = ResourceHandler(
            mcp_resource=mock_resource,
            handler=resource_func,
            cache_ttl=None,
            _cached_mcp_format={},
            _cached_mcp_bytes=b"",
        )

        assert handler.mime_type == "application/json"

    def test_is_cached_with_no_ttl(self):
        """Test is_cached returns False when no TTL is set."""

        def resource_func():
            return "test"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=None,  # No TTL
        )

        # Set cached content manually
        handler._cached_content = "cached"
        handler._cache_timestamp = time.time()

        assert handler.is_cached() is False  # Should be False without TTL

    def test_is_cached_with_no_content(self):
        """Test is_cached returns False when no content is cached."""

        def resource_func():
            return "test"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=60,
        )

        assert handler.is_cached() is False  # No content cached

    def test_is_cached_with_no_timestamp(self):
        """Test is_cached returns False when no timestamp is set."""

        def resource_func():
            return "test"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=60,
        )

        # Set content but no timestamp
        handler._cached_content = "cached"
        handler._cache_timestamp = None

        assert handler.is_cached() is False

    def test_is_cached_with_valid_cache(self):
        """Test is_cached returns True for valid cache."""

        def resource_func():
            return "test"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=60,
        )

        # Set valid cache
        handler._cached_content = "cached"
        handler._cache_timestamp = time.time()

        assert handler.is_cached() is True

    def test_is_cached_with_expired_cache(self):
        """Test is_cached returns False for expired cache."""

        def resource_func():
            return "test"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=1,  # 1 second TTL
        )

        # Set expired cache
        handler._cached_content = "cached"
        handler._cache_timestamp = time.time() - 10  # 10 seconds ago

        assert handler.is_cached() is False

    def test_get_cache_info_no_ttl(self):
        """Test get_cache_info when no TTL is set."""

        def resource_func():
            return "test"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=None,
        )

        info = handler.get_cache_info()
        assert info == {"caching": False, "reason": "no_ttl_set"}

    def test_get_cache_info_empty_cache(self):
        """Test get_cache_info when cache is empty."""

        def resource_func():
            return "test"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=60,
        )

        info = handler.get_cache_info()
        assert info == {"caching": True, "status": "empty", "ttl": 60}

    def test_get_cache_info_cached(self):
        """Test get_cache_info when content is cached and valid."""

        def resource_func():
            return "test"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=60,
        )

        # Set valid cache
        handler._cached_content = "cached"
        handler._cache_timestamp = time.time()

        info = handler.get_cache_info()
        assert info["caching"] is True
        assert info["status"] == "cached"
        assert info["ttl"] == 60
        # Check for age_seconds and remaining_seconds (actual keys used)
        assert "age_seconds" in info
        assert "remaining_seconds" in info
        assert info["remaining_seconds"] > 0

    def test_get_cache_info_expired(self):
        """Test get_cache_info when cache is expired."""

        def resource_func():
            return "test"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=1,
        )

        # Set expired cache
        handler._cached_content = "cached"
        handler._cache_timestamp = time.time() - 10

        info = handler.get_cache_info()
        assert info["caching"] is True
        assert info["status"] == "expired"
        assert info["remaining_seconds"] == 0

    def test_get_cache_info_no_timestamp(self):
        """Test get_cache_info when content exists but no timestamp."""

        def resource_func():
            return "test"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=60,
        )

        # Set content without timestamp
        handler._cached_content = "cached"
        handler._cache_timestamp = None

        info = handler.get_cache_info()
        assert info["caching"] is True
        assert info["status"] == "expired"  # No timestamp means expired
        assert info["age_seconds"] == 0
        assert info["remaining_seconds"] == 0

    @pytest.mark.asyncio
    async def test_read_with_cache_disabled(self):
        """Test read method when caching is disabled."""

        def resource_func():
            return {"data": "test"}

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            mime_type="application/json",
            cache_ttl=None,  # Caching disabled
        )

        # Read multiple times
        content1 = await handler.read()
        content2 = await handler.read()

        # Both should be formatted JSON
        assert '"data"' in content1
        assert content1 == content2
        # Cache should not be used
        assert handler._cached_content is None

    @pytest.mark.asyncio
    async def test_read_with_expired_cache(self):
        """Test read method refreshes expired cache."""
        call_count = 0

        def resource_func():
            nonlocal call_count
            call_count += 1
            return f"call_{call_count}"

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=resource_func,
            cache_ttl=1,  # 1 second TTL
        )

        # First read
        content1 = await handler.read()
        assert content1 == "call_1"

        # Expire the cache
        handler._cache_timestamp = time.time() - 10

        # Second read should refresh
        content2 = await handler.read()
        assert content2 == "call_2"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_read_error_handling(self):
        """Test read method error handling."""

        def failing_func():
            raise ValueError("Test error")

        handler = ResourceHandler.from_function(
            uri="test://resource",
            func=failing_func,
        )

        from chuk_mcp_server.types.base import MCPError

        with pytest.raises(MCPError, match="Failed to read resource"):
            await handler.read()

    def test_from_function_with_all_parameters(self):
        """Test from_function with all parameters specified."""

        def test_resource():
            """Custom docstring."""
            return "content"

        handler = ResourceHandler.from_function(
            uri="custom://uri",
            func=test_resource,
            name="Custom Name",
            description="Custom Description",
            mime_type="text/markdown",
            cache_ttl=300,
        )

        assert handler.uri == "custom://uri"
        assert handler.name == "Custom Name"
        assert handler.description == "Custom Description"
        assert handler.mime_type == "text/markdown"
        assert handler.cache_ttl == 300


class TestResourceUtilitiesExtended:
    """Extended tests for resource utility functions."""

    def test_create_resource_with_cache_ttl(self):
        """Test creating resource with cache TTL."""

        def cached_resource():
            return "cached content"

        handler = create_resource_from_function(
            uri="cache://test",
            func=cached_resource,
            cache_ttl=120,
        )

        assert handler.cache_ttl == 120

    def test_resource_handler_function_with_underscores(self):
        """Test function name with underscores gets properly formatted."""

        def my_test_resource():
            return "content"

        handler = ResourceHandler.from_function(
            uri="test://uri",
            func=my_test_resource,
        )

        # Underscores should be replaced with spaces and title-cased
        assert handler.name == "My Test Resource"
