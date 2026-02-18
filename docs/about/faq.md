# Frequently Asked Questions

Common questions about ChukMCPServer.

## General

### What is ChukMCPServer?

ChukMCPServer is a high-performance Python framework for building MCP (Model Context Protocol) servers. It provides zero-configuration deployment with automatic environment detection, achieving 39,000+ requests per second.

### Why ChukMCPServer?

- **Zero Configuration**: Auto-detects everything (project name, host, port, workers)
- **High Performance**: 39,000+ RPS with uvloop and orjson
- **Developer Friendly**: FastAPI-like decorator syntax
- **Deployment Ready**: Built-in OAuth, cloud support, comprehensive tests

### Is it ready for deployment?

Yes! ChukMCPServer v1.0+ is battle-tested with:
- 87%+ test coverage (1400+ tests)
- Type-safe with full mypy checking
- Battle-tested in cloud environments
- OAuth 2.1 with PKCE support

### What's the license?

MIT License - free for commercial and personal use. See [License](license.md).

## Installation

### How do I install ChukMCPServer?

```bash
pip install chuk-mcp-server

# With OAuth support
pip install chuk-mcp-server[google_drive]
```

### What Python version is required?

Python 3.11 or higher.

### Can I use pip instead of uv?

Yes! While uv is recommended for speed, standard pip works fine:

```bash
pip install chuk-mcp-server
```

## Usage

### Do I need to configure anything?

Nope! Just write your tools and run:

```python
from chuk_mcp_server import tool, run

@tool
def hello(name: str) -> str:
    return f"Hello, {name}!"

run()  # Everything auto-detected
```

### How do I choose HTTP vs STDIO transport?

```python
# STDIO (default for Claude Desktop)
run()  # or run(transport="stdio")

# HTTP (for web APIs)
run(transport="http")
```

ChukMCPServer auto-detects the best transport based on your environment.

### Can I use async functions?

Absolutely! ChukMCPServer handles both sync and async:

```python
@tool
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### How do I add authentication?

Use the built-in OAuth middleware:

```python
from chuk_mcp_server import tool, requires_auth

@tool
@requires_auth(scopes=["read"])
async def protected_tool(_external_access_token: str | None = None):
    # Use token to call external API
    return {"data": "protected"}
```

See [OAuth Guide](../oauth/overview.md).

## Performance

### How fast is ChukMCPServer?

- **Simple tools**: 35,000-40,000 RPS
- **Database queries**: 15,000-25,000 RPS
- **External APIs**: 5,000-15,000 RPS

See [Benchmarks](../performance/benchmarks.md).

### How do I optimize performance?

Most optimizations are automatic, but you can:
1. Use async for I/O operations
2. Enable connection pooling
3. Add caching where appropriate
4. Adjust worker count

See [Performance Guide](../advanced/performance.md).

### Why is it so fast?

- **uvloop**: 2-4x faster event loop
- **orjson**: 2-3x faster JSON serialization
- **Pre-cached schemas**: Zero overhead at runtime
- **Starlette**: High-performance ASGI framework

## Deployment

### How do I deploy?

Multiple options:

```bash
# HTTP mode (easiest)
python server.py

# Docker
docker build -t my-mcp-server .
docker run -p 8000:8000 my-mcp-server

# Cloud platforms (auto-detected)
# Just deploy - ChukMCPServer adapts automatically
```

See [Deployment Guides](../deployment/http-mode.md).

### Does it work in Docker?

Yes! ChukMCPServer auto-detects Docker and optimizes accordingly:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install chuk-mcp-server
CMD ["python", "server.py"]
```

### What cloud platforms are supported?

All major platforms with auto-detection:
- Google Cloud (Cloud Run, Cloud Functions)
- AWS (Lambda, ECS, Fargate)
- Azure (Functions, Container Apps)
- Edge (Vercel, Netlify, Cloudflare Workers)

See [Cloud Deployment](../deployment/cloud.md).

## Integration

### Can I integrate with Claude Desktop?

Yes! ChukMCPServer works perfectly with Claude Desktop via STDIO transport.

See [Claude Desktop Guide](../getting-started/claude-desktop.md).

### Can I use it with FastAPI?

Yes! Mount ChukMCPServer into your FastAPI app:

```python
from fastapi import FastAPI
from chuk_mcp_server import ChukMCPServer

app = FastAPI()
mcp = ChukMCPServer(name="my-server")

app.mount("/mcp", mcp.app)
```

### Does it work with existing Python projects?

Absolutely! ChukMCPServer is just a library - integrate it anywhere:

```python
from your_project import business_logic
from chuk_mcp_server import tool

@tool
def process_data(data: dict) -> dict:
    return business_logic.process(data)
```

## Troubleshooting

### Tests are failing

```bash
# Run tests locally
make test

# Check specific test
pytest tests/test_file.py::test_name -v

# Debug
pytest --pdb
```

### Type errors with mypy

Ensure all functions have type hints:

```python
# ❌ Bad
def my_tool(data):
    return data

# ✅ Good
def my_tool(data: dict) -> dict:
    return data
```

### Import errors

Check your installation:

```bash
pip list | grep chuk-mcp-server

# Reinstall if needed
pip install --force-reinstall chuk-mcp-server
```

### Performance issues

1. Check worker count: `mcp.run(workers=16)`
2. Use async for I/O: `async def my_tool()`
3. Enable connection pooling
4. Profile with benchmarks: `python benchmarks/quick_benchmark.py`

## Development

### How do I contribute?

We welcome contributions! See [Contributing Guide](../contributing/pull-requests.md).

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### How do I run tests?

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test
pytest tests/test_file.py -v
```

### How do I report bugs?

[Open an issue](https://github.com/chrishayuk/chuk-mcp-server/issues) with:
- Description of the issue
- Minimal reproduction example
- Expected vs actual behavior
- Python version and OS

## Support

### Where can I get help?

- **Documentation**: You're reading it!
- **GitHub Issues**: Bug reports
- **GitHub Discussions**: Questions
- **Discord**: Real-time chat

### Is commercial support available?

Yes! Contact for enterprise support options:
- Priority bug fixes
- Custom features
- Training and consulting

## Still Have Questions?

- [Read the docs](../index.md)
- [Check examples](../examples/calculator.md)
- [Ask on GitHub](https://github.com/chrishayuk/chuk-mcp-server/discussions)
- [Join Discord](https://discord.gg/your-server)
