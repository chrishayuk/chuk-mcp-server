# Type Validation

ChukMCPServer automatically validates all tool inputs based on Python type hints.

## Supported Types

| Type | Example | Validation |
|------|---------|------------|
| `int` | `42` | Must be integer |
| `float` | `3.14` | Must be number |
| `str` | `"hello"` | Must be string |
| `bool` | `True` | Must be boolean |
| `list` | `[1, 2, 3]` | Must be array |
| `dict` | `{"key": "value"}` | Must be object |

## Optional Parameters

```python
from typing import Optional

@tool
def greet(name: str, title: Optional[str] = None) -> str:
    """Greet with optional title."""
    if title:
        return f"Hello, {title} {name}"
    return f"Hello, {name}"
```

## Union Types

```python
from typing import Union

@tool
def process(value: Union[int, str]) -> str:
    """Process int or string."""
    return str(value)
```

## Complex Types

```python
from typing import List, Dict, Any

@tool
def analyze(
    items: List[str],
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze items with options."""
    return {
        "count": len(items),
        "options": options
    }
```

## Validation Errors

Invalid types are rejected automatically:

```python
@tool
def add(a: int, b: int) -> int:
    return a + b

# Claude calls: add(5, "hello")
# Error: Expected int for parameter 'b', got str
```

## Next Steps

- [Basic Tools](basic.md) - Tool fundamentals
- [Error Handling](errors.md) - Handle errors
- [Testing](testing.md) - Test your tools
