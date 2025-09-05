#!/usr/bin/env python3
"""Tests for cloud/base.py module."""

import pytest

from chuk_mcp_server.cloud.base import CloudProvider


class TestCloudProvider:
    """Test the CloudProvider base class."""

    def test_cloud_provider_is_abstract(self):
        """Test that CloudProvider cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            CloudProvider()

    def test_cloud_provider_subclass(self):
        """Test creating a valid CloudProvider subclass."""

        class TestProvider(CloudProvider):
            @property
            def name(self) -> str:
                return "test"

            @property
            def display_name(self) -> str:
                return "Test Provider"

            def detect(self) -> bool:
                return True

            def get_config_overrides(self) -> dict:
                return {"test": True}

            def get_environment_type(self) -> str:
                return "test-env"

        provider = TestProvider()
        assert provider.name == "test"
        assert provider.display_name == "Test Provider"
        assert provider.detect() is True
        assert provider.get_config_overrides() == {"test": True}
        # get_service_type() is not abstract, it has a default implementation
        assert provider.get_service_type() == "test-env"  # Returns get_environment_type() by default
        assert provider.get_environment_type() == "test-env"

    def test_cloud_provider_missing_abstract_methods(self):
        """Test that subclass must implement all abstract methods."""

        class IncompleteProvider(CloudProvider):
            @property
            def name(self) -> str:
                return "incomplete"

            @property
            def display_name(self) -> str:
                return "Incomplete Provider"

            def detect(self) -> bool:
                return True

            # Missing get_config_overrides and get_environment_type

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteProvider()

    def test_cloud_provider_attributes(self):
        """Test that CloudProvider requires name and display_name as abstract properties."""

        # Provider missing name property should fail to instantiate
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):

            class ProviderMissingName(CloudProvider):
                @property
                def display_name(self) -> str:
                    return "No Name Provider"

                def detect(self) -> bool:
                    return True

                def get_config_overrides(self) -> dict:
                    return {}

                def get_environment_type(self) -> str:
                    return "env"

            ProviderMissingName()

        # Provider missing display_name property should fail to instantiate
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):

            class ProviderMissingDisplayName(CloudProvider):
                @property
                def name(self) -> str:
                    return "no-display"

                def detect(self) -> bool:
                    return True

                def get_config_overrides(self) -> dict:
                    return {}

                def get_environment_type(self) -> str:
                    return "env"

            ProviderMissingDisplayName()

    def test_cloud_provider_return_types(self):
        """Test that CloudProvider methods return correct types."""

        class TypeTestProvider(CloudProvider):
            @property
            def name(self) -> str:
                return "typetest"

            @property
            def display_name(self) -> str:
                return "Type Test Provider"

            def detect(self) -> bool:
                return "not a bool"  # type: ignore

            def get_config_overrides(self) -> dict:
                return "not a dict"  # type: ignore

            def get_environment_type(self) -> str:
                return None  # type: ignore

        provider = TypeTestProvider()
        # These should work at runtime even with wrong types
        # (Python doesn't enforce type hints at runtime)
        assert provider.detect() == "not a bool"
        assert provider.get_config_overrides() == "not a dict"
        # get_service_type returns get_environment_type by default
        assert provider.get_service_type() is None
        assert provider.get_environment_type() is None
