#!/usr/bin/env python3
# tests/config/test_system_detector.py
"""
Unit tests for SystemDetector.
"""

import os
from unittest.mock import patch

import pytest

from chuk_mcp_server.config.system_detector import SystemDetector


class TestSystemDetector:
    """Test system resource detection."""

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_optimal_workers_production_low_core(self, mock_memory, mock_cpu_count):
        """Test worker calculation for production with low cores."""
        mock_cpu_count.return_value = 2
        mock_memory.return_value.available = 2 * 1024**3  # 2GB

        detector = SystemDetector()
        result = detector.detect_optimal_workers("production", False)
        assert result == 2

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_optimal_workers_production_medium_core(self, mock_memory, mock_cpu_count):
        """Test worker calculation for production with medium cores."""
        mock_cpu_count.return_value = 8
        mock_memory.return_value.available = 8 * 1024**3  # 8GB

        detector = SystemDetector()
        result = detector.detect_optimal_workers("production", False)
        assert result == 8

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_optimal_workers_production_high_core(self, mock_memory, mock_cpu_count):
        """Test worker calculation for production with high cores."""
        mock_cpu_count.return_value = 32
        mock_memory.return_value.available = 32 * 1024**3  # 32GB

        detector = SystemDetector()
        result = detector.detect_optimal_workers("production", False)
        assert result == int(32 * 0.6)  # 60% of cores = 19

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_optimal_workers_serverless(self, mock_memory, mock_cpu_count):
        """Test worker calculation for serverless environment."""
        mock_cpu_count.return_value = 4
        mock_memory.return_value.available = 4 * 1024**3  # 4GB

        detector = SystemDetector()
        result = detector.detect_optimal_workers("serverless", False)
        assert result == 1  # Serverless always uses 1 worker

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_optimal_workers_development(self, mock_memory, mock_cpu_count):
        """Test worker calculation for development environment."""
        mock_cpu_count.return_value = 8
        mock_memory.return_value.available = 8 * 1024**3  # 8GB

        detector = SystemDetector()
        result = detector.detect_optimal_workers("development", False)
        assert result == 4  # Half cores for development, max 4

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_optimal_workers_development_high_core(self, mock_memory, mock_cpu_count):
        """Test worker calculation for development with many cores."""
        mock_cpu_count.return_value = 16
        mock_memory.return_value.available = 16 * 1024**3  # 16GB

        detector = SystemDetector()
        result = detector.detect_optimal_workers("development", False)
        assert result == 4  # Capped at 4 for development

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_optimal_workers_containerized_good_memory(self, mock_memory, mock_cpu_count):
        """Test worker calculation for containerized with good memory."""
        mock_cpu_count.return_value = 4
        mock_memory.return_value.available = 4 * 1024**3  # 4GB (good memory)

        detector = SystemDetector()
        result = detector.detect_optimal_workers("production", True)
        assert result == 4  # Full cores when memory is sufficient

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_optimal_workers_containerized_limited_memory(self, mock_memory, mock_cpu_count):
        """Test worker calculation for containerized with limited memory."""
        mock_cpu_count.return_value = 4
        mock_memory.return_value.available = 1 * 1024**3  # 1GB (limited)

        detector = SystemDetector()
        result = detector.detect_optimal_workers("production", True)
        assert result == 2  # Conservative for limited memory

    @patch("psutil.cpu_count", side_effect=Exception("psutil error"))
    def test_detect_optimal_workers_fallback(self, mock_cpu_count):
        """Test worker calculation fallback when psutil fails."""
        detector = SystemDetector()
        result = detector.detect_optimal_workers()
        assert result == 1

    @patch("psutil.virtual_memory")
    def test_detect_max_connections_high_memory(self, mock_memory):
        """Test connection limit calculation for high memory systems."""
        mock_memory.return_value.available = 16 * 1024**3  # 16GB

        detector = SystemDetector()
        result = detector.detect_max_connections("production", False)
        expected = min(int(16 * 800), 10000)  # 800 connections per GB, max 10k
        assert result == expected

    @patch("psutil.virtual_memory")
    def test_detect_max_connections_serverless(self, mock_memory):
        """Test connection limit calculation for serverless environment."""
        mock_memory.return_value.available = 1 * 1024**3  # 1GB

        detector = SystemDetector()
        result = detector.detect_max_connections("serverless", False)
        assert result == 100  # Serverless limit

    @patch("psutil.virtual_memory")
    def test_detect_max_connections_development(self, mock_memory):
        """Test connection limit calculation for development environment."""
        mock_memory.return_value.available = 8 * 1024**3  # 8GB

        detector = SystemDetector()
        result = detector.detect_max_connections("development", False)
        assert result == min(int(8 * 800), 1000)  # Dev limit is 1000

    @patch("psutil.virtual_memory")
    def test_detect_max_connections_containerized(self, mock_memory):
        """Test connection limit calculation for containerized environment."""
        mock_memory.return_value.available = 4 * 1024**3  # 4GB

        detector = SystemDetector()
        result = detector.detect_max_connections("production", True)
        assert result == min(int(4 * 800), 5000)  # Container limit is 5000

    @patch("psutil.virtual_memory", side_effect=Exception("psutil error"))
    def test_detect_max_connections_fallback(self, mock_memory):
        """Test connection limit fallback when psutil fails."""
        detector = SystemDetector()
        result = detector.detect_max_connections()
        assert result == 1000

    @patch.dict(os.environ, {"DEBUG": "true"})
    def test_detect_debug_explicit_true(self):
        """Test debug detection with explicit DEBUG=true."""
        detector = SystemDetector()
        result = detector.detect_debug_mode()
        assert result is True

    @patch.dict(os.environ, {"DEBUG": "false"})
    def test_detect_debug_explicit_false(self):
        """Test debug detection with explicit DEBUG=false."""
        detector = SystemDetector()
        result = detector.detect_debug_mode()
        assert result is False

    @patch.dict(os.environ, {"DEBUG": "1"})
    def test_detect_debug_numeric_true(self):
        """Test debug detection with DEBUG=1."""
        detector = SystemDetector()
        result = detector.detect_debug_mode()
        assert result is True

    @patch.dict(os.environ, {"DEBUG": "0"})
    def test_detect_debug_numeric_false(self):
        """Test debug detection with DEBUG=0."""
        detector = SystemDetector()
        result = detector.detect_debug_mode()
        assert result is False

    @patch.dict(os.environ, {"DEBUG": "yes"})
    def test_detect_debug_yes(self):
        """Test debug detection with DEBUG=yes."""
        detector = SystemDetector()
        result = detector.detect_debug_mode()
        assert result is True

    @patch.dict(os.environ, {"DEBUG": "on"})
    def test_detect_debug_on(self):
        """Test debug detection with DEBUG=on."""
        detector = SystemDetector()
        result = detector.detect_debug_mode()
        assert result is True

    def test_detect_debug_development_env(self):
        """Test debug enabled by default in development environment."""
        detector = SystemDetector()
        result = detector.detect_debug_mode("development")
        assert result is True

    def test_detect_debug_testing_env(self):
        """Test debug enabled by default in testing environment."""
        detector = SystemDetector()
        result = detector.detect_debug_mode("testing")
        assert result is True

    def test_detect_debug_production_env(self):
        """Test debug disabled by default in production environment."""
        detector = SystemDetector()
        result = detector.detect_debug_mode("production")
        assert result is False

    def test_detect_debug_no_environment(self):
        """Test debug default when no environment specified."""
        detector = SystemDetector()
        result = detector.detect_debug_mode()
        assert result is True  # Default to True when no environment

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_detect_log_level_explicit(self):
        """Test log level detection with explicit LOG_LEVEL."""
        detector = SystemDetector()
        result = detector.detect_log_level()
        assert result == "DEBUG"

    @patch.dict(os.environ, {"LOG_LEVEL": "info"})  # Test case insensitivity
    def test_detect_log_level_case_insensitive(self):
        """Test log level detection is case insensitive."""
        detector = SystemDetector()
        result = detector.detect_log_level()
        assert result == "INFO"

    @patch.dict(os.environ, {"LOG_LEVEL": "invalid"})
    def test_detect_log_level_invalid_explicit(self):
        """Test log level detection with invalid LOG_LEVEL."""
        detector = SystemDetector()
        result = detector.detect_log_level("development")
        assert result == "INFO"  # Should fall back to environment-based default

    def test_detect_log_level_development(self):
        """Test log level for development environment."""
        detector = SystemDetector()
        result = detector.detect_log_level("development")
        assert result == "INFO"

    def test_detect_log_level_testing(self):
        """Test log level for testing environment."""
        detector = SystemDetector()
        result = detector.detect_log_level("testing")
        assert result == "WARNING"

    def test_detect_log_level_production(self):
        """Test log level for production environment."""
        detector = SystemDetector()
        result = detector.detect_log_level("production")
        assert result == "WARNING"

    def test_detect_log_level_no_environment(self):
        """Test log level default when no environment specified."""
        detector = SystemDetector()
        result = detector.detect_log_level()
        assert result == "INFO"

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_performance_mode_ultra_high(self, mock_memory, mock_cpu_count):
        """Test ultra high performance mode detection."""
        mock_cpu_count.return_value = 16
        mock_memory.return_value.total = 16 * 1024**3  # 16GB

        detector = SystemDetector()
        result = detector.detect_performance_mode("production")
        assert result == "ultra_high_performance"

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_performance_mode_high(self, mock_memory, mock_cpu_count):
        """Test high performance mode detection."""
        mock_cpu_count.return_value = 4
        mock_memory.return_value.total = 4 * 1024**3  # 4GB

        detector = SystemDetector()
        result = detector.detect_performance_mode("production")
        assert result == "high_performance"

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_performance_mode_balanced(self, mock_memory, mock_cpu_count):
        """Test balanced performance mode detection."""
        mock_cpu_count.return_value = 2
        mock_memory.return_value.total = 2 * 1024**3  # 2GB

        detector = SystemDetector()
        result = detector.detect_performance_mode("production")
        assert result == "balanced"

    def test_detect_performance_mode_serverless(self):
        """Test serverless performance mode detection."""
        detector = SystemDetector()
        result = detector.detect_performance_mode("serverless")
        assert result == "serverless_optimized"

    def test_detect_performance_mode_development(self):
        """Test development performance mode detection."""
        detector = SystemDetector()
        result = detector.detect_performance_mode("development")
        assert result == "development"

    def test_detect_performance_mode_testing(self):
        """Test testing performance mode detection."""
        detector = SystemDetector()
        result = detector.detect_performance_mode("testing")
        assert result == "testing"

    @patch("psutil.cpu_count", side_effect=Exception("psutil error"))
    def test_detect_performance_mode_fallback(self, mock_cpu_count):
        """Test performance mode fallback when psutil fails."""
        detector = SystemDetector()
        result = detector.detect_performance_mode()
        assert result == "balanced"

    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_detect_returns_comprehensive_dict(self, mock_memory, mock_cpu_count):
        """Test that detect() method returns comprehensive system configuration."""
        mock_cpu_count.return_value = 4
        mock_memory.return_value.available = 4 * 1024**3
        mock_memory.return_value.total = 4 * 1024**3

        detector = SystemDetector()
        result = detector.detect()

        expected_keys = {"workers", "max_connections", "debug", "log_level", "performance_mode"}
        assert set(result.keys()) == expected_keys

        # Verify types
        assert isinstance(result["workers"], int)
        assert isinstance(result["max_connections"], int)
        assert isinstance(result["debug"], bool)
        assert isinstance(result["log_level"], str)
        assert isinstance(result["performance_mode"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
