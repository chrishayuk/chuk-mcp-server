# HTTP Mode

Deploy your MCP server as an HTTP API for web applications, production services, or testing.

## Quick Start

```python
from chuk_mcp_server import tool, run

@tool
def greet(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"

# Run in HTTP mode
run(transport="http", port=8000)
```

Access at `http://localhost:8000`

## HTTP vs STDIO

| Feature         | STDIO          | HTTP                 |
| --------------- | -------------- | -------------------- |
| **Use Case**    | Claude Desktop | Web APIs, Production |
| **Transport**   | stdin/stdout   | HTTP/HTTPS           |
| **Performance** | N/A (local)    | 36,000+ RPS          |
| **Testing**     | Pipe commands  | curl, browser        |
| **Deployment**  | Desktop only   | Cloud, Docker, etc.  |

## Configuration

### Basic Server

```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer("my-api")

@mcp.tool
def my_tool(param: str) -> dict:
    return {"result": param}

mcp.run(host="0.0.0.0", port=8000)
```

### Production Settings

```python
mcp.run(
    transport="http",
    host="0.0.0.0",      # Listen on all interfaces
    port=8000,
    workers=4,           # Number of worker processes
    log_level="info"     # Logging level
)
```

### Environment Variables

```bash
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
export MCP_LOG_LEVEL=info
export MCP_WORKERS=4
```

## Endpoints

When running in HTTP mode, these endpoints are available:

### Health Check

```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

### List Tools

```bash
curl http://localhost:8000/tools/list
# Returns list of available tools
```

### MCP Protocol

```bash
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Version

```bash
curl http://localhost:8000/version
# {"version": "0.4.4"}
```

## Testing

### With curl

```bash
# Health check
curl http://localhost:8000/health

# List tools
curl http://localhost:8000/tools/list

# Call a tool
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "greet",
      "arguments": {"name": "World"}
    }
  }'
```

### With Python

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "greet",
                "arguments": {"name": "World"}
            }
        }
    )
    print(response.json())
```

## CORS

CORS is enabled by default for HTTP mode. Configure if needed:

```python
from starlette.middleware.cors import CORSMiddleware
from chuk_mcp_server.endpoint_registry import register_middleware

# CORS is auto-configured, but you can customize:
class CustomCORSMiddleware:
    def __init__(self, app):
        self.app = app
        self.cors_middleware = CORSMiddleware(
            app=app,
            allow_origins=["https://example.com"],
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
            expose_headers=["X-Custom-Header"],
        )

    async def __call__(self, scope, receive, send):
        await self.cors_middleware(scope, receive, send)

# Register with high priority so it runs early
register_middleware(CustomCORSMiddleware, priority=20, name="custom_cors")
```

## Performance

HTTP mode achieves 36,000+ requests/second. Optimize with:

### 1. Multiple Workers

```python
mcp.run(workers=4)  # Use 4 worker processes
```

### 2. uvloop

Automatically enabled on Linux/macOS:

```bash
pip install uvloop  # Included by default
```

### 3. Production Server

Use uvicorn directly for more control:

```bash
uvicorn my_server:mcp.app --host 0.0.0.0 --port 8000 --workers 4
```

## SSL/HTTPS

For production, use HTTPS:

```python
mcp.run(
    host="0.0.0.0",
    port=443,
    ssl_certfile="/path/to/cert.pem",
    ssl_keyfile="/path/to/key.pem"
)
```

Or use a reverse proxy (recommended):

```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring

### Logging

```python
import logging

logging.basicConfig(level=logging.INFO)

mcp.run(log_level="info")
```

### Health Checks

```bash
# Simple health check
curl http://localhost:8000/health

# Use in Docker healthcheck
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
```

## Next Steps

- [Docker Deployment](docker.md) - Containerize your server
- [Cloud Deployment](cloud.md) - Deploy to AWS, GCP, Azure
- [Production Guide](production.md) - Best practices
- [Performance](../performance/benchmarks.md) - Optimization guide
