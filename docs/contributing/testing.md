# Testing Guide

How to write and run tests for ChukMCPServer.

## Running Tests

```bash
# Run all tests
make test
# or
uv run pytest

# Run with coverage
make test-cov
# or
uv run pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_core.py -v

# Run specific test
pytest tests/test_core.py::test_function_name -v

# Run tests matching pattern
pytest -k "oauth" -v

# Run with debugging
pytest --pdb
```

## Test Structure

### Basic Test

```python
# tests/test_calculator.py
from chuk_mcp_server import ChukMCPServer

def test_add_tool():
    """Test that add tool works correctly."""
    mcp = ChukMCPServer(name="test-server")

    @mcp.tool
    def add(a: int, b: int) -> int:
        return a + b

    # Verify tool registered
    assert "add" in mcp._tool_handlers

    # Test execution
    handler = mcp._tool_handlers["add"]
    result = handler(a=2, b=3)
    assert result == 5
```

### Async Tests

```python
import pytest

class TestAsyncTools:
    """Test async tool functionality."""

    @pytest.mark.asyncio
    async def test_async_tool(self):
        """Test async tool execution."""
        mcp = ChukMCPServer(name="test-server")

        @mcp.tool
        async def async_add(a: int, b: int) -> int:
            return a + b

        handler = mcp._tool_handlers["async_add"]
        result = await handler(a=2, b=3)
        assert result == 5
```

## Fixtures

### Common Fixtures

```python
# tests/conftest.py
import pytest
from chuk_mcp_server import ChukMCPServer

@pytest.fixture
def mcp_server():
    """Create a test MCP server."""
    return ChukMCPServer(name="test-server")

@pytest.fixture
async def async_client():
    """Create async HTTP client."""
    import httpx
    async with httpx.AsyncClient() as client:
        yield client
```

### Using Fixtures

```python
def test_with_fixture(mcp_server):
    """Test using server fixture."""
    @mcp_server.tool
    def hello():
        return "world"

    assert "hello" in mcp_server._tool_handlers
```

## Mocking

### Mock External APIs

```python
from unittest.mock import patch, AsyncMock
import pytest

class TestExternalAPI:
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_fetch_data(self, mock_get):
        """Test API call with mock."""
        # Setup mock
        mock_response = AsyncMock()
        mock_response.json.return_value = {"temp": 72}
        mock_get.return_value = mock_response

        # Test
        from your_module import fetch_weather
        result = await fetch_weather("NYC")

        # Verify
        assert result["temp"] == 72
        mock_get.assert_called_once()
```

### Mock Environment Variables

```python
import os
from unittest.mock import patch

def test_env_var():
    """Test environment variable handling."""
    with patch.dict(os.environ, {"API_KEY": "test-key"}):
        from your_module import get_api_key
        assert get_api_key() == "test-key"
```

## Parametrized Tests

Test multiple inputs:

```python
import pytest

@pytest.mark.parametrize("a,b,expected", [
    (2, 3, 5),
    (-1, 1, 0),
    (0, 0, 0),
    (100, -50, 50),
])
def test_add_multiple(a, b, expected):
    """Test add with various inputs."""
    from calculator import add
    assert add(a, b) == expected
```

## Exception Testing

```python
import pytest

def test_divide_by_zero():
    """Test that divide by zero raises error."""
    from calculator import divide

    with pytest.raises(ZeroDivisionError):
        divide(1, 0)

def test_invalid_input():
    """Test invalid input handling."""
    from calculator import process

    with pytest.raises(ValueError, match="Expected positive number"):
        process(-1)
```

## Integration Tests

Test full server:

```python
import pytest
from httpx import AsyncClient
from chuk_mcp_server import ChukMCPServer

@pytest.mark.asyncio
async def test_full_server():
    """Test complete MCP server."""
    mcp = ChukMCPServer(name="test-server")

    @mcp.tool
    def add(a: int, b: int) -> int:
        return a + b

    # Start server in test mode
    async with AsyncClient(app=mcp.app, base_url="http://test") as client:
        # Test tool listing
        response = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert any(t["name"] == "add" for t in data["result"]["tools"])
```

## Coverage

### Check Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View in browser
open htmlcov/index.html
```

### Coverage Requirements

- Overall: 80% minimum
- New features: 90% minimum
- Critical paths: 100%

### Exclude from Coverage

```python
# tests/conftest.py
def some_helper():  # pragma: no cover
    """Helper only for manual testing."""
    pass
```

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_core.py             # Core functionality
├── test_types.py            # Type system
├── transport/
│   ├── test_http.py         # HTTP transport
│   └── test_stdio.py        # STDIO transport
├── oauth/
│   ├── test_middleware.py   # OAuth middleware
│   ├── test_helpers.py      # OAuth helpers
│   └── test_providers.py    # OAuth providers
└── integration/
    └── test_full_server.py  # Integration tests
```

## Performance Testing

```python
import time
import pytest

def test_performance():
    """Test that operation completes quickly."""
    start = time.perf_counter()

    # Operation
    result = expensive_operation()

    duration = time.perf_counter() - start
    assert duration < 0.1  # Must complete in 100ms
```

## Benchmarking

```bash
# Run benchmarks
python benchmarks/ultra_minimal_mcp_performance_test.py

# Custom benchmark
python benchmarks/quick_benchmark.py --duration 30
```

## Continuous Integration

Tests run automatically on:
- Every push
- Every pull request
- Main branch merges

See `.github/workflows/test.yml`

## Next Steps

- [Style Guide](style.md) - Code standards
- [Pull Requests](pull-requests.md) - Contributing workflow
- [Setup](setup.md) - Development setup
