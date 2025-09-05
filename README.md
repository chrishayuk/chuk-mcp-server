# ChukMCPServer

[![PyPI](https://img.shields.io/pypi/v/chuk-mcp-server)](https://pypi.org/project/chuk-mcp-server/)
[![Python](https://img.shields.io/pypi/pyversions/chuk-mcp-server)](https://pypi.org/project/chuk-mcp-server/)
[![License](https://img.shields.io/pypi/l/chuk-mcp-server)](https://github.com/chrishayuk/chuk-mcp-server/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/tests-824%20passing-success)](https://github.com/chrishayuk/chuk-mcp-server)
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)](https://github.com/chrishayuk/chuk-mcp-server)

**The fastest, most intelligent MCP (Model Context Protocol) server framework.** Build LLM-integrated tools with zero configuration, blazing performance, and seamless Claude Desktop integration.

## 🎯 Why ChukMCPServer?

- **🚀 Instant Setup**: Works with Claude Desktop in under 30 seconds
- **⚡ Blazing Fast**: 39,000+ requests/second with sub-5ms latency
- **🧠 Zero Config**: Auto-detects everything - just write your tools
- **🔌 Dual Transport**: Native stdio for Claude Desktop + HTTP/SSE for web
- **📦 No Dependencies**: Pure Python with optional performance boosters
- **🎨 Clean API**: Decorator-based like FastAPI, but simpler

## 📸 Quick Demo

```python
# server.py - A complete MCP server in 10 lines!
from chuk_mcp_server import tool, resource, run

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return f"{expression} = {eval(expression)}"

@resource("data://example")
def get_data() -> dict:
    """Get example data."""
    return {"message": "Hello from ChukMCP!", "status": "ready"}

if __name__ == "__main__":
    run()  # That's it! 🎉
```

## 🚀 Quickstart

### 1. Install

```bash
# Using pip
pip install chuk-mcp-server

# Using uv (recommended)
uv add chuk-mcp-server
```

### 2. Run with Claude Desktop

Add to your Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {"MCP_STDIO": "1"}
    }
  }
}
```

Or use `uvx` for zero-install:

```json
{
  "mcpServers": {
    "chuk": {
      "command": "uvx",
      "args": ["chuk-mcp-server", "stdio"]
    }
  }
}
```

### 3. Test It

```bash
# Quick test with stdio
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python server.py

# Run as HTTP server
python server.py  # Visit http://localhost:8000

# Use the CLI
uvx chuk-mcp-server stdio  # For Claude Desktop
uvx chuk-mcp-server http   # For web/HTTP clients
```

## 🎨 Real-World Examples

### File System Tools

```python
from chuk_mcp_server import ChukMCPServer
import os
from pathlib import Path

mcp = ChukMCPServer(name="filesystem-tools")

@mcp.tool
def list_files(directory: str = ".", pattern: str = "*") -> list[str]:
    """List files in a directory matching a pattern."""
    path = Path(directory)
    if not path.exists():
        return [f"Error: {directory} does not exist"]
    
    files = []
    for item in path.glob(pattern):
        if item.is_file():
            size = item.stat().st_size
            files.append(f"{item.name} ({size:,} bytes)")
    return files

@mcp.tool
def read_file(filepath: str, lines: int = None) -> str:
    """Read contents of a file."""
    try:
        with open(filepath, 'r') as f:
            if lines:
                return ''.join(f.readlines()[:lines])
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

@mcp.tool  
def write_file(filepath: str, content: str, append: bool = False) -> str:
    """Write content to a file."""
    mode = 'a' if append else 'w'
    try:
        with open(filepath, mode) as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing file: {e}"

@mcp.resource("fs://current-dir")
def current_directory() -> dict:
    """Get current directory information."""
    cwd = os.getcwd()
    return {
        "path": cwd,
        "files": len([f for f in os.listdir(cwd) if os.path.isfile(f)]),
        "directories": len([d for d in os.listdir(cwd) if os.path.isdir(d)]),
        "readable": os.access(cwd, os.R_OK),
        "writable": os.access(cwd, os.W_OK)
    }

if __name__ == "__main__":
    mcp.run()  # Auto-detects stdio vs HTTP mode!
```

### API Integration Tools

```python
from chuk_mcp_server import ChukMCPServer
import httpx
import asyncio

mcp = ChukMCPServer(name="api-tools")

@mcp.tool
async def fetch_url(url: str, method: str = "GET", headers: dict = None) -> dict:
    """Fetch data from a URL."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, headers=headers)
            return {
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": response.text[:1000],  # First 1000 chars
                "size": len(response.content)
            }
        except Exception as e:
            return {"error": str(e)}

@mcp.tool
async def parallel_fetch(urls: list[str]) -> list[dict]:
    """Fetch multiple URLs in parallel."""
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for url, resp in zip(urls, responses):
            if isinstance(resp, Exception):
                results.append({"url": url, "error": str(resp)})
            else:
                results.append({
                    "url": url,
                    "status": resp.status_code,
                    "size": len(resp.content)
                })
        return results

@mcp.resource("api://status")
async def api_status() -> dict:
    """Check status of common APIs."""
    endpoints = [
        "https://api.github.com",
        "https://api.openai.com/v1/models",
        "https://www.googleapis.com/discovery/v1/apis"
    ]
    
    statuses = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for endpoint in endpoints:
            try:
                resp = await client.get(endpoint)
                statuses[endpoint] = "✅ Online" if resp.status_code < 500 else "⚠️ Issues"
            except:
                statuses[endpoint] = "❌ Offline"
    
    return statuses

if __name__ == "__main__":
    mcp.run()
```

### Data Processing Tools

```python
from chuk_mcp_server import ChukMCPServer
import json
import csv
from io import StringIO

mcp = ChukMCPServer(name="data-tools")

@mcp.tool
def json_to_csv(json_data: str | list | dict) -> str:
    """Convert JSON data to CSV format."""
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data
    
    if not isinstance(data, list):
        data = [data]
    
    if not data:
        return "No data to convert"
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()

@mcp.tool
def analyze_json(json_data: str | dict) -> dict:
    """Analyze JSON structure and statistics."""
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data
    
    def analyze_value(value, path="root"):
        stats = {"path": path, "type": type(value).__name__}
        
        if isinstance(value, dict):
            stats["keys"] = len(value)
            stats["nested"] = {}
            for k, v in value.items():
                stats["nested"][k] = analyze_value(v, f"{path}.{k}")
        elif isinstance(value, list):
            stats["length"] = len(value)
            if value:
                stats["item_types"] = list(set(type(v).__name__ for v in value))
        elif isinstance(value, str):
            stats["length"] = len(value)
        elif isinstance(value, (int, float)):
            stats["value"] = value
            
        return stats
    
    return analyze_value(data)

@mcp.tool
def transform_data(
    data: list[dict],
    operations: list[str]
) -> list[dict]:
    """
    Apply transformations to data.
    Operations: 'uppercase', 'lowercase', 'trim', 'remove_nulls'
    """
    result = data.copy()
    
    for op in operations:
        if op == "uppercase":
            result = [{k: v.upper() if isinstance(v, str) else v 
                      for k, v in item.items()} for item in result]
        elif op == "lowercase":
            result = [{k: v.lower() if isinstance(v, str) else v 
                      for k, v in item.items()} for item in result]
        elif op == "trim":
            result = [{k: v.strip() if isinstance(v, str) else v 
                      for k, v in item.items()} for item in result]
        elif op == "remove_nulls":
            result = [{k: v for k, v in item.items() if v is not None} 
                     for item in result]
    
    return result

if __name__ == "__main__":
    mcp.run()
```

## 🔌 Transport Modes

ChukMCPServer supports two transport modes, auto-detected based on environment:

### STDIO Mode (for Claude Desktop & CLI tools)

```bash
# Auto-detects stdio when piped or when MCP_STDIO is set
MCP_STDIO=1 python server.py

# Or use the CLI
uvx chuk-mcp-server stdio
```

### HTTP Mode (for web clients & APIs)

```bash
# Auto-detects HTTP when not piped
python server.py

# Or use the CLI  
uvx chuk-mcp-server http --port 8000
```

## ⚡ Performance

ChukMCPServer is the fastest MCP implementation available:

| Metric | Performance | Conditions |
|--------|------------|------------|
| **Throughput** | 39,651 RPS | Ping endpoint, local |
| **Latency** | < 5ms p99 | Tool execution |
| **Concurrency** | 1,000+ connections | HTTP/SSE mode |
| **Memory** | < 50MB | 1000 tools registered |
| **Startup** | < 100ms | Full initialization |

### Performance Tips

```python
# Enable performance mode
mcp = ChukMCPServer(performance_mode="high")

# Or via environment
os.environ["MCP_PERFORMANCE_MODE"] = "high_performance"
```

## 🧠 Smart Configuration

ChukMCPServer auto-detects everything:

- **Project name** from package.json, pyproject.toml, or directory
- **Environment** (development/production/serverless)
- **Network settings** (host, port, available ports)
- **Transport mode** (stdio vs HTTP)
- **Performance settings** based on system resources
- **Cloud environment** (AWS, GCP, Azure, Vercel, etc.)

Override anything you need:

```python
mcp = ChukMCPServer(
    name="my-server",           # Auto-detected if not set
    port=3000,                  # Auto-detected if not set
    host="0.0.0.0",            # Auto-detected if not set
    performance_mode="high"     # Auto-detected if not set
)
```

## 📚 API Reference

### Tools

```python
@mcp.tool
def my_tool(param: str, optional: int = 10) -> dict:
    """Tool description for LLM."""
    return {"result": param, "count": optional}

# Async tools
@mcp.tool
async def async_tool(data: str) -> str:
    await asyncio.sleep(1)
    return f"Processed: {data}"

# Renamed tools
@mcp.tool("custom-name")
def another_tool() -> str:
    return "result"
```

### Resources

```python
@mcp.resource("protocol://path")
def my_resource() -> dict:
    """Resource description."""
    return {"data": "value"}

# Async resources
@mcp.resource("async://data")
async def async_resource() -> dict:
    await fetch_data()
    return {"data": "value"}

# Markdown resources
@mcp.resource("docs://readme", mime_type="text/markdown")
def get_docs() -> str:
    return "# Documentation\nContent here..."
```

### Prompts

```python
@mcp.prompt
def my_prompt(context: str) -> str:
    """Generate a prompt based on context."""
    return f"Based on {context}, please..."

# With arguments
@mcp.prompt("code-review")
def code_review_prompt(language: str, code: str) -> str:
    return f"Review this {language} code:\n{code}"
```

## 🔧 CLI Usage

```bash
# Install globally
pip install chuk-mcp-server

# Run in stdio mode (for MCP clients)
chuk-mcp-server stdio

# Run in HTTP mode
chuk-mcp-server http --port 8000

# Run with debug output
chuk-mcp-server stdio --debug

# Auto-detect mode from environment
chuk-mcp-server auto
```

## 🐳 Docker Support

```dockerfile
FROM python:3.11-slim
RUN pip install chuk-mcp-server
COPY server.py .

# For stdio mode
CMD ["python", "server.py"]

# For HTTP mode
# EXPOSE 8000
# CMD ["chuk-mcp-server", "http", "--host", "0.0.0.0"]
```

## 🧪 Testing

```python
# test_server.py
from chuk_mcp_server import ChukMCPServer
import pytest

@pytest.fixture
def mcp():
    server = ChukMCPServer()
    
    @server.tool
    def test_tool(value: int) -> int:
        return value * 2
    
    return server

def test_tool_execution(mcp):
    # Tools are automatically executable
    result = mcp.get_tools()[0]
    assert result["name"] == "test_tool"
```

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

```bash
# Setup development environment
git clone https://github.com/chrishayuk/chuk-mcp-server
cd chuk-mcp-server
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov

# Type checking
mypy src
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

Built on top of the [Model Context Protocol](https://modelcontextprotocol.io) specification by Anthropic.

## 🔗 Links

- [Documentation](https://github.com/chrishayuk/chuk-mcp-server/docs)
- [PyPI Package](https://pypi.org/project/chuk-mcp-server/)
- [GitHub Repository](https://github.com/chrishayuk/chuk-mcp-server)
- [Issue Tracker](https://github.com/chrishayuk/chuk-mcp-server/issues)

---

**Made with ❤️ for the MCP community**