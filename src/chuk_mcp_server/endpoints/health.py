#!/usr/bin/env python3
"""
Health check endpoint with dynamic fixed-length timestamps
"""

import time

import orjson
from starlette.requests import Request
from starlette.responses import Response

from ..protocol import MCPProtocolHandler
from .constants import CONTENT_TYPE_JSON, HEADERS_CORS_NOCACHE, SERVER_NAME, STATUS_HEALTHY

_SERVER_START_TIME = time.time()


class HealthEndpoint:
    def __init__(self, protocol_handler: MCPProtocolHandler):
        self.protocol = protocol_handler
        self.start_time = time.time()

    async def handle_request(self, request: Request) -> Response:
        return await handle_health_ultra_fast(request)


async def handle_health_ultra_fast(_request: Request) -> Response:
    """Dynamic health check with Unix millisecond timestamp"""
    current_time = time.time()
    timestamp_ms = int(current_time * 1000)
    uptime_seconds = int(current_time - _SERVER_START_TIME)

    response_data = {
        "status": STATUS_HEALTHY,
        "server": SERVER_NAME,
        "timestamp": timestamp_ms,
        "uptime": uptime_seconds,
    }

    return Response(orjson.dumps(response_data), media_type=CONTENT_TYPE_JSON, headers=HEADERS_CORS_NOCACHE)
