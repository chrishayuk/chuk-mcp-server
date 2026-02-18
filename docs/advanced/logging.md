# Advanced Logging

Configure logging for debugging and deployment monitoring.

## Log Levels

ChukMCPServer uses Python's standard logging:

```python
from chuk_mcp_server import ChukMCPServer

# Development: detailed logs
mcp = ChukMCPServer(name="my-server")
mcp.run(log_level="debug")

# Deployed: minimal logs
mcp.run(log_level="warning")
```

Available levels:
- `debug` - Verbose, all operations
- `info` - Normal operations
- `warning` - Warning messages
- `error` - Error messages only
- `critical` - Critical errors only

## Custom Logger

Use your own logger:

```python
import logging
from chuk_mcp_server import ChukMCPServer

# Configure custom logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("my_mcp_server")

mcp = ChukMCPServer(name="my-server")

@mcp.tool
def my_tool():
    logger.info("Tool called")
    return "result"

mcp.run()
```

## Structured Logging

For deployed systems:

```python
import structlog
from chuk_mcp_server import ChukMCPServer

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

mcp = ChukMCPServer(name="my-server")

@mcp.tool
def process_data(data: dict):
    logger.info("processing_data",
                data_size=len(data),
                user_id=data.get("user_id"))
    return {"processed": True}

mcp.run()
```

## Request Logging

Log all MCP requests:

```python
from chuk_mcp_server import ChukMCPServer
from chuk_mcp_server.endpoint_registry import register_middleware
import logging

logger = logging.getLogger(__name__)

mcp = ChukMCPServer(name="my-server")

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Log request
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "UNKNOWN")
        logger.info(f"Request: {method} {path}")

        # Create wrapped send to log responses
        original_send = send

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                status = message.get("status", 0)
                logger.info(f"Response: {status}")
            await original_send(message)

        # Continue processing with wrapped send function
        await self.app(scope, receive, wrapped_send)

# Register middleware
register_middleware(LoggingMiddleware, priority=30, name="request_logging")

mcp.run()
```

## Error Tracking

Integrate with error tracking services:

```python
import sentry_sdk
from chuk_mcp_server import ChukMCPServer

# Initialize Sentry
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)

mcp = ChukMCPServer(name="my-server")

@mcp.tool
def risky_operation():
    try:
        # Operation that might fail
        result = perform_operation()
        return result
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

mcp.run()
```

## Performance Logging

Track performance metrics:

```python
from chuk_mcp_server import ChukMCPServer
import time
import logging

logger = logging.getLogger(__name__)

mcp = ChukMCPServer(name="my-server")

@mcp.tool
def slow_operation():
    start = time.time()

    # Do work
    result = compute_something()

    duration = time.time() - start
    logger.info(f"Operation took {duration:.2f}s")

    if duration > 1.0:
        logger.warning(f"Slow operation: {duration:.2f}s")

    return result

mcp.run()
```

## Next Steps

- [Configuration](configuration.md) - Advanced config
- [Performance](performance.md) - Optimization
- [Production](../deployment/production.md) - Deployment
