#!/usr/bin/env python3
"""
Tests for HTTP request context functionality.

Tests the get_http_request and set_http_request functions added to the context module.
"""

import pytest

from chuk_mcp_server.context import (
    clear_all,
    get_http_request,
    set_http_request,
)


@pytest.fixture(autouse=True)
def cleanup_context():
    """Ensure context is clean before and after each test."""
    clear_all()
    yield
    clear_all()


class TestHTTPRequestContext:
    """Test HTTP request context management."""

    def test_get_http_request_default(self):
        """Test get_http_request returns None by default."""
        assert get_http_request() is None

    def test_set_and_get_http_request(self):
        """Test setting and getting HTTP request object."""
        mock_request = {"type": "http", "path": "/test"}
        set_http_request(mock_request)
        assert get_http_request() == mock_request

    def test_set_http_request_none(self):
        """Test setting HTTP request to None."""
        mock_request = {"type": "http", "path": "/test"}
        set_http_request(mock_request)
        set_http_request(None)
        assert get_http_request() is None

    def test_http_request_with_clear_all(self):
        """Test clear_all clears HTTP request context."""
        mock_request = {"type": "http", "path": "/test"}
        set_http_request(mock_request)
        clear_all()
        assert get_http_request() is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
