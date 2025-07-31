#!/usr/bin/env python3
# src/chuk_mcp_server/__init__.py
"""
ChukMCPServer - Zero Configuration MCP Framework

The world's smartest MCP framework with zero configuration built right in.

ZERO CONFIG USAGE:
    from chuk_mcp_server import ChukMCPServer, tool, resource, run
    
    # Option 1: Global decorators (ultimate simplicity)
    @tool
    def hello(name: str) -> str:
        return f"Hello, {name}!"
    
    @resource("config://settings")
    def get_settings() -> dict:
        return {"app": "my_app", "version": "1.0"}
    
    if __name__ == "__main__":
        run()  # Auto-detects everything!

    # Option 2: Server instance (traditional but smart)
    mcp = ChukMCPServer()  # Auto-detects name, host, port, etc.
    
    @mcp.tool  # Auto-infers category, metadata, etc.
    def process_data(data: str) -> dict:
        return {"processed": data}
    
    mcp.run()  # Uses smart defaults

ADVANCED USAGE (Full Control):
    from chuk_mcp_server import ChukMCPServer
    
    mcp = ChukMCPServer(
        name="My Server", 
        version="1.0.0",
        host="0.0.0.0",
        port=8000,
        debug=False
    )
    
    @mcp.tool(tags=["custom"])
    def hello(name: str) -> str:
        return f"Hello, {name}!"
    
    mcp.run()
"""

# Import the core server with integrated zero-config
from typing import Optional
from .core import ChukMCPServer, create_mcp_server, quick_server

# Import traditional decorators for global usage
from .decorators import tool, resource

# Import types for advanced usage
from .types import (
    ToolHandler as Tool,
    ResourceHandler as Resource,
    ToolParameter,
    ServerInfo,
    create_server_capabilities,
)

# Create backward compatibility for Capabilities
def Capabilities(**kwargs):
    """Legacy capabilities function for backward compatibility."""
    return create_server_capabilities(**kwargs)

__version__ = "2.0.0"  # Zero-config integrated version

# ============================================================================
# Global Magic Decorators (Fixed Implementation)
# ============================================================================

# Global server instance for magic decorators
_global_server: Optional[ChukMCPServer] = None

def get_or_create_global_server() -> ChukMCPServer:
    """Get or create the global server instance."""
    global _global_server
    if _global_server is None:
        _global_server = ChukMCPServer()  # Uses all smart defaults
    return _global_server

def run(**kwargs):
    """Run the global smart server."""
    server = get_or_create_global_server()
    server.run(**kwargs)

# ============================================================================
# Exports - Clean API
# ============================================================================

__all__ = [
    # 🧠 PRIMARY INTERFACE (Zero Config)
    "ChukMCPServer",      # Smart server with zero config built-in
    
    # 🪄 MAGIC DECORATORS (Global convenience)
    "tool",               # Global tool decorator
    "resource",           # Global resource decorator  
    "run",                # Global run function
    
    # 🏭 FACTORY FUNCTIONS
    "create_mcp_server",  # Factory function
    "quick_server",       # Quick prototyping server
    
    # 📚 TYPES & UTILITIES (Advanced)
    "Tool",               # ToolHandler alias
    "Resource",           # ResourceHandler alias
    "ToolParameter",      # Parameter type system
    "ServerInfo",         # Server information type
    "Capabilities",       # Legacy capabilities function
]

# ============================================================================
# Smart Examples Documentation
# ============================================================================

def show_examples():
    """Show zero configuration examples."""
    examples = """
🧠 ChukMCPServer - Zero Configuration Examples

1️⃣ ULTIMATE ZERO CONFIG (Magic Decorators):
   
   from chuk_mcp_server import tool, resource, run
   
   @tool
   def hello(name: str) -> str:
       '''Auto-inferred: category=general, tags=["tool", "general"]'''
       return f"Hello, {name}!"
   
   @resource("config://app")  
   def get_config() -> dict:
       '''Auto-inferred: mime_type=application/json, tags=["resource", "config"]'''
       return {"app": "zero-config", "magic": True}
   
   if __name__ == "__main__":
       run()  # 🧠 Everything auto-detected!

2️⃣ SMART SERVER (Traditional but Intelligent):

   from chuk_mcp_server import ChukMCPServer
   
   mcp = ChukMCPServer()  # 🧠 Name, host, port all auto-detected
   
   @mcp.tool  # 🧠 Category, metadata all auto-inferred
   def calculate(expression: str) -> float:
       '''Mathematics category auto-detected'''
       return eval(expression)
   
   mcp.run()  # 🧠 Smart defaults: localhost:8000 in dev, 0.0.0.0:PORT in prod

3️⃣ SMART INFERENCE EXAMPLES:

   @tool
   def process_file(path: str) -> dict:
       '''🧠 Auto-detected: category="file_operations", tags=["tool", "file_operations"]'''
       
   @tool  
   def fetch_api(url: str) -> dict:
       '''🧠 Auto-detected: category="network", tags=["tool", "network"]'''
       
   @tool
   def math_calc(x: int, y: int) -> int:
       '''🧠 Auto-detected: category="mathematics", tags=["tool", "mathematics"]'''

4️⃣ ENVIRONMENT AUTO-DETECTION:

   🏠 Development: localhost:8000, debug=True, smart logging
   🏭 Production: 0.0.0.0:PORT, debug=False, JSON logging  
   ☁️  AWS Lambda: serverless optimizations
   🐳 Docker: container optimizations
   
Ready to try zero config? All examples work out of the box! 🚀
"""
    print(examples)

# Show examples in interactive environments
import sys
if hasattr(sys, 'ps1'):  # Interactive Python
    print("🧠 ChukMCPServer v2.0.0 - Zero Configuration Built-In")
    print("Type show_examples() to see usage examples!")