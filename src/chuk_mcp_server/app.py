#!/usr/bin/env python3
"""
app.py - Updated Main Server Application

Creates and configures the Starlette application with modular endpoints
organized by functionality for better maintainability and optimization.
"""

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

# Import endpoint modules
from .endpoints.mcp import (
    mcp_endpoint,
    mcp_initialize_endpoint,
    mcp_ping_endpoint,
    mcp_tools_endpoint,
    mcp_resources_endpoint,
    mcp_sessions_endpoint,
    mcp_performance_endpoint
)

from .endpoints.health import (
    health_endpoint,
    health_detailed_endpoint,
    readiness_endpoint,
    liveness_endpoint,
    metrics_endpoint,
    prometheus_metrics_endpoint,
    status_endpoint,
    ping_endpoint,
    version_endpoint
)

from .endpoints.info import (
    root_endpoint,
    info_endpoint,
    api_discovery_endpoint,
    tools_info_endpoint,
    resources_info_endpoint,
    help_endpoint
)


# ============================================================================
# Application Factory
# ============================================================================

def create_app(debug: bool = False) -> Starlette:
    """
    Create and configure the Starlette application with modular endpoints
    
    Args:
        debug: Enable debug mode (adds logging, etc.)
    
    Returns:
        Configured Starlette application
    """
    
    # Middleware stack - order matters for performance
    middleware = [
        # CORS - must be first for preflight handling
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["Mcp-Session-Id", "Content-Length"],
            max_age=3600  # Cache preflight for 1 hour
        ),
        
        # GZip compression for larger responses
        Middleware(
            GZipMiddleware,
            minimum_size=1000,  # Only compress responses > 1KB
            compresslevel=6     # Balance speed vs compression
        ),
    ]
    
    # Routes organized by frequency and functionality
    routes = [
        # ====================================================================
        # Core MCP Protocol Endpoints (highest frequency)
        # ====================================================================
        Route("/mcp", mcp_endpoint, methods=["POST"]),
        
        # Direct MCP endpoints for convenience/testing
        Route("/mcp/initialize", mcp_initialize_endpoint, methods=["POST"]),
        Route("/mcp/ping", mcp_ping_endpoint, methods=["GET"]),
        Route("/mcp/tools", mcp_tools_endpoint, methods=["GET", "POST"]),
        Route("/mcp/resources", mcp_resources_endpoint, methods=["GET"]),
        Route("/mcp/sessions", mcp_sessions_endpoint, methods=["GET", "DELETE"]),
        Route("/mcp/performance", mcp_performance_endpoint, methods=["GET"]),
        
        # ====================================================================
        # Health and Monitoring Endpoints (high frequency)
        # ====================================================================
        Route("/health", health_endpoint, methods=["GET"]),
        Route("/health/detailed", health_detailed_endpoint, methods=["GET"]),
        Route("/readiness", readiness_endpoint, methods=["GET"]),
        Route("/liveness", liveness_endpoint, methods=["GET"]),
        Route("/ping", ping_endpoint, methods=["GET"]),
        Route("/status", status_endpoint, methods=["GET"]),  # Alias for health
        
        # Metrics endpoints
        Route("/metrics", metrics_endpoint, methods=["GET"]),
        Route("/metrics/prometheus", prometheus_metrics_endpoint, methods=["GET"]),
        
        # ====================================================================
        # Information and Discovery Endpoints (medium frequency)
        # ====================================================================
        Route("/", root_endpoint, methods=["GET"]),
        Route("/info", info_endpoint, methods=["GET"]),
        Route("/version", version_endpoint, methods=["GET"]),
        
        # API discovery and documentation
        Route("/api", api_discovery_endpoint, methods=["GET"]),
        Route("/tools", tools_info_endpoint, methods=["GET"]),
        Route("/resources", resources_info_endpoint, methods=["GET"]),
        Route("/help", help_endpoint, methods=["GET"]),
        
        # ====================================================================
        # Convenience aliases and shortcuts
        # ====================================================================
        Route("/docs", api_discovery_endpoint, methods=["GET"]),  # Alias for /api
        Route("/openapi", api_discovery_endpoint, methods=["GET"]),  # OpenAPI spec
    ]
    
    # Create application
    app = Starlette(
        debug=debug,
        routes=routes,
        middleware=middleware
    )
    
    # Add event handlers
    app.add_event_handler("startup", startup_handler)
    app.add_event_handler("shutdown", shutdown_handler)
    
    return app


# ============================================================================
# Event Handlers
# ============================================================================

async def startup_handler():
    """Application startup handler"""
    from .models import get_state
    
    state = get_state()
    print(f"🚀 Fast MCP Server starting...")
    print(f"   📋 Modular endpoint architecture")
    print(f"   📊 Metrics initialized")
    print(f"   🔧 {len(state.get_tools())} tools available")
    print(f"   📄 {len(state.get_resources())} resources available")
    print(f"   🌐 REST and MCP endpoints ready")
    print(f"   ⚡ Ready for high-performance requests")


async def shutdown_handler():
    """Application shutdown handler"""
    from .models import get_state
    
    state = get_state()
    uptime = state.metrics.uptime()
    total_requests = state.metrics.total_requests
    avg_rps = state.metrics.rps()
    
    print(f"📊 Fast MCP Server shutdown statistics:")
    print(f"   ⏱️  Uptime: {uptime:.1f} seconds")
    print(f"   📨 Total requests: {total_requests}")
    print(f"   ⚡ Average RPS: {avg_rps:.1f}")
    print(f"   🔧 Tool calls: {state.metrics.tool_calls}")
    print(f"   📖 Resource reads: {state.metrics.resource_reads}")
    print(f"   ❌ Errors: {state.metrics.errors}")
    print(f"   🧹 Session cleanup performed")
    print(f"👋 Goodbye!")


# ============================================================================
# Enhanced Configuration Classes
# ============================================================================

class ServerConfig:
    """Enhanced server configuration with endpoint-specific settings"""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        workers: int = 1,
        debug: bool = False,
        auto_reload: bool = False,
        
        # Performance settings
        max_concurrency: int = 10000,
        backlog: int = 4096,
        keepalive_timeout: int = 5,
        
        # Endpoint settings
        enable_direct_mcp: bool = True,
        enable_rest_endpoints: bool = True,
        enable_prometheus: bool = True,
        
        # Logging
        log_level: str = "error",
        access_log: bool = False,
    ):
        self.host = host
        self.port = port
        self.workers = workers
        self.debug = debug
        self.auto_reload = auto_reload
        
        # Performance
        self.max_concurrency = max_concurrency
        self.backlog = backlog
        self.keepalive_timeout = keepalive_timeout
        
        # Endpoints
        self.enable_direct_mcp = enable_direct_mcp
        self.enable_rest_endpoints = enable_rest_endpoints
        self.enable_prometheus = enable_prometheus
        
        # Logging
        self.log_level = log_level
        self.access_log = access_log
    
    def get_uvicorn_config(self) -> dict:
        """Get uvicorn configuration dictionary"""
        config = {
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "log_level": self.log_level,
            "access_log": self.access_log,
            "limit_concurrency": self.max_concurrency,
            "backlog": self.backlog,
            "timeout_keep_alive": self.keepalive_timeout,
        }
        
        # Add performance optimizations for production
        if not self.debug:
            config.update({
                "loop": "uvloop",       # Faster event loop
                "http": "httptools",    # Faster HTTP parser
            })
        
        # Development settings
        if self.debug or self.auto_reload:
            config.update({
                "reload": self.auto_reload,
                "log_level": "info",
                "access_log": True,
            })
        
        return config
    
    def print_info(self):
        """Print server configuration info with endpoint details"""
        print("🚀 Fast MCP Server Configuration")
        print("=" * 60)
        print(f"Host: {self.host}")
        print(f"Port: {self.port}")
        print(f"Workers: {self.workers}")
        print(f"Debug: {self.debug}")
        print(f"Max Concurrency: {self.max_concurrency}")
        print(f"Backlog: {self.backlog}")
        print(f"Keep-Alive Timeout: {self.keepalive_timeout}s")
        print()
        
        # Endpoint categories
        base_url = f"http://{self.host}:{self.port}"
        
        print("🌐 Core MCP Protocol Endpoints:")
        print(f"  POST {base_url}/mcp                    - Main MCP JSON-RPC endpoint")
        if self.enable_direct_mcp:
            print(f"  POST {base_url}/mcp/initialize         - Direct initialize")
            print(f"  GET  {base_url}/mcp/ping               - Direct ping")
            print(f"  GET  {base_url}/mcp/tools              - List tools (REST)")
            print(f"  POST {base_url}/mcp/tools              - Call tool (REST)")
            print(f"  GET  {base_url}/mcp/resources          - List/read resources")
        print()
        
        print("💚 Health and Monitoring:")
        print(f"  GET  {base_url}/health                 - Fast health check")
        print(f"  GET  {base_url}/health/detailed        - Detailed health")
        print(f"  GET  {base_url}/readiness              - Kubernetes readiness")
        print(f"  GET  {base_url}/liveness               - Kubernetes liveness")
        print(f"  GET  {base_url}/metrics                - JSON metrics")
        if self.enable_prometheus:
            print(f"  GET  {base_url}/metrics/prometheus     - Prometheus metrics")
        print()
        
        if self.enable_rest_endpoints:
            print("📋 Information and Discovery:")
            print(f"  GET  {base_url}/                       - Server information")
            print(f"  GET  {base_url}/info                   - Detailed server info")
            print(f"  GET  {base_url}/api                    - API discovery")
            print(f"  GET  {base_url}/tools                  - Tools information")
            print(f"  GET  {base_url}/resources              - Resources information")
            print(f"  GET  {base_url}/help                   - Text help")
            print()
        
        # Show available tools and resources
        from .models import get_state
        state = get_state()
        
        tools = state.get_tools()
        print(f"🔧 Available Tools ({len(tools)}):")
        for tool in tools:
            print(f"  • {tool['name']}: {tool['description']}")
        
        resources = state.get_resources()
        print(f"\n📄 Available Resources ({len(resources)}):")
        for resource in resources:
            print(f"  • {resource['name']}: {resource['description']}")
        
        print()
        print("🎯 Performance Targets:")
        print("  • 10,000+ RPS for core operations")
        print("  • Sub-millisecond response times") 
        print("  • High concurrency support")
        print("  • Minimal memory footprint")
        print("  • Modular endpoint architecture")
        print()
        print("🧪 Test Commands:")
        print(f"  curl {base_url}/health")
        print(f"  curl {base_url}/info")
        print(f"  python quick_benchmark.py {base_url}/mcp")
        print("=" * 60)


# ============================================================================
# Endpoint Management Utilities
# ============================================================================

def get_endpoint_summary() -> dict:
    """Get summary of all available endpoints"""
    from .models import get_state
    state = get_state()
    
    return {
        "core_mcp": {
            "count": 6,
            "endpoints": ["/mcp", "/mcp/initialize", "/mcp/ping", "/mcp/tools", "/mcp/resources", "/mcp/sessions"]
        },
        "health_monitoring": {
            "count": 6,
            "endpoints": ["/health", "/health/detailed", "/readiness", "/liveness", "/metrics", "/metrics/prometheus"]
        },
        "information": {
            "count": 6,
            "endpoints": ["/", "/info", "/api", "/tools", "/resources", "/help"]
        },
        "capabilities": {
            "tools_count": len(state.get_tools()),
            "resources_count": len(state.get_resources()),
            "active_sessions": len(state.sessions)
        }
    }


def validate_endpoint_health() -> dict:
    """Validate that all endpoints are properly configured"""
    from .models import get_state
    state = get_state()
    
    checks = {
        "tools_loaded": len(state.get_tools()) > 0,
        "resources_loaded": len(state.get_resources()) > 0,
        "state_initialized": state.metrics.start_time > 0,
        "low_error_rate": state.metrics.errors < 100
    }
    
    return {
        "all_healthy": all(checks.values()),
        "checks": checks,
        "endpoint_categories": get_endpoint_summary()
    }