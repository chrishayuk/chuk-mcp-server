# API Reference

Complete reference for all ChukMCPServer APIs, decorators, functions, and types.

## Core Decorators

| Decorator | Purpose | Required Parameters | Optional Parameters |
|-----------|---------|---------------------|---------------------|
| `@tool` | Define a callable tool/function for Claude | None | `name`, `description` |
| `@resource(uri)` | Define a data resource Claude can read | `uri` (e.g., `"config://app"`) | `name`, `description`, `mime_type` |
| `@prompt` | Define a reusable prompt template | None | `name`, `description` |
| `@requires_auth()` | Mark a tool as requiring OAuth | None | `scopes` (list of strings) |

### Examples

**Basic Tool:**
```python
from chuk_mcp_server import tool

@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
```

**Resource:**
```python
from chuk_mcp_server import resource

@resource("config://app")
def get_config() -> dict:
    """Application configuration."""
    return {"version": "1.0", "mode": "production"}
```

**Prompt Template:**
```python
from chuk_mcp_server import prompt

@prompt
def code_review(code: str, language: str = "python") -> str:
    """Review code for best practices."""
    return f"Review this {language} code:\\n{code}"
```

**Authenticated Tool:**
```python
from chuk_mcp_server import tool, requires_auth

@tool
@requires_auth(scopes=["email", "profile"])
async def get_user_info() -> dict:
    """Get authenticated user information."""
    # OAuth user ID is automatically available
    return {"authenticated": True}
```

## Server Functions

| Function | Purpose | Parameters | Example |
|----------|---------|------------|---------|
| `run()` | Start the MCP server | `transport` ("stdio"/"http"), `host`, `port`, `log_level` | `run()` or `run(port=8000)` |
| `ChukMCPServer()` | Create server instance (class-based API) | `name` (optional) | `mcp = ChukMCPServer("my-server")` |

### Examples

**Simple STDIO Server:**
```python
from chuk_mcp_server import tool, run

@tool
def hello(name: str = "World") -> str:
    return f"Hello, {name}!"

run()  # Starts STDIO server for Claude Desktop
```

**HTTP Server:**
```python
run(transport="http", port=8000)  # HTTP server at http://localhost:8000
```

**Class-Based API:**
```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(name="my-custom-server")

@mcp.tool
def my_tool() -> str:
    return "Hello from class-based API"

mcp.run()
```

## Context Management

| Function | Purpose | Returns | Use Case |
|----------|---------|---------|----------|
| `get_session_id()` | Get current MCP session ID | `str \| None` | Track requests per session |
| `get_user_id()` | Get current OAuth user ID | `str \| None` | Check if user is authenticated |
| `require_user_id()` | Get user ID or raise error | `str` (raises `PermissionError`) | Enforce authentication |
| `set_session_id(id)` | Set session context | None | Testing, manual control |
| `set_user_id(id)` | Set user context | None | Testing, manual control |
| `RequestContext()` | Context manager for request context | Context manager | Testing, background tasks |

See [Context Management Guide](../guides/context-management.md) for detailed examples.

## Artifact Storage

| Function | Purpose | Returns |
|----------|---------|---------|
| `get_artifact_store()` | Get the current artifact store | `ArtifactStore` |
| `set_artifact_store(store)` | Set artifact store for current context | None |
| `set_global_artifact_store(store)` | Set global fallback store | None |
| `has_artifact_store()` | Check if store is available | `bool` |
| `clear_artifact_store()` | Clear store (useful for testing) | None |
| `create_blob_namespace(**kwargs)` | Create blob namespace | `NamespaceInfo` |
| `create_workspace_namespace(name, **kwargs)` | Create workspace namespace | `NamespaceInfo` |
| `write_blob(namespace_id, data, mime)` | Write blob data | None |
| `read_blob(namespace_id)` | Read blob data | `bytes` |
| `write_workspace_file(namespace_id, path, data)` | Write file to workspace | None |
| `read_workspace_file(namespace_id, path)` | Read file from workspace | `bytes` |
| `get_namespace_vfs(namespace_id)` | Get VFS for workspace | `AsyncVirtualFileSystem` |

See [Artifacts Guide](../guides/artifacts.md) for detailed examples.

## Cloud Helpers

| Function | Purpose | Returns |
|----------|---------|---------|
| `is_cloud()` | Check if running in any cloud environment | `bool` |
| `is_gcf()` | Check if running in Google Cloud Functions | `bool` |
| `is_lambda()` | Check if running in AWS Lambda | `bool` |
| `is_azure()` | Check if running in Azure Functions | `bool` |
| `get_deployment_info()` | Get detailed deployment information | `dict` |
| `get_cloud_handler()` | Get cloud-specific handler | Handler function |

### Examples

```python
from chuk_mcp_server import is_cloud, get_deployment_info

if is_cloud():
    info = get_deployment_info()
    print(f"Running in {info['provider']} - {info['service_type']}")
```

## Type Hints

ChukMCPServer automatically generates JSON schemas from Python type hints:

```python
from typing import Literal

@tool
def process_file(
    filename: str,
    mode: Literal["read", "write", "append"] = "read",
    encoding: str = "utf-8"
) -> dict:
    """Process a file with specified mode."""
    return {
        "filename": filename,
        "mode": mode,
        "encoding": encoding
    }
```

Supported types:
- `str`, `int`, `float`, `bool`
- `list`, `dict`
- `Optional[T]`, `Union[T1, T2]`
- `Literal["choice1", "choice2"]`
- Pydantic models
- Custom dataclasses

## Async Support

All decorators support both sync and async functions:

```python
import httpx

@tool
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

## Error Handling

ChukMCPServer automatically converts Python exceptions to MCP error responses:

```python
@tool
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

Claude will receive a proper error message if division by zero is attempted.

## Configuration

See [Configuration Guide](../deployment/configuration.md) for:
- Environment variables
- Logging configuration
- Port and host settings
- Performance tuning

## Related Documentation

- [Getting Started](../getting-started/) - Quick start guides
- [Guides](../guides/) - How-to guides and tutorials
- [Deployment](../deployment/) - Deployment guides
- [OAuth Integration](../OAUTH.md) - OAuth 2.1 setup
- [Transport Modes](../TRANSPORT_MODES.md) - STDIO vs HTTP
