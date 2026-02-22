# ChukMCPServer

**The fastest, most developer-friendly MCP server framework for Python.**

Build production-ready [Model Context Protocol](https://modelcontextprotocol.io) servers in minutes with decorator-based tools, zero-config deployment, and world-class performance.

[![PyPI](https://img.shields.io/pypi/v/chuk-mcp-server)](https://pypi.org/project/chuk-mcp-server/)
[![Python](https://img.shields.io/pypi/pyversions/chuk-mcp-server)](https://pypi.org/project/chuk-mcp-server/)
[![Tests](https://github.com/IBM/chuk-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/IBM/chuk-mcp-server/actions)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)](https://github.com/IBM/chuk-mcp-server)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

```python
from chuk_mcp_server import tool, run

@tool
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

run()  # That's it! Server running on stdio
```

## ⚡ Quick Start

### Installation

```bash
# Basic installation
pip install chuk-mcp-server

# With optional features
pip install chuk-mcp-server[google_drive]  # Google Drive OAuth
```

### Your First Server (30 seconds)

**Option 1: Use the scaffolder** (recommended)
```bash
uvx chuk-mcp-server init my-server
cd my-server
uv run my-server
```

**Option 2: Write it yourself** (5 lines of code)
```python
from chuk_mcp_server import tool, run

@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

run()
```

**Option 3: Add to Claude Desktop** (instant integration)
```bash
uvx chuk-mcp-server init my-server --claude
# Automatically adds to claude_desktop_config.json
```

### Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "my-server"]
    }
  }
}
```

Restart Claude Desktop - your tools are now available!

## 🚀 Why ChukMCPServer?

- **🏆 World-Class Performance**: 36,000+ requests/second, <3ms overhead
- **📋 Full MCP 2025-11-25**: Complete conformance with the latest MCP specification
- **🤖 Claude Desktop Ready**: Zero-config stdio transport
- **⚡ Zero Configuration**: Smart defaults detect everything automatically
- **🔐 OAuth 2.1 Built-In**: Full OAuth support with `@requires_auth` decorator
- **☁️ Cloud Native**: Auto-detects GCP, AWS, Azure, Vercel
- **🔒 Type Safe**: Automatic schema generation from Python type hints
- **🏷️ Tool Annotations**: `read_only_hint`, `destructive_hint`, `idempotent_hint`, `open_world_hint`
- **📊 Structured Output**: `output_schema` on tools with typed `structuredContent` responses
- **🎨 Icons**: Icons on tools, resources, prompts, and server info
- **📦 Dual Transport**: STDIO + Streamable HTTP (with GET SSE streams), both with bidirectional support
- **🧩 Full Protocol Surface**: Sampling, elicitation, progress, roots, subscriptions, completions, tasks, cancellation
- **🛡️ Production Hardened**: Rate limiting, request validation, graceful shutdown, thread safety, health probes
- **🧪 ToolRunner**: Test tools without transport overhead
- **📄 OpenAPI**: Auto-generated OpenAPI 3.1.0 spec at `/openapi.json`

## 📚 Documentation

**Full documentation available at:** https://IBM.github.io/chuk-mcp-server/

- [Getting Started Guide](https://IBM.github.io/chuk-mcp-server/getting-started)
- [Building Tools](https://IBM.github.io/chuk-mcp-server/tools)
- [OAuth Authentication](https://IBM.github.io/chuk-mcp-server/oauth)
- [Deployment Guide](https://IBM.github.io/chuk-mcp-server/deployment)
- [API Reference](https://IBM.github.io/chuk-mcp-server/api)
- [Examples & Tutorials](https://IBM.github.io/chuk-mcp-server/examples)

## 🎯 Core Features

### Decorators for Everything

```python
from chuk_mcp_server import tool, resource, resource_template, prompt, requires_auth

@tool(read_only_hint=True, idempotent_hint=True,
      output_schema={"type": "object", "properties": {"result": {"type": "integer"}}})
def calculate(x: int, y: int) -> dict:
    """Perform calculations with structured output."""
    return {"result": x + y}

@resource("config://settings",
          icons=[{"uri": "https://example.com/gear.svg", "mimeType": "image/svg+xml"}])
def get_settings() -> dict:
    """Access configuration."""
    return {"theme": "dark", "version": "1.0"}

@resource_template("users://{user_id}/profile")
def get_user_profile(user_id: str) -> dict:
    """Parameterized resource template (RFC 6570)."""
    return {"user_id": user_id, "name": "Example User"}

@prompt
def code_review(code: str, language: str) -> str:
    """Generate code review prompt."""
    return f"Review this {language} code:\n{code}"

@tool
@requires_auth()
async def publish_post(content: str, _external_access_token: str | None = None) -> dict:
    """OAuth-protected tool."""
    # Token automatically injected and validated
    ...
```

### HTTP Mode for Web Apps

```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(
    name="my-api",
    description="My production API server",
    icons=[{"uri": "https://example.com/icon.png", "mimeType": "image/png"}],
    website_url="https://example.com",
)

@mcp.tool
async def process_data(data: str) -> dict:
    return {"processed": data}

mcp.run(host="0.0.0.0", port=8000)  # HTTP server
```

### MCP Apps — Rich UI Views in Claude.ai

Render interactive charts, maps, tables, and more directly in Claude.ai using [MCP Apps](https://modelcontextprotocol.io) structured content.

```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(name="my-view-server", version="1.0.0")

@mcp.tool(
    name="show_chart",
    description="Show sales data as a chart.",
    meta={
        "ui": {
            "resourceUri": "ui://my-view-server/chart",
            "viewUrl": "https://chuk-mcp-ui-views.fly.dev/chart/v1",
        }
    },
)
async def show_chart(chart_type: str = "bar") -> dict:
    return {
        "content": [{"type": "text", "text": "Sales chart."}],
        "structuredContent": {
            "type": "chart",
            "version": "1.0",
            "title": "Q1 Sales",
            "chartType": chart_type,
            "data": [{"label": "Revenue", "values": [
                {"label": "Jan", "value": 4200},
                {"label": "Feb", "value": 5100},
                {"label": "Mar", "value": 4800},
            ]}],
        },
    }

mcp.run()
```

**How it works:**
- `meta.ui.resourceUri` — a `ui://` URI identifying the view
- `meta.ui.viewUrl` — HTTPS URL serving the view's HTML/JS bundle
- The server **automatically** registers an MCP resource at the `resourceUri` that fetches the HTML from `viewUrl`
- The server **automatically** enables the `experimental` capability
- Claude.ai reads the HTML via `resources/read`, renders it in an iframe, and passes `structuredContent` as the data payload

See [`examples/mcp_apps_view_example.py`](examples/mcp_apps_view_example.py) for a complete example.

### Cloud Deployment (Auto-Detection)

```python
# Same code works everywhere - cloud platform auto-detected!
from chuk_mcp_server import tool, run

@tool
def my_tool(x: int) -> int:
    return x * 2

run()  # Automatically adapts to GCP, AWS, Azure, Vercel, etc.
```

### Server Composition (Mix Local & Remote Tools)

Combine multiple MCP servers into one unified interface. Import tools from local Python modules or remote servers (STDIO/HTTP/SSE):

```python
# config.yaml
composition:
  import:
    # Local Python module
    - name: "echo"
      type: "module"
      module: "chuk_mcp_echo.server:echo_service"
      prefix: "echo"

    # Remote MCP server via STDIO
    - name: "fetch"
      type: "stdio"
      command: "uvx"
      args: ["mcp-server-fetch"]
      prefix: "fetch"

    # Remote MCP server via HTTP
    - name: "weather"
      type: "http"
      url: "https://api.weather.com/mcp"
      prefix: "weather"
```

```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer("composed-server")
mcp.load_config("config.yaml")
mcp.run()  # All tools available under unified namespaces
```

**What you get:**
- ✅ **Module imports**: Direct Python imports (fastest)
- ✅ **STDIO proxy**: Connect to subprocess servers (uvx, npx, python -m)
- ✅ **HTTP proxy**: Connect to remote HTTP MCP servers
- ✅ **Built-in resilience**: Automatic timeouts, retries, circuit breakers (via chuk-tool-processor)
- ✅ **Unified namespace**: Tools prefixed by source (e.g., `fetch.fetch`, `echo.echo_text`)

## 🏆 Performance

ChukMCPServer is built for high throughput:

- **36,348 RPS** peak throughput (performance test)
- **39,261 RPS** with max optimizations (ultra test)
- **<3ms overhead** per tool call
- **100% success rate** under sustained load

See [Performance Benchmarks](https://IBM.github.io/chuk-mcp-server/benchmarks) for detailed results.

## 📖 Learn More

- **[Full Documentation](https://IBM.github.io/chuk-mcp-server/)** - Complete guides and tutorials
- **[API Reference](https://IBM.github.io/chuk-mcp-server/api)** - Detailed API documentation
- **[Examples](https://IBM.github.io/chuk-mcp-server/examples)** - Real-world examples
- **[GitHub](https://github.com/IBM/chuk-mcp-server)** - Source code and issues
- **[PyPI](https://pypi.org/project/chuk-mcp-server/)** - Package distribution

### Real-World Examples

- **[chuk-mcp-chart](https://github.com/chrishayuk/chuk-mcp-chart)** - Interactive chart server with MCP Apps views
- **[chuk-mcp-linkedin](https://github.com/IBM/chuk-mcp-linkedin)** - LinkedIn OAuth integration
- **[chuk-mcp-stage](https://github.com/IBM/chuk-mcp-stage)** - 3D scene management with Google Drive

## 🤝 Contributing

Contributions welcome! See [Contributing Guide](https://IBM.github.io/chuk-mcp-server/contributing) for details.

## 📄 License

Apache 2.0 License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: https://IBM.github.io/chuk-mcp-server/
- **PyPI Package**: https://pypi.org/project/chuk-mcp-server/
- **GitHub**: https://github.com/IBM/chuk-mcp-server
- **Issues**: https://github.com/IBM/chuk-mcp-server/issues
- **Model Context Protocol**: https://modelcontextprotocol.io

---
