#!/usr/bin/env python3
"""Synchronous STDIO Transport for ChukMCP Server."""

import asyncio
import json
import logging
import sys
from typing import Any

logger = logging.getLogger(__name__)


class StdioSyncTransport:
    """Synchronous MCP transport over stdin/stdout."""

    def __init__(self, protocol_handler: Any) -> None:
        self.protocol = protocol_handler
        self.session_id: str | None = None

    def run(self) -> None:
        """Run the STDIO transport synchronously."""
        logger.info("🔌 Starting MCP STDIO transport (sync)")

        try:
            while True:
                try:
                    # Read line from stdin
                    line = sys.stdin.readline()
                    if not line:  # EOF
                        break

                    line = line.strip()
                    if not line:
                        continue

                    # Process message
                    asyncio.run(self._handle_message(line))

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32603, "message": f"Transport error: {str(e)}"},
                    }
                    self._send_response(error_response)

        except Exception as e:
            logger.error(f"STDIO transport error: {e}")
        finally:
            logger.info("🔌 STDIO transport stopped")

    async def _handle_message(self, line: str) -> None:
        """Handle incoming JSON-RPC message."""
        try:
            message = json.loads(line)

            # Process with protocol handler
            response, new_session_id = await self.protocol.handle_request(message, self.session_id)

            # Update session ID if this was initialization
            if new_session_id:
                self.session_id = new_session_id

            # Send response if one was generated
            if response:
                self._send_response(response)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            self._send_error(-32700, "Parse error")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            self._send_error(-32603, f"Internal error: {str(e)}")

    def _send_response(self, response: dict[str, Any]) -> None:
        """Send response to stdout."""
        try:
            response_line = json.dumps(response, separators=(",", ":"))
            print(response_line, flush=True)

        except Exception as e:
            logger.error(f"Error sending response: {e}")

    def _send_error(self, code: int, message: str, request_id: Any = None) -> None:
        """Send error response."""
        error_response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
        self._send_response(error_response)
