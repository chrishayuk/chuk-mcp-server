#!/usr/bin/env python3
"""
ChukMCPServer - Production Ready Example

This is the final optimized version that works perfectly with Inspector
and demonstrates all the modular components working together.
"""

import logging
import random
import time
from datetime import datetime
from typing import Any

# Import our modular ChukMCPServer framework
from chuk_mcp_server import Capabilities, ChukMCPServer

# Configure logging for production
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Create ChukMCP Server with full configuration
mcp = ChukMCPServer(
    name="ChukMCPServer Example",
    version="1.0.0",
    title="ChukMCPServer Production Server",
    description="A fully featured MCP server demonstrating ChukMCPServer framework",
    capabilities=Capabilities(
        tools=True,
        resources=True,
        prompts=False,  # Can be enabled later
        logging=False,  # Can be enabled later
    ),
)

# ============================================================================
# Advanced Tools with Type Safety
# ============================================================================


@mcp.tool
def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}! Welcome to ChukMCPServer!"


@mcp.tool(description="Add two numbers together")
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y


@mcp.tool
def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.
    Supports basic operations and math functions like sin, cos, sqrt, etc.

    Args:
        expression: Mathematical expression to evaluate (e.g., 'sqrt(16) + 2 * 3')
    """
    import math

    # Safe evaluation context
    safe_dict = {
        "__builtins__": {},
        # Basic operations
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        # Math constants
        "pi": math.pi,
        "e": math.e,
        # Math functions
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "floor": math.floor,
        "ceil": math.ceil,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "degrees": math.degrees,
        "radians": math.radians,
    }

    try:
        result = eval(expression, safe_dict, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {str(e)}"


@mcp.tool
def generate_random(type: str = "number", min_val: int = 1, max_val: int = 100, length: int = 10) -> str:
    """
    Generate random data of various types.

    Args:
        type: Type of random data ("number", "string", "uuid", "password")
        min_val: Minimum value for numbers
        max_val: Maximum value for numbers
        length: Length for strings/passwords
    """
    if type == "number":
        result = random.randint(min_val, max_val)
        return f"Random number between {min_val} and {max_val}: {result}"
    elif type == "string":
        import string

        chars = string.ascii_letters + string.digits
        result = "".join(random.choice(chars) for _ in range(length))
        return f"Random string ({length} chars): {result}"
    elif type == "uuid":
        import uuid

        result = str(uuid.uuid4())
        return f"Random UUID: {result}"
    elif type == "password":
        import string

        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        result = "".join(random.choice(chars) for _ in range(length))
        return f"Random password ({length} chars): {result}"
    else:
        return f"Unknown type '{type}'. Supported: number, string, uuid, password"


@mcp.tool
def get_time(format: str = "iso") -> str:
    """
    Get current time in various formats.

    Args:
        format: Time format ("iso", "timestamp", "human", "utc")
    """
    now = time.time()

    if format == "iso":
        return datetime.fromtimestamp(now).isoformat()
    elif format == "timestamp":
        return str(int(now))
    elif format == "human":
        return datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
    elif format == "utc":
        return datetime.utcfromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        return f"Unknown format '{format}'. Supported: iso, timestamp, human, utc"


@mcp.tool
def text_process(text: str, operation: str) -> str:
    """
    Process text with various operations.

    Args:
        text: Text to process
        operation: Operation ("uppercase", "lowercase", "title", "reverse", "word_count", "char_count")
    """
    operations = {
        "uppercase": lambda t: t.upper(),
        "lowercase": lambda t: t.lower(),
        "title": lambda t: t.title(),
        "reverse": lambda t: t[::-1],
        "word_count": lambda t: f"Word count: {len(t.split())}",
        "char_count": lambda t: f"Character count: {len(t)}",
        "trim": lambda t: t.strip(),
        "capitalize": lambda t: t.capitalize(),
    }

    if operation not in operations:
        available = ", ".join(operations.keys())
        return f"Unknown operation '{operation}'. Available: {available}"

    try:
        result = operations[operation](text)
        return f"Operation '{operation}' result: {result}"
    except Exception as e:
        return f"Error processing text: {str(e)}"


@mcp.tool
def list_tools() -> dict[str, Any]:
    """Get information about all available tools."""
    tools_info = []

    for tool in mcp.get_tools():
        tool_info = {
            "name": tool.name,
            "description": tool.description,
            "parameters": [
                {"name": param.name, "type": param.type, "required": param.required, "description": param.description}
                for param in tool.parameters
            ],
        }
        tools_info.append(tool_info)

    return {"total_tools": len(tools_info), "tools": tools_info}


# ============================================================================
# Rich Resources with Different MIME Types
# ============================================================================


@mcp.resource("server://status")
def server_status() -> dict[str, Any]:
    """Get comprehensive server status."""
    return {
        "server": "ChukMCPServer Example",
        "status": "running",
        "uptime": time.time(),
        "tools_count": len(mcp.get_tools()),
        "resources_count": len(mcp.get_resources()),
        "framework": "ChukMCPServer with chuk_mcp",
        "inspector_compatible": True,
        "session_count": len(mcp.protocol.session_manager.sessions),
        "timestamp": time.time(),
        "version": "1.0.0",
    }


@mcp.resource("config://settings", mime_type="application/json")
def get_settings() -> dict[str, Any]:
    """Get server configuration and capabilities."""
    return {
        "app_name": "ChukMCPServer Example Server",
        "version": "1.0.0",
        "framework": "ChukMCPServer",
        "powered_by": "chuk_mcp",
        "features": [
            "Type-safe tools",
            "Rich resources",
            "Inspector compatibility",
            "Automatic schema generation",
            "Robust error handling",
            "Session management",
        ],
        "capabilities": {"tools": True, "resources": True, "prompts": False, "logging": False},
        "endpoints": {"mcp": "/mcp", "health": "/health", "docs": "/"},
        "transport": "HTTP with SSE support",
    }


@mcp.resource("docs://readme", mime_type="text/markdown")
def get_readme() -> str:
    """Get comprehensive documentation."""
    return """# ChukMCPServer Example Server

This is a demonstration of ChukMCPServer's clean and simple API powered by chuk_mcp.

## 🚀 Features

- **Type-safe tools** with automatic schema generation
- **Rich resources** with multiple MIME types
- **Inspector compatibility** with perfect SSE streaming  
- **Robust error handling** with chuk_mcp integration
- **Session management** for stateful interactions
- **Modular design** for easy maintenance

## 🔧 Available Tools

- `hello(name)` - Say hello to someone
- `add(x, y)` - Add two numbers
- `calculate(expression)` - Evaluate mathematical expressions
- `generate_random(type, min_val, max_val, length)` - Generate random data
- `get_time(format)` - Get current time in various formats
- `text_process(text, operation)` - Process text with various operations
- `list_tools()` - Get information about all tools

## 📂 Available Resources

- `server://status` - Real-time server status (JSON)
- `config://settings` - Server configuration (JSON)
- `docs://readme` - This documentation (Markdown)
- `data://examples` - Tool usage examples (JSON)

## 🔍 Usage with MCP Inspector

1. This server runs on port 8000
2. Use proxy on port 8011 for Inspector
3. Set Transport Type: **Streamable HTTP**
4. Set URL: `http://localhost:8011/mcp/inspector`
5. Click **Connect**

## 💡 Example Tool Calls

```json
// Say hello
{"name": "hello", "arguments": {"name": "World"}}

// Add numbers  
{"name": "add", "arguments": {"x": 5, "y": 3}}

// Calculate expression
{"name": "calculate", "arguments": {"expression": "sqrt(16) + 2 * 3"}}

// Generate random UUID
{"name": "generate_random", "arguments": {"type": "uuid"}}

// Get current time
{"name": "get_time", "arguments": {"format": "human"}}
```

## 🏗️ Built With

- **ChukMCPServer** - Developer-friendly MCP framework
- **chuk_mcp** - Robust MCP protocol handling
- **Starlette** - Modern ASGI web framework
- **uvicorn** - Lightning-fast ASGI server

## 📈 Performance

- Sub-millisecond tool execution
- Efficient SSE streaming
- Automatic session cleanup
- Comprehensive error handling
- Zero-copy JSON serialization

---

**Powered by ChukMCPServer with chuk_mcp integration!** 🚀
"""


@mcp.resource("data://examples", mime_type="application/json")
def get_examples() -> dict[str, Any]:
    """Get comprehensive tool usage examples."""
    return {
        "description": "Comprehensive tool usage examples for ChukMCP Server",
        "server_info": {
            "name": "ChukMCPServer Example",
            "version": "1.0.0",
            "tools_count": len(mcp.get_tools()),
            "framework": "ChukMCPServer with chuk_mcp",
        },
        "examples": [
            {
                "category": "Basic Operations",
                "tools": [
                    {
                        "tool": "hello",
                        "arguments": {"name": "World"},
                        "description": "Simple greeting",
                        "expected_result": "Hello, World! Welcome to ChukMCPServer!",
                    },
                    {
                        "tool": "add",
                        "arguments": {"x": 10, "y": 15},
                        "description": "Add two integers",
                        "expected_result": 25,
                    },
                ],
            },
            {
                "category": "Mathematical Operations",
                "tools": [
                    {
                        "tool": "calculate",
                        "arguments": {"expression": "sqrt(16) + 2 * 3"},
                        "description": "Complex math expression",
                        "expected_result": "sqrt(16) + 2 * 3 = 10.0",
                    },
                    {
                        "tool": "calculate",
                        "arguments": {"expression": "sin(pi/2)"},
                        "description": "Trigonometric function",
                        "expected_result": "sin(pi/2) = 1.0",
                    },
                ],
            },
            {
                "category": "Random Data Generation",
                "tools": [
                    {
                        "tool": "generate_random",
                        "arguments": {"type": "number", "min_val": 1, "max_val": 100},
                        "description": "Random number in range",
                    },
                    {"tool": "generate_random", "arguments": {"type": "uuid"}, "description": "Random UUID"},
                    {
                        "tool": "generate_random",
                        "arguments": {"type": "password", "length": 12},
                        "description": "Secure password",
                    },
                ],
            },
            {
                "category": "Text Processing",
                "tools": [
                    {
                        "tool": "text_process",
                        "arguments": {"text": "Hello World", "operation": "uppercase"},
                        "description": "Convert to uppercase",
                        "expected_result": "Operation 'uppercase' result: HELLO WORLD",
                    },
                    {
                        "tool": "text_process",
                        "arguments": {"text": "The quick brown fox", "operation": "word_count"},
                        "description": "Count words",
                        "expected_result": "Operation 'word_count' result: Word count: 4",
                    },
                ],
            },
            {
                "category": "Time Operations",
                "tools": [
                    {"tool": "get_time", "arguments": {"format": "iso"}, "description": "ISO format timestamp"},
                    {"tool": "get_time", "arguments": {"format": "human"}, "description": "Human readable time"},
                ],
            },
            {
                "category": "Introspection",
                "tools": [
                    {"tool": "list_tools", "arguments": {}, "description": "Get information about all available tools"}
                ],
            },
        ],
        "usage_tips": [
            "All tools have comprehensive error handling",
            "Type validation is automatic based on function signatures",
            "Default values are supported for optional parameters",
            "Results are formatted as proper MCP content responses",
            "Tools can return strings, numbers, or complex objects",
        ],
    }


# ============================================================================
# Production Server Setup
# ============================================================================


def main():
    """Main entry point for production server."""
    print("🚀 ChukMCPServer Production Server")
    print("=" * 50)

    # Show server information
    info = mcp.info()
    print(f"Server: {info['server']['name']}")
    print(f"Version: {info['server']['version']}")
    print("Framework: ChukMCPServer with chuk_mcp")
    print()

    # Handle both old and new info structure
    mcp_info = info.get("mcp_components", info)  # Fallback to old structure
    print(f"🔧 Tools: {mcp_info['tools']['count']}")
    for tool_name in mcp_info["tools"]["names"]:
        print(f"   - {tool_name}")
    print()
    print(f"📂 Resources: {mcp_info['resources']['count']}")
    for resource_uri in mcp_info["resources"]["uris"]:
        print(f"   - {resource_uri}")
    print()
    print("🔍 MCP Inspector Instructions:")
    print("   1. This server: http://localhost:8000/mcp")
    print("   2. Use proxy: http://localhost:8011/mcp/inspector")
    print("   3. Transport: Streamable HTTP")
    print("   4. All tools and resources available!")
    print("=" * 50)

    # Run server in production mode
    try:
        mcp.run(
            host="localhost",
            port=8000,
            debug=False,  # Production mode
        )
    except KeyboardInterrupt:
        print("\n👋 Server shutting down gracefully...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        logging.error(f"Server error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
