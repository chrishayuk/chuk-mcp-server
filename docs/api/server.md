# ChukMCPServer API

Complete API reference for the ChukMCPServer class.

## Constructor

```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(name="my-server")
```

**Parameters:**
- `name` (str): Server name

## Methods

### tool()

Register a tool decorator.

```python
@mcp.tool
def my_tool():
    ...
```

### resource()

Register a resource decorator.

```python
@mcp.resource("uri://path")
def my_resource():
    ...
```

### prompt()

Register a prompt decorator.

```python
@mcp.prompt
def my_prompt():
    ...
```

### run()

Start the server.

```python
mcp.run(
    transport="http",  # "stdio" or "http"
    host="0.0.0.0",
    port=8000,
    workers=4,
    log_level="info",
    post_register_hook=setup_oauth
)
```

## Next Steps

- [Decorators](decorators.md) - Decorator API
- [OAuth API](oauth.md) - OAuth module
- [Examples](../examples/calculator.md) - Usage examples
