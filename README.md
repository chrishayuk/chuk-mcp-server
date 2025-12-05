# ChukMCPServer

**The fastest, most developer-friendly MCP server framework for Python.**

Build production-ready [Model Context Protocol](https://modelcontextprotocol.io) servers in minutes with decorator-based tools, zero-config deployment, and world-class performance.

[![PyPI](https://img.shields.io/pypi/v/chuk-mcp-server)](https://pypi.org/project/chuk-mcp-server/)
[![Python](https://img.shields.io/pypi/pyversions/chuk-mcp-server)](https://pypi.org/project/chuk-mcp-server/)
[![Tests](https://github.com/chrishayuk/chuk-mcp-server/actions/workflows/test.yml/badge.svg)](https://github.com/chrishayuk/chuk-mcp-server/actions)
[![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen)](https://github.com/chrishayuk/chuk-mcp-server)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

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
- **🤖 Claude Desktop Ready**: Zero-config stdio transport
- **⚡ Zero Configuration**: Smart defaults detect everything automatically
- **🔐 OAuth 2.1 Built-In**: Full OAuth support with `@requires_auth` decorator
- **☁️ Cloud Native**: Auto-detects GCP, AWS, Azure, Vercel
- **🔒 Type Safe**: Automatic schema generation from Python type hints
- **💬 Prompts Support**: Create reusable prompt templates
- **🔄 Context Management**: Track sessions and users
- **📦 Dual Transport**: STDIO (Claude Desktop) + HTTP (Web APIs)

## 📚 Documentation

**Full documentation available at:** https://chrishayuk.github.io/chuk-mcp-server/

- [Getting Started Guide](https://chrishayuk.github.io/chuk-mcp-server/getting-started)
- [Building Tools](https://chrishayuk.github.io/chuk-mcp-server/tools)
- [OAuth Authentication](https://chrishayuk.github.io/chuk-mcp-server/oauth)
- [Deployment Guide](https://chrishayuk.github.io/chuk-mcp-server/deployment)
- [API Reference](https://chrishayuk.github.io/chuk-mcp-server/api)
- [Examples & Tutorials](https://chrishayuk.github.io/chuk-mcp-server/examples)

## 🎯 Core Features

### Decorators for Everything

```python
from chuk_mcp_server import tool, resource, prompt, requires_auth

@tool
def calculate(x: int, y: int) -> int:
    """Perform calculations."""
    return x + y

@resource("config://settings")
def get_settings() -> dict:
    """Access configuration."""
    return {"theme": "dark", "version": "1.0"}

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

mcp = ChukMCPServer("my-api")

@mcp.tool
async def process_data(data: str) -> dict:
    return {"processed": data}

mcp.run(host="0.0.0.0", port=8000)  # Production-ready HTTP server
```

### Cloud Deployment (Auto-Detection)

```python
# Same code works everywhere - cloud platform auto-detected!
from chuk_mcp_server import tool, run

@tool
def my_tool(x: int) -> int:
    return x * 2

run()  # Automatically adapts to GCP, AWS, Azure, Vercel, etc.
```

## 🏆 Performance

ChukMCPServer is built for production:

- **36,348 RPS** peak throughput (performance test)
- **39,261 RPS** with max optimizations (ultra test)
- **<3ms overhead** per tool call
- **100% success rate** under sustained load

See [Performance Benchmarks](https://chrishayuk.github.io/chuk-mcp-server/benchmarks) for detailed results.

## 📖 Learn More

- **[Full Documentation](https://chrishayuk.github.io/chuk-mcp-server/)** - Complete guides and tutorials
- **[API Reference](https://chrishayuk.github.io/chuk-mcp-server/api)** - Detailed API documentation
- **[Examples](https://chrishayuk.github.io/chuk-mcp-server/examples)** - Real-world examples
- **[GitHub](https://github.com/chrishayuk/chuk-mcp-server)** - Source code and issues
- **[PyPI](https://pypi.org/project/chuk-mcp-server/)** - Package distribution

### Real-World Examples

- **[chuk-mcp-linkedin](https://github.com/chrishayuk/chuk-mcp-linkedin)** - LinkedIn OAuth integration
- **[chuk-mcp-stage](https://github.com/chrishayuk/chuk-mcp-stage)** - 3D scene management with Google Drive

## 🤝 Contributing

Contributions welcome! See [Contributing Guide](https://chrishayuk.github.io/chuk-mcp-server/contributing) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: https://chrishayuk.github.io/chuk-mcp-server/
- **PyPI Package**: https://pypi.org/project/chuk-mcp-server/
- **GitHub**: https://github.com/chrishayuk/chuk-mcp-server
- **Issues**: https://github.com/chrishayuk/chuk-mcp-server/issues
- **Model Context Protocol**: https://modelcontextprotocol.io

---

**Built with ❤️ for the Claude ecosystem**
