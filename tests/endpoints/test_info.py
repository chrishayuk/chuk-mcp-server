#!/usr/bin/env python3
"""Tests for info endpoint."""

from unittest.mock import MagicMock

import orjson
import pytest
from starlette.datastructures import QueryParams

from chuk_mcp_server.endpoints.info import InfoEndpoint


class MockRequest:
    """Mock request for testing."""

    def __init__(self, method="GET", query_params=None, host="localhost", scheme="http"):
        self.method = method
        self.query_params = QueryParams(query_params or {})
        self.headers = {"host": host}
        self.url = MagicMock()
        self.url.scheme = scheme


class TestInfoEndpoint:
    """Tests for InfoEndpoint class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock protocol handler
        self.mock_protocol = MagicMock()

        # Mock server info
        self.mock_protocol.server_info.model_dump.return_value = {
            "name": "TestServer",
            "version": "1.0.0",
        }

        # Mock capabilities
        self.mock_protocol.capabilities.model_dump.return_value = {
            "tools": {"listTools": {}},
            "resources": {"listResources": {}},
        }

        # Mock tools and resources
        self.mock_protocol.tools = {"tool1": MagicMock(), "tool2": MagicMock()}
        self.mock_protocol.resources = {"resource1": MagicMock()}

        self.endpoint = InfoEndpoint(self.mock_protocol)

    @pytest.mark.asyncio
    async def test_init(self):
        """Test InfoEndpoint initialization."""
        assert self.endpoint.protocol == self.mock_protocol

    @pytest.mark.asyncio
    async def test_handle_request_get_json(self):
        """Test handling GET request with JSON format."""
        request = MockRequest(method="GET")

        response = await self.endpoint.handle_request(request)

        assert response.status_code == 200
        assert response.media_type == "application/json"

        # Check headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert response.headers["Access-Control-Allow-Origin"] == "*"
        assert "Cache-Control" in response.headers

        # Check body structure
        body = orjson.loads(response.body)
        assert "server" in body
        assert "capabilities" in body
        assert "protocol" in body
        assert "framework" in body
        assert "endpoints" in body
        assert "tools" in body
        assert "resources" in body
        assert "performance" in body
        assert "quick_start" in body

    @pytest.mark.asyncio
    async def test_handle_request_method_not_allowed(self):
        """Test handling non-GET requests."""
        for method in ["POST", "PUT", "DELETE", "PATCH"]:
            request = MockRequest(method=method)

            response = await self.endpoint.handle_request(request)

            assert response.status_code == 405
            assert response.media_type == "application/json"

            body = orjson.loads(response.body)
            assert body["error"] == "Method not allowed"
            assert body["code"] == 405

    @pytest.mark.asyncio
    async def test_handle_request_docs_format(self):
        """Test handling request with docs format."""
        request = MockRequest(query_params={"format": "docs"})

        response = await self.endpoint.handle_request(request)

        assert response.status_code == 200
        assert response.media_type == "text/markdown"

        # Check markdown content
        content = response.body.decode()
        assert "# TestServer - ChukMCPServer" in content
        assert "**Version:** 1.0.0" in content
        assert "## 🚀 Performance Achieved" in content
        assert "## 🔗 Endpoints" in content
        assert "## 🚀 Quick Test" in content
        assert "```bash" in content

    @pytest.mark.asyncio
    async def test_endpoints_urls(self):
        """Test endpoint URLs are correctly generated."""
        request = MockRequest(host="example.com", scheme="https")

        response = await self.endpoint.handle_request(request)
        body = orjson.loads(response.body)

        endpoints = body["endpoints"]
        assert endpoints["mcp"] == "https://example.com/mcp"
        assert endpoints["health"] == "https://example.com/health"
        assert endpoints["ping"] == "https://example.com/ping"
        assert endpoints["version"] == "https://example.com/version"
        assert endpoints["info"] == "https://example.com/"
        assert endpoints["documentation"] == "https://example.com/docs"

    @pytest.mark.asyncio
    async def test_tools_and_resources_info(self):
        """Test tools and resources information."""
        request = MockRequest()

        response = await self.endpoint.handle_request(request)
        body = orjson.loads(response.body)

        # Check tools
        assert body["tools"]["count"] == 2
        assert set(body["tools"]["available"]) == {"tool1", "tool2"}

        # Check resources
        assert body["resources"]["count"] == 1
        assert body["resources"]["available"] == ["resource1"]

    @pytest.mark.asyncio
    async def test_protocol_info(self):
        """Test protocol information."""
        request = MockRequest()

        response = await self.endpoint.handle_request(request)
        body = orjson.loads(response.body)

        protocol = body["protocol"]
        assert protocol["version"] == "MCP 2025-03-26"
        assert protocol["transport"] == "HTTP with SSE"
        assert protocol["inspector_compatible"] is True

    @pytest.mark.asyncio
    async def test_framework_info(self):
        """Test framework information."""
        request = MockRequest()

        response = await self.endpoint.handle_request(request)
        body = orjson.loads(response.body)

        framework = body["framework"]
        assert framework["name"] == "ChukMCPServer"
        assert framework["powered_by"] == "chuk_mcp"
        assert "orjson for JSON serialization" in framework["optimizations"]

    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test performance metrics information."""
        request = MockRequest()

        response = await self.endpoint.handle_request(request)
        body = orjson.loads(response.body)

        performance = body["performance"]
        assert "ping" in performance
        assert "version" in performance
        assert "health" in performance
        assert "mcp_protocol" in performance
        assert "RPS" in performance["ping"]

    @pytest.mark.asyncio
    async def test_quick_start_commands(self):
        """Test quick start commands."""
        request = MockRequest(host="api.test.com", scheme="https")

        response = await self.endpoint.handle_request(request)
        body = orjson.loads(response.body)

        quick_start = body["quick_start"]
        assert quick_start["health_check"] == "curl https://api.test.com/health"
        assert quick_start["ping_test"] == "curl https://api.test.com/ping"
        assert quick_start["version_info"] == "curl https://api.test.com/version"

    @pytest.mark.asyncio
    async def test_format_parameter_case_insensitive(self):
        """Test format parameter is case insensitive."""
        for format_value in ["DOCS", "Docs", "DoCs"]:
            request = MockRequest(query_params={"format": format_value})

            response = await self.endpoint.handle_request(request)

            assert response.status_code == 200
            assert response.media_type == "text/markdown"
