# Running the Proxy Demo

This guide shows you how to test the multi-server proxy functionality.

## Quick Start

### Terminal 1: Start the Proxy Server

```bash
cd /Users/chrishay/chris-source/chuk-ai/chuk-mcp-server

# Run the proxy demo server
uv run python examples/proxy_demo.py
```

You should see:
```
🌐 ChukMCPServer Proxy Demo
======================================================================

This server proxies a simple backend MCP server and adds local tools.

🔧 Available Tools:

  LOCAL TOOLS (run on proxy server):
    - proxy_status: Check proxy manager status
    - list_servers: List all proxied servers

  PROXIED TOOLS (forwarded to backend):
    - proxy.backend.echo: Echo back a message
    - proxy.backend.greet: Greet someone by name
    - proxy.backend.add: Add two numbers
    - proxy.backend.uppercase: Convert text to uppercase
...
```

### Terminal 2: Test the Proxy

```bash
# In a new terminal
cd /Users/chrishay/chris-source/chuk-ai/chuk-mcp-server

# Run the test client
uv run python examples/test_proxy_client.py
```

You should see output like:
```
🧪 Testing Proxy Server
======================================================================

1️⃣  Listing all available tools...
   Found 6 tools:
     - proxy_status: Get the status of the proxy manager.
     - list_servers: List all proxied servers.
     - proxy.backend.echo: Echo back the message.
     - proxy.backend.greet: Greet someone by name.
     - proxy.backend.add: Add two numbers.
     - proxy.backend.uppercase: Convert text to uppercase.

2️⃣  Calling local tool: proxy_status
   Result: {
     "status": "running",
     "details": {...}
   }

3️⃣  Calling proxied tool: proxy.backend.echo
   Result: "Echo: Hello from proxy!"

...
```

## Manual Testing with curl

You can also test with curl:

### Initialize session (required first)
```bash
# Initialize and get session ID
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 0,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "curl-client", "version": "1.0"}
    }
  }'

# Save the session ID from response, then use it in subsequent calls
SESSION_ID="your-session-id"
```

### List all tools
```bash
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }' | jq '.result.tools[].name'
```

### Call a local tool
```bash
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "proxy_status",
      "arguments": {}
    }
  }' | jq '.result'
```

### Call a proxied tool
```bash
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "proxy.backend.echo",
      "arguments": {
        "message": "Hello from curl!"
      }
    }
  }' | jq '.result'
```

## Testing with MCP Inspector

1. Start the proxy server (Terminal 1):
   ```bash
   uv run python examples/proxy_demo.py
   ```

2. Open MCP Inspector:
   - Go to https://inspector.anthropic.com
   - Or use the desktop app

3. Connect to your server:
   - URL: `http://localhost:8000/mcp`
   - Transport: `Streamable HTTP`

4. You should see all tools (local + proxied)

5. Try calling tools:
   - Local: `proxy_status`
   - Proxied: `proxy.backend.echo` with `message: "test"`
   - Proxied: `proxy.backend.greet` with `name: "Alice"`
   - Proxied: `proxy.backend.add` with `a: 10, b: 20`

## Understanding the Architecture

```
┌─────────────────────────────────────┐
│  proxy_demo.py                      │
│  (ChukMCPServer with ProxyManager)  │
│                                     │
│  Local Tools:                       │
│  - proxy_status                     │
│  - list_servers                     │
│                                     │
│  ProxyManager                       │
│  ├─ Backend: simple_backend_server  │
│  │  (stdio subprocess)              │
│  │  └─ Tools: echo, greet, add,     │
│  │     uppercase                    │
│  │                                  │
│  HTTP Server (port 8000)            │
└──────────────┬──────────────────────┘
               │
               ▼
        Test Client / MCP Inspector
```

## Troubleshooting

### Server won't start
- Check port 8000 is not in use: `lsof -i :8000`
- Try a different port: Edit `proxy_demo.py` and change `port=8000`

### Backend not connecting
- Check Python path in `proxy_demo.py` (should use `sys.executable`)
- Verify `simple_backend_server.py` exists in examples/
- Check server logs for subprocess errors

### Tools not showing up
- Wait a few seconds after server starts (backend needs to initialize)
- Check server output for proxy manager startup messages
- Call `proxy_status` tool to verify proxy is running

### Client can't connect
- Make sure proxy server is running in Terminal 1
- Check the URL: `http://localhost:8000/mcp`
- Verify aiohttp is installed: `uv pip install aiohttp`

## Next Steps

- Try adding more backend servers to `proxy_config`
- Create your own backend server with custom tools
- Experiment with different tool namespaces
- Test with multiple concurrent clients
