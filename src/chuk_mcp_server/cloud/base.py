#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/base.py
"""
Base classes for cloud provider system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class CloudProvider(ABC):
    """Base interface for cloud provider detection and configuration."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'gcp', 'aws', 'azure')."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        pass
    
    @abstractmethod
    def detect(self) -> bool:
        """Detect if running on this cloud provider."""
        pass
    
    @abstractmethod
    def get_environment_type(self) -> str:
        """Get specific environment type (e.g., 'serverless', 'production')."""
        pass
    
    @abstractmethod
    def get_config_overrides(self) -> Dict[str, Any]:
        """Get provider-specific configuration overrides."""
        pass
    
    def get_service_type(self) -> str:
        """Get specific service type (e.g., 'gcf_gen2', 'lambda_arm64')."""
        return self.get_environment_type()
    
    def get_priority(self) -> int:
        """Detection priority (lower = higher priority)."""
        return 100