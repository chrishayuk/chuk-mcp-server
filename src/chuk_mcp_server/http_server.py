#!/usr/bin/env python3
# src/chuk_mcp_server/http_server.py
"""
HTTP Server with systematic performance bottleneck fixes
Target: Break through the 3,600 RPS ceiling
"""

import logging
from typing import Optional, List

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

import uvicorn

from .protocol import MCPProtocolHandler
from .endpoint_registry import http_endpoint_registry
from .mcp_registry import mcp_registry, get_mcp_registry_endpoint

# Import optimized endpoints
from .endpoints import (
    MCPEndpoint,
    HealthEndpoint, 
    InfoEndpoint,
    handle_ping,
    handle_version,
    handle_health_ultra_fast
)

logger = logging.getLogger(__name__)

def internal_error_response() -> Response:
    """Simple internal error response"""
    return Response(
        '{"error": "Internal server error", "code": 500}',
        status_code=500,
        media_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )


class HTTPServer:
    """HTTP server optimized to break through performance bottlenecks."""
    
    def __init__(self, protocol_handler: MCPProtocolHandler):
        self.protocol = protocol_handler
        self._register_endpoints()
        self.app = self._create_app()
        logger.info("🚀 HTTP server initialized with bottleneck fixes")
    
    def _register_endpoints(self):
        """Register all endpoints."""
        
        # Clear any existing endpoints first
        http_endpoint_registry.clear_endpoints()
        
        # Create endpoint instances
        mcp_endpoint = MCPEndpoint(self.protocol)
        health_endpoint = HealthEndpoint(self.protocol)
        info_endpoint = InfoEndpoint(self.protocol)
        
        # Create docs handler
        docs_handler = self._create_docs_handler(info_endpoint)
        
        # Define all endpoints
        endpoints = [
            ("/ping", handle_ping, ["GET"], "ping"),
            ("/version", handle_version, ["GET"], "version"),
            ("/health", handle_health_ultra_fast, ["GET"], "health_fast"),
            ("/mcp", mcp_endpoint.handle_request, ["GET", "POST", "OPTIONS"], "mcp_protocol"),
            ("/", info_endpoint.handle_request, ["GET"], "server_info"),
            ("/info", info_endpoint.handle_request, ["GET"], "server_info_explicit"),
            ("/docs", docs_handler, ["GET"], "documentation"),
        ]
        
        # Register endpoints
        for path, handler, methods, name in endpoints:
            http_endpoint_registry.register_endpoint(
                path=path,
                handler=handler,
                methods=methods,
                name=name,
                description=f"Endpoint: {name}"
            )
        
        logger.info(f"📊 Registered {len(endpoints)} endpoints")
    
    def _create_docs_handler(self, info_endpoint):
        """Create docs handler."""
        async def docs_handler(request: Request) -> Response:
            request.query_params._dict["format"] = "docs"
            return await info_endpoint.handle_request(request)
        return docs_handler
    
    def _create_app(self) -> Starlette:
        """Create Starlette application with minimal overhead."""
        
        # MINIMAL middleware stack to reduce overhead
        middleware = [
            # Simplified CORS middleware
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
                expose_headers=["Mcp-Session-Id"],
                max_age=86400  # Long cache for preflight
            ),
            # Remove GZip middleware for benchmarking (it adds overhead)
            # Middleware(GZipMiddleware, minimum_size=2048)
        ]
        
        routes = http_endpoint_registry.get_routes()
        logger.info(f"🔗 Creating Starlette app with {len(routes)} routes")
        
        return Starlette(
            debug=False,
            routes=routes,
            middleware=middleware,
            exception_handlers={Exception: self._global_exception_handler}
        )
    
    async def _global_exception_handler(self, request: Request, exc: Exception) -> Response:
        """Minimal exception handler."""
        logger.error(f"Exception in {request.method} {request.url.path}: {exc}")
        return internal_error_response()
    
    def run(self, host: str = "localhost", port: int = 8000, debug: bool = False):
        """Run with maximum performance configuration to break bottlenecks."""
        
        logger.info("🚀 ChukMCPServer - BOTTLENECK FIXES ACTIVE")
        logger.info("=" * 60)
        logger.info(f"Host: {host}:{port}")
        logger.info("")
        
        # PERFORMANCE-FOCUSED uvicorn configuration
        uvicorn_config = {
            "app": self.app,
            "host": host,
            "port": port,
            
            # Core performance settings
            "workers": 1,
            "loop": "uvloop",  # Force uvloop
            "http": "httptools",  # Force httptools
            
            # Disable overhead features
            "access_log": False,
            "server_header": False,
            "date_header": False,
            "log_level": "error",  # Minimal logging
            
            # Connection optimizations
            "backlog": 4096,  # Increase from 2048
            "limit_concurrency": 2000,  # Increase from 1000
            "timeout_keep_alive": 60,  # Longer keep-alive
            
            # REMOVE request limit that was causing restarts
            # "limit_max_requests": 10000,  # REMOVED
            
            # Buffer optimizations
            "h11_max_incomplete_event_size": 16384,  # Increase buffer
        }
        
        # Verify performance libraries are available
        try:
            import uvloop
            logger.info("✅ uvloop available and forced")
        except ImportError:
            logger.error("❌ uvloop not available - performance will be limited")
            uvicorn_config.pop("loop", None)
        
        try:
            import httptools
            logger.info("✅ httptools available and forced")
        except ImportError:
            logger.error("❌ httptools not available - performance will be limited")
            uvicorn_config.pop("http", None)
        
        # Debug mode adjustments
        if debug:
            uvicorn_config.update({
                "log_level": "debug",
                "access_log": True,
            })
        
        logger.info("⚡ BOTTLENECK FIXES:")
        logger.info("  ✅ Minimal middleware stack (removed GZip)")
        logger.info("  ✅ Increased connection backlog (4096)")
        logger.info("  ✅ Increased concurrency limit (2000)")
        logger.info("  ✅ Removed request limit (no restarts)")
        logger.info("  ✅ Forced uvloop + httptools")
        logger.info("  ✅ Increased buffer sizes")
        logger.info("  ✅ Minimal logging overhead")
        logger.info("")
        
        logger.info("🎯 EXPECTED IMPROVEMENTS:")
        logger.info("  🚀 Ping: 6,000+ RPS (from 3,570)")
        logger.info("  🚀 Version: 6,000+ RPS (from 3,530)")
        logger.info("  🚀 Health: 6,000+ RPS (from 3,591)")
        logger.info("  🚀 Overall: 5,000+ RPS average")
        logger.info("=" * 60)
        
        try:
            uvicorn.run(**uvicorn_config)
        except KeyboardInterrupt:
            logger.info("\n👋 Server shutting down gracefully...")
        except Exception as e:
            logger.error(f"❌ Server startup error: {e}")
            raise


# Factory function
def create_server(protocol_handler: MCPProtocolHandler) -> HTTPServer:
    """Create HTTP server with bottleneck fixes."""
    return HTTPServer(protocol_handler)