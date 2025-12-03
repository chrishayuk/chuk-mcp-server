# Context Architecture for chuk-mcp-server

## Overview

The context management system provides thread-safe, async-safe storage for request-scoped data across the MCP server framework and consumer applications.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Consumer Applications (chuk-mcp-linkedin, etc.)             │
│ ├─ Import: from chuk_mcp_server import require_user_id     │
│ └─ Usage: user_id = require_user_id()                      │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│ chuk-mcp-server Framework                                   │
│ ├─ context.py: Generic context management                  │
│ │  ├─ Session ID (MCP session)                            │
│ │  ├─ User ID (OAuth user)                                │
│ │  ├─ HTTP Request (Starlette request data)               │
│ │  ├─ Progress Token                                       │
│ │  └─ Metadata                                             │
│ └─ protocol.py: Sets context on each request              │
│    ├─ set_session_id() on initialize                      │
│    └─ set_user_id() after OAuth validation                │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│ Python contextvars (stdlib)                                 │
│ └─ Thread-safe, async-safe context isolation               │
└─────────────────────────────────────────────────────────────┘
```

## Context Variables

### Session Context
- **Purpose**: Identify the MCP session
- **Set by**: Protocol handler during initialization
- **Used by**: Server infrastructure, logging, session management
- **Functions**: `get_session_id()`, `set_session_id()`, `require_session_id()`

### User Context
- **Purpose**: Identify the authenticated OAuth user
- **Set by**: Protocol handler after OAuth token validation
- **Used by**: Consumer tools/resources that need user-specific data
- **Functions**: `get_user_id()`, `set_user_id()`, `require_user_id()`

### HTTP Request Context
- **Purpose**: Access HTTP request data in tools and middleware
- **Set by**: ContextMiddleware (automatically via HTTP server)
- **Used by**: Tools that need request data
- **Functions**: `get_http_request()`

### Progress Token
- **Purpose**: Enable progress notifications to clients
- **Set by**: Protocol handler from request params
- **Used by**: Long-running tools to report progress
- **Functions**: `get_progress_token()`, `set_progress_token()`

### Metadata
- **Purpose**: Store arbitrary request-scoped data
- **Set by**: Any layer that needs to pass context
- **Used by**: Extensions, middleware, custom features
- **Functions**: `get_metadata()`, `set_metadata()`, `update_metadata()`

## Usage Patterns

### In Protocol Handler (chuk-mcp-server)

```python
# protocol.py
from .context import set_session_id, set_user_id

async def handle_request(self, message, session_id=None, oauth_token=None):
    # Set session context
    if session_id:
        set_session_id(session_id)

    # After OAuth validation
    if user_id:
        set_user_id(user_id)

    # Handle request...
```

### In Consumer Tools (chuk-mcp-linkedin)

```python
# LinkedIn tool
from chuk_mcp_server import require_user_id, get_session_id

@mcp.tool()
async def create_linkedin_post(content: str):
    # Require authentication
    user_id = require_user_id()  # Raises PermissionError if not authenticated

    # Optional: get session for logging
    session_id = get_session_id()  # Returns None if not in session

    # Use user-scoped manager
    manager = get_manager_for_user(user_id)
    return manager.create_draft(content)
```

### Using HTTP Request Context

```python
# Tool with access to HTTP request data
from chuk_mcp_server import tool, get_http_request

@tool
def get_request_info() -> dict:
    """Tool that returns information about the HTTP request."""
    request = get_http_request()  # Get the HTTP request from context

    # Access request properties
    return {
        "path": request.get("path", ""),
        "method": request.get("method", ""),
        "client_host": request.get("client", {}).get("host", ""),
        "headers": {
            k.decode("utf-8"): v.decode("utf-8")
            for k, v in request.get("headers", [])
        }
    }
```

### With Context Manager (for complex scenarios)

```python
from chuk_mcp_server import RequestContext

async with RequestContext(
    session_id="abc123",
    user_id="user456",
    progress_token=1,
    metadata={"source": "api"}
):
    # Context is set for this block
    await handle_tool_call()
    # Context is automatically restored on exit
```

## Comparison with chuk-mcp-runtime

The `chuk-mcp-server` context is inspired by `chuk-mcp-runtime` but adapted for the server framework:

### Similarities
- Both use Python `contextvars` for thread/async safety
- Both provide context manager pattern for lifecycle management
- Both support nested contexts with restoration
- Both include progress notification support

### Differences
- **chuk-mcp-server**: Generic server framework (session + user + metadata)
- **chuk-mcp-runtime**: Client runtime focused on progress notifications
- **chuk-mcp-server**: Provides `require_user_id()` for auth enforcement
- **chuk-mcp-runtime**: Provides `send_progress()` convenience function

## Migration from chuk-mcp-linkedin.auth

Consumer applications should migrate from local auth context to generic server context:

### Before (chuk-mcp-linkedin specific)
```python
from chuk_mcp_linkedin.auth import get_current_user_id, set_current_user

user_id = get_current_user_id()
```

### After (generic chuk-mcp-server)
```python
from chuk_mcp_server import require_user_id, set_user_id

user_id = require_user_id()
```

## Benefits

1. **Generic**: Reusable across all chuk-mcp consumer applications
2. **Consistent**: Same patterns as chuk-mcp-runtime
3. **Type-safe**: Full type hints and IDE support
4. **Thread-safe**: Built on contextvars stdlib
5. **Async-safe**: Works correctly with async/await
6. **Nestable**: Supports nested contexts with proper restoration
7. **Extensible**: Metadata system for custom data

## Future Enhancements

Potential additions to consider:

1. **Progress notifications**: Add `send_progress()` helper (like chuk-mcp-runtime)
2. **Request ID**: Add unique ID for each request for tracing
3. **Timing**: Add request start time for performance tracking
4. **Cancellation**: Add cancellation token support
5. **Logging**: Add structured logging context helpers
