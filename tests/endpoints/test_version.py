#!/usr/bin/env python3
"""Tests for version endpoint."""

from unittest.mock import MagicMock

import orjson
import pytest
from starlette.requests import Request

from chuk_mcp_server.endpoints.version import (
    get_server_name,
    get_version_info,
    get_version_string,
    handle_request,
)


class TestVersionEndpoint:
    """Tests for version endpoint."""

    @pytest.mark.asyncio
    async def test_basic_response(self):
        """Test basic version response."""
        mock_request = MagicMock(spec=Request)

        response = await handle_request(mock_request)

        assert response.status_code == 200
        assert response.media_type == "application/json"

        # Check headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert response.headers["Access-Control-Allow-Origin"] == "*"
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "public, max-age=3600, immutable"
        assert "Content-Type" in response.headers
        assert response.headers["Content-Type"] == "application/json"

        # Check body structure
        body = orjson.loads(response.body)
        assert "name" in body
        assert "version" in body
        assert "framework" in body
        assert "protocol" in body
        assert "features" in body
        assert "optimization" in body

    @pytest.mark.asyncio
    async def test_response_content(self):
        """Test version response content."""
        mock_request = MagicMock(spec=Request)

        response = await handle_request(mock_request)
        body = orjson.loads(response.body)

        # Check main fields
        assert body["name"] == "ChukMCPServer"
        assert body["version"] == "1.0.0"
        assert body["framework"] == "ChukMCPServer with chuk_mcp"

        # Check protocol
        assert body["protocol"]["name"] == "MCP"
        assert body["protocol"]["version"] == "2025-03-26"

        # Check features list
        assert isinstance(body["features"], list)
        assert len(body["features"]) > 0
        assert "High-performance HTTP endpoints" in body["features"]
        assert "MCP protocol support" in body["features"]

        # Check optimization info
        assert body["optimization"]["json_serializer"] == "orjson"
        assert body["optimization"]["response_caching"] is True
        assert body["optimization"]["event_loop"] == "uvloop"
        assert body["optimization"]["http_parser"] == "httptools"

    @pytest.mark.asyncio
    async def test_cached_response(self):
        """Test that response is cached (same object returned)."""
        mock_request = MagicMock(spec=Request)

        # Get multiple responses
        response1 = await handle_request(mock_request)
        response2 = await handle_request(mock_request)
        response3 = await handle_request(mock_request)

        # Should be the exact same response object (cached)
        assert response1 is response2
        assert response2 is response3

    @pytest.mark.asyncio
    async def test_request_not_used(self):
        """Test that request parameter is not used (performance optimization)."""
        # Pass None or any object - should still work
        response = await handle_request(None)

        assert response.status_code == 200
        body = orjson.loads(response.body)
        assert body["name"] == "ChukMCPServer"

    def test_get_version_info(self):
        """Test get_version_info utility function."""
        info = get_version_info()

        assert isinstance(info, dict)
        assert info["name"] == "ChukMCPServer"
        assert info["version"] == "1.0.0"
        assert "features" in info
        assert "optimization" in info

        # Should return a copy, not the original
        info2 = get_version_info()
        assert info is not info2
        assert info == info2

    def test_get_version_string(self):
        """Test get_version_string utility function."""
        version = get_version_string()

        assert isinstance(version, str)
        assert version == "1.0.0"

    def test_get_server_name(self):
        """Test get_server_name utility function."""
        name = get_server_name()

        assert isinstance(name, str)
        assert name == "ChukMCPServer"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent version requests."""
        mock_request = MagicMock(spec=Request)

        # Simulate concurrent requests
        responses = []
        for _ in range(10):
            response = await handle_request(mock_request)
            responses.append(response)

        # All should be successful and the same cached object
        first_response = responses[0]
        for response in responses:
            assert response.status_code == 200
            assert response is first_response  # Same cached object
