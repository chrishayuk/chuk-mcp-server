#!/usr/bin/env python3
# tests/config/test_diagnostic.py
"""
Diagnostic tests to verify basic functionality.
"""

import pytest
from unittest.mock import patch

from chuk_mcp_server.config.container_detector import ContainerDetector
from chuk_mcp_server.config.network_detector import NetworkDetector


def test_container_detector_basic():
    """Basic test of container detector."""
    detector = ContainerDetector()
    
    # Mock all methods to return False
    with patch.object(detector, '_check_docker_env', return_value=False):
        with patch.object(detector, '_check_kubernetes', return_value=False):
            with patch.object(detector, '_check_generic_container', return_value=False):
                with patch.object(detector, '_check_cgroup_container', return_value=False):
                    with patch.object(detector, '_check_mountinfo_container', return_value=False):
                        result = detector.detect()
                        assert result is False
    
    # Test with one method returning True
    with patch.object(detector, '_check_docker_env', return_value=True):
        result = detector.detect()
        assert result is True


def test_network_detector_basic():
    """Basic test of network detector."""
    detector = NetworkDetector()
    
    # Test basic functionality
    with patch.dict('os.environ', {'VERCEL': '1'}, clear=True):
        port = detector.detect_port()
        assert port == 3000
    
    with patch.dict('os.environ', {'PORT': '8080'}, clear=True):
        port = detector.detect_port()
        assert port == 8080


def test_container_detector_docker_env():
    """Test Docker environment detection directly."""
    detector = ContainerDetector()
    
    # Test the actual _check_docker_env method
    with patch('pathlib.Path.exists', return_value=True):
        result = detector._check_docker_env()
        assert result is True
    
    with patch('pathlib.Path.exists', return_value=False):
        result = detector._check_docker_env()
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])