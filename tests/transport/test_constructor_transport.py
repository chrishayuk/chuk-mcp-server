#!/usr/bin/env python3
"""Test ChukMCPServer constructor transport parameter."""

import json
import subprocess
import sys
import tempfile
import pytest


def test_constructor_stdio_transport():
    """Test STDIO transport via constructor parameter."""
    server_code = '''#!/usr/bin/env python3
from chuk_mcp_server import ChukMCPServer

# Create server with STDIO transport in constructor
mcp = ChukMCPServer(transport="stdio", debug=False)

@mcp.tool
def test_tool(message: str = "test") -> str:
    return f"Constructor STDIO: {message}"

if __name__ == "__main__":
    mcp.run()  # Should automatically use STDIO transport
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(server_code)
        server_path = f.name
    
    try:
        # Test initialization and tool call
        test_messages = [
            '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test","version":"1.0"},"protocolVersion":"2025-06-18"}}',
            '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"test_tool","arguments":{"message":"constructor"}}}'
        ]
        
        input_text = "\n".join(test_messages) + "\n"
        
        result = subprocess.run(
            [sys.executable, server_path],
            input=input_text,
            text=True,
            capture_output=True,
            timeout=10
        )
        
        assert result.returncode == 0
        
        # Parse responses
        json_lines = [line for line in result.stdout.split('\n') if line.startswith('{')]
        assert len(json_lines) >= 2
        
        # Check initialization response
        init_response = json.loads(json_lines[0])
        assert init_response['jsonrpc'] == '2.0'
        assert init_response['id'] == 1
        assert 'result' in init_response
        
        # Check tool call response
        tool_response = json.loads(json_lines[1])
        assert tool_response['jsonrpc'] == '2.0'
        assert tool_response['id'] == 2
        assert 'result' in tool_response
        
        # Verify the tool was called correctly
        content = tool_response['result']['content']
        assert len(content) > 0
        assert 'Constructor STDIO: constructor' in str(content)
        
    finally:
        import os
        os.unlink(server_path)


def test_constructor_http_transport():
    """Test that constructor HTTP transport is properly stored."""
    from chuk_mcp_server import ChukMCPServer
    
    # Test HTTP transport via constructor
    mcp = ChukMCPServer(transport="http")
    assert mcp.smart_transport == "http"
    
    # Test STDIO transport via constructor 
    mcp_stdio = ChukMCPServer(transport="stdio")
    assert mcp_stdio.smart_transport == "stdio"
    
    # Test default (None)
    mcp_default = ChukMCPServer()
    assert mcp_default.smart_transport is None


def test_all_transport_methods_consistency():
    """Test that all three transport specification methods work consistently."""
    
    # Method 1: Constructor parameter
    server_code_constructor = '''#!/usr/bin/env python3
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(transport="stdio", debug=False)

@mcp.tool
def method_test() -> str:
    return "constructor_method"

if __name__ == "__main__":
    mcp.run()
'''
    
    # Method 2: Global run() with transport parameter
    server_code_global = '''#!/usr/bin/env python3
from chuk_mcp_server import tool, run

@tool
def method_test() -> str:
    return "global_method"

if __name__ == "__main__":
    run(transport="stdio", debug=False)
'''
    
    # Method 3: run_stdio() method
    server_code_run_stdio = '''#!/usr/bin/env python3
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(debug=False)

@mcp.tool
def method_test() -> str:
    return "run_stdio_method"

if __name__ == "__main__":
    mcp.run_stdio()
'''
    
    test_cases = [
        ("constructor", server_code_constructor, "constructor_method"),
        ("global", server_code_global, "global_method"), 
        ("run_stdio", server_code_run_stdio, "run_stdio_method")
    ]
    
    for method_name, server_code, expected_response in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(server_code)
            server_path = f.name
        
        try:
            # Test tool call for each method
            test_messages = [
                '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test","version":"1.0"},"protocolVersion":"2025-06-18"}}',
                '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"method_test","arguments":{}}}'
            ]
            
            input_text = "\n".join(test_messages) + "\n"
            
            result = subprocess.run(
                [sys.executable, server_path],
                input=input_text,
                text=True,
                capture_output=True,
                timeout=10
            )
            
            assert result.returncode == 0, f"Method {method_name} failed with return code {result.returncode}"
            
            # Parse responses
            json_lines = [line for line in result.stdout.split('\n') if line.startswith('{')]
            assert len(json_lines) >= 2, f"Method {method_name} didn't return enough responses"
            
            # Check tool call response
            tool_response = json.loads(json_lines[1])
            assert 'result' in tool_response, f"Method {method_name} tool call failed"
            
            # Verify correct response
            content = tool_response['result']['content']
            assert expected_response in str(content), f"Method {method_name} returned unexpected content"
            
        finally:
            import os
            os.unlink(server_path)


def test_global_decorators_with_constructor_transport():
    """Test that global decorators work with constructor-specified transport."""
    server_code = '''#!/usr/bin/env python3
from chuk_mcp_server import tool, ChukMCPServer

# Global decorator
@tool
def global_tool(msg: str) -> str:
    return f"Global: {msg}"

# Create server with constructor transport
mcp = ChukMCPServer(transport="stdio", debug=False)

# Class decorator 
@mcp.tool
def class_tool(msg: str) -> str:
    return f"Class: {msg}"

if __name__ == "__main__":
    mcp.run()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(server_code)
        server_path = f.name
    
    try:
        test_messages = [
            '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test","version":"1.0"},"protocolVersion":"2025-06-18"}}',
            '{"jsonrpc":"2.0","id":2,"method":"tools/list"}',
            '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"global_tool","arguments":{"msg":"test1"}}}',
            '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"class_tool","arguments":{"msg":"test2"}}}'
        ]
        
        input_text = "\n".join(test_messages) + "\n"
        
        result = subprocess.run(
            [sys.executable, server_path],
            input=input_text,
            text=True,
            capture_output=True,
            timeout=10
        )
        
        assert result.returncode == 0
        
        # Parse responses
        json_lines = [line for line in result.stdout.split('\n') if line.startswith('{')]
        assert len(json_lines) >= 4
        
        # Check tools list
        tools_response = json.loads(json_lines[1])
        tools = tools_response['result']['tools']
        tool_names = [tool['name'] for tool in tools]
        assert 'global_tool' in tool_names
        assert 'class_tool' in tool_names
        
        # Check both tool calls work
        global_response = json.loads(json_lines[2])
        assert 'Global: test1' in str(global_response['result']['content'])
        
        class_response = json.loads(json_lines[3])
        assert 'Class: test2' in str(class_response['result']['content'])
        
    finally:
        import os
        os.unlink(server_path)


if __name__ == "__main__":
    print("🧪 Running Constructor Transport Tests")
    print("=" * 50)
    
    try:
        print("1. Testing constructor STDIO transport...")
        test_constructor_stdio_transport()
        print("   ✅ PASSED")
        
        print("2. Testing constructor transport storage...")
        test_constructor_http_transport()
        print("   ✅ PASSED")
        
        print("3. Testing all transport methods consistency...")
        test_all_transport_methods_consistency()
        print("   ✅ PASSED")
        
        print("4. Testing global decorators with constructor transport...")
        test_global_decorators_with_constructor_transport()
        print("   ✅ PASSED")
        
        print("\n🎉 ALL CONSTRUCTOR TRANSPORT TESTS PASSED!")
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)