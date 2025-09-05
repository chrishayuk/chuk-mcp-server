#!/usr/bin/env python3
# src/chuk_mcp_server/endpoints/version.py
"""
Version information endpoint with pre-cached static response
"""

import orjson
from starlette.requests import Request
from starlette.responses import Response

_VERSION_INFO = {
    "name": "ChukMCPServer",
    "version": "1.0.0",
    "framework": "ChukMCPServer with chuk_mcp",
    "protocol": {"name": "MCP", "version": "2025-03-26"},
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

_VERSION_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "public, max-age=3600, immutable",
    "Content-Type": "application/json",
}

_CACHED_VERSION_RESPONSE = Response(
    orjson.dumps(_VERSION_INFO), media_type="application/json", headers=_VERSION_HEADERS
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
