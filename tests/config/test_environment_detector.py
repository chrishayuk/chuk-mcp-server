#!/usr/bin/env python3
# tests/config/test_environment_detector.py
"""
Unit tests for EnvironmentDetector.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from chuk_mcp_server.config.environment_detector import EnvironmentDetector


class TestEnvironmentDetector:
    """Test environment detection."""

    @patch.dict(os.environ, {"NODE_ENV": "production"}, clear=True)
    def test_detect_production_node_env(self):
        """Test production detection from NODE_ENV."""
        detector = EnvironmentDetector()
        result = detector.detect()
        assert result == "production"

    @patch.dict(os.environ, {"ENV": "prod"}, clear=True)
    def test_detect_production_env(self):
        """Test production detection from ENV."""
        detector = EnvironmentDetector()
        result = detector.detect()
        assert result == "production"

    @patch.dict(os.environ, {"NODE_ENV": "staging"}, clear=True)
    def test_detect_staging(self):
        """Test staging detection."""
        detector = EnvironmentDetector()
        result = detector.detect()
        assert result == "staging"

    @patch.dict(os.environ, {"NODE_ENV": "test"}, clear=True)
    def test_detect_testing(self):
        """Test testing detection."""
        detector = EnvironmentDetector()
        result = detector.detect()
        assert result == "testing"

    @patch.dict(os.environ, {"NODE_ENV": "development"}, clear=True)
    def test_detect_development(self):
        """Test development detection."""
        detector = EnvironmentDetector()
        result = detector.detect()
        assert result == "development"

    @patch.dict(os.environ, {"CI": "true"}, clear=True)
    def test_detect_ci_testing(self):
        """Test CI environment detection."""
        detector = EnvironmentDetector()
        result = detector.detect()
        assert result == "testing"

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True)
    def test_detect_github_actions(self):
        """Test GitHub Actions detection."""
        detector = EnvironmentDetector()
        result = detector.detect()
        assert result == "testing"

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "my-function"}, clear=True)
    def test_detect_serverless_aws(self):
        """Test AWS Lambda serverless detection."""
        detector = EnvironmentDetector()
        result = detector.detect()
        assert result == "serverless"

    @patch.dict(os.environ, {"VERCEL": "1"}, clear=True)
    def test_detect_serverless_vercel(self):
        """Test Vercel serverless detection."""
        detector = EnvironmentDetector()
        result = detector.detect()
        assert result == "serverless"

    @patch.dict(os.environ, {"NETLIFY": "true"}, clear=True)
    def test_detect_serverless_netlify(self):
        """Test Netlify serverless detection."""
        detector = EnvironmentDetector()
        result = detector.detect()
        assert result == "serverless"

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_containerized_production(self):
        """Test containerized environment defaults to production."""
        detector = EnvironmentDetector()

        with patch.object(detector, "_is_containerized", return_value=True):
            result = detector.detect()
            assert result == "production"

    @patch.dict(os.environ, {}, clear=True)
    @patch("pathlib.Path.cwd")
    @patch("pathlib.Path.exists")
    def test_detect_development_from_git(self, mock_exists, mock_cwd):
        """Test development detection from git repository."""
        mock_cwd.return_value = Path("/home/user/project")
        mock_exists.return_value = True  # .git exists

        detector = EnvironmentDetector()

        with patch.object(detector, "_is_containerized", return_value=False):
            result = detector.detect()
            assert result == "development"

    @patch.dict(os.environ, {}, clear=True)
    @patch("pathlib.Path.cwd")
    @patch("pathlib.Path.exists")
    def test_detect_development_from_directory_name(self, mock_exists, mock_cwd):
        """Test development detection from directory name."""
        mock_cwd.return_value = Path("/home/user/dev")
        mock_exists.return_value = False  # No .git

        detector = EnvironmentDetector()

        with patch.object(detector, "_is_containerized", return_value=False):
            result = detector.detect()
            assert result == "development"

    @patch.dict(os.environ, {}, clear=True)
    @patch("pathlib.Path.cwd")
    @patch("pathlib.Path.exists")
    def test_detect_development_from_package_json(self, mock_exists, mock_cwd):
        """Test development detection from package.json without PORT."""
        mock_cwd.return_value = Path("/home/user/project")

        def exists_side_effect(path=None):
            if path:
                return str(path).endswith("package.json")
            # For the .git check
            return str(mock_exists.call_args[0][0]).endswith("package.json")

        mock_exists.side_effect = exists_side_effect

        detector = EnvironmentDetector()

        with patch.object(detector, "_is_containerized", return_value=False):
            result = detector.detect()
            assert result == "development"

    @patch.dict(os.environ, {"PORT": "8080"}, clear=True)
    def test_detect_production_from_port(self):
        """Test production detection when PORT is set without explicit environment."""
        detector = EnvironmentDetector()

        with patch.object(detector, "_is_containerized", return_value=False):
            with patch.object(detector, "_is_development_environment", return_value=False):
                result = detector.detect()
                assert result == "production"

    @patch.dict(os.environ, {}, clear=True)
    @patch("pathlib.Path.cwd")
    @patch("pathlib.Path.exists")
    def test_detect_default_fallback(self, mock_exists, mock_cwd):
        """Test default fallback to development."""
        mock_cwd.return_value = Path("/home/user/project")
        mock_exists.return_value = False  # No .git, no dev files

        detector = EnvironmentDetector()

        with patch.object(detector, "_is_containerized", return_value=False):
            result = detector.detect()
            assert result == "development"

    def test_get_explicit_environment_variations(self):
        """Test various explicit environment variable formats."""
        detector = EnvironmentDetector()

        # Test production variations
        with patch.dict(os.environ, {"NODE_ENV": "PRODUCTION"}, clear=True):
            result = detector._get_explicit_environment()
            assert result == "production"

        with patch.dict(os.environ, {"ENV": "prod"}, clear=True):
            result = detector._get_explicit_environment()
            assert result == "production"

        # Test staging variations
        with patch.dict(os.environ, {"ENVIRONMENT": "stage"}, clear=True):
            result = detector._get_explicit_environment()
            assert result == "staging"

        # Test development variations
        with patch.dict(os.environ, {"NODE_ENV": "dev"}, clear=True):
            result = detector._get_explicit_environment()
            assert result == "development"

    def test_is_ci_environment(self):
        """Test CI environment detection."""
        detector = EnvironmentDetector()

        # Test various CI indicators
        ci_vars = ["CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_HOME"]

        for ci_var in ci_vars:
            with patch.dict(os.environ, {ci_var: "true"}, clear=True):
                assert detector._is_ci_environment() is True

        # Test no CI
        with patch.dict(os.environ, {}, clear=True):
            assert detector._is_ci_environment() is False

    def test_is_serverless_environment(self):
        """Test serverless environment detection."""
        detector = EnvironmentDetector()

        # Test various serverless indicators
        serverless_vars = [
            "AWS_LAMBDA_FUNCTION_NAME",
            "GOOGLE_CLOUD_FUNCTION_NAME",
            "AZURE_FUNCTIONS_ENVIRONMENT",
            "VERCEL",
            "NETLIFY",
        ]

        for serverless_var in serverless_vars:
            with patch.dict(os.environ, {serverless_var: "true"}, clear=True):
                assert detector._is_serverless_environment() is True

        # Test no serverless
        with patch.dict(os.environ, {}, clear=True):
            assert detector._is_serverless_environment() is False

    @patch("pathlib.Path.cwd", side_effect=Exception("Path error"))
    def test_is_development_environment_handles_errors(self, mock_cwd):
        """Test development environment detection handles errors gracefully."""
        detector = EnvironmentDetector()
        result = detector._is_development_environment()
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
