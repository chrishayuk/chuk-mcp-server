# Error Handling

Best practices for handling errors in MCP tools.

## Return Error Objects

Prefer returning error information over raising exceptions:

```python
@tool
def divide(a: float, b: float) -> dict:
    """Divide with error handling."""
    if b == 0:
        return {
            "status": "error",
            "error": "Cannot divide by zero"
        }

    return {
        "status": "success",
        "result": a / b
    }
```

## Try-Except Patterns

```python
@tool
def fetch_user(user_id: int) -> dict:
    """Fetch user with error handling."""
    try:
        user = database.get(user_id)
        if not user:
            return {"status": "not_found"}

        return {"status": "success", "user": user}
    except DatabaseError as e:
        return {"status": "error", "error": str(e)}
```

## Validation Errors

```python
@tool
def update_settings(key: str, value: str) -> dict:
    """Update setting with validation."""
    valid_keys = ["theme", "language"]

    if key not in valid_keys:
        return {
            "status": "error",
            "error": f"Invalid key. Must be one of: {', '.join(valid_keys)}"
        }

    # Update setting...
    return {"status": "success", "key": key, "value": value}
```

## Structured Errors

```python
from enum import Enum

class ErrorCode(str, Enum):
    NOT_FOUND = "not_found"
    INVALID_INPUT = "invalid_input"
    PERMISSION_DENIED = "permission_denied"

@tool
def get_resource(resource_id: str) -> dict:
    """Get resource with structured errors."""
    if not resource_id:
        return {
            "status": "error",
            "code": ErrorCode.INVALID_INPUT,
            "message": "Resource ID is required"
        }

    resource = find_resource(resource_id)
    if not resource:
        return {
            "status": "error",
            "code": ErrorCode.NOT_FOUND,
            "message": f"Resource {resource_id} not found"
        }

    return {"status": "success", "resource": resource}
```

## Next Steps

- [Basic Tools](basic.md) - Tool fundamentals
- [Testing](testing.md) - Test error cases
- [Examples](../examples/calculator.md) - Real examples
