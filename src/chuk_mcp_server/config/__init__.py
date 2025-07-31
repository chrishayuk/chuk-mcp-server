#!/usr/bin/env python3
# src/chuk_mcp_server/config/__init__.py
"""
Modular Smart Configuration System

A well-structured, testable configuration system that intelligently detects
optimal settings for different environments and platforms.
"""

from .project_detector import ProjectDetector
from .environment_detector import EnvironmentDetector
from .network_detector import NetworkDetector
from .system_detector import SystemDetector
from .container_detector import ContainerDetector
from .smart_config import SmartConfig

# Convenience function for backward compatibility
def get_smart_defaults() -> dict:
    """Get all smart defaults - backward compatibility function."""
    return SmartConfig().get_all_defaults()

__all__ = [
    'ProjectDetector',
    'EnvironmentDetector', 
    'NetworkDetector',
    'SystemDetector',
    'ContainerDetector',
    'SmartConfig',
    'get_smart_defaults'
]