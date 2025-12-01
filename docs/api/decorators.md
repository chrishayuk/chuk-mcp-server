# Decorators API

Complete API reference for ChukMCPServer decorators.

## @tool

Register a tool (action Claude can perform).

```python
@tool
def my_tool(param: str) -> dict:
    """Tool description."""
    return {"result": param}
```

**Parameters:**
- `name` (optional): Custom tool name

## @resource

Register a resource (read-only data).

```python
@resource("config://app")
def get_config() -> dict:
    """Resource description."""
    return {"version": "1.0.0"}
```

**Parameters:**
- `uri` (required): Resource URI

## @prompt

Register a prompt template.

```python
@prompt
def code_review(code: str) -> str:
    """Prompt description."""
    return f"Review this code:\n{code}"
```

## @requires_auth

Mark tool as requiring OAuth authentication.

```python
@tool
@requires_auth(scopes=["read", "write"])
async def protected_tool(_external_access_token: str | None = None):
    """Protected tool description."""
    # Use token...
```

**Parameters:**
- `scopes` (optional): Required OAuth scopes

## Next Steps

- [Server API](server.md) - ChukMCPServer class
- [OAuth API](oauth.md) - OAuth module
- [Types](types.md) - Type definitions
