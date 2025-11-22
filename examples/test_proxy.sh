#!/bin/bash
# Improved proxy test script with proper cleanup

echo "🧪 Proxy Integration Test"
echo "========================="
echo ""

# Kill any existing servers on port 8000
echo "Cleaning up any existing servers..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# Start the proxy server
echo "Starting proxy server..."
uv run python examples/proxy_demo.py > /tmp/proxy_test.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Cleaning up..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
    echo "Server stopped"
}
trap cleanup EXIT

# Wait for server to start properly
echo "Waiting for server to start..."
for i in {1..20}; do
    if curl -s http://localhost:8000/mcp > /dev/null 2>&1; then
        echo "✅ Server is up!"
        break
    fi
    if [ $i -eq 20 ]; then
        echo "❌ Server failed to start"
        echo "Server log:"
        cat /tmp/proxy_test.log
        exit 1
    fi
    sleep 0.5
done

# Initialize session
echo ""
echo "🔑 Initializing MCP session..."
INIT_RESPONSE=$(curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 0,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0"}
    }
  }')

SESSION_ID=$(echo "$INIT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('sessionId', 'default-session'))" 2>/dev/null || echo "default-session")
echo "Session ID: $SESSION_ID"

# List tools
echo ""
echo "1️⃣  Listing all tools..."
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }' | python3 -m json.tool | grep '"name"'

# Test local tool
echo ""
echo "2️⃣  Testing local tool (proxy_status)..."
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
  }' | python3 -m json.tool | grep -A 5 "result"

# Test proxied tool - echo
echo ""
echo "3️⃣  Testing proxied tool (proxy.backend.echo)..."
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "proxy.backend.echo",
      "arguments": {"message": "Hello World!"}
    }
  }' | python3 -m json.tool

# Test proxied tool - add
echo ""
echo "4️⃣  Testing proxied tool (proxy.backend.add)..."
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "proxy.backend.add",
      "arguments": {"a": 42, "b": 58}
    }
  }' | python3 -m json.tool

echo ""
echo "========================="
echo "✅ Test complete!"
echo ""
echo "Server log (last 30 lines):"
tail -n 30 /tmp/proxy_test.log
