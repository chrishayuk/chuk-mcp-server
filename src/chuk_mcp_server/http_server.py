#!/usr/bin/env python3
"""
HTTP Server - Registry-driven HTTP server implementation
"""

import logging
from typing import Optional, List

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response

import uvicorn

from .protocol import MCPProtocolHandler
from .endpoint_registry import http_endpoint_registry
from .mcp_registry import mcp_registry, get_mcp_registry_endpoint
from .endpoints import MCPEndpoint, HealthEndpoint, InfoEndpoint

logger = logging.getLogger(__name__)


# ============================================================================
# Registry-Driven HTTP Server Implementation
# ============================================================================

class HTTPServer:
    """HTTP server for MCP with registry-driven architecture."""
    
    def __init__(self, protocol_handler: MCPProtocolHandler):
        self.protocol = protocol_handler
        
        # Register core endpoints in the registry
        self._register_core_endpoints()
        
        # Create Starlette application
        self.app = self._create_app()
        
        logger.info("HTTP server initialized with registry-driven architecture")
    
    def _register_core_endpoints(self):
        """Register core ChukMCPServer endpoints in the endpoint registry."""
        
        # Create endpoint handlers
        mcp_endpoint = MCPEndpoint(self.protocol)
        health_endpoint = HealthEndpoint(self.protocol)
        info_endpoint = InfoEndpoint(self.protocol)
        
        # Register core MCP endpoint
        http_endpoint_registry.register_endpoint(
            path="/mcp",
            handler=mcp_endpoint.handle_request,
            methods=["GET", "POST", "OPTIONS"],
            name="mcp_protocol",
            description="Core MCP protocol endpoint with SSE support",
            metadata={
                "core": True,
                "protocol": "MCP 2025-03-26",
                "features": ["json-rpc", "sse", "session_management"]
            }
        )
        
        # Register health endpoints
        http_endpoint_registry.register_endpoint(
            path="/health",
            handler=health_endpoint.handle_request,
            methods=["GET"],
            name="health_check",
            description="Server health check and diagnostics",
            metadata={"core": True, "category": "monitoring"}
        )
        
        http_endpoint_registry.register_endpoint(
            path="/status",
            handler=health_endpoint.handle_request,
            methods=["GET"],
            name="status_check",
            description="Server status (alias for health)",
            metadata={"core": True, "category": "monitoring", "alias_for": "/health"}
        )
        
        # Register info endpoints
        http_endpoint_registry.register_endpoint(
            path="/",
            handler=info_endpoint.handle_request,
            methods=["GET"],
            name="server_info",
            description="Comprehensive server information",
            metadata={"core": True, "category": "information"}
        )
        
        http_endpoint_registry.register_endpoint(
            path="/info",
            handler=info_endpoint.handle_request,
            methods=["GET"],
            name="server_info_explicit",
            description="Server information (explicit path)",
            metadata={"core": True, "category": "information", "alias_for": "/"}
        )
        
        # Register docs endpoint with custom handler
        async def docs_handler(request: Request) -> Response:
            # Force docs format
            request.query_params._dict["format"] = "docs"
            return await info_endpoint.handle_request(request)
        
        http_endpoint_registry.register_endpoint(
            path="/docs",
            handler=docs_handler,
            methods=["GET"],
            name="documentation",
            description="Server documentation in Markdown format",
            metadata={"core": True, "category": "documentation", "format": "markdown"}
        )
        
        # Register utility ping endpoint
        async def ping_handler(request: Request) -> Response:
            return Response(
                '{"status": "pong", "server": "ChukMCPServer", "timestamp": ' + str(time.time()) + '}',
                media_type="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        http_endpoint_registry.register_endpoint(
            path="/ping",
            handler=ping_handler,
            methods=["GET"],
            name="ping",
            description="Simple connectivity test",
            metadata={"core": True, "category": "utility"}
        )
        
        # Register MCP registry endpoint
        mcp_endpoint_config = get_mcp_registry_endpoint()
        http_endpoint_registry.register_endpoint(
            path=mcp_endpoint_config["path"],
            handler=mcp_endpoint_config["handler"],
            methods=mcp_endpoint_config["methods"],
            name=mcp_endpoint_config["name"],
            description=mcp_endpoint_config["description"],
            metadata={"core": True, "category": "registry", "registry_type": "mcp"}
        )
        
        logger.info(f"Registered {len(http_endpoint_registry.list_endpoints())} core endpoints")
    
    def _create_app(self) -> Starlette:
        """Create Starlette application using registries."""
        
        # Get middleware from registry
        middleware_configs = http_endpoint_registry.get_middleware()
        middleware = self._build_middleware_stack(middleware_configs)
        
        # Get routes from registry
        routes = http_endpoint_registry.get_routes()
        
        logger.info(f"Created app with {len(routes)} routes and {len(middleware)} middleware")
        
        return Starlette(
            debug=False,
            routes=routes,
            middleware=middleware,
            exception_handlers={
                Exception: self._global_exception_handler
            }
        )
    
    def _build_middleware_stack(self, middleware_configs: List) -> List[Middleware]:
        """Build middleware stack from registry plus defaults."""
        
        # Start with default ChukMCPServer middleware
        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
                expose_headers=["Mcp-Session-Id", "MCP-Protocol-Version"],
                max_age=3600
            ),
            Middleware(GZipMiddleware, minimum_size=1000)
        ]
        
        # Add registered middleware (sorted by priority)
        for config in middleware_configs:
            try:
                middleware_instance = Middleware(
                    config.middleware_class,
                    *config.args,
                    **config.kwargs
                )
                middleware.append(middleware_instance)
                logger.debug(f"Added middleware: {config.name}")
            except Exception as e:
                logger.error(f"Failed to add middleware {config.name}: {e}")
        
        return middleware
    
    async def _global_exception_handler(self, request: Request, exc: Exception) -> Response:
        """Global exception handler for unhandled errors."""
        import traceback
        import orjson
        
        logger.error(f"Unhandled exception in {request.method} {request.url}: {exc}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return a safe error response
        error_response = {
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "status": 500,
            "path": str(request.url.path),
            "method": request.method
        }
        
        return Response(
            orjson.dumps(error_response),
            status_code=500,
            media_type="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    
    def add_custom_routes(self, routes: List[Route]):
        """Add custom routes to the application (for advanced use cases)."""
        # This would require rebuilding the app, which is complex
        # Better to use the registry system instead
        logger.warning("Use endpoint registry for adding routes instead of add_custom_routes")
    
    def get_route_info(self) -> dict:
        """Get information about all registered routes."""
        endpoint_configs = http_endpoint_registry.list_endpoints()
        
        return {
            "total_routes": len(endpoint_configs),
            "core_routes": len([c for c in endpoint_configs if c.metadata.get("core", False)]),
            "custom_routes": len([c for c in endpoint_configs if not c.metadata.get("core", False)]),
            "routes": [
                {
                    "path": config.path,
                    "name": config.name,
                    "methods": config.methods,
                    "description": config.description,
                    "is_core": config.metadata.get("core", False),
                    "category": config.metadata.get("category", "custom")
                }
                for config in endpoint_configs
            ]
        }
    
    def run(self, host: str = "localhost", port: int = 8000, debug: bool = False):
        """Run the HTTP server with comprehensive logging."""
        
        self._log_startup_info(host, port, debug)
        
        # Configure uvicorn settings
        uvicorn_config = {
            "app": self.app,
            "host": host,
            "port": port,
            "log_level": "info" if debug else "warning",
            "access_log": debug,
            "server_header": False,
            "date_header": True,
        }
        
        if debug:
            uvicorn_config["reload"] = False
            uvicorn_config["log_level"] = "debug"
        
        # Start the server
        try:
            uvicorn.run(**uvicorn_config)
        except KeyboardInterrupt:
            logger.info("\n👋 Server shutting down gracefully...")
        except Exception as e:
            logger.error(f"❌ Server startup error: {e}")
            raise
    
    def _log_startup_info(self, host: str, port: int, debug: bool):
        """Log comprehensive startup information."""
        import time
        
        logger.info("🚀 Starting ChukMCPServer HTTP Server")
        logger.info("=" * 60)
        logger.info(f"Server: {self.protocol.server_info.name}")
        logger.info(f"Version: {self.protocol.server_info.version}")
        logger.info(f"Host: {host}:{port}")
        logger.info(f"Debug: {debug}")
        logger.info(f"Framework: ChukMCPServer with chuk_mcp")
        logger.info("")
        
        # Log MCP capabilities
        logger.info("📋 MCP Capabilities:")
        logger.info(f"  Tools: {len(self.protocol.tools)}")
        logger.info(f"  Resources: {len(self.protocol.resources)}")
        logger.info(f"  Sessions: {len(self.protocol.session_manager.sessions)}")
        
        if self.protocol.tools:
            logger.info("  🔧 Available tools:")
            for tool_name in list(self.protocol.tools.keys())[:5]:  # Show first 5
                logger.info(f"     - {tool_name}")
            if len(self.protocol.tools) > 5:
                logger.info(f"     ... and {len(self.protocol.tools) - 5} more")
        
        if self.protocol.resources:
            logger.info("  📂 Available resources:")
            for resource_uri in list(self.protocol.resources.keys())[:3]:  # Show first 3
                logger.info(f"     - {resource_uri}")
            if len(self.protocol.resources) > 3:
                logger.info(f"     ... and {len(self.protocol.resources) - 3} more")
        
        logger.info("")
        
        # Log HTTP endpoints from registry
        route_info = self.get_route_info()
        logger.info("🔗 HTTP Endpoints:")
        logger.info(f"  Total: {route_info['total_routes']} (Core: {route_info['core_routes']}, Custom: {route_info['custom_routes']})")
        
        # Group by category
        categories = {}
        for route in route_info['routes']:
            category = route['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(route)
        
        for category, routes in categories.items():
            logger.info(f"  📁 {category.title()}:")
            for route in routes:
                methods_str = ', '.join(route['methods'])
                logger.info(f"     {route['path']} ({methods_str}) - {route['description']}")
        
        logger.info("")
        
        # Log registry statistics
        endpoint_stats = http_endpoint_registry.get_stats()
        mcp_stats = mcp_registry.get_stats()
        
        logger.info("📊 Registry Statistics:")
        logger.info(f"  HTTP Endpoints: {endpoint_stats['endpoints']['total']}")
        logger.info(f"  MCP Components: {mcp_stats['total_components']}")
        logger.info(f"  Component Tags: {mcp_stats['tags']['total_unique']}")
        logger.info("")
        
        # Log Inspector compatibility
        logger.info("🔍 MCP Inspector Compatibility:")
        logger.info("  ✅ SSE streaming supported")
        logger.info("  ✅ Session management enabled")
        logger.info("  ✅ Protocol 2025-03-26 compatible")
        logger.info("  📝 Use proxy for Inspector connection")
        logger.info("")
        
        # Log key URLs
        logger.info("🌐 Key URLs:")
        logger.info(f"  MCP Protocol: http://{host}:{port}/mcp")
        logger.info(f"  Health Check: http://{host}:{port}/health")
        logger.info(f"  Documentation: http://{host}:{port}/docs")
        logger.info(f"  Registry Info: http://{host}:{port}/registry/endpoints")
        logger.info("=" * 60)


# ============================================================================
# Server Factory
# ============================================================================

def create_server(protocol_handler: MCPProtocolHandler) -> HTTPServer:
    """Create HTTP server with protocol handler."""
    return HTTPServer(protocol_handler)


def create_server_from_config(server_config: dict, protocol_handler: MCPProtocolHandler) -> HTTPServer:
    """Create HTTP server from configuration dictionary."""
    server = HTTPServer(protocol_handler)
    
    # Apply server-specific configuration
    if "custom_endpoints" in server_config:
        for endpoint_config in server_config["custom_endpoints"]:
            http_endpoint_registry.register_endpoint(**endpoint_config)
    
    if "middleware" in server_config:
        for middleware_config in server_config["middleware"]:
            http_endpoint_registry.register_middleware(**middleware_config)
    
    return server


def create_minimal_server(protocol_handler: MCPProtocolHandler) -> HTTPServer:
    """Create minimal server with only essential endpoints."""
    # Clear any existing registrations
    http_endpoint_registry.clear_endpoints()
    
    # Register only essential endpoints
    from .endpoints import MCPEndpoint
    
    mcp_endpoint = MCPEndpoint(protocol_handler)
    http_endpoint_registry.register_endpoint(
        "/mcp", mcp_endpoint.handle_request, ["GET", "POST", "OPTIONS"],
        name="mcp_only", description="MCP protocol only"
    )
    
    return HTTPServer(protocol_handler)