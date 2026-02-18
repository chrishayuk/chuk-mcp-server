# Transport Modes

ChukMCPServer supports two transport modes: STDIO and HTTP.

## STDIO Transport

Standard input/output transport for Claude Desktop:

```python
from chuk_mcp_server import tool, run

@tool
def my_tool():
    return "Hello"

run()  # Default: STDIO
```

**Use for:**
- Claude Desktop integration
- Local development
- Command-line tools

## HTTP Transport

HTTP server for web APIs and deployed services:

```python
from chuk_mcp_server import tool, run

@tool
def my_tool():
    return "Hello"

run(transport="http", port=8000)
```

**Use for:**
- Web applications
- Deployed APIs
- Testing with curl/browser
- Cloud deployment

## Comparison

| Feature | STDIO | HTTP |
|---------|-------|------|
| Use Case | Desktop | Web/Cloud |
| Performance | N/A | 36,000+ RPS |
| Testing | Pipes | curl/browser |
| Deployment | Local | Anywhere |

## Next Steps

- [Claude Desktop Setup](../getting-started/claude-desktop.md) - STDIO
- [HTTP Mode](../deployment/http-mode.md) - HTTP deployment
- [Cloud Deployment](../deployment/cloud.md) - Cloud platforms
