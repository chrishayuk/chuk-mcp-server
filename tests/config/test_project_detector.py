#!/usr/bin/env python3
# tests/config/test_project_detector.py
"""
Unit tests for ProjectDetector.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from chuk_mcp_server.config.project_detector import ProjectDetector


class TestProjectDetector:
    """Test project name detection."""

    @patch("pathlib.Path.cwd")
    def test_detect_from_directory(self, mock_cwd):
        """Test project name detection from current directory."""
        mock_cwd.return_value = Path("/home/user/my-awesome-project")

        detector = ProjectDetector()
        result = detector.detect()
        assert result == "My Awesome Project MCP Server"

    @patch("pathlib.Path.cwd")
    def test_detect_skips_generic_dirs(self, mock_cwd):
        """Test that generic directory names like 'src' are skipped."""
        mock_cwd.return_value = Path("/home/user/project/src")

        detector = ProjectDetector()
        result = detector.detect()
        assert result == "Project MCP Server"

    @patch("pathlib.Path.cwd")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_detect_from_package_json(self, mock_exists, mock_read_text, mock_cwd):
        """Test project name detection from package.json."""
        mock_cwd.return_value = Path("/home/user/src")

        # Mock the package.json file path
        package_json_path = Path("/home/user/src/package.json")
        mock_exists.side_effect = lambda: True

        package_data = {"name": "my-node-project", "version": "1.0.0"}
        mock_read_text.return_value = json.dumps(package_data)

        detector = ProjectDetector()

        # Patch the specific file reading
        with patch.object(detector, "safe_file_read", return_value=json.dumps(package_data)):
            result = detector.detect()
            assert result == "My Node Project MCP Server"

    @patch("pathlib.Path.cwd")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_detect_from_pyproject_toml(self, mock_exists, mock_read_text, mock_cwd):
        """Test project name detection from pyproject.toml."""
        mock_cwd.return_value = Path("/home/user/src")
        mock_exists.return_value = True

        toml_content = """
[tool.poetry]
name = "my-python-package"
version = "0.1.0"
        """

        detector = ProjectDetector()
        with patch.object(detector, "safe_file_read", return_value=toml_content.strip()):
            result = detector.detect()
            assert result == "My Python Package MCP Server"

    @patch("pathlib.Path.cwd")
    def test_detect_from_setup_py(self, mock_cwd):
        """Test project name detection from setup.py."""
        mock_cwd.return_value = Path("/home/user/src")

        setup_content = """
from setuptools import setup

setup(
    name="my-setup-package",
    version="1.0.0"
)
        """

        detector = ProjectDetector()
        with patch.object(detector, "safe_file_read", return_value=setup_content):
            result = detector.detect()
            assert result == "My Setup Package MCP Server"

    @patch("pathlib.Path.cwd")
    def test_detect_from_cargo_toml(self, mock_cwd):
        """Test project name detection from Cargo.toml."""
        mock_cwd.return_value = Path("/home/user/src")

        cargo_content = """
[package]
name = "my-rust-project"
version = "0.1.0"
        """

        detector = ProjectDetector()
        with patch.object(detector, "safe_file_read", return_value=cargo_content.strip()):
            result = detector.detect()
            assert result == "My Rust Project MCP Server"

    @patch("pathlib.Path.cwd")
    def test_detect_from_parent_directory(self, mock_cwd):
        """Test fallback to parent directory for common subdirectories."""
        mock_cwd.return_value = Path("/home/user/awesome-project/lib")

        detector = ProjectDetector()
        result = detector.detect()
        assert result == "Awesome Project MCP Server"

    @patch("pathlib.Path.cwd")
    def test_detect_fallback_when_no_config_files(self, mock_cwd):
        """Test fallback when no config files exist."""
        mock_cwd.return_value = Path("/tmp/random-dir")

        detector = ProjectDetector()

        # Mock all safe_file_read calls to return None (file doesn't exist)
        with patch.object(detector, "safe_file_read", return_value=None):
            result = detector.detect()
            assert result == "Smart MCP Server"

    @patch("pathlib.Path.cwd", side_effect=Exception("Path error"))
    def test_detect_handles_path_errors(self, mock_cwd):
        """Test project name detection handles Path errors gracefully."""
        detector = ProjectDetector()
        result = detector.detect()
        assert result == "Smart MCP Server"

    def test_format_project_name(self):
        """Test project name formatting."""
        detector = ProjectDetector()

        # Test underscore replacement
        result = detector._format_project_name("my_awesome_project")
        assert result == "My Awesome Project MCP Server"

        # Test hyphen replacement
        result = detector._format_project_name("my-web-app")
        assert result == "My Web App MCP Server"

        # Test mixed
        result = detector._format_project_name("my_web-service")
        assert result == "My Web Service MCP Server"

    def test_detect_from_directory_empty_name(self):
        """Test detection when directory name is empty or None."""
        detector = ProjectDetector()

        with patch("pathlib.Path.cwd") as mock_cwd:
            # Mock empty directory name
            mock_path = MagicMock()
            mock_path.name = ""
            mock_cwd.return_value = mock_path

            result = detector._detect_from_directory()
            assert result is None

    def test_safe_file_read_nonexistent(self):
        """Test safe_file_read with non-existent file."""
        detector = ProjectDetector()

        with patch("pathlib.Path.exists", return_value=False):
            result = detector.safe_file_read(Path("/nonexistent/file.txt"))
            assert result is None

    def test_safe_json_parse_invalid(self):
        """Test safe_json_parse with invalid JSON."""
        detector = ProjectDetector()

        result = detector.safe_json_parse("invalid json {")
        assert result is None

    def test_safe_json_parse_valid(self):
        """Test safe_json_parse with valid JSON."""
        detector = ProjectDetector()

        result = detector.safe_json_parse('{"name": "test-project"}')
        assert result == {"name": "test-project"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
