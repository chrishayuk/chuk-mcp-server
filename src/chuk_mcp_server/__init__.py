#!/usr/bin/env python3
"""
CleanMCP - A developer-friendly MCP framework powered by chuk_mcp

Simple, clean API similar to FastMCP but with chuk_mcp robustness:

    from cleanmcp import CleanMCP
    
    mcp = CleanMCP()
    
    @mcp.tool
    def hello(name: str) -> str:
        return f"Hello, {name}!"
    
    @mcp.resource("config://settings")
    def get_settings() -> dict:
        return {"app": "my_app", "version": "1.0"}
    
    if __name__ == "__main__":
        mcp.run(transport="http", port=8000)
"""

from .core import CleanMCP
from .decorators import tool, resource
from .types import Tool, Resource, ServerInfo, Capabilities

__version__ = "1.0.0"
__all__ = [
    "CleanMCP",
    "tool", 
    "resource",
    "Tool",
    "Resource", 
    "ServerInfo",
    "Capabilities"
]