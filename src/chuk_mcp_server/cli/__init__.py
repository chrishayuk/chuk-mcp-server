#!/usr/bin/env python3
# src/chuk_mcp_server/cli/__init__.py
"""
CLI entry point for ChukMCPServer.

Provides command-line interface for running the server in different modes.
Template strings for ``scaffold_project`` live in ``cli.templates``.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

from ..core import ChukMCPServer


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

        @server.tool("echo")  # type: ignore[untyped-decorator]
        def echo(message: str) -> str:
            """Echo back the provided message."""
            return f"Echo: {message}"

        @server.tool("add")  # type: ignore[untyped-decorator]
        def add(a: float, b: float) -> float:
            """Add two numbers together."""
            return a + b

        @server.tool("get_env")  # type: ignore[untyped-decorator]
        def get_env(key: str) -> str | None:
            """Get an environment variable value."""
            return os.environ.get(key)

    # Add example resource if no resources are registered
    if not server.get_resources():

        @server.resource("server://info")  # type: ignore[untyped-decorator]
        def server_info() -> dict[str, Any]:
            """Get server information."""
            return {
                "name": server.server_info.name,
                "version": server.server_info.version,
                "transport": "stdio" if os.environ.get("MCP_STDIO") else "http",
                "pid": os.getpid(),
            }

    return server


def scaffold_project(project_name: str, directory: str | None = None) -> None:
    """Scaffold a new MCP server project."""
    from .templates import (
        docker_compose_template,
        dockerfile_template,
        gitignore_template,
        pyproject_toml_template,
        readme_md_template,
        server_py_template,
    )

    # Determine project directory
    project_dir = Path(directory) if directory else Path.cwd() / project_name

    # Check if directory already exists
    if project_dir.exists():
        print(f"Error: Directory '{project_dir}' already exists")
        sys.exit(1)

    # Create project directory
    project_dir.mkdir(parents=True)
    print(f"Created project directory: {project_dir}")

    # Write all project files (use encoding="utf-8" for cross-platform compat)
    files: list[tuple[str, str]] = [
        ("server.py", server_py_template(project_name)),
        ("pyproject.toml", pyproject_toml_template(project_name)),
        ("README.md", readme_md_template(project_name, project_dir)),
        (".gitignore", gitignore_template()),
        ("Dockerfile", dockerfile_template()),
        ("docker-compose.yml", docker_compose_template(project_name)),
    ]

    for filename, content in files:
        (project_dir / filename).write_text(content, encoding="utf-8")
        print(f"Created {filename}")

    # Print success message with next steps
    print(f"\nProject '{project_name}' created successfully!")
    print("\nNext steps:")
    print(f"   cd {project_dir.name}")
    print("   uv pip install --system chuk-mcp-server")
    print("   python server.py")
    print("\nOr run with Docker:")
    print("   docker-compose up")
    print(f"\nFor Claude Desktop - see {project_dir.name}/README.md for config")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="chuk-mcp-server",
        description="High-performance MCP server with stdio and HTTP transport support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new MCP server project
  uvx chuk-mcp-server init my-awesome-server

  # Run in stdio mode (for MCP clients)
  uvx chuk-mcp-server stdio

  # Run in HTTP mode on default port
  uvx chuk-mcp-server http

  # Run in HTTP mode on custom port
  uvx chuk-mcp-server http --port 9000

  # Run with specific log level (suppress INFO/DEBUG logs)
  uvx chuk-mcp-server http --log-level warning

  # Run with debug logging
  uvx chuk-mcp-server http --debug
  uvx chuk-mcp-server http --log-level debug

  # Run with minimal logging (errors only)
  uvx chuk-mcp-server http --log-level error

  # Run with custom server name
  MCP_SERVER_NAME=my-server uvx chuk-mcp-server stdio

Environment Variables:
  MCP_SERVER_NAME     Server name (default: chuk-mcp-server)
  MCP_SERVER_VERSION  Server version (default: 0.2.3)
  MCP_TRANSPORT       Force transport mode (stdio|http)
  MCP_LOG_LEVEL       Logging level (debug|info|warning|error|critical)
  MCP_STDIO          Set to 1 to force stdio mode
  USE_STDIO          Alternative to MCP_STDIO
        """,
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="mode", help="Transport mode", required=True)

    # Stdio mode
    stdio_parser = subparsers.add_parser("stdio", help="Run in stdio mode for MCP clients")
    stdio_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    stdio_parser.add_argument(
        "--log-level",
        default="warning",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level (default: warning)",
    )

    # HTTP mode
    http_parser = subparsers.add_parser("http", help="Run in HTTP mode with SSE streaming")
    http_parser.add_argument("--host", default=None, help="Host to bind to (default: auto-detect)")
    http_parser.add_argument("--port", type=int, default=None, help="Port to bind to (default: auto-detect)")
    http_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    http_parser.add_argument("--reload", action="store_true", help="Enable hot reload (auto-restart on file changes)")
    http_parser.add_argument("--inspect", action="store_true", help="Open MCP Inspector in browser after starting")
    http_parser.add_argument(
        "--log-level",
        default="warning",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level (default: warning)",
    )

    # Auto mode (detect from environment)
    auto_parser = subparsers.add_parser("auto", help="Auto-detect transport mode from environment")
    auto_parser.add_argument("--host", default=None, help="Host for HTTP mode (default: auto-detect)")
    auto_parser.add_argument("--port", type=int, default=None, help="Port for HTTP mode (default: auto-detect)")
    auto_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    auto_parser.add_argument(
        "--log-level",
        default="warning",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level (default: warning)",
    )

    # Init mode (scaffold new project)
    init_parser = subparsers.add_parser("init", help="Create a new MCP server project")
    init_parser.add_argument("project_name", help="Name of the project to create")
    init_parser.add_argument(
        "--dir", dest="directory", default=None, help="Directory to create project in (default: ./<project_name>)"
    )

    args = parser.parse_args()

    # Handle init mode separately (no server needed)
    if args.mode == "init":
        scaffold_project(args.project_name, args.directory)
        return

    # Set up logging (to stderr for stdio mode)
    setup_logging(debug=args.debug, stderr=(args.mode == "stdio"))

    # Create server
    server = create_example_server()

    # Run in appropriate mode
    if args.mode == "stdio":
        # Force stdio mode
        logging.info("Starting ChukMCPServer in STDIO mode...")
        server.run(stdio=True, debug=args.debug, log_level=getattr(args, "log_level", "warning"))

    elif args.mode == "http":
        # Force HTTP mode
        logging.info("Starting ChukMCPServer in HTTP mode...")
        server.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            stdio=False,
            log_level=getattr(args, "log_level", "warning"),
            reload=getattr(args, "reload", False),
            inspect=getattr(args, "inspect", False),
        )

    else:  # auto mode
        # Let smart config detect
        logging.info("Starting ChukMCPServer in AUTO mode...")
        server.run(
            host=getattr(args, "host", None),
            port=getattr(args, "port", None),
            debug=args.debug,
            log_level=getattr(args, "log_level", "warning"),
        )


if __name__ == "__main__":
    main()
