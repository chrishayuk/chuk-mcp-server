#!/usr/bin/env python3
# src/chuk_mcp_server/config/environment_detector.py
"""
Enhanced environment detection that integrates with cloud detection.
"""

import logging
from pathlib import Path
from typing import Optional
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
        # 1. Explicit env var
        env_var = self._get_explicit_environment()
        if env_var:
            logger.debug(f"Explicit environment detected: {env_var}")
            return env_var

        # 2. CI/CD
        if self._is_ci_environment():
            logger.debug("CI/CD environment detected")
            return "testing"

        # 3. Serverless
        if self._is_serverless_environment():
            logger.debug("Serverless environment detected")
            return "serverless"

        # 4. Cloud provider's own environment type
        cloud_env = self._get_cloud_environment()
        if cloud_env:
            logger.debug(f"Cloud environment detected: {cloud_env}")
            return cloud_env

        # 5. PORT env var implies production
        if self.get_env_var('PORT'):
            logger.debug("PORT environment variable detected; assuming production")
            return "production"

        # 6. Container fallback -> production
        if self._is_containerized():
            logger.debug("Containerized environment detected")
            return "production"

        # 7. Development indicators
        if self._is_development_environment():
            logger.debug("Development environment detected")
            return "development"

        # 8. Default to development
        logger.debug("Defaulting to development environment")
        return "development"

    def get_cloud_detector(self):
        """Lazy-load and return the CloudDetector."""
        if self._cloud_detector is None:
            from .cloud_detector import CloudDetector
            self._cloud_detector = CloudDetector()
        return self._cloud_detector

    def _is_serverless_environment(self) -> bool:
        """Check for serverless environment vars."""
        serverless_vars = [
            'AWS_LAMBDA_FUNCTION_NAME',
            'GOOGLE_CLOUD_FUNCTION_NAME',
            'AZURE_FUNCTIONS_ENVIRONMENT',
            'VERCEL',
            'NETLIFY'
        ]
        return any(self.get_env_var(var) for var in serverless_vars)

    def _get_cloud_environment(self) -> Optional[str]:
        """Ask the CloudDetector for its environment type."""
        try:
            detector = self.get_cloud_detector()
            return detector.get_environment_type()
        except Exception as e:
            logger.debug(f"Cloud detection failed: {e}")
            return None

    def _get_explicit_environment(self) -> str:
        """Check NODE_ENV, ENV, ENVIRONMENT for explicit setting."""
        env_var = self.get_env_var(
            'NODE_ENV',
            self.get_env_var('ENV', self.get_env_var('ENVIRONMENT', ''))
        ).lower()
        if env_var in ('production', 'prod'):
            return "production"
        if env_var in ('staging', 'stage'):
            return "staging"
        if env_var in ('test', 'testing'):
            return "testing"
        if env_var in ('development', 'dev'):
            return "development"
        return ""

    def _is_ci_environment(self) -> bool:
        """Detect CI/CD via common env vars."""
        return any(self.get_env_var(var) for var in self.CI_INDICATORS)

    def _is_containerized(self) -> bool:
        """Detect container via detector or filesystem hints."""
        try:
            from .container_detector import ContainerDetector
            return ContainerDetector().detect()
        except ImportError:
            # Fallback: /.dockerenv or KUBERNETES_SERVICE_HOST or CONTAINER
            return bool(
                Path('/.dockerenv').exists() or
                self.get_env_var('KUBERNETES_SERVICE_HOST') or
                self.get_env_var('CONTAINER')
            )

    def _is_development_environment(self) -> bool:
        """Detect dev by directory name, git presence, or dev files + no PORT."""
        try:
            cwd = Path.cwd()
            if cwd.name in ('dev', 'development'):
                return True
            if (cwd / '.git').exists():
                return True
            dev_files = ['package.json', 'pyproject.toml', 'requirements.txt', 'Pipfile']
            if any((cwd / f).exists() for f in dev_files) and not self.get_env_var('PORT'):
                return True
        except Exception as e:
            logger.debug(f"Error checking development indicators: {e}")
        return False

    def get_detection_info(self) -> dict:
        """Return detailed flags and values used in detection."""
        cloud_info = self.get_cloud_detector().get_detection_info()
        return {
            "environment": self.detect(),
            "explicit_env_vars": {
                "NODE_ENV": self.get_env_var('NODE_ENV'),
                "ENV": self.get_env_var('ENV'),
                "ENVIRONMENT": self.get_env_var('ENVIRONMENT'),
            },
            "ci_detected": self._is_ci_environment(),
            "serverless_detected": self._is_serverless_environment(),
            "containerized": self._is_containerized(),
            "development_indicators": self._is_development_environment(),
            "cloud": cloud_info,
        }
