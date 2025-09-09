#!/usr/bin/env python3
"""
ChukMCPServer STDIO Transport Example

This example demonstrates how to run an MCP server using the STDIO transport,
which is the standard MCP protocol for process-based communication.

Perfect for:
- MCP clients (Claude Desktop, etc.)
- Editor plugins and integrations
- Subprocess-based communication
- Zero network overhead scenarios
"""

import sys
from chuk_mcp_server import tool, resource, run

# ============================================================================
# Tools - Functions available via MCP
# ============================================================================

@tool
def greet(name: str = "World", style: str = "friendly") -> str:
    """
    Greet someone with different styles.
    
    Args:
        name: The name to greet
        style: Greeting style (friendly, formal, casual)
    """
    styles = {
        "friendly": f"Hey there, {name}! Great to meet you! 😊",
        "formal": f"Good day, {name}. It is a pleasure to make your acquaintance.",
        "casual": f"What's up, {name}?",
    }
    return styles.get(style, styles["friendly"])


@tool
def calculate(expression: str) -> dict:
    """
    Safely evaluate mathematical expressions.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")
    """
    try:
        # Simple whitelist of allowed operations for safety
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return {"error": "Expression contains invalid characters"}
        
        result = eval(expression)
        return {
            "expression": expression,
            "result": result,
            "type": type(result).__name__
        }
    except Exception as e:
        return {"error": f"Calculation error: {str(e)}"}


@tool
def system_info() -> dict:
    """Get basic system information."""
    import platform
    import os
    import sys
    
    return {
        "platform": {
            "system": platform.system(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
        },
        "python": {
            "version": sys.version,
            "executable": sys.executable,
        },
        "environment": {
            "cwd": os.getcwd(),
            "user": os.getenv("USER", "unknown"),
            "path_entries": len(os.getenv("PATH", "").split(":")),
        },
        "transport": "stdio"
    }


@tool
def create_data_structure(data_type: str, items: list = None) -> dict:
    """
    Create and manipulate different data structures.
    
    Args:
        data_type: Type of structure (list, set, dict, tuple)
        items: Items to include in the structure
    """
    if items is None:
        items = ["apple", "banana", "cherry", "date"]
    
    try:
        if data_type == "list":
            result = list(items)
        elif data_type == "set":
            result = list(set(items))  # Convert back to list for JSON serialization
        elif data_type == "dict":
            result = {f"item_{i}": item for i, item in enumerate(items)}
        elif data_type == "tuple":
            result = list(tuple(items))  # Convert to list for JSON serialization
        else:
            return {"error": f"Unsupported data type: {data_type}"}
        
        return {
            "data_type": data_type,
            "input_items": items,
            "result": result,
            "count": len(result) if isinstance(result, list) else len(result.keys())
        }
    except Exception as e:
        return {"error": f"Error creating {data_type}: {str(e)}"}


# ============================================================================
# Resources - Data/content available via MCP
# ============================================================================

@resource("config://server")
def get_server_config() -> dict:
    """Server configuration and capabilities."""
    return {
        "name": "ChukMCPServer STDIO Example",
        "version": "1.0.0",
        "transport": "stdio",
        "capabilities": {
            "tools": True,
            "resources": True,
            "prompts": False
        },
        "features": [
            "Zero configuration",
            "Type-safe tools",
            "Automatic schema generation",
            "Standard MCP protocol",
            "Process-based communication"
        ]
    }


@resource("docs://readme")
def get_readme() -> str:
    """Documentation for this STDIO MCP server."""
    return """# ChukMCPServer STDIO Example

This is an example MCP server running over STDIO transport.

## Available Tools

- `greet`: Greet someone with different styles
- `calculate`: Safely evaluate mathematical expressions  
- `system_info`: Get basic system information
- `create_data_structure`: Create and manipulate data structures

## Available Resources

- `config://server`: Server configuration and capabilities
- `docs://readme`: This documentation

## Usage

This server communicates via JSON-RPC over stdin/stdout.

### Example Requests

Initialize:
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"client","version":"1.0"},"protocolVersion":"2025-06-18"}}
```

List tools:
```json
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
```

Call a tool:
```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"greet","arguments":{"name":"Alice","style":"formal"}}}
```

## Transport Benefits

- Zero network overhead
- Direct process communication
- Standard MCP protocol
- Perfect for subprocess integration
"""


@resource("examples://usage")
def get_usage_examples() -> dict:
    """Usage examples for each tool."""
    return {
        "greet_examples": [
            {"name": "Alice", "style": "friendly"},
            {"name": "Bob", "style": "formal"},
            {"name": "Charlie", "style": "casual"}
        ],
        "calculate_examples": [
            "2 + 3",
            "10 * 5 - 3",
            "(4 + 6) / 2",
            "2 ** 8"
        ],
        "data_structure_examples": [
            {"data_type": "list", "items": ["red", "green", "blue"]},
            {"data_type": "set", "items": ["a", "b", "c", "a", "b"]},
            {"data_type": "dict", "items": ["key1", "key2", "key3"]},
            {"data_type": "tuple", "items": [1, 2, 3, 4, 5]}
        ]
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("🔌 ChukMCPServer STDIO Transport Example", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print("This server uses STDIO transport for MCP communication.", file=sys.stderr)
    print("All logs go to stderr, JSON-RPC responses to stdout.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Transport Options:", file=sys.stderr)
    print("  1. Global: run(transport='stdio')  # Current method", file=sys.stderr)
    print("  2. Constructor: ChukMCPServer(transport='stdio')", file=sys.stderr)
    print("  3. Method: mcp.run_stdio()", file=sys.stderr)
    print("", file=sys.stderr)
    print("Available tools:", file=sys.stderr)
    print("  - greet: Greet someone with different styles", file=sys.stderr)
    print("  - calculate: Safely evaluate math expressions", file=sys.stderr)
    print("  - system_info: Get system information", file=sys.stderr)
    print("  - create_data_structure: Create data structures", file=sys.stderr)
    print("", file=sys.stderr)
    print("Ready for JSON-RPC messages on stdin...", file=sys.stderr)
    print("", file=sys.stderr)
    
    # Method 1: Run the server with STDIO transport via global run()
    run(transport="stdio", debug=False)
