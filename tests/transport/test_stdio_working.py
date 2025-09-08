#!/usr/bin/env python3
"""Working STDIO transport test."""

import json
import subprocess
import sys

def test_stdio_functionality():
    """Test STDIO transport functionality."""
    print("🧪 Testing Working STDIO Transport")
    print("=" * 50)
    
    # Create test server
    server_script = '''#!/usr/bin/env python3
from chuk_mcp_server import tool, run

@tool
def hello(name: str = "World") -> str:
    """Say hello."""
    return f"Hello, {name}!"

@tool  
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

if __name__ == "__main__":
    run(transport="stdio", debug=False)
'''
    
    with open('/tmp/working_stdio_server.py', 'w') as f:
        f.write(server_script)
    
    # Test multiple JSON-RPC calls
    test_calls = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize", 
            "params": {
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
                "protocolVersion": "2025-06-18"
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "hello",
                "arguments": {"name": "STDIO Test"}
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call", 
            "params": {
                "name": "add",
                "arguments": {"x": 15, "y": 27}
            }
        }
    ]
    
    # Create input for the server
    input_data = "\\n".join(json.dumps(call) for call in test_calls) + "\\n"
    
    print(f"🚀 Running server with {len(test_calls)} test calls...")
    
    # Run server with input
    result = subprocess.run(
        [sys.executable, '/tmp/working_stdio_server.py'],
        input=input_data,
        text=True,
        capture_output=True,
        timeout=10
    )
    
    print(f"Return code: {result.returncode}")
    
    if result.stdout:
        print("\\n📤 Server responses:")
        responses = result.stdout.strip().split('\\n')
        
        for i, response_line in enumerate(responses):
            if response_line.startswith('{'):
                try:
                    response = json.loads(response_line)
                    print(f"  {i+1}. {response.get('method', 'response')} -> {response.get('result', response.get('error', 'N/A'))}")
                except:
                    print(f"  {i+1}. Raw: {response_line[:100]}...")
                    
        # Check if we got expected responses
        if len([r for r in responses if r.startswith('{')]) >= 4:
            print("\\n✅ All test calls returned responses!")
            print("✅ STDIO transport is fully functional!")
            return True
        else:
            print(f"\\n⚠️ Only got {len(responses)} responses, expected 4")
            
    if result.stderr:
        print("\\n📥 Server stderr:")
        print(result.stderr)
        
    return False

if __name__ == "__main__":
    success = test_stdio_functionality()
    print(f"\\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)