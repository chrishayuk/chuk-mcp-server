#!/usr/bin/env python3
"""
Ultra-fast ping endpoint with dynamic fixed-length timestamps
"""

import time

import orjson
from starlette.requests import Request
from starlette.responses import Response

from .constants import CONTENT_TYPE_JSON, HEADERS_CORS_NOCACHE, SERVER_NAME, STATUS_PONG


async def handle_request(_request: Request) -> Response:
    """Dynamic ping with Unix millisecond timestamp (always 13 digits)"""
    timestamp_ms = int(time.time() * 1000)

    response_data = {"status": STATUS_PONG, "server": SERVER_NAME, "timestamp": timestamp_ms}

    body: bytes = orjson.dumps(response_data)
    return Response(body, media_type=CONTENT_TYPE_JSON, headers=HEADERS_CORS_NOCACHE)
