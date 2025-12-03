# Context Management

Track sessions, users, and HTTP requests across tool calls.

## Session Context

Get the current MCP session ID:

```python
from chuk_mcp_server import tool, get_session_id

@tool
def my_tool() -> dict:
    """Tool with session context."""
    session = get_session_id()
    return {"session": session}
```

## User Context

Get the current OAuth user ID:

```python
from chuk_mcp_server import tool, get_user_id

@tool
def my_tool() -> dict:
    """Tool with user context."""
    user = get_user_id()  # None if not authenticated
    return {"user": user}
```

## HTTP Request Context

Access the HTTP request data in tools:

```python
from chuk_mcp_server import tool, get_http_request

@tool
def request_info() -> dict:
    """Tool with HTTP request context."""
    request = get_http_request()  # Get request from context

    # Access request properties (headers, path, method, etc.)
    return {
        "path": request.get("path", ""),
        "method": request.get("method", ""),
        "headers": {
            k.decode("utf-8"): v.decode("utf-8")
            for k, v in request.get("headers", [])
        }
    }
```

## Require Authentication

```python
from chuk_mcp_server import tool, require_user_id

@tool
def protected_tool() -> dict:
    """Requires authentication."""
    user_id = require_user_id()  # Raises if not authenticated
    return {"user": user_id}
```

## Next Steps

- [OAuth](../oauth/overview.md) - Authentication
- [Protected Tools](../oauth/protected-tools.md) - Auth tools
- [Tools Guide](../tools/basic.md) - Building tools
