#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/providers/__init__.py
"""
Cloud Providers Package

Registers all cloud providers with the global registry.
"""

import logging

logger = logging.getLogger(__name__)

def register_all_providers(cloud_registry):
    """Register all cloud providers with the given registry."""
    
    # Register GCP Provider
    try:
        from .gcp import register_gcp_provider
        register_gcp_provider(cloud_registry)
        logger.debug("Registered GCP provider")
    except ImportError as e:
        logger.debug(f"GCP provider not available: {e}")
    except Exception as e:
        logger.error(f"Error registering GCP provider: {e}")

    # Register AWS Provider
    try:
        from .aws import register_aws_provider
        register_aws_provider(cloud_registry)
        logger.debug("Registered AWS provider")
    except ImportError as e:
        logger.debug(f"AWS provider not available: {e}")
    except Exception as e:
        logger.error(f"Error registering AWS provider: {e}")

    # Register Azure Provider
    try:
        from .azure import register_azure_provider
        register_azure_provider(cloud_registry)
        logger.debug("Registered Azure provider")
    except ImportError as e:
        logger.debug(f"Azure provider not available: {e}")
    except Exception as e:
        logger.error(f"Error registering Azure provider: {e}")

    # Register Edge Providers
    try:
        from .edge import register_edge_providers
        register_edge_providers(cloud_registry)
        logger.debug("Registered Edge providers")
    except ImportError as e:
        logger.debug(f"Edge providers not available: {e}")
    except Exception as e:
        logger.error(f"Error registering Edge providers: {e}")

    logger.debug("Cloud providers registration complete")