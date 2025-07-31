#!/usr/bin/env python3
# src/chuk_mcp_server/config/environment_detector.py
"""
Enhanced environment detection that integrates with cloud detection.
"""

import os
import logging
from pathlib import Path
from typing import Set, Optional
from .base import ConfigDetector

logger = logging.getLogger(__name__)


class EnvironmentDetector(ConfigDetector):
    """Enhanced environment detector with cloud integration."""
    
    CI_INDICATORS = {
        'CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 
        'GITLAB_CI', 'JENKINS_HOME', 'TRAVIS', 'CIRCLECI',
        'BUILDKITE', 'DRONE', 'BAMBOO_BUILD_KEY'
    }
    
    def __init__(self):
        super().__init__()
        self._cloud_detector = None
    
    def detect(self) -> str:
        """Detect environment with cloud integration."""
        # Check explicit environment variables first
        env_var = self._get_explicit_environment()
        if env_var:
            self.logger.debug(f"Explicit environment detected: {env_var}")
            return env_var
        
        # Check for CI/CD environments
        if self._is_ci_environment():
            self.logger.debug("CI/CD environment detected")
            return "testing"
        
        # Check cloud environment
        cloud_env = self._get_cloud_environment()
        if cloud_env:
            self.logger.debug(f"Cloud environment detected: {cloud_env}")
            return cloud_env
        
        # Fallback to container/development detection
        if self._is_containerized():
            self.logger.debug("Containerized environment detected")
            return "production"
        
        if self._is_development_environment():
            self.logger.debug("Development environment detected")
            return "development"
        
        # Default
        self.logger.debug("Defaulting to development environment")
        return "development"
    
    def get_cloud_detector(self):
        """Get cloud detector instance (lazy loading)."""
        if self._cloud_detector is None:
            from .cloud_detector import CloudDetector
            self._cloud_detector = CloudDetector()
        return self._cloud_detector
    
    def _get_cloud_environment(self) -> Optional[str]:
        """Get environment type from cloud detection."""
        try:
            cloud_detector = self.get_cloud_detector()
            return cloud_detector.get_environment_type()
        except Exception as e:
            self.logger.debug(f"Cloud detection failed: {e}")
            return None
    
    def _get_explicit_environment(self) -> str:
        """Get explicitly set environment variables."""
        env_var = self.get_env_var('NODE_ENV', 
                                   self.get_env_var('ENV', 
                                                   self.get_env_var('ENVIRONMENT', ''))).lower()
        
        if env_var in ['production', 'prod']:
            return "production"
        elif env_var in ['staging', 'stage']:
            return "staging"
        elif env_var in ['test', 'testing']:
            return "testing"
        elif env_var in ['development', 'dev']:
            return "development"
        
        return ""
    
    def _is_ci_environment(self) -> bool:
        """Check if running in CI/CD environment."""
        return any(self.get_env_var(var) for var in self.CI_INDICATORS)
    
    def _is_containerized(self) -> bool:
        """Check if running in a container."""
        try:
            from .container_detector import ContainerDetector
            return ContainerDetector().detect()
        except ImportError:
            # Fallback container detection
            return bool(
                Path('/.dockerenv').exists() or
                self.get_env_var('KUBERNETES_SERVICE_HOST') or
                self.get_env_var('CONTAINER')
            )
    
    def _is_development_environment(self) -> bool:
        """Check for development-like setup indicators."""
        try:
            # Check current directory name
            current_dir = Path.cwd().name
            if current_dir in ['dev', 'development']:
                return True
            
            # Check for git repository
            if (Path.cwd() / '.git').exists():
                return True
            
            # Check for common development files without PORT env var
            dev_files = ['package.json', 'pyproject.toml', 'requirements.txt', 'Pipfile']
            if any((Path.cwd() / f).exists() for f in dev_files) and not self.get_env_var('PORT'):
                return True
                
        except Exception as e:
            self.logger.debug(f"Error checking development indicators: {e}")
        
        return False
    
    def get_detection_info(self) -> dict:
        """Get detailed detection information."""
        cloud_detector = self.get_cloud_detector()
        cloud_info = cloud_detector.get_detection_info()
        
        return {
            "environment": self.detect(),
            "explicit_env_vars": {
                "NODE_ENV": self.get_env_var('NODE_ENV'),
                "ENV": self.get_env_var('ENV'),
                "ENVIRONMENT": self.get_env_var('ENVIRONMENT'),
            },
            "ci_detected": self._is_ci_environment(),
            "containerized": self._is_containerized(),
            "development_indicators": self._is_development_environment(),
            "cloud": cloud_info
        }