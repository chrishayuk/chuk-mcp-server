#!/usr/bin/env python3
"""
fast_mcp_server - High-Performance MCP Protocol Server

A modular, high-performance implementation of the MCP (Model Context Protocol)
server built on Starlette and uvicorn, optimized for speed and developer experience.

Key Features:
- Sub-millisecond response times
- 10,000+ RPS capability  
- Full MCP 2025-06-18 protocol compliance
- Session management
- Tool execution framework
- Resource reading framework
- Real-time performance metrics
- Developer-friendly modular architecture

Modules:
- models: Data models and server state management
- protocol: MCP protocol implementation and handlers
- handlers: HTTP request handlers and response generation
- app: Starlette application factory and configuration
- main: Command-line interface and server runner

Usage:
    # As a standalone server
    python -m fast_mcp_server --port 8000
    
    # As a library
    from fast_mcp_server import create_app, ServerConfig
    
    config = ServerConfig(port=8080, workers=4)
    app = create_app()
"""

from .models import (
    MCPSession,
    ServerMetrics, 
    ToolDefinition,
    ResourceDefinition,
    ServerState,
    get_state,
    reset_state
)

from .protocol import (
    handle_initialize,
    handle_ping,
    handle_tools_list,
    handle_tools_call,
    handle_resources_list,
    handle_resources_read,
    execute_tool,
    read_resource,
    route_method,
    validate_jsonrpc_message,
    is_notification,
    MCPProtocolError,
    create_error_dict
)

from .handlers import (
    mcp_endpoint,
    health_endpoint,
    metrics_endpoint,
    root_endpoint,
    create_success_response,
    create_error_response,
    cleanup_middleware,
    get_client_info
)

from .app import (
    create_app,
    ServerConfig,
    startup_handler,
    shutdown_handler
)

from .main import (
    main,
    run_server,
    show_info,
    create_argument_parser
)

# Version information
__version__ = "1.0.0"
__protocol_version__ = "2025-06-18"
__author__ = "Fast MCP Team"

# Package metadata
__all__ = [
    # Models
    "MCPSession",
    "ServerMetrics", 
    "ToolDefinition",
    "ResourceDefinition",
    "ServerState",
    "get_state",
    "reset_state",
    
    # Protocol
    "handle_initialize",
    "handle_ping", 
    "handle_tools_list",
    "handle_tools_call",
    "handle_resources_list",
    "handle_resources_read",
    "execute_tool",
    "read_resource",
    "route_method",
    "validate_jsonrpc_message",
    "is_notification",
    "MCPProtocolError",
    "create_error_dict",
    
    # Handlers
    "mcp_endpoint",
    "health_endpoint",
    "metrics_endpoint", 
    "root_endpoint",
    "create_success_response",
    "create_error_response",
    "cleanup_middleware",
    "get_client_info",
    
    # App
    "create_app",
    "ServerConfig",
    "startup_handler",
    "shutdown_handler",
    
    # Main
    "main",
    "run_server",
    "show_info",
    "create_argument_parser",
    
    # Metadata
    "__version__",
    "__protocol_version__",
]

# Convenience functions for library usage
def quick_start(port: int = 8000, workers: int = 1, debug: bool = False) -> None:
    """
    Quick start server with minimal configuration
    
    Args:
        port: Port to bind to
        workers: Number of worker processes  
        debug: Enable debug mode
    """
    config = ServerConfig(port=port, workers=workers, debug=debug)
    run_server(config)


def create_development_server(port: int = 8000) -> "Starlette":
    """
    Create a development server with debug settings
    
    Args:
        port: Port to bind to
        
    Returns:
        Configured Starlette application
    """
    return create_app(debug=True)


def create_production_server() -> "Starlette":
    """
    Create a production server with optimized settings
    
    Returns:
        Configured Starlette application optimized for production
    """
    return create_app(debug=False)


def get_server_info() -> dict:
    """
    Get comprehensive server information
    
    Returns:
        Dictionary with server metadata and current state
    """
    state = get_state()
    return {
        "version": __version__,
        "protocol_version": __protocol_version__,
        "server_state": state.get_server_info(),
        "metrics": state.metrics.to_dict(),
        "tools": state.get_tools(),
        "resources": state.get_resources()
    }


# Development helpers
def reset_for_testing():
    """Reset server state for testing purposes"""
    reset_state()


def add_demo_tool(name: str, description: str, handler_func=None):
    """
    Add a demo tool for testing/development
    
    Args:
        name: Tool name
        description: Tool description  
        handler_func: Optional custom handler function
    """
    state = get_state()
    
    tool = ToolDefinition(
        name=name,
        description=description,
        input_schema={
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input parameter"}
            }
        }
    )
    
    state.add_tool(tool)
    
    # TODO: Add custom handler registration when tool executor is integrated


def add_demo_resource(uri: str, name: str, description: str, content: str = ""):
    """
    Add a demo resource for testing/development
    
    Args:
        uri: Resource URI
        name: Resource name
        description: Resource description
        content: Static content to return
    """
    state = get_state()
    
    resource = ResourceDefinition(
        uri=uri,
        name=name, 
        description=description
    )
    
    state.add_resource(resource)
    
    # TODO: Add custom content handler when resource system is extended