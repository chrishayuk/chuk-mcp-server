#!/usr/bin/env python3
# tests/config/test_container_detector.py
"""
Fixed unit tests for ContainerDetector with better isolation.
"""

import os
from unittest.mock import patch

import pytest

from chuk_mcp_server.config.container_detector import ContainerDetector


class TestContainerDetectorFixed:
    """Test container detection with proper isolation."""

    def test_detect_with_all_false(self):
        """Test detect() when all checks return False."""
        detector = ContainerDetector()

        # Mock ALL individual check methods to return False
        with patch.object(detector, "_check_docker_env", return_value=False):
            with patch.object(detector, "_check_kubernetes", return_value=False):
                with patch.object(detector, "_check_generic_container", return_value=False):
                    with patch.object(detector, "_check_cgroup_container", return_value=False):
                        with patch.object(detector, "_check_mountinfo_container", return_value=False):
                            result = detector.detect()
                            assert result is False

    def test_detect_with_docker_true(self):
        """Test detect() when Docker check returns True."""
        detector = ContainerDetector()

        # Only mock Docker check to return True, others False
        with patch.object(detector, "_check_docker_env", return_value=True):
            with patch.object(detector, "_check_kubernetes", return_value=False):
                with patch.object(detector, "_check_generic_container", return_value=False):
                    with patch.object(detector, "_check_cgroup_container", return_value=False):
                        with patch.object(detector, "_check_mountinfo_container", return_value=False):
                            result = detector.detect()
                            assert result is True

    def test_detect_with_kubernetes_true(self):
        """Test detect() when Kubernetes check returns True."""
        detector = ContainerDetector()

        # Only mock Kubernetes check to return True
        with patch.object(detector, "_check_docker_env", return_value=False):
            with patch.object(detector, "_check_kubernetes", return_value=True):
                with patch.object(detector, "_check_generic_container", return_value=False):
                    with patch.object(detector, "_check_cgroup_container", return_value=False):
                        with patch.object(detector, "_check_mountinfo_container", return_value=False):
                            result = detector.detect()
                            assert result is True

    def test_check_docker_env_true(self):
        """Test _check_docker_env returns True when .dockerenv exists."""
        detector = ContainerDetector()

        with patch("pathlib.Path.exists", return_value=True):
            result = detector._check_docker_env()
            assert result is True

    def test_check_docker_env_false(self):
        """Test _check_docker_env returns False when .dockerenv doesn't exist."""
        detector = ContainerDetector()

        with patch("pathlib.Path.exists", return_value=False):
            result = detector._check_docker_env()
            assert result is False

    def test_check_kubernetes_true(self):
        """Test _check_kubernetes returns True when env var is set."""
        detector = ContainerDetector()

        with patch.dict(os.environ, {"KUBERNETES_SERVICE_HOST": "10.0.0.1"}):
            result = detector._check_kubernetes()
            assert result is True

    def test_check_kubernetes_false(self):
        """Test _check_kubernetes returns False when env var is not set."""
        detector = ContainerDetector()

        with patch.dict(os.environ, {}, clear=True):
            result = detector._check_kubernetes()
            assert result is False

    def test_check_generic_container_true(self):
        """Test _check_generic_container returns True when CONTAINER is set."""
        detector = ContainerDetector()

        with patch.dict(os.environ, {"CONTAINER": "docker"}):
            result = detector._check_generic_container()
            assert result is True

    def test_check_generic_container_false(self):
        """Test _check_generic_container returns False when CONTAINER is not set."""
        detector = ContainerDetector()

        with patch.dict(os.environ, {}, clear=True):
            result = detector._check_generic_container()
            assert result is False

    def test_check_cgroup_container_with_docker(self):
        """Test _check_cgroup_container detects Docker."""
        detector = ContainerDetector()

        cgroup_content = "1:name=systemd:/docker/abc123"

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(detector, "safe_file_read", return_value=cgroup_content):
                result = detector._check_cgroup_container()
                assert result is True

    def test_check_cgroup_container_with_kubernetes(self):
        """Test _check_cgroup_container detects Kubernetes."""
        detector = ContainerDetector()

        cgroup_content = "1:name=systemd:/kubepods/besteffort/pod123"

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(detector, "safe_file_read", return_value=cgroup_content):
                result = detector._check_cgroup_container()
                assert result is True

    def test_check_cgroup_container_host_system(self):
        """Test _check_cgroup_container returns False for host system."""
        detector = ContainerDetector()

        cgroup_content = "1:name=systemd:/"

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(detector, "safe_file_read", return_value=cgroup_content):
                result = detector._check_cgroup_container()
                assert result is False

    def test_check_cgroup_container_file_not_exists(self):
        """Test _check_cgroup_container when file doesn't exist."""
        detector = ContainerDetector()

        with patch("pathlib.Path.exists", return_value=False):
            result = detector._check_cgroup_container()
            assert result is False

    def test_check_mountinfo_container_with_docker(self):
        """Test _check_mountinfo_container detects Docker."""
        detector = ContainerDetector()

        mountinfo_content = "cgroup docker rw"

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(detector, "safe_file_read", return_value=mountinfo_content):
                result = detector._check_mountinfo_container()
                assert result is True

    def test_check_mountinfo_container_with_containerd(self):
        """Test _check_mountinfo_container detects containerd."""
        detector = ContainerDetector()

        mountinfo_content = "cgroup containerd rw"

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(detector, "safe_file_read", return_value=mountinfo_content):
                result = detector._check_mountinfo_container()
                assert result is True

    def test_check_mountinfo_container_host_system(self):
        """Test _check_mountinfo_container returns False for host system."""
        detector = ContainerDetector()

        mountinfo_content = "tmpfs tmpfs rw"

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(detector, "safe_file_read", return_value=mountinfo_content):
                result = detector._check_mountinfo_container()
                assert result is False

    def test_check_mountinfo_container_file_not_exists(self):
        """Test _check_mountinfo_container when file doesn't exist."""
        detector = ContainerDetector()

        with patch("pathlib.Path.exists", return_value=False):
            result = detector._check_mountinfo_container()
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
