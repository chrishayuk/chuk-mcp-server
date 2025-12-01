# Quick Start

Get up and running with ChukMCPServer in 30 seconds.

## Three Ways to Start

Choose the approach that works best for you:

=== "Scaffolder (Recommended)"

    The fastest way to create a new server:

    ```bash
    uvx chuk-mcp-server init my-server
    cd my-server
    uv run my-server
    ```

    This creates a complete project structure with:
    - Pre-configured `pyproject.toml`
    - Example tools
    - Test setup
    - Documentation

=== "Manual (5 Lines)"

    Write it yourself in seconds:

    ```python
    from chuk_mcp_server import tool, run

    @tool
    def greet(name: str) -> str:
        """Greet someone by name."""
        return f"Hello, {name}!"

    run()
    ```

    Save as `server.py` and run:
    ```bash
    python server.py
    ```

=== "Claude Desktop (Instant)"

    Auto-configure for Claude Desktop:

    ```bash
    uvx chuk-mcp-server init my-server --claude
    ```

    This automatically:
    - Creates the server
    - Adds to `claude_desktop_config.json`
    - Configures the command path

    Restart Claude Desktop and you're ready!

## Your First Tool

Let's build a simple calculator:

```python
from chuk_mcp_server import tool, run

@tool
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

run()
```

That's it! Save and run:

```bash
python calculator.py
```

## Testing Your Server

### With STDIO Transport (Default)

The server runs on stdio transport by default, perfect for Claude Desktop:

```bash
python server.py
```

Test by piping JSON-RPC:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python server.py
```

### With HTTP Transport

For web APIs and testing in the browser:

```python
from chuk_mcp_server import tool, run

@tool
def greet(name: str) -> str:
    return f"Hello, {name}!"

run(transport="http", port=8000)
```

Test with curl:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/tools/list
```

## Adding More Tools

Tools are just Python functions with the `@tool` decorator:

```python
from chuk_mcp_server import tool

@tool
def get_weather(city: str) -> dict:
    """Get weather for a city."""
    # In real code, call a weather API
    return {
        "city": city,
        "temperature": 72,
        "condition": "sunny"
    }

@tool
async def fetch_data(url: str) -> str:
    """Fetch data from a URL (async example)."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

## Next Steps

- [Your First Server](first-server.md) - Detailed tutorial
- [Claude Desktop Setup](claude-desktop.md) - Connect to Claude
- [Building Tools](../tools/basic.md) - Learn all about tools
- [Examples](../examples/calculator.md) - See real-world examples

## Common Patterns

### Global vs Server-Based API

=== "Global (Simple)"

    ```python
    from chuk_mcp_server import tool, run

    @tool
    def my_tool():
        return "Hello"

    run()
    ```

=== "Server-Based (Advanced)"

    ```python
    from chuk_mcp_server import ChukMCPServer

    mcp = ChukMCPServer("my-server")

    @mcp.tool
    def my_tool():
        return "Hello"

    mcp.run()
    ```

Use **global** for quick scripts, **server-based** for multiple servers or advanced features.

## Troubleshooting

**Server won't start?**

Check that the port isn't already in use:
```bash
lsof -i :8000  # Check if port 8000 is in use
```

**Tools not showing in Claude?**

Make sure:
1. Server is running
2. `claude_desktop_config.json` is correct
3. Claude Desktop was restarted after config changes

**Import errors?**

Ensure ChukMCPServer is installed:
```bash
pip install chuk-mcp-server
```
