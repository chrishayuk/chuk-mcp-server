#!/usr/bin/env python3
"""Tests for health endpoint."""

from unittest.mock import MagicMock, patch

import orjson
import pytest
from starlette.requests import Request

from chuk_mcp_server.endpoints.health import HealthEndpoint, handle_health_ultra_fast


class TestHealthEndpoint:
    """Tests for HealthEndpoint class."""

    def test_init(self):
        """Test HealthEndpoint initialization."""
        mock_protocol = MagicMock()
        endpoint = HealthEndpoint(mock_protocol)

        assert endpoint.protocol == mock_protocol
        assert hasattr(endpoint, "start_time")
        assert isinstance(endpoint.start_time, float)

    @pytest.mark.asyncio
    async def test_handle_request(self):
        """Test HealthEndpoint.handle_request delegates to handle_health_ultra_fast."""
        mock_protocol = MagicMock()
        endpoint = HealthEndpoint(mock_protocol)
        mock_request = MagicMock(spec=Request)

        with patch("chuk_mcp_server.endpoints.health.handle_health_ultra_fast") as mock_handle:
            mock_response = MagicMock()
            mock_handle.return_value = mock_response

            result = await endpoint.handle_request(mock_request)

            mock_handle.assert_called_once_with(mock_request)
            assert result == mock_response


class TestHandleHealthUltraFast:
    """Tests for handle_health_ultra_fast function."""

    @pytest.mark.asyncio
    async def test_basic_response(self):
        """Test basic health check response."""
        mock_request = MagicMock(spec=Request)

        with patch("chuk_mcp_server.endpoints.health.time.time") as mock_time:
            # Mock time for consistent testing
            mock_time.return_value = 1700000000.123

            with patch("chuk_mcp_server.endpoints.health._SERVER_START_TIME", 1700000000.0):
                response = await handle_health_ultra_fast(mock_request)

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
        assert body["status"] == "healthy"
        assert body["server"] == "ChukMCPServer"
        assert body["timestamp"] == 1700000000123  # milliseconds
        assert body["uptime"] == 0  # 0.123 seconds rounds down to 0

    @pytest.mark.asyncio
    async def test_uptime_calculation(self):
        """Test uptime calculation in health response."""
        mock_request = MagicMock(spec=Request)

        with patch("chuk_mcp_server.endpoints.health.time.time") as mock_time:
            # Mock time for 1 hour after start
            mock_time.return_value = 1700003600.0

            with patch("chuk_mcp_server.endpoints.health._SERVER_START_TIME", 1700000000.0):
                response = await handle_health_ultra_fast(mock_request)

        body = orjson.loads(response.body)
        assert body["uptime"] == 3600  # 1 hour in seconds

    @pytest.mark.asyncio
    async def test_timestamp_milliseconds(self):
        """Test that timestamp is in milliseconds."""
        mock_request = MagicMock(spec=Request)

        with patch("chuk_mcp_server.endpoints.health.time.time") as mock_time:
            # Test various time values
            test_times = [
                1700000000.0,  # Exact second
                1700000000.999,  # Almost next second
                1700000000.001,  # Just after second
                1234567890.123456,  # Random time with microseconds
            ]

            for test_time in test_times:
                mock_time.return_value = test_time
                response = await handle_health_ultra_fast(mock_request)

                body = orjson.loads(response.body)
                expected_ms = int(test_time * 1000)
                assert body["timestamp"] == expected_ms

    @pytest.mark.asyncio
    async def test_response_format(self):
        """Test response format and structure."""
        mock_request = MagicMock(spec=Request)

        response = await handle_health_ultra_fast(mock_request)

        # Response should be valid JSON
        body = orjson.loads(response.body)

        # Check all required fields
        required_fields = {"status", "server", "timestamp", "uptime"}
        assert set(body.keys()) == required_fields

        # Check field types
        assert isinstance(body["status"], str)
        assert isinstance(body["server"], str)
        assert isinstance(body["timestamp"], int)
        assert isinstance(body["uptime"], int)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent health requests."""
        mock_request = MagicMock(spec=Request)

        # Simulate concurrent requests
        responses = []
        for _ in range(10):
            response = await handle_health_ultra_fast(mock_request)
            responses.append(response)

        # All should be successful
        for response in responses:
            assert response.status_code == 200
            body = orjson.loads(response.body)
            assert body["status"] == "healthy"
