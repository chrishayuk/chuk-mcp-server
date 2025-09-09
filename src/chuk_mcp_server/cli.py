#!/usr/bin/env python3
"""
CLI entry point for ChukMCPServer.

Provides command-line interface for running the server in different modes.
"""

import argparse
import logging
import os
import sys
from typing import Any

from .core import ChukMCPServer


def setup_logging(debug: bool = False, stderr: bool = True) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    stream = sys.stderr if stderr else sys.stdout

    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=stream)


def create_example_server() -> ChukMCPServer:
    """Create a simple example server with basic tools."""
    server = ChukMCPServer(
        name=os.environ.get("MCP_SERVER_NAME", "chuk-mcp-server"),
        version=os.environ.get("MCP_SERVER_VERSION", "0.2.3"),
        description="High-performance MCP server with stdio and HTTP support",
    )

    # Add example tools if no tools are registered
    if not server.get_tools():

        @server.tool("echo")  # type: ignore[misc]
        def echo(message: str) -> str:
            """Echo back the provided message."""
            return f"Echo: {message}"

        @server.tool("add")  # type: ignore[misc]
        def add(a: float, b: float) -> float:
            """Add two numbers together."""
            return a + b

        @server.tool("get_env")  # type: ignore[misc]
        def get_env(key: str) -> str | None:
            """Get an environment variable value."""
            return os.environ.get(key)

    # Add example resource if no resources are registered
    if not server.get_resources():

        @server.resource("server://info")  # type: ignore[misc]
        def server_info() -> dict[str, Any]:
            """Get server information."""
            return {
                "name": server.server_info.name,
                "version": server.server_info.version,
                "transport": "stdio" if os.environ.get("MCP_STDIO") else "http",
                "pid": os.getpid(),
            }

    return server


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="chuk-mcp-server",
        description="High-performance MCP server with stdio and HTTP transport support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in stdio mode (for MCP clients)
  uvx chuk-mcp-server stdio

  # Run in HTTP mode on default port
  uvx chuk-mcp-server http

  # Run in HTTP mode on custom port
  uvx chuk-mcp-server http --port 9000

  # Run with debug logging
  uvx chuk-mcp-server stdio --debug

  # Run with custom server name
  MCP_SERVER_NAME=my-server uvx chuk-mcp-server stdio

Environment Variables:
  MCP_SERVER_NAME     Server name (default: chuk-mcp-server)
  MCP_SERVER_VERSION  Server version (default: 0.2.3)
  MCP_TRANSPORT       Force transport mode (stdio|http)
  MCP_STDIO          Set to 1 to force stdio mode
  USE_STDIO          Alternative to MCP_STDIO
        """,
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="mode", help="Transport mode", required=True)

    # Stdio mode
    stdio_parser = subparsers.add_parser("stdio", help="Run in stdio mode for MCP clients")
    stdio_parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # HTTP mode
    http_parser = subparsers.add_parser("http", help="Run in HTTP mode with SSE streaming")
    http_parser.add_argument("--host", default=None, help="Host to bind to (default: auto-detect)")
    http_parser.add_argument("--port", type=int, default=None, help="Port to bind to (default: auto-detect)")
    http_parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Auto mode (detect from environment)
    auto_parser = subparsers.add_parser("auto", help="Auto-detect transport mode from environment")
    auto_parser.add_argument("--host", default=None, help="Host for HTTP mode (default: auto-detect)")
    auto_parser.add_argument("--port", type=int, default=None, help="Port for HTTP mode (default: auto-detect)")
    auto_parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Set up logging (to stderr for stdio mode)
    setup_logging(debug=args.debug, stderr=(args.mode == "stdio"))

    # Create server
    server = create_example_server()

    # Run in appropriate mode
    if args.mode == "stdio":
        # Force stdio mode
        logging.info("Starting ChukMCPServer in STDIO mode...")
        server.run(stdio=True, debug=args.debug)

    elif args.mode == "http":
        # Force HTTP mode
        logging.info("Starting ChukMCPServer in HTTP mode...")
        server.run(host=args.host, port=args.port, debug=args.debug, stdio=False)

    else:  # auto mode
        # Let smart config detect
        logging.info("Starting ChukMCPServer in AUTO mode...")
        server.run(host=getattr(args, "host", None), port=getattr(args, "port", None), debug=args.debug)


if __name__ == "__main__":
    main()
