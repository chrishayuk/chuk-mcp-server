# Context Management

Access request context in your tools and resources to track sessions, authenticate users, and manage request-specific data.

## Overview

ChukMCPServer provides context management for:
- **Session tracking**: MCP session IDs for request correlation
- **User authentication**: OAuth user IDs for authenticated requests
- **Request metadata**: Custom data for advanced scenarios

## Basic Context Access

```python
from chuk_mcp_server import tool, get_session_id, get_user_id

@tool
def get_current_context() -> dict:
    """Get information about the current request."""
    session = get_session_id()  # MCP session ID (or None)
    user = get_user_id()        # OAuth user ID (or None)

    return {
        "session_id": session,
        "user_id": user,
        "authenticated": user is not None
    }
```

## Require Authentication

Use `require_user_id()` to enforce OAuth authentication:

```python
from chuk_mcp_server import tool, require_user_id, requires_auth

@tool
@requires_auth()
async def create_private_resource(name: str) -> dict:
    """Create a user-specific resource."""
    # This will raise PermissionError if user is not authenticated
    user_id = require_user_id()

    # Now safely use user_id for user-specific operations
    return {
        "created": name,
        "owner": user_id,
        "private": True
    }
```

## Context Manager Pattern

Set context manually for testing or advanced scenarios:

```python
from chuk_mcp_server import RequestContext

async with RequestContext(
    session_id="test-session",
    user_id="user-123",
    metadata={"source": "test"}
):
    # All tools called within this block will have this context
    result = await my_tool()
```

## Available Context Functions

```python
from chuk_mcp_server import (
    get_session_id,      # Get current MCP session ID
    set_session_id,      # Set MCP session ID
    get_user_id,         # Get current OAuth user ID (returns None if not authenticated)
    set_user_id,         # Set OAuth user ID
    require_user_id,     # Get user ID or raise PermissionError
    RequestContext,      # Context manager for manual control
)
```

## Use Cases

| Function | Purpose | When to Use |
|----------|---------|-------------|
| `get_user_id()` | Check if user is authenticated (optional) | When authentication is optional |
| `require_user_id()` | Enforce authentication (raises error if not authenticated) | When authentication is required |
| `get_session_id()` | Track requests per MCP session | For session-based state management |
| `RequestContext` | Manual context control | Testing, background tasks, manual control |

## Examples

### Optional Authentication

```python
@tool
def get_user_data() -> dict:
    """Get user-specific or public data."""
    user_id = get_user_id()

    if user_id:
        # Return personalized data
        return {"data": "private", "user": user_id}
    else:
        # Return public data
        return {"data": "public"}
```

### Required Authentication

```python
@tool
@requires_auth()
async def delete_account() -> dict:
    """Delete the authenticated user's account."""
    user_id = require_user_id()  # Will raise PermissionError if not authenticated

    # Proceed with deletion
    await delete_user(user_id)

    return {"deleted": user_id}
```

### Session Tracking

```python
@tool
def track_request() -> dict:
    """Track requests by session."""
    session_id = get_session_id()

    # Store or log request by session
    log_request(session_id=session_id)

    return {"session": session_id, "tracked": True}
```

### Testing with Context

```python
import pytest
from chuk_mcp_server import RequestContext, require_user_id

async def test_authenticated_tool():
    """Test tool with authentication."""
    async with RequestContext(user_id="test-user-123"):
        # Tool will see user_id as "test-user-123"
        user_id = require_user_id()
        assert user_id == "test-user-123"

async def test_unauthenticated_tool():
    """Test tool without authentication."""
    with pytest.raises(PermissionError):
        # No context set, should raise error
        require_user_id()
```

## Architecture

For details on how context management is implemented, see [Context Architecture](../CONTEXT_ARCHITECTURE.md).

## Related Documentation

- [OAuth Integration](../OAUTH.md) - Setting up OAuth authentication
- [Artifacts](./artifacts.md) - Using context with artifact storage
- [API Reference](./api-reference.md) - Complete API documentation
