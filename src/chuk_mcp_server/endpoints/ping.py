#!/usr/bin/env python3
# src/chuk_mcp_server/endpoints/ping.py
"""
Ultra-fast ping endpoint with dynamic fixed-length timestamps
"""

import time
import orjson
from starlette.requests import Request
from starlette.responses import Response

_PING_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "no-cache",
    "Content-Type": "application/json"
}

async def handle_request(request: Request) -> Response:
    """Dynamic ping with Unix millisecond timestamp (always 13 digits)"""
    timestamp_ms = int(time.time() * 1000)
    
    response_data = {
        "status": "pong",
        "server": "ChukMCPServer",
        "timestamp": timestamp_ms
    }
    
    return Response(
        orjson.dumps(response_data),
        media_type="application/json",
        headers=_PING_HEADERS
    )