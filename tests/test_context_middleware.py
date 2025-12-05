#!/usr/bin/env python3
"""
Tests for ContextMiddleware.

Tests the middleware that stores HTTP requests in context.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from chuk_mcp_server.context import clear_all, get_http_request
from chuk_mcp_server.middlewares.context_middleware import ContextMiddleware


@pytest.fixture(autouse=True)
def cleanup_context():
    """Ensure context is clean before and after each test."""
    clear_all()
    yield
    clear_all()


class TestContextMiddleware:
    """Test the context middleware for storing HTTP requests."""

    @pytest.mark.asyncio
    async def test_middleware_sets_request_in_context(self):
        """Test that middleware stores request scope in context."""
        # Create mock app and scope
        mock_app = AsyncMock()
        mock_scope = {"type": "http", "path": "/test", "method": "GET"}
        mock_receive = AsyncMock()
        mock_send = AsyncMock()

        # Create middleware instance
        middleware = ContextMiddleware(mock_app)

        # Call middleware
        await middleware(mock_scope, mock_receive, mock_send)

        # Verify context was set with scope
        assert get_http_request() == mock_scope

        # Verify app was called with correct parameters
        mock_app.assert_called_once_with(mock_scope, mock_receive, mock_send)

    @pytest.mark.asyncio
    async def test_middleware_with_app_exception(self):
        """Test middleware when app raises exception."""
        # Create mock app that raises exception
        mock_app = AsyncMock(side_effect=ValueError("Test error"))
        mock_scope = {"type": "http", "path": "/test"}
        mock_receive = AsyncMock()
        mock_send = AsyncMock()

        # Create middleware instance
        middleware = ContextMiddleware(mock_app)

        # Call middleware - should propagate exception
        with pytest.raises(ValueError):
            await middleware(mock_scope, mock_receive, mock_send)

        # Verify context was set despite exception
        assert get_http_request() == mock_scope

    def test_middleware_init(self):
        """Test middleware initialization."""
        mock_app = Mock()
        middleware = ContextMiddleware(mock_app)
        assert middleware.app == mock_app


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
