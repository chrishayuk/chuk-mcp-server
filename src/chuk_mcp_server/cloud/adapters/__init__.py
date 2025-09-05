#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/adapters/__init__.py
"""
Cloud Adapters System

Modular adapters that automatically configure ChukMCPServer for different cloud platforms.
Each adapter handles the specific requirements of its cloud provider.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# Base Cloud Adapter
# ============================================================================


class CloudAdapter(ABC):
    """Base class for cloud platform adapters."""

    def __init__(self, server):
        self.server = server
        self.cloud_provider = None

    @abstractmethod
    def is_compatible(self) -> bool:
        """Check if this adapter is compatible with current environment."""
        pass

    @abstractmethod
    def setup(self) -> bool:
        """Setup the server for this cloud platform."""
        pass

    def get_handler(self) -> Callable | None:
        """Get cloud-specific handler function if available."""
        return None

    def get_deployment_info(self) -> dict[str, Any]:
        """Get deployment information for this cloud platform."""
        return {}


# ============================================================================
# Cloud Adapter Registry
# ============================================================================


class CloudAdapterRegistry:
    """Registry for cloud adapters."""

    def __init__(self):
        self._adapters: dict[str, type[CloudAdapter]] = {}
        self._active_adapter: CloudAdapter | None = None

    def register_adapter(self, name: str, adapter_class: type[CloudAdapter]):
        """Register a cloud adapter."""
        self._adapters[name] = adapter_class
        logger.debug(f"Registered cloud adapter: {name}")

    def auto_setup(self, server) -> CloudAdapter | None:
        """Automatically setup the appropriate cloud adapter."""
        for name, adapter_class in self._adapters.items():
            try:
                adapter = adapter_class(server)
                if adapter.is_compatible():
                    logger.info(f"🌟 Auto-setting up {name} adapter")
                    if adapter.setup():
                        self._active_adapter = adapter
                        return adapter
                    else:
                        logger.warning(f"Failed to setup {name} adapter")
            except Exception as e:
                logger.debug(f"Error setting up {name} adapter: {e}")

        return None

    def get_active_adapter(self) -> CloudAdapter | None:
        """Get the currently active adapter."""
        return self._active_adapter

    def list_adapters(self) -> dict[str, type[CloudAdapter]]:
        """List all registered adapters."""
        return self._adapters.copy()


# Global adapter registry
adapter_registry = CloudAdapterRegistry()


# ============================================================================
# Auto-Registration Decorator
# ============================================================================


def cloud_adapter(name: str):
    """Decorator to auto-register cloud adapters."""

    def decorator(cls: type[CloudAdapter]):
        adapter_registry.register_adapter(name, cls)
        return cls

    return decorator


# ============================================================================
# Integration Functions
# ============================================================================


def auto_setup_cloud_adapter(server):
    """Auto-setup cloud adapter for the server."""
    return adapter_registry.auto_setup(server)


def get_active_cloud_adapter():
    """Get the active cloud adapter."""
    return adapter_registry.get_active_adapter()


def is_cloud_adapted() -> bool:
    """Check if server is adapted for a cloud platform."""
    return adapter_registry.get_active_adapter() is not None


__all__ = [
    "CloudAdapter",
    "CloudAdapterRegistry",
    "adapter_registry",
    "cloud_adapter",
    "auto_setup_cloud_adapter",
    "get_active_cloud_adapter",
    "is_cloud_adapted",
]
