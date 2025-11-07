#!/bin/bash
# Quick test script for proxy functionality

echo "🧪 Quick Proxy Test"
echo "=================="
echo ""

# Start the proxy server in the background
echo "Starting proxy server..."
uv run python examples/proxy_demo.py > /tmp/proxy_server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to initialize..."
sleep 5

# Check if server is up
echo "Checking server health..."
curl -s http://localhost:8000/mcp | python -m json.tool | head -10

# Initialize MCP session first (required by MCP protocol)
echo ""
echo "🔑 Initializing MCP session..."
SESSION_RESPONSE=$(curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 0,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }')

# Extract session ID from response headers
SESSION_ID=$(echo "$SESSION_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('sessionId', ''))" 2>/dev/null || echo "")

if [ -z "$SESSION_ID" ]; then
  # Try to get from Mcp-Session-Id header instead (older version)
  SESSION_ID="default-session"
fi

echo "   Session ID: $SESSION_ID"

# Test 1: List tools
echo ""
echo "1️⃣  Listing available tools:"
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }' | python -m json.tool | grep '"name"' | head -10

# Test 2: Call local tool
echo ""
echo "2️⃣  Calling local tool (proxy_status):"
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
  }' | python -m json.tool

# Test 3: Call proxied tool
echo ""
echo "3️⃣  Calling proxied tool (proxy.backend.echo):"
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
        "message": "Hello from proxy test!"
      }
    }
  }' | python -m json.tool

# Test 4: Call another proxied tool
echo ""
echo "4️⃣  Calling proxied tool (proxy.backend.add):"
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "proxy.backend.add",
      "arguments": {
        "a": 15,
        "b": 27
      }
    }
  }' | python -m json.tool

# Cleanup
echo ""
echo "=================="
echo "✅ Tests complete!"
echo ""
echo "Server log:"
tail -n 20 /tmp/proxy_server.log
echo ""
echo "Shutting down server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo "Done!"
