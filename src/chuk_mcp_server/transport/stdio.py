#!/usr/bin/env python3
"""STDIO Transport for ChukMCP Server - MCP over stdin/stdout."""

import asyncio
import json
import logging
import sys
from typing import Any, AsyncGenerator, Optional

logger = logging.getLogger(__name__)


class StdioTransport:
    """MCP transport over stdin/stdout."""
    
    def __init__(self, protocol_handler):
        self.protocol = protocol_handler
        self.session_id: Optional[str] = None
        self._running = False
        
    async def run(self):
        """Run the STDIO transport."""
        self._running = True
        logger.info("🔌 Starting MCP STDIO transport")
        
        try:
            async for line in self._read_stdin():
                if not self._running:
                    break
                    
                await self._handle_message(line)
                    
        except Exception as e:
            logger.error(f"STDIO transport error: {e}")
            await self._send_error(-32603, f"Transport error: {str(e)}")
        finally:
            self._running = False
            
    async def _read_stdin(self) -> AsyncGenerator[str, None]:
        """Read lines from stdin asynchronously."""
        loop = asyncio.get_event_loop()
        
        while self._running:
            try:
                # Read from stdin in a non-blocking way using proper readline
                def read_line():
                    return sys.stdin.readline()
                    
                line = await loop.run_in_executor(None, read_line)
                if not line:  # EOF
                    break
                line = line.strip()
                if line:
                    yield line
            except Exception as e:
                logger.error(f"Error reading stdin: {e}")
                break
                
    async def _handle_message(self, line: str):
        """Handle incoming JSON-RPC message."""
        try:
            message = json.loads(line)
            
            # Process with protocol handler
            response, new_session_id = await self.protocol.handle_request(
                message, self.session_id
            )
            
            # Update session ID if this was initialization
            if new_session_id:
                self.session_id = new_session_id
                
            # Send response if one was generated
            if response:
                await self._send_response(response)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            await self._send_error(-32700, "Parse error")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await self._send_error(-32603, f"Internal error: {str(e)}")
            
    async def _send_response(self, response: dict[str, Any]):
        """Send response to stdout."""
        try:
            response_line = json.dumps(response, separators=(',', ':'))
            sys.stdout.write(response_line + '\n')
            sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            
    async def _send_error(self, code: int, message: str, request_id: Any = None):
        """Send error response."""
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message}
        }
        await self._send_response(error_response)
        
    def stop(self):
        """Stop the transport."""
        self._running = False