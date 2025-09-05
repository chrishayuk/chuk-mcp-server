#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/registry.py
"""
Cloud detection registry system.
"""

import logging
from collections.abc import Callable
from typing import Any

from .base import CloudProvider

logger = logging.getLogger(__name__)


class CloudDetectionRegistry:
    """Registry for cloud provider detectors."""

    def __init__(self) -> None:
        self._providers: dict[str, CloudProvider] = {}
        self._detection_cache: CloudProvider | None = None

    def register_provider(self, provider: CloudProvider) -> None:
        """Register a cloud provider detector."""
        self._providers[provider.name] = provider
        self._detection_cache = None  # Invalidate cache
        logger.debug(f"Registered cloud provider: {provider.display_name}")

    def detect_provider(self) -> CloudProvider | None:
        """Detect the current cloud provider."""
        if self._detection_cache is not None:
            return self._detection_cache

        # Sort providers by priority for consistent detection order
        sorted_providers = sorted(self._providers.values(), key=lambda p: p.get_priority())

        for provider in sorted_providers:
            try:
                if provider.detect():
                    logger.info(f"🌟 Detected cloud provider: {provider.display_name}")
                    self._detection_cache = provider
                    return provider
            except Exception as e:
                logger.debug(f"Error detecting {provider.name}: {e}")

        logger.debug("No cloud provider detected")
        self._detection_cache = None
        return None

    def get_provider(self, name: str) -> CloudProvider | None:
        """Get a specific provider by name."""
        return self._providers.get(name)

    def list_providers(self) -> list[CloudProvider]:
        """List all registered providers."""
        return list(self._providers.values())

    def clear_cache(self) -> None:
        """Clear detection cache."""
        self._detection_cache = None

    def get_registry_info(self) -> dict[str, Any]:
        """Get registry information."""
        current_provider = self.detect_provider()

        return {
            "total_providers": len(self._providers),
            "provider_names": list(self._providers.keys()),
            "current_detection": {
                "provider": current_provider.name if current_provider else None,
                "display_name": current_provider.display_name if current_provider else None,
                "service_type": current_provider.get_service_type() if current_provider else None,
            },
            "cache_status": {
                "cached": self._detection_cache is not None,
                "cached_provider": self._detection_cache.name if self._detection_cache else None,
            },
        }


def cloud_provider(
    name: str, display_name: str | None = None, priority: int = 100
) -> Callable[[type[CloudProvider]], type[CloudProvider]]:
    """Decorator to auto-register cloud providers."""

    def decorator(cls: type[CloudProvider]) -> type[CloudProvider]:
        # Create instance and register
        instance = cls()

        # Override name and display_name properties
        instance._name = name  # type: ignore[attr-defined]
        instance._display_name = display_name or name.upper()  # type: ignore[attr-defined]
        instance._priority = priority  # type: ignore[attr-defined]

        # Override the property methods to use the stored values
        def name_property(self: Any) -> str:
            return self._name

        def display_name_property(self: Any) -> str:
            return self._display_name

        def get_priority_method(self: Any) -> int:
            return self._priority

        # Monkey patch the instance
        instance.__class__.name = property(name_property)  # type: ignore[assignment]
        instance.__class__.display_name = property(display_name_property)  # type: ignore[assignment]
        instance.__class__.get_priority = get_priority_method  # type: ignore[assignment]

        # Register with global registry (imported by __init__.py)
        # We'll register it when the cloud module is imported
        # For now, just mark it for registration
        if not hasattr(cls, "_registry_info"):
            cls._registry_info = (name, display_name, priority, instance)  # type: ignore[attr-defined]

        return cls

    return decorator


# Registry instances will be created and providers registered in __init__.py
