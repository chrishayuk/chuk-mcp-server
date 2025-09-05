#!/usr/bin/env python3
# tests/config/test_smart_config.py
"""
Unit tests for SmartConfig orchestrator.
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from chuk_mcp_server.config.smart_config import SmartConfig


class TestSmartConfig:
    """Test the main SmartConfig orchestrator."""

    def test_initialization(self):
        """Test SmartConfig initializes all detectors."""
        config = SmartConfig()

        # Verify all detectors are created
        assert hasattr(config, "project_detector")
        assert hasattr(config, "environment_detector")
        assert hasattr(config, "network_detector")
        assert hasattr(config, "system_detector")
        assert hasattr(config, "container_detector")

        # Verify cache is initialized
        assert hasattr(config, "_cache")
        assert isinstance(config._cache, dict)

    def test_get_project_name_cached(self):
        """Test project name detection with caching."""
        config = SmartConfig()

        with patch.object(config.project_detector, "detect", return_value="Test Project MCP Server") as mock_detect:
            # First call should trigger detection
            result1 = config.get_project_name()
            assert result1 == "Test Project MCP Server"
            assert mock_detect.call_count == 1

            # Second call should use cache
            result2 = config.get_project_name()
            assert result2 == "Test Project MCP Server"
            assert mock_detect.call_count == 1  # No additional calls

    def test_get_environment_cached(self):
        """Test environment detection with caching."""
        config = SmartConfig()

        with patch.object(config.environment_detector, "detect", return_value="production") as mock_detect:
            # First call should trigger detection
            result1 = config.get_environment()
            assert result1 == "production"
            assert mock_detect.call_count == 1

            # Second call should use cache
            result2 = config.get_environment()
            assert result2 == "production"
            assert mock_detect.call_count == 1

    def test_is_containerized_cached(self):
        """Test container detection with caching."""
        config = SmartConfig()

        with patch.object(config.container_detector, "detect", return_value=True) as mock_detect:
            result1 = config.is_containerized()
            assert result1 is True
            assert mock_detect.call_count == 1

            result2 = config.is_containerized()
            assert result2 is True
            assert mock_detect.call_count == 1

    def test_get_host_with_dependencies(self):
        """Test host detection considers environment and containerization."""
        config = SmartConfig()

        with patch.object(config.environment_detector, "detect", return_value="production"):
            with patch.object(config.container_detector, "detect", return_value=True):
                with patch.object(config.network_detector, "detect_host", return_value="0.0.0.0") as mock_detect_host:
                    result = config.get_host()
                    assert result == "0.0.0.0"
                    mock_detect_host.assert_called_once_with("production", True)

    def test_get_port_cached(self):
        """Test port detection with caching."""
        config = SmartConfig()

        with patch.object(config.network_detector, "detect_port", return_value=8080) as mock_detect:
            result1 = config.get_port()
            assert result1 == 8080
            assert mock_detect.call_count == 1

            result2 = config.get_port()
            assert result2 == 8080
            assert mock_detect.call_count == 1

    def test_get_workers_with_dependencies(self):
        """Test worker detection considers environment and containerization."""
        config = SmartConfig()

        with patch.object(config.environment_detector, "detect", return_value="development"):
            with patch.object(config.container_detector, "detect", return_value=False):
                with patch.object(config.system_detector, "detect_optimal_workers", return_value=4) as mock_detect:
                    result = config.get_workers()
                    assert result == 4
                    mock_detect.assert_called_once_with("development", False)

    def test_get_max_connections_with_dependencies(self):
        """Test max connections detection considers environment and containerization."""
        config = SmartConfig()

        with patch.object(config.environment_detector, "detect", return_value="production"):
            with patch.object(config.container_detector, "detect", return_value=True):
                with patch.object(config.system_detector, "detect_max_connections", return_value=5000) as mock_detect:
                    result = config.get_max_connections()
                    assert result == 5000
                    mock_detect.assert_called_once_with("production", True)

    def test_should_enable_debug_with_environment(self):
        """Test debug detection considers environment."""
        config = SmartConfig()

        with patch.object(config.environment_detector, "detect", return_value="development"):
            with patch.object(config.system_detector, "detect_debug_mode", return_value=True) as mock_detect:
                result = config.should_enable_debug()
                assert result is True
                mock_detect.assert_called_once_with("development")

    def test_get_log_level_with_environment(self):
        """Test log level detection considers environment."""
        config = SmartConfig()

        with patch.object(config.environment_detector, "detect", return_value="production"):
            with patch.object(config.system_detector, "detect_log_level", return_value="WARNING") as mock_detect:
                result = config.get_log_level()
                assert result == "WARNING"
                mock_detect.assert_called_once_with("production")

    def test_get_performance_mode_with_environment(self):
        """Test performance mode detection considers environment."""
        config = SmartConfig()

        with (
            patch.object(config.environment_detector, "detect", return_value="serverless"),
            patch.object(
                config.system_detector, "detect_performance_mode", return_value="serverless_optimized"
            ) as mock_detect,
        ):
            result = config.get_performance_mode()
            assert result == "serverless_optimized"
            mock_detect.assert_called_once_with("serverless")

    def test_get_all_defaults_comprehensive(self):
        """Test comprehensive configuration detection."""
        config = SmartConfig()

        # Mock all detectors
        with patch.object(config.project_detector, "detect", return_value="Test Project MCP Server"):
            with patch.object(config.environment_detector, "detect", return_value="production"):
                with patch.object(config.container_detector, "detect", return_value=True):
                    with patch.object(config.network_detector, "detect_network_config", return_value=("0.0.0.0", 8000)):
                        with patch.object(config.system_detector, "detect_optimal_workers", return_value=4):
                            with patch.object(config.system_detector, "detect_max_connections", return_value=5000):
                                with patch.object(config.system_detector, "detect_debug_mode", return_value=False):
                                    with patch.object(
                                        config.system_detector, "detect_log_level", return_value="WARNING"
                                    ):
                                        with patch.object(
                                            config.system_detector,
                                            "detect_performance_mode",
                                            return_value="high_performance",
                                        ):
                                            result = config.get_all_defaults()

                                            # Verify all expected keys are present
                                            expected_keys = {
                                                "project_name",
                                                "environment",
                                                "host",
                                                "port",
                                                "debug",
                                                "workers",
                                                "max_connections",
                                                "log_level",
                                                "performance_mode",
                                                "containerized",
                                            }
                                            assert set(result.keys()) == expected_keys

                                            # Verify values
                                            assert result["project_name"] == "Test Project MCP Server"
                                            assert result["environment"] == "production"
                                            assert result["host"] == "0.0.0.0"
                                            assert result["port"] == 8000
                                            assert result["debug"] is False
                                            assert result["workers"] == 4
                                            assert result["max_connections"] == 5000
                                            assert result["log_level"] == "WARNING"
                                            assert result["performance_mode"] == "high_performance"
                                            assert result["containerized"] is True

    def test_get_all_defaults_caching(self):
        """Test that get_all_defaults caches results."""
        config = SmartConfig()

        with patch.object(config, "_detect_all") as mock_detect_all:
            # Mock cache with some data
            config._cache = {"test": "cached_data"}

            result = config.get_all_defaults()

            # Should return cached data without calling _detect_all
            assert result == {"test": "cached_data"}
            mock_detect_all.assert_not_called()

    def test_get_all_defaults_triggers_detection(self):
        """Test that get_all_defaults triggers detection when cache is empty."""
        config = SmartConfig()

        with patch.object(config, "_detect_all") as mock_detect_all:
            # Mock _detect_all to populate cache
            def populate_cache():
                config._cache = {"detected": "data"}

            mock_detect_all.side_effect = populate_cache

            result = config.get_all_defaults()

            # Should call _detect_all and return the result
            assert result == {"detected": "data"}
            mock_detect_all.assert_called_once()

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        config = SmartConfig()

        # Populate cache
        config._cache = {"test": "value", "another": "item"}
        assert config._cache

        # Clear cache
        config.clear_cache()
        assert not config._cache
        assert config._cache == {}

    def test_clear_cache_forces_redetection(self):
        """Test that clearing cache forces redetection."""
        config = SmartConfig()

        with patch.object(config.project_detector, "detect", side_effect=["First", "Second"]) as mock_detect:
            # First call
            result1 = config.get_project_name()
            assert result1 == "First"
            assert mock_detect.call_count == 1

            # Clear cache
            config.clear_cache()

            # Second call should trigger detection again
            result2 = config.get_project_name()
            assert result2 == "Second"
            assert mock_detect.call_count == 2

    def test_get_summary(self):
        """Test configuration summary generation."""
        config = SmartConfig()

        # Mock get_all_defaults
        mock_config = {
            "project_name": "Test Project MCP Server",
            "environment": "production",
            "host": "0.0.0.0",
            "port": 8000,
            "containerized": True,
            "performance_mode": "high_performance",
            "workers": 4,
            "max_connections": 5000,
            "log_level": "WARNING",
            "debug": False,
        }

        with patch.object(config, "get_all_defaults", return_value=mock_config):
            result = config.get_summary()

            # Verify structure
            assert "detection_summary" in result
            assert "full_config" in result

            # Verify summary content
            summary = result["detection_summary"]
            assert summary["project"] == "Test Project MCP Server"
            assert summary["environment"] == "production"
            assert summary["network"] == "0.0.0.0:8000"
            assert summary["containerized"] is True
            assert summary["performance"] == "high_performance"
            assert summary["resources"] == "4 workers, 5000 max connections"
            assert summary["logging"] == "WARNING level, debug=False"

            # Verify full config is included
            assert result["full_config"] == mock_config

    def test_detect_all_method(self):
        """Test the internal _detect_all method."""
        config = SmartConfig()

        # Mock all detectors
        with patch.object(config.project_detector, "detect", return_value="Test Project"):
            with patch.object(config.environment_detector, "detect", return_value="development"):
                with patch.object(config.container_detector, "detect", return_value=False):
                    with patch.object(
                        config.network_detector, "detect_network_config", return_value=("localhost", 8000)
                    ):
                        with patch.object(config.system_detector, "detect_optimal_workers", return_value=2):
                            with patch.object(config.system_detector, "detect_max_connections", return_value=1000):
                                with patch.object(config.system_detector, "detect_debug_mode", return_value=True):
                                    with patch.object(config.system_detector, "detect_log_level", return_value="INFO"):
                                        with patch.object(
                                            config.system_detector,
                                            "detect_performance_mode",
                                            return_value="development",
                                        ):
                                            # Call _detect_all
                                            config._detect_all()

                                            # Verify cache is populated
                                            assert config._cache["project_name"] == "Test Project"
                                            assert config._cache["environment"] == "development"
                                            assert config._cache["host"] == "localhost"
                                            assert config._cache["port"] == 8000
                                            assert config._cache["containerized"] is False
                                            assert config._cache["workers"] == 2
                                            assert config._cache["max_connections"] == 1000
                                            assert config._cache["debug"] is True
                                            assert config._cache["log_level"] == "INFO"
                                            assert config._cache["performance_mode"] == "development"


class TestSmartConfigIntegration:
    """Integration tests for SmartConfig with realistic scenarios."""

    @patch("pathlib.Path.cwd")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    @patch.dict(os.environ, {"NODE_ENV": "production", "PORT": "3000", "CONTAINER": "docker"})
    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    @patch("socket.socket")
    def test_production_docker_scenario(
        self, mock_socket, mock_memory, mock_cpu_count, mock_exists, mock_read_text, mock_cwd
    ):
        """Test complete production Docker scenario."""
        # Setup mocks
        mock_cwd.return_value = Path("/app/my-web-service")
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({"name": "my-web-service"})
        mock_cpu_count.return_value = 4
        mock_memory.return_value.available = 4 * 1024**3
        mock_memory.return_value.total = 4 * 1024**3

        # Mock socket for port check (though PORT is set)
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock

        config = SmartConfig()
        result = config.get_all_defaults()

        # Verify production Docker configuration
        assert result["project_name"] == "My Web Service MCP Server"
        assert result["environment"] == "production"
        assert result["host"] == "0.0.0.0"
        assert result["port"] == 3000
        assert result["debug"] is False
        assert result["containerized"] is True
        assert result["performance_mode"] == "high_performance"
        assert result["log_level"] == "WARNING"

    @patch("pathlib.Path.cwd")
    @patch("pathlib.Path.exists")
    @patch.dict(os.environ, {"NODE_ENV": "development"}, clear=True)
    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    @patch("socket.socket")
    def test_development_local_scenario(self, mock_socket, mock_memory, mock_cpu_count, mock_exists, mock_cwd):
        """Test complete development local scenario."""
        # Setup mocks
        mock_cwd.return_value = Path("/home/dev/my-project")
        mock_exists.return_value = True  # .git exists
        mock_cpu_count.return_value = 8
        mock_memory.return_value.available = 16 * 1024**3
        mock_memory.return_value.total = 16 * 1024**3

        # Mock socket for port detection
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.bind.return_value = None

        config = SmartConfig()

        # Need to ensure containerized detection returns False for development
        with patch.object(config.container_detector, "detect", return_value=False):
            result = config.get_all_defaults()

            # Verify development configuration
            assert result["project_name"] == "My Project MCP Server"
            assert result["environment"] == "development"
            assert result["host"] == "localhost"  # Should be localhost for non-containerized dev
            assert result["port"] == 8000
            assert result["debug"] is True
            assert result["containerized"] is False
            assert result["performance_mode"] == "development"
            assert result["log_level"] == "INFO"

    @patch("pathlib.Path.cwd")
    @patch.dict(
        os.environ,
        {
            "AWS_LAMBDA_FUNCTION_NAME": "my-function",
            "AWS_REGION": "us-east-1",
            "CI": "",
            "GITHUB_ACTIONS": "",
            "JENKINS": "",
            "TRAVIS": "",
        },
        clear=False,
    )
    @patch("psutil.cpu_count")
    @patch("psutil.virtual_memory")
    def test_serverless_aws_scenario(self, mock_memory, mock_cpu_count, mock_cwd):
        """Test complete AWS Lambda serverless scenario."""
        # Setup
        mock_cwd.return_value = Path("/var/task")
        mock_cpu_count.return_value = 2  # Lambda has limited CPU
        mock_memory.return_value.available = 512 * 1024**2  # 512MB
        mock_memory.return_value.total = 512 * 1024**2

        config = SmartConfig()
        result = config.get_all_defaults()

        # Verify serverless configuration
        assert result["environment"] == "serverless"
        assert result["host"] == "0.0.0.0"
        assert result["debug"] is False
        assert result["workers"] == 1  # Serverless uses single worker
        assert result["max_connections"] == 100  # Limited for serverless
        assert result["performance_mode"] == "serverless_optimized"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
