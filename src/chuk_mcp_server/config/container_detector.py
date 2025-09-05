#!/usr/bin/env python3
# src/chuk_mcp_server/config/container_detector.py
"""
Container environment detection.
"""

from pathlib import Path

from .base import ConfigDetector


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
            return Path("/.dockerenv").exists()
        except Exception as e:
            self.logger.debug(f"Error checking Docker env: {e}")
            return False

    def _check_kubernetes(self) -> bool:
        """Check for Kubernetes environment."""
        return bool(self.get_env_var("KUBERNETES_SERVICE_HOST"))

    def _check_generic_container(self) -> bool:
        """Check for generic container environment variable."""
        return bool(self.get_env_var("CONTAINER"))

    def _check_cgroup_container(self) -> bool:
        """Check cgroup for container indicators."""
        try:
            cgroup_file = Path("/proc/1/cgroup")
            if not cgroup_file.exists():
                return False

            content = self.safe_file_read(cgroup_file)
            if content:
                container_indicators = ["docker", "containerd", "lxc", "kubepods"]
                return any(indicator in content for indicator in container_indicators)
        except Exception as e:
            self.logger.debug(f"Error checking cgroup: {e}")
        return False

    def _check_mountinfo_container(self) -> bool:
        """Check mountinfo for container indicators."""
        try:
            mountinfo_file = Path("/proc/self/mountinfo")
            if not mountinfo_file.exists():
                return False

            content = self.safe_file_read(mountinfo_file)
            if content:
                return "docker" in content or "containerd" in content
        except Exception as e:
            self.logger.debug(f"Error checking mountinfo: {e}")
        return False
