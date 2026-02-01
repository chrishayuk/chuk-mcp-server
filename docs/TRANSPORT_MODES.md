# ChukMCPServer Transport Modes

ChukMCPServer supports two transport modes for the Model Context Protocol (MCP):

## 1. STDIO Transport (Process-based)

For direct integration with MCP clients like Claude Desktop via standard input/output streams.

### Quick Start
```bash
# Install and run with uvx (recommended)
uvx chuk-mcp-server stdio

# Or with environment variable
MCP_STDIO=1 uvx chuk-mcp-server auto
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "chuk-mcp": {
      "command": "uvx",
      "args": ["chuk-mcp-server", "stdio"]
    }
  }
}
```

### Features
- Lowest latency communication
- Direct process integration
- JSON-RPC over stdin/stdout
- Clean separation (logs to stderr, data to stdout)

## 2. HTTP Transport with SSE Streaming

For network-based communication with support for multiple concurrent clients.

### Quick Start
```bash
# Run on default port (8000)
uvx chuk-mcp-server http

# Run on custom port
uvx chuk-mcp-server http --port 9000
```

### Client Configuration
```json
{
  "mcpServers": {
    "chuk-http": {
      "url": "http://localhost:8000/mcp",
      "transport": "http",
      "streaming": true
    }
  }
}
```

### Features
- Server-Sent Events (SSE) for real-time streaming
- Multiple concurrent connections
- REST API endpoints
- Web-based MCP Inspector compatibility
- High performance (39,000+ RPS)

## Auto-Detection Mode

The server can automatically detect the appropriate transport:

```bash
# Auto-detect from environment
uvx chuk-mcp-server auto
```

Detection priority:
1. Environment variables (`MCP_TRANSPORT`, `MCP_STDIO`, `USE_STDIO`)
2. Piped I/O detection (requires explicit env var)
3. Default to HTTP mode

## Comparison

| Feature | STDIO | HTTP + SSE |
|---------|-------|------------|
| Latency | Lowest | Low |
| Concurrent Clients | Single | Multiple |
| Network Access | No | Yes |
| Process Integration | Direct | Remote |
| Debugging | Via stderr | Via browser/tools |
| Best For | Claude Desktop | Web clients, APIs |

## Protocol Support

Both transports support the full MCP protocol:
- `initialize` - Session initialization
- `tools/list` - List available tools
- `tools/call` - Execute tools
- `resources/list` - List resources
- `resources/read` - Read resource content
- `prompts/list` - List prompts
- `prompts/get` - Get prompt details
- Notifications and subscriptions

## Examples

### Custom Server with Both Modes

```python
from chuk_mcp_server import ChukMCPServer
import sys

mcp = ChukMCPServer(name="my-server")

@mcp.tool
def my_tool(input: str) -> str:
    return f"Processed: {input}"

# Run based on command line argument
if len(sys.argv) > 1 and sys.argv[1] == "stdio":
    mcp.run(stdio=True)
else:
    mcp.run()  # HTTP mode
```

### Testing

```bash
# Test STDIO mode
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | \
  uvx chuk-mcp-server stdio 2>/dev/null | jq .

# Test HTTP mode
uvx chuk-mcp-server http --port 8000 &
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## Environment Variables

- `MCP_TRANSPORT`: Force transport mode (`stdio` or `http`)
- `MCP_STDIO`: Set to `1` to enable stdio mode
- `USE_STDIO`: Alternative to `MCP_STDIO`
- `MCP_SERVER_NAME`: Custom server name
- `MCP_SERVER_VERSION`: Custom server version

## Performance Tuning

### STDIO Mode
- Minimal overhead
- Direct process communication
- Best for single-client scenarios

### HTTP Mode
```bash
# High-performance settings
MCP_PERFORMANCE_MODE=high_performance \
MCP_WORKERS=8 \
MCP_MAX_CONNECTIONS=10000 \
uvx chuk-mcp-server http
```

## Troubleshooting

### STDIO Issues
- Ensure logs go to stderr: `logging.basicConfig(stream=sys.stderr)`
- Check JSON formatting: Messages must end with newline
- Verify environment variables are set

### HTTP Issues
- Check port availability: `lsof -i :8000`
- Verify CORS headers for browser clients
- Monitor SSE connections for timeouts

## Migration Guide

Existing HTTP-only servers automatically support STDIO with no code changes:
1. Update to latest version: `pip install -U chuk-mcp-server`
2. Use CLI or set environment variables
3. Both modes work with the same tool/resource definitions
