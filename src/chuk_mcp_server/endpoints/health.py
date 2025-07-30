#!/usr/bin/env python3
# src/chuk_mcp_server/endpoints/health.py
"""
Health check endpoint with dynamic fixed-length timestamps
"""

import time
import orjson
from starlette.requests import Request
from starlette.responses import Response

from ..protocol import MCPProtocolHandler

_HEALTH_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "no-cache",
    "Content-Type": "application/json"
}

_SERVER_START_TIME = time.time()

class HealthEndpoint:
    def __init__(self, protocol_handler: MCPProtocolHandler):
        self.protocol = protocol_handler
        self.start_time = time.time()

    async def handle_request(self, request: Request) -> Response:
        return await handle_health_ultra_fast(request)

async def handle_health_ultra_fast(request: Request) -> Response:
    """Dynamic health check with Unix millisecond timestamp"""
    current_time = time.time()
    timestamp_ms = int(current_time * 1000)
    uptime_seconds = int(current_time - _SERVER_START_TIME)
    
    response_data = {
        "status": "healthy",
        "server": "ChukMCPServer",
        "timestamp": timestamp_ms,
        "uptime": uptime_seconds
    }
    
    return Response(
        orjson.dumps(response_data),
        media_type="application/json",
        headers=_HEALTH_HEADERS
    )