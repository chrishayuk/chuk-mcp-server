# Style Guide

Code standards and conventions for ChukMCPServer.

## Code Quality Tools

All code must pass:

```bash
make check  # Runs all checks
```

This runs:
1. **ruff** - Linting and formatting
2. **mypy** - Type checking
3. **pytest** - Tests with 80%+ coverage

## Python Style

### Type Hints

All code must have complete type annotations:

```python
# ✅ Good
def add(a: int, b: int) -> int:
    return a + b

async def fetch(url: str) -> dict[str, Any]:
    ...

# ❌ Bad
def add(a, b):
    return a + b
```

### Formatting

Use ruff format (black-compatible):

```bash
make format
# or
uv run ruff format .
```

Standards:
- Line length: 88 characters
- Indent: 4 spaces
- Quotes: Double quotes preferred
- Trailing commas: Yes for multi-line

### Imports

Organized automatically by ruff:

```python
# Standard library
import os
import sys
from typing import Any, Optional

# Third-party
import httpx
from starlette.responses import JSONResponse

# Local
from chuk_mcp_server import ChukMCPServer
from chuk_mcp_server.types import ToolHandler
```

### Naming Conventions

```python
# Functions and variables: snake_case
def process_request():
    user_count = 0

# Classes: PascalCase
class OAuthProvider:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_CONNECTIONS = 1000

# Private: leading underscore
def _internal_helper():
    pass

class MyClass:
    def __init__(self):
        self._private_attr = None
```

## Documentation

### Docstrings

Use Google style:

```python
def complex_function(param1: str, param2: int) -> dict[str, Any]:
    """One-line summary.

    Longer description if needed. Can span multiple lines
    and include examples.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Dictionary containing results with keys:
        - "status": Operation status
        - "data": Result data

    Raises:
        ValueError: If param2 is negative
        RuntimeError: If operation fails

    Example:
        >>> result = complex_function("test", 42)
        >>> result["status"]
        "success"
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")

    return {"status": "success", "data": param1 * param2}
```

### Comments

Write clear, helpful comments:

```python
# ✅ Good: Explains why
# Use orjson for 2-3x faster serialization
import orjson

# ✅ Good: Complex logic
# Binary search requires sorted input; sort once and cache
sorted_items = sorted(items)

# ❌ Bad: States the obvious
# Increment counter
counter += 1
```

## Testing Standards

### Test Organization

```python
# tests/test_feature.py
import pytest
from chuk_mcp_server import ChukMCPServer

class TestFeature:
    """Test suite for feature."""

    def test_basic_case(self):
        """Test basic functionality."""
        assert True

    def test_edge_case(self):
        """Test edge cases."""
        assert True

    @pytest.mark.asyncio
    async def test_async_case(self):
        """Test async functionality."""
        assert True
```

### Test Naming

```python
# Pattern: test_<what>_<condition>_<expected>

def test_add_positive_numbers_returns_sum():
    assert add(2, 3) == 5

def test_add_negative_numbers_returns_sum():
    assert add(-2, -3) == -5

def test_divide_by_zero_raises_error():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)
```

### Coverage Requirements

- Minimum 80% overall coverage
- New code should have 90%+ coverage
- Critical paths must be 100% covered

```bash
# Check coverage
make test-cov

# View HTML report
open htmlcov/index.html
```

## Git Conventions

### Commit Messages

Follow conventional commits:

```
type(scope): Short description

Longer description if needed.

- Bullet points for details
- Multiple changes listed

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `chore`: Maintenance

Examples:

```
feat(oauth): Add Google Drive OAuth provider

Implements OAuth 2.1 with PKCE for Google Drive integration.

- Automatic token refresh
- Secure token storage
- Drive API scopes

Fixes #42
```

```
fix(transport): Handle SSE connection drops

Gracefully reconnect when SSE connection is interrupted.

Fixes #56
```

### Branch Names

```
feature/oauth-google-drive
fix/sse-connection-drops
docs/update-quickstart
test/oauth-providers
refactor/type-system
```

## Error Handling

### Explicit is Better

```python
# ✅ Good: Specific exceptions
def process_file(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    if not path.endswith('.json'):
        raise ValueError(f"Expected JSON file, got: {path}")

    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

# ❌ Bad: Catch-all
def process_file(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}
```

## Performance

### Async First

```python
# ✅ Good: Async I/O
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# ❌ Bad: Blocking I/O
def fetch_data(url: str) -> dict:
    import requests
    return requests.get(url).json()
```

### Type Annotations

Help mypy optimize:

```python
# ✅ Good: Specific types
def process(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# ❌ Bad: Generic types
def process(items: list) -> dict:
    return {item: len(item) for item in items}
```

## Next Steps

- [Testing](testing.md) - Testing guide
- [Pull Requests](pull-requests.md) - Contributing workflow
- [Setup](setup.md) - Development setup
