# Testing Tools

Test your MCP tools to ensure reliability.

## Basic Testing

```python
import pytest
from my_server import mcp

def test_add():
    """Test addition tool."""
    tool = mcp._tool_handlers["add"].func
    assert tool(5, 3) == 8
    assert tool(-5, 3) == -2
```

## Testing Async Tools

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_data():
    """Test async tool."""
    tool = mcp._tool_handlers["fetch_data"].func
    result = await tool("https://api.example.com/data")
    assert result["status"] == "success"
```

## Mocking External APIs

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_api_call():
    """Test tool with mocked API."""
    tool = mcp._tool_handlers["fetch_weather"].func
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"temp": 72}
        mock_get.return_value = mock_response
        
        result = await tool("San Francisco")
        assert result["temp"] == 72
```

## Testing Error Cases

```python
def test_divide_by_zero():
    """Test division by zero."""
    tool = mcp._tool_handlers["divide"].func
    result = tool(10, 0)
    assert result["status"] == "error"
    assert "zero" in result["error"].lower()
```

## Integration Tests

```python
import httpx

@pytest.mark.asyncio
async def test_server_integration():
    """Test full server integration."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "add",
                    "arguments": {"a": 5, "b": 3}
                }
            }
        )
        result = response.json()
        assert result["result"] == 8
```

## Next Steps

- [Basic Tools](basic.md) - Build tools
- [Error Handling](errors.md) - Handle errors
- [Examples](../examples/calculator.md) - Complete examples
