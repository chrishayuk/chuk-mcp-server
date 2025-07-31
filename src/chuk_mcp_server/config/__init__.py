#!/usr/bin/env python3
# src/chuk_mcp_server/config/__init__.py
"""
Configuration Detection System

Clean, modular configuration system where cloud_detector uses 
providers from the cloud module.
"""

from .project_detector import ProjectDetector
from .environment_detector import EnvironmentDetector
from .network_detector import NetworkDetector
from .system_detector import SystemDetector
from .container_detector import ContainerDetector
from .cloud_detector import CloudDetector
from .smart_config import SmartConfig

# Convenience functions
def get_smart_defaults() -> dict:
    """Get all smart defaults."""
    return SmartConfig().get_all_defaults()

def detect_cloud_provider():
    """Detect cloud provider."""
    return CloudDetector().detect()

def get_cloud_config() -> dict:
    """Get cloud configuration overrides."""
    return CloudDetector().get_config_overrides()

def is_cloud_environment() -> bool:
    """Check if running in cloud environment."""
    return CloudDetector().is_cloud_environment()

__all__ = [
    # Detectors
    'ProjectDetector',
    'EnvironmentDetector', 
    'NetworkDetector',
    'SystemDetector',
    'ContainerDetector',
    'CloudDetector',
    
    # Main config class
    'SmartConfig',
    
    # Convenience functions
    'get_smart_defaults',
    'detect_cloud_provider',
    'get_cloud_config',
    'is_cloud_environment',
]