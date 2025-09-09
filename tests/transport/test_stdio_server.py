#!/usr/bin/env python3
"""Test script for STDIO transport."""

from chuk_mcp_server import resource, run, tool


@tool
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"


@tool
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y


@resource("config://test")
def get_test_config() -> dict:
    """Get test configuration."""
    return {"mode": "stdio", "working": True}


if __name__ == "__main__":
    print("🔌 Starting MCP server over STDIO transport", flush=True)
    run(transport="stdio", debug=True)
