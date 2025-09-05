#!/usr/bin/env python3
# src/chuk_mcp_server/config/cloud_detector.py
"""
Cloud detector that uses providers from the cloud module.
"""

import logging
from typing import Any

from .base import ConfigDetector

logger = logging.getLogger(__name__)


class CloudDetector(ConfigDetector):
    """Detects cloud providers and their configurations."""

    def __init__(self):
        super().__init__()
        self._detected_provider = None
        self._cloud_registry = None

    def detect(self):
        """Detect the current cloud provider."""
        if self._detected_provider is not None:
            return self._detected_provider

        try:
            # Import cloud registry from cloud module
            from ..cloud import cloud_registry

            self._cloud_registry = cloud_registry

            provider = cloud_registry.detect_provider()
            if provider:
                self.logger.info(f"🌟 Detected cloud provider: {provider.display_name}")
                self._detected_provider = provider
                return provider
            else:
                self.logger.debug("No cloud provider detected")
                self._detected_provider = None
                return None

        except ImportError as e:
            self.logger.debug(f"Cloud module not available: {e}")
            self._detected_provider = None
            return None

    def get_provider(self):
        """Get the detected cloud provider."""
        return self.detect()

    def get_config_overrides(self) -> dict[str, Any]:
        """Get cloud-specific configuration overrides."""
        provider = self.detect()
        return provider.get_config_overrides() if provider else {}

    def is_cloud_environment(self) -> bool:
        """Check if running in a cloud environment."""
        return self.detect() is not None

    def get_environment_type(self) -> str | None:
        """Get cloud environment type."""
        provider = self.detect()
        return provider.get_environment_type() if provider else None

    def get_service_type(self) -> str | None:
        """Get cloud service type."""
        provider = self.detect()
        return provider.get_service_type() if provider else None

    def clear_cache(self):
        """Clear detection cache."""
        self._detected_provider = None
        if self._cloud_registry:
            self._cloud_registry.clear_cache()

    def get_detection_info(self) -> dict[str, Any]:
        """Get detailed detection information."""
        provider = self.detect()

        try:
            from ..cloud import cloud_registry

            available_providers = [p.name for p in cloud_registry.list_providers()]
            total_providers = len(cloud_registry.list_providers())
        except ImportError:
            available_providers = []
            total_providers = 0

        return {
            "detected": provider is not None,
            "provider": provider.name if provider else None,
            "display_name": provider.display_name if provider else None,
            "service_type": provider.get_service_type() if provider else None,
            "environment_type": provider.get_environment_type() if provider else None,
            "config_overrides": provider.get_config_overrides() if provider else {},
            "available_providers": available_providers,
            "total_providers": total_providers,
        }
