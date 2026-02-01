#!/usr/bin/env python3
"""
Optimized endpoint utilities with pre-computed responses and zero-allocation patterns
"""

from typing import Any

import orjson
from starlette.responses import Response

from .constants import (
    CONTENT_TYPE_JSON,
    CORS_ALLOW_ALL,
    ERROR_BAD_REQUEST,
    ERROR_EMPTY_BODY,
    ERROR_INTERNAL,
    ERROR_INVALID_JSON,
    ERROR_JSON_PARSE,
    ERROR_METHOD_NOT_ALLOWED,
    ERROR_NOT_FOUND,
    ERROR_TYPE_BAD_REQUEST,
    ERROR_TYPE_INTERNAL,
    ERROR_TYPE_METHOD_NOT_ALLOWED,
    ERROR_TYPE_NOT_FOUND,
    HEADER_ALLOW,
    HEADER_CONTENT_TYPE,
    HEADER_CORS_HEADERS,
    HEADER_CORS_MAX_AGE,
    HEADER_CORS_METHODS,
    HEADER_CORS_ORIGIN,
    HEADER_MCP_SESSION_ID,
    HEADERS_CORS_LONG_CACHE,
    HEADERS_CORS_NOCACHE,
    HEADERS_CORS_SHORT_CACHE,
    METHOD_GET,
    METHOD_OPTIONS,
    METHOD_POST,
    STATUS_SUCCESS,
    HttpStatus,
)

# Pre-built common error responses for maximum performance
_ERROR_RESPONSES = {
    HttpStatus.BAD_REQUEST: orjson.dumps(
        {"error": ERROR_BAD_REQUEST, "code": HttpStatus.BAD_REQUEST, "type": ERROR_TYPE_BAD_REQUEST}
    ),
    HttpStatus.NOT_FOUND: orjson.dumps(
        {"error": ERROR_NOT_FOUND, "code": HttpStatus.NOT_FOUND, "type": ERROR_TYPE_NOT_FOUND}
    ),
    HttpStatus.METHOD_NOT_ALLOWED: orjson.dumps(
        {
            "error": ERROR_METHOD_NOT_ALLOWED,
            "code": HttpStatus.METHOD_NOT_ALLOWED,
            "type": ERROR_TYPE_METHOD_NOT_ALLOWED,
        }
    ),
    HttpStatus.INTERNAL_SERVER_ERROR: orjson.dumps(
        {"error": ERROR_INTERNAL, "code": HttpStatus.INTERNAL_SERVER_ERROR, "type": ERROR_TYPE_INTERNAL}
    ),
}


def json_response_fast(
    data: dict[str, Any] | list[Any] | str | int | float | bool,
    status_code: int = HttpStatus.OK,
    cache_level: str = "none",
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
        headers = HEADERS_CORS_SHORT_CACHE
    elif cache_level == "long":
        headers = HEADERS_CORS_LONG_CACHE
    else:
        headers = HEADERS_CORS_NOCACHE

    return Response(orjson.dumps(data), status_code=status_code, media_type=CONTENT_TYPE_JSON, headers=headers)


def json_response_bytes(data_bytes: bytes, status_code: int = HttpStatus.OK, cache_level: str = "none") -> Response:
    """
    Maximum performance JSON response using pre-serialized bytes.

    Use this when you have pre-computed JSON bytes.
    """
    if cache_level == "short":
        headers = HEADERS_CORS_SHORT_CACHE
    elif cache_level == "long":
        headers = HEADERS_CORS_LONG_CACHE
    else:
        headers = HEADERS_CORS_NOCACHE

    return Response(data_bytes, status_code=status_code, media_type=CONTENT_TYPE_JSON, headers=headers)


def error_response_fast(code: int, message: str | None = None) -> Response:
    """
    Ultra-fast error response using pre-built responses.

    For common error codes, uses pre-serialized responses.
    Expected performance: 12,000+ RPS
    """
    if code in _ERROR_RESPONSES and message is None:
        # Use pre-built response for maximum speed
        return Response(
            _ERROR_RESPONSES[code], status_code=code, media_type=CONTENT_TYPE_JSON, headers=HEADERS_CORS_NOCACHE
        )
    else:
        # Custom error message
        error_data = {"error": message or "Error", "code": code}
        return Response(
            orjson.dumps(error_data), status_code=code, media_type=CONTENT_TYPE_JSON, headers=HEADERS_CORS_NOCACHE
        )


def success_response_fast(data: Any = None, message: str = STATUS_SUCCESS, cache_level: str = "none") -> Response:
    """
    Fast success response with optional data.
    """
    response_data = {"status": message} if data is None else {"status": message, "data": data}

    return json_response_fast(response_data, cache_level=cache_level)


# Ultra-fast pre-built responses for common scenarios
_NOT_FOUND_RESPONSE = Response(
    _ERROR_RESPONSES[HttpStatus.NOT_FOUND],
    status_code=HttpStatus.NOT_FOUND,
    media_type=CONTENT_TYPE_JSON,
    headers=HEADERS_CORS_NOCACHE,
)

_METHOD_NOT_ALLOWED_RESPONSE = Response(
    _ERROR_RESPONSES[HttpStatus.METHOD_NOT_ALLOWED],
    status_code=HttpStatus.METHOD_NOT_ALLOWED,
    media_type=CONTENT_TYPE_JSON,
    headers=HEADERS_CORS_NOCACHE,
)

_INTERNAL_ERROR_RESPONSE = Response(
    _ERROR_RESPONSES[HttpStatus.INTERNAL_SERVER_ERROR],
    status_code=HttpStatus.INTERNAL_SERVER_ERROR,
    media_type=CONTENT_TYPE_JSON,
    headers=HEADERS_CORS_NOCACHE,
)

_BAD_REQUEST_RESPONSE = Response(
    _ERROR_RESPONSES[HttpStatus.BAD_REQUEST],
    status_code=HttpStatus.BAD_REQUEST,
    media_type=CONTENT_TYPE_JSON,
    headers=HEADERS_CORS_NOCACHE,
)


def not_found_response() -> Response:
    """Pre-built 404 response for maximum performance"""
    return _NOT_FOUND_RESPONSE


def method_not_allowed_response(allowed_methods: list[str] | None = None) -> Response:
    """Pre-built 405 response with optional Allow header"""
    if allowed_methods:
        # Need custom headers, create new response
        headers = HEADERS_CORS_NOCACHE.copy()
        headers[HEADER_ALLOW] = ", ".join(allowed_methods)
        return Response(
            _ERROR_RESPONSES[HttpStatus.METHOD_NOT_ALLOWED],
            status_code=HttpStatus.METHOD_NOT_ALLOWED,
            media_type=CONTENT_TYPE_JSON,
            headers=headers,
        )
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
        return False, ERROR_EMPTY_BODY

    try:
        parsed_data = orjson.loads(request_body)
        return True, parsed_data
    except orjson.JSONDecodeError:
        return False, ERROR_INVALID_JSON
    except Exception:
        return False, ERROR_JSON_PARSE


def create_cors_preflight_response_fast(allowed_methods: list[str] | None = None, max_age: int = 3600) -> Response:
    """
    Ultra-fast CORS preflight response.

    Uses pre-computed headers for common scenarios.
    """
    if allowed_methods is None:
        allowed_methods = [METHOD_GET, METHOD_POST, METHOD_OPTIONS]

    headers = {
        HEADER_CORS_ORIGIN: CORS_ALLOW_ALL,
        HEADER_CORS_METHODS: ", ".join(allowed_methods),
        HEADER_CORS_HEADERS: f"{HEADER_CONTENT_TYPE}, {HEADER_MCP_SESSION_ID}",
        HEADER_CORS_MAX_AGE: str(max_age),
    }

    return Response("", status_code=HttpStatus.NO_CONTENT, headers=headers)


# Response object pool for heavy reuse scenarios
class ResponsePool:
    """
    Response object pool for high-frequency endpoints.

    Reuses Response objects to reduce garbage collection pressure.
    """

    def __init__(self, pool_size: int = 100):
        self.pool: list[Response] = []
        self.pool_size = pool_size

    def get_response(self, content: bytes, status_code: int = HttpStatus.OK) -> Response:
        """Get a response object from the pool or create new one."""
        if self.pool:
            response = self.pool.pop()
            response.body = content
            response.status_code = status_code
            return response
        else:
            return Response(
                content, status_code=status_code, media_type=CONTENT_TYPE_JSON, headers=HEADERS_CORS_NOCACHE
            )

    def return_response(self, response: Response) -> None:
        """Return a response object to the pool."""
        if len(self.pool) < self.pool_size:
            # Reset response for reuse
            response.body = b""
            response.status_code = HttpStatus.OK
            self.pool.append(response)


# Global response pool instance
_response_pool = ResponsePool()


def pooled_json_response(data: dict[str, Any] | list[Any], status_code: int = HttpStatus.OK) -> Response:
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
