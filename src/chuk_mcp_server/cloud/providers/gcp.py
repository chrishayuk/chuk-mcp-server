#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/providers/gcp.py
"""
Google Cloud Platform Provider
"""

import os
from typing import Any

from ..base import CloudProvider


class GCPProvider(CloudProvider):
    """Google Cloud Platform detection and configuration."""

    @property
    def name(self) -> str:
        return "gcp"

    @property
    def display_name(self) -> str:
        return "Google Cloud Platform"

    def get_priority(self) -> int:
        return 10

    def detect(self) -> bool:
        """Detect if running on Google Cloud Platform."""
        gcp_indicators = [
            # Cloud Functions
            "GOOGLE_CLOUD_FUNCTION_NAME",  # Gen 1
            "FUNCTION_NAME",  # Gen 2
            "FUNCTION_TARGET",  # Gen 2
            # Cloud Run
            "K_SERVICE",
            "K_CONFIGURATION",
            "K_REVISION",
            # App Engine
            "GAE_APPLICATION",
            "GAE_DEPLOYMENT_ID",
            "GAE_ENV",
            "GAE_INSTANCE",
            "GAE_MEMORY_MB",
            "GAE_RUNTIME",
            "GAE_SERVICE",
            "GAE_VERSION",
            # Compute Engine
            "GCE_METADATA_TIMEOUT",
            # General GCP
            "GOOGLE_CLOUD_PROJECT",
            "GCLOUD_PROJECT",
            "GCP_PROJECT",
        ]

        return any(os.environ.get(var) for var in gcp_indicators)

    def get_environment_type(self) -> str:
        """Determine specific GCP service type."""
        if self._is_cloud_functions() or self._is_cloud_run() or self._is_app_engine():
            return "serverless"
        elif self._is_compute_engine():
            return "production"
        else:
            return "production"  # Generic GCP

    def get_service_type(self) -> str:
        """Get specific GCP service type."""
        if self._is_cloud_functions():
            if os.environ.get("GOOGLE_CLOUD_FUNCTION_NAME"):
                return "gcf_gen1"
            else:
                return "gcf_gen2"
        elif self._is_cloud_run():
            return "cloud_run"
        elif self._is_app_engine():
            if os.environ.get("GAE_ENV") == "standard":
                return "gae_standard"
            else:
                return "gae_flexible"
        elif self._is_compute_engine():
            return "gce"
        else:
            return "gcp_generic"

    def get_config_overrides(self) -> dict[str, Any]:
        """Get GCP-specific configuration overrides."""
        service_type = self.get_service_type()

        base_config = {
            "cloud_provider": "gcp",
            "service_type": service_type,
            "project_id": self._get_project_id(),
        }

        if service_type.startswith("gcf_"):
            return {**base_config, **self._get_cloud_functions_config()}
        elif service_type == "cloud_run":
            return {**base_config, **self._get_cloud_run_config()}
        elif service_type.startswith("gae_"):
            return {**base_config, **self._get_app_engine_config()}
        elif service_type == "gce":
            return {**base_config, **self._get_compute_engine_config()}
        else:
            return base_config

    def _is_cloud_functions(self) -> bool:
        """Check if running in Cloud Functions."""
        return bool(
            os.environ.get("GOOGLE_CLOUD_FUNCTION_NAME")
            or os.environ.get("FUNCTION_NAME")
            or os.environ.get("FUNCTION_TARGET")
        )

    def _is_cloud_run(self) -> bool:
        """Check if running in Cloud Run."""
        return bool(os.environ.get("K_SERVICE"))

    def _is_app_engine(self) -> bool:
        """Check if running in App Engine."""
        return bool(os.environ.get("GAE_APPLICATION"))

    def _is_compute_engine(self) -> bool:
        """Check if running in Compute Engine."""
        # This is harder to detect definitively
        return bool(os.environ.get("GCE_METADATA_TIMEOUT"))

    def _get_project_id(self) -> str:
        """Get GCP project ID."""
        return (
            os.environ.get("GOOGLE_CLOUD_PROJECT")
            or os.environ.get("GCLOUD_PROJECT")
            or os.environ.get("GCP_PROJECT")
            or "unknown"
        )

    def _get_cloud_functions_config(self) -> dict[str, Any]:
        """Get Cloud Functions specific configuration."""
        return {
            "host": "0.0.0.0",  # nosec B104 - Required for GCP Cloud Functions runtime
            "port": int(os.environ.get("PORT", 8080)),
            "workers": 1,  # Cloud Functions is single-threaded
            "max_connections": min(int(os.environ.get("FUNCTION_MEMORY_MB", 512)) // 100 * 10, 1000),
            "log_level": "WARNING",  # Optimized for performance
            "debug": False,
            "performance_mode": self._get_gcf_performance_mode(),
            "timeout_sec": int(os.environ.get("FUNCTION_TIMEOUT_SEC", 60)),
            "memory_mb": int(os.environ.get("FUNCTION_MEMORY_MB", 512)),
            "function_name": os.environ.get("FUNCTION_NAME", os.environ.get("GOOGLE_CLOUD_FUNCTION_NAME", "unknown")),
        }

    def _get_cloud_run_config(self) -> dict[str, Any]:
        """Get Cloud Run specific configuration."""
        return {
            "host": "0.0.0.0",  # nosec B104 - Required for GCP Cloud Run runtime
            "port": int(os.environ.get("PORT", 8080)),
            "workers": min(int(os.environ.get("CLOUD_RUN_CPU", 1)) * 2, 8),
            "max_connections": int(os.environ.get("CLOUD_RUN_CONCURRENCY", 1000)),
            "log_level": "INFO",
            "debug": False,
            "performance_mode": "cloud_run_optimized",
            "service_name": os.environ.get("K_SERVICE", "unknown"),
            "revision": os.environ.get("K_REVISION", "unknown"),
        }

    def _get_app_engine_config(self) -> dict[str, Any]:
        """Get App Engine specific configuration."""
        return {
            "host": "0.0.0.0",  # nosec B104 - Required for GCP App Engine runtime
            "port": int(os.environ.get("PORT", 8080)),
            "workers": 1 if os.environ.get("GAE_ENV") == "standard" else 4,
            "max_connections": 1000,
            "log_level": "INFO",
            "debug": False,
            "performance_mode": "app_engine_optimized",
            "gae_application": os.environ.get("GAE_APPLICATION", "unknown"),
            "gae_service": os.environ.get("GAE_SERVICE", "default"),
            "gae_version": os.environ.get("GAE_VERSION", "unknown"),
            "gae_runtime": os.environ.get("GAE_RUNTIME", "unknown"),
        }

    def _get_compute_engine_config(self) -> dict[str, Any]:
        """Get Compute Engine specific configuration."""
        return {
            "host": "0.0.0.0",  # nosec B104 - Required for GCP Compute Engine load balancer
            "port": int(os.environ.get("PORT", 8000)),
            "workers": 4,  # Will be optimized by system detector
            "max_connections": 5000,
            "log_level": "INFO",
            "debug": False,
            "performance_mode": "gce_optimized",
        }

    def _get_gcf_performance_mode(self) -> str:
        """Get Cloud Functions performance mode based on memory."""
        memory_mb = int(os.environ.get("FUNCTION_MEMORY_MB", 512))

        if memory_mb >= 2048:  # 2GB+
            return "gcf_high_memory"
        elif memory_mb >= 1024:  # 1GB+
            return "gcf_standard"
        else:  # < 1GB
            return "gcf_minimal"


# Manual registration function (called by providers/__init__.py)
def register_gcp_provider(registry: Any) -> None:
    """Register GCP provider with the registry."""
    gcp_provider = GCPProvider()
    registry.register_provider(gcp_provider)
