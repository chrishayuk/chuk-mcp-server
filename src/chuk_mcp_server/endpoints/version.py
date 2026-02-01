#!/usr/bin/env python3
"""
Version information endpoint with pre-cached static response
"""

import orjson
from starlette.requests import Request
from starlette.responses import Response

from .constants import (
    CONTENT_TYPE_JSON,
    FRAMEWORK_DESCRIPTION,
    HEADERS_CORS_LONG_CACHE,
    MCP_PROTOCOL_VERSION,
    SERVER_NAME,
)

_VERSION_INFO = {
    "name": SERVER_NAME,
    "version": "1.0.0",
    "framework": FRAMEWORK_DESCRIPTION,
    "protocol": {"name": "MCP", "version": MCP_PROTOCOL_VERSION},
    "features": [
        "High-performance HTTP endpoints",
        "MCP protocol support",
        "Registry-driven architecture",
        "Type-safe tools and resources",
        "Session management",
        "SSE streaming support",
    ],
    "optimization": {
        "json_serializer": "orjson",
        "response_caching": True,
        "event_loop": "uvloop",
        "http_parser": "httptools",
    },
}

_CACHED_VERSION_RESPONSE = Response(
    orjson.dumps(_VERSION_INFO), media_type=CONTENT_TYPE_JSON, headers=HEADERS_CORS_LONG_CACHE
)


async def handle_request(_request: Request) -> Response:
    """Pre-cached static version response for maximum performance"""
    return _CACHED_VERSION_RESPONSE


def get_version_info():
    return _VERSION_INFO.copy()


def get_version_string():
    return _VERSION_INFO["version"]


def get_server_name():
    return _VERSION_INFO["name"]
