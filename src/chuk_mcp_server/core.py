#!/usr/bin/env python3
# src/chuk_mcp_server/core.py
"""
Core - Main ChukMCP Server class with integrated zero-config intelligence
"""

import os
import sys
import socket
import psutil
import logging
from typing import Callable, Optional, Dict, Any, List
from pathlib import Path

# Updated imports for clean types API
from .types import (
    # Framework handlers
    ToolHandler, ResourceHandler, 
    
    # Direct chuk_mcp types
    ServerInfo, create_server_capabilities,
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
# Smart Auto-Detection (Integrated)
# ============================================================================

class SmartDefaults:
    """Smart defaults with auto-detection built into core."""
    
    @staticmethod
    def detect_project_name() -> str:
        """Auto-detect project name from various sources."""
        # Try current directory name
        current_dir = Path.cwd().name
        if current_dir and current_dir not in ["src", "lib", "app"]:
            return f"{current_dir.replace('_', ' ').replace('-', ' ').title()} MCP Server"
        
        # Try package.json if it exists
        package_json = Path.cwd() / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    data = json.load(f)
                    return f"{data.get('name', 'MCP Server').title()} MCP Server"
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Try pyproject.toml
        pyproject = Path.cwd() / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject) as f:
                    for line in f:
                        if line.strip().startswith('name = '):
                            name = line.split('=')[1].strip().strip('"\'')
                            return f"{name.replace('_', ' ').replace('-', ' ').title()} MCP Server"
            except Exception:
                pass
        
        # Fallback
        return "Smart MCP Server"
    
    @staticmethod
    def detect_environment() -> str:
        """Detect runtime environment."""
        # Check environment variables
        env_var = os.environ.get('NODE_ENV', os.environ.get('ENV', '')).lower()
        if env_var in ['production', 'prod']:
            return "production"
        elif env_var in ['staging', 'stage']:
            return "staging"
        elif env_var in ['test', 'testing']:
            return "testing"
        
        # Check for CI/CD environments
        ci_indicators = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'GITLAB_CI']
        if any(os.environ.get(var) for var in ci_indicators):
            return "testing"
        
        # Check for serverless
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            return "serverless"
        
        # Default to development
        return "development"
    
    @staticmethod
    def detect_optimal_host() -> str:
        """Detect optimal host binding."""
        env = SmartDefaults.detect_environment()
        
        # In production/containers, bind to all interfaces
        if env == "production" or SmartDefaults.is_containerized():
            return "0.0.0.0"
        
        # Development: localhost for security
        return "localhost"
    
    @staticmethod
    def detect_optimal_port() -> int:
        """Detect optimal port."""
        # Check environment variable first
        env_port = os.environ.get('PORT')
        if env_port:
            try:
                return int(env_port)
            except ValueError:
                pass
        
        # Find available port starting from 8000
        for port in range(8000, 8100):
            if SmartDefaults.is_port_available(port):
                return port
        
        # Fallback
        return 8000
    
    @staticmethod
    def is_port_available(port: int) -> bool:
        """Check if port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    @staticmethod
    def is_containerized() -> bool:
        """Detect if running in a container."""
        indicators = [
            os.path.exists('/.dockerenv'),
            os.environ.get('KUBERNETES_SERVICE_HOST') is not None,
            os.environ.get('CONTAINER') is not None,
        ]
        return any(indicators)
    
    @staticmethod
    def get_optimal_workers() -> int:
        """Calculate optimal worker count."""
        cpu_cores = psutil.cpu_count(logical=True) or 1
        return min(cpu_cores, 8) if cpu_cores <= 16 else cpu_cores // 2


class SmartInference:
    """Smart type inference integrated into core."""
    
    @staticmethod
    def infer_tool_category(name: str, description: str) -> str:
        """Infer tool category from name and description."""
        name_lower = name.lower()
        desc_lower = description.lower()
        
        # Data processing
        if any(word in name_lower for word in ['process', 'transform', 'convert', 'parse']):
            return "data_processing"
        
        # File operations
        if any(word in name_lower for word in ['file', 'read', 'write', 'save', 'load']):
            return "file_operations"
        
        # API/Network
        if any(word in name_lower for word in ['api', 'http', 'request', 'fetch', 'download']):
            return "network"
        
        # Database
        if any(word in name_lower for word in ['db', 'database', 'sql', 'query', 'table']):
            return "database"
        
        # Math/Calculation
        if any(word in name_lower for word in ['calc', 'math', 'compute', 'sum', 'count']):
            return "mathematics"
        
        # System
        if any(word in name_lower for word in ['system', 'os', 'process', 'service']):
            return "system"
        
        return "general"
    
    @staticmethod
    def infer_mime_type(uri: str, func_name: str) -> str:
        """Infer MIME type from URI or function name."""
        uri_lower = uri.lower()
        func_name_lower = func_name.lower()
        
        # JSON indicators
        if any(indicator in uri_lower + func_name_lower 
               for indicator in ['json', 'api', 'data', 'config']):
            return "application/json"
        
        # Markdown indicators  
        if any(indicator in uri_lower + func_name_lower 
               for indicator in ['md', 'markdown', 'doc', 'readme']):
            return "text/markdown"
        
        # HTML indicators
        if any(indicator in uri_lower + func_name_lower 
               for indicator in ['html', 'page', 'template']):
            return "text/html"
        
        # Default to plain text
        return "text/plain"


# ============================================================================
# Main ChukMCPServer Class with Integrated Zero Config
# ============================================================================

class ChukMCPServer:
    """
    ChukMCPServer - Zero configuration MCP framework with intelligent defaults.
    
    Usage:
        # Zero config - everything auto-detected
        mcp = ChukMCPServer()
        
        @mcp.tool  # Auto-infers category, caching, security, etc.
        def hello(name: str) -> str:
            return f"Hello, {name}!"
        
        mcp.run()  # Auto-detects host, port, performance settings
    """
    
    def __init__(self, 
                 name: Optional[str] = None,
                 version: str = "1.0.0",
                 title: Optional[str] = None,
                 description: Optional[str] = None,
                 capabilities=None,
                 tools: bool = True,
                 resources: bool = True,
                 prompts: bool = False,
                 logging: bool = False,
                 experimental: Optional[Dict[str, Any]] = None,
                 # Smart defaults (all optional)
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 debug: Optional[bool] = None,
                 **kwargs):
        """
        Initialize ChukMCP Server with integrated zero-config intelligence.
        
        Args:
            name: Server name (auto-detected if None)
            version: Server version
            title: Optional server title
            description: Optional server description
            capabilities: ServerCapabilities object (auto-configured if None)
            tools: Enable tools capability
            resources: Enable resources capability  
            prompts: Enable prompts capability
            logging: Enable logging capability
            experimental: Experimental capabilities
            host: Host to bind to (auto-detected if None)
            port: Port to bind to (auto-detected if None)
            debug: Debug mode (auto-detected if None)
            **kwargs: Additional keyword arguments
        """
        # Auto-detect name if not provided
        if name is None:
            name = SmartDefaults.detect_project_name()
        
        # Use chuk_mcp ServerInfo directly
        self.server_info = ServerInfo(
            name=name,
            version=version,
            title=title
        )
        
        # Handle capabilities flexibly
        if capabilities is not None:
            self.capabilities = capabilities
        else:
            self.capabilities = create_server_capabilities(
                tools=tools,
                resources=resources,
                prompts=prompts,
                logging=logging,
                experimental=experimental
            )
        
        # Store smart defaults for run()
        self.smart_host = host or SmartDefaults.detect_optimal_host()
        self.smart_port = port or SmartDefaults.detect_optimal_port()
        self.smart_debug = debug if debug is not None else (SmartDefaults.detect_environment() == "development")
        
        # Create protocol handler with direct chuk_mcp types
        self.protocol = MCPProtocolHandler(self.server_info, self.capabilities)
        
        # Register any globally decorated functions
        self._register_global_functions()
        
        # HTTP server will be created when needed
        self._server = None
        
        # Print smart configuration info in debug mode
        if self.smart_debug:
            self._print_smart_config()
        
        logger.info(f"Initialized ChukMCP Server: {name} v{version}")
    
    def _print_smart_config(self):
        """Print smart configuration summary."""
        env = SmartDefaults.detect_environment()
        print("🧠 ChukMCPServer - Zero Configuration Mode")
        print("=" * 50)
        print(f"📊 Environment: {env}")
        print(f"🌐 Network: {self.smart_host}:{self.smart_port}")
        print(f"🔧 Workers: {SmartDefaults.get_optimal_workers()}")
        print(f"🐳 Container: {SmartDefaults.is_containerized()}")
        print("=" * 50)
    
    def _register_global_functions(self):
        """Register globally decorated functions in both protocol and registries."""
        # Register global tools
        for tool in get_global_tools():
            if hasattr(tool, 'handler'):
                tool_handler = tool
            else:
                tool_handler = ToolHandler.from_function(
                    tool.handler, 
                    name=tool.name, 
                    description=tool.description
                )
            
            self.protocol.register_tool(tool_handler)
            mcp_registry.register_tool(tool_handler.name, tool_handler)
        
        # Register global resources
        for resource in get_global_resources():
            if hasattr(resource, 'handler'):
                resource_handler = resource
            else:
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
    # Enhanced Tool Registration with Smart Inference
    # ============================================================================
    
    def tool(self, name: Optional[str] = None, description: Optional[str] = None, **kwargs):
        """
        Enhanced tool decorator with integrated smart inference.
        
        Usage:
            @mcp.tool  # Auto-infers everything
            def hello(name: str) -> str:
                return f"Hello, {name}!"
            
            @mcp.tool(tags=["custom"])  # Override smart defaults
            def advanced_tool(data: dict) -> dict:
                return {"processed": data}
        """
        def decorator(func: Callable) -> Callable:
            # Smart inference
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or f"Execute {tool_name}"
            
            # Create tool handler from function
            tool_handler = ToolHandler.from_function(func, name=tool_name, description=tool_description)
            
            # Register in protocol handler (for MCP functionality)
            self.protocol.register_tool(tool_handler)
            
            # Smart metadata for registry
            smart_metadata = {
                "category": SmartInference.infer_tool_category(tool_name, tool_description),
                "auto_inferred": True,
                "function_name": func.__name__,
                "parameter_count": len(tool_handler.parameters)
            }
            
            # Smart tags
            smart_tags = ["tool", smart_metadata["category"]]
            if "tags" in kwargs:
                smart_tags.extend(kwargs.pop("tags"))
            
            # Register in MCP registry with smart metadata
            mcp_registry.register_tool(
                tool_handler.name, 
                tool_handler, 
                metadata=smart_metadata,
                tags=smart_tags,
                **kwargs
            )
            
            # Add tool metadata to function
            func._mcp_tool = tool_handler
            
            logger.debug(f"Registered tool: {tool_handler.name} (category: {smart_metadata['category']})")
            return func
        
        # Handle both @mcp.tool and @mcp.tool() usage
        if callable(name):
            func = name
            name = None
            return decorator(func)
        else:
            return decorator
    
    def resource(self, uri: str, name: Optional[str] = None, description: Optional[str] = None, 
                mime_type: Optional[str] = None, **kwargs):
        """
        Enhanced resource decorator with integrated smart inference.
        
        Usage:
            @mcp.resource("config://settings")  # Auto-infers MIME type
            def get_settings() -> dict:
                return {"app": "my_app"}
        """
        def decorator(func: Callable) -> Callable:
            # Smart inference
            resource_name = name or func.__name__.replace('_', ' ').title()
            resource_description = description or func.__doc__ or f"Resource: {uri}"
            smart_mime_type = mime_type or SmartInference.infer_mime_type(uri, func.__name__)
            
            # Create resource handler from function
            resource_handler = ResourceHandler.from_function(
                uri=uri, 
                func=func, 
                name=resource_name, 
                description=resource_description,
                mime_type=smart_mime_type
            )
            
            # Register in protocol handler (for MCP functionality)
            self.protocol.register_resource(resource_handler)
            
            # Smart metadata for registry
            smart_metadata = {
                "auto_inferred": True,
                "function_name": func.__name__,
                "inferred_mime_type": smart_mime_type,
                "uri_scheme": uri.split("://")[0] if "://" in uri else "unknown"
            }
            
            # Smart tags
            smart_tags = ["resource", smart_metadata["uri_scheme"]]
            if "tags" in kwargs:
                smart_tags.extend(kwargs.pop("tags"))
            
            # Register in MCP registry with smart metadata
            mcp_registry.register_resource(
                resource_handler.uri, 
                resource_handler,
                metadata=smart_metadata,
                tags=smart_tags,
                **kwargs
            )
            
            # Add resource metadata to function
            func._mcp_resource = resource_handler
            
            logger.debug(f"Registered resource: {resource_handler.uri} (mime: {smart_mime_type})")
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
            "smart_config": {
                "host": self.smart_host,
                "port": self.smart_port,
                "debug": self.smart_debug,
                "environment": SmartDefaults.detect_environment(),
                "containerized": SmartDefaults.is_containerized(),
                "workers": SmartDefaults.get_optimal_workers()
            },
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
            }
        }
    
    # ============================================================================
    # Registry Management
    # ============================================================================
    
    def clear_tools(self):
        """Clear all registered tools."""
        self.protocol.tools.clear()
        mcp_registry.clear_type(mcp_registry.MCPComponentType.TOOL)
        logger.info("Cleared all tools")
    
    def clear_resources(self):
        """Clear all registered resources."""
        self.protocol.resources.clear()
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
    # Smart Server Management
    # ============================================================================
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None, debug: Optional[bool] = None):
        """
        Run the MCP server with smart defaults.
        
        Args:
            host: Host to bind to (uses smart default if None)
            port: Port to bind to (uses smart default if None)
            debug: Enable debug logging (uses smart default if None)
        """
        # Use smart defaults if not overridden
        final_host = host or self.smart_host
        final_port = port or self.smart_port
        final_debug = debug if debug is not None else self.smart_debug
        
        if final_debug:
            logging.basicConfig(level=logging.DEBUG)
        
        # Create HTTP server
        if self._server is None:
            self._server = create_server(self.protocol)
        
        # Show startup information
        self._print_startup_info(final_host, final_port, final_debug)
        
        # Run the server
        try:
            self._server.run(host=final_host, port=final_port, debug=final_debug)
        except KeyboardInterrupt:
            logger.info("\n👋 Server shutting down gracefully...")
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
            raise
    
    def _print_startup_info(self, host: str, port: int, debug: bool):
        """Print comprehensive startup information."""
        print("🚀 ChukMCPServer")
        print("=" * 50)
        
        # Server information
        info = self.info()
        print(f"Server: {info['server']['name']}")
        print(f"Version: {info['server']['version']}")
        print(f"Framework: ChukMCPServer with Zero Configuration")
        print()
        
        # Smart configuration
        smart_config = info['smart_config']
        print("🧠 Smart Configuration:")
        print(f"   Environment: {smart_config['environment']}")
        print(f"   Host: {smart_config['host']}:{smart_config['port']}")
        print(f"   Debug: {smart_config['debug']}")
        print(f"   Workers: {smart_config['workers']}")
        print(f"   Container: {smart_config['containerized']}")
        print()
        
        # MCP Components
        mcp_info = info['mcp_components']
        print(f"🔧 MCP Tools: {mcp_info['tools']['count']}")
        for tool_name in mcp_info['tools']['names']:
            print(f"   - {tool_name}")
        print()
        
        print(f"📂 MCP Resources: {mcp_info['resources']['count']}")
        for resource_uri in mcp_info['resources']['uris']:
            print(f"   - {resource_uri}")
        print()
        
        # Connection information
        print("🌐 Server Information:")
        print(f"   URL: http://{host}:{port}")
        print(f"   MCP Endpoint: http://{host}:{port}/mcp")
        print(f"   Debug: {debug}")
        print()
        
        # Inspector compatibility
        print("🔍 MCP Inspector:")
        print(f"   URL: http://{host}:{port}/mcp")
        print("   Transport: Streamable HTTP")
        print("=" * 50)
    
    # ============================================================================
    # Context Manager Support
    # ============================================================================
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass


# ============================================================================
# Factory Functions
# ============================================================================

def create_mcp_server(name: Optional[str] = None, **kwargs) -> ChukMCPServer:
    """Factory function to create a ChukMCP Server with zero config."""
    return ChukMCPServer(name=name, **kwargs)


def quick_server(name: Optional[str] = None) -> ChukMCPServer:
    """Create a server with minimal configuration for quick prototyping."""
    return ChukMCPServer(name=name or "Quick Server", version="0.1.0")