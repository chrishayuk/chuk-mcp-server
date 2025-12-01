# Resources

Resources provide read-only data that Claude can access.

## What is a Resource?

A resource exposes data or configuration:

```python
from chuk_mcp_server import resource

@resource("config://app")
def get_config() -> dict:
    """Application configuration."""
    return {
        "version": "1.0.0",
        "environment": "production"
    }
```

## Resource URIs

Resources are identified by URIs:

- `config://app` - Application config
- `data://users` - User data
- `file://README.md` - File content

## When to Use Resources

Use resources for:
- **Configuration** - App settings
- **Static data** - Lists, lookup tables
- **Documentation** - Help text
- **Templates** - Reusable content

## Tools vs Resources

| Feature | Tools | Resources |
|---------|-------|-----------|
| Purpose | Actions | Data |
| Read/Write | Both | Read-only |
| Parameters | Yes | No |
| URI | No | Yes |

## Next Steps

- [Tools](tools.md) - For actions
- [Prompts](prompts.md) - For templates
- [Building Tools](../tools/basic.md) - Complete guide
