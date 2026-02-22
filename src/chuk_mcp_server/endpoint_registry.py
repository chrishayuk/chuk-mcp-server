#!/usr/bin/env python3
"""
Endpoint Registry - HTTP endpoint registration and management
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

# starlette
from starlette.routing import Route

from .constants import CONTENT_TYPE_JSON, CORS_ALLOW_ALL, HEADER_CORS_ORIGIN

# logger
logger = logging.getLogger(__name__)


# ============================================================================
# Endpoint Registry Data Structures
# ============================================================================


@dataclass
class EndpointConfig:
    """Configuration for a registered HTTP endpoint."""

    path: str
    handler: Callable
    methods: list[str]
    name: str
    description: str
    middleware: list[Any] | None = None
    metadata: dict[str, Any] | None = None
    registered_at: float = None

    def __post_init__(self):
        if self.registered_at is None:
            self.registered_at = time.time()


@dataclass
class MiddlewareConfig:
    """Configuration for registered middleware."""

    middleware_class: Any
    args: tuple = ()
    kwargs: dict[str, Any] = None
    priority: int = 100  # Lower numbers run first
    name: str = ""
    description: str = ""
    registered_at: float = None

    def __post_init__(self):
        if self.registered_at is None:
            self.registered_at = time.time()
        if self.kwargs is None:
            self.kwargs = {}


# ============================================================================
# HTTP Endpoint Registry
# ============================================================================


class HTTPEndpointRegistry:
    """Registry for custom HTTP endpoint handlers."""

    def __init__(self):
        self.endpoints: dict[str, EndpointConfig] = {}
        self.middleware: list[MiddlewareConfig] = []
        self._route_cache: list[Route] | None = None

        logger.debug("HTTP endpoint registry initialized")

    def register_endpoint(
        self,
        path: str,
        handler: Callable,
        methods: list[str] = None,
        name: str = None,
        description: str = "",
        middleware: list[Any] = None,
        metadata: dict[str, Any] = None,
    ):
        """
        Register a custom HTTP endpoint.

        Args:
            path: URL path for the endpoint (e.g., "/api/data")
            handler: Async function to handle requests
            methods: HTTP methods to support (default: ["GET"])
            name: Human-readable name for the endpoint
            description: Description of endpoint functionality
            middleware: Endpoint-specific middleware
            metadata: Additional metadata for the endpoint
        """
        if methods is None:
            methods = ["GET"]

        if name is None:
            name = path.strip("/").replace("/", "_") or "root"

        if metadata is None:
            metadata = {}

        # Validate path
        if not path.startswith("/"):
            path = "/" + path

        config = EndpointConfig(
            path=path,
            handler=handler,
            methods=methods,
            name=name,
            description=description,
            middleware=middleware,
            metadata=metadata,
        )

        self.endpoints[path] = config
        self._invalidate_cache()

        logger.info(f"📍 Registered endpoint: {path} ({', '.join(methods)}) - {name}")

    def register_middleware(
        self, middleware_class: Any, *args, priority: int = 100, name: str = "", description: str = "", **kwargs
    ):
        """
        Register global HTTP middleware.

        Args:
            middleware_class: Middleware class to register
            *args: Positional arguments for middleware
            priority: Priority order (lower numbers run first)
            name: Human-readable name
            description: Description of middleware functionality
            **kwargs: Keyword arguments for middleware
        """
        config = MiddlewareConfig(
            middleware_class=middleware_class,
            args=args,
            kwargs=kwargs,
            priority=priority,
            name=name or middleware_class.__name__,
            description=description,
        )

        self.middleware.append(config)
        self.middleware.sort(key=lambda x: x.priority)
        self._invalidate_cache()

        logger.info(f"🔧 Registered middleware: {config.name} (priority: {priority})")

    def unregister_endpoint(self, path: str):
        """Unregister an HTTP endpoint."""
        if path in self.endpoints:
            config = self.endpoints.pop(path)
            self._invalidate_cache()
            logger.info(f"🗑️ Unregistered endpoint: {path} - {config.name}")
            return True
        else:
            logger.warning(f"⚠️ Attempted to unregister non-existent endpoint: {path}")
            return False

    def get_endpoint(self, path: str) -> EndpointConfig | None:
        """Get endpoint configuration by path."""
        return self.endpoints.get(path)

    def list_endpoints(self) -> list[EndpointConfig]:
        """Get list of all registered endpoints."""
        return list(self.endpoints.values())

    def get_routes(self) -> list[Route]:
        """Get Starlette routes for all registered endpoints."""
        if self._route_cache is None:
            routes = []

            for config in self.endpoints.values():
                route = Route(config.path, config.handler, methods=config.methods, name=config.name)
                routes.append(route)

            self._route_cache = routes
            logger.debug(f"Generated {len(routes)} routes from registry")

        return self._route_cache.copy()

    def get_middleware(self) -> list[MiddlewareConfig]:
        """Get list of registered middleware ordered by priority."""
        return self.middleware.copy()

    def _invalidate_cache(self):
        """Invalidate the route cache."""
        if self._route_cache is not None:
            logger.debug("Invalidated route cache")
        self._route_cache = None

    def clear_endpoints(self):
        """Clear all registered endpoints."""
        count = len(self.endpoints)
        self.endpoints.clear()
        self._invalidate_cache()
        logger.info(f"🗑️ Cleared {count} endpoints from registry")

    def clear_middleware(self):
        """Clear all registered middleware."""
        count = len(self.middleware)
        self.middleware.clear()
        self._invalidate_cache()
        logger.info(f"🗑️ Cleared {count} middleware from registry")

    def clear_all(self):
        """Clear all registered endpoints and middleware."""
        self.clear_endpoints()
        self.clear_middleware()

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        return {
            "endpoints": {
                "total": len(self.endpoints),
                "by_method": self._count_by_method(),
                "paths": list(self.endpoints.keys()),
            },
            "middleware": {"total": len(self.middleware), "by_priority": self._count_by_priority()},
            "cache": {
                "is_cached": self._route_cache is not None,
                "route_count": len(self._route_cache) if self._route_cache else 0,
            },
        }

    def get_info(self) -> dict[str, Any]:
        """Get comprehensive registry information."""
        return {
            "endpoints": {
                "count": len(self.endpoints),
                "registered": [
                    {
                        "path": config.path,
                        "name": config.name,
                        "methods": config.methods,
                        "description": config.description,
                        "registered_at": config.registered_at,
                        "metadata": config.metadata,
                    }
                    for config in self.endpoints.values()
                ],
            },
            "middleware": {
                "count": len(self.middleware),
                "registered": [
                    {
                        "name": config.name,
                        "priority": config.priority,
                        "description": config.description,
                        "registered_at": config.registered_at,
                    }
                    for config in self.middleware
                ],
            },
            "stats": self.get_stats(),
        }

    def _count_by_method(self) -> dict[str, int]:
        """Count endpoints by HTTP method."""
        method_counts = {}
        for config in self.endpoints.values():
            for method in config.methods:
                method_counts[method] = method_counts.get(method, 0) + 1
        return method_counts

    def _count_by_priority(self) -> dict[str, int]:
        """Count middleware by priority range."""
        priority_ranges = {"high (0-50)": 0, "medium (51-100)": 0, "low (101+)": 0}

        for config in self.middleware:
            if config.priority <= 50:
                priority_ranges["high (0-50)"] += 1
            elif config.priority <= 100:
                priority_ranges["medium (51-100)"] += 1
            else:
                priority_ranges["low (101+)"] += 1

        return priority_ranges


# ============================================================================
# Global Registry Instance
# ============================================================================

# Global instance for use throughout the application
http_endpoint_registry = HTTPEndpointRegistry()


# ============================================================================
# Convenience Functions
# ============================================================================


def register_endpoint(path: str, handler: Callable, **kwargs):
    """Convenience function to register an HTTP endpoint."""
    return http_endpoint_registry.register_endpoint(path, handler, **kwargs)


def register_middleware(middleware_class: Any, **kwargs):
    """Convenience function to register HTTP middleware."""
    return http_endpoint_registry.register_middleware(middleware_class, **kwargs)


def unregister_endpoint(path: str):
    """Convenience function to unregister an HTTP endpoint."""
    return http_endpoint_registry.unregister_endpoint(path)


def get_endpoint(path: str):
    """Convenience function to get endpoint configuration."""
    return http_endpoint_registry.get_endpoint(path)


def list_endpoints():
    """Convenience function to list all registered endpoints."""
    return http_endpoint_registry.list_endpoints()


# ============================================================================
# Decorators
# ============================================================================


def endpoint(path: str, methods: list[str] = None, **kwargs):
    """
    Decorator to register an HTTP endpoint.

    Usage:
        @endpoint("/api/data", methods=["GET", "POST"])
        async def data_handler(request):
            return Response('{"status": "ok"}')
    """

    def decorator(handler: Callable):
        register_endpoint(path, handler, methods=methods, **kwargs)
        return handler

    return decorator


def middleware(priority: int = 100, **kwargs):
    """
    Decorator to register HTTP middleware.

    Usage:
        @middleware(priority=50, name="auth")
        class AuthMiddleware:
            def __init__(self, app):
                self.app = app
    """

    def decorator(middleware_class: Any):
        register_middleware(middleware_class, priority=priority, **kwargs)
        return middleware_class

    return decorator


# ============================================================================
# Registry Information Endpoint
# ============================================================================


async def endpoint_registry_info_handler(_request: Request) -> Response:
    """Handler for endpoint registry information."""
    import orjson

    info = {
        "registry_type": "HTTP Endpoint Registry",
        "description": "Manages custom HTTP endpoints and middleware",
        "data": http_endpoint_registry.get_info(),
    }

    return Response(
        orjson.dumps(info, option=orjson.OPT_INDENT_2),
        media_type=CONTENT_TYPE_JSON,
        headers={HEADER_CORS_ORIGIN: CORS_ALLOW_ALL},
    )


# Auto-register the registry info endpoint
http_endpoint_registry.register_endpoint(
    "/registry/endpoints",
    endpoint_registry_info_handler,
    methods=["GET"],
    name="endpoint_registry_info",
    description="Information about registered HTTP endpoints and middleware",
)
