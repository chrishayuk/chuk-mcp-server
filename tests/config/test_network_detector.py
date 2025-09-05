#!/usr/bin/env python3
# tests/config/test_network_detector.py
"""
Unit tests for NetworkDetector.
"""

import os
import socket
from unittest.mock import MagicMock, patch

import pytest

from chuk_mcp_server.config.network_detector import NetworkDetector


class TestNetworkDetector:
    """Test network configuration detection."""

    def test_detect_host_production(self):
        """Test host detection for production."""
        detector = NetworkDetector()
        result = detector.detect_host("production", False)
        assert result == "0.0.0.0"

    def test_detect_host_development(self):
        """Test host detection for development."""
        detector = NetworkDetector()
        result = detector.detect_host("development", False)
        assert result == "localhost"

    def test_detect_host_serverless(self):
        """Test host detection for serverless."""
        detector = NetworkDetector()
        result = detector.detect_host("serverless", False)
        assert result == "0.0.0.0"

    def test_detect_host_containerized(self):
        """Test host detection when containerized."""
        detector = NetworkDetector()
        result = detector.detect_host("development", True)
        assert result == "0.0.0.0"

    @patch.dict(os.environ, {"VERCEL": "1"})
    def test_detect_host_vercel(self):
        """Test host detection for Vercel platform."""
        detector = NetworkDetector()
        result = detector.detect_host()
        assert result == "0.0.0.0"

    @patch.dict(os.environ, {"RAILWAY_ENVIRONMENT": "production"})
    def test_detect_host_railway(self):
        """Test host detection for Railway platform."""
        detector = NetworkDetector()
        result = detector.detect_host()
        assert result == "0.0.0.0"

    @patch.dict(os.environ, {"HEROKU_APP_NAME": "my-app"})
    def test_detect_host_heroku(self):
        """Test host detection for Heroku platform."""
        detector = NetworkDetector()
        result = detector.detect_host()
        assert result == "0.0.0.0"

    @patch.dict(os.environ, {"PORT": "8080"})
    def test_detect_port_from_env(self):
        """Test port detection from environment variable."""
        detector = NetworkDetector()
        result = detector.detect_port()
        assert result == 8080

    @patch.dict(os.environ, {"PORT": "invalid"})
    def test_detect_port_invalid_env(self):
        """Test port detection with invalid PORT environment variable."""
        detector = NetworkDetector()

        with patch.object(detector, "_is_port_available", return_value=True):
            result = detector.detect_port()
            assert result == 8000  # Should fall back to preferred ports

    @patch.dict(os.environ, {"PORT": "99999"})  # Out of valid range
    def test_detect_port_out_of_range(self):
        """Test port detection with out-of-range PORT value."""
        detector = NetworkDetector()

        with patch.object(detector, "_is_port_available", return_value=True):
            result = detector.detect_port()
            assert result == 8000  # Should fall back to preferred ports

    @patch.dict(os.environ, {"VERCEL": "1"})
    def test_detect_port_vercel(self):
        """Test port detection for Vercel platform."""
        detector = NetworkDetector()
        result = detector.detect_port()
        assert result == 3000

    @patch.dict(os.environ, {"NETLIFY": "1"})
    def test_detect_port_netlify(self):
        """Test port detection for Netlify platform."""
        detector = NetworkDetector()
        result = detector.detect_port()
        assert result == 8888

    @patch.dict(os.environ, {"RAILWAY_ENVIRONMENT": "production"})
    def test_detect_port_railway(self):
        """Test port detection for Railway platform."""
        detector = NetworkDetector()
        result = detector.detect_port()
        assert result == 8000

    def test_detect_port_scanning_preferred(self):
        """Test port detection through scanning preferred ports."""
        detector = NetworkDetector()

        with patch.object(detector, "_is_port_available") as mock_available:
            # Mock 8000 as available (first preferred port)
            mock_available.return_value = True
            result = detector.detect_port()
            assert result == 8000

    def test_detect_port_scanning_second_preferred(self):
        """Test port detection finds second preferred port."""
        detector = NetworkDetector()

        with patch.object(detector, "_is_port_available") as mock_available:
            # Mock 8000 as unavailable, 8001 as available
            mock_available.side_effect = lambda port: port == 8001
            result = detector.detect_port()
            assert result == 8001

    def test_detect_port_scanning_range_8000(self):
        """Test port detection scans 8000-8100 range."""
        detector = NetworkDetector()

        with patch.object(detector, "_is_port_available") as mock_available:
            # Mock all preferred ports as unavailable, 8050 as available
            mock_available.side_effect = lambda port: port == 8050
            result = detector.detect_port()
            assert result == 8050

    def test_detect_port_scanning_range_3000(self):
        """Test port detection scans 3000-3100 range."""
        detector = NetworkDetector()

        with patch.object(detector, "_is_port_available") as mock_available:
            # Mock all other ports as unavailable, 3050 as available
            mock_available.side_effect = lambda port: port == 3050
            result = detector.detect_port()
            assert result == 3050

    def test_detect_port_fallback(self):
        """Test port detection fallback when all ports seem unavailable."""
        detector = NetworkDetector()

        with patch.object(detector, "_is_port_available", return_value=False):
            result = detector.detect_port()
            assert result == 8000  # Should fall back to 8000

    @patch("socket.socket")
    def test_is_port_available_true(self, mock_socket):
        """Test port availability check - port is available."""
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.bind.return_value = None  # No exception = port available

        detector = NetworkDetector()
        result = detector._is_port_available(8000)
        assert result is True

        # Verify socket configuration
        mock_sock.setsockopt.assert_called_once_with(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mock_sock.bind.assert_called_once_with(("localhost", 8000))

    @patch("socket.socket")
    def test_is_port_available_false(self, mock_socket):
        """Test port availability check - port is unavailable."""
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.bind.side_effect = OSError("Port already in use")

        detector = NetworkDetector()
        result = detector._is_port_available(8000)
        assert result is False

    @patch("socket.socket")
    def test_is_port_available_generic_exception(self, mock_socket):
        """Test port availability check handles generic exceptions."""
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.bind.side_effect = Exception("Generic socket error")

        detector = NetworkDetector()
        result = detector._is_port_available(8000)
        assert result is False

    def test_detect_network_config(self):
        """Test detection of both host and port configuration."""
        detector = NetworkDetector()

        with patch.object(detector, "detect_host", return_value="0.0.0.0"):
            with patch.object(detector, "detect_port", return_value=8080):
                host, port = detector.detect_network_config("production", True)
                assert host == "0.0.0.0"
                assert port == 8080

    def test_detect_returns_dict(self):
        """Test that detect() method returns proper dictionary."""
        detector = NetworkDetector()

        with patch.object(detector, "detect_host", return_value="localhost"):
            with patch.object(detector, "detect_port", return_value=8000):
                result = detector.detect()
                assert isinstance(result, dict)
                assert result == {"host": "localhost", "port": 8000}

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_no_platform_variables(self):
        """Test detection when no platform-specific variables are set."""
        detector = NetworkDetector()

        with patch.object(detector, "_is_port_available", return_value=True):
            host = detector.detect_host("development", False)
            port = detector.detect_port()

            assert host == "localhost"
            assert port == 8000  # First available preferred port

    def test_platform_host_priority(self):
        """Test that platform-specific hosts take priority."""
        detector = NetworkDetector()

        # Test multiple platform variables set (should use first found)
        with patch.dict(os.environ, {"VERCEL": "1", "HEROKU_APP_NAME": "test"}):
            result = detector.detect_host()
            assert result == "0.0.0.0"  # Should detect one of the platforms

    def test_platform_port_priority(self):
        """Test that platform-specific ports take priority over PORT env var."""
        detector = NetworkDetector()

        # Test the specific priority logic by checking platform ports first
        # This tests the actual implementation logic directly

        # Mock get_env_var to simulate both VERCEL and PORT being set
        with patch.object(detector, "get_env_var") as mock_get_env:

            def side_effect(key, default=None):
                if key == "VERCEL":
                    return "1"
                elif key == "NETLIFY" or key == "RAILWAY_ENVIRONMENT":
                    return None
                elif key == "PORT":
                    return "9000"
                else:
                    return default

            mock_get_env.side_effect = side_effect

            result = detector.detect_port()

            # Verify that get_env_var was called for platform checks
            assert mock_get_env.called

            # Should return 3000 (VERCEL port) not 9000 (PORT value)
            assert result == 3000, f"Expected 3000 (Vercel port), but got {result}. Platform priority not working."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
