#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/__init__.py
"""
Cloud Provider Detection System

Self-contained cloud provider system with reliable auto-registration.
"""

import logging
from typing import Any

# Import base classes first
from .base import CloudProvider

# Import registry system
from .registry import CloudDetectionRegistry

logger = logging.getLogger(__name__)

# Create global registry instance
cloud_registry = CloudDetectionRegistry()

# ============================================================================
# Provider Registration (Simple and Reliable)
# ============================================================================


def _register_providers():
    """Register all cloud providers with the global registry."""
    # Only register if registry is empty
    if len(cloud_registry.list_providers()) > 0:
        return

    # Register GCP Provider
    try:
        from .providers.gcp import GCPProvider

        gcp_provider = GCPProvider()
        cloud_registry.register_provider(gcp_provider)
        logger.debug("Registered GCP provider")
    except Exception as e:
        logger.debug(f"Could not register GCP provider: {e}")

    # Register AWS Provider
    try:
        from .providers.aws import AWSProvider

        aws_provider = AWSProvider()
        cloud_registry.register_provider(aws_provider)
        logger.debug("Registered AWS provider")
    except Exception as e:
        logger.debug(f"Could not register AWS provider: {e}")

    # Register Azure Provider
    try:
        from .providers.azure import AzureProvider

        azure_provider = AzureProvider()
        cloud_registry.register_provider(azure_provider)
        logger.debug("Registered Azure provider")
    except Exception as e:
        logger.debug(f"Could not register Azure provider: {e}")

    # Register Edge Providers
    try:
        from .providers.edge import CloudflareProvider, NetlifyProvider, VercelProvider

        vercel_provider = VercelProvider()
        netlify_provider = NetlifyProvider()
        cloudflare_provider = CloudflareProvider()

        cloud_registry.register_provider(vercel_provider)
        cloud_registry.register_provider(netlify_provider)
        cloud_registry.register_provider(cloudflare_provider)
        logger.debug("Registered Edge providers")
    except Exception as e:
        logger.debug(f"Could not register Edge providers: {e}")

    total_providers = len(cloud_registry.list_providers())
    logger.debug(f"Registered {total_providers} cloud providers")


# Register providers immediately on import
_register_providers()

# ============================================================================
# Public API Functions
# ============================================================================


def detect_cloud_provider() -> CloudProvider | None:
    """Convenience function to detect cloud provider."""
    # Ensure providers are registered
    _register_providers()
    return cloud_registry.detect_provider()


def get_cloud_config() -> dict[str, Any]:
    """Get cloud-specific configuration."""
    provider = detect_cloud_provider()
    return provider.get_config_overrides() if provider else {}


def register_cloud_provider(provider: CloudProvider) -> None:
    """Register a cloud provider."""
    cloud_registry.register_provider(provider)


def is_cloud_environment() -> bool:
    """Check if running in any cloud environment."""
    return detect_cloud_provider() is not None


def get_cloud_summary() -> dict[str, Any]:
    """Get summary of cloud detection."""
    provider = detect_cloud_provider()
    if not provider:
        return {"detected": False}

    return {
        "detected": True,
        "provider": provider.name,
        "display_name": provider.display_name,
        "service_type": provider.get_service_type(),
        "environment_type": provider.get_environment_type(),
        "config_overrides": provider.get_config_overrides(),
    }


def list_cloud_providers() -> list[dict[str, Any]]:
    """List all registered cloud providers."""
    # Ensure providers are registered
    _register_providers()

    providers = cloud_registry.list_providers()
    return [{"name": p.name, "display_name": p.display_name, "detected": p.detect()} for p in providers]


def get_cloud_info() -> dict[str, Any]:
    """Get comprehensive cloud information."""
    return {
        "current_detection": get_cloud_summary(),
        "available_providers": list_cloud_providers(),
        "registry_stats": {"total_providers": len(cloud_registry.list_providers()), "providers_loaded": True},
    }


def clear_cloud_cache():
    """Clear cloud detection cache."""
    cloud_registry.clear_cache()


def force_reload_providers():
    """Force reload all providers (for testing)."""
    # Clear existing providers
    cloud_registry._providers.clear()
    cloud_registry._detection_cache = None

    # Re-register
    _register_providers()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Base classes
    "CloudProvider",
    # Registry
    "cloud_registry",
    # Detection functions
    "detect_cloud_provider",
    "get_cloud_config",
    "register_cloud_provider",
    "is_cloud_environment",
    "get_cloud_summary",
    "list_cloud_providers",
    "get_cloud_info",
    "clear_cloud_cache",
    "force_reload_providers",
]
