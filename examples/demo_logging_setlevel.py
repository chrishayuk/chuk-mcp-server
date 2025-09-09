#!/usr/bin/env python3
"""
Demo script showing how MCP clients can dynamically change server log levels.

This demonstrates the complete MCP logging functionality:
1. Server sends log notifications to client
2. Client can dynamically change server log levels via logging/setLevel
"""

import asyncio
import json
import logging
import sys

from chuk_mcp_server.core import ChukMCPServer

# Configure logging to show different levels
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s", stream=sys.stderr)

# Create server with logging enabled
mcp = ChukMCPServer(name="Dynamic Logging Demo Server", version="1.0.0", transport="stdio", logging=True, debug=False)

# Get a logger for our demo
demo_logger = logging.getLogger("demo")


@mcp.tool
async def generate_logs(count: int = 5) -> dict:
    """Generate sample log messages at different levels."""
    demo_logger.info(f"Starting to generate {count} log messages")

    for i in range(count):
        demo_logger.debug(f"Debug message {i + 1}")
        demo_logger.info(f"Info message {i + 1}")
        demo_logger.warning(f"Warning message {i + 1}")
        demo_logger.error(f"Error message {i + 1}")

    demo_logger.info(f"Completed generating {count * 4} log messages")

    return {
        "status": "completed",
        "messages_generated": count * 4,
        "levels": ["debug", "info", "warning", "error"],
        "note": "Check your MCP client for log notifications",
    }


@mcp.tool
def get_current_log_level() -> dict:
    """Get the current logging level for the chuk_mcp_server logger."""
    logger = logging.getLogger("chuk_mcp_server")
    current_level = logger.level
    level_name = logging.getLevelName(current_level)

    return {
        "logger": "chuk_mcp_server",
        "numeric_level": current_level,
        "level_name": level_name,
        "note": "Use logging/setLevel to change this dynamically",
    }


async def demo_dynamic_logging():
    """Demo function showing how to change log levels dynamically."""

    print("🎭 MCP Dynamic Logging Demo", file=sys.stderr)
    print("=" * 40, file=sys.stderr)
    print("", file=sys.stderr)
    print("This demo shows how MCP clients can:", file=sys.stderr)
    print("1. Receive log notifications from the server", file=sys.stderr)
    print("2. Dynamically change server log levels via logging/setLevel", file=sys.stderr)
    print("", file=sys.stderr)
    print("Available tools:", file=sys.stderr)
    print("  - generate_logs: Generate sample log messages", file=sys.stderr)
    print("  - get_current_log_level: Check current server log level", file=sys.stderr)
    print("", file=sys.stderr)
    print("MCP Methods:", file=sys.stderr)
    print("  - logging/setLevel: Change server log level dynamically", file=sys.stderr)
    print("    Valid levels: debug, info, warning, error", file=sys.stderr)
    print("", file=sys.stderr)
    print("Example logging/setLevel requests:", file=sys.stderr)

    # Demonstrate different logging/setLevel requests
    example_requests = [{"level": "debug"}, {"level": "info"}, {"level": "warning"}, {"level": "error"}]

    for params in example_requests:
        request = {"jsonrpc": "2.0", "id": 1, "method": "logging/setLevel", "params": params}
        print(f"  {json.dumps(request)}", file=sys.stderr)

        # Show what the response would be
        response, _ = await mcp.protocol.handle_request(request)
        if response and "result" in response:
            print(f"    → Response: {response['result']['message']}", file=sys.stderr)
        else:
            print(f"    → Error: {response}", file=sys.stderr)

    print("", file=sys.stderr)
    print("💡 Try calling tools and changing log levels to see the effect!", file=sys.stderr)
    print("", file=sys.stderr)
    print("📡 Server ready for MCP communication...", file=sys.stderr)


if __name__ == "__main__":
    # Run the demo setup
    asyncio.run(demo_dynamic_logging())

    # Start the MCP server
    mcp.run()
