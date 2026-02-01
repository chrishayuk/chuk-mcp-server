# STDIO Transport Support

ChukMCPServer now supports both HTTP streaming and STDIO transport modes for the Model Context Protocol (MCP).

## Overview

The server can operate in two transport modes:
- **HTTP Mode** (default): Server-based communication with SSE streaming support
- **STDIO Mode**: Process-based communication via standard input/output

## Using STDIO Mode

### 1. Explicit Configuration

```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(name="my-server")

@mcp.tool
def hello(name: str) -> str:
    return f"Hello, {name}!"

# Run in stdio mode explicitly
mcp.run(stdio=True)
```

### 2. Environment Variables

```bash
# Using MCP_TRANSPORT
MCP_TRANSPORT=stdio python my_server.py

# Using MCP_STDIO flag
MCP_STDIO=1 python my_server.py

# Using USE_STDIO flag
USE_STDIO=1 python my_server.py
```

### 3. Auto-Detection

The server automatically detects stdio mode when:
- Input/output is piped or redirected
- Running in a non-interactive environment (with explicit env vars)

```bash
# Pipe mode (requires MCP_STDIO=1 to enable auto-detection)
echo '{"jsonrpc":"2.0","method":"initialize","params":{"clientInfo":{"name":"test"}},"id":1}' | MCP_STDIO=1 python my_server.py
```

## Protocol Communication

### Initialize Session

```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "clientInfo": {
      "name": "my-client",
      "version": "1.0.0"
    },
    "protocolVersion": "2025-03-26"
  },
  "id": 1
}
```

### Call a Tool

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "hello",
    "arguments": {
      "name": "World"
    }
  },
  "id": 2
}
```

### List Available Tools

```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 3
}
```

## Example Server

```python
#!/usr/bin/env python3
"""
MCP server with stdio transport support.
"""

import argparse
import logging
import sys

from chuk_mcp_server import ChukMCPServer

# Configure logging to stderr to keep stdout clean
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdio", action="store_true", help="Run in stdio mode")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP mode")
    args = parser.parse_args()

    # Create server
    mcp = ChukMCPServer(name="example-server")

    # Register tools
    @mcp.tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @mcp.tool
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b

    # Register resources
    @mcp.resource("example://data")
    def get_data() -> str:
        """Get example data."""
        return "Example data content"

    # Run server
    if args.stdio:
        print("Starting in stdio mode...", file=sys.stderr)
        mcp.run(stdio=True)
    else:
        print(f"Starting in HTTP mode on port {args.port}...", file=sys.stderr)
        mcp.run(port=args.port, stdio=False)

if __name__ == "__main__":
    main()
```

## Testing STDIO Mode

### Using a Test Client

```python
import subprocess
import json

# Start the server in stdio mode
proc = subprocess.Popen(
    ["python", "server.py", "--stdio"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Initialize
request = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "clientInfo": {"name": "test-client"}
    },
    "id": 1
}

proc.stdin.write(json.dumps(request) + "\n")
proc.stdin.flush()

# Read response
response = proc.stdout.readline()
print(json.loads(response))
```

### Manual Testing

```bash
# Start server in stdio mode
MCP_STDIO=1 python server.py

# In another terminal, send requests
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | nc localhost <stdin_pipe>
```

## Configuration Detection

The smart configuration system automatically detects the appropriate transport mode:

1. **Explicit Environment Variables** (highest priority)
   - `MCP_TRANSPORT=stdio`
   - `MCP_STDIO=1`
   - `USE_STDIO=1`

2. **Auto-detection** (requires explicit env var)
   - Piped input/output
   - Non-TTY environments

3. **Default** (lowest priority)
   - HTTP mode with SSE streaming

## Implementation Details

### Architecture

- **StdioTransport**: Handles async I/O for stdin/stdout communication
- **MCPProtocolHandler**: Shared protocol handler for both transports
- **Smart Config**: Auto-detects optimal transport mode

### Features

- Full MCP protocol support
- Session management
- Async message handling
- Error handling with proper JSON-RPC error codes
- Context manager support
- Logging to stderr (keeps stdout clean)

### Performance

- Uses `orjson` for fast JSON serialization
- Async I/O for non-blocking operations
- Efficient buffer management
- Minimal overhead for message processing

## Compatibility

- Works with all MCP clients that support stdio transport
- Compatible with Claude Desktop and other MCP-enabled applications
- Supports protocol version 2025-03-26
- Python 3.11+ required

## Migration from HTTP-only

If you have an existing HTTP-only server, migration is simple:

1. Update to latest chuk-mcp-server version
2. No code changes required for basic functionality
3. Optionally add `stdio=True` parameter to `run()` for explicit stdio mode
4. Set environment variables for auto-detection if desired

The server maintains full backward compatibility with HTTP mode as the default.
