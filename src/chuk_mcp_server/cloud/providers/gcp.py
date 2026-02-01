#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/providers/gcp.py
"""
Google Cloud Platform Provider
"""

import os
from typing import Any

from ..base import CloudProvider
from ..constants import (
    CFG_CLOUD_PROVIDER,
    CFG_DEBUG,
    CFG_FUNCTION_NAME,
    CFG_HOST,
    CFG_LOG_LEVEL,
    CFG_MAX_CONNECTIONS,
    CFG_MEMORY_MB,
    CFG_PERFORMANCE_MODE,
    CFG_PORT,
    CFG_PROJECT_ID,
    CFG_SERVICE_TYPE,
    CFG_TIMEOUT_SEC,
    CFG_WORKERS,
    DEFAULT_FUNCTION_MEMORY,
    DEFAULT_FUNCTION_TIMEOUT,
    DEFAULT_HOST,
    DEFAULT_PORT_GCP,
    DEFAULT_PORT_GENERAL,
    DISPLAY_GCP,
    ENV_PORT,
    ENV_TYPE_PRODUCTION,
    ENV_TYPE_SERVERLESS,
    GCP_CLOUD_FUNCTION_NAME,
    GCP_CLOUD_PROJECT,
    GCP_CLOUD_RUN_CONCURRENCY,
    GCP_CLOUD_RUN_CPU,
    GCP_FUNCTION_MEMORY_MB,
    GCP_FUNCTION_NAME,
    GCP_FUNCTION_TARGET,
    GCP_FUNCTION_TIMEOUT_SEC,
    GCP_GAE_APPLICATION,
    GCP_GAE_DEPLOYMENT_ID,
    GCP_GAE_ENV,
    GCP_GAE_ENV_STANDARD,
    GCP_GAE_INSTANCE,
    GCP_GAE_MEMORY_MB,
    GCP_GAE_RUNTIME,
    GCP_GAE_SERVICE,
    GCP_GAE_VERSION,
    GCP_GCE_METADATA_TIMEOUT,
    GCP_GCLOUD_PROJECT,
    GCP_K_CONFIGURATION,
    GCP_K_REVISION,
    GCP_K_SERVICE,
    GCP_PROJECT,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    MEMORY_HIGH_THRESHOLD,
    MEMORY_MEDIUM_THRESHOLD,
    PERF_APP_ENGINE_OPTIMIZED,
    PERF_CLOUD_RUN_OPTIMIZED,
    PERF_GCE_OPTIMIZED,
    PERF_GCF_HIGH_MEMORY,
    PERF_GCF_MINIMAL,
    PERF_GCF_STANDARD,
    PROVIDER_GCP,
    SVC_CLOUD_RUN,
    SVC_GAE_FLEXIBLE,
    SVC_GAE_STANDARD,
    SVC_GCE,
    SVC_GCF_GEN1,
    SVC_GCF_GEN2,
    SVC_GCP_GENERIC,
)


class GCPProvider(CloudProvider):
    """Google Cloud Platform detection and configuration."""

    @property
    def name(self) -> str:
        return PROVIDER_GCP

    @property
    def display_name(self) -> str:
        return DISPLAY_GCP

    def get_priority(self) -> int:
        return 10

    def detect(self) -> bool:
        """Detect if running on Google Cloud Platform."""
        gcp_indicators = [
            # Cloud Functions
            GCP_CLOUD_FUNCTION_NAME,  # Gen 1
            GCP_FUNCTION_NAME,  # Gen 2
            GCP_FUNCTION_TARGET,  # Gen 2
            # Cloud Run
            GCP_K_SERVICE,
            GCP_K_CONFIGURATION,
            GCP_K_REVISION,
            # App Engine
            GCP_GAE_APPLICATION,
            GCP_GAE_DEPLOYMENT_ID,
            GCP_GAE_ENV,
            GCP_GAE_INSTANCE,
            GCP_GAE_MEMORY_MB,
            GCP_GAE_RUNTIME,
            GCP_GAE_SERVICE,
            GCP_GAE_VERSION,
            # Compute Engine
            GCP_GCE_METADATA_TIMEOUT,
            # General GCP
            GCP_CLOUD_PROJECT,
            GCP_GCLOUD_PROJECT,
            GCP_PROJECT,
        ]

        return any(os.environ.get(var) for var in gcp_indicators)

    def get_environment_type(self) -> str:
        """Determine specific GCP service type."""
        if self._is_cloud_functions() or self._is_cloud_run() or self._is_app_engine():
            return ENV_TYPE_SERVERLESS
        elif self._is_compute_engine():
            return ENV_TYPE_PRODUCTION
        else:
            return ENV_TYPE_PRODUCTION  # Generic GCP

    def get_service_type(self) -> str:
        """Get specific GCP service type."""
        if self._is_cloud_functions():
            if os.environ.get(GCP_CLOUD_FUNCTION_NAME):
                return SVC_GCF_GEN1
            else:
                return SVC_GCF_GEN2
        elif self._is_cloud_run():
            return SVC_CLOUD_RUN
        elif self._is_app_engine():
            if os.environ.get(GCP_GAE_ENV) == GCP_GAE_ENV_STANDARD:
                return SVC_GAE_STANDARD
            else:
                return SVC_GAE_FLEXIBLE
        elif self._is_compute_engine():
            return SVC_GCE
        else:
            return SVC_GCP_GENERIC

    def get_config_overrides(self) -> dict[str, Any]:
        """Get GCP-specific configuration overrides."""
        service_type = self.get_service_type()

        base_config = {
            CFG_CLOUD_PROVIDER: PROVIDER_GCP,
            CFG_SERVICE_TYPE: service_type,
            CFG_PROJECT_ID: self._get_project_id(),
        }

        if service_type.startswith("gcf_"):
            return {**base_config, **self._get_cloud_functions_config()}
        elif service_type == SVC_CLOUD_RUN:
            return {**base_config, **self._get_cloud_run_config()}
        elif service_type.startswith("gae_"):
            return {**base_config, **self._get_app_engine_config()}
        elif service_type == SVC_GCE:
            return {**base_config, **self._get_compute_engine_config()}
        else:
            return base_config

    def _is_cloud_functions(self) -> bool:
        """Check if running in Cloud Functions."""
        return bool(
            os.environ.get(GCP_CLOUD_FUNCTION_NAME)
            or os.environ.get(GCP_FUNCTION_NAME)
            or os.environ.get(GCP_FUNCTION_TARGET)
        )

    def _is_cloud_run(self) -> bool:
        """Check if running in Cloud Run."""
        return bool(os.environ.get(GCP_K_SERVICE))

    def _is_app_engine(self) -> bool:
        """Check if running in App Engine."""
        return bool(os.environ.get(GCP_GAE_APPLICATION))

    def _is_compute_engine(self) -> bool:
        """Check if running in Compute Engine."""
        # This is harder to detect definitively
        return bool(os.environ.get(GCP_GCE_METADATA_TIMEOUT))

    def _get_project_id(self) -> str:
        """Get GCP project ID."""
        return (
            os.environ.get(GCP_CLOUD_PROJECT)
            or os.environ.get(GCP_GCLOUD_PROJECT)
            or os.environ.get(GCP_PROJECT)
            or "unknown"
        )

    def _get_cloud_functions_config(self) -> dict[str, Any]:
        """Get Cloud Functions specific configuration."""
        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for GCP Cloud Functions runtime
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_GCP)),
            CFG_WORKERS: 1,  # Cloud Functions is single-threaded
            CFG_MAX_CONNECTIONS: min(
                int(os.environ.get(GCP_FUNCTION_MEMORY_MB, DEFAULT_FUNCTION_MEMORY)) // 100 * 10, 1000
            ),
            CFG_LOG_LEVEL: LOG_LEVEL_WARNING,  # Optimized for performance
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: self._get_gcf_performance_mode(),
            CFG_TIMEOUT_SEC: int(os.environ.get(GCP_FUNCTION_TIMEOUT_SEC, DEFAULT_FUNCTION_TIMEOUT)),
            CFG_MEMORY_MB: int(os.environ.get(GCP_FUNCTION_MEMORY_MB, DEFAULT_FUNCTION_MEMORY)),
            CFG_FUNCTION_NAME: os.environ.get(GCP_FUNCTION_NAME, os.environ.get(GCP_CLOUD_FUNCTION_NAME, "unknown")),
        }

    def _get_cloud_run_config(self) -> dict[str, Any]:
        """Get Cloud Run specific configuration."""
        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for GCP Cloud Run runtime
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_GCP)),
            CFG_WORKERS: min(int(os.environ.get(GCP_CLOUD_RUN_CPU, 1)) * 2, 8),
            CFG_MAX_CONNECTIONS: int(os.environ.get(GCP_CLOUD_RUN_CONCURRENCY, 1000)),
            CFG_LOG_LEVEL: LOG_LEVEL_INFO,
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_CLOUD_RUN_OPTIMIZED,
            "service_name": os.environ.get(GCP_K_SERVICE, "unknown"),
            "revision": os.environ.get(GCP_K_REVISION, "unknown"),
        }

    def _get_app_engine_config(self) -> dict[str, Any]:
        """Get App Engine specific configuration."""
        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for GCP App Engine runtime
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_GCP)),
            CFG_WORKERS: 1 if os.environ.get(GCP_GAE_ENV) == GCP_GAE_ENV_STANDARD else 4,
            CFG_MAX_CONNECTIONS: 1000,
            CFG_LOG_LEVEL: LOG_LEVEL_INFO,
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_APP_ENGINE_OPTIMIZED,
            "gae_application": os.environ.get(GCP_GAE_APPLICATION, "unknown"),
            "gae_service": os.environ.get(GCP_GAE_SERVICE, "default"),
            "gae_version": os.environ.get(GCP_GAE_VERSION, "unknown"),
            "gae_runtime": os.environ.get(GCP_GAE_RUNTIME, "unknown"),
        }

    def _get_compute_engine_config(self) -> dict[str, Any]:
        """Get Compute Engine specific configuration."""
        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for GCP Compute Engine load balancer
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_GENERAL)),
            CFG_WORKERS: 4,  # Will be optimized by system detector
            CFG_MAX_CONNECTIONS: 5000,
            CFG_LOG_LEVEL: LOG_LEVEL_INFO,
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_GCE_OPTIMIZED,
        }

    def _get_gcf_performance_mode(self) -> str:
        """Get Cloud Functions performance mode based on memory."""
        memory_mb = int(os.environ.get(GCP_FUNCTION_MEMORY_MB, DEFAULT_FUNCTION_MEMORY))

        if memory_mb >= MEMORY_HIGH_THRESHOLD:  # 2GB+
            return PERF_GCF_HIGH_MEMORY
        elif memory_mb >= MEMORY_MEDIUM_THRESHOLD:  # 1GB+
            return PERF_GCF_STANDARD
        else:  # < 1GB
            return PERF_GCF_MINIMAL


# Manual registration function (called by providers/__init__.py)
def register_gcp_provider(registry: Any) -> None:
    """Register GCP provider with the registry."""
    gcp_provider = GCPProvider()
    registry.register_provider(gcp_provider)
