# Example: Calculator Server

A complete calculator MCP server demonstrating basic tools, error handling, and testing.

## Overview

This example shows:
- Multiple related tools
- Type validation
- Error handling
- Testing
- Claude Desktop integration

## Complete Code

```python
from chuk_mcp_server import ChukMCPServer, tool

mcp = ChukMCPServer("calculator")

@mcp.tool
def add(a: float, b: float) -> float:
    """
    Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b

@mcp.tool
def subtract(a: float, b: float) -> float:
    """
    Subtract b from a.

    Args:
        a: Number to subtract from
        b: Number to subtract

    Returns:
        Difference of a and b
    """
    return a - b

@mcp.tool
def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of a and b
    """
    return a * b

@mcp.tool
def divide(a: float, b: float) -> dict:
    """
    Divide a by b with error handling.

    Args:
        a: Dividend
        b: Divisor

    Returns:
        Dictionary with result or error
    """
    if b == 0:
        return {
            "status": "error",
            "error": "Cannot divide by zero"
        }

    return {
        "status": "success",
        "result": a / b
    }

@mcp.tool
def power(base: float, exponent: float) -> float:
    """
    Raise base to the power of exponent.

    Args:
        base: Base number
        exponent: Exponent

    Returns:
        base^exponent
    """
    return base ** exponent

@mcp.tool
def square_root(n: float) -> dict:
    """
    Calculate square root of a number.

    Args:
        n: Number to calculate square root of

    Returns:
        Dictionary with result or error
    """
    if n < 0:
        return {
            "status": "error",
            "error": "Cannot calculate square root of negative number"
        }

    import math
    return {
        "status": "success",
        "result": math.sqrt(n)
    }

if __name__ == "__main__":
    mcp.run()
```

## Project Structure

```
calculator/
├── pyproject.toml
├── src/
│   └── calculator/
│       ├── __init__.py
│       └── server.py
├── tests/
│   └── test_calculator.py
└── README.md
```

## Testing

Create `tests/test_calculator.py`:

```python
import pytest
from calculator.server import mcp

def test_add():
    """Test addition."""
    tool = mcp._tool_handlers["add"].func
    assert tool(5, 3) == 8
    assert tool(-5, 3) == -2
    assert tool(0.1, 0.2) == pytest.approx(0.3)

def test_subtract():
    """Test subtraction."""
    tool = mcp._tool_handlers["subtract"].func
    assert tool(5, 3) == 2
    assert tool(3, 5) == -2

def test_multiply():
    """Test multiplication."""
    tool = mcp._tool_handlers["multiply"].func
    assert tool(5, 3) == 15
    assert tool(-5, 3) == -15
    assert tool(0, 100) == 0

def test_divide():
    """Test division."""
    tool = mcp._tool_handlers["divide"].func

    # Normal division
    result = tool(10, 2)
    assert result["status"] == "success"
    assert result["result"] == 5

    # Division by zero
    result = tool(10, 0)
    assert result["status"] == "error"
    assert "zero" in result["error"].lower()

def test_power():
    """Test power function."""
    tool = mcp._tool_handlers["power"].func
    assert tool(2, 3) == 8
    assert tool(5, 2) == 25
    assert tool(10, 0) == 1

def test_square_root():
    """Test square root."""
    tool = mcp._tool_handlers["square_root"].func

    # Valid input
    result = tool(9)
    assert result["status"] == "success"
    assert result["result"] == 3

    # Negative input
    result = tool(-9)
    assert result["status"] == "error"
    assert "negative" in result["error"].lower()
```

Run tests:

```bash
pytest tests/
```

## Claude Desktop Integration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "calculator": {
      "command": "uv",
      "args": ["run", "calculator"]
    }
  }
}
```

Restart Claude Desktop, then try:

> "Can you calculate 15 * 7 + 3?"

Claude will use your calculator tools!

## HTTP Mode

For testing in browser or with curl:

```python
if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
```

Test with curl:

```bash
# Add numbers
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "add",
      "arguments": {"a": 5, "b": 3}
    }
  }'

# Divide (with error handling)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "divide",
      "arguments": {"a": 10, "b": 0}
    }
  }'
```

## Enhancements

### Add Memory

```python
from typing import Dict, List

class Calculator:
    def __init__(self):
        self.history: List[Dict] = []

    def record(self, operation: str, a: float, b: float, result: float):
        self.history.append({
            "operation": operation,
            "a": a,
            "b": b,
            "result": result
        })

calc = Calculator()

@mcp.tool
def add_with_history(a: float, b: float) -> dict:
    """Add two numbers and record in history."""
    result = a + b
    calc.record("add", a, b, result)
    return {
        "result": result,
        "history_length": len(calc.history)
    }

@mcp.tool
def get_history() -> list:
    """Get calculation history."""
    return calc.history
```

### Add Advanced Functions

```python
import math

@mcp.tool
def factorial(n: int) -> dict:
    """Calculate factorial of n."""
    if n < 0:
        return {"status": "error", "error": "Factorial of negative number"}
    if n > 100:
        return {"status": "error", "error": "Number too large"}

    result = math.factorial(n)
    return {"status": "success", "result": result}

@mcp.tool
def sin(x: float) -> float:
    """Calculate sine of x (in radians)."""
    return math.sin(x)

@mcp.tool
def cos(x: float) -> float:
    """Calculate cosine of x (in radians)."""
    return math.cos(x)
```

## Key Learnings

1. **Type hints are validated automatically** - No manual checking needed
2. **Error handling via return values** - Better than exceptions for Claude
3. **Clear docstrings help Claude** - Write for LLM consumption
4. **Testing is straightforward** - Access tool functions directly
5. **Both STDIO and HTTP work** - Same code, different transports

## Next Steps

- [Weather Server Example](weather.md) - Async tools with external APIs
- [Database Example](database.md) - CRUD operations
- [OAuth Example](oauth.md) - Authenticated tools
- [Building Tools Guide](../tools/basic.md) - Comprehensive tool documentation
