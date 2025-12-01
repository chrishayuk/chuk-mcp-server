# Context Management

Track sessions and users across tool calls.

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
