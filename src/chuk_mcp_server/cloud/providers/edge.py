#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/providers/edge.py
"""
Edge Computing Providers

Detects and configures for edge platforms including:
- Vercel Edge Functions
- Cloudflare Workers
- Netlify Edge Functions
- Fastly Compute@Edge
"""

import os
from typing import Any

from ..base import CloudProvider


class VercelProvider(CloudProvider):
    """Vercel platform detection and configuration."""

    @property
    def name(self) -> str:
        return "vercel"

    @property
    def display_name(self) -> str:
        return "Vercel"

    def get_priority(self) -> int:
        return 5  # High priority for edge platforms

    def detect(self) -> bool:
        """Detect if running on Vercel."""
        vercel_indicators = [
            "VERCEL",
            "VERCEL_ENV",
            "VERCEL_URL",
            "VERCEL_REGION",
            "VERCEL_GIT_COMMIT_SHA",
        ]
        return any(os.environ.get(var) for var in vercel_indicators)

    def get_environment_type(self) -> str:
        return "serverless"

    def get_service_type(self) -> str:
        if os.environ.get("VERCEL_ENV") == "production":
            return "vercel_production"
        else:
            return "vercel_preview"

    def get_config_overrides(self) -> dict[str, Any]:
        return {
            "cloud_provider": "vercel",
            "service_type": self.get_service_type(),
            "host": "0.0.0.0",  # nosec B104 - Required for Vercel edge platform routing
            "port": int(os.environ.get("PORT", 3000)),
            "workers": 1,
            "max_connections": 100,
            "log_level": "WARNING",
            "debug": False,
            "performance_mode": "vercel_optimized",
            "vercel_env": os.environ.get("VERCEL_ENV", "development"),
            "vercel_region": os.environ.get("VERCEL_REGION", "unknown"),
            "vercel_url": os.environ.get("VERCEL_URL", "unknown"),
        }


class NetlifyProvider(CloudProvider):
    """Netlify platform detection and configuration."""

    @property
    def name(self) -> str:
        return "netlify"

    @property
    def display_name(self) -> str:
        return "Netlify"

    def get_priority(self) -> int:
        return 5  # High priority for edge platforms

    def detect(self) -> bool:
        """Detect if running on Netlify."""
        netlify_indicators = [
            "NETLIFY",
            "NETLIFY_DEV",
            "SITE_ID",
            "DEPLOY_ID",
            "CONTEXT",
            "BRANCH",
            "COMMIT_REF",
        ]
        return any(os.environ.get(var) for var in netlify_indicators)

    def get_environment_type(self) -> str:
        return "serverless"

    def get_service_type(self) -> str:
        context = os.environ.get("CONTEXT", "")
        if context == "production":
            return "netlify_production"
        elif context == "deploy-preview":
            return "netlify_preview"
        else:
            return "netlify_dev"

    def get_config_overrides(self) -> dict[str, Any]:
        return {
            "cloud_provider": "netlify",
            "service_type": self.get_service_type(),
            "host": "0.0.0.0",  # nosec B104 - Required for Netlify edge platform routing
            "port": int(os.environ.get("PORT", 8888)),
            "workers": 1,
            "max_connections": 100,
            "log_level": "WARNING",
            "debug": False,
            "performance_mode": "netlify_optimized",
            "site_id": os.environ.get("SITE_ID", "unknown"),
            "deploy_id": os.environ.get("DEPLOY_ID", "unknown"),
            "context": os.environ.get("CONTEXT", "unknown"),
            "branch": os.environ.get("BRANCH", "unknown"),
        }


class CloudflareProvider(CloudProvider):
    """Cloudflare Workers detection and configuration."""

    @property
    def name(self) -> str:
        return "cloudflare"

    @property
    def display_name(self) -> str:
        return "Cloudflare Workers"

    def get_priority(self) -> int:
        return 5  # High priority for edge platforms

    def detect(self) -> bool:
        """Detect if running on Cloudflare Workers."""
        cf_indicators = [
            "CF_PAGES",
            "CF_PAGES_COMMIT_SHA",
            "CF_PAGES_BRANCH",
            "CLOUDFLARE_ACCOUNT_ID",
            "CLOUDFLARE_API_TOKEN",
        ]
        return any(os.environ.get(var) for var in cf_indicators)

    def get_environment_type(self) -> str:
        return "serverless"

    def get_service_type(self) -> str:
        if os.environ.get("CF_PAGES"):
            return "cloudflare_pages"
        else:
            return "cloudflare_workers"

    def get_config_overrides(self) -> dict[str, Any]:
        return {
            "cloud_provider": "cloudflare",
            "service_type": self.get_service_type(),
            "host": "0.0.0.0",  # nosec B104 - Required for Cloudflare edge platform routing
            "port": int(os.environ.get("PORT", 8787)),
            "workers": 1,
            "max_connections": 50,  # Very conservative for edge
            "log_level": "ERROR",  # Minimal logging for edge performance
            "debug": False,
            "performance_mode": "cloudflare_optimized",
            "cf_pages": bool(os.environ.get("CF_PAGES")),
            "cf_branch": os.environ.get("CF_PAGES_BRANCH", "unknown"),
        }


def register_edge_providers(registry: Any) -> None:
    """Register edge providers with the registry."""
    vercel_provider = VercelProvider()
    netlify_provider = NetlifyProvider()
    cloudflare_provider = CloudflareProvider()

    registry.register_provider(vercel_provider)
    registry.register_provider(netlify_provider)
    registry.register_provider(cloudflare_provider)
