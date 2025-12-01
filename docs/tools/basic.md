# Building Tools

Tools are the core of MCP - they're Python functions that Claude can call to perform actions. With ChukMCPServer, creating tools is as simple as adding a decorator.

## Your First Tool

The simplest tool is just a function with `@tool`:

```python
from chuk_mcp_server import tool, run

@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

run()
```

That's it! Claude can now call your `greet` tool.

## Tool Anatomy

Every tool has:

1. **Decorator**: `@tool` marks the function as a tool
2. **Function name**: Becomes the tool name (e.g., `greet`)
3. **Parameters**: Define what inputs the tool accepts
4. **Type hints**: Automatically validated
5. **Docstring**: Becomes the tool description (shown to Claude)
6. **Return value**: What Claude receives back

```python
@tool
def calculate_tip(bill: float, tip_percent: float = 15.0) -> dict:
    """
    Calculate tip amount and total bill.

    Args:
        bill: Total bill amount before tip
        tip_percent: Tip percentage (default: 15%)

    Returns:
        Dictionary with tip amount and total
    """
    tip = bill * (tip_percent / 100)
    total = bill + tip

    return {
        "bill": bill,
        "tip_percent": tip_percent,
        "tip_amount": round(tip, 2),
        "total": round(total, 2)
    }
```

## Type Validation

ChukMCPServer automatically validates all inputs based on type hints:

```python
@tool
def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

# Claude calls with: add_numbers(5, "hello")
# ❌ Automatic error: "Expected int, got str for parameter 'b'"
```

### Supported Types

| Type | Example | Validation |
|------|---------|------------|
| `int` | `42` | Must be integer |
| `float` | `3.14` | Must be number |
| `str` | `"hello"` | Must be string |
| `bool` | `True` | Must be boolean |
| `list` | `[1, 2, 3]` | Must be array |
| `dict` | `{"key": "value"}` | Must be object |
| `Optional[T]` | `None` or `T` | Can be null |
| `Union[A, B]` | `A` or `B` | Either type |

### Complex Types

```python
from typing import Optional, List, Dict

@tool
def process_data(
    items: List[str],
    options: Optional[Dict[str, Any]] = None,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """Process a list of items with options."""
    if options is None:
        options = {}

    return {
        "processed": len(items),
        "threshold": threshold,
        "options": options
    }
```

## Default Values

Provide sensible defaults for optional parameters:

```python
@tool
def search(
    query: str,
    limit: int = 10,
    sort_by: str = "relevance"
) -> list:
    """
    Search for items.

    Args:
        query: Search query (required)
        limit: Maximum results to return (default: 10)
        sort_by: Sort order (default: relevance)
    """
    # Implementation
    return [...]
```

Claude can call this as:
- `search("python")` - Uses defaults
- `search("python", 20)` - Custom limit
- `search("python", limit=5, sort_by="date")` - Named args

## Return Values

### Simple Returns

```python
@tool
def get_status() -> str:
    """Get system status."""
    return "All systems operational"
```

### Structured Returns

Better to return structured data:

```python
@tool
def get_status() -> dict:
    """Get detailed system status."""
    return {
        "status": "operational",
        "uptime": 12345,
        "load": 0.42,
        "services": {
            "database": "healthy",
            "cache": "healthy",
            "queue": "degraded"
        }
    }
```

### Lists

```python
@tool
def list_users() -> list:
    """Get all users."""
    return [
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "user"},
    ]
```

## Error Handling

### Raising Errors

```python
@tool
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

### Try-Except

```python
@tool
def fetch_user(user_id: int) -> dict:
    """Fetch user by ID."""
    try:
        # Database query
        user = database.get_user(user_id)
        if not user:
            return {
                "status": "not_found",
                "error": f"User {user_id} not found"
            }
        return {
            "status": "success",
            "user": user
        }
    except DatabaseError as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

### Custom Error Messages

```python
@tool
def update_settings(key: str, value: str) -> dict:
    """Update a setting."""
    valid_keys = ["theme", "language", "timezone"]

    if key not in valid_keys:
        raise ValueError(
            f"Invalid key '{key}'. Must be one of: {', '.join(valid_keys)}"
        )

    # Save setting
    return {"key": key, "value": value, "updated": True}
```

## Multiple Tools

Register multiple tools in one server:

```python
from chuk_mcp_server import tool, run

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@tool
def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

@tool
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

run()  # All 4 tools available
```

## Naming Conventions

### Tool Names

Tool names are automatically derived from function names:

```python
@tool
def get_user():  # Tool name: "get_user"
    ...

@tool
def calculateTax():  # Tool name: "calculateTax" (not recommended)
    ...
```

**Best practice**: Use `snake_case` for consistency:

```python
@tool
def calculate_tax():  # ✅ Good
    ...

@tool
def fetchUserData():  # ❌ Inconsistent
    ...
```

### Custom Tool Names

Override the auto-generated name:

```python
@tool(name="greet_user")
def complex_greeting_function(name: str) -> str:
    """Greet a user."""
    return f"Hello, {name}!"
```

## Documentation

### Docstrings

Write clear docstrings - Claude sees them:

```python
@tool
def search_products(
    query: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None
) -> list:
    """
    Search for products in the catalog.

    This tool searches the product database and returns matching items.
    You can filter by category and maximum price.

    Args:
        query: Search query (product name, description, or keywords)
        category: Optional category filter (e.g., "electronics", "books")
        max_price: Maximum price in USD (e.g., 99.99)

    Returns:
        List of matching products with name, price, and category

    Examples:
        - search_products("laptop") - Find all laptops
        - search_products("laptop", category="electronics", max_price=1000)
    """
    # Implementation
    ...
```

### Parameter Descriptions

Use clear, concise descriptions:

```python
@tool
def create_user(
    username: str,      # Short, unique username (3-20 chars)
    email: str,         # Valid email address
    role: str = "user"  # User role: "admin", "user", or "guest"
) -> dict:
    """Create a new user account."""
    ...
```

## Tool Organization

### Global API (Simple)

For quick scripts:

```python
from chuk_mcp_server import tool, run

@tool
def tool1():
    ...

@tool
def tool2():
    ...

run()
```

### Server-Based API (Recommended)

For larger applications:

```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer("my-app")

@mcp.tool
def tool1():
    ...

@mcp.tool
def tool2():
    ...

if __name__ == "__main__":
    mcp.run()
```

### Modular Organization

```python
# tools/math.py
def register_math_tools(mcp):
    @mcp.tool
    def add(a: int, b: int) -> int:
        return a + b

    @mcp.tool
    def multiply(a: int, b: int) -> int:
        return a * b

# tools/string.py
def register_string_tools(mcp):
    @mcp.tool
    def uppercase(text: str) -> str:
        return text.upper()

    @mcp.tool
    def reverse(text: str) -> str:
        return text[::-1]

# main.py
from chuk_mcp_server import ChukMCPServer
from tools.math import register_math_tools
from tools.string import register_string_tools

mcp = ChukMCPServer("my-app")

register_math_tools(mcp)
register_string_tools(mcp)

mcp.run()
```

## Best Practices

### 1. Single Responsibility

Each tool should do one thing well:

```python
# ❌ Bad: Tool does too much
@tool
def manage_user(action: str, user_id: int, data: dict) -> dict:
    if action == "create":
        ...
    elif action == "update":
        ...
    elif action == "delete":
        ...

# ✅ Good: Separate tools
@tool
def create_user(username: str, email: str) -> dict:
    ...

@tool
def update_user(user_id: int, data: dict) -> dict:
    ...

@tool
def delete_user(user_id: int) -> dict:
    ...
```

### 2. Descriptive Names

Use clear, action-oriented names:

```python
# ❌ Bad
@tool
def user(id: int):
    ...

# ✅ Good
@tool
def get_user(user_id: int):
    ...

@tool
def fetch_user_profile(user_id: int):
    ...
```

### 3. Type Everything

Always use type hints:

```python
# ❌ Bad
@tool
def process(data):
    ...

# ✅ Good
@tool
def process_data(data: dict) -> dict:
    ...
```

### 4. Handle Errors Gracefully

Return structured error information:

```python
@tool
def risky_operation(param: str) -> dict:
    """Perform a risky operation."""
    try:
        result = do_something_risky(param)
        return {
            "status": "success",
            "result": result
        }
    except SpecificError as e:
        return {
            "status": "error",
            "error_type": "specific_error",
            "message": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "unknown",
            "message": "An unexpected error occurred"
        }
```

### 5. Use Enums for Fixed Sets

```python
from enum import Enum

class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

@tool
def update_status(user_id: int, status: Status) -> dict:
    """Update user status."""
    # status is guaranteed to be valid
    return {"user_id": user_id, "status": status.value}
```

## Next Steps

- [Async Tools](async.md) - Handle async operations
- [Type Validation](types.md) - Advanced type system
- [Error Handling](errors.md) - Robust error handling
- [Testing Tools](testing.md) - Test your tools
- [Examples](../examples/calculator.md) - Real-world examples
