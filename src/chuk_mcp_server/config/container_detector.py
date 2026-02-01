#!/usr/bin/env python3
# src/chuk_mcp_server/config/container_detector.py
"""
Container environment detection.
"""

from pathlib import Path

from .base import ConfigDetector
from .constants import (
    CGROUP_PATH,
    CONTAINER_INDICATORS,
    DOCKERENV_PATH,
    ENV_CONTAINER,
    ENV_KUBERNETES_HOST,
    MOUNTINFO_PATH,
)


class ContainerDetector(ConfigDetector):
    """Detects if running in a container environment."""

    def detect(self) -> bool:
        """Detect if running in a container environment."""
        indicators = [
            self._check_docker_env(),
            self._check_kubernetes(),
            self._check_generic_container(),
            self._check_cgroup_container(),
            self._check_mountinfo_container(),
        ]
        return any(indicators)

    def _check_docker_env(self) -> bool:
        """Check for Docker environment file."""
        try:
            return Path(DOCKERENV_PATH).exists()
        except Exception as e:
            self.logger.debug(f"Error checking Docker env: {e}")
            return False

    def _check_kubernetes(self) -> bool:
        """Check for Kubernetes environment."""
        return bool(self.get_env_var(ENV_KUBERNETES_HOST))

    def _check_generic_container(self) -> bool:
        """Check for generic container environment variable."""
        return bool(self.get_env_var(ENV_CONTAINER))

    def _check_cgroup_container(self) -> bool:
        """Check cgroup for container indicators."""
        try:
            cgroup_file = Path(CGROUP_PATH)
            if not cgroup_file.exists():
                return False

            content = self.safe_file_read(cgroup_file)
            if content:
                return any(indicator in content for indicator in CONTAINER_INDICATORS)
        except Exception as e:
            self.logger.debug(f"Error checking cgroup: {e}")
        return False

    def _check_mountinfo_container(self) -> bool:
        """Check mountinfo for container indicators."""
        try:
            mountinfo_file = Path(MOUNTINFO_PATH)
            if not mountinfo_file.exists():
                return False

            content = self.safe_file_read(mountinfo_file)
            if content:
                return any(indicator in content for indicator in CONTAINER_INDICATORS)
        except Exception as e:
            self.logger.debug(f"Error checking mountinfo: {e}")
        return False
