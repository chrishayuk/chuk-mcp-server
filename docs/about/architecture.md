# Architecture

Deep dive into ChukMCPServer's design and architecture.

## High-Level Architecture

ChukMCPServer is built on a modular, high-performance architecture that achieves 39,000+ RPS through intelligent design choices.

```
┌─────────────────────────────────────────────┐
│          ChukMCPServer (Core)               │
│  ┌──────────────┐  ┌──────────────┐        │
│  │   Decorator  │  │   Registry   │        │
│  │     API      │  │    System    │        │
│  └──────────────┘  └──────────────┘        │
│  ┌──────────────────────────────────┐      │
│  │      SmartConfig System          │      │
│  │  Auto-detection & Optimization   │      │
│  └──────────────────────────────────┘      │
└─────────────────────────────────────────────┘
            │                   │
    ┌───────┴───────┐   ┌──────┴──────┐
    │  HTTP         │   │  STDIO      │
    │  Transport    │   │  Transport  │
    │  (Starlette)  │   │  (Standard) │
    └───────────────┘   └─────────────┘
```

## Core Components

### 1. SmartConfig System

Modular detection system that auto-configures based on environment:

```python
SmartConfig
    ├── ProjectDetector      # Name from pyproject.toml/directory
    ├── EnvironmentDetector  # Dev/prod/container/serverless
    ├── NetworkDetector      # Optimal host/port
    ├── SystemDetector       # Hardware optimization
    ├── ContainerDetector    # Docker/K8s detection
    └── CloudDetector        # AWS/GCP/Azure/Edge
```

**Zero Configuration**: Every setting auto-detected with sensible defaults.

### 2. Registry System

Two-tier registry for tools and endpoints:

```python
# MCP Registry: Tools, Resources, Prompts
mcp_registry.py
    - Tool registration with schema caching
    - Resource URI management
    - Prompt template storage

# Endpoint Registry: HTTP routes
endpoint_registry.py
    - Auto-registered HTTP endpoints
    - CORS configuration
    - SSE streaming support
```

**Pre-Cached Schemas**: Generated once at registration, zero overhead at runtime.

### 3. Type System

Type-safe handlers with automatic validation:

```python
src/chuk_mcp_server/types/
    ├── tool_handler.py      # Tool execution
    ├── resource_handler.py  # Resource access
    └── schema_generator.py  # JSON schema from types
```

**Performance**: Direct integration with underlying `chuk_mcp` library, orjson serialization.

### 4. Transport Layer

Dual transport support:

```python
src/chuk_mcp_server/transport/
    ├── http.py    # Starlette + uvloop (39K+ RPS)
    └── stdio.py   # Standard MCP protocol
```

**HTTP Transport**:
- Built on Starlette for ASGI performance
- uvloop event loop (2-4x faster)
- Automatic CORS support
- SSE for streaming

**STDIO Transport**:
- Standard MCP protocol
- Process-based communication
- Zero network overhead

### 5. Protocol Layer

MCP JSON-RPC implementation:

```python
protocol.py
    - JSON-RPC request/response handling
    - Session management
    - Error handling
    - Capability negotiation
```

### 6. OAuth System

Two-layer authentication:

```python
src/chuk_mcp_server/oauth/
    ├── middleware.py       # OAuth middleware
    ├── models.py           # Data models
    ├── token_store.py      # Secure storage
    ├── helpers.py          # Setup helpers
    └── providers/
        └── google_drive.py # Provider implementations
```

**Layer 1**: MCP Layer (Claude ↔ Your Server)
**Layer 2**: Provider Layer (Your Server ↔ External Service)

### 7. Cloud Support

Platform-specific adapters:

```python
src/chuk_mcp_server/cloud/
    ├── base.py            # Base adapter
    ├── gcp.py             # Google Cloud
    ├── aws.py             # AWS Lambda
    ├── azure.py           # Azure Functions
    └── edge.py            # Edge platforms
```

Auto-detects cloud environment and exports appropriate handler.

## Design Patterns

### Decorator Pattern

Clean, FastAPI-like API:

```python
@tool
def my_tool():
    ...

# Translates to:
def my_tool():
    ...
my_tool = tool(my_tool)
```

### Registry Pattern

Centralized component management:

```python
# Registration
mcp.register_tool("add", handler)

# Retrieval
handler = mcp.get_tool("add")

# Discovery
tools = mcp.list_tools()
```

### Factory Pattern

Dynamic handler creation:

```python
def create_tool_handler(func):
    """Create optimized handler for function."""
    # Analyze function signature
    # Generate schema
    # Create wrapper
    return handler
```

### Middleware Pattern

Request/response processing:

```python
from chuk_mcp_server.endpoint_registry import register_middleware

# Define middleware class
class CustomMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Pre-processing logic
        if scope["type"] == "http":
            # Modify scope if needed
            scope["custom_data"] = "value"

        # Continue to next middleware/application
        await self.app(scope, receive, send)

        # No post-processing possible with this pattern
        # (Post-processing would need to be done in the send function)

# Register middleware with priority (lower runs earlier)
register_middleware(CustomMiddleware, priority=50, name="custom_middleware")
```

## Performance Architecture

### 1. Pre-Caching

Schemas generated once at registration:

```python
# At registration time
schema = generate_schema(tool_func)
registry.cache_schema(tool_name, schema)

# At runtime (zero overhead)
schema = registry.get_cached_schema(tool_name)
```

### 2. orjson Serialization

2-3x faster JSON operations:

```python
import orjson

# Serialize
data = orjson.dumps(obj)

# Deserialize
obj = orjson.loads(data)
```

### 3. uvloop Event Loop

2-4x faster than standard asyncio:

```python
import uvloop

uvloop.install()
asyncio.run(main())
```

### 4. Worker Optimization

Intelligent worker count:

```python
# I/O bound (default)
workers = (cpu_count * 2) + 1

# CPU bound
workers = cpu_count
```

## Data Flow

### Tool Execution Flow

```
1. HTTP Request → Starlette App
2. JSON-RPC Parsing → Protocol Layer
3. Tool Lookup → Registry
4. Schema Validation → Type System
5. Handler Execution → Tool Function
6. Result Serialization → orjson
7. HTTP Response → Client
```

### OAuth Flow

```
1. Tool Call (requires auth)
2. Check Token Store
3. If expired: Refresh Token
4. Call External API with Token
5. Return Result
```

## Extension Points

### 1. Custom Transports

Implement new transport layer:

```python
from chuk_mcp_server.transport.base import Transport

class MyTransport(Transport):
    async def start(self):
        ...
    
    async def handle_request(self, request):
        ...
```

### 2. Custom OAuth Providers

Implement OAuth provider:

```python
from chuk_mcp_server.oauth import BaseOAuthProvider

class MyProvider(BaseOAuthProvider):
    async def authorize(self, params):
        ...
    
    async def exchange_authorization_code(self, code):
        ...
```

### 3. Custom Middleware

Add custom processing:

```python
from chuk_mcp_server.endpoint_registry import register_middleware

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Log the request
        print(f"Request: {scope['method']} {scope['path']}")

        # Pass to the next middleware/application
        await self.app(scope, receive, send)

# Register with priority (lower numbers run earlier)
register_middleware(LoggingMiddleware, priority=10, name="logging")
```

## Scalability

### Horizontal Scaling

Deploy multiple instances behind load balancer:

```
Load Balancer
    ├── Instance 1 (4 workers)
    ├── Instance 2 (4 workers)
    ├── Instance 3 (4 workers)
    └── Instance 4 (4 workers)
```

### Vertical Scaling

Optimize single instance:

```python
# More workers
mcp.run(workers=16)

# Larger connection pool
pool = await asyncpg.create_pool(max_size=100)
```

## Security Architecture

### 1. OAuth 2.1

- PKCE required
- Secure token storage
- Automatic refresh
- Scope validation

### 2. Input Validation

- Type checking via mypy
- Schema validation via JSON Schema
- Automatic sanitization

### 3. Error Handling

- No stack traces in production
- Secure error messages
- Comprehensive logging

## Next Steps

- [FAQ](faq.md) - Common questions
- [Performance](../performance/benchmarks.md) - Benchmarks
- [Advanced](../advanced/configuration.md) - Deep dive
