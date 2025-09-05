#!/usr/bin/env python3
"""Tests for ping endpoint."""

from unittest.mock import MagicMock, patch

import orjson
import pytest
from starlette.requests import Request

from chuk_mcp_server.endpoints.ping import handle_request


class TestPingEndpoint:
    """Tests for ping endpoint."""

    @pytest.mark.asyncio
    async def test_basic_response(self):
        """Test basic ping response."""
        mock_request = MagicMock(spec=Request)

        with patch("chuk_mcp_server.endpoints.ping.time.time") as mock_time:
            mock_time.return_value = 1700000000.123
            response = await handle_request(mock_request)

        assert response.status_code == 200
        assert response.media_type == "application/json"

        # Check headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert response.headers["Access-Control-Allow-Origin"] == "*"
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-cache"
        assert "Content-Type" in response.headers
        assert response.headers["Content-Type"] == "application/json"

        # Check body
        body = orjson.loads(response.body)
        assert body["status"] == "pong"
        assert body["server"] == "ChukMCPServer"
        assert body["timestamp"] == 1700000000123  # milliseconds

    @pytest.mark.asyncio
    async def test_timestamp_milliseconds(self):
        """Test that timestamp is in milliseconds."""
        mock_request = MagicMock(spec=Request)

        with patch("chuk_mcp_server.endpoints.ping.time.time") as mock_time:
            # Test various time values
            test_times = [
                1700000000.0,  # Exact second
                1700000000.999,  # Almost next second
                1700000000.001,  # Just after second
                1234567890.123456,  # Random time with microseconds
            ]

            for test_time in test_times:
                mock_time.return_value = test_time
                response = await handle_request(mock_request)

                body = orjson.loads(response.body)
                expected_ms = int(test_time * 1000)
                assert body["timestamp"] == expected_ms

    @pytest.mark.asyncio
    async def test_response_format(self):
        """Test response format and structure."""
        mock_request = MagicMock(spec=Request)

        response = await handle_request(mock_request)

        # Response should be valid JSON
        body = orjson.loads(response.body)

        # Check all required fields
        required_fields = {"status", "server", "timestamp"}
        assert set(body.keys()) == required_fields

        # Check field types
        assert isinstance(body["status"], str)
        assert isinstance(body["server"], str)
        assert isinstance(body["timestamp"], int)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent ping requests."""
        mock_request = MagicMock(spec=Request)

        # Simulate concurrent requests
        responses = []
        for _ in range(10):
            response = await handle_request(mock_request)
            responses.append(response)

        # All should be successful
        for response in responses:
            assert response.status_code == 200
            body = orjson.loads(response.body)
            assert body["status"] == "pong"

    @pytest.mark.asyncio
    async def test_request_not_used(self):
        """Test that request parameter is not used (performance optimization)."""
        # Pass None or any object - should still work
        response = await handle_request(None)

        assert response.status_code == 200
        body = orjson.loads(response.body)
        assert body["status"] == "pong"
