# ChukMCPServer Documentation

Welcome to the **ChukMCPServer** documentation! ChukMCPServer is the fastest, most developer-friendly Model Context Protocol (MCP) server framework for Python.

## What is ChukMCPServer?

ChukMCPServer lets you build production-ready MCP servers in minutes with:

- **Decorator-based API** - Define tools with simple `@tool` decorators
- **Zero Configuration** - Smart defaults detect everything automatically
- **World-Class Performance** - 36,000+ requests/second, <3ms overhead
- **OAuth 2.1 Built-In** - Full authentication with `@requires_auth`
- **Cloud Native** - Auto-detects GCP, AWS, Azure, Vercel
- **Dual Transport** - STDIO (Claude Desktop) + HTTP (Web APIs)

```python
from chuk_mcp_server import tool, run

@tool
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

run()  # That's it! Production-ready server
```

## Quick Links

<div class="grid cards" markdown>

- :material-rocket-launch: **[Getting Started](getting-started/installation.md)**

    Install ChukMCPServer and create your first server in 30 seconds

- :material-hammer-wrench: **[Building Tools](tools/basic.md)**

    Learn how to create powerful tools for Claude

- :material-shield-lock: **[OAuth & Auth](oauth/overview.md)**

    Add OAuth 2.1 authentication to your servers

- :material-cloud-upload: **[Deployment](deployment/http-mode.md)**

    Deploy to production with HTTP, Docker, or cloud platforms

- :material-speedometer: **[Performance](performance/benchmarks.md)**

    See benchmark results and optimization guides

- :material-code-braces: **[API Reference](api/decorators.md)**

    Complete API documentation

</div>

## Features at a Glance

### 🎯 Core Features

| Feature | Description |
|---------|-------------|
| **@tool** | Define callable tools for Claude |
| **@resource** | Expose data and configurations |
| **@prompt** | Create reusable prompt templates |
| **@requires_auth** | Add OAuth protection to tools |
| **Context Management** | Track sessions and users |
| **Type Safety** | Automatic validation from type hints |

### 🚀 Transport Modes

| Transport | Use Case | Performance |
|-----------|----------|-------------|
| **STDIO** | Claude Desktop integration | N/A (local) |
| **HTTP** | Web APIs, production deployment | 36,000+ RPS |

### ☁️ Cloud Support

Auto-detects and optimizes for:

- Google Cloud Platform (Cloud Functions, Cloud Run)
- AWS (Lambda, ECS, Fargate)
- Azure (Functions, Container Apps)
- Vercel, Netlify, Cloudflare Workers
- Docker, Kubernetes

### 🔐 OAuth 2.1

Full OAuth 2.1 implementation with:

- PKCE support (RFC 7636)
- Authorization Server Discovery (RFC 8414)
- Protected Resource Metadata (RFC 9728)
- Built-in Google Drive provider
- Custom provider support

## Why Choose ChukMCPServer?

=== "Performance"

    **36,000+ requests/second** with <3ms overhead per tool call

    - Built on uvloop and Starlette
    - Pre-cached schema generation
    - Optimized JSON-RPC handling
    - Zero-copy operations where possible

=== "Developer Experience"

    **Write less code, ship faster**

    - Decorator-based API (FastAPI-style)
    - Zero configuration required
    - Automatic type validation
    - Built-in scaffolder

=== "Production Ready"

    **Deploy with confidence**

    - Cloud platform auto-detection
    - OAuth 2.1 authentication
    - Comprehensive error handling
    - 88% test coverage

=== "Ecosystem"

    **Integrates with everything**

    - Claude Desktop (zero config)
    - HTTP APIs (REST-friendly)
    - Docker & Kubernetes
    - Cloud platforms (GCP, AWS, Azure)

## Getting Started

Ready to build your first MCP server?

1. **[Install ChukMCPServer](getting-started/installation.md)** - Get up and running in minutes
2. **[Create Your First Server](getting-started/first-server.md)** - Build a simple calculator
3. **[Add to Claude Desktop](getting-started/claude-desktop.md)** - Connect to Claude
4. **[Build Real Tools](tools/basic.md)** - Create production tools

## Example Servers

See real-world examples:

- **[chuk-mcp-linkedin](https://github.com/chrishayuk/chuk-mcp-linkedin)** - LinkedIn OAuth integration
- **[chuk-mcp-stage](https://github.com/chrishayuk/chuk-mcp-stage)** - 3D scene management with Google Drive

## Community & Support

- **[GitHub Issues](https://github.com/chrishayuk/chuk-mcp-server/issues)** - Report bugs or request features
- **[GitHub Discussions](https://github.com/chrishayuk/chuk-mcp-server/discussions)** - Ask questions
- **[Contributing Guide](contributing/setup.md)** - Help improve ChukMCPServer

## License

ChukMCPServer is released under the [MIT License](about/license.md).
