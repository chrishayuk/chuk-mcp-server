#!/usr/bin/env python3
"""Tests for Google Cloud Functions adapter."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from chuk_mcp_server.cloud.adapters.gcf import GCFAdapter, get_gcf_handler


class TestGCFAdapter:
    """Test the Google Cloud Functions adapter."""

    def test_initialization(self):
        """Test GCF adapter initialization."""
        mock_server = Mock()
        adapter = GCFAdapter(mock_server)

        assert adapter.server == mock_server
        assert adapter._handler_function is None
        assert adapter._is_setup is False

    @patch.dict(os.environ, {"GOOGLE_CLOUD_FUNCTION_NAME": "test-function"})
    def test_is_compatible_gen1(self):
        """Test compatibility detection for Gen 1 Cloud Functions."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is True

    @patch.dict(os.environ, {"FUNCTION_NAME": "test-function"})
    def test_is_compatible_gen2_function_name(self):
        """Test compatibility detection for Gen 2 with FUNCTION_NAME."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is True

    @patch.dict(os.environ, {"FUNCTION_TARGET": "main"})
    def test_is_compatible_gen2_function_target(self):
        """Test compatibility detection for Gen 2 with FUNCTION_TARGET."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is True

    @patch.dict(os.environ, {"K_SERVICE": "test-service"})
    def test_is_compatible_cloud_run(self):
        """Test compatibility detection for Cloud Run (Gen 2)."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_is_compatible_false(self):
        """Test compatibility when not in GCF environment."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is False

    @patch("chuk_mcp_server.cloud.adapters.gcf.logger")
    @patch.dict(os.environ, {"FUNCTION_NAME": "test"})
    def test_is_compatible_with_logging(self, mock_logger):
        """Test that compatibility detection logs correctly."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is True
        mock_logger.debug.assert_called_with("🌟 Google Cloud Functions environment detected")

    def test_setup_without_functions_framework(self):
        """Test setup fails when functions-framework is not installed."""
        adapter = GCFAdapter(Mock())

        with patch("builtins.__import__", side_effect=ImportError("No module")):
            result = adapter.setup()

        assert result is False
        assert adapter._is_setup is False

    @patch("chuk_mcp_server.cloud.adapters.gcf.logger")
    def test_setup_import_error_logging(self, mock_logger):
        """Test setup logs error when functions-framework missing."""
        adapter = GCFAdapter(Mock())

        with patch("builtins.__import__", side_effect=ImportError("No module")):
            adapter.setup()

        mock_logger.error.assert_called_with(
            "functions-framework is required for GCF support. Install with: pip install 'chuk-mcp-server[gcf]'"
        )

    def test_setup_success(self):
        """Test successful setup."""
        adapter = GCFAdapter(Mock())

        with patch("builtins.__import__"):
            with patch.object(adapter, "_create_gcf_handler"):
                with patch.object(adapter, "_apply_gcf_optimizations"):
                    result = adapter.setup()

        assert result is True
        assert adapter._is_setup is True

    def test_setup_exception_handling(self):
        """Test setup handles exceptions gracefully."""
        adapter = GCFAdapter(Mock())

        with patch("builtins.__import__"):
            with patch.object(adapter, "_create_gcf_handler", side_effect=RuntimeError("Test error")):
                result = adapter.setup()

        assert result is False
        assert adapter._is_setup is False

    def test_get_handler(self):
        """Test getting the handler function."""
        adapter = GCFAdapter(Mock())
        mock_handler = Mock()
        adapter._handler_function = mock_handler

        assert adapter.get_handler() == mock_handler

    def test_get_handler_none(self):
        """Test getting handler when not set."""
        adapter = GCFAdapter(Mock())
        assert adapter.get_handler() is None

    @patch.dict(
        os.environ,
        {
            "FUNCTION_NAME": "test-func",
            "FUNCTION_REGION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        },
    )
    def test_get_deployment_info(self):
        """Test getting deployment information."""
        adapter = GCFAdapter(Mock())
        info = adapter.get_deployment_info()

        assert info["platform"] == "Google Cloud Functions"
        assert info["entry_point"] == "mcp_gcf_handler"
        assert info["runtime"] == "python311"
        assert "deployment_command" in info
        assert "test_urls" in info
        assert "configuration" in info

    def test_create_gcf_handler(self):
        """Test creating the GCF handler function."""
        adapter = GCFAdapter(Mock())

        # Mock functions_framework
        mock_ff = MagicMock()
        mock_ff.http = lambda func: func

        with patch.dict("sys.modules", {"functions_framework": mock_ff}):
            with patch("sys.modules") as mock_modules:
                mock_modules.__getitem__.return_value = MagicMock()
                adapter._create_gcf_handler()

        assert adapter._handler_function is not None
        assert adapter._handler_function.__name__ == "mcp_gcf_handler"

    def test_handle_gcf_request_options(self):
        """Test handling OPTIONS request (CORS preflight)."""
        adapter = GCFAdapter(Mock())
        mock_request = Mock(method="OPTIONS")

        response = adapter._handle_gcf_request(mock_request)

        assert response[1] == 204  # No Content
        assert "Access-Control-Allow-Origin" in response[2]

    def test_handle_gcf_request_get_ping(self):
        """Test handling GET /ping request."""
        mock_server = Mock()
        mock_protocol = AsyncMock()
        mock_protocol.handle_request = AsyncMock(return_value=({"result": "pong"}, "session123"))
        mock_server.protocol = mock_protocol

        adapter = GCFAdapter(mock_server)
        mock_request = Mock(method="GET", path="/ping")

        response = adapter._handle_gcf_request(mock_request)

        assert response[1] == 200
        assert "Access-Control-Allow-Origin" in response[2]
        body = json.loads(response[0])
        assert body["result"] == "pong"

    def test_handle_gcf_request_post(self):
        """Test handling POST request with JSON-RPC."""
        mock_server = Mock()
        mock_protocol = AsyncMock()
        mock_protocol.handle_request = AsyncMock(return_value=({"result": "test"}, None))
        mock_server.protocol = mock_protocol

        adapter = GCFAdapter(mock_server)
        mock_request = Mock(method="POST")
        mock_request.get_json.return_value = {"method": "tools/list", "id": 1}

        response = adapter._handle_gcf_request(mock_request)

        assert response[1] == 200
        body = json.loads(response[0])
        assert body["result"] == "test"

    def test_handle_gcf_request_exception(self):
        """Test handling request with exception."""
        adapter = GCFAdapter(Mock())
        mock_request = Mock(method="POST")
        mock_request.get_json.side_effect = RuntimeError("Test error")

        response = adapter._handle_gcf_request(mock_request)

        assert response[1] == 500
        body = json.loads(response[0])
        assert "error" in body

    def test_convert_gcf_to_mcp_request_get_tools(self):
        """Test converting GET /tools request."""
        adapter = GCFAdapter(Mock())
        mock_request = Mock(method="GET", path="/tools")

        result = adapter._convert_gcf_to_mcp_request(mock_request)

        assert result["method"] == "tools/list"
        assert result["id"] == "gcf_tools"

    def test_convert_gcf_to_mcp_request_get_health(self):
        """Test converting GET /health request."""
        adapter = GCFAdapter(Mock())
        mock_request = Mock(method="GET", path="/health")

        result = adapter._convert_gcf_to_mcp_request(mock_request)

        assert result["method"] == "tools/list"
        assert result["id"] == "gcf_health"

    def test_convert_gcf_to_mcp_request_get_resources(self):
        """Test converting GET /resources request."""
        adapter = GCFAdapter(Mock())
        mock_request = Mock(method="GET", path="/resources")

        result = adapter._convert_gcf_to_mcp_request(mock_request)

        assert result["method"] == "resources/list"
        assert result["id"] == "gcf_resources"

    def test_convert_gcf_to_mcp_request_get_unknown(self):
        """Test converting GET request with unknown path."""
        adapter = GCFAdapter(Mock())
        mock_request = Mock(method="GET", path="/unknown")

        result = adapter._convert_gcf_to_mcp_request(mock_request)

        assert result["method"] == "tools/list"
        assert result["id"] == "gcf_default"

    def test_convert_gcf_to_mcp_request_post_valid(self):
        """Test converting valid POST request."""
        adapter = GCFAdapter(Mock())
        mock_request = Mock(method="POST")
        test_data = {"method": "custom/method", "id": 123}
        mock_request.get_json.return_value = test_data

        result = adapter._convert_gcf_to_mcp_request(mock_request)

        assert result == test_data

    def test_convert_gcf_to_mcp_request_post_invalid(self):
        """Test converting invalid POST request."""
        adapter = GCFAdapter(Mock())
        mock_request = Mock(method="POST")
        mock_request.get_json.return_value = None

        result = adapter._convert_gcf_to_mcp_request(mock_request)

        assert result["method"] == "tools/list"
        assert result["id"] == "gcf_invalid_json"

    def test_convert_gcf_to_mcp_request_post_exception(self):
        """Test converting POST request that raises exception."""
        adapter = GCFAdapter(Mock())
        mock_request = Mock(method="POST")
        mock_request.get_json.side_effect = ValueError("Parse error")

        result = adapter._convert_gcf_to_mcp_request(mock_request)

        assert result["method"] == "tools/list"
        assert result["id"] == "gcf_parse_error"

    def test_convert_gcf_to_mcp_request_unsupported_method(self):
        """Test converting request with unsupported method."""
        adapter = GCFAdapter(Mock())
        mock_request = Mock(method="PUT")

        result = adapter._convert_gcf_to_mcp_request(mock_request)

        assert result["method"] == "tools/list"
        assert result["id"] == "gcf_unsupported_method"

    def test_convert_mcp_to_gcf_response_with_data(self):
        """Test converting MCP response with data."""
        adapter = GCFAdapter(Mock())
        response_data = {"result": "test", "id": 1}

        result = adapter._convert_mcp_to_gcf_response(response_data, "session123")

        body, status, headers = result
        assert status == 200
        assert headers["Content-Type"] == "application/json"
        assert headers["Mcp-Session-Id"] == "session123"
        assert json.loads(body) == response_data

    def test_convert_mcp_to_gcf_response_without_data(self):
        """Test converting MCP response without data."""
        adapter = GCFAdapter(Mock())

        result = adapter._convert_mcp_to_gcf_response(None, None)

        body, status, headers = result
        assert status == 200
        assert json.loads(body) == {"status": "ok"}
        assert "Mcp-Session-Id" not in headers

    def test_cors_preflight_response(self):
        """Test CORS preflight response."""
        adapter = GCFAdapter(Mock())
        body, status, headers = adapter._cors_preflight_response()

        assert body == ""
        assert status == 204
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["Access-Control-Max-Age"] == "3600"

    def test_error_response(self):
        """Test error response generation."""
        adapter = GCFAdapter(Mock())
        body, status, headers = adapter._error_response("Test error")

        assert status == 500
        response_data = json.loads(body)
        assert response_data["error"]["code"] == -32603
        assert "Test error" in response_data["error"]["message"]

    @patch("logging.getLogger")
    def test_apply_gcf_optimizations(self, mock_get_logger):
        """Test applying GCF optimizations."""
        adapter = GCFAdapter(Mock())
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        adapter._apply_gcf_optimizations()

        mock_get_logger.assert_called_with("chuk_mcp_server")
        mock_logger.setLevel.assert_called_with(30)  # logging.WARNING

    @patch.dict(os.environ, {"FUNCTION_NAME": "my-func"})
    def test_get_deployment_command(self):
        """Test getting deployment command."""
        adapter = GCFAdapter(Mock())
        command = adapter._get_deployment_command()

        assert "gcloud functions deploy my-func" in command
        assert "--gen2" in command
        assert "--runtime python311" in command

    @patch.dict(os.environ, {}, clear=True)
    def test_get_deployment_command_default(self):
        """Test deployment command with default values."""
        adapter = GCFAdapter(Mock())
        command = adapter._get_deployment_command()

        assert "my-mcp-server" in command

    @patch.dict(
        os.environ,
        {
            "FUNCTION_REGION": "europe-west1",
            "GOOGLE_CLOUD_PROJECT": "my-project",
            "FUNCTION_NAME": "test-func",
        },
    )
    def test_get_test_urls(self):
        """Test getting test URLs."""
        adapter = GCFAdapter(Mock())
        urls = adapter._get_test_urls()

        assert urls["health_check"] == "https://europe-west1-my-project.cloudfunctions.net/test-func/ping"
        assert urls["tools_list"] == "https://europe-west1-my-project.cloudfunctions.net/test-func"
        assert urls["mcp_endpoint"] == "https://europe-west1-my-project.cloudfunctions.net/test-func"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_test_urls_defaults(self):
        """Test test URLs with default values."""
        adapter = GCFAdapter(Mock())
        urls = adapter._get_test_urls()

        assert "us-central1" in urls["health_check"]
        assert "YOUR-PROJECT" in urls["tools_list"]

    @patch.dict(
        os.environ,
        {
            "FUNCTION_NAME": "test",
            "FUNCTION_MEMORY_MB": "2048",
            "FUNCTION_TIMEOUT_SEC": "300",
            "FUNCTION_REGION": "asia-east1",
            "GOOGLE_CLOUD_PROJECT": "test-proj",
        },
    )
    def test_get_gcf_config_info(self):
        """Test getting GCF configuration info."""
        adapter = GCFAdapter(Mock())
        config = adapter._get_gcf_config_info()

        assert config["function_name"] == "test"
        assert config["memory_mb"] == 2048
        assert config["timeout_sec"] == 300
        assert config["region"] == "asia-east1"
        assert config["project"] == "test-proj"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_gcf_config_info_defaults(self):
        """Test GCF config with default values."""
        adapter = GCFAdapter(Mock())
        config = adapter._get_gcf_config_info()

        assert config["function_name"] == "unknown"
        assert config["memory_mb"] == 512
        assert config["timeout_sec"] == 60

    @patch.dict(os.environ, {"GOOGLE_CLOUD_FUNCTION_NAME": "test"})
    def test_detect_gcf_generation_gen1(self):
        """Test detecting Gen 1 Cloud Functions."""
        adapter = GCFAdapter(Mock())
        assert adapter._detect_gcf_generation() == "gen1"

    @patch.dict(os.environ, {"FUNCTION_TARGET": "main"})
    def test_detect_gcf_generation_gen2_target(self):
        """Test detecting Gen 2 with FUNCTION_TARGET."""
        adapter = GCFAdapter(Mock())
        assert adapter._detect_gcf_generation() == "gen2"

    @patch.dict(os.environ, {"K_SERVICE": "service"})
    def test_detect_gcf_generation_gen2_k_service(self):
        """Test detecting Gen 2 with K_SERVICE."""
        adapter = GCFAdapter(Mock())
        assert adapter._detect_gcf_generation() == "gen2"

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_gcf_generation_unknown(self):
        """Test generation detection when unknown."""
        adapter = GCFAdapter(Mock())
        assert adapter._detect_gcf_generation() == "unknown"


class TestGCFHandlerModule:
    """Test module-level GCF handler functions."""

    @patch("chuk_mcp_server.cloud.adapters.adapter_registry")
    def test_get_gcf_handler_with_active_adapter(self, mock_registry):
        """Test getting handler when adapter is already active."""
        mock_adapter = Mock(spec=GCFAdapter)
        mock_handler = Mock()
        mock_adapter.get_handler.return_value = mock_handler
        mock_registry.get_active_adapter.return_value = mock_adapter

        result = get_gcf_handler()

        assert result == mock_handler
        mock_adapter.get_handler.assert_called_once()

    @patch("chuk_mcp_server.cloud.adapters.adapter_registry")
    @patch("chuk_mcp_server.get_or_create_global_server")
    def test_get_gcf_handler_no_active_adapter(self, mock_get_server, mock_registry):
        """Test getting handler when no adapter is active."""
        mock_registry.get_active_adapter.return_value = None
        mock_server = Mock()
        mock_get_server.return_value = mock_server

        with patch.object(GCFAdapter, "is_compatible", return_value=True):
            with patch.object(GCFAdapter, "setup", return_value=True):
                with patch.object(GCFAdapter, "get_handler") as mock_get_handler:
                    mock_handler = Mock()
                    mock_get_handler.return_value = mock_handler

                    result = get_gcf_handler()

                    assert result == mock_handler
                    assert mock_registry._active_adapter is not None

    @patch("chuk_mcp_server.cloud.adapters.adapter_registry")
    @patch("chuk_mcp_server.get_or_create_global_server")
    def test_get_gcf_handler_not_compatible(self, mock_get_server, mock_registry):
        """Test getting handler when environment is not compatible."""
        mock_registry.get_active_adapter.return_value = None
        mock_server = Mock()
        mock_get_server.return_value = mock_server

        with patch.object(GCFAdapter, "is_compatible", return_value=False):
            result = get_gcf_handler()

            assert result is None

    @patch("chuk_mcp_server.cloud.adapters.adapter_registry")
    @patch("chuk_mcp_server.get_or_create_global_server")
    def test_get_gcf_handler_setup_fails(self, mock_get_server, mock_registry):
        """Test getting handler when setup fails."""
        mock_registry.get_active_adapter.return_value = None
        mock_server = Mock()
        mock_get_server.return_value = mock_server

        with patch.object(GCFAdapter, "is_compatible", return_value=True):
            with patch.object(GCFAdapter, "setup", return_value=False):
                result = get_gcf_handler()

                assert result is None

    @patch.dict(os.environ, {"FUNCTION_NAME": "test"})
    @patch("chuk_mcp_server.cloud.adapters.gcf.get_gcf_handler")
    def test_module_auto_export(self, mock_get_handler):
        """Test module auto-exports handler in GCF environment."""
        mock_handler = Mock()
        mock_get_handler.return_value = mock_handler

        # Re-import to trigger auto-export
        import importlib

        import chuk_mcp_server.cloud.adapters.gcf as gcf_module

        with patch.object(gcf_module, "get_gcf_handler", return_value=mock_handler):
            importlib.reload(gcf_module)

        # Handler should be set at module level when in GCF environment
        # This test verifies the auto-export logic exists
        assert hasattr(gcf_module, "mcp_gcf_handler")
