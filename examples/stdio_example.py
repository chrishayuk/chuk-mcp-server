#!/usr/bin/env python3
"""
Example demonstrating stdio transport mode for MCP server.

Usage:
    # Run in stdio mode explicitly
    python examples/stdio_example.py --stdio

    # Run with environment variable
    MCP_TRANSPORT=stdio python examples/stdio_example.py

    # Pipe mode (will auto-detect stdio)
    echo '{"jsonrpc":"2.0","method":"initialize","params":{"clientInfo":{"name":"test"}},"id":1}' | python examples/stdio_example.py
"""

import argparse
import logging
import sys

from chuk_mcp_server import ChukMCPServer

# Configure logging to stderr to keep stdout clean for stdio
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stderr
)


def main():
    parser = argparse.ArgumentParser(description="MCP Server with stdio support")
    parser.add_argument("--stdio", action="store_true", help="Run in stdio mode (reads from stdin, writes to stdout)")
    parser.add_argument("--http", action="store_true", help="Force HTTP mode even if stdio would be auto-detected")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP mode (default: 8000)")
    args = parser.parse_args()

    # Create server
    mcp = ChukMCPServer(
        name="stdio-example", version="1.0.0", description="Example server demonstrating stdio transport"
    )

    # Register a simple tool
    @mcp.tool
    def echo(message: str) -> str:
        """Echo back the message."""
        return f"Echo: {message}"

    @mcp.tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @mcp.resource("example://hello")
    def hello_resource() -> str:
        """A simple resource."""
        return "Hello from stdio example!"

    # Determine mode
    if args.stdio:
        print("Starting in stdio mode...", file=sys.stderr)
        mcp.run(stdio=True)
    elif args.http:
        print(f"Starting in HTTP mode on port {args.port}...", file=sys.stderr)
        mcp.run(port=args.port, stdio=False)
    else:
        # Let smart config auto-detect
        print("Auto-detecting transport mode...", file=sys.stderr)
        mcp.run(port=args.port)


if __name__ == "__main__":
    main()
