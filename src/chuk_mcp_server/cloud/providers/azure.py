#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/providers/azure.py
"""
Microsoft Azure Provider
"""

import os
from typing import Any

from ..base import CloudProvider


class AzureProvider(CloudProvider):
    """Microsoft Azure detection and configuration."""

    @property
    def name(self) -> str:
        return "azure"

    @property
    def display_name(self) -> str:
        return "Microsoft Azure"

    def get_priority(self) -> int:
        return 30

    def detect(self) -> bool:
        """Detect if running on Microsoft Azure."""
        # Strong indicators (definitive Azure)
        strong_indicators = [
            "AZURE_FUNCTIONS_ENVIRONMENT",
            "WEBSITE_SITE_NAME",
            "ACI_RESOURCE_GROUP",
        ]

        # Check strong indicators first
        if any(os.environ.get(var) for var in strong_indicators):
            return True

        # Weaker indicators (need multiple matches)
        weak_indicators = [
            "AzureWebJobsScriptRoot",
            "AzureWebJobsStorage",
            "FUNCTIONS_WORKER_RUNTIME",
            "AZURE_CLIENT_ID",
            "AZURE_SUBSCRIPTION_ID",
        ]
        return sum(1 for var in weak_indicators if os.environ.get(var)) >= 2

    def get_environment_type(self) -> str:
        """Determine specific Azure service type."""
        if self._is_azure_functions() or self._is_container_instances():
            return "serverless"
        else:
            return "production"

    def get_service_type(self) -> str:
        """Get specific Azure service type."""
        if self._is_azure_functions():
            runtime = os.environ.get("FUNCTIONS_WORKER_RUNTIME", "")
            return f"azure_functions_{runtime}" if runtime else "azure_functions"
        elif self._is_app_service():
            return "app_service"
        elif self._is_container_instances():
            return "container_instances"
        else:
            return "azure_generic"

    def get_config_overrides(self) -> dict[str, Any]:
        """Get Azure-specific configuration overrides."""
        service_type = self.get_service_type()

        base_config = {
            "cloud_provider": "azure",
            "service_type": service_type,
            "subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID", "unknown"),
        }

        if service_type.startswith("azure_functions"):
            return {**base_config, **self._get_azure_functions_config()}
        elif service_type == "app_service":
            return {**base_config, **self._get_app_service_config()}
        elif service_type == "container_instances":
            return {**base_config, **self._get_container_instances_config()}
        else:
            return base_config

    def _is_azure_functions(self) -> bool:
        """Check if running in Azure Functions."""
        return bool(os.environ.get("AZURE_FUNCTIONS_ENVIRONMENT") or os.environ.get("AzureWebJobsScriptRoot"))  # noqa: SIM112

    def _is_app_service(self) -> bool:
        """Check if running in Azure App Service."""
        return bool(os.environ.get("WEBSITE_SITE_NAME"))

    def _is_container_instances(self) -> bool:
        """Check if running in Azure Container Instances."""
        return bool(os.environ.get("ACI_RESOURCE_GROUP"))

    def _get_azure_functions_config(self) -> dict[str, Any]:
        """Get Azure Functions specific configuration."""
        return {
            "host": "0.0.0.0",  # nosec B104 - Required for Azure Functions runtime
            "port": int(os.environ.get("PORT", 7071)),  # Azure Functions default
            "workers": 1,  # Azure Functions is single-threaded per instance
            "max_connections": 200,  # Conservative for Azure Functions
            "log_level": "WARNING",  # Optimized for performance
            "debug": False,
            "performance_mode": "azure_functions_optimized",
            "worker_runtime": os.environ.get("FUNCTIONS_WORKER_RUNTIME", "python"),
            "extension_version": os.environ.get("FUNCTIONS_EXTENSION_VERSION", "~4"),
            "script_root": os.environ.get("AzureWebJobsScriptRoot", "unknown"),  # noqa: SIM112
        }

    def _get_app_service_config(self) -> dict[str, Any]:
        """Get App Service specific configuration."""
        return {
            "host": "0.0.0.0",  # nosec B104 - Required for Azure App Service runtime
            "port": int(os.environ.get("PORT", 8000)),
            "workers": 4,  # Will be optimized by system detector
            "max_connections": 2000,
            "log_level": "INFO",
            "debug": False,
            "performance_mode": "app_service_optimized",
            "site_name": os.environ.get("WEBSITE_SITE_NAME", "unknown"),
            "resource_group": os.environ.get("WEBSITE_RESOURCE_GROUP", "unknown"),
            "sku": os.environ.get("WEBSITE_SKU", "unknown"),
            "instance_id": os.environ.get("WEBSITE_INSTANCE_ID", "unknown"),
        }

    def _get_container_instances_config(self) -> dict[str, Any]:
        """Get Container Instances specific configuration."""
        return {
            "host": "0.0.0.0",  # nosec B104 - Required for Azure Container Instances runtime
            "port": int(os.environ.get("PORT", 8000)),
            "workers": 2,  # Conservative for ACI
            "max_connections": 1000,
            "log_level": "INFO",
            "debug": False,
            "performance_mode": "aci_optimized",
            "resource_group": os.environ.get("ACI_RESOURCE_GROUP", "unknown"),
        }


def register_azure_provider(registry: Any) -> None:
    """Register Azure provider with the registry."""
    azure_provider = AzureProvider()
    registry.register_provider(azure_provider)
