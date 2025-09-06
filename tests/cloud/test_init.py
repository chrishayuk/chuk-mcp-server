#!/usr/bin/env python3
"""Tests for cloud/__init__.py module."""

import os
from unittest.mock import patch

from chuk_mcp_server.cloud import (
    CloudProvider,
    clear_cloud_cache,
    cloud_registry,
    detect_cloud_provider,
    force_reload_providers,
    get_cloud_config,
    get_cloud_info,
    get_cloud_summary,
    is_cloud_environment,
    list_cloud_providers,
    register_cloud_provider,
)


class TestCloudInit:
    """Test the cloud module initialization and public API."""

    def test_cloud_registry_exists(self):
        """Test that global cloud registry exists."""
        assert cloud_registry is not None
        from chuk_mcp_server.cloud.registry import CloudDetectionRegistry

        assert isinstance(cloud_registry, CloudDetectionRegistry)

    def test_providers_registered_on_import(self):
        """Test that providers are registered on module import."""
        providers = cloud_registry.list_providers()
        assert len(providers) > 0

        # Check that specific providers are registered
        provider_names = [p.name for p in providers]
        assert "aws" in provider_names
        assert "gcp" in provider_names
        assert "azure" in provider_names
        assert "vercel" in provider_names
        assert "netlify" in provider_names
        assert "cloudflare" in provider_names

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_cloud_provider_no_cloud(self):
        """Test cloud detection when not in cloud."""
        clear_cloud_cache()
        provider = detect_cloud_provider()
        assert provider is None

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test-func"})
    def test_detect_cloud_provider_aws(self):
        """Test cloud detection for AWS."""
        clear_cloud_cache()
        provider = detect_cloud_provider()
        assert provider is not None
        assert provider.name == "aws"

    @patch.dict(os.environ, {"VERCEL": "1"})
    def test_detect_cloud_provider_vercel(self):
        """Test cloud detection for Vercel."""
        clear_cloud_cache()
        provider = detect_cloud_provider()
        assert provider is not None
        assert provider.name == "vercel"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_cloud_config_no_cloud(self):
        """Test getting config when not in cloud."""
        clear_cloud_cache()
        config = get_cloud_config()
        assert config == {}

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test-func"})
    def test_get_cloud_config_with_cloud(self):
        """Test getting config when in cloud."""
        clear_cloud_cache()
        config = get_cloud_config()
        assert config is not None
        assert "cloud_provider" in config
        assert config["cloud_provider"] == "aws"

    def test_register_cloud_provider(self):
        """Test registering a custom cloud provider."""

        class CustomProvider(CloudProvider):
            @property
            def name(self) -> str:
                return "custom"

            @property
            def display_name(self) -> str:
                return "Custom Provider"

            def detect(self) -> bool:
                return os.environ.get("CUSTOM_CLOUD") == "1"

            def get_config_overrides(self) -> dict:
                return {"custom": True}

            def get_environment_type(self) -> str:
                return "custom"

        # Store initial count
        initial_count = len(cloud_registry.list_providers())

        # Register custom provider
        provider = CustomProvider()
        register_cloud_provider(provider)

        # Check it was registered
        assert len(cloud_registry.list_providers()) == initial_count + 1
        assert cloud_registry.get_provider("custom") == provider

        # Test detection with custom provider
        with patch.dict(os.environ, {"CUSTOM_CLOUD": "1"}):
            clear_cloud_cache()
            detected = detect_cloud_provider()
            assert detected is not None
            assert detected.name == "custom"

    @patch.dict(os.environ, {}, clear=True)
    def test_is_cloud_environment_false(self):
        """Test is_cloud_environment when not in cloud."""
        clear_cloud_cache()
        assert is_cloud_environment() is False

    @patch.dict(os.environ, {"K_SERVICE": "test-service"})
    def test_is_cloud_environment_true(self):
        """Test is_cloud_environment when in cloud."""
        clear_cloud_cache()
        assert is_cloud_environment() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_get_cloud_summary_no_cloud(self):
        """Test getting cloud summary when not in cloud."""
        clear_cloud_cache()
        summary = get_cloud_summary()
        assert summary == {"detected": False}

    @patch.dict(os.environ, {"FUNCTION_NAME": "test-func", "GOOGLE_CLOUD_PROJECT": "test-proj"})
    def test_get_cloud_summary_with_cloud(self):
        """Test getting cloud summary when in cloud."""
        clear_cloud_cache()
        summary = get_cloud_summary()
        assert summary["detected"] is True
        assert summary["provider"] == "gcp"
        assert summary["display_name"] == "Google Cloud Platform"
        assert "service_type" in summary
        assert "environment_type" in summary
        assert "config_overrides" in summary

    def test_list_cloud_providers(self):
        """Test listing all cloud providers."""
        providers = list_cloud_providers()
        assert isinstance(providers, list)
        assert len(providers) > 0

        # Check structure of provider info
        for provider in providers:
            assert "name" in provider
            assert "display_name" in provider
            assert "detected" in provider
            assert isinstance(provider["detected"], bool)

    @patch.dict(os.environ, {"NETLIFY": "true"})
    def test_list_cloud_providers_with_detection(self):
        """Test listing providers shows correct detection."""
        clear_cloud_cache()
        providers = list_cloud_providers()

        # Find netlify provider
        netlify = next((p for p in providers if p["name"] == "netlify"), None)
        assert netlify is not None
        assert netlify["detected"] is True

        # Others should be false
        aws = next((p for p in providers if p["name"] == "aws"), None)
        assert aws is not None
        assert aws["detected"] is False

    @patch.dict(os.environ, {}, clear=True)
    def test_get_cloud_info(self):
        """Test getting comprehensive cloud information."""
        clear_cloud_cache()
        info = get_cloud_info()

        assert "current_detection" in info
        assert "available_providers" in info
        assert "registry_stats" in info

        assert info["current_detection"]["detected"] is False
        assert len(info["available_providers"]) > 0
        assert info["registry_stats"]["total_providers"] > 0
        assert info["registry_stats"]["providers_loaded"] is True

    def test_clear_cloud_cache(self):
        """Test clearing cloud detection cache."""
        # Trigger detection to populate cache
        with patch.dict(os.environ, {"CF_PAGES": "1"}):
            provider = detect_cloud_provider()
            assert provider is not None
            assert cloud_registry._detection_cache is not None

            # Clear cache
            clear_cloud_cache()
            assert cloud_registry._detection_cache is None

    def test_force_reload_providers(self):
        """Test force reloading providers."""
        # Get initial provider count
        initial_providers = cloud_registry.list_providers()
        initial_count = len(initial_providers)
        assert initial_count > 0

        # Force reload
        force_reload_providers()

        # Should have same number of core providers after reload
        new_providers = cloud_registry.list_providers()
        new_count = len(new_providers)

        # Count should be at least 6 (aws, gcp, azure, vercel, netlify, cloudflare)
        assert new_count >= 6

        # Cache should be cleared
        assert cloud_registry._detection_cache is None

    def test_register_providers_idempotent(self):
        """Test that _register_providers is idempotent."""
        from chuk_mcp_server.cloud import _register_providers

        # Get initial count
        initial_count = len(cloud_registry.list_providers())

        # Call register again
        _register_providers()

        # Count should be the same
        assert len(cloud_registry.list_providers()) == initial_count

    @patch("chuk_mcp_server.cloud.logger")
    def test_register_providers_handles_import_errors(self, mock_logger):
        """Test that _register_providers handles import errors gracefully."""
        from chuk_mcp_server.cloud import _register_providers

        # Clear providers first
        cloud_registry._providers.clear()

        # Mock an import error for one provider
        with patch("chuk_mcp_server.cloud.providers.aws.AWSProvider", side_effect=ImportError("Test error")):
            _register_providers()

            # Should still register other providers
            assert len(cloud_registry.list_providers()) > 0

            # Should log debug message about failed registration
            # Note: This would need actual verification of logger calls

    def test_module_exports(self):
        """Test that all exported functions exist."""
        from chuk_mcp_server import cloud

        expected_exports = [
            "CloudProvider",
            "cloud_registry",
            "detect_cloud_provider",
            "get_cloud_config",
            "register_cloud_provider",
            "is_cloud_environment",
            "get_cloud_summary",
            "list_cloud_providers",
            "get_cloud_info",
            "clear_cloud_cache",
            "force_reload_providers",
        ]

        for export in expected_exports:
            assert hasattr(cloud, export), f"Missing export: {export}"

    def test_cloud_provider_priority_ordering(self):
        """Test that providers are detected in priority order."""
        # Edge providers have priority 5 (highest)
        # GCP has priority 10
        # AWS has priority 20
        # Azure has priority 30

        # Set environment variables for multiple providers
        with patch.dict(
            os.environ,
            {
                "VERCEL": "1",  # Priority 5
                "GOOGLE_CLOUD_PROJECT": "test",  # Priority 10
                "AWS_REGION": "us-east-1",  # Priority 20
                "AWS_DEFAULT_REGION": "us-east-1",  # Priority 20
            },
        ):
            clear_cloud_cache()
            provider = detect_cloud_provider()
            # Should detect Vercel first due to highest priority
            assert provider is not None
            assert provider.name == "vercel"
