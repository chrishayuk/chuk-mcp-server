#!/usr/bin/env python3
"""Tests for cloud registry decorator."""

from chuk_mcp_server.cloud.base import CloudProvider
from chuk_mcp_server.cloud.registry import cloud_provider


class TestCloudProviderDecorator:
    """Test the cloud_provider decorator."""

    def test_cloud_provider_decorator_basic(self):
        """Test basic cloud_provider decorator."""

        @cloud_provider("test_provider")
        class TestProvider(CloudProvider):
            @property
            def name(self) -> str:
                return self._name

            @property
            def display_name(self) -> str:
                return self._display_name

            def detect(self) -> bool:
                return True

            def get_config_overrides(self) -> dict:
                return {"test": True}

            def get_environment_type(self) -> str:
                return "test"

        # Check that the class has _registry_info
        assert hasattr(TestProvider, "_registry_info")
        name, display_name, priority, instance = TestProvider._registry_info
        assert name == "test_provider"
        assert display_name == "TEST_PROVIDER"  # Default is name.upper()
        assert priority == 100  # Default priority
        assert instance is not None

    def test_cloud_provider_decorator_with_display_name(self):
        """Test cloud_provider decorator with custom display_name."""

        @cloud_provider("my_cloud", display_name="My Cloud Platform")
        class MyCloudProvider(CloudProvider):
            @property
            def name(self) -> str:
                return self._name

            @property
            def display_name(self) -> str:
                return self._display_name

            def detect(self) -> bool:
                return False

            def get_config_overrides(self) -> dict:
                return {}

            def get_environment_type(self) -> str:
                return "custom"

        # Check registry info
        name, display_name, priority, instance = MyCloudProvider._registry_info
        assert name == "my_cloud"
        assert display_name == "My Cloud Platform"
        assert priority == 100

    def test_cloud_provider_decorator_with_priority(self):
        """Test cloud_provider decorator with custom priority."""

        @cloud_provider("high_priority", priority=5)
        class HighPriorityProvider(CloudProvider):
            @property
            def name(self) -> str:
                return self._name

            @property
            def display_name(self) -> str:
                return self._display_name

            def detect(self) -> bool:
                return True

            def get_config_overrides(self) -> dict:
                return {}

            def get_environment_type(self) -> str:
                return "high"

        # Check registry info
        name, display_name, priority, instance = HighPriorityProvider._registry_info
        assert name == "high_priority"
        assert display_name == "HIGH_PRIORITY"
        assert priority == 5

    def test_cloud_provider_decorator_full_params(self):
        """Test cloud_provider decorator with all parameters."""

        @cloud_provider("full", display_name="Full Provider", priority=50)
        class FullProvider(CloudProvider):
            @property
            def name(self) -> str:
                return self._name

            @property
            def display_name(self) -> str:
                return self._display_name

            def detect(self) -> bool:
                return True

            def get_config_overrides(self) -> dict:
                return {"full": True}

            def get_environment_type(self) -> str:
                return "complete"

        # Check registry info
        name, display_name, priority, instance = FullProvider._registry_info
        assert name == "full"
        assert display_name == "Full Provider"
        assert priority == 50

    def test_decorated_instance_properties(self):
        """Test that decorated instance has proper properties."""

        @cloud_provider("prop_test", display_name="Property Test", priority=25)
        class PropTestProvider(CloudProvider):
            @property
            def name(self) -> str:
                return self._name

            @property
            def display_name(self) -> str:
                return self._display_name

            def detect(self) -> bool:
                return True

            def get_config_overrides(self) -> dict:
                return {}

            def get_environment_type(self) -> str:
                return "test"

        # Get the instance from registry info
        _, _, _, instance = PropTestProvider._registry_info

        # Test that the instance has the correct properties
        assert instance.name == "prop_test"
        assert instance.display_name == "Property Test"
        assert instance.get_priority() == 25

    def test_decorated_instance_methods_work(self):
        """Test that decorated instance methods work correctly."""

        @cloud_provider("method_test")
        class MethodTestProvider(CloudProvider):
            @property
            def name(self) -> str:
                return self._name

            @property
            def display_name(self) -> str:
                return self._display_name

            def detect(self) -> bool:
                return True

            def get_config_overrides(self) -> dict:
                return {"method": "test"}

            def get_environment_type(self) -> str:
                return "method_env"

        # Get the instance
        _, _, _, instance = MethodTestProvider._registry_info

        # Test methods
        assert instance.detect() is True
        assert instance.get_config_overrides() == {"method": "test"}
        assert instance.get_environment_type() == "method_env"
        assert instance.get_service_type() == "method_env"  # Default implementation

    def test_decorator_doesnt_override_existing_registry_info(self):
        """Test that decorator doesn't override existing _registry_info."""

        @cloud_provider("first")
        class TestProvider(CloudProvider):
            @property
            def name(self) -> str:
                return self._name

            @property
            def display_name(self) -> str:
                return self._display_name

            def detect(self) -> bool:
                return True

            def get_config_overrides(self) -> dict:
                return {}

            def get_environment_type(self) -> str:
                return "test"

        # Store original registry info
        original_info = TestProvider._registry_info

        # Try to decorate again (simulating re-import)
        @cloud_provider("second")
        class TestProvider(CloudProvider):  # noqa: F811
            _registry_info = original_info  # Pre-existing registry info

            @property
            def name(self) -> str:
                return self._name

            @property
            def display_name(self) -> str:
                return self._display_name

            def detect(self) -> bool:
                return True

            def get_config_overrides(self) -> dict:
                return {}

            def get_environment_type(self) -> str:
                return "test"

        # Should still have original info
        assert TestProvider._registry_info == original_info

    def test_multiple_decorators_different_classes(self):
        """Test multiple decorators on different classes."""

        @cloud_provider("provider1", priority=10)
        class Provider1(CloudProvider):
            @property
            def name(self) -> str:
                return self._name

            @property
            def display_name(self) -> str:
                return self._display_name

            def detect(self) -> bool:
                return True

            def get_config_overrides(self) -> dict:
                return {"p1": True}

            def get_environment_type(self) -> str:
                return "env1"

        @cloud_provider("provider2", priority=20)
        class Provider2(CloudProvider):
            @property
            def name(self) -> str:
                return self._name

            @property
            def display_name(self) -> str:
                return self._display_name

            def detect(self) -> bool:
                return False

            def get_config_overrides(self) -> dict:
                return {"p2": True}

            def get_environment_type(self) -> str:
                return "env2"

        # Check both have their own registry info
        p1_info = Provider1._registry_info
        p2_info = Provider2._registry_info

        assert p1_info[0] == "provider1"
        assert p1_info[2] == 10
        assert p2_info[0] == "provider2"
        assert p2_info[2] == 20

        # Check instances are different
        assert p1_info[3] is not p2_info[3]
        assert p1_info[3].detect() is True
        assert p2_info[3].detect() is False
