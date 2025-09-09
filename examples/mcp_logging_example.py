#!/usr/bin/env python3
"""
ChukMCPServer Custom Logging Handler Example

This example demonstrates how to extend ChukMCPServer with a custom logging handler
to support the MCP logging capability. This allows the server to send log messages
to MCP clients as notifications.

Features demonstrated:
- Custom logging handler that sends MCP notifications
- Integration with Python's logging system
- Different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Structured log messages with metadata
- Automatic client notification of server-side events
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from typing import Any, Optional

from chuk_mcp_server import ChukMCPServer, resource, tool

# ============================================================================
# Custom MCP Logging Handler
# ============================================================================


class MCPLoggingHandler(logging.Handler):
    """
    Custom logging handler that sends log messages to MCP clients via notifications.

    This handler converts Python log records into MCP logging notifications
    and sends them to connected clients.
    """

    def __init__(self, mcp_server: ChukMCPServer):
        super().__init__()
        self.mcp_server = mcp_server
        self.notification_queue: list[dict[str, Any]] = []
        self.clients: dict[str, Any] = {}  # Track connected clients

        # Set up formatting
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord):
        """Emit a log record as an MCP notification."""
        try:
            # Format the log message
            formatted_message = self.format(record)

            # Create MCP logging notification
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/message",
                "params": {
                    "level": self._map_log_level(record.levelno),
                    "logger": record.name,
                    "data": {
                        "message": record.getMessage(),
                        "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                        "module": record.module,
                        "function": record.funcName,
                        "line": record.lineno,
                        "formatted": formatted_message,
                    },
                },
            }

            # Add exception info if present
            if record.exc_info:
                notification["params"]["data"]["exception"] = self.formatException(record.exc_info)

            # Queue notification for sending to clients
            self.notification_queue.append(notification)

            # In a real implementation, you would send this to connected clients
            # For this example, we'll just print to stderr for demonstration
            print(f"[MCP LOG NOTIFICATION] {json.dumps(notification)}", file=sys.stderr)

        except Exception:
            # Don't raise exceptions in logging handler
            self.handleError(record)

    def _map_log_level(self, python_level: int) -> str:
        """Map Python logging levels to MCP logging levels."""
        if python_level >= logging.CRITICAL:
            return "error"  # MCP doesn't have CRITICAL, map to error
        elif python_level >= logging.ERROR:
            return "error"
        elif python_level >= logging.WARNING:
            return "warning"
        elif python_level >= logging.INFO:
            return "info"
        else:
            return "debug"


# ============================================================================
# Enhanced ChukMCPServer with Logging Support
# ============================================================================


class LoggingEnabledMCPServer(ChukMCPServer):
    """
    Extended ChukMCPServer with integrated MCP logging support.

    This class adds MCP logging capability and automatically sets up
    a custom logging handler to send log messages to MCP clients.
    """

    def __init__(self, *args, **kwargs):
        # Enable logging capability by default
        kwargs.setdefault("logging", True)

        super().__init__(*args, **kwargs)

        # Track server events
        self.server_events: list[dict[str, Any]] = []

        # Server logger
        self.server_logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Set up custom MCP logging handler
        self.mcp_logging_handler = MCPLoggingHandler(self)
        self.setup_logging()

    def setup_logging(self):
        """Set up the MCP logging system."""
        # Get the root logger for the chuk_mcp_server package
        mcp_logger = logging.getLogger("chuk_mcp_server")

        # Add our custom handler
        mcp_logger.addHandler(self.mcp_logging_handler)

        # Also add to the example logger
        example_logger = logging.getLogger(__name__)
        example_logger.addHandler(self.mcp_logging_handler)

        self.server_logger.info("🔊 MCP Logging system initialized")

    def log_server_event(self, event_type: str, message: str, data: dict[str, Any] | None = None):
        """Log a server event that will be sent to MCP clients."""
        event = {"type": event_type, "message": message, "timestamp": datetime.now().isoformat(), "data": data or {}}

        self.server_events.append(event)

        # Log through Python logging system (will trigger MCP notification)
        self.server_logger.info(f"[{event_type.upper()}] {message}", extra={"mcp_data": data})

    def get_log_notifications(self) -> list[dict[str, Any]]:
        """Get queued log notifications (for testing/debugging)."""
        return self.mcp_logging_handler.notification_queue.copy()


# ============================================================================
# Example Tools with Logging
# ============================================================================

# Create server with logging enabled
mcp = LoggingEnabledMCPServer(name="MCP Logging Demo Server", version="1.0.0", transport="stdio", debug=False)

# Get a logger for our tools
tool_logger = logging.getLogger(__name__ + ".tools")


@mcp.tool
async def process_data(data: list[int], operation: str = "sum") -> dict[str, Any]:
    """
    Process data with detailed logging.

    This tool demonstrates how server operations can generate log messages
    that are automatically sent to MCP clients.
    """
    start_time = time.time()

    # Log the start of processing
    tool_logger.info(f"Starting data processing: operation={operation}, size={len(data)}")
    mcp.log_server_event(
        "PROCESSING_START", f"Processing {len(data)} items", {"operation": operation, "data_size": len(data)}
    )

    try:
        # Validate operation
        valid_operations = ["sum", "average", "max", "min", "count"]
        if operation not in valid_operations:
            tool_logger.warning(f"Invalid operation requested: {operation}")
            return {"error": f"Invalid operation. Must be one of: {valid_operations}"}

        # Log data validation
        if not data:
            tool_logger.warning("Empty data provided for processing")
            return {"error": "No data provided"}

        if not all(isinstance(x, int | float) for x in data):
            tool_logger.error("Invalid data type detected - all items must be numbers")
            return {"error": "All data items must be numbers"}

        tool_logger.debug(f"Data validation passed for {len(data)} items")

        # Perform operation
        if operation == "sum":
            result = sum(data)
        elif operation == "average":
            result = sum(data) / len(data)
        elif operation == "max":
            result = max(data)
        elif operation == "min":
            result = min(data)
        elif operation == "count":
            result = len(data)

        processing_time = time.time() - start_time

        # Log successful completion
        tool_logger.info(f"Data processing completed: result={result}, time={processing_time:.3f}s")
        mcp.log_server_event(
            "PROCESSING_COMPLETE",
            f"Operation {operation} completed",
            {"result": result, "processing_time": processing_time, "data_size": len(data)},
        )

        return {
            "operation": operation,
            "result": result,
            "data_size": len(data),
            "processing_time": processing_time,
            "status": "success",
        }

    except Exception as e:
        # Log errors
        tool_logger.error(f"Error processing data: {str(e)}", exc_info=True)
        mcp.log_server_event(
            "PROCESSING_ERROR", f"Processing failed: {str(e)}", {"operation": operation, "error": str(e)}
        )

        return {"error": f"Processing failed: {str(e)}", "operation": operation, "status": "error"}


@mcp.tool
async def simulate_long_task(duration: float = 2.0, fail_probability: float = 0.0) -> dict[str, Any]:
    """
    Simulate a long-running task with progress logging.

    This demonstrates how long-running operations can provide
    progress updates via MCP logging notifications.
    """
    task_id = f"task_{int(time.time())}"

    tool_logger.info(f"Starting long task {task_id} (duration: {duration}s)")
    mcp.log_server_event(
        "TASK_START",
        f"Starting task {task_id}",
        {"task_id": task_id, "duration": duration, "fail_probability": fail_probability},
    )

    try:
        # Simulate progress updates
        steps = 5
        step_duration = duration / steps

        for step in range(1, steps + 1):
            await asyncio.sleep(step_duration)

            progress = (step / steps) * 100
            tool_logger.info(f"Task {task_id} progress: {progress:.1f}%")
            mcp.log_server_event(
                "TASK_PROGRESS",
                f"Task {task_id} at {progress:.1f}%",
                {"task_id": task_id, "progress": progress, "step": step, "total_steps": steps},
            )

        # Simulate potential failure
        import random

        if random.random() < fail_probability:
            raise Exception(f"Task {task_id} failed randomly (simulated failure)")

        # Task completed successfully
        tool_logger.info(f"Task {task_id} completed successfully")
        mcp.log_server_event(
            "TASK_COMPLETE",
            f"Task {task_id} completed",
            {"task_id": task_id, "duration": duration, "status": "success"},
        )

        return {"task_id": task_id, "duration": duration, "status": "completed", "steps": steps}

    except Exception as e:
        tool_logger.error(f"Task {task_id} failed: {str(e)}")
        mcp.log_server_event(
            "TASK_FAILED", f"Task {task_id} failed", {"task_id": task_id, "error": str(e), "status": "failed"}
        )

        return {"task_id": task_id, "status": "failed", "error": str(e)}


@mcp.tool
def test_log_levels() -> dict[str, str]:
    """Test all log levels to demonstrate MCP logging notifications."""

    tool_logger.debug("This is a DEBUG message")
    tool_logger.info("This is an INFO message")
    tool_logger.warning("This is a WARNING message")
    tool_logger.error("This is an ERROR message")
    tool_logger.critical("This is a CRITICAL message")

    # Also test server event logging
    mcp.log_server_event(
        "LOG_TEST", "Tested all log levels", {"levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]}
    )

    return {
        "status": "Log level test completed",
        "levels_tested": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "note": "Check MCP client for log notifications",
    }


# ============================================================================
# Resources with Logging Information
# ============================================================================


@mcp.resource("logs://recent")
async def get_recent_logs() -> dict[str, Any]:
    """Get recent server events and log notifications."""
    return {
        "server_events": mcp.server_events[-10:],  # Last 10 events
        "log_notifications_count": len(mcp.get_log_notifications()),
        "logging_enabled": True,
        "timestamp": datetime.now().isoformat(),
    }


@mcp.resource("logs://config")
def get_logging_config() -> dict[str, Any]:
    """Get current logging configuration."""
    return {
        "mcp_logging_enabled": True,
        "logging_capability": True,
        "handler_class": "MCPLoggingHandler",
        "log_levels": {"DEBUG": "debug", "INFO": "info", "WARNING": "warning", "ERROR": "error", "CRITICAL": "error"},
        "loggers": ["chuk_mcp_server", __name__, f"{__name__}.tools"],
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("🔊 ChukMCPServer MCP Logging Example", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print("This server demonstrates MCP logging capability.", file=sys.stderr)
    print("Log messages are sent to MCP clients as notifications.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Features:", file=sys.stderr)
    print("  - Custom MCP logging handler", file=sys.stderr)
    print("  - Python logging integration", file=sys.stderr)
    print("  - Multiple log levels (DEBUG, INFO, WARNING, ERROR)", file=sys.stderr)
    print("  - Structured log messages with metadata", file=sys.stderr)
    print("  - Server event tracking", file=sys.stderr)
    print("", file=sys.stderr)
    print("Available tools:", file=sys.stderr)
    print("  - process_data: Process data with detailed logging", file=sys.stderr)
    print("  - simulate_long_task: Long task with progress logging", file=sys.stderr)
    print("  - test_log_levels: Test all log levels", file=sys.stderr)
    print("", file=sys.stderr)
    print("Available resources:", file=sys.stderr)
    print("  - logs://recent: Recent server events and logs", file=sys.stderr)
    print("  - logs://config: Current logging configuration", file=sys.stderr)
    print("", file=sys.stderr)
    print("📡 Ready for MCP communication with logging enabled...", file=sys.stderr)
    print("", file=sys.stderr)

    # Log server startup
    mcp.log_server_event(
        "SERVER_START",
        "MCP Logging Demo Server starting up",
        {"capabilities": ["tools", "resources", "logging"], "transport": "stdio"},
    )

    # Run the server
    mcp.run()
