#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/providers/azure.py
"""
Microsoft Azure Provider
"""

import os
from typing import Any

from ..base import CloudProvider
from ..constants import (
    AZURE_ACI_RESOURCE_GROUP,
    AZURE_CLIENT_ID,
    AZURE_DEFAULT_RUNTIME,
    AZURE_FUNCTIONS_ENVIRONMENT,
    AZURE_FUNCTIONS_EXTENSION_VERSION,
    AZURE_FUNCTIONS_WORKER_RUNTIME,
    AZURE_SUBSCRIPTION_ID,
    AZURE_WEBJOBS_SCRIPT_ROOT,
    AZURE_WEBJOBS_STORAGE,
    AZURE_WEBSITE_INSTANCE_ID,
    AZURE_WEBSITE_RESOURCE_GROUP,
    AZURE_WEBSITE_SITE_NAME,
    AZURE_WEBSITE_SKU,
    CFG_CLOUD_PROVIDER,
    CFG_DEBUG,
    CFG_HOST,
    CFG_LOG_LEVEL,
    CFG_MAX_CONNECTIONS,
    CFG_PERFORMANCE_MODE,
    CFG_PORT,
    CFG_SERVICE_TYPE,
    CFG_SUBSCRIPTION_ID,
    CFG_WORKERS,
    DEFAULT_HOST,
    DEFAULT_PORT_AZURE_FUNCTIONS,
    DEFAULT_PORT_GENERAL,
    DISPLAY_AZURE,
    ENV_PORT,
    ENV_TYPE_PRODUCTION,
    ENV_TYPE_SERVERLESS,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    PERF_ACI_OPTIMIZED,
    PERF_APP_SERVICE_OPTIMIZED,
    PERF_AZURE_FUNCTIONS_OPTIMIZED,
    PROVIDER_AZURE,
    SVC_APP_SERVICE,
    SVC_AZURE_FUNCTIONS,
    SVC_AZURE_GENERIC,
    SVC_CONTAINER_INSTANCES,
)


class AzureProvider(CloudProvider):
    """Microsoft Azure detection and configuration."""

    @property
    def name(self) -> str:
        return PROVIDER_AZURE

    @property
    def display_name(self) -> str:
        return DISPLAY_AZURE

    def get_priority(self) -> int:
        return 30

    def detect(self) -> bool:
        """Detect if running on Microsoft Azure."""
        # Strong indicators (definitive Azure)
        strong_indicators = [
            AZURE_FUNCTIONS_ENVIRONMENT,
            AZURE_WEBSITE_SITE_NAME,
            AZURE_ACI_RESOURCE_GROUP,
        ]

        # Check strong indicators first
        if any(os.environ.get(var) for var in strong_indicators):
            return True

        # Weaker indicators (need multiple matches)
        weak_indicators = [
            AZURE_WEBJOBS_SCRIPT_ROOT,
            AZURE_WEBJOBS_STORAGE,
            AZURE_FUNCTIONS_WORKER_RUNTIME,
            AZURE_CLIENT_ID,
            AZURE_SUBSCRIPTION_ID,
        ]
        return sum(1 for var in weak_indicators if os.environ.get(var)) >= 2

    def get_environment_type(self) -> str:
        """Determine specific Azure service type."""
        if self._is_azure_functions() or self._is_container_instances():
            return ENV_TYPE_SERVERLESS
        else:
            return ENV_TYPE_PRODUCTION

    def get_service_type(self) -> str:
        """Get specific Azure service type."""
        if self._is_azure_functions():
            runtime = os.environ.get(AZURE_FUNCTIONS_WORKER_RUNTIME, "")
            return f"{SVC_AZURE_FUNCTIONS}_{runtime}" if runtime else SVC_AZURE_FUNCTIONS
        elif self._is_app_service():
            return SVC_APP_SERVICE
        elif self._is_container_instances():
            return SVC_CONTAINER_INSTANCES
        else:
            return SVC_AZURE_GENERIC

    def get_config_overrides(self) -> dict[str, Any]:
        """Get Azure-specific configuration overrides."""
        service_type = self.get_service_type()

        base_config = {
            CFG_CLOUD_PROVIDER: PROVIDER_AZURE,
            CFG_SERVICE_TYPE: service_type,
            CFG_SUBSCRIPTION_ID: os.environ.get(AZURE_SUBSCRIPTION_ID, "unknown"),
        }

        if service_type.startswith(SVC_AZURE_FUNCTIONS):
            return {**base_config, **self._get_azure_functions_config()}
        elif service_type == SVC_APP_SERVICE:
            return {**base_config, **self._get_app_service_config()}
        elif service_type == SVC_CONTAINER_INSTANCES:
            return {**base_config, **self._get_container_instances_config()}
        else:
            return base_config

    def _is_azure_functions(self) -> bool:
        """Check if running in Azure Functions."""
        return bool(os.environ.get(AZURE_FUNCTIONS_ENVIRONMENT) or os.environ.get(AZURE_WEBJOBS_SCRIPT_ROOT))  # noqa: SIM112

    def _is_app_service(self) -> bool:
        """Check if running in Azure App Service."""
        return bool(os.environ.get(AZURE_WEBSITE_SITE_NAME))

    def _is_container_instances(self) -> bool:
        """Check if running in Azure Container Instances."""
        return bool(os.environ.get(AZURE_ACI_RESOURCE_GROUP))

    def _get_azure_functions_config(self) -> dict[str, Any]:
        """Get Azure Functions specific configuration."""
        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for Azure Functions runtime
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_AZURE_FUNCTIONS)),  # Azure Functions default
            CFG_WORKERS: 1,  # Azure Functions is single-threaded per instance
            CFG_MAX_CONNECTIONS: 200,  # Conservative for Azure Functions
            CFG_LOG_LEVEL: LOG_LEVEL_WARNING,  # Optimized for performance
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_AZURE_FUNCTIONS_OPTIMIZED,
            "worker_runtime": os.environ.get(AZURE_FUNCTIONS_WORKER_RUNTIME, AZURE_DEFAULT_RUNTIME),
            "extension_version": os.environ.get(AZURE_FUNCTIONS_EXTENSION_VERSION, "~4"),
            "script_root": os.environ.get(AZURE_WEBJOBS_SCRIPT_ROOT, "unknown"),  # noqa: SIM112
        }

    def _get_app_service_config(self) -> dict[str, Any]:
        """Get App Service specific configuration."""
        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for Azure App Service runtime
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_GENERAL)),
            CFG_WORKERS: 4,  # Will be optimized by system detector
            CFG_MAX_CONNECTIONS: 2000,
            CFG_LOG_LEVEL: LOG_LEVEL_INFO,
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_APP_SERVICE_OPTIMIZED,
            "site_name": os.environ.get(AZURE_WEBSITE_SITE_NAME, "unknown"),
            "resource_group": os.environ.get(AZURE_WEBSITE_RESOURCE_GROUP, "unknown"),
            "sku": os.environ.get(AZURE_WEBSITE_SKU, "unknown"),
            "instance_id": os.environ.get(AZURE_WEBSITE_INSTANCE_ID, "unknown"),
        }

    def _get_container_instances_config(self) -> dict[str, Any]:
        """Get Container Instances specific configuration."""
        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for Azure Container Instances runtime
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_GENERAL)),
            CFG_WORKERS: 2,  # Conservative for ACI
            CFG_MAX_CONNECTIONS: 1000,
            CFG_LOG_LEVEL: LOG_LEVEL_INFO,
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_ACI_OPTIMIZED,
            "resource_group": os.environ.get(AZURE_ACI_RESOURCE_GROUP, "unknown"),
        }


def register_azure_provider(registry: Any) -> None:
    """Register Azure provider with the registry."""
    azure_provider = AzureProvider()
    registry.register_provider(azure_provider)
