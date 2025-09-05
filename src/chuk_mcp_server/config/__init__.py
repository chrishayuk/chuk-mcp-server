#!/usr/bin/env python3
# src/chuk_mcp_server/config/__init__.py
"""
Configuration Detection System

Clean, modular configuration system where cloud_detector uses
providers from the cloud module.
"""

from typing import Any

from .cloud_detector import CloudDetector
from .container_detector import ContainerDetector
from .environment_detector import EnvironmentDetector
from .network_detector import NetworkDetector
from .project_detector import ProjectDetector
from .smart_config import SmartConfig
from .system_detector import SystemDetector


# Convenience functions
def get_smart_defaults() -> dict[str, Any]:
    """Get all smart defaults."""
    return SmartConfig().get_all_defaults()


def detect_cloud_provider():
    """Detect cloud provider."""
    return CloudDetector().detect()


def get_cloud_config() -> dict[str, Any]:
    """Get cloud configuration overrides."""
    return CloudDetector().get_config_overrides()


def is_cloud_environment() -> bool:
    """Check if running in cloud environment."""
    return CloudDetector().is_cloud_environment()


__all__ = [
    # Detectors
    "ProjectDetector",
    "EnvironmentDetector",
    "NetworkDetector",
    "SystemDetector",
    "ContainerDetector",
    "CloudDetector",
    # Main config class
    "SmartConfig",
    # Convenience functions
    "get_smart_defaults",
    "detect_cloud_provider",
    "get_cloud_config",
    "is_cloud_environment",
]
