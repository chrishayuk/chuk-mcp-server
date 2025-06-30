#!/usr/bin/env python3
"""
Core - Main ChukMCP Server class with direct chuk_mcp integration
"""

import logging
from typing import Callable, Optional, Dict, Any, List

# Updated imports for direct chuk_mcp integration
from .types import (
    # Framework handlers
    ToolHandler, ResourceHandler, 
    
    # Direct chuk_mcp types
    ServerInfo, create_server_capabilities,
    
    # Legacy compatibility
    Capabilities
)
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
# Main ChukMCPServer Class - Updated with Direct chuk_mcp Integration
# ============================================================================

class ChukMCPServer:
    """
    ChukMCPServer - A developer-friendly MCP framework with clean architecture.
    
    Usage:
        mcp = ChukMCPServer(name="My Server")
        
        @mcp.tool
        def hello(name: str) -> str:
            return f"Hello, {name}!"
        
        @mcp.resource("config://settings")
        def get_settings() -> dict:
            return {"app": "my_app"}
        
        mcp.run(port=8000)
    """
    
    def __init__(self, 
                 name: str = "ChukMCP Server",
                 version: str = "1.0.0",
                 title: Optional[str] = None,
                 description: Optional[str] = None,
                 capabilities=None,
                 tools: bool = True,
                 resources: bool = True,
                 prompts: bool = False,
                 logging: bool = False,
                 experimental: Optional[Dict[str, Any]] = None,
                 **kwargs):
        """
        Initialize ChukMCP Server with direct chuk_mcp integration.
        
        Args:
            name: Server name
            version: Server version
            title: Optional server title
            description: Optional server description
            capabilities: Legacy Capabilities object (for backward compatibility)
            tools: Enable tools capability
            resources: Enable resources capability  
            prompts: Enable prompts capability
            logging: Enable logging capability
            experimental: Experimental capabilities
            **kwargs: Additional keyword arguments (ignored)
        """
        # Use chuk_mcp ServerInfo directly
        self.server_info = ServerInfo(
            name=name,
            version=version,
            title=title
        )
        
        # Handle capabilities flexibly
        if capabilities is not None:
            # Legacy Capabilities object or ServerCapabilities passed
            if hasattr(capabilities, 'model_dump'):
                # Already a ServerCapabilities object from chuk_mcp
                self.capabilities = capabilities
            else:
                # Legacy Capabilities function result - use it directly
                self.capabilities = capabilities
        else:
            # Create from individual flags
            self.capabilities = create_server_capabilities(
                tools=tools,
                resources=resources,
                prompts=prompts,
                logging=logging,
                experimental=experimental
            )
        
        # Create protocol handler with direct chuk_mcp types
        self.protocol = MCPProtocolHandler(self.server_info, self.capabilities)
        
        # Register any globally decorated functions
        self._register_global_functions()
        
        # HTTP server will be created when needed
        self._server = None
        
        logger.info(f"Initialized ChukMCP Server: {name} v{version}")
    
    def _register_global_functions(self):
        """Register globally decorated functions in both protocol and registries."""
        # Register global tools (now as ToolHandlers)
        for tool in get_global_tools():
            # Convert old Tool to new ToolHandler if needed
            if hasattr(tool, 'handler'):
                tool_handler = tool  # Already a handler
            else:
                # Convert old-style tool to handler
                tool_handler = ToolHandler.from_function(
                    tool.handler, 
                    name=tool.name, 
                    description=tool.description
                )
            
            self.protocol.register_tool(tool_handler)
            mcp_registry.register_tool(tool_handler.name, tool_handler)
        
        # Register global resources (now as ResourceHandlers)
        for resource in get_global_resources():
            # Convert old Resource to new ResourceHandler if needed
            if hasattr(resource, 'handler'):
                resource_handler = resource  # Already a handler
            else:
                # Convert old-style resource to handler
                resource_handler = ResourceHandler.from_function(
                    resource.uri,
                    resource.handler,
                    name=resource.name,
                    description=resource.description,
                    mime_type=resource.mime_type
                )
            
            self.protocol.register_resource(resource_handler)
            mcp_registry.register_resource(resource_handler.uri, resource_handler)
        
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
            # Create tool handler from function
            tool_handler = ToolHandler.from_function(func, name=name, description=description)
            
            # Register in protocol handler (for MCP functionality)
            self.protocol.register_tool(tool_handler)
            
            # Register in MCP registry (for introspection and management)
            mcp_registry.register_tool(tool_handler.name, tool_handler, **kwargs)
            
            # Add tool metadata to function
            func._mcp_tool = tool_handler
            
            logger.debug(f"Registered tool: {tool_handler.name}")
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
            # Create resource handler from function
            resource_handler = ResourceHandler.from_function(
                uri=uri, 
                func=func, 
                name=name, 
                description=description,
                mime_type=mime_type
            )
            
            # Register in protocol handler (for MCP functionality)
            self.protocol.register_resource(resource_handler)
            
            # Register in MCP registry (for introspection and management)
            mcp_registry.register_resource(resource_handler.uri, resource_handler, **kwargs)
            
            # Add resource metadata to function
            func._mcp_resource = resource_handler
            
            logger.debug(f"Registered resource: {resource_handler.uri}")
            return func
        
        return decorator
    
    # ============================================================================
    # HTTP Endpoint Registration (unchanged)
    # ============================================================================
    
    def endpoint(self, path: str, methods: List[str] = None, **kwargs):
        """
        Decorator to register a custom HTTP endpoint.
        
        Usage:
            @mcp.endpoint("/api/data", methods=["GET", "POST"])
            async def data_handler(request):
                return Response('{"data": "example"}')
        """
        def decorator(handler: Callable):
            http_endpoint_registry.register_endpoint(path, handler, methods=methods, **kwargs)
            logger.debug(f"Registered endpoint: {path}")
            return handler
        return decorator
    
    # ============================================================================
    # Manual Registration Methods
    # ============================================================================
    
    def add_tool(self, tool_handler: ToolHandler, **kwargs):
        """Manually add an MCP tool handler."""
        self.protocol.register_tool(tool_handler)
        mcp_registry.register_tool(tool_handler.name, tool_handler, **kwargs)
        logger.debug(f"Added tool: {tool_handler.name}")
    
    def add_resource(self, resource_handler: ResourceHandler, **kwargs):
        """Manually add an MCP resource handler."""
        self.protocol.register_resource(resource_handler)
        mcp_registry.register_resource(resource_handler.uri, resource_handler, **kwargs)
        logger.debug(f"Added resource: {resource_handler.uri}")
    
    def add_endpoint(self, path: str, handler: Callable, methods: List[str] = None, **kwargs):
        """Manually add a custom HTTP endpoint."""
        http_endpoint_registry.register_endpoint(path, handler, methods=methods, **kwargs)
        logger.debug(f"Added endpoint: {path}")
    
    def register_function_as_tool(self, func: Callable, name: Optional[str] = None, 
                                description: Optional[str] = None, **kwargs):
        """Register an existing function as an MCP tool."""
        tool_handler = ToolHandler.from_function(func, name=name, description=description)
        self.add_tool(tool_handler, **kwargs)
        return tool_handler
    
    def register_function_as_resource(self, func: Callable, uri: str, name: Optional[str] = None,
                                    description: Optional[str] = None, mime_type: str = "text/plain", **kwargs):
        """Register an existing function as an MCP resource."""
        resource_handler = ResourceHandler.from_function(
            uri=uri, func=func, name=name, description=description, mime_type=mime_type
        )
        self.add_resource(resource_handler, **kwargs)
        return resource_handler
    
    # ============================================================================
    # Component Search and Discovery
    # ============================================================================
    
    def search_tools_by_tag(self, tag: str) -> List[ToolHandler]:
        """Search tools by tag."""
        configs = mcp_registry.search_by_tag(tag)
        return [
            config.component for config in configs 
            if config.component_type.value == "tool"
        ]
    
    def search_resources_by_tag(self, tag: str) -> List[ResourceHandler]:
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
    
    def get_tools(self) -> List[ToolHandler]:
        """Get all registered MCP tool handlers."""
        return list(self.protocol.tools.values())
    
    def get_resources(self) -> List[ResourceHandler]:
        """Get all registered MCP resource handlers."""
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
            "server": self.server_info.model_dump(exclude_none=True),
            "capabilities": self.capabilities.model_dump(exclude_none=True),
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
    # Server Management (unchanged)
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
        print("🚀 ChukMCP Server")
        print("=" * 50)
        
        # Server information
        info = self.info()
        print(f"Server: {info['server']['name']}")
        print(f"Version: {info['server']['version']}")
        print(f"Framework: ChukMCPServer with direct chuk_mcp integration")
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
    # Context Manager Support (unchanged)
    # ============================================================================
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        # Cleanup registries if needed
        pass


# ============================================================================
# Factory Functions (updated for new types)
# ============================================================================

def create_mcp_server(name: str, **kwargs) -> ChukMCPServer:
    """Factory function to create a ChukMCP Server."""
    return ChukMCPServer(name=name, **kwargs)


def quick_server(name: str = "Quick Server") -> ChukMCPServer:
    """Create a server with minimal configuration for quick prototyping."""
    return ChukMCPServer(
        name=name,
        version="0.1.0",
        tools=True,
        resources=True
    )