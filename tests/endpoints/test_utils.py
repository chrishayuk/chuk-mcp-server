#!/usr/bin/env python3
"""Tests for endpoint utilities."""

import orjson
from starlette.responses import Response

from chuk_mcp_server.endpoints.utils import (
    ResponsePool,
    add_performance_headers,
    bad_request_response,
    create_cors_preflight_response_fast,
    error_response_fast,
    internal_error_response,
    json_response_bytes,
    json_response_fast,
    method_not_allowed_response,
    not_found_response,
    pooled_json_response,
    success_response_fast,
    validate_json_request_fast,
)


class TestJSONResponseFunctions:
    """Tests for JSON response functions."""

    def test_json_response_fast_basic(self):
        """Test basic JSON response."""
        data = {"key": "value", "number": 42}
        response = json_response_fast(data)

        assert response.status_code == 200
        assert response.media_type == "application/json"
        assert "Access-Control-Allow-Origin" in response.headers
        assert response.headers["Cache-Control"] == "no-cache"

        body = orjson.loads(response.body)
        assert body == data

    def test_json_response_fast_with_cache_levels(self):
        """Test JSON response with different cache levels."""
        data = {"test": "data"}

        # No cache (default)
        response_none = json_response_fast(data, cache_level="none")
        assert response_none.headers["Cache-Control"] == "no-cache"

        # Short cache
        response_short = json_response_fast(data, cache_level="short")
        assert response_short.headers["Cache-Control"] == "public, max-age=300"

        # Long cache
        response_long = json_response_fast(data, cache_level="long")
        assert response_long.headers["Cache-Control"] == "public, max-age=3600, immutable"

    def test_json_response_fast_with_status_code(self):
        """Test JSON response with custom status code."""
        data = {"error": "Not found"}
        response = json_response_fast(data, status_code=404)

        assert response.status_code == 404
        body = orjson.loads(response.body)
        assert body == data

    def test_json_response_fast_various_types(self):
        """Test JSON response with various data types."""
        # List
        list_response = json_response_fast([1, 2, 3])
        assert orjson.loads(list_response.body) == [1, 2, 3]

        # String
        str_response = json_response_fast("test")
        assert orjson.loads(str_response.body) == "test"

        # Number
        num_response = json_response_fast(42)
        assert orjson.loads(num_response.body) == 42

        # Boolean
        bool_response = json_response_fast(True)
        assert orjson.loads(bool_response.body) is True

    def test_json_response_bytes(self):
        """Test JSON response with pre-serialized bytes."""
        data = {"key": "value"}
        data_bytes = orjson.dumps(data)

        response = json_response_bytes(data_bytes)

        assert response.status_code == 200
        assert response.body == data_bytes
        body = orjson.loads(response.body)
        assert body == data

    def test_json_response_bytes_with_cache_levels(self):
        """Test JSON response bytes with different cache levels."""
        data_bytes = orjson.dumps({"test": "data"})

        # Short cache
        response_short = json_response_bytes(data_bytes, cache_level="short")
        assert response_short.headers["Cache-Control"] == "public, max-age=300"

        # Long cache
        response_long = json_response_bytes(data_bytes, cache_level="long")
        assert response_long.headers["Cache-Control"] == "public, max-age=3600, immutable"

    def test_json_response_bytes_with_status_code(self):
        """Test JSON response bytes with custom status code."""
        data_bytes = orjson.dumps({"error": "Server error"})
        response = json_response_bytes(data_bytes, status_code=500)

        assert response.status_code == 500


class TestErrorResponseFunctions:
    """Tests for error response functions."""

    def test_error_response_fast_predefined(self):
        """Test error response with predefined codes."""
        for code in [400, 404, 405, 500]:
            response = error_response_fast(code)

            assert response.status_code == code
            body = orjson.loads(response.body)
            assert body["code"] == code
            assert "error" in body
            assert "type" in body

    def test_error_response_fast_custom_message(self):
        """Test error response with custom message."""
        response = error_response_fast(403, "Forbidden")

        assert response.status_code == 403
        body = orjson.loads(response.body)
        assert body["error"] == "Forbidden"
        assert body["code"] == 403

    def test_error_response_fast_custom_code_no_message(self):
        """Test error response with custom code and no message."""
        response = error_response_fast(418)  # I'm a teapot

        assert response.status_code == 418
        body = orjson.loads(response.body)
        assert body["error"] == "Error"
        assert body["code"] == 418

    def test_not_found_response(self):
        """Test pre-built 404 response."""
        response = not_found_response()

        assert response.status_code == 404
        body = orjson.loads(response.body)
        assert body["code"] == 404
        assert body["type"] == "not_found"

    def test_method_not_allowed_response(self):
        """Test pre-built 405 response."""
        # Without allowed methods
        response = method_not_allowed_response()

        assert response.status_code == 405
        body = orjson.loads(response.body)
        assert body["code"] == 405

        # With allowed methods
        response_with_allow = method_not_allowed_response(["GET", "POST"])

        assert response_with_allow.status_code == 405
        assert response_with_allow.headers["Allow"] == "GET, POST"

    def test_internal_error_response(self):
        """Test pre-built 500 response."""
        response = internal_error_response()

        assert response.status_code == 500
        body = orjson.loads(response.body)
        assert body["code"] == 500
        assert body["type"] == "internal_error"

    def test_bad_request_response(self):
        """Test pre-built 400 response."""
        response = bad_request_response()

        assert response.status_code == 400
        body = orjson.loads(response.body)
        assert body["code"] == 400
        assert body["type"] == "bad_request"


class TestSuccessResponse:
    """Tests for success response function."""

    def test_success_response_fast_no_data(self):
        """Test success response without data."""
        response = success_response_fast()

        assert response.status_code == 200
        body = orjson.loads(response.body)
        assert body == {"status": "success"}

    def test_success_response_fast_with_data(self):
        """Test success response with data."""
        data = {"result": "test"}
        response = success_response_fast(data)

        body = orjson.loads(response.body)
        assert body["status"] == "success"
        assert body["data"] == data

    def test_success_response_fast_custom_message(self):
        """Test success response with custom message."""
        response = success_response_fast(message="created")

        body = orjson.loads(response.body)
        assert body["status"] == "created"

    def test_success_response_fast_with_cache(self):
        """Test success response with cache level."""
        response = success_response_fast(cache_level="short")

        assert response.headers["Cache-Control"] == "public, max-age=300"


class TestValidateJSONRequest:
    """Tests for JSON validation function."""

    def test_validate_json_request_fast_valid(self):
        """Test valid JSON request."""
        data = {"key": "value"}
        request_body = orjson.dumps(data)

        is_valid, parsed = validate_json_request_fast(request_body)

        assert is_valid is True
        assert parsed == data

    def test_validate_json_request_fast_empty(self):
        """Test empty request body."""
        is_valid, error = validate_json_request_fast(b"")

        assert is_valid is False
        assert error == "Empty request body"

    def test_validate_json_request_fast_invalid_json(self):
        """Test invalid JSON format."""
        is_valid, error = validate_json_request_fast(b"{invalid json}")

        assert is_valid is False
        assert error == "Invalid JSON format"

    def test_validate_json_request_fast_valid_types(self):
        """Test various valid JSON types."""
        # Array
        is_valid, parsed = validate_json_request_fast(b"[1, 2, 3]")
        assert is_valid is True
        assert parsed == [1, 2, 3]

        # String
        is_valid, parsed = validate_json_request_fast(b'"test"')
        assert is_valid is True
        assert parsed == "test"

        # Number
        is_valid, parsed = validate_json_request_fast(b"42")
        assert is_valid is True
        assert parsed == 42

        # Boolean
        is_valid, parsed = validate_json_request_fast(b"true")
        assert is_valid is True
        assert parsed is True


class TestCORSPreflight:
    """Tests for CORS preflight response."""

    def test_create_cors_preflight_response_fast_defaults(self):
        """Test CORS preflight with defaults."""
        response = create_cors_preflight_response_fast()

        assert response.status_code == 204
        assert response.headers["Access-Control-Allow-Origin"] == "*"
        assert response.headers["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"
        assert response.headers["Access-Control-Allow-Headers"] == "Content-Type, Mcp-Session-Id"
        assert response.headers["Access-Control-Max-Age"] == "3600"

    def test_create_cors_preflight_response_fast_custom(self):
        """Test CORS preflight with custom values."""
        response = create_cors_preflight_response_fast(allowed_methods=["GET", "PUT", "DELETE"], max_age=7200)

        assert response.status_code == 204
        assert response.headers["Access-Control-Allow-Methods"] == "GET, PUT, DELETE"
        assert response.headers["Access-Control-Max-Age"] == "7200"


class TestResponsePool:
    """Tests for ResponsePool class."""

    def test_response_pool_init(self):
        """Test ResponsePool initialization."""
        pool = ResponsePool(pool_size=50)

        assert pool.pool_size == 50
        assert len(pool.pool) == 0

    def test_response_pool_get_response_new(self):
        """Test getting new response when pool is empty."""
        pool = ResponsePool()
        content = b'{"test": "data"}'

        response = pool.get_response(content, status_code=201)

        assert response.body == content
        assert response.status_code == 201
        assert response.media_type == "application/json"

    def test_response_pool_get_response_from_pool(self):
        """Test getting response from pool."""
        pool = ResponsePool()

        # Add a response to pool
        old_response = Response(b"old", status_code=200)
        pool.pool.append(old_response)

        # Get response from pool
        content = b'{"new": "data"}'
        response = pool.get_response(content, status_code=202)

        assert response is old_response  # Same object
        assert response.body == content  # New content
        assert response.status_code == 202  # New status

    def test_response_pool_return_response(self):
        """Test returning response to pool."""
        pool = ResponsePool(pool_size=2)

        response = Response(b"test", status_code=404)
        pool.return_response(response)

        assert len(pool.pool) == 1
        assert response.body == b""  # Reset
        assert response.status_code == 200  # Reset

    def test_response_pool_size_limit(self):
        """Test pool size limit."""
        pool = ResponsePool(pool_size=2)

        # Return responses up to limit
        for i in range(3):
            response = Response(b"test", status_code=200)
            pool.return_response(response)

        # Pool should only contain 2 responses
        assert len(pool.pool) == 2

    def test_pooled_json_response(self):
        """Test pooled JSON response function."""
        data = {"key": "value"}
        response = pooled_json_response(data, status_code=201)

        assert response.status_code == 201
        body = orjson.loads(response.body)
        assert body == data


class TestPerformanceHeaders:
    """Tests for performance monitoring headers."""

    def test_add_performance_headers(self):
        """Test adding performance headers to response."""
        response = Response(b"test", status_code=200)

        result = add_performance_headers(response, "test-endpoint")

        assert result is response  # Same object
        assert response.headers["X-Endpoint"] == "test-endpoint"
        assert response.headers["X-Optimization"] == "orjson+pooling"
