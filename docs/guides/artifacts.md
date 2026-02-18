# Artifact & Workspace Storage

ChukMCPServer integrates with the **[chuk-artifacts](https://github.com/chuk-ai/chuk-artifacts)** package to provide unified artifact and workspace storage for your MCP tools. This allows you to store blobs, manage workspaces with virtual filesystems, and handle file operations across different storage backends.

## Overview

**chuk-artifacts** provides:
- **Blob Storage**: Store binary data (files, images, documents)
- **Workspace VFS**: Virtual filesystems for project-like structures
- **Multiple Backends**: Memory, filesystem, S3, SQLite
- **Scoped Storage**: Session, user, global, or sandbox scopes

## Installation

The artifact functionality is optional and requires the `chuk-artifacts` package:

```bash
# Install with artifact support
pip install 'chuk-mcp-server[artifacts]'

# Or install separately
pip install chuk-mcp-server chuk-artifacts
```

## Quick Start

### Basic Blob Storage

```python
from chuk_mcp_server import tool, set_artifact_store, get_artifact_store
from chuk_artifacts import ArtifactStore, NamespaceType, StorageScope

# Initialize the artifact store (do this once at startup)
store = ArtifactStore()
set_artifact_store(store)

@tool
async def store_file(filename: str, content: bytes) -> str:
    """Store a file as a blob artifact."""
    store = get_artifact_store()

    # Create a blob namespace
    ns = await store.create_namespace(
        type=NamespaceType.BLOB,
        scope=StorageScope.SESSION
    )

    # Write the blob data
    await store.write_namespace(ns.namespace_id, data=content)

    return f"Stored {filename} with ID: {ns.namespace_id}"
```

### Workspace with VFS

```python
@tool
async def create_workspace(project_name: str) -> str:
    """Create a workspace with a virtual filesystem."""
    store = get_artifact_store()

    # Create a workspace namespace
    ns = await store.create_namespace(
        name=project_name,
        type=NamespaceType.WORKSPACE,
        scope=StorageScope.SESSION,
        provider_type="vfs-memory"  # or vfs-filesystem, vfs-s3, vfs-sqlite
    )

    # Get the VFS for file operations
    vfs = store.get_namespace_vfs(ns.namespace_id)
    await vfs.write_file("/README.md", b"# My Project\n")
    await vfs.write_file("/src/main.py", b"print('hello')")

    return f"Created workspace: {ns.namespace_id}"
```

## Convenience Functions

ChukMCPServer provides convenience functions for common artifact operations:

```python
from chuk_mcp_server import (
    # Namespace creation
    create_blob_namespace,
    create_workspace_namespace,

    # Blob operations
    write_blob,
    read_blob,

    # Workspace file operations
    write_workspace_file,
    read_workspace_file,

    # VFS access
    get_namespace_vfs,
)
```

### Blob Example

```python
from chuk_artifacts import StorageScope

@tool
async def quick_blob_example(data: bytes) -> str:
    """Store a blob using convenience functions."""
    # Create blob namespace
    ns = await create_blob_namespace(scope=StorageScope.SESSION)

    # Write blob data
    await write_blob(ns.namespace_id, data, mime="application/octet-stream")

    # Read it back
    retrieved = await read_blob(ns.namespace_id)

    return f"Stored and retrieved {len(retrieved)} bytes"
```

### Workspace Example

```python
@tool
async def quick_workspace_example(project_name: str) -> str:
    """Create a workspace using convenience functions."""
    # Create workspace
    ws = await create_workspace_namespace(
        name=project_name,
        scope=StorageScope.SESSION,
        provider_type="vfs-memory"
    )

    # Write files
    await write_workspace_file(ws.namespace_id, "/main.py", b"print('hello')")
    await write_workspace_file(ws.namespace_id, "/README.md", b"# Project\n")

    # Read files
    code = await read_workspace_file(ws.namespace_id, "/main.py")

    # Or use VFS directly for advanced operations
    vfs = get_namespace_vfs(ws.namespace_id)
    files = await vfs.list_directory("/")

    return f"Workspace {project_name} created with {len(files)} files"
```

## Storage Scopes

Artifacts can have different storage scopes:

| Scope | Description | Use Case |
|-------|-------------|----------|
| `StorageScope.SESSION` | Scoped to the current MCP session (default) | Temporary data for current session |
| `StorageScope.USER` | Scoped to the authenticated user | User-specific persistent data |
| `StorageScope.GLOBAL` | Globally accessible | Shared data (use with caution) |
| `StorageScope.SANDBOX` | Isolated sandbox | Testing and isolation |

### Example with User Scope

```python
from chuk_mcp_server import tool, require_user_id
from chuk_artifacts import StorageScope

@tool
async def save_user_file(filename: str, content: bytes) -> str:
    """Save a file to the user's personal storage."""
    # Ensure user is authenticated
    user_id = require_user_id()

    # Create user-scoped workspace
    ws = await create_workspace_namespace(
        name=f"user-{user_id}-files",
        scope=StorageScope.USER,
        user_id=user_id
    )

    # Store file
    await write_workspace_file(ws.namespace_id, f"/{filename}", content)

    return f"Saved {filename} to your personal storage"
```

## Storage Backends

The `chuk-artifacts` package supports multiple storage backends:

| Backend | Description | Use Case |
|---------|-------------|----------|
| `vfs-memory` | In-memory storage | Fast, ephemeral data |
| `vfs-filesystem` | Local filesystem | Persistent local storage |
| `vfs-s3` | AWS S3 storage | Cloud storage (requires `boto3`) |
| `vfs-sqlite` | SQLite-backed | Embedded database storage |

### Example: Filesystem Backend

```python
# Create workspace with filesystem backend
ws = await create_workspace_namespace(
    name="my-project",
    provider_type="vfs-filesystem",
    provider_config={"base_path": "/tmp/workspaces"}
)
```

### Example: S3 Backend

```python
# Create workspace with S3 backend
ws = await create_workspace_namespace(
    name="cloud-project",
    provider_type="vfs-s3",
    provider_config={
        "bucket": "my-bucket",
        "prefix": "workspaces/"
    }
)
```

## API Reference

### Store Management

| Function | Purpose | Returns |
|----------|---------|---------|
| `get_artifact_store()` | Get the current artifact store | `ArtifactStore` (raises error if not set) |
| `set_artifact_store(store)` | Set artifact store for current context | None |
| `set_global_artifact_store(store)` | Set global fallback store | None |
| `has_artifact_store()` | Check if store is available | `bool` |
| `clear_artifact_store()` | Clear store (useful for testing) | None |

### Namespace Operations

| Function | Purpose | Returns |
|----------|---------|---------|
| `create_blob_namespace(**kwargs)` | Create blob namespace | `NamespaceInfo` |
| `create_workspace_namespace(name, **kwargs)` | Create workspace namespace | `NamespaceInfo` |

### Blob Operations

| Function | Purpose | Returns |
|----------|---------|---------|
| `write_blob(namespace_id, data, mime)` | Write blob data | None |
| `read_blob(namespace_id)` | Read blob data | `bytes` |

### Workspace Operations

| Function | Purpose | Returns |
|----------|---------|---------|
| `write_workspace_file(namespace_id, path, data)` | Write file to workspace | None |
| `read_workspace_file(namespace_id, path)` | Read file from workspace | `bytes` |
| `get_namespace_vfs(namespace_id)` | Get VFS for workspace | `AsyncVirtualFileSystem` |

## Advanced Usage

### VFS Operations

When you need more control, use the VFS directly:

```python
vfs = get_namespace_vfs(workspace_id)

# List files
files = await vfs.list_directory("/")

# Check if file exists
exists = await vfs.exists("/path/to/file")

# Create directory
await vfs.create_directory("/new/path")

# Delete file
await vfs.delete_file("/old/file")

# Read file metadata
info = await vfs.get_file_info("/file")
```

### Testing with Artifacts

```python
import pytest
from chuk_mcp_server import set_artifact_store, clear_artifact_store
from chuk_artifacts import ArtifactStore

@pytest.fixture
def artifact_store():
    """Provide a clean artifact store for each test."""
    store = ArtifactStore()
    set_artifact_store(store)
    yield store
    clear_artifact_store()

async def test_workspace_creation(artifact_store):
    """Test workspace creation."""
    ws = await create_workspace_namespace(
        name="test-workspace",
        scope=StorageScope.SANDBOX
    )

    assert ws.name == "test-workspace"
    assert ws.type == NamespaceType.WORKSPACE
```

## Best Practices

1. **Initialize Once**: Set up the artifact store once at application startup
2. **Use Scopes Wisely**: Choose appropriate scopes for your data
   - SESSION for temporary data
   - USER for personal data
   - GLOBAL sparingly and with proper access control
3. **Clean Up**: Clear artifacts when sessions end (if using SESSION scope)
4. **Choose Right Backend**:
   - Memory for ephemeral/test data
   - Filesystem for local development
   - S3 for cloud deployments
5. **Handle Errors**: Always handle potential errors from storage operations

## Related Documentation

- [chuk-artifacts Documentation](https://github.com/chuk-ai/chuk-artifacts) - Full artifact package docs
- [Context Management](./context-management.md) - Working with request context
- [OAuth Integration](../OAUTH.md) - Setting up user authentication
- [API Reference](./api-reference.md) - Complete API documentation
