#!/usr/bin/env python3
# simple_test_integrated.py
"""
Simple test to verify integrated zero config works.
"""

print("🧠 Testing Integrated Zero Config...")

# Test 1: Global magic decorators
from chuk_mcp_server import resource, tool


@tool
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"


@tool
def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y


@resource("config://test")
def get_test_config() -> dict:
    """Test configuration."""
    return {"test": True, "zero_config": True, "integrated": True}


print("✅ Global magic decorators work!")

# Test 2: Smart server with zero config
from chuk_mcp_server import ChukMCPServer

print("🧠 Testing Smart Server...")

mcp = ChukMCPServer()  # Everything auto-detected!


@mcp.tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


@mcp.resource("info://server")
def server_info() -> dict:
    """Server information."""
    return {"name": "Auto-detected Smart Server", "zero_config": True, "integrated": True}


print("✅ Smart server works!")

# Test 3: Show smart configuration
print("\n🧠 Smart Configuration Detected:")
info = mcp.info()
smart_config = info["smart_config"]
print(f"   Host: {smart_config['host']}")
print(f"   Port: {smart_config['port']}")
print(f"   Environment: {smart_config['environment']}")
print(f"   Debug: {smart_config['debug']}")
print(f"   Workers: {smart_config['workers']}")

print("\n🎉 Integrated Zero Configuration Test Passed!")
print("Zero config is now seamlessly built into the core framework!")

# To actually run the server, uncomment this:
# if __name__ == "__main__":
#     run()  # Uses global server with all smart defaults
