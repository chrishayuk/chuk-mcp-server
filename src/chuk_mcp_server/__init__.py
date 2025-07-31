#!/usr/bin/env python3
# src/chuk_mcp_server/__init__.py
"""
Chuk MCP Server - A developer-friendly MCP framework powered by chuk_mcp

Simple, clean API similar to FastMCP but with chuk_mcp robustness:

    from chuk_mcp_server import ChukMCPServer
    
    mcp = ChukMCPServer()
    
    @mcp.tool
    def hello(name: str) -> str:
        return f"Hello, {name}!"
    
    @mcp.resource("config://settings")
    def get_settings() -> dict:
        return {"app": "my_app", "version": "1.0"}
    
    if __name__ == "__main__":
        mcp.run(port=8000)
"""

from .core import ChukMCPServer
from .decorators import tool, resource
from .types import (
    ToolHandler as Tool,  # Backward compatibility alias
    ResourceHandler as Resource,  # Backward compatibility alias
    ServerInfo, 
    create_server_capabilities,
    ToolParameter,
)

# Create backward compatibility for Capabilities
def Capabilities(**kwargs):
    """Legacy Capabilities function for backward compatibility."""
    return create_server_capabilities(**kwargs)

__version__ = "1.0.0"
__all__ = [
    "ChukMCPServer",
    "tool", 
    "resource",
    "Tool",        # -> ToolHandler (backward compatibility)
    "Resource",    # -> ResourceHandler (backward compatibility) 
    "ServerInfo",
    "Capabilities", # Legacy function
    "ToolParameter",
]