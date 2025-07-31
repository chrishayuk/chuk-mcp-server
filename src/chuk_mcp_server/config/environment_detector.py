#!/usr/bin/env python3
# src/chuk_mcp_server/config/environment_detector.py
"""
Environment detection (dev/prod/serverless/container).
"""

from pathlib import Path
from typing import Set
from .base import ConfigDetector


class EnvironmentDetector(ConfigDetector):
    """Detects runtime environment with comprehensive checks."""
    
    CI_INDICATORS = {
        'CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 
        'GITLAB_CI', 'JENKINS_HOME', 'TRAVIS', 'CIRCLECI',
        'BUILDKITE', 'DRONE', 'BAMBOO_BUILD_KEY'
    }
    
    SERVERLESS_INDICATORS = {
        'AWS_LAMBDA_FUNCTION_NAME', 'GOOGLE_CLOUD_FUNCTION_NAME',
        'AZURE_FUNCTIONS_ENVIRONMENT', 'VERCEL', 'NETLIFY'
    }
    
    def detect(self) -> str:
        """Detect runtime environment with comprehensive checks."""
        # Check explicit environment variables first
        env_var = self._get_explicit_environment()
        if env_var:
            return env_var
        
        # Check for CI/CD environments
        if self._is_ci_environment():
            return "testing"
        
        # Check for serverless environments
        if self._is_serverless_environment():
            return "serverless"
        
        # Check for container environments
        if self._is_containerized():
            return "production"
        
        # Check for development indicators
        if self._is_development_environment():
            return "development"
        
        # If PORT is set but no explicit environment, assume production
        if self.get_env_var('PORT'):
            return "production"
        
        # Default to development for safety
        return "development"
    
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
    
    def _is_serverless_environment(self) -> bool:
        """Check if running in serverless environment."""
        return any(self.get_env_var(var) for var in self.SERVERLESS_INDICATORS)
    
    def _is_containerized(self) -> bool:
        """Check if running in a container."""
        # Import here to avoid circular dependencies
        from .container_detector import ContainerDetector
        return ContainerDetector().detect()
    
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
            dev_files = ['package.json', 'pyproject.toml']
            if any((Path.cwd() / f).exists() for f in dev_files) and not self.get_env_var('PORT'):
                return True
                
        except Exception as e:
            self.logger.debug(f"Error checking development indicators: {e}")
        
        return False