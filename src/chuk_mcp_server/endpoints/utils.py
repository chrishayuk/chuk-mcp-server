#!/usr/bin/env python3
# src/chuk_mcp_server/endpoints/utils.py
"""
Optimized endpoint utilities with pre-computed responses and zero-allocation patterns
"""

from typing import Any

import orjson
from starlette.responses import Response

# Pre-computed header combinations (avoid dictionary operations in hot paths)
_CORS_NOCACHE = {"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache", "Content-Type": "application/json"}

_CORS_SHORT_CACHE = {
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "public, max-age=300",
    "Content-Type": "application/json",
}

_CORS_LONG_CACHE = {
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "public, max-age=3600, immutable",
    "Content-Type": "application/json",
}

# Pre-built common error responses for maximum performance
_ERROR_RESPONSES = {
    400: orjson.dumps({"error": "Bad request", "code": 400, "type": "bad_request"}),
    404: orjson.dumps({"error": "Not found", "code": 404, "type": "not_found"}),
    405: orjson.dumps({"error": "Method not allowed", "code": 405, "type": "method_not_allowed"}),
    500: orjson.dumps({"error": "Internal server error", "code": 500, "type": "internal_error"}),
}


def json_response_fast(
    data: dict[str, Any] | list[Any] | str | int | float | bool, status_code: int = 200, cache_level: str = "none"
) -> Response:
    """
    Ultra-fast JSON response using pre-computed headers.

    Args:
        data: Data to serialize to JSON
        status_code: HTTP status code
        cache_level: "none", "short", "long" for different cache strategies

    Returns:
        Optimized Response with minimal allocation overhead
    """
    # Select pre-computed headers based on cache level
    if cache_level == "short":
        headers = _CORS_SHORT_CACHE
    elif cache_level == "long":
        headers = _CORS_LONG_CACHE
    else:
        headers = _CORS_NOCACHE

    return Response(orjson.dumps(data), status_code=status_code, media_type="application/json", headers=headers)


def json_response_bytes(data_bytes: bytes, status_code: int = 200, cache_level: str = "none") -> Response:
    """
    Maximum performance JSON response using pre-serialized bytes.

    Use this when you have pre-computed JSON bytes.
    """
    if cache_level == "short":
        headers = _CORS_SHORT_CACHE
    elif cache_level == "long":
        headers = _CORS_LONG_CACHE
    else:
        headers = _CORS_NOCACHE

    return Response(data_bytes, status_code=status_code, media_type="application/json", headers=headers)


def error_response_fast(code: int, message: str | None = None) -> Response:
    """
    Ultra-fast error response using pre-built responses.

    For common error codes, uses pre-serialized responses.
    Expected performance: 12,000+ RPS
    """
    if code in _ERROR_RESPONSES and message is None:
        # Use pre-built response for maximum speed
        return Response(_ERROR_RESPONSES[code], status_code=code, media_type="application/json", headers=_CORS_NOCACHE)
    else:
        # Custom error message
        error_data = {"error": message or "Error", "code": code}
        return Response(
            orjson.dumps(error_data), status_code=code, media_type="application/json", headers=_CORS_NOCACHE
        )


def success_response_fast(data: Any = None, message: str = "success", cache_level: str = "none") -> Response:
    """
    Fast success response with optional data.
    """
    response_data = {"status": message} if data is None else {"status": message, "data": data}

    return json_response_fast(response_data, cache_level=cache_level)


# Ultra-fast pre-built responses for common scenarios
_NOT_FOUND_RESPONSE = Response(
    _ERROR_RESPONSES[404], status_code=404, media_type="application/json", headers=_CORS_NOCACHE
)

_METHOD_NOT_ALLOWED_RESPONSE = Response(
    _ERROR_RESPONSES[405], status_code=405, media_type="application/json", headers=_CORS_NOCACHE
)

_INTERNAL_ERROR_RESPONSE = Response(
    _ERROR_RESPONSES[500], status_code=500, media_type="application/json", headers=_CORS_NOCACHE
)

_BAD_REQUEST_RESPONSE = Response(
    _ERROR_RESPONSES[400], status_code=400, media_type="application/json", headers=_CORS_NOCACHE
)


def not_found_response() -> Response:
    """Pre-built 404 response for maximum performance"""
    return _NOT_FOUND_RESPONSE


def method_not_allowed_response(allowed_methods: list[str] | None = None) -> Response:
    """Pre-built 405 response with optional Allow header"""
    if allowed_methods:
        # Need custom headers, create new response
        headers = _CORS_NOCACHE.copy()
        headers["Allow"] = ", ".join(allowed_methods)
        return Response(_ERROR_RESPONSES[405], status_code=405, media_type="application/json", headers=headers)
    else:
        return _METHOD_NOT_ALLOWED_RESPONSE


def internal_error_response() -> Response:
    """Pre-built 500 response for maximum performance"""
    return _INTERNAL_ERROR_RESPONSE


def bad_request_response() -> Response:
    """Pre-built 400 response for maximum performance"""
    return _BAD_REQUEST_RESPONSE


def validate_json_request_fast(request_body: bytes) -> tuple[bool, dict[str, Any] | str]:
    """
    Optimized JSON validation using orjson.

    Returns:
        (is_valid, parsed_data_or_error_message)
    """
    if not request_body:
        return False, "Empty request body"

    try:
        parsed_data = orjson.loads(request_body)
        return True, parsed_data
    except orjson.JSONDecodeError:
        return False, "Invalid JSON format"
    except Exception:
        return False, "JSON parsing error"


def create_cors_preflight_response_fast(allowed_methods: list[str] | None = None, max_age: int = 3600) -> Response:
    """
    Ultra-fast CORS preflight response.

    Uses pre-computed headers for common scenarios.
    """
    if allowed_methods is None:
        allowed_methods = ["GET", "POST", "OPTIONS"]

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": ", ".join(allowed_methods),
        "Access-Control-Allow-Headers": "Content-Type, Mcp-Session-Id",
        "Access-Control-Max-Age": str(max_age),
    }

    return Response("", status_code=204, headers=headers)


# Response object pool for heavy reuse scenarios
class ResponsePool:
    """
    Response object pool for high-frequency endpoints.

    Reuses Response objects to reduce garbage collection pressure.
    """

    def __init__(self, pool_size: int = 100):
        self.pool: list[Response] = []
        self.pool_size = pool_size

    def get_response(self, content: bytes, status_code: int = 200) -> Response:
        """Get a response object from the pool or create new one."""
        if self.pool:
            response = self.pool.pop()
            response.body = content
            response.status_code = status_code
            return response
        else:
            return Response(content, status_code=status_code, media_type="application/json", headers=_CORS_NOCACHE)

    def return_response(self, response: Response) -> None:
        """Return a response object to the pool."""
        if len(self.pool) < self.pool_size:
            # Reset response for reuse
            response.body = b""
            response.status_code = 200
            self.pool.append(response)


# Global response pool instance
_response_pool = ResponsePool()


def pooled_json_response(data: dict[str, Any] | list[Any], status_code: int = 200) -> Response:
    """
    JSON response using object pooling for maximum performance.

    Best for high-frequency endpoints with small responses.
    """
    content_bytes = orjson.dumps(data)
    return _response_pool.get_response(content_bytes, status_code)


# Performance monitoring helpers
def add_performance_headers(response: Response, endpoint_name: str) -> Response:
    """Add performance monitoring headers to response."""
    response.headers["X-Endpoint"] = endpoint_name
    response.headers["X-Optimization"] = "orjson+pooling"
    return response
