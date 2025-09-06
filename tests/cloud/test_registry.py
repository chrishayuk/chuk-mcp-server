#!/usr/bin/env python3
"""Tests for cloud/registry.py module."""

from unittest.mock import Mock, patch

from chuk_mcp_server.cloud.base import CloudProvider
from chuk_mcp_server.cloud.registry import CloudDetectionRegistry


class MockProvider(CloudProvider):
    """Mock cloud provider for testing."""

    def __init__(self, name="mock", display_name="Mock Provider", should_detect=False):
        self._name = name
        self._display_name = display_name
        self._should_detect = should_detect

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return self._display_name

    def detect(self) -> bool:
        return self._should_detect

    def get_config_overrides(self) -> dict:
        return {"mock_config": True}

    def get_environment_type(self) -> str:
        return "mock-env"


class TestCloudDetectionRegistry:
    """Test the CloudDetectionRegistry class."""

    def test_initialization(self):
        """Test registry initialization."""
        registry = CloudDetectionRegistry()
        assert registry._providers == {}
        assert registry._detection_cache is None

    def test_register_provider(self):
        """Test registering a cloud provider."""
        registry = CloudDetectionRegistry()
        provider = MockProvider()

        registry.register_provider(provider)

        assert len(registry._providers) == 1
        assert registry._providers[provider.name] == provider

    def test_register_provider_clears_cache(self):
        """Test that registering a provider clears the detection cache."""
        registry = CloudDetectionRegistry()

        # Set up a cached detection
        provider1 = MockProvider("p1", "Provider 1", should_detect=True)
        registry.register_provider(provider1)

        # Trigger cache
        detected = registry.detect_provider()
        assert detected == provider1
        assert registry._detection_cache == provider1

        # Register new provider should clear cache
        provider2 = MockProvider("p2", "Provider 2")
        registry.register_provider(provider2)
        assert registry._detection_cache is None

    def test_detect_provider_no_providers(self):
        """Test detection when no providers are registered."""
        registry = CloudDetectionRegistry()
        detected = registry.detect_provider()
        assert detected is None

    def test_detect_provider_single_match(self):
        """Test detection with single matching provider."""
        registry = CloudDetectionRegistry()
        provider = MockProvider(should_detect=True)
        registry.register_provider(provider)

        detected = registry.detect_provider()
        assert detected == provider

    def test_detect_provider_multiple_providers_first_matches(self):
        """Test detection with multiple providers, first matches."""
        registry = CloudDetectionRegistry()
        provider1 = MockProvider("p1", "Provider 1", should_detect=True)
        provider2 = MockProvider("p2", "Provider 2", should_detect=False)
        provider3 = MockProvider("p3", "Provider 3", should_detect=True)

        registry.register_provider(provider1)
        registry.register_provider(provider2)
        registry.register_provider(provider3)

        detected = registry.detect_provider()
        # Should return the first matching provider
        assert detected == provider1

    def test_detect_provider_no_matches(self):
        """Test detection when no providers match."""
        registry = CloudDetectionRegistry()
        provider1 = MockProvider("p1", "Provider 1", should_detect=False)
        provider2 = MockProvider("p2", "Provider 2", should_detect=False)

        registry.register_provider(provider1)
        registry.register_provider(provider2)

        detected = registry.detect_provider()
        assert detected is None

    def test_detect_provider_caching(self):
        """Test that detection result is cached."""
        registry = CloudDetectionRegistry()

        # Create a provider with side effects to track calls
        provider = MockProvider(should_detect=True)
        provider.detect = Mock(return_value=True)

        registry.register_provider(provider)

        # First detection
        detected1 = registry.detect_provider()
        assert detected1 == provider
        assert provider.detect.call_count == 1

        # Second detection should use cache
        detected2 = registry.detect_provider()
        assert detected2 == provider
        assert provider.detect.call_count == 1  # Should not be called again

    def test_detect_provider_with_logging(self):
        """Test detection with logging."""
        registry = CloudDetectionRegistry()
        provider = MockProvider(should_detect=True)
        registry.register_provider(provider)

        with patch("chuk_mcp_server.cloud.registry.logger") as mock_logger:
            detected = registry.detect_provider()
            assert detected == provider
            # Check that info logging was called for successful detection
            mock_logger.info.assert_called()

    def test_detect_provider_exception_handling(self):
        """Test that exceptions in detect() are handled."""
        registry = CloudDetectionRegistry()

        # Create a provider that raises an exception
        provider = MockProvider()
        provider.detect = Mock(side_effect=Exception("Detection failed"))

        registry.register_provider(provider)

        with patch("chuk_mcp_server.cloud.registry.logger") as mock_logger:
            detected = registry.detect_provider()
            assert detected is None
            # Check that error was logged
            mock_logger.debug.assert_called()

    def test_list_providers(self):
        """Test listing registered providers."""
        registry = CloudDetectionRegistry()

        provider1 = MockProvider("p1", "Provider 1")
        provider2 = MockProvider("p2", "Provider 2")

        registry.register_provider(provider1)
        registry.register_provider(provider2)

        providers = registry.list_providers()
        assert len(providers) == 2
        assert provider1 in providers
        assert provider2 in providers

    def test_list_providers_empty(self):
        """Test listing providers when none are registered."""
        registry = CloudDetectionRegistry()
        providers = registry.list_providers()
        assert providers == []

    def test_clear_cache(self):
        """Test clearing the detection cache."""
        registry = CloudDetectionRegistry()
        provider = MockProvider(should_detect=True)
        registry.register_provider(provider)

        # Trigger cache
        registry.detect_provider()
        assert registry._detection_cache == provider

        # Clear cache
        registry.clear_cache()
        assert registry._detection_cache is None

    def test_priority_ordering(self):
        """Test that providers are checked in registration order."""
        registry = CloudDetectionRegistry()

        # All providers detect as True
        provider1 = MockProvider("p1", "Provider 1", should_detect=True)
        provider2 = MockProvider("p2", "Provider 2", should_detect=True)
        provider3 = MockProvider("p3", "Provider 3", should_detect=True)

        # Register in specific order
        registry.register_provider(provider2)
        registry.register_provider(provider1)
        registry.register_provider(provider3)

        detected = registry.detect_provider()
        # Should return provider2 as it was registered first
        assert detected == provider2

    def test_thread_safety_consideration(self):
        """Test that registry handles concurrent access safely."""
        import threading

        registry = CloudDetectionRegistry()
        results = []

        def register_and_detect(provider):
            registry.register_provider(provider)
            detected = registry.detect_provider()
            results.append(detected)

        providers = [MockProvider(f"p{i}", f"Provider {i}", should_detect=True) for i in range(5)]

        threads = [threading.Thread(target=register_and_detect, args=(p,)) for p in providers]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All threads should have completed
        assert len(results) == 5
        # At least one should have detected something
        assert any(r is not None for r in results)

    def test_get_provider(self):
        """Test getting a specific provider by name."""
        registry = CloudDetectionRegistry()

        # Try to get non-existent provider
        assert registry.get_provider("nonexistent") is None

        # Register a provider and get it
        provider = MockProvider("test", "Test Provider")
        registry.register_provider(provider)

        retrieved = registry.get_provider("test")
        assert retrieved == provider
        assert retrieved.name == "test"

    def test_get_registry_info(self):
        """Test getting registry information."""
        registry = CloudDetectionRegistry()

        # Register some providers
        provider1 = MockProvider("p1", "Provider 1", should_detect=False)
        provider2 = MockProvider("p2", "Provider 2", should_detect=True)
        registry.register_provider(provider1)
        registry.register_provider(provider2)

        # Get registry info
        info = registry.get_registry_info()

        # Check structure
        assert "total_providers" in info
        assert "provider_names" in info
        assert "current_detection" in info
        assert "cache_status" in info

        assert info["total_providers"] == 2
        assert set(info["provider_names"]) == {"p1", "p2"}

        # Current detection should find p2
        assert info["current_detection"]["provider"] == "p2"
        assert info["current_detection"]["display_name"] == "Provider 2"
        assert info["current_detection"]["service_type"] == "mock-env"  # Returns get_environment_type() by default

        # Cache should be populated after detection
        assert info["cache_status"]["cached"] is True
        assert info["cache_status"]["cached_provider"] == "p2"

    def test_get_registry_info_no_detection(self):
        """Test registry info when no provider is detected."""
        registry = CloudDetectionRegistry()

        # Register non-detecting provider
        provider = MockProvider("p1", "Provider 1", should_detect=False)
        registry.register_provider(provider)

        info = registry.get_registry_info()

        assert info["total_providers"] == 1
        assert info["provider_names"] == ["p1"]
        assert info["current_detection"]["provider"] is None
        assert info["current_detection"]["display_name"] is None
        assert info["current_detection"]["service_type"] is None
        assert info["cache_status"]["cached"] is False
        assert info["cache_status"]["cached_provider"] is None
