# Context & Session Management Examples

These examples demonstrate how to use chuk-mcp-server's context system with chuk-artifacts for proper user and session isolation.

## Overview

The context system provides automatic user and session tracking for MCP servers, enabling:
- **Session Isolation**: Each conversation has isolated ephemeral storage
- **User Persistence**: User data persists across all their sessions
- **Automatic Scoping**: No manual parameter passing needed
- **Thread-safe**: Uses ContextVars for async-safe isolation

## Examples

### 1. Context Basics (`context_basics_example.py`)

**What it shows:**
- Basic context variable access (`get_user_id()`, `get_session_id()`)
- Using `RequestContext` manager for automatic setup/cleanup
- Nested contexts and restoration
- Authentication checks with `require_user_id()` and `require_session_id()`
- Simulating request handlers
- Context metadata

**Run it:**
```bash
uv run examples/context_basics_example.py
```

**Key takeaways:**
- Context is automatically isolated per request
- `RequestContext` handles setup and cleanup
- No manual parameter passing needed
- Works seamlessly with async/await

---

### 2. Session Isolation (`context_session_isolation_example.py`)

**What it shows:**
- SESSION scope: Data isolated per session
- Same user in different sessions = different data
- Session-to-session data isolation
- Workspace isolation per session
- Concurrent session handling
- Proper SessionManager integration

**Run it:**
```bash
uv run --extra artifacts examples/context_session_isolation_example.py
```

**Key takeaways:**
- Grid paths include session ID: `grid/{sandbox}/session-{id}/{namespace_id}`
- Each session is completely isolated
- Perfect for ephemeral conversation data
- Multiple sessions can run concurrently
- Data expires when session expires

**Example output:**
```
✓ Alice creates a document in Session 1:
  Grid path: grid/sandbox-0cb4280c/session-001/ns-107f77bd1130

✓ Session 1 lists its artifacts:
  Found 1 artifact(s)

✓ Session 2 lists its artifacts:
  Found 1 artifact(s)  # Different artifact, isolated!
```

---

### 3. User Persistence (`context_user_persistence_example.py`)

**What it shows:**
- USER scope: Data persists across all user sessions
- Same user can access data from any session
- User-to-user data isolation
- Persistent workspaces and projects
- User preferences pattern
- Different users have separate USER storage

**Run it:**
```bash
uv run --extra artifacts examples/context_user_persistence_example.py
```

**Key takeaways:**
- Grid paths use user ID: `grid/{sandbox}/user-{user_id}/{namespace_id}`
- USER data accessible from ALL sessions
- Perfect for projects, preferences, persistent storage
- Changes in one session visible in all others
- Users cannot see each other's USER data

**Example output:**
```
✓ Alice creates a USER-scoped document in Session 1:
  Grid path: grid/sandbox-37125b4c/user-alice/ns-6f36ed4eef13

✓ Alice accesses the SAME document from Session 2:
  Content: Alice's persistent data v1
  Current session: alice-sess-2
  Document created in different session: alice-sess-1

✓ Alice updates the document from Session 3:
  Changes made in Session 3 are visible in Session 1!
```

---

## Storage Scope Comparison

| Scope | Lifetime | Grid Path | Use Cases |
|-------|----------|-----------|-----------|
| **SESSION** | Ephemeral | `grid/{sandbox}/session-{id}/{namespace_id}` | Temporary work, caches, conversation data |
| **USER** | Persistent | `grid/{sandbox}/user-{id}/{namespace_id}` | Projects, preferences, personal data |
| **SANDBOX** | Shared | `grid/{sandbox}/shared/{namespace_id}` | Templates, shared libraries, documentation |

## Typical Usage Pattern

```python
from chuk_mcp_server import ChukMCPServer
from chuk_mcp_server.context import RequestContext, get_user_id, get_session_id
from chuk_artifacts import ArtifactStore, StorageScope

# In your MCP server
server = ChukMCPServer()
store = ArtifactStore()

@server.tool
async def create_temp_document(content: str):
    """Create temporary document in current session."""
    # Context is already set by MCP framework
    ns = await store.create_namespace(
        scope=StorageScope.SESSION,  # Ephemeral
        user_id=get_user_id(),       # From context
        session_id=get_session_id(), # From context
    )
    await store.write_namespace(ns.namespace_id, data=content.encode())
    return {"id": ns.namespace_id, "path": ns.grid_path}

@server.tool
async def create_user_project(name: str):
    """Create persistent project for user."""
    ns = await store.create_namespace(
        type=NamespaceType.WORKSPACE,
        name=name,
        scope=StorageScope.USER,  # Persists across sessions!
        user_id=get_user_id(),
    )
    return {"id": ns.namespace_id, "path": ns.grid_path}
```

## Context Flow in MCP Server

```
1. Client sends request to MCP server
   ↓
2. MCP framework extracts user_id and session_id from request
   ↓
3. Framework sets up RequestContext:
   async with RequestContext(user_id=..., session_id=...):
   ↓
4. Tool functions execute with context available:
   - get_user_id() returns current user
   - get_session_id() returns current session
   ↓
5. ArtifactStore operations automatically use context:
   - SESSION scope uses current session_id
   - USER scope uses current user_id
   ↓
6. RequestContext cleans up automatically on exit
```

## Key APIs

### Context Functions
```python
from chuk_mcp_server.context import (
    RequestContext,         # Async context manager
    get_user_id,           # Get current user (or None)
    get_session_id,        # Get current session (or None)
    require_user_id,       # Get user or raise PermissionError
    require_session_id,    # Get session or raise RuntimeError
)

# Usage in tools
@server.tool
async def my_tool():
    user = get_user_id()            # Optional: returns None if not set
    user = require_user_id()        # Required: raises if not set
    session = get_session_id()       # Optional: returns None if not set
    session = require_session_id()   # Required: raises if not set
```

### SessionManager
```python
# Allocate sessions (typically done by framework)
session_id = await session_manager.allocate_session(
    session_id="optional-custom-id",
    user_id="alice",
    ttl_hours=24,
)

# Validate session
is_valid = await session_manager.validate_session(session_id)

# Extend session TTL
extended = await session_manager.extend_session_ttl(session_id, additional_hours=12)

# Delete session
deleted = await session_manager.delete_session(session_id)
```

### ArtifactStore with Context
```python
from chuk_artifacts import ArtifactStore, StorageScope, NamespaceType

store = ArtifactStore()

# SESSION-scoped artifact (ephemeral)
ns = await store.create_namespace(
    type=NamespaceType.BLOB,
    scope=StorageScope.SESSION,
    user_id=get_user_id(),
    session_id=get_session_id(),
)

# USER-scoped artifact (persistent)
ns = await store.create_namespace(
    type=NamespaceType.WORKSPACE,
    name="my-project",
    scope=StorageScope.USER,
    user_id=get_user_id(),
)

# List artifacts for current session
session_artifacts = store.list_namespaces(session_id=get_session_id())

# List artifacts for current user
user_artifacts = store.list_namespaces(user_id=get_user_id())
```

## Dependencies

Basic context examples:
```bash
uv run examples/context_basics_example.py
```

Examples with artifacts (SESSION/USER isolation):
```bash
# Install with artifacts extras
uv pip install -e ".[artifacts]"

# Or run with extras flag
uv run --extra artifacts examples/context_session_isolation_example.py
uv run --extra artifacts examples/context_user_persistence_example.py
```

## Related Documentation

- **chuk-mcp-server**: [Context API](../src/chuk_mcp_server/context.py)
- **chuk-artifacts**: [Namespace Architecture](../../chuk-artifacts/README.md)
- **chuk-sessions**: [Session Management](../../chuk-sessions/README.md)
- **chuk-mcp-vfs**: [VFS with Unified Architecture](../chuk-mcp-vfs/README.md)

## Real-World Integration

For a complete example of these patterns in action, see:
- **chuk-mcp-vfs**: Virtual filesystem server using unified namespace architecture
- **chuk-artifacts examples**: `09_mcp_server_integration.py` for tool patterns

## Common Patterns

### Pattern 1: Temporary Conversation Data
```python
# Use SESSION scope for ephemeral data
async with RequestContext(user_id="alice", session_id="conv-123"):
    temp_doc = await store.create_namespace(
        scope=StorageScope.SESSION,
        user_id=get_user_id(),
        session_id=get_session_id(),
    )
    # Data expires when session expires
```

### Pattern 2: Persistent User Projects
```python
# Use USER scope for persistent data
async with RequestContext(user_id="alice", session_id="conv-123"):
    project = await store.create_namespace(
        type=NamespaceType.WORKSPACE,
        name="my-project",
        scope=StorageScope.USER,
        user_id=get_user_id(),
    )
    # Accessible from ANY session for this user
```

### Pattern 3: User Preferences
```python
# Store and load user preferences
async with RequestContext(user_id="alice", session_id="conv-456"):
    # Save preferences (persists across sessions)
    prefs = await store.create_namespace(
        name="preferences",
        scope=StorageScope.USER,
        user_id=get_user_id(),
    )
    await store.write_namespace(prefs.namespace_id, data=json.dumps({
        "theme": "dark",
        "language": "en",
    }).encode())

    # Later, in different session
    async with RequestContext(user_id="alice", session_id="conv-789"):
        content = await store.read_namespace(prefs.namespace_id)
        prefs = json.loads(content.decode())  # Preferences loaded!
```

## Benefits

✅ **No Manual Parameter Passing**: Context automatically available
✅ **Automatic Isolation**: Sessions and users automatically isolated
✅ **Type-Safe**: Uses ContextVar for async-safe storage
✅ **Clean API**: Simple get/set/require functions
✅ **Flexible Scoping**: SESSION, USER, or SANDBOX as needed
✅ **Grid Architecture**: Clear, organized storage structure
✅ **Production Ready**: Used in chuk-mcp-vfs and other servers

---

**Questions?** Check the inline documentation in the example files or the main context.py module.
