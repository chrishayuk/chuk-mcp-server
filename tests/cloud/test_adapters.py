#!/usr/bin/env python3
"""Tests for cloud/adapters module."""

from unittest.mock import Mock, patch

import pytest

from chuk_mcp_server.cloud.adapters import (
    CloudAdapter,
    CloudAdapterRegistry,
    adapter_registry,
    auto_setup_cloud_adapter,
    cloud_adapter,
    get_active_cloud_adapter,
    is_cloud_adapted,
)


class TestCloudAdapter:
    """Test the CloudAdapter base class."""

    def test_cloud_adapter_is_abstract(self):
        """Test that CloudAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            CloudAdapter(Mock())

    def test_cloud_adapter_subclass(self):
        """Test creating a valid CloudAdapter subclass."""

        class TestAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        server = Mock()
        adapter = TestAdapter(server)

        assert adapter.server == server
        assert adapter.cloud_provider is None
        assert adapter.is_compatible() is True
        assert adapter.setup() is True
        assert adapter.get_handler() is None
        assert adapter.get_deployment_info() == {}

    def test_cloud_adapter_with_handler(self):
        """Test CloudAdapter with custom handler."""

        class TestAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

            def get_handler(self):
                def handler(event, context):
                    return {"statusCode": 200}

                return handler

        adapter = TestAdapter(Mock())
        handler = adapter.get_handler()
        assert handler is not None
        assert callable(handler)
        assert handler({}, {}) == {"statusCode": 200}

    def test_cloud_adapter_with_deployment_info(self):
        """Test CloudAdapter with deployment info."""

        class TestAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

            def get_deployment_info(self):
                return {"platform": "test", "region": "us-east-1", "runtime": "python3.11"}

        adapter = TestAdapter(Mock())
        info = adapter.get_deployment_info()
        assert info["platform"] == "test"
        assert info["region"] == "us-east-1"
        assert info["runtime"] == "python3.11"


class TestCloudAdapterRegistry:
    """Test the CloudAdapterRegistry class."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = CloudAdapterRegistry()
        assert registry._adapters == {}
        assert registry._active_adapter is None

    def test_register_adapter(self):
        """Test registering an adapter."""
        registry = CloudAdapterRegistry()

        class TestAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        registry.register_adapter("test", TestAdapter)

        assert "test" in registry._adapters
        assert registry._adapters["test"] == TestAdapter

    def test_auto_setup_no_adapters(self):
        """Test auto_setup when no adapters are registered."""
        registry = CloudAdapterRegistry()
        server = Mock()

        adapter = registry.auto_setup(server)
        assert adapter is None
        assert registry._active_adapter is None

    def test_auto_setup_incompatible_adapter(self):
        """Test auto_setup when adapter is not compatible."""
        registry = CloudAdapterRegistry()

        class IncompatibleAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return False

            def setup(self) -> bool:
                return True

        registry.register_adapter("incompatible", IncompatibleAdapter)
        server = Mock()

        adapter = registry.auto_setup(server)
        assert adapter is None
        assert registry._active_adapter is None

    def test_auto_setup_successful(self):
        """Test successful auto_setup."""
        registry = CloudAdapterRegistry()

        class CompatibleAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        registry.register_adapter("compatible", CompatibleAdapter)
        server = Mock()

        adapter = registry.auto_setup(server)
        assert adapter is not None
        assert isinstance(adapter, CompatibleAdapter)
        assert adapter.server == server
        assert registry._active_adapter == adapter

    def test_auto_setup_first_compatible_wins(self):
        """Test that first compatible adapter wins."""
        registry = CloudAdapterRegistry()

        class FirstAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        class SecondAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        registry.register_adapter("first", FirstAdapter)
        registry.register_adapter("second", SecondAdapter)
        server = Mock()

        adapter = registry.auto_setup(server)
        assert adapter is not None
        assert isinstance(adapter, FirstAdapter)

    def test_auto_setup_handles_exceptions(self):
        """Test that auto_setup handles exceptions gracefully."""
        registry = CloudAdapterRegistry()

        class ErrorAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                raise RuntimeError("Test error")

            def setup(self) -> bool:
                return True

        class GoodAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        registry.register_adapter("error", ErrorAdapter)
        registry.register_adapter("good", GoodAdapter)
        server = Mock()

        with patch("chuk_mcp_server.cloud.adapters.logger") as mock_logger:
            adapter = registry.auto_setup(server)
            assert adapter is not None
            assert isinstance(adapter, GoodAdapter)
            # Check that error was logged
            mock_logger.debug.assert_called()

    def test_auto_setup_setup_failure(self):
        """Test when adapter setup fails."""
        registry = CloudAdapterRegistry()

        class FailingAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return False

        registry.register_adapter("failing", FailingAdapter)
        server = Mock()

        with patch("chuk_mcp_server.cloud.adapters.logger") as mock_logger:
            adapter = registry.auto_setup(server)
            assert adapter is None
            assert registry._active_adapter is None
            # Check that warning was logged
            mock_logger.warning.assert_called()

    def test_get_active_adapter(self):
        """Test getting the active adapter."""
        registry = CloudAdapterRegistry()

        # No active adapter initially
        assert registry.get_active_adapter() is None

        # Setup an adapter
        class TestAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        registry.register_adapter("test", TestAdapter)
        registry.auto_setup(Mock())

        active = registry.get_active_adapter()
        assert active is not None
        assert isinstance(active, TestAdapter)

    def test_list_adapters(self):
        """Test listing registered adapters."""
        registry = CloudAdapterRegistry()

        class Adapter1(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        class Adapter2(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        registry.register_adapter("adapter1", Adapter1)
        registry.register_adapter("adapter2", Adapter2)

        adapters = registry.list_adapters()
        assert len(adapters) == 2
        assert "adapter1" in adapters
        assert "adapter2" in adapters
        assert adapters["adapter1"] == Adapter1
        assert adapters["adapter2"] == Adapter2


class TestCloudAdapterDecorator:
    """Test the cloud_adapter decorator."""

    def test_cloud_adapter_decorator(self):
        """Test that cloud_adapter decorator registers the adapter."""
        # Clear existing adapters
        adapter_registry._adapters.clear()

        @cloud_adapter("decorated_test")
        class DecoratedAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        # Check that adapter was registered
        assert "decorated_test" in adapter_registry._adapters
        assert adapter_registry._adapters["decorated_test"] == DecoratedAdapter

    def test_multiple_decorators(self):
        """Test multiple decorated adapters."""
        # Clear existing adapters
        adapter_registry._adapters.clear()

        @cloud_adapter("adapter1")
        class Adapter1(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        @cloud_adapter("adapter2")
        class Adapter2(CloudAdapter):
            def is_compatible(self) -> bool:
                return False

            def setup(self) -> bool:
                return True

        assert "adapter1" in adapter_registry._adapters
        assert "adapter2" in adapter_registry._adapters
        assert len(adapter_registry._adapters) >= 2


class TestIntegrationFunctions:
    """Test the integration functions."""

    def test_auto_setup_cloud_adapter(self):
        """Test auto_setup_cloud_adapter function."""
        # Clear existing adapters and active adapter
        adapter_registry._adapters.clear()
        adapter_registry._active_adapter = None

        @cloud_adapter("test_auto")
        class TestAutoAdapter(CloudAdapter):
            def is_compatible(self) -> bool:
                return True

            def setup(self) -> bool:
                return True

        server = Mock()
        adapter = auto_setup_cloud_adapter(server)

        assert adapter is not None
        assert isinstance(adapter, TestAutoAdapter)
        assert adapter.server == server

    def test_get_active_cloud_adapter(self):
        """Test get_active_cloud_adapter function."""
        # Clear active adapter
        adapter_registry._active_adapter = None

        # No active adapter initially
        assert get_active_cloud_adapter() is None

        # Setup an adapter
        server = Mock()
        auto_setup_cloud_adapter(server)

        # Should have an active adapter now
        active = get_active_cloud_adapter()
        assert active is not None
        assert active.server == server

    def test_is_cloud_adapted(self):
        """Test is_cloud_adapted function."""
        # Clear active adapter
        adapter_registry._active_adapter = None

        # Not adapted initially
        assert is_cloud_adapted() is False

        # Setup an adapter
        auto_setup_cloud_adapter(Mock())

        # Should be adapted now
        assert is_cloud_adapted() is True

    def test_module_exports(self):
        """Test that all exported functions exist."""
        from chuk_mcp_server.cloud import adapters

        expected_exports = [
            "CloudAdapter",
            "CloudAdapterRegistry",
            "adapter_registry",
            "cloud_adapter",
            "auto_setup_cloud_adapter",
            "get_active_cloud_adapter",
            "is_cloud_adapted",
        ]

        for export in expected_exports:
            assert hasattr(adapters, export), f"Missing export: {export}"
