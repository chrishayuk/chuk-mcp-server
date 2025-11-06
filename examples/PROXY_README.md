# ChukMCPServer Proxy Mode

ChukMCPServer can act as a proxy/gateway to multiple backend MCP servers, exposing their tools under a unified namespace. This enables you to:

- **Aggregate multiple MCP servers** into a single endpoint
- **Namespace tools** to avoid naming conflicts (e.g., `proxy.time.get_current_time`)
- **Combine local and remote tools** in one server
- **Create service gateways** for complex MCP architectures

## Quick Start

### 1. Basic Proxy Configuration

```python
from chuk_mcp_server import ChukMCPServer

# Define proxy configuration
proxy_config = {
    "proxy": {
        "enabled": True,
        "namespace": "proxy",  # All proxied tools under proxy.*
    },
    "servers": {
        "time": {
            "type": "stdio",
            "command": "uvx",
            "args": ["mcp-server-time"],
        },
    },
}

# Create server with proxy
mcp = ChukMCPServer(proxy_config=proxy_config)
mcp.run()
```

### 2. Multiple Servers

```python
proxy_config = {
    "proxy": {"enabled": True, "namespace": "proxy"},
    "servers": {
        "time": {
            "type": "stdio",
            "command": "uvx",
            "args": ["mcp-server-time"],
        },
        "weather": {
            "type": "stdio",
            "command": "python",
            "args": ["-m", "weather_server"],
        },
        "database": {
            "type": "stdio",
            "command": "node",
            "args": ["db-mcp-server.js"],
        },
    },
}
```

### 3. With Local Tools

You can combine proxied and local tools:

```python
mcp = ChukMCPServer(proxy_config=proxy_config)

# Local tool
@mcp.tool
def local_status() -> dict:
    """Check proxy status."""
    return mcp.get_proxy_stats()

# Proxied tools are automatically available as:
# - proxy.time.get_current_time
# - proxy.weather.get_forecast
# - etc.
```

## Configuration Reference

### Proxy Configuration

```yaml
proxy:
  enabled: true           # Enable proxy mode
  namespace: "proxy"      # Namespace prefix (default: "proxy")
```

### Server Configuration (stdio)

```yaml
servers:
  server_name:
    type: stdio                    # Transport type (currently only stdio)
    command: "python"              # Executable command
    args: ["-m", "my_server"]      # Command arguments
    cwd: "/path/to/workdir"        # Optional working directory
```

## Tool Naming

All proxied tools are exposed with the following naming pattern:

```
{namespace}.{server_name}.{tool_name}
```

Examples:
- `proxy.time.get_current_time`
- `proxy.weather.get_forecast`
- `proxy.database.query`

## Examples

See the example files in this directory:

- **`proxy_example.py`** - Basic proxy setup
- **`proxy_time_example.py`** - Proxy with mcp-server-time
- **`proxy_multi_server_example.py`** - Multiple servers with local tools
- **`proxy_config_example.yaml`** - YAML configuration format

## Running Examples

```bash
# Install prerequisite (optional time server)
pip install mcp-server-time

# Run basic example
python examples/proxy_example.py

# Run time server proxy
python examples/proxy_time_example.py

# Run multi-server proxy
python examples/proxy_multi_server_example.py
```

## Testing with MCP Inspector

1. Start your proxy server:
   ```bash
   python examples/proxy_time_example.py
   ```

2. Open MCP Inspector

3. Connect to: `http://localhost:8000/mcp`

4. You should see all proxied tools with their namespaced names

5. Call tools normally - the proxy handles routing

## Proxy Management API

ChukMCPServer provides methods to manage the proxy:

```python
# Get proxy statistics
stats = mcp.get_proxy_stats()
# Returns: {"enabled": True, "namespace": "proxy", "servers": 2, "tools": 5}

# Call a proxied tool programmatically
result = await mcp.call_proxied_tool("proxy.time.get_current_time", timezone="UTC")

# Enable proxy dynamically
mcp.enable_proxy(proxy_config)
```

## Architecture

```
┌─────────────────────────────────┐
│   ChukMCPServer (Proxy Mode)    │
│                                 │
│  ┌─────────────────────────┐   │
│  │  Local Tools            │   │
│  │  - local_tool_1         │   │
│  │  - local_tool_2         │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │  Proxy Manager          │   │
│  │                         │   │
│  │  ┌─────────────────┐   │   │
│  │  │ Server: time     │◄──┼───┼── stdio → mcp-server-time
│  │  │ - get_current.. │   │   │
│  │  └─────────────────┘   │   │
│  │                         │   │
│  │  ┌─────────────────┐   │   │
│  │  │ Server: weather  │◄──┼───┼── stdio → weather_server
│  │  │ - get_forecast  │   │   │
│  │  └─────────────────┘   │   │
│  └─────────────────────────┘   │
│                                 │
│  HTTP/STDIO Transport           │
└─────────────────────────────────┘
         │
         ▼
    MCP Clients
```

## Supported Transports

Currently supported:
- **stdio** - Standard input/output (subprocess communication)

Coming soon:
- **HTTP** - Direct HTTP connections to remote MCP servers
- **SSE** - Server-Sent Events transport

## Limitations

- Currently only stdio transport is supported for backend servers
- Backend servers must support the MCP protocol
- Tool name collisions are prevented by namespacing
- Async tool execution is required

## Comparison with chuk-mcp-runtime

This proxy implementation is inspired by chuk-mcp-runtime but designed to be:

- **Simpler** - Fewer configuration options, focused on common use cases
- **Integrated** - Built directly into ChukMCPServer
- **Zero-config friendly** - Works with ChukMCPServer's smart defaults
- **Extensible** - Easy to add local tools alongside proxied ones

For production deployments with advanced features (sessions, artifacts, JWT auth), consider using chuk-mcp-runtime.

## Next Steps

- Add HTTP/SSE transport support for backend servers
- Add tool filtering and renaming options
- Add health checking for backend servers
- Add automatic reconnection on failure
- Add request/response caching

## Contributing

Contributions are welcome! See the main repository README for guidelines.
