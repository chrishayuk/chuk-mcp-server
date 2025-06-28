#!/usr/bin/env python3
"""
main.py - Main Server Entry Point

Command-line interface and server runner for the Fast MCP Server.
Handles argument parsing, configuration, and server startup.
"""

import argparse
import sys
import uvicorn
from typing import Optional

from .app import create_app, ServerConfig
from .models import get_state


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    
    parser = argparse.ArgumentParser(
        description="Fast MCP Protocol Server - High-performance MCP implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m fast_mcp_server                          # Run with defaults
  python -m fast_mcp_server --port 8080              # Custom port
  python -m fast_mcp_server --workers 4              # Multi-worker
  python -m fast_mcp_server --debug                  # Development mode
  python -m fast_mcp_server --workers 4 --port 8080  # Production setup

Performance Tips:
  • Use multiple workers for CPU-bound tasks
  • Single worker often fastest for I/O-bound tasks
  • Monitor with /metrics endpoint
  • Test with quick_benchmark.py
        """
    )
    
    # Basic server settings
    parser.add_argument(
        "--host", 
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1,
        help="Number of worker processes (default: 1)"
    )
    
    # Development settings
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode (verbose logging, auto-reload)"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true",
        help="Enable auto-reload on file changes"
    )
    
    # Performance settings
    parser.add_argument(
        "--max-concurrency", 
        type=int, 
        default=10000,
        help="Maximum concurrent connections (default: 10000)"
    )
    
    parser.add_argument(
        "--backlog", 
        type=int, 
        default=4096,
        help="Socket backlog size (default: 4096)"
    )
    
    parser.add_argument(
        "--keepalive-timeout", 
        type=int, 
        default=5,
        help="Keep-alive timeout in seconds (default: 5)"
    )
    
    # Logging settings
    parser.add_argument(
        "--log-level", 
        choices=["critical", "error", "warning", "info", "debug"],
        default="error",
        help="Log level (default: error)"
    )
    
    parser.add_argument(
        "--access-log", 
        action="store_true",
        help="Enable access logging"
    )
    
    # Utility commands
    parser.add_argument(
        "--version", 
        action="version",
        version="Fast MCP Server 1.0.0"
    )
    
    parser.add_argument(
        "--info", 
        action="store_true",
        help="Show server information and exit"
    )
    
    return parser


def run_server(config: ServerConfig) -> None:
    """Run the MCP server with given configuration"""
    
    # Print configuration info
    config.print_info()
    
    # Create application
    app = create_app(debug=config.debug)
    
    # Get uvicorn configuration
    uvicorn_config = config.get_uvicorn_config()
    
    try:
        # Run server
        uvicorn.run(app, **uvicorn_config)
    except KeyboardInterrupt:
        print("\n👋 Fast MCP Server stopped by user")
    except Exception as e:
        print(f"\n💥 Server error: {e}")
        sys.exit(1)


def show_info() -> None:
    """Show server information without starting"""
    
    state = get_state()
    
    print("🚀 Fast MCP Server Information")
    print("=" * 50)
    print("Version: 1.0.0")
    print("Protocol: MCP 2025-06-18")
    print("Framework: Starlette + uvicorn")
    print("JSON Library: orjson")
    print()
    
    print("Performance Features:")
    print("  • Sub-millisecond response times")
    print("  • 10,000+ RPS capability")
    print("  • Optimized JSON serialization")
    print("  • Minimal memory allocation")
    print("  • High concurrency support")
    print()
    
    print("MCP Features:")
    print("  • Full MCP 2025-06-18 compliance")
    print("  • Session management")
    print("  • Tool execution")
    print("  • Resource reading")
    print("  • Real-time metrics")
    print()
    
    tools = state.get_tools()
    print(f"Available Tools ({len(tools)}):")
    for tool in tools:
        print(f"  • {tool['name']}: {tool['description']}")
    
    resources = state.get_resources()
    print(f"\nAvailable Resources ({len(resources)}):")
    for resource in resources:
        print(f"  • {resource['name']}: {resource['description']}")
    
    print("\nEndpoints:")
    print("  POST /mcp       - MCP protocol endpoint")
    print("  GET  /health    - Health check")
    print("  GET  /metrics   - Performance metrics")
    print("  GET  /          - Server information")
    
    print("\nUsage:")
    print("  python -m fast_mcp_server --help")
    print("  python -m fast_mcp_server --port 8080")
    print("  python -m fast_mcp_server --workers 4")


def main() -> None:
    """Main entry point"""
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle info command
    if args.info:
        show_info()
        return
    
    # Create server configuration
    config = ServerConfig(
        host=args.host,
        port=args.port,
        workers=args.workers,
        debug=args.debug,
        auto_reload=args.reload,
        max_concurrency=args.max_concurrency,
        backlog=args.backlog,
        keepalive_timeout=args.keepalive_timeout,
        log_level=args.log_level,
        access_log=args.access_log,
    )
    
    # Run server
    run_server(config)


if __name__ == "__main__":
    main()