#!/usr/bin/env python3
# src/chuk_mcp_server/decorators.py
"""
Simple decorators for tools and resources
"""

from collections.abc import Callable
from functools import wraps

from .types import ResourceHandler, ToolHandler

# ============================================================================
# Global Registry (for standalone decorators)
# ============================================================================

_global_tools = []
_global_resources = []


def get_global_tools():
    """Get globally registered tools."""
    return _global_tools.copy()


def get_global_resources():
    """Get globally registered resources."""
    return _global_resources.copy()


def clear_global_registry():
    """Clear global registry (useful for testing)."""
    global _global_tools, _global_resources
    _global_tools = []
    _global_resources = []


# ============================================================================
# Tool Decorator
# ============================================================================


def tool(name: str | None = None, description: str | None = None):
    """
    Decorator to register a function as an MCP tool.

    Usage:
        @tool
        def hello(name: str) -> str:
            return f"Hello, {name}!"

        @tool(name="custom_name", description="Custom description")
        def my_func(x: int, y: int = 10) -> int:
            return x + y
    """

    def decorator(func: Callable) -> Callable:
        # Create tool from function
        mcp_tool = ToolHandler.from_function(func, name=name, description=description)

        # Register globally
        _global_tools.append(mcp_tool)

        # Add tool metadata to function
        func._mcp_tool = mcp_tool

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    # Handle both @tool and @tool() usage
    if callable(name):
        # @tool usage (no parentheses)
        func = name
        name = None
        return decorator(func)
    else:
        # @tool() or @tool(name="...") usage
        return decorator


# ============================================================================
# Resource Decorator
# ============================================================================


def resource(uri: str, name: str | None = None, description: str | None = None, mime_type: str = "text/plain"):
    """
    Decorator to register a function as an MCP resource.

    Usage:
        @resource("config://settings")
        def get_settings() -> dict:
            return {"app": "my_app", "version": "1.0"}

        @resource("file://readme", mime_type="text/markdown")
        def get_readme() -> str:
            return "# My Application\\n\\nThis is awesome!"
    """

    def decorator(func: Callable) -> Callable:
        # Create resource from function
        mcp_resource = ResourceHandler.from_function(
            uri=uri, func=func, name=name, description=description, mime_type=mime_type
        )

        # Register globally
        _global_resources.append(mcp_resource)

        # Add resource metadata to function
        func._mcp_resource = mcp_resource

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Helper Functions
# ============================================================================


def is_tool(func: Callable) -> bool:
    """Check if a function is decorated as a tool."""
    return hasattr(func, "_mcp_tool")


def is_resource(func: Callable) -> bool:
    """Check if a function is decorated as a resource."""
    return hasattr(func, "_mcp_resource")


def get_tool_from_function(func: Callable) -> ToolHandler | None:
    """Get the tool metadata from a decorated function."""
    return getattr(func, "_mcp_tool", None)


def get_resource_from_function(func: Callable) -> ResourceHandler | None:
    """Get the resource metadata from a decorated function."""
    return getattr(func, "_mcp_resource", None)
