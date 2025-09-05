#!/usr/bin/env python3
# src/chuk_mcp_server/decorators.py
"""
Simple decorators for tools and resources
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from .types import PromptHandler, ResourceHandler, ToolHandler

# ============================================================================
# Global Registry (for standalone decorators)
# ============================================================================

_global_tools: list[ToolHandler] = []
_global_resources: list[ResourceHandler] = []
_global_prompts: list[PromptHandler] = []


def get_global_tools() -> list[ToolHandler]:
    """Get globally registered tools."""
    return _global_tools.copy()


def get_global_resources() -> list[ResourceHandler]:
    """Get globally registered resources."""
    return _global_resources.copy()


def get_global_prompts() -> list[PromptHandler]:
    """Get globally registered prompts."""
    return _global_prompts.copy()


def clear_global_registry() -> None:
    """Clear global registry (useful for testing)."""
    global _global_tools, _global_resources, _global_prompts
    _global_tools = []
    _global_resources = []
    _global_prompts = []


# ============================================================================
# Tool Decorator
# ============================================================================


def tool(name: str | None = None, description: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
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

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Create tool from function
        mcp_tool = ToolHandler.from_function(func, name=name, description=description)

        # Register globally
        _global_tools.append(mcp_tool)

        # Add tool metadata to function
        func._mcp_tool = mcp_tool  # type: ignore[attr-defined]

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
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


def resource(
    uri: str, name: str | None = None, description: str | None = None, mime_type: str = "text/plain"
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
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

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Create resource from function
        mcp_resource = ResourceHandler.from_function(
            uri=uri, func=func, name=name, description=description, mime_type=mime_type
        )

        # Register globally
        _global_resources.append(mcp_resource)

        # Add resource metadata to function
        func._mcp_resource = mcp_resource  # type: ignore[attr-defined]

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Prompt Decorator
# ============================================================================


def prompt(
    name: str | None = None, description: str | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to register a function as an MCP prompt.

    Usage:
        @prompt
        def code_review(code: str, language: str = "python") -> str:
            return f"Please review this {language} code:\\n\\n{code}"

        @prompt(name="custom_prompt", description="Custom prompt template")
        def my_prompt(topic: str, style: str = "formal") -> str:
            return f"Write about {topic} in a {style} style"
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Create prompt from function
        mcp_prompt = PromptHandler.from_function(func, name=name, description=description)

        # Register globally
        _global_prompts.append(mcp_prompt)

        # Add prompt metadata to function
        func._mcp_prompt = mcp_prompt  # type: ignore[attr-defined]

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    # Handle both @prompt and @prompt() usage
    if callable(name):
        # @prompt usage (no parentheses)
        func = name
        name = None
        return decorator(func)
    else:
        # @prompt() or @prompt(name="...") usage
        return decorator


# ============================================================================
# Helper Functions
# ============================================================================


def is_tool(func: Callable[..., Any]) -> bool:
    """Check if a function is decorated as a tool."""
    return hasattr(func, "_mcp_tool")


def is_resource(func: Callable[..., Any]) -> bool:
    """Check if a function is decorated as a resource."""
    return hasattr(func, "_mcp_resource")


def is_prompt(func: Callable[..., Any]) -> bool:
    """Check if a function is decorated as a prompt."""
    return hasattr(func, "_mcp_prompt")


def get_tool_from_function(func: Callable[..., Any]) -> ToolHandler | None:
    """Get the tool metadata from a decorated function."""
    return getattr(func, "_mcp_tool", None)


def get_resource_from_function(func: Callable[..., Any]) -> ResourceHandler | None:
    """Get the resource metadata from a decorated function."""
    return getattr(func, "_mcp_resource", None)


def get_prompt_from_function(func: Callable[..., Any]) -> PromptHandler | None:
    """Get the prompt metadata from a decorated function."""
    return getattr(func, "_mcp_prompt", None)
