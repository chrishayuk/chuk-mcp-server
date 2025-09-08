#!/usr/bin/env python3
"""Final STDIO transport test."""

import json
import subprocess
import sys
import tempfile

def test_stdio_transport():
    """Test STDIO transport with proper line-by-line input."""
    print("🧪 Final STDIO Transport Test")
    print("=" * 50)
    
    # Create simple test server
    server_code = '''#!/usr/bin/env python3
from chuk_mcp_server import tool, run

@tool
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

@tool
def calculate(x: int, y: int, operation: str = "add") -> int:
    """Perform arithmetic operations."""
    if operation == "add":
        return x + y
    elif operation == "multiply":
        return x * y
    elif operation == "subtract":
        return x - y
    else:
        return 0

if __name__ == "__main__":
    run(transport="stdio", debug=False)
'''
    
    # Write server file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(server_code)
        server_path = f.name
    
    # Create test input with one JSON per line
    test_messages = [
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test","version":"1.0.0"},"protocolVersion":"2025-06-18"}}',
        '{"jsonrpc":"2.0","id":2,"method":"tools/list"}',
        '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"hello","arguments":{"name":"STDIO"}}}',
        '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"calculate","arguments":{"x":10,"y":5,"operation":"add"}}}'
    ]
    
    input_text = "\\n".join(test_messages) + "\\n"
    
    print(f"📤 Sending {len(test_messages)} test messages...")
    
    # Run the test
    try:
        result = subprocess.run(
            [sys.executable, server_path],
            input=input_text,
            text=True,
            capture_output=True,
            timeout=10
        )
        
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            stdout_lines = result.stdout.strip().split('\\n')
            json_responses = [line for line in stdout_lines if line.startswith('{')]
            
            print(f"\\n📥 Got {len(json_responses)} JSON responses:")
            
            success_count = 0
            for i, response_line in enumerate(json_responses):
                try:
                    response = json.loads(response_line)
                    req_id = response.get('id')
                    
                    if 'result' in response:
                        print(f"  ✅ ID {req_id}: Success")
                        success_count += 1
                    elif 'error' in response:
                        print(f"  ❌ ID {req_id}: Error - {response['error']['message']}")
                    else:
                        print(f"  ⚠️ ID {req_id}: Unknown response format")
                        
                except json.JSONDecodeError as e:
                    print(f"  ❌ Line {i}: Invalid JSON - {e}")
            
            # Check success criteria
            if success_count >= 3:  # initialize + at least 2 tool calls
                print(f"\\n🎉 SUCCESS: {success_count}/4 calls succeeded!")
                print("✅ STDIO transport is working correctly!")
                return True
            else:
                print(f"\\n⚠️ Only {success_count}/4 calls succeeded")
        
        if result.stderr:
            stderr_lines = [line for line in result.stderr.split('\\n') if line.strip()]
            if stderr_lines:
                print("\\n📋 Server log:")
                for line in stderr_lines[-5:]:  # Show last 5 log lines
                    print(f"  {line}")
                    
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    finally:
        import os
        try:
            os.unlink(server_path)
        except:
            pass
    
    return False

if __name__ == "__main__":
    success = test_stdio_transport()
    exit_code = 0 if success else 1
    print(f"\\nTest {'PASSED' if success else 'FAILED'} (exit {exit_code})")
    sys.exit(exit_code)