#!/usr/bin/env python3
"""
ChukMCPServer Constructor Transport Example

This example demonstrates how to set the transport mode directly in the 
ChukMCPServer constructor, providing a clean API for transport selection.

Three ways to specify transport:
1. Constructor parameter: ChukMCPServer(transport="stdio") 
2. run() parameter: run(transport="stdio")
3. run_stdio() method: mcp.run_stdio()
"""

import sys
from chuk_mcp_server import ChukMCPServer

def create_stdio_server():
    """Create a server configured for STDIO transport via constructor."""
    
    # Transport specified in constructor - cleanest approach
    mcp = ChukMCPServer(
        name="Constructor Transport Demo",
        version="1.0.0", 
        transport="stdio",  # This sets the default transport
        debug=False
    )
    
    @mcp.tool
    def greet(name: str = "World", enthusiastic: bool = True) -> str:
        """Greet someone with optional enthusiasm."""
        greeting = f"Hello, {name}!"
        if enthusiastic:
            greeting += " 🎉"
        return greeting
    
    @mcp.tool
    def calculate(a: float, b: float, operation: str = "add") -> dict:
        """Perform arithmetic operations."""
        operations = {
            "add": a + b,
            "subtract": a - b, 
            "multiply": a * b,
            "divide": a / b if b != 0 else None
        }
        
        if operation not in operations:
            return {"error": f"Unknown operation: {operation}"}
        
        result = operations[operation]
        if result is None:
            return {"error": "Division by zero"}
        
        return {
            "operation": operation,
            "operands": [a, b],
            "result": result
        }
    
    @mcp.resource("info://server")
    def get_server_info() -> dict:
        """Get information about this server instance."""
        return {
            "name": "Constructor Transport Demo",
            "transport": "stdio",
            "configured_via": "constructor_parameter", 
            "features": [
                "Constructor-based transport selection",
                "Clean API design",
                "Automatic transport detection",
                "Zero additional configuration"
            ]
        }
    
    return mcp

def create_http_server():
    """Create a server configured for HTTP transport via constructor."""
    
    mcp = ChukMCPServer(
        name="HTTP Constructor Demo",
        transport="http",  # Explicit HTTP transport
        debug=False
    )
    
    @mcp.tool
    def ping() -> str:
        """Simple ping tool for HTTP testing."""
        return "pong"
    
    return mcp

def demonstrate_all_transport_methods():
    """Demonstrate different ways to specify transport."""
    
    print("🚀 ChukMCPServer Transport Configuration Methods", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Method 1: Constructor parameter (recommended)
    print("1. Constructor Parameter (Recommended):", file=sys.stderr)
    print("   mcp = ChukMCPServer(transport='stdio')", file=sys.stderr)
    print("   mcp.run()  # Uses STDIO automatically", file=sys.stderr)
    print("", file=sys.stderr)
    
    # Method 2: Global decorators with run() parameter  
    print("2. Global Decorators:", file=sys.stderr)
    print("   from chuk_mcp_server import tool, run", file=sys.stderr)
    print("   run(transport='stdio')", file=sys.stderr)
    print("", file=sys.stderr)
    
    # Method 3: Dedicated method
    print("3. Dedicated Method:", file=sys.stderr)
    print("   mcp = ChukMCPServer()", file=sys.stderr) 
    print("   mcp.run_stdio()", file=sys.stderr)
    print("", file=sys.stderr)
    
    print("✅ This example uses Method 1 (Constructor Parameter)", file=sys.stderr)
    print("", file=sys.stderr)

if __name__ == "__main__":
    demonstrate_all_transport_methods()
    
    # Create and run STDIO server using constructor transport parameter
    mcp = create_stdio_server()
    
    print("🔌 Starting server with constructor-configured STDIO transport...", file=sys.stderr)
    mcp.run()  # No need to specify transport - it's already configured!