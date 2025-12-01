# Tools

Tools are Python functions that Claude can call to perform actions.

## What is a Tool?

A tool is any Python function decorated with `@tool`:

```python
from chuk_mcp_server import tool

@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"
```

## Tool Components

1. **@tool decorator** - Registers the function
2. **Function name** - Becomes the tool name
3. **Parameters** - Define inputs
4. **Type hints** - Automatic validation
5. **Docstring** - Description for Claude
6. **Return value** - Result sent to Claude

## When to Use Tools

Use tools for:
- **Actions** - Things Claude can do (create, update, delete)
- **Queries** - Fetching data from APIs or databases
- **Computations** - Calculations or transformations
- **External integrations** - Calling third-party services

## Next Steps

- [Building Tools](../tools/basic.md) - Complete guide
- [Resources](resources.md) - For read-only data
- [Prompts](prompts.md) - For reusable templates
