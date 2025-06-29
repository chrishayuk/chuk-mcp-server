#!/usr/bin/env python3
"""
Core - Main CleanMCP class with separate registry systems
"""

import logging
from typing import Callable, Optional, Dict, Any, List

from .types import Tool, Resource, ServerInfo, Capabilities
from .protocol import MCPProtocolHandler
from .http_server import create_server
from .endpoint_registry import http_endpoint_registry
from .mcp_registry import mcp_registry
from .decorators import (
    get_global_tools, get_global_resources, clear_global_registry,
    is_tool, is_resource, get_tool_from_function, get_resource_from_function
)

logger = logging.getLogger(__name__)


# ============================================================================
# Main CleanMCP Class - Updated with Separate Registries
# ============================================================================

class CleanMCP:
    """
    CleanMCP - A developer-friendly MCP framework with clean architecture.
    
    Usage:
        mcp = CleanMCP(name="My Server")
        
        @mcp.tool
        def hello(name: str) -> str:
            return f"Hello, {name}!"
        
        @mcp.endpoint("/api/data")
        async def data_handler(request):
            return Response('{"data": "example"}')
        
        mcp.run(port=8000)
    """
    
    def __init__(self, 
                 name: str = "CleanMCP Server",
                 version: str = "1.0.0",
                 title: Optional[str] = None,
                 description: Optional[str] = None,
                 capabilities: Optional[Capabilities] = None):
        """
        Initialize CleanMCP server.
        
        Args:
            name: Server name
            version: Server version
            title: Optional server title
            description: Optional server description
            capabilities: Server capabilities (defaults to tools + resources)
        """
        self.server_info = ServerInfo(
            name=name,
            version=version,
            title=title,
            description=description
        )
        
        self.capabilities = capabilities or Capabilities(
            tools=True,
            resources=True,
            prompts=False,
            logging=False
        )
        
        # Create protocol handler
        self.protocol = MCPProtocolHandler(self.server_info, self.capabilities)
        
        # Register any globally decorated functions
        self._register_global_functions()
        
        # HTTP server will be created when needed
        self._server = None
        
        logger.info(f"Initialized CleanMCP server: {name} v{version}")
    
    def _register_global_functions(self):
        """Register globally decorated functions in both protocol and registries."""
        # Register global tools
        for tool in get_global_tools():
            self.protocol.register_tool(tool)
            mcp_registry.register_tool(tool.name, tool)
        
        # Register global resources
        for resource in get_global_resources():
            self.protocol.register_resource(resource)
            mcp_registry.register_resource(resource.uri, resource)
        
        # Clear global registry to avoid duplicate registrations
        clear_global_registry()
    
    # ============================================================================
    # MCP Component Registration (Tools & Resources)
    # ============================================================================
    
    def tool(self, name: Optional[str] = None, description: Optional[str] = None, **kwargs):
        """
        Decorator to register a function as an MCP tool.
        
        Usage:
            @mcp.tool
            def hello(name: str) -> str:
                return f"Hello, {name}!"
            
            @mcp.tool(name="custom_name", description="Custom description", tags=["math"])
            def my_func(x: int, y: int = 10) -> int:
                return x + y
        """
        def decorator(func: Callable) -> Callable:
            # Create tool from function
            tool = Tool.from_function(func, name=name, description=description)
            
            # Register in protocol handler (for MCP functionality)
            self.protocol.register_tool(tool)
            
            # Register in MCP registry (for introspection and management)
            mcp_registry.register_tool(tool.name, tool, **kwargs)
            
            # Add tool metadata to function
            func._mcp_tool = tool
            
            logger.debug(f"Registered tool: {tool.name}")
            return func
        
        # Handle both @mcp.tool and @mcp.tool() usage
        if callable(name):
            # @mcp.tool usage (no parentheses)
            func = name
            name = None
            return decorator(func)
        else:
            # @mcp.tool() or @mcp.tool(name="...") usage
            return decorator
    
    def resource(self, uri: str, name: Optional[str] = None, description: Optional[str] = None, 
                mime_type: str = "text/plain", **kwargs):
        """
        Decorator to register a function as an MCP resource.
        
        Usage:
            @mcp.resource("config://settings")
            def get_settings() -> dict:
                return {"app": "my_app", "version": "1.0"}
            
            @mcp.resource("file://readme", mime_type="text/markdown", tags=["docs"])
            def get_readme() -> str:
                return "# My Application\\n\\nThis is awesome!"
        """
        def decorator(func: Callable) -> Callable:
            # Create resource from function
            resource = Resource.from_function(
                uri=uri, 
                func=func, 
                name=name, 
                description=description,
                mime_type=mime_type
            )
            
            # Register in protocol handler (for MCP functionality)
            self.protocol.register_resource(resource)
            
            # Register in MCP registry (for introspection and management)
            mcp_registry.register_resource(resource.uri, resource, **kwargs)
            
            # Add resource metadata to function
            func._mcp_resource = resource
            
            logger.debug(f"Registered resource: {resource.uri}")
            return func
        
        return decorator
    
    # ============================================================================
    # HTTP Endpoint Registration
    # ============================================================================
    
    def endpoint(self, path: str, methods: List[str] = None, **kwargs):
        """
        Decorator to register a custom HTTP endpoint.
        
        Usage:
            @mcp.endpoint("/api/data", methods=["GET", "POST"])
            async def data_handler(request):
                return Response('{"data": "example"}')
            
            @mcp.endpoint("/health", description="Custom health check")
            async def health_handler(request):
                return Response('{"status": "ok"}')
        """
        def decorator(handler: Callable):
            http_endpoint_registry.register_endpoint(path, handler, methods=methods, **kwargs)
            logger.debug(f"Registered endpoint: {path}")
            return handler
        return decorator
    
    # ============================================================================
    # Manual Registration Methods
    # ============================================================================
    
    def add_tool(self, tool: Tool, **kwargs):
        """Manually add an MCP tool."""
        self.protocol.register_tool(tool)
        mcp_registry.register_tool(tool.name, tool, **kwargs)
        logger.debug(f"Added tool: {tool.name}")
    
    def add_resource(self, resource: Resource, **kwargs):
        """Manually add an MCP resource."""
        self.protocol.register_resource(resource)
        mcp_registry.register_resource(resource.uri, resource, **kwargs)
        logger.debug(f"Added resource: {resource.uri}")
    
    def add_endpoint(self, path: str, handler: Callable, methods: List[str] = None, **kwargs):
        """Manually add a custom HTTP endpoint."""
        http_endpoint_registry.register_endpoint(path, handler, methods=methods, **kwargs)
        logger.debug(f"Added endpoint: {path}")
    
    def register_function_as_tool(self, func: Callable, name: Optional[str] = None, 
                                description: Optional[str] = None, **kwargs):
        """Register an existing function as an MCP tool."""
        tool = Tool.from_function(func, name=name, description=description)
        self.add_tool(tool, **kwargs)
        return tool
    
    def register_function_as_resource(self, func: Callable, uri: str, name: Optional[str] = None,
                                    description: Optional[str] = None, mime_type: str = "text/plain", **kwargs):
        """Register an existing function as an MCP resource."""
        resource = Resource.from_function(
            uri=uri, func=func, name=name, description=description, mime_type=mime_type
        )
        self.add_resource(resource, **kwargs)
        return resource
    
    # ============================================================================
    # Component Search and Discovery
    # ============================================================================
    
    def search_tools_by_tag(self, tag: str) -> List[Tool]:
        """Search tools by tag."""
        configs = mcp_registry.search_by_tag(tag)
        return [
            config.component for config in configs 
            if config.component_type.value == "tool"
        ]
    
    def search_resources_by_tag(self, tag: str) -> List[Resource]:
        """Search resources by tag."""
        configs = mcp_registry.search_by_tag(tag)
        return [
            config.component for config in configs 
            if config.component_type.value == "resource"
        ]
    
    def search_components_by_tags(self, tags: List[str], match_all: bool = False):
        """Search components by multiple tags."""
        return mcp_registry.search_by_tags(tags, match_all=match_all)
    
    # ============================================================================
    # Information and Introspection
    # ============================================================================
    
    def get_tools(self) -> List[Tool]:
        """Get all registered MCP tools."""
        return list(self.protocol.tools.values())
    
    def get_resources(self) -> List[Resource]:
        """Get all registered MCP resources."""
        return list(self.protocol.resources.values())
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """Get all registered custom HTTP endpoints."""
        return [
            {
                "path": config.path,
                "name": config.name,
                "methods": config.methods,
                "description": config.description,
                "registered_at": config.registered_at
            }
            for config in http_endpoint_registry.list_endpoints()
        ]
    
    def get_component_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an MCP component."""
        return mcp_registry.get_component_info(name)
    
    def info(self) -> Dict[str, Any]:
        """Get comprehensive server information."""
        return {
            "server": self.server_info.to_dict(),
            "capabilities": self.capabilities.to_dict(),
            "mcp_components": {
                "tools": {
                    "count": len(self.protocol.tools),
                    "names": list(self.protocol.tools.keys())
                },
                "resources": {
                    "count": len(self.protocol.resources),
                    "uris": list(self.protocol.resources.keys())
                },
                "stats": mcp_registry.get_stats()
            },
            "http_endpoints": {
                "count": len(http_endpoint_registry.list_endpoints()),
                "custom": self.get_endpoints(),
                "stats": http_endpoint_registry.get_stats()
            },
            "registries": {
                "mcp_registry": mcp_registry.get_info(),
                "endpoint_registry": http_endpoint_registry.get_info()
            }
        }
    
    # ============================================================================
    # Registry Management
    # ============================================================================
    
    def clear_tools(self):
        """Clear all registered tools."""
        # Clear from protocol
        self.protocol.tools.clear()
        # Clear from registry  
        mcp_registry.clear_type(mcp_registry.MCPComponentType.TOOL)
        logger.info("Cleared all tools")
    
    def clear_resources(self):
        """Clear all registered resources."""
        # Clear from protocol
        self.protocol.resources.clear()
        # Clear from registry
        mcp_registry.clear_type(mcp_registry.MCPComponentType.RESOURCE)
        logger.info("Cleared all resources")
    
    def clear_endpoints(self):
        """Clear all custom HTTP endpoints."""
        http_endpoint_registry.clear_endpoints()
        logger.info("Cleared all custom endpoints")
    
    def clear_all(self):
        """Clear all registered components and endpoints."""
        self.clear_tools()
        self.clear_resources()
        self.clear_endpoints()
        logger.info("Cleared all components and endpoints")
    
    # ============================================================================
    # Server Management
    # ============================================================================
    
    def run(self, host: str = "localhost", port: int = 8000, debug: bool = False):
        """
        Run the MCP server.
        
        Args:
            host: Host to bind to
            port: Port to bind to 
            debug: Enable debug logging
        """
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        
        # Create HTTP server
        if self._server is None:
            self._server = create_server(self.protocol)
        
        # Show startup information
        self._print_startup_info(host, port, debug)
        
        # Run the server
        try:
            self._server.run(host=host, port=port, debug=debug)
        except KeyboardInterrupt:
            logger.info("\n👋 Server shutting down gracefully...")
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
            raise
    
    def _print_startup_info(self, host: str, port: int, debug: bool):
        """Print comprehensive startup information."""
        print("🚀 CleanMCP Server")
        print("=" * 50)
        
        # Server information
        info = self.info()
        print(f"Server: {info['server']['name']}")
        print(f"Version: {info['server']['version']}")
        print(f"Framework: CleanMCP with chuk_mcp")
        print()
        
        # MCP Components
        mcp_info = info['mcp_components']
        print(f"🔧 MCP Tools: {mcp_info['tools']['count']}")
        if mcp_info['tools']['names']:
            for tool_name in mcp_info['tools']['names']:
                print(f"   - {tool_name}")
        print()
        
        print(f"📂 MCP Resources: {mcp_info['resources']['count']}")
        if mcp_info['resources']['uris']:
            for resource_uri in mcp_info['resources']['uris']:
                print(f"   - {resource_uri}")
        print()
        
        # HTTP Endpoints
        http_info = info['http_endpoints']
        if http_info['count'] > 0:
            print(f"🔗 Custom HTTP Endpoints: {http_info['count']}")
            for endpoint in http_info['custom']:
                print(f"   - {endpoint['path']} ({', '.join(endpoint['methods'])})")
            print()
        
        # Registry Statistics
        print("📊 Registry Statistics:")
        print(f"   MCP Components: {sum(mcp_info['stats']['by_type'].values())}")
        print(f"   HTTP Endpoints: {http_info['stats']['endpoints']['total']}")
        print(f"   Tags: {mcp_info['stats']['tags']['total_unique']}")
        print()
        
        # Connection information
        print("🌐 Server Information:")
        print(f"   Host: {host}:{port}")
        print(f"   Debug: {debug}")
        print()
        
        # Inspector compatibility
        print("🔍 MCP Inspector Instructions:")
        print("   1. This server: http://localhost:8000/mcp")
        print("   2. Use proxy: http://localhost:8011/mcp/inspector") 
        print("   3. Transport: Streamable HTTP")
        print("   4. All tools and resources available!")
        print()
        
        # Registry endpoints
        print("🔍 Registry Endpoints:")
        print(f"   MCP Registry: http://{host}:{port}/registry/mcp")
        print(f"   HTTP Registry: http://{host}:{port}/registry/endpoints")
        print("=" * 50)
    
    # ============================================================================
    # Context Manager Support
    # ============================================================================
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        # Cleanup registries if needed
        pass


# ============================================================================
# Factory Functions
# ============================================================================

def create_mcp_server(name: str, **kwargs) -> CleanMCP:
    """Factory function to create a CleanMCP server."""
    return CleanMCP(name=name, **kwargs)


def quick_server(name: str = "Quick Server") -> CleanMCP:
    """Create a server with minimal configuration for quick prototyping."""
    return CleanMCP(
        name=name,
        version="0.1.0",
        capabilities=Capabilities(tools=True, resources=True)
    )