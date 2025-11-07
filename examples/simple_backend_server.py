#!/usr/bin/env python3
"""
Simple Backend MCP Server for Proxy Testing

This is a minimal MCP server that will be proxied by ChukMCPServer.
It provides a few simple tools for demonstration.
"""

from chuk_mcp_server import ChukMCPServer

# Create a simple backend server
backend = ChukMCPServer(name="Simple Backend", version="1.0.0")


@backend.tool
def echo(message: str) -> str:
    """Echo back the message."""
    return f"Echo: {message}"


@backend.tool
def greet(name: str = "World") -> dict:
    """Greet someone by name."""
    return {
        "greeting": f"Hello, {name}!",
        "message": "This tool is running on the backend server",
    }


@backend.tool
def add(a: int, b: int) -> dict:
    """Add two numbers."""
    return {
        "operation": "addition",
        "a": a,
        "b": b,
        "result": a + b,
    }


@backend.tool
def uppercase(text: str) -> str:
    """Convert text to uppercase."""
    return text.upper()


if __name__ == "__main__":
    # Run in stdio mode so it can be proxied
    backend.run_stdio()
