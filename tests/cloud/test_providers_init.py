#!/usr/bin/env python3
"""Tests for cloud/providers/__init__.py module."""

from unittest.mock import Mock, patch

from chuk_mcp_server.cloud.providers import register_all_providers


class TestRegisterAllProviders:
    """Test the register_all_providers function."""

    def test_register_all_providers_success(self):
        """Test successful registration of all providers."""
        mock_registry = Mock()

        # Mock all the registration functions
        with patch("chuk_mcp_server.cloud.providers.gcp.register_gcp_provider") as mock_gcp:
            with patch("chuk_mcp_server.cloud.providers.aws.register_aws_provider") as mock_aws:
                with patch("chuk_mcp_server.cloud.providers.azure.register_azure_provider") as mock_azure:
                    with patch("chuk_mcp_server.cloud.providers.edge.register_edge_providers") as mock_edge:
                        register_all_providers(mock_registry)

                        # Verify all registration functions were called
                        mock_gcp.assert_called_once_with(mock_registry)
                        mock_aws.assert_called_once_with(mock_registry)
                        mock_azure.assert_called_once_with(mock_registry)
                        mock_edge.assert_called_once_with(mock_registry)

    def test_register_all_providers_gcp_import_error(self):
        """Test handling of GCP provider import error."""
        mock_registry = Mock()

        with patch("chuk_mcp_server.cloud.providers.gcp.register_gcp_provider", side_effect=ImportError("No module")):
            with patch("chuk_mcp_server.cloud.providers.aws.register_aws_provider") as mock_aws:
                with patch("chuk_mcp_server.cloud.providers.azure.register_azure_provider") as mock_azure:
                    with patch("chuk_mcp_server.cloud.providers.edge.register_edge_providers") as mock_edge:
                        with patch("chuk_mcp_server.cloud.providers.logger") as mock_logger:
                            register_all_providers(mock_registry)

                            # GCP failed but others should still be called
                            mock_aws.assert_called_once()
                            mock_azure.assert_called_once()
                            mock_edge.assert_called_once()
                            mock_logger.debug.assert_any_call("GCP provider not available: No module")

    def test_register_all_providers_gcp_exception(self):
        """Test handling of GCP provider exception."""
        mock_registry = Mock()

        with patch("chuk_mcp_server.cloud.providers.gcp.register_gcp_provider", side_effect=RuntimeError("Test error")):
            with patch("chuk_mcp_server.cloud.providers.aws.register_aws_provider") as mock_aws:
                with patch("chuk_mcp_server.cloud.providers.azure.register_azure_provider") as mock_azure:
                    with patch("chuk_mcp_server.cloud.providers.edge.register_edge_providers") as mock_edge:
                        with patch("chuk_mcp_server.cloud.providers.logger") as mock_logger:
                            register_all_providers(mock_registry)

                            # GCP failed but others should still be called
                            mock_aws.assert_called_once()
                            mock_azure.assert_called_once()
                            mock_edge.assert_called_once()
                            mock_logger.error.assert_any_call("Error registering GCP provider: Test error")

    def test_register_all_providers_aws_import_error(self):
        """Test handling of AWS provider import error."""
        mock_registry = Mock()

        with patch("chuk_mcp_server.cloud.providers.gcp.register_gcp_provider") as mock_gcp:
            with patch(
                "chuk_mcp_server.cloud.providers.aws.register_aws_provider", side_effect=ImportError("No module")
            ):
                with patch("chuk_mcp_server.cloud.providers.azure.register_azure_provider") as mock_azure:
                    with patch("chuk_mcp_server.cloud.providers.edge.register_edge_providers") as mock_edge:
                        with patch("chuk_mcp_server.cloud.providers.logger") as mock_logger:
                            register_all_providers(mock_registry)

                            # AWS failed but others should still be called
                            mock_gcp.assert_called_once()
                            mock_azure.assert_called_once()
                            mock_edge.assert_called_once()
                            mock_logger.debug.assert_any_call("AWS provider not available: No module")

    def test_register_all_providers_azure_exception(self):
        """Test handling of Azure provider exception."""
        mock_registry = Mock()

        with patch("chuk_mcp_server.cloud.providers.gcp.register_gcp_provider") as mock_gcp:
            with patch("chuk_mcp_server.cloud.providers.aws.register_aws_provider") as mock_aws:
                with patch(
                    "chuk_mcp_server.cloud.providers.azure.register_azure_provider",
                    side_effect=RuntimeError("Azure error"),
                ):
                    with patch("chuk_mcp_server.cloud.providers.edge.register_edge_providers") as mock_edge:
                        with patch("chuk_mcp_server.cloud.providers.logger") as mock_logger:
                            register_all_providers(mock_registry)

                            # Azure failed but others should still be called
                            mock_gcp.assert_called_once()
                            mock_aws.assert_called_once()
                            mock_edge.assert_called_once()
                            mock_logger.error.assert_any_call("Error registering Azure provider: Azure error")

    def test_register_all_providers_edge_import_error(self):
        """Test handling of Edge provider import error."""
        mock_registry = Mock()

        with patch("chuk_mcp_server.cloud.providers.gcp.register_gcp_provider") as mock_gcp:
            with patch("chuk_mcp_server.cloud.providers.aws.register_aws_provider") as mock_aws:
                with patch("chuk_mcp_server.cloud.providers.azure.register_azure_provider") as mock_azure:
                    with patch(
                        "chuk_mcp_server.cloud.providers.edge.register_edge_providers",
                        side_effect=ImportError("No edge"),
                    ):
                        with patch("chuk_mcp_server.cloud.providers.logger") as mock_logger:
                            register_all_providers(mock_registry)

                            # Edge failed but others should still be called
                            mock_gcp.assert_called_once()
                            mock_aws.assert_called_once()
                            mock_azure.assert_called_once()
                            mock_logger.debug.assert_any_call("Edge providers not available: No edge")

    def test_register_all_providers_all_fail(self):
        """Test when all providers fail to register."""
        mock_registry = Mock()

        with patch("chuk_mcp_server.cloud.providers.gcp.register_gcp_provider", side_effect=ImportError("No GCP")):
            with patch("chuk_mcp_server.cloud.providers.aws.register_aws_provider", side_effect=ImportError("No AWS")):
                with patch(
                    "chuk_mcp_server.cloud.providers.azure.register_azure_provider",
                    side_effect=ImportError("No Azure"),
                ):
                    with patch(
                        "chuk_mcp_server.cloud.providers.edge.register_edge_providers",
                        side_effect=ImportError("No Edge"),
                    ):
                        with patch("chuk_mcp_server.cloud.providers.logger") as mock_logger:
                            register_all_providers(mock_registry)

                            # All failed, but function should complete
                            assert mock_logger.debug.call_count >= 5  # At least one for each provider + completion

    @patch("chuk_mcp_server.cloud.providers.logger")
    def test_register_all_providers_logs_completion(self, mock_logger):
        """Test that completion is logged."""
        mock_registry = Mock()

        with patch("chuk_mcp_server.cloud.providers.gcp.register_gcp_provider"):
            with patch("chuk_mcp_server.cloud.providers.aws.register_aws_provider"):
                with patch("chuk_mcp_server.cloud.providers.azure.register_azure_provider"):
                    with patch("chuk_mcp_server.cloud.providers.edge.register_edge_providers"):
                        register_all_providers(mock_registry)

                        # Check that completion is logged
                        mock_logger.debug.assert_any_call("Cloud providers registration complete")

    def test_register_all_providers_mixed_success_and_failure(self):
        """Test mixed success and failure scenario."""
        mock_registry = Mock()

        # GCP succeeds, AWS import fails, Azure exception, Edge succeeds
        with patch("chuk_mcp_server.cloud.providers.gcp.register_gcp_provider") as mock_gcp:
            with patch("chuk_mcp_server.cloud.providers.aws.register_aws_provider", side_effect=ImportError("No AWS")):
                with patch(
                    "chuk_mcp_server.cloud.providers.azure.register_azure_provider",
                    side_effect=RuntimeError("Azure error"),
                ):
                    with patch("chuk_mcp_server.cloud.providers.edge.register_edge_providers") as mock_edge:
                        with patch("chuk_mcp_server.cloud.providers.logger") as mock_logger:
                            register_all_providers(mock_registry)

                            # Check successful ones were called
                            mock_gcp.assert_called_once_with(mock_registry)
                            mock_edge.assert_called_once_with(mock_registry)

                            # Check failures were logged appropriately
                            mock_logger.debug.assert_any_call("AWS provider not available: No AWS")
                            mock_logger.error.assert_any_call("Error registering Azure provider: Azure error")
