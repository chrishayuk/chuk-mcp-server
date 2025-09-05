#!/usr/bin/env python3
"""Tests for Google Cloud Functions adapter."""

import os
from unittest.mock import MagicMock, Mock, patch

from chuk_mcp_server.cloud.adapters import CloudAdapter
from chuk_mcp_server.cloud.adapters.gcf import GCFAdapter


class TestGCFAdapter:
    """Test the GCFAdapter class."""

    def test_gcf_adapter_initialization(self):
        """Test GCFAdapter initialization."""
        server = Mock()
        adapter = GCFAdapter(server)

        assert adapter.server == server
        assert adapter._handler_function is None
        assert adapter._is_setup is False

    @patch.dict(os.environ, {}, clear=True)
    def test_is_compatible_no_gcf(self):
        """Test compatibility check when not in GCF."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is False

    @patch.dict(os.environ, {"GOOGLE_CLOUD_FUNCTION_NAME": "test-func"})
    def test_is_compatible_gen1(self):
        """Test compatibility check for GCF Gen 1."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is True

    @patch.dict(os.environ, {"FUNCTION_NAME": "test-func"})
    def test_is_compatible_gen2_function_name(self):
        """Test compatibility check for GCF Gen 2 with FUNCTION_NAME."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is True

    @patch.dict(os.environ, {"FUNCTION_TARGET": "test-target"})
    def test_is_compatible_gen2_function_target(self):
        """Test compatibility check for GCF Gen 2 with FUNCTION_TARGET."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is True

    @patch.dict(os.environ, {"K_SERVICE": "test-service"})
    def test_is_compatible_cloud_run(self):
        """Test compatibility check for Cloud Run (GCF Gen 2)."""
        adapter = GCFAdapter(Mock())
        assert adapter.is_compatible() is True

    @patch("chuk_mcp_server.cloud.adapters.gcf.logger")
    def test_setup_without_functions_framework(self, mock_logger):
        """Test setup fails without functions-framework."""
        adapter = GCFAdapter(Mock())

        # Mock import error for functions_framework
        with patch("builtins.__import__", side_effect=ImportError("No module named 'functions_framework'")):
            result = adapter.setup()

            assert result is False
            assert adapter._is_setup is False
            mock_logger.error.assert_called_once()

    def test_setup_with_functions_framework(self):
        """Test successful setup with functions-framework."""
        server = Mock()
        adapter = GCFAdapter(server)

        # Mock functions_framework
        mock_ff = MagicMock()
        mock_ff.http = lambda f: f  # Decorator that returns the function

        with patch.dict("sys.modules", {"functions_framework": mock_ff}):
            with patch.object(adapter, "_apply_gcf_optimizations"):
                result = adapter.setup()

                assert result is True
                assert adapter._is_setup is True
                assert adapter._handler_function is not None
                assert callable(adapter._handler_function)

                # Verify optimizations were applied
                adapter._apply_gcf_optimizations.assert_called_once()

    def test_setup_exception_handling(self):
        """Test setup handles exceptions gracefully."""
        adapter = GCFAdapter(Mock())

        # Mock an exception during setup
        with patch.object(adapter, "_create_gcf_handler", side_effect=RuntimeError("Test error")):
            with patch("chuk_mcp_server.cloud.adapters.gcf.logger") as mock_logger:
                result = adapter.setup()

                assert result is False
                assert adapter._is_setup is False
                mock_logger.error.assert_called()

    def test_get_handler(self):
        """Test getting the handler function."""
        adapter = GCFAdapter(Mock())

        # No handler initially
        assert adapter.get_handler() is None

        # Set a handler
        mock_handler = Mock()
        adapter._handler_function = mock_handler

        assert adapter.get_handler() == mock_handler

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
        """Test creating the GCF handler."""
        server = Mock()
        adapter = GCFAdapter(server)

        # Mock functions_framework
        mock_ff = MagicMock()
        mock_ff.http = lambda f: f  # Decorator that returns the function

        # Mock _handle_gcf_request
        mock_response = {"status": "ok"}
        adapter._handle_gcf_request = Mock(return_value=mock_response)

        with patch.dict("sys.modules", {"functions_framework": mock_ff}):
            adapter._create_gcf_handler()

            assert adapter._handler_function is not None
            assert callable(adapter._handler_function)

            # Test the handler
            mock_request = Mock()
            response = adapter._handler_function(mock_request)

            adapter._handle_gcf_request.assert_called_once_with(mock_request)
            assert response == mock_response

    def test_handler_registered_in_module(self):
        """Test that handler is registered in the module."""
        server = Mock()
        adapter = GCFAdapter(server)

        # Mock functions_framework
        mock_ff = MagicMock()
        mock_ff.http = lambda f: f

        with patch.dict("sys.modules", {"functions_framework": mock_ff}):
            adapter._create_gcf_handler()

            # Check that handler is available in the module
            import sys

            current_module = sys.modules["chuk_mcp_server.cloud.adapters.gcf"]
            assert hasattr(current_module, "mcp_gcf_handler")
            assert current_module.mcp_gcf_handler == adapter._handler_function

    @patch.dict(os.environ, {"FUNCTION_NAME": "test-func", "GOOGLE_CLOUD_PROJECT": "test-project"})
    def test_get_gcf_config_info(self):
        """Test getting GCF configuration info."""
        adapter = GCFAdapter(Mock())

        # Mock the _get_gcf_config_info method if it exists
        if hasattr(adapter, "_get_gcf_config_info"):
            config = adapter._get_gcf_config_info()
            assert isinstance(config, dict)

    def test_adapter_is_cloud_adapter_subclass(self):
        """Test that GCFAdapter is a CloudAdapter subclass."""
        assert issubclass(GCFAdapter, CloudAdapter)

        server = Mock()
        adapter = GCFAdapter(server)
        assert isinstance(adapter, CloudAdapter)
