# MCP Client Setup Guide

This guide shows how to configure ChukMCPServer with various MCP clients using both stdio and HTTP transport modes.

## Quick Start with uvx

The easiest way to run ChukMCPServer is using `uvx` (comes with `uv`):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run in STDIO mode (for MCP clients)
uvx chuk-mcp-server stdio

# Run in HTTP mode with SSE streaming
uvx chuk-mcp-server http

# Run on a specific port
uvx chuk-mcp-server http --port 9000

# Run with debug logging
uvx chuk-mcp-server stdio --debug
```

## Claude Desktop Configuration

### STDIO Mode (Recommended for Claude Desktop)

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "chuk-mcp": {
      "command": "uvx",
      "args": ["chuk-mcp-server", "stdio"],
      "env": {
        "MCP_SERVER_NAME": "chuk-mcp-production"
      }
    }
  }
}
```

### With Custom Tools

Create a Python file `my_tools.py`:

```python
#!/usr/bin/env python3
from chuk_mcp_server import ChukMCPServer

# Create server
mcp = ChukMCPServer(name="my-tools")

# Add your custom tools
@mcp.tool
def search_files(pattern: str, directory: str = ".") -> list[str]:
    """Search for files matching a pattern."""
    import glob
    import os
    search_path = os.path.join(directory, "**", pattern)
    return glob.glob(search_path, recursive=True)

@mcp.tool
def read_file(filepath: str) -> str:
    """Read contents of a file."""
    with open(filepath, 'r') as f:
        return f.read()

@mcp.tool
def write_file(filepath: str, content: str) -> str:
    """Write content to a file."""
    with open(filepath, 'w') as f:
        f.write(content)
    return f"Written {len(content)} bytes to {filepath}"

# Run in stdio mode
if __name__ == "__main__":
    import sys
    import os
    # Check if running via stdio
    if not sys.stdin.isatty() or os.environ.get("MCP_STDIO"):
        mcp.run(stdio=True)
    else:
        mcp.run()  # HTTP mode for testing
```

Then configure Claude Desktop:

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "python",
      "args": ["/path/to/my_tools.py"],
      "env": {
        "MCP_STDIO": "1"
      }
    }
  }
}
```

## HTTP Mode Configuration

### For Web-based MCP Clients

```json
{
  "mcpServers": {
    "chuk-mcp-http": {
      "url": "http://localhost:8000/mcp",
      "transport": "http",
      "streaming": true
    }
  }
}
```

Start the server:

```bash
# Using uvx
uvx chuk-mcp-server http --port 8000

# Or run in background
nohup uvx chuk-mcp-server http --port 8000 > server.log 2>&1 &

# Or using systemd (see below)
```

## Advanced Configurations

### Multiple Servers with Different Modes

```json
{
  "mcpServers": {
    "chuk-stdio": {
      "command": "uvx",
      "args": ["chuk-mcp-server", "stdio"],
      "env": {
        "MCP_SERVER_NAME": "stdio-server"
      }
    },
    "chuk-http": {
      "url": "http://localhost:8000/mcp",
      "transport": "http"
    },
    "custom-tools": {
      "command": "python",
      "args": ["/home/user/my_mcp_tools.py"],
      "env": {
        "MCP_STDIO": "1",
        "PYTHONPATH": "/home/user/libs"
      }
    }
  }
}
```

### Docker Container

```dockerfile
FROM python:3.11-slim

RUN pip install --no-cache-dir chuk-mcp-server

# For STDIO mode
CMD ["chuk-mcp-server", "stdio"]

# For HTTP mode
# CMD ["chuk-mcp-server", "http", "--host", "0.0.0.0", "--port", "8000"]
```

Run with Docker:

```bash
# STDIO mode
docker run -i chuk-mcp

# HTTP mode
docker run -p 8000:8000 chuk-mcp chuk-mcp-server http --host 0.0.0.0
```

### Systemd Service (HTTP Mode)

Create `/etc/systemd/system/chuk-mcp.service`:

```ini
[Unit]
Description=ChukMCP Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/lib/chuk-mcp
ExecStart=/usr/local/bin/uvx chuk-mcp-server http --port 8000
Restart=always
RestartSec=10
Environment="MCP_SERVER_NAME=deployed-mcp"

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable chuk-mcp
sudo systemctl start chuk-mcp
sudo systemctl status chuk-mcp
```

## Environment Variables

Configure the server behavior using environment variables:

```bash
# Server identification
export MCP_SERVER_NAME="my-custom-server"
export MCP_SERVER_VERSION="1.0.0"

# Force transport mode
export MCP_TRANSPORT="stdio"  # or "http"
export MCP_STDIO=1            # Force stdio mode
export USE_STDIO=1            # Alternative to MCP_STDIO

# Performance tuning (HTTP mode)
export MCP_WORKERS=8
export MCP_MAX_CONNECTIONS=5000
export MCP_PERFORMANCE_MODE="high_performance"

# Run with configuration
uvx chuk-mcp-server auto
```

## Testing Your Configuration

### Test STDIO Mode

```bash
# Test with a simple request
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | uvx chuk-mcp-server stdio

# Expected output (on stdout):
# {"jsonrpc":"2.0","id":1,"result":{"tools":[...]}}
```

### Test HTTP Mode

```bash
# Start server
uvx chuk-mcp-server http --port 8000 &

# Test health endpoint
curl http://localhost:8000/health

# Test MCP endpoint
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# Test SSE streaming
curl -N -H "Accept: text/event-stream" \
  -X POST http://localhost:8000/mcp \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"clientInfo":{"name":"test"}},"id":1}'
```

## Platform-Specific Examples

### macOS with Homebrew

```bash
# Install uv
brew install uv

# Add to Claude Desktop config
cat << 'EOF' > ~/Library/Application\ Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "chuk": {
      "command": "uvx",
      "args": ["chuk-mcp-server", "stdio"]
    }
  }
}
EOF

# Restart Claude Desktop
```

### Windows with PowerShell

```powershell
# Install uv
irm https://astral.sh/uv/install.ps1 | iex

# Add to Claude Desktop config
$config = @{
  mcpServers = @{
    chuk = @{
      command = "uvx"
      args = @("chuk-mcp-server", "stdio")
    }
  }
}
$config | ConvertTo-Json | Set-Content "$env:APPDATA\Claude\claude_desktop_config.json"

# Restart Claude Desktop
```

### Linux

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to config
mkdir -p ~/.config/claude
cat << 'EOF' > ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "chuk": {
      "command": "uvx",
      "args": ["chuk-mcp-server", "stdio"]
    }
  }
}
EOF
```

## Troubleshooting

### Check if server is working

```bash
# STDIO mode test
echo '{"jsonrpc":"2.0","method":"initialize","params":{"clientInfo":{"name":"test"}},"id":1}' | \
  uvx chuk-mcp-server stdio 2>/dev/null | jq .

# HTTP mode test
uvx chuk-mcp-server http --port 8000 &
sleep 2
curl -s http://localhost:8000/health | jq .
```

### Enable debug logging

```bash
# STDIO mode with debug
uvx chuk-mcp-server stdio --debug

# HTTP mode with debug
uvx chuk-mcp-server http --debug --port 8000
```

### Common Issues

1. **"command not found: uvx"** - Install uv first: `curl -LsSf https://astral.sh/uv/install.sh | sh`

2. **"Connection refused" in HTTP mode** - Check if port is already in use: `lsof -i :8000`

3. **No output in STDIO mode** - Make sure to set `MCP_STDIO=1` or use the `stdio` subcommand

4. **Claude Desktop not connecting** - Check config file location and JSON syntax

## Performance Tips

### For High-Volume Usage

```bash
# HTTP mode with performance settings
MCP_PERFORMANCE_MODE=high_performance \
MCP_WORKERS=8 \
MCP_MAX_CONNECTIONS=10000 \
uvx chuk-mcp-server http --port 8000
```

### For Low-Latency Requirements

```bash
# STDIO mode (lowest latency)
uvx chuk-mcp-server stdio
```

### For Deployment

```bash
# HTTP mode with monitoring
uvx chuk-mcp-server http --port 8000 2>&1 | \
  tee -a /var/log/mcp-server.log | \
  grep -E "(ERROR|WARNING)" | \
  mail -s "MCP Server Alert" admin@example.com
```
