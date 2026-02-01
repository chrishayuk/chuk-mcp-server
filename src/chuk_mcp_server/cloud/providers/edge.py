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
from ..constants import (
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    CF_PAGES,
    CF_PAGES_BRANCH,
    CF_PAGES_COMMIT_SHA,
    CFG_CLOUD_PROVIDER,
    CFG_DEBUG,
    CFG_HOST,
    CFG_LOG_LEVEL,
    CFG_MAX_CONNECTIONS,
    CFG_PERFORMANCE_MODE,
    CFG_PORT,
    CFG_SERVICE_TYPE,
    CFG_WORKERS,
    DEFAULT_HOST,
    DEFAULT_PORT_CLOUDFLARE,
    DEFAULT_PORT_NETLIFY,
    DEFAULT_PORT_VERCEL,
    DISPLAY_CLOUDFLARE,
    DISPLAY_NETLIFY,
    DISPLAY_VERCEL,
    ENV_PORT,
    ENV_TYPE_PRODUCTION,
    ENV_TYPE_SERVERLESS,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_WARNING,
    NETLIFY_BRANCH,
    NETLIFY_COMMIT_REF,
    NETLIFY_CONTEXT,
    NETLIFY_CTX_DEPLOY_PREVIEW,
    NETLIFY_CTX_PRODUCTION,
    NETLIFY_DEPLOY_ID,
    NETLIFY_DEV,
    NETLIFY_ENV_FLAG,
    NETLIFY_SITE_ID,
    PERF_CLOUDFLARE_OPTIMIZED,
    PERF_NETLIFY_OPTIMIZED,
    PERF_VERCEL_OPTIMIZED,
    PROVIDER_CLOUDFLARE,
    PROVIDER_NETLIFY,
    PROVIDER_VERCEL,
    SVC_CLOUDFLARE_PAGES,
    SVC_CLOUDFLARE_WORKERS,
    SVC_NETLIFY_DEV,
    SVC_NETLIFY_PREVIEW,
    SVC_NETLIFY_PRODUCTION,
    SVC_VERCEL_PREVIEW,
    SVC_VERCEL_PRODUCTION,
    VERCEL_ENV,
    VERCEL_ENV_FLAG,
    VERCEL_GIT_COMMIT_SHA,
    VERCEL_REGION,
    VERCEL_URL,
)


class VercelProvider(CloudProvider):
    """Vercel platform detection and configuration."""

    @property
    def name(self) -> str:
        return PROVIDER_VERCEL

    @property
    def display_name(self) -> str:
        return DISPLAY_VERCEL

    def get_priority(self) -> int:
        return 5  # High priority for edge platforms

    def detect(self) -> bool:
        """Detect if running on Vercel."""
        vercel_indicators = [
            VERCEL_ENV_FLAG,
            VERCEL_ENV,
            VERCEL_URL,
            VERCEL_REGION,
            VERCEL_GIT_COMMIT_SHA,
        ]
        return any(os.environ.get(var) for var in vercel_indicators)

    def get_environment_type(self) -> str:
        return ENV_TYPE_SERVERLESS

    def get_service_type(self) -> str:
        if os.environ.get(VERCEL_ENV) == ENV_TYPE_PRODUCTION:
            return SVC_VERCEL_PRODUCTION
        else:
            return SVC_VERCEL_PREVIEW

    def get_config_overrides(self) -> dict[str, Any]:
        return {
            CFG_CLOUD_PROVIDER: PROVIDER_VERCEL,
            CFG_SERVICE_TYPE: self.get_service_type(),
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for Vercel edge platform routing
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_VERCEL)),
            CFG_WORKERS: 1,
            CFG_MAX_CONNECTIONS: 100,
            CFG_LOG_LEVEL: LOG_LEVEL_WARNING,
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_VERCEL_OPTIMIZED,
            "vercel_env": os.environ.get(VERCEL_ENV, "development"),
            "vercel_region": os.environ.get(VERCEL_REGION, "unknown"),
            "vercel_url": os.environ.get(VERCEL_URL, "unknown"),
        }


class NetlifyProvider(CloudProvider):
    """Netlify platform detection and configuration."""

    @property
    def name(self) -> str:
        return PROVIDER_NETLIFY

    @property
    def display_name(self) -> str:
        return DISPLAY_NETLIFY

    def get_priority(self) -> int:
        return 5  # High priority for edge platforms

    def detect(self) -> bool:
        """Detect if running on Netlify."""
        netlify_indicators = [
            NETLIFY_ENV_FLAG,
            NETLIFY_DEV,
            NETLIFY_SITE_ID,
            NETLIFY_DEPLOY_ID,
            NETLIFY_CONTEXT,
            NETLIFY_BRANCH,
            NETLIFY_COMMIT_REF,
        ]
        return any(os.environ.get(var) for var in netlify_indicators)

    def get_environment_type(self) -> str:
        return ENV_TYPE_SERVERLESS

    def get_service_type(self) -> str:
        context = os.environ.get(NETLIFY_CONTEXT, "")
        if context == NETLIFY_CTX_PRODUCTION:
            return SVC_NETLIFY_PRODUCTION
        elif context == NETLIFY_CTX_DEPLOY_PREVIEW:
            return SVC_NETLIFY_PREVIEW
        else:
            return SVC_NETLIFY_DEV

    def get_config_overrides(self) -> dict[str, Any]:
        return {
            CFG_CLOUD_PROVIDER: PROVIDER_NETLIFY,
            CFG_SERVICE_TYPE: self.get_service_type(),
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for Netlify edge platform routing
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_NETLIFY)),
            CFG_WORKERS: 1,
            CFG_MAX_CONNECTIONS: 100,
            CFG_LOG_LEVEL: LOG_LEVEL_WARNING,
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_NETLIFY_OPTIMIZED,
            "site_id": os.environ.get(NETLIFY_SITE_ID, "unknown"),
            "deploy_id": os.environ.get(NETLIFY_DEPLOY_ID, "unknown"),
            "context": os.environ.get(NETLIFY_CONTEXT, "unknown"),
            "branch": os.environ.get(NETLIFY_BRANCH, "unknown"),
        }


class CloudflareProvider(CloudProvider):
    """Cloudflare Workers detection and configuration."""

    @property
    def name(self) -> str:
        return PROVIDER_CLOUDFLARE

    @property
    def display_name(self) -> str:
        return DISPLAY_CLOUDFLARE

    def get_priority(self) -> int:
        return 5  # High priority for edge platforms

    def detect(self) -> bool:
        """Detect if running on Cloudflare Workers."""
        cf_indicators = [
            CF_PAGES,
            CF_PAGES_COMMIT_SHA,
            CF_PAGES_BRANCH,
            CF_ACCOUNT_ID,
            CF_API_TOKEN,
        ]
        return any(os.environ.get(var) for var in cf_indicators)

    def get_environment_type(self) -> str:
        return ENV_TYPE_SERVERLESS

    def get_service_type(self) -> str:
        if os.environ.get(CF_PAGES):
            return SVC_CLOUDFLARE_PAGES
        else:
            return SVC_CLOUDFLARE_WORKERS

    def get_config_overrides(self) -> dict[str, Any]:
        return {
            CFG_CLOUD_PROVIDER: PROVIDER_CLOUDFLARE,
            CFG_SERVICE_TYPE: self.get_service_type(),
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for Cloudflare edge platform routing
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_CLOUDFLARE)),
            CFG_WORKERS: 1,
            CFG_MAX_CONNECTIONS: 50,  # Very conservative for edge
            CFG_LOG_LEVEL: LOG_LEVEL_ERROR,  # Minimal logging for edge performance
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_CLOUDFLARE_OPTIMIZED,
            "cf_pages": bool(os.environ.get(CF_PAGES)),
            "cf_branch": os.environ.get(CF_PAGES_BRANCH, "unknown"),
        }


def register_edge_providers(registry: Any) -> None:
    """Register edge providers with the registry."""
    vercel_provider = VercelProvider()
    netlify_provider = NetlifyProvider()
    cloudflare_provider = CloudflareProvider()

    registry.register_provider(vercel_provider)
    registry.register_provider(netlify_provider)
    registry.register_provider(cloudflare_provider)
