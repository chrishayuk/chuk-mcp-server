# Advanced Configuration

Deep dive into ChukMCPServer configuration options.

## SmartConfig System

ChukMCPServer uses a modular detection system:

```python
from chuk_mcp_server import ChukMCPServer
from chuk_mcp_server.config import SmartConfig

# Auto-detection (recommended)
mcp = ChukMCPServer(name="my-server")
mcp.run()  # Everything auto-detected

# Manual configuration
config = SmartConfig(
    project_name="my-custom-name",
    host="0.0.0.0",
    port=9000,
    workers=8,
    log_level="debug"
)
mcp = ChukMCPServer.from_config(config)
```

## Configuration Detectors

### ProjectDetector

Auto-detects project name from:
- `pyproject.toml`
- `setup.py`
- Directory name

```python
from chuk_mcp_server.config import ProjectDetector

detector = ProjectDetector()
name = detector.detect()  # "my-mcp-server"
```

### EnvironmentDetector

Identifies environment:
- Development
- Production
- Container (Docker/K8s)
- Serverless (Lambda/Cloud Functions)

```python
from chuk_mcp_server.config import EnvironmentDetector

detector = EnvironmentDetector()
env = detector.detect()  # "development" | "production" | "container" | "serverless"
```

### NetworkDetector

Optimizes network settings:

```python
from chuk_mcp_server.config import NetworkDetector

detector = NetworkDetector()
host, port = detector.detect()

# Development: localhost:8000
# Container: 0.0.0.0:8000
# Cloud: 0.0.0.0:$PORT
```

### SystemDetector

Hardware optimization:

```python
from chuk_mcp_server.config import SystemDetector

detector = SystemDetector()
workers = detector.detect_workers()  # CPU count * 2 + 1
```

## Environment Variables

Override any setting:

```bash
# Network
export CHUK_HOST=0.0.0.0
export CHUK_PORT=9000

# Performance
export CHUK_WORKERS=16
export CHUK_LOG_LEVEL=debug

# Features
export CHUK_ENABLE_CORS=true
export CHUK_ENABLE_METRICS=true
```

## Runtime Configuration

Change settings at runtime:

```python
from chuk_mcp_server import ChukMCPServer
from chuk_mcp_server.endpoint_registry import register_middleware

mcp = ChukMCPServer(name="my-server")

# Add custom middleware
class CustomMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Custom logic before request

        # Modify scope if needed
        scope["custom_data"] = "value"

        # Continue to next middleware
        await self.app(scope, receive, send)

# Register the middleware (priority 50 means it runs earlier)
register_middleware(CustomMiddleware, priority=50, name="custom_middleware")

# Add custom routes
@mcp.app.get("/health")
async def health_check():
    return {"status": "healthy"}

mcp.run()
```

## Next Steps

- [Logging](logging.md) - Advanced logging
- [Performance](performance.md) - Optimization tips
- [Deployment](../deployment/production.md) - Production setup
