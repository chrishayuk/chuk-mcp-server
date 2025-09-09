#!/usr/bin/env python3
"""Comprehensive tests for endpoint_registry module."""

import time
from unittest.mock import AsyncMock, Mock

import pytest
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from chuk_mcp_server.endpoint_registry import (
    EndpointConfig,
    HTTPEndpointRegistry,
    MiddlewareConfig,
    endpoint,
    endpoint_registry_info_handler,
    get_endpoint,
    http_endpoint_registry,
    list_endpoints,
    middleware,
    register_endpoint,
    register_middleware,
    unregister_endpoint,
)


class TestEndpointConfig:
    """Test EndpointConfig dataclass."""

    def test_endpoint_config_basic(self):
        """Test basic EndpointConfig creation."""
        handler = Mock()
        config = EndpointConfig(
            path="/test", handler=handler, methods=["GET"], name="test_endpoint", description="Test endpoint"
        )

        assert config.path == "/test"
        assert config.handler == handler
        assert config.methods == ["GET"]
        assert config.name == "test_endpoint"
        assert config.description == "Test endpoint"
        assert config.middleware is None
        assert config.metadata is None
        assert config.registered_at is not None

    def test_endpoint_config_post_init(self):
        """Test EndpointConfig __post_init__ method."""
        start_time = time.time()

        config = EndpointConfig(path="/test", handler=Mock(), methods=["GET"], name="test", description="Test")

        # Should have set registered_at automatically
        assert config.registered_at >= start_time
        assert config.registered_at <= time.time()

    def test_endpoint_config_with_registered_at(self):
        """Test EndpointConfig with explicit registered_at."""
        explicit_time = 123456789.0

        config = EndpointConfig(
            path="/test", handler=Mock(), methods=["GET"], name="test", description="Test", registered_at=explicit_time
        )

        # Should keep explicit value
        assert config.registered_at == explicit_time

    def test_endpoint_config_with_all_params(self):
        """Test EndpointConfig with all parameters."""
        handler = Mock()
        middleware = [Mock()]
        metadata = {"key": "value"}

        config = EndpointConfig(
            path="/test",
            handler=handler,
            methods=["GET", "POST"],
            name="test_endpoint",
            description="Test endpoint",
            middleware=middleware,
            metadata=metadata,
        )

        assert config.middleware == middleware
        assert config.metadata == metadata


class TestMiddlewareConfig:
    """Test MiddlewareConfig dataclass."""

    def test_middleware_config_basic(self):
        """Test basic MiddlewareConfig creation."""
        middleware_class = Mock()

        config = MiddlewareConfig(middleware_class=middleware_class)

        assert config.middleware_class == middleware_class
        assert config.args == ()
        assert config.kwargs == {}
        assert config.priority == 100
        assert config.name == ""
        assert config.description == ""
        assert config.registered_at is not None

    def test_middleware_config_post_init(self):
        """Test MiddlewareConfig __post_init__ method."""
        start_time = time.time()

        config = MiddlewareConfig(middleware_class=Mock())

        # Should have set registered_at automatically
        assert config.registered_at >= start_time
        assert config.registered_at <= time.time()
        assert config.kwargs == {}

    def test_middleware_config_with_kwargs(self):
        """Test MiddlewareConfig with explicit kwargs."""
        middleware_class = Mock()
        explicit_kwargs = {"key": "value"}

        config = MiddlewareConfig(middleware_class=middleware_class, kwargs=explicit_kwargs)

        # Should keep explicit kwargs
        assert config.kwargs == explicit_kwargs

    def test_middleware_config_with_all_params(self):
        """Test MiddlewareConfig with all parameters."""
        middleware_class = Mock()
        args = (1, 2, 3)
        kwargs = {"key": "value"}

        config = MiddlewareConfig(
            middleware_class=middleware_class,
            args=args,
            kwargs=kwargs,
            priority=50,
            name="test_middleware",
            description="Test middleware",
        )

        assert config.args == args
        assert config.kwargs == kwargs
        assert config.priority == 50
        assert config.name == "test_middleware"
        assert config.description == "Test middleware"


class TestHTTPEndpointRegistry:
    """Test HTTPEndpointRegistry class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = HTTPEndpointRegistry()

    def test_registry_initialization(self):
        """Test registry initialization."""
        assert isinstance(self.registry.endpoints, dict)
        assert len(self.registry.endpoints) == 0
        assert isinstance(self.registry.middleware, list)
        assert len(self.registry.middleware) == 0
        assert self.registry._route_cache is None

    def test_register_endpoint_basic(self):
        """Test basic endpoint registration."""
        handler = AsyncMock()

        self.registry.register_endpoint("/test", handler)

        assert "/test" in self.registry.endpoints
        config = self.registry.endpoints["/test"]
        assert config.path == "/test"
        assert config.handler == handler
        assert config.methods == ["GET"]  # Default
        assert config.name == "test"  # Generated from path

    def test_register_endpoint_with_all_params(self):
        """Test endpoint registration with all parameters."""
        handler = AsyncMock()
        methods = ["GET", "POST"]
        middleware_list = [Mock()]
        metadata = {"key": "value"}

        self.registry.register_endpoint(
            "/api/data",
            handler,
            methods=methods,
            name="data_endpoint",
            description="Data endpoint",
            middleware=middleware_list,
            metadata=metadata,
        )

        config = self.registry.endpoints["/api/data"]
        assert config.path == "/api/data"
        assert config.handler == handler
        assert config.methods == methods
        assert config.name == "data_endpoint"
        assert config.description == "Data endpoint"
        assert config.middleware == middleware_list
        assert config.metadata == metadata

    def test_register_endpoint_path_normalization(self):
        """Test endpoint path normalization."""
        handler = AsyncMock()

        # Test path without leading slash
        self.registry.register_endpoint("test", handler)
        assert "/test" in self.registry.endpoints

    def test_register_endpoint_name_generation(self):
        """Test endpoint name generation."""
        handler = AsyncMock()

        # Test complex path
        self.registry.register_endpoint("/api/v1/users", handler)
        config = self.registry.endpoints["/api/v1/users"]
        assert config.name == "api_v1_users"

        # Test root path
        self.registry.register_endpoint("/", handler)
        config = self.registry.endpoints["/"]
        assert config.name == "root"

    def test_register_middleware(self):
        """Test middleware registration."""
        middleware_class = Mock()
        middleware_class.__name__ = "MockMiddleware"  # Add __name__ attribute

        self.registry.register_middleware(middleware_class)

        assert len(self.registry.middleware) == 1
        config = self.registry.middleware[0]
        assert config.middleware_class == middleware_class
        assert config.priority == 100  # Default

    def test_register_middleware_with_params(self):
        """Test middleware registration with parameters."""
        middleware_class = Mock()
        middleware_class.__name__ = "TestMiddleware"

        self.registry.register_middleware(
            middleware_class,
            "arg1",
            "arg2",
            priority=50,
            name="custom_middleware",
            description="Custom middleware",
            key="value",
        )

        config = self.registry.middleware[0]
        assert config.middleware_class == middleware_class
        assert config.args == ("arg1", "arg2")
        assert config.kwargs == {"key": "value"}
        assert config.priority == 50
        assert config.name == "custom_middleware"
        assert config.description == "Custom middleware"

    def test_register_middleware_sorting(self):
        """Test middleware sorting by priority."""
        middleware1 = Mock()
        middleware1.__name__ = "Middleware1"
        middleware2 = Mock()
        middleware2.__name__ = "Middleware2"
        middleware3 = Mock()
        middleware3.__name__ = "Middleware3"

        # Register in random order
        self.registry.register_middleware(middleware2, priority=100)
        self.registry.register_middleware(middleware1, priority=50)
        self.registry.register_middleware(middleware3, priority=150)

        # Should be sorted by priority
        priorities = [config.priority for config in self.registry.middleware]
        assert priorities == [50, 100, 150]

    def test_register_middleware_name_fallback(self):
        """Test middleware name fallback to class name."""

        class TestMiddleware:
            pass

        self.registry.register_middleware(TestMiddleware)

        config = self.registry.middleware[0]
        assert config.name == "TestMiddleware"

    def test_unregister_endpoint_success(self):
        """Test successful endpoint unregistration."""
        handler = AsyncMock()
        self.registry.register_endpoint("/test", handler)

        result = self.registry.unregister_endpoint("/test")

        assert result is True
        assert "/test" not in self.registry.endpoints

    def test_unregister_endpoint_not_found(self):
        """Test unregistering non-existent endpoint."""
        result = self.registry.unregister_endpoint("/nonexistent")

        assert result is False

    def test_get_endpoint(self):
        """Test getting endpoint configuration."""
        handler = AsyncMock()
        self.registry.register_endpoint("/test", handler)

        config = self.registry.get_endpoint("/test")
        assert config is not None
        assert config.path == "/test"

        # Test non-existent endpoint
        assert self.registry.get_endpoint("/nonexistent") is None

    def test_list_endpoints(self):
        """Test listing all endpoints."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        self.registry.register_endpoint("/test1", handler1)
        self.registry.register_endpoint("/test2", handler2)

        endpoints = self.registry.list_endpoints()
        assert len(endpoints) == 2
        assert all(isinstance(config, EndpointConfig) for config in endpoints)

    def test_get_routes(self):
        """Test getting Starlette routes."""
        handler = AsyncMock()
        self.registry.register_endpoint("/test", handler, methods=["GET", "POST"])

        routes = self.registry.get_routes()
        assert len(routes) == 1
        assert isinstance(routes[0], Route)
        assert routes[0].path == "/test"
        # Starlette automatically adds HEAD and sometimes OPTIONS
        assert "GET" in routes[0].methods
        assert "POST" in routes[0].methods

    def test_get_routes_caching(self):
        """Test route caching functionality."""
        handler = AsyncMock()
        self.registry.register_endpoint("/test", handler)

        # First call should create cache
        routes1 = self.registry.get_routes()
        assert self.registry._route_cache is not None

        # Second call should use cache
        routes2 = self.registry.get_routes()
        assert routes1 == routes2

        # Should return copies
        assert routes1 is not routes2

    def test_get_middleware(self):
        """Test getting middleware list."""
        middleware1 = Mock()
        middleware1.__name__ = "Middleware1"
        middleware2 = Mock()
        middleware2.__name__ = "Middleware2"

        self.registry.register_middleware(middleware1, priority=100)
        self.registry.register_middleware(middleware2, priority=50)

        middleware_configs = self.registry.get_middleware()
        assert len(middleware_configs) == 2
        # Should be sorted by priority
        assert middleware_configs[0].priority == 50
        assert middleware_configs[1].priority == 100

    def test_cache_invalidation(self):
        """Test route cache invalidation."""
        handler = AsyncMock()
        self.registry.register_endpoint("/test", handler)

        # Create cache
        self.registry.get_routes()
        assert self.registry._route_cache is not None

        # Register another endpoint - should invalidate cache
        self.registry.register_endpoint("/test2", handler)
        assert self.registry._route_cache is None

        # Unregister endpoint - should invalidate cache
        self.registry.get_routes()  # Recreate cache
        assert self.registry._route_cache is not None
        self.registry.unregister_endpoint("/test2")
        assert self.registry._route_cache is None

    def test_clear_endpoints(self):
        """Test clearing all endpoints."""
        handler = AsyncMock()
        self.registry.register_endpoint("/test1", handler)
        self.registry.register_endpoint("/test2", handler)

        assert len(self.registry.endpoints) == 2

        self.registry.clear_endpoints()
        assert len(self.registry.endpoints) == 0

    def test_clear_middleware(self):
        """Test clearing all middleware."""
        middleware1 = Mock()
        middleware1.__name__ = "Middleware1"
        middleware2 = Mock()
        middleware2.__name__ = "Middleware2"

        self.registry.register_middleware(middleware1)
        self.registry.register_middleware(middleware2)

        assert len(self.registry.middleware) == 2

        self.registry.clear_middleware()
        assert len(self.registry.middleware) == 0

    def test_clear_all(self):
        """Test clearing both endpoints and middleware."""
        handler = AsyncMock()
        middleware = Mock()
        middleware.__name__ = "TestMiddleware"

        self.registry.register_endpoint("/test", handler)
        self.registry.register_middleware(middleware)

        assert len(self.registry.endpoints) == 1
        assert len(self.registry.middleware) == 1

        self.registry.clear_all()
        assert len(self.registry.endpoints) == 0
        assert len(self.registry.middleware) == 0

    def test_get_stats(self):
        """Test getting registry statistics."""
        handler = AsyncMock()
        middleware = Mock()
        middleware.__name__ = "TestMiddleware"

        self.registry.register_endpoint("/api/users", handler, methods=["GET", "POST"])
        self.registry.register_endpoint("/api/data", handler, methods=["GET"])
        self.registry.register_middleware(middleware, priority=50)

        stats = self.registry.get_stats()

        assert stats["endpoints"]["total"] == 2
        assert stats["endpoints"]["by_method"]["GET"] == 2
        assert stats["endpoints"]["by_method"]["POST"] == 1
        assert "/api/users" in stats["endpoints"]["paths"]
        assert "/api/data" in stats["endpoints"]["paths"]

        assert stats["middleware"]["total"] == 1
        assert stats["middleware"]["by_priority"]["high (0-50)"] == 1

        assert stats["cache"]["is_cached"] is False
        assert stats["cache"]["route_count"] == 0

    def test_get_info(self):
        """Test getting comprehensive registry information."""
        handler = AsyncMock()
        middleware = Mock()

        self.registry.register_endpoint(
            "/test",
            handler,
            methods=["GET"],
            name="test_endpoint",
            description="Test endpoint",
            metadata={"version": "1.0"},
        )
        self.registry.register_middleware(
            middleware, priority=100, name="test_middleware", description="Test middleware"
        )

        info = self.registry.get_info()

        assert info["endpoints"]["count"] == 1
        endpoint_info = info["endpoints"]["registered"][0]
        assert endpoint_info["path"] == "/test"
        assert endpoint_info["name"] == "test_endpoint"
        assert endpoint_info["methods"] == ["GET"]
        assert endpoint_info["description"] == "Test endpoint"
        assert endpoint_info["metadata"] == {"version": "1.0"}

        assert info["middleware"]["count"] == 1
        middleware_info = info["middleware"]["registered"][0]
        assert middleware_info["name"] == "test_middleware"
        assert middleware_info["priority"] == 100
        assert middleware_info["description"] == "Test middleware"

        assert "stats" in info

    def test_count_by_method(self):
        """Test _count_by_method method."""
        handler = AsyncMock()

        self.registry.register_endpoint("/api1", handler, methods=["GET"])
        self.registry.register_endpoint("/api2", handler, methods=["GET", "POST"])
        self.registry.register_endpoint("/api3", handler, methods=["PUT"])

        method_counts = self.registry._count_by_method()

        assert method_counts["GET"] == 2
        assert method_counts["POST"] == 1
        assert method_counts["PUT"] == 1

    def test_count_by_priority(self):
        """Test _count_by_priority method."""
        middleware1 = Mock()
        middleware1.__name__ = "Middleware1"
        middleware2 = Mock()
        middleware2.__name__ = "Middleware2"
        middleware3 = Mock()
        middleware3.__name__ = "Middleware3"
        middleware4 = Mock()
        middleware4.__name__ = "Middleware4"

        self.registry.register_middleware(middleware1, priority=25)  # high
        self.registry.register_middleware(middleware2, priority=75)  # medium
        self.registry.register_middleware(middleware3, priority=150)  # low
        self.registry.register_middleware(middleware4, priority=50)  # high (boundary)

        priority_counts = self.registry._count_by_priority()

        assert priority_counts["high (0-50)"] == 2
        assert priority_counts["medium (51-100)"] == 1
        assert priority_counts["low (101+)"] == 1


class TestGlobalRegistryInstance:
    """Test the global registry instance."""

    def test_global_registry_exists(self):
        """Test that global registry instance exists."""
        assert http_endpoint_registry is not None
        assert isinstance(http_endpoint_registry, HTTPEndpointRegistry)

    def test_global_registry_auto_registration(self):
        """Test that registry info endpoint is auto-registered."""
        # Ensure auto-registration happens (in case other tests cleared the registry)
        if http_endpoint_registry.get_endpoint("/registry/endpoints") is None:
            from chuk_mcp_server.endpoint_registry import endpoint_registry_info_handler

            http_endpoint_registry.register_endpoint(
                "/registry/endpoints",
                endpoint_registry_info_handler,
                methods=["GET"],
                name="endpoint_registry_info",
                description="Information about registered HTTP endpoints and middleware",
            )

        config = http_endpoint_registry.get_endpoint("/registry/endpoints")
        assert config is not None
        assert config.name == "endpoint_registry_info"
        assert config.methods == ["GET"]


class TestConvenienceFunctions:
    """Test convenience functions."""

    def setup_method(self):
        """Clear global registry before each test."""
        http_endpoint_registry.clear_all()

    def test_register_endpoint_function(self):
        """Test register_endpoint convenience function."""
        handler = AsyncMock()

        register_endpoint("/test", handler, name="test")

        config = http_endpoint_registry.get_endpoint("/test")
        assert config is not None
        assert config.name == "test"

    def test_register_middleware_function(self):
        """Test register_middleware convenience function."""
        middleware_class = Mock()
        middleware_class.__name__ = "TestMiddleware"

        register_middleware(middleware_class, priority=50)

        middleware_configs = http_endpoint_registry.get_middleware()
        assert len(middleware_configs) >= 1  # Account for auto-registered endpoints
        # Find our middleware
        our_middleware = next((m for m in middleware_configs if m.priority == 50), None)
        assert our_middleware is not None

    def test_unregister_endpoint_function(self):
        """Test unregister_endpoint convenience function."""
        handler = AsyncMock()
        register_endpoint("/test", handler)

        result = unregister_endpoint("/test")
        assert result is True
        assert http_endpoint_registry.get_endpoint("/test") is None

    def test_get_endpoint_function(self):
        """Test get_endpoint convenience function."""
        handler = AsyncMock()
        register_endpoint("/test", handler)

        config = get_endpoint("/test")
        assert config is not None
        assert config.path == "/test"

    def test_list_endpoints_function(self):
        """Test list_endpoints convenience function."""
        handler = AsyncMock()
        register_endpoint("/test1", handler)
        register_endpoint("/test2", handler)

        endpoints = list_endpoints()
        assert len(endpoints) == 2


class TestDecorators:
    """Test decorator functions."""

    def setup_method(self):
        """Clear global registry before each test."""
        http_endpoint_registry.clear_all()

    def test_endpoint_decorator(self):
        """Test @endpoint decorator."""

        @endpoint("/api/test", methods=["GET", "POST"])
        async def test_handler(request):
            return Response("test")

        config = http_endpoint_registry.get_endpoint("/api/test")
        assert config is not None
        assert config.handler == test_handler
        assert config.methods == ["GET", "POST"]

    def test_endpoint_decorator_with_kwargs(self):
        """Test @endpoint decorator with additional kwargs."""

        @endpoint("/api/test", methods=["GET"], name="custom_name", description="Custom description")
        async def test_handler(request):
            return Response("test")

        config = http_endpoint_registry.get_endpoint("/api/test")
        assert config.name == "custom_name"
        assert config.description == "Custom description"

    def test_middleware_decorator(self):
        """Test @middleware decorator."""

        @middleware(priority=75, name="test_middleware")
        class TestMiddleware:
            def __init__(self, app):
                self.app = app

        middleware_configs = http_endpoint_registry.get_middleware()
        assert len(middleware_configs) == 1
        config = middleware_configs[0]
        assert config.middleware_class == TestMiddleware
        assert config.priority == 75
        assert config.name == "test_middleware"


class TestEndpointRegistryInfoHandler:
    """Test endpoint registry info handler."""

    @pytest.mark.asyncio
    async def test_endpoint_registry_info_handler(self):
        """Test the registry info handler."""
        request = Mock(spec=Request)

        # Add some test data to registry
        http_endpoint_registry.register_endpoint("/test", AsyncMock(), name="test")

        response = await endpoint_registry_info_handler(request)

        assert isinstance(response, Response)
        assert response.media_type == "application/json"
        assert response.headers["Access-Control-Allow-Origin"] == "*"

        # Response should contain orjson-formatted data
        assert response.body is not None
        assert len(response.body) > 0


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = HTTPEndpointRegistry()

    def test_register_endpoint_empty_path(self):
        """Test registering endpoint with empty path."""
        handler = AsyncMock()

        self.registry.register_endpoint("", handler)

        # Should be normalized to "/"
        assert "/" in self.registry.endpoints

    def test_register_endpoint_none_values(self):
        """Test registering endpoint with None values."""
        handler = AsyncMock()

        self.registry.register_endpoint("/test", handler, methods=None, name=None, metadata=None)

        config = self.registry.endpoints["/test"]
        assert config.methods == ["GET"]  # Default
        assert config.name == "test"  # Generated
        assert config.metadata == {}  # Default

    def test_get_routes_empty_registry(self):
        """Test getting routes from empty registry."""
        routes = self.registry.get_routes()
        assert routes == []

    def test_cache_invalidation_edge_cases(self):
        """Test cache invalidation edge cases."""
        # Test invalidation when cache is None
        self.registry._invalidate_cache()
        assert self.registry._route_cache is None

        # Test invalidation when cache exists
        self.registry._route_cache = []
        self.registry._invalidate_cache()
        assert self.registry._route_cache is None

    def test_stats_empty_registry(self):
        """Test getting stats from empty registry."""
        stats = self.registry.get_stats()

        assert stats["endpoints"]["total"] == 0
        assert stats["endpoints"]["by_method"] == {}
        assert stats["endpoints"]["paths"] == []
        assert stats["middleware"]["total"] == 0
        assert stats["cache"]["is_cached"] is False

    def test_complex_path_name_generation(self):
        """Test name generation for complex paths."""
        handler = AsyncMock()

        # Test path with multiple segments and special characters
        self.registry.register_endpoint("/api/v2/users-data", handler)
        config = self.registry.endpoints["/api/v2/users-data"]
        assert config.name == "api_v2_users-data"

        # Test path with trailing slash
        self.registry.register_endpoint("/api/test/", handler)
        config = self.registry.endpoints["/api/test/"]
        assert config.name == "api_test"
