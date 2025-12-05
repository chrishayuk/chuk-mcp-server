#!/usr/bin/env python3
"""
Tests for middleware integration in the HTTP server.

Tests that the ContextMiddleware is properly added to the HTTP server's middleware stack.
"""

from unittest.mock import Mock, patch

import pytest

from chuk_mcp_server.http_server import HTTPServer
from chuk_mcp_server.middlewares import ContextMiddleware


class TestMiddlewareInHttpServer:
    """Test middleware integration in the HTTP server."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock protocol handler
        self.mock_protocol = Mock()
        self.mock_protocol.server_info = Mock()
        self.mock_protocol.server_info.name = "TestServer"
        self.mock_protocol.server_info.version = "1.0.0"
        self.mock_protocol.tools = {}
        self.mock_protocol.resources = {}
        self.mock_protocol.capabilities = Mock()

    @patch("chuk_mcp_server.http_server.http_endpoint_registry")
    @patch("chuk_mcp_server.http_server.MCPEndpoint")
    @patch("chuk_mcp_server.http_server.HealthEndpoint")
    @patch("chuk_mcp_server.http_server.InfoEndpoint")
    @patch("chuk_mcp_server.http_server.Middleware")
    def test_context_middleware_added_to_stack(
        self, mock_middleware, mock_info_endpoint, mock_health_endpoint, mock_mcp_endpoint, mock_registry
    ):
        """Test that ContextMiddleware is added to the middleware stack."""
        # Mock registry
        mock_registry.clear_endpoints = Mock()
        mock_registry.register_endpoint = Mock()
        mock_registry.get_routes.return_value = []
        mock_registry.get_middleware.return_value = []

        # Mock endpoints
        mock_info_endpoint.return_value = Mock()
        mock_mcp_endpoint.return_value = Mock()

        # Create server (this will call Middleware with ContextMiddleware)
        HTTPServer(self.mock_protocol)

        # Check if Middleware was called with ContextMiddleware
        middleware_calls = [call[0][0] for call in mock_middleware.call_args_list]
        context_middleware_found = ContextMiddleware in middleware_calls

        assert context_middleware_found, "ContextMiddleware not found in middleware stack"

    @patch("chuk_mcp_server.http_server.http_endpoint_registry")
    @patch("chuk_mcp_server.http_server.MCPEndpoint")
    @patch("chuk_mcp_server.http_server.HealthEndpoint")
    @patch("chuk_mcp_server.http_server.InfoEndpoint")
    @patch("chuk_mcp_server.http_server.Middleware")
    def test_middleware_initialization_order(
        self, mock_middleware, mock_info_endpoint, mock_health_endpoint, mock_mcp_endpoint, mock_registry
    ):
        """Test that middleware is initialized in the correct order with ContextMiddleware last."""
        # Mock registry with some custom middlewares
        mock_registry.clear_endpoints = Mock()
        mock_registry.register_endpoint = Mock()
        mock_registry.get_routes.return_value = []

        # Create mock custom middleware configs
        class CustomMiddleware1:
            pass

        class CustomMiddleware2:
            pass

        mock_middleware1 = Mock()
        mock_middleware1.middleware_class = CustomMiddleware1
        mock_middleware2 = Mock()
        mock_middleware2.middleware_class = CustomMiddleware2

        # Return some mock middleware configs
        mock_registry.get_middleware.return_value = [mock_middleware1, mock_middleware2]

        # Mock endpoints
        mock_info_endpoint.return_value = Mock()
        mock_mcp_endpoint.return_value = Mock()

        # Create server
        HTTPServer(self.mock_protocol)

        # Check the middleware initialization
        middleware_classes = [call[0][0] for call in mock_middleware.call_args_list]

        # Find CORSMiddleware, custom middlewares, and ContextMiddleware in the middleware list
        cors_index = -1
        custom1_index = -1
        custom2_index = -1
        context_index = -1

        for i, cls in enumerate(middleware_classes):
            if "CORSMiddleware" in str(cls):
                cors_index = i
            if cls == CustomMiddleware1:
                custom1_index = i
            if cls == CustomMiddleware2:
                custom2_index = i
            if cls == ContextMiddleware:
                context_index = i

        # Verify middlewares were found
        assert cors_index != -1, "CORSMiddleware not found in middleware list"
        assert custom1_index != -1, "CustomMiddleware1 not found in middleware list"
        assert custom2_index != -1, "CustomMiddleware2 not found in middleware list"
        assert context_index != -1, "ContextMiddleware not found in middleware list"

        # Verify middleware order:
        # 1. CORS middleware should be first
        # 2. Custom middlewares should follow
        # 3. ContextMiddleware should be last
        assert cors_index < custom1_index, "CORS middleware should be initialized before custom middlewares"
        assert custom1_index < custom2_index, "Custom middlewares should be initialized in order"
        assert custom2_index < context_index, "Custom middlewares should be initialized before ContextMiddleware"
        assert context_index == len(middleware_classes) - 1, (
            "ContextMiddleware should be the last middleware initialized"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
