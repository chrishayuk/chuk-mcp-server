#!/usr/bin/env python3
"""
Tests for composition configuration loader.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from chuk_mcp_server.composition.config_loader import (
    CompositionConfigLoader,
    load_from_config,
)


class TestCompositionConfigLoader:
    """Test CompositionConfigLoader class."""

    def test_initialization_with_path_string(self, tmp_path):
        """Test initialization with string path."""
        config_path = str(tmp_path / "config.yaml")
        loader = CompositionConfigLoader(config_path)
        assert loader.config_path == Path(config_path)
        assert loader.config == {}

    def test_initialization_with_path_object(self, tmp_path):
        """Test initialization with Path object."""
        config_path = tmp_path / "config.yaml"
        loader = CompositionConfigLoader(config_path)
        assert loader.config_path == config_path
        assert loader.config == {}

    def test_initialization_with_none(self):
        """Test initialization with None defaults to config.yaml."""
        loader = CompositionConfigLoader(None)
        assert loader.config_path == Path("config.yaml")
        assert loader.config == {}

    def test_initialization_default(self):
        """Test initialization without arguments."""
        loader = CompositionConfigLoader()
        assert loader.config_path == Path("config.yaml")
        assert loader.config == {}

    def test_load_file_not_found(self, tmp_path):
        """Test load raises FileNotFoundError when config doesn't exist."""
        config_path = tmp_path / "nonexistent.yaml"
        loader = CompositionConfigLoader(config_path)

        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            loader.load()

    def test_load_valid_config(self, tmp_path):
        """Test loading valid configuration file."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "server": {"name": "test-server", "transport": "http", "port": 8000},
            "composition": {
                "import": [{"name": "github", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}]
            },
        }

        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        loaded = loader.load()

        assert loaded == config_data
        assert loader.config == config_data

    def test_load_with_env_var_substitution(self, tmp_path):
        """Test environment variable substitution during load."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "server": {"name": "test-server"},
            "composition": {"import": [{"name": "github", "env": {"GITHUB_TOKEN": "${TEST_TOKEN}"}}]},
        }

        config_path.write_text(yaml.dump(config_data))

        # Set environment variable
        os.environ["TEST_TOKEN"] = "secret123"

        try:
            loader = CompositionConfigLoader(config_path)
            loaded = loader.load()

            # Check substitution happened
            assert loaded["composition"]["import"][0]["env"]["GITHUB_TOKEN"] == "secret123"
        finally:
            # Clean up
            if "TEST_TOKEN" in os.environ:
                del os.environ["TEST_TOKEN"]

    def test_load_invalid_yaml(self, tmp_path):
        """Test load raises YAMLError for invalid YAML."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("invalid: yaml: [content")

        loader = CompositionConfigLoader(config_path)

        with pytest.raises(yaml.YAMLError):
            loader.load()

    def test_substitute_env_vars_dict(self):
        """Test environment variable substitution in dict."""
        loader = CompositionConfigLoader()
        os.environ["TEST_VAR"] = "test_value"

        try:
            config = {"key1": "${TEST_VAR}", "key2": {"nested": "${TEST_VAR}"}}
            result = loader._substitute_env_vars(config)

            assert result["key1"] == "test_value"
            assert result["key2"]["nested"] == "test_value"
        finally:
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]

    def test_substitute_env_vars_list(self):
        """Test environment variable substitution in list."""
        loader = CompositionConfigLoader()
        os.environ["TEST_VAR"] = "test_value"

        try:
            config = ["${TEST_VAR}", "normal", ["nested", "${TEST_VAR}"]]
            result = loader._substitute_env_vars(config)

            assert result[0] == "test_value"
            assert result[1] == "normal"
            assert result[2][1] == "test_value"
        finally:
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]

    def test_substitute_env_vars_string_with_var(self):
        """Test environment variable substitution in string."""
        loader = CompositionConfigLoader()
        os.environ["TEST_VAR"] = "test_value"

        try:
            result = loader._substitute_env_vars("${TEST_VAR}")
            assert result == "test_value"
        finally:
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]

    def test_substitute_env_vars_string_missing_var(self):
        """Test environment variable substitution with missing var."""
        loader = CompositionConfigLoader()
        # Make sure var doesn't exist
        if "NONEXISTENT_VAR" in os.environ:
            del os.environ["NONEXISTENT_VAR"]

        result = loader._substitute_env_vars("${NONEXISTENT_VAR}")
        # Should return original string if var not found
        assert result == "${NONEXISTENT_VAR}"

    def test_substitute_env_vars_string_no_var(self):
        """Test environment variable substitution with regular string."""
        loader = CompositionConfigLoader()
        result = loader._substitute_env_vars("regular string")
        assert result == "regular string"

    def test_substitute_env_vars_other_types(self):
        """Test environment variable substitution with non-string/dict/list types."""
        loader = CompositionConfigLoader()
        assert loader._substitute_env_vars(123) == 123
        assert loader._substitute_env_vars(True) is True
        assert loader._substitute_env_vars(None) is None
        assert loader._substitute_env_vars(12.34) == 12.34

    def test_apply_to_manager_empty_config(self, tmp_path):
        """Test applying empty configuration to manager."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()

        stats = loader.apply_to_manager(manager)

        assert stats["imported"] == 0
        assert stats["mounted"] == 0
        assert stats["modules"] == 0
        assert stats["skipped"] == 0

    def test_apply_to_manager_with_import(self, tmp_path):
        """Test applying configuration with import section."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "composition": {
                "import": [
                    {"name": "github", "enabled": True, "type": "stdio", "command": "npx", "args": ["-y", "server"]}
                ]
            }
        }
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()
        manager.parent_server = MagicMock()

        with patch("chuk_mcp_server.proxy.manager.ProxyManager") as mock_proxy:
            mock_proxy_instance = MagicMock()
            mock_proxy.return_value = mock_proxy_instance

            stats = loader.apply_to_manager(manager)

            assert stats["imported"] == 1
            assert stats["skipped"] == 0

    def test_apply_to_manager_with_disabled_import(self, tmp_path):
        """Test applying configuration with disabled import."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "composition": {"import": [{"name": "github", "enabled": False, "type": "stdio", "command": "npx"}]}
        }
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()

        stats = loader.apply_to_manager(manager)

        assert stats["imported"] == 0
        assert stats["skipped"] == 1

    def test_apply_to_manager_import_exception(self, tmp_path):
        """Test applying configuration when import fails."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "composition": {"import": [{"name": "github", "enabled": True, "type": "stdio", "command": "npx"}]}
        }
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()
        manager.parent_server = MagicMock()
        # Configure the mock to raise an exception when import_from_config is called
        manager.import_from_config.side_effect = Exception("Import failed")

        stats = loader.apply_to_manager(manager)

        # Should handle exception and not increment imported
        assert stats["imported"] == 0

    def test_apply_to_manager_with_mount(self, tmp_path):
        """Test applying configuration with mount section."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "composition": {
                "mount": [
                    {
                        "name": "api",
                        "enabled": True,
                        "type": "http",
                        "url": "http://localhost:8001",
                        "prefix": "api_",
                    }
                ]
            }
        }
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()

        stats = loader.apply_to_manager(manager)

        assert stats["mounted"] == 1
        assert stats["skipped"] == 0
        manager.mount.assert_called_once()

    def test_apply_to_manager_with_disabled_mount(self, tmp_path):
        """Test applying configuration with disabled mount."""
        config_path = tmp_path / "config.yaml"
        config_data = {"composition": {"mount": [{"name": "api", "enabled": False, "type": "http"}]}}
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()

        stats = loader.apply_to_manager(manager)

        assert stats["mounted"] == 0
        assert stats["skipped"] == 1

    def test_apply_to_manager_mount_exception(self, tmp_path):
        """Test applying configuration when mount fails."""
        config_path = tmp_path / "config.yaml"
        config_data = {"composition": {"mount": [{"name": "api", "enabled": True, "type": "http"}]}}
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()
        manager.mount.side_effect = Exception("Mount failed")

        stats = loader.apply_to_manager(manager)

        # Should handle exception and not increment mounted
        assert stats["mounted"] == 0

    def test_apply_to_manager_with_modules(self, tmp_path):
        """Test applying configuration with modules section."""
        config_path = tmp_path / "config.yaml"
        config_data = {"modules": {"custom_tools": {"module": "my_tools", "enabled": True}}}
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()
        manager.load_module.return_value = {"custom_tools": "loaded"}

        stats = loader.apply_to_manager(manager)

        assert stats["modules"] == 1
        manager.load_module.assert_called_once()

    def test_apply_to_manager_with_disabled_modules(self, tmp_path):
        """Test applying configuration with disabled modules."""
        config_path = tmp_path / "config.yaml"
        config_data = {"modules": {"custom_tools": {"module": "my_tools", "enabled": False}}}
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()

        stats = loader.apply_to_manager(manager)

        # Should not call load_module for disabled modules
        manager.load_module.assert_not_called()
        assert stats["modules"] == 0

    def test_apply_to_manager_modules_exception(self, tmp_path):
        """Test applying configuration when module loading fails."""
        config_path = tmp_path / "config.yaml"
        config_data = {"modules": {"custom_tools": {"module": "my_tools", "enabled": True}}}
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()
        manager.load_module.side_effect = Exception("Module load failed")

        stats = loader.apply_to_manager(manager)

        # Should handle exception and not set modules count
        assert stats["modules"] == 0

    def test_apply_to_manager_loads_config_if_not_loaded(self, tmp_path):
        """Test apply_to_manager loads config if not already loaded."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()

        # Config should be empty before apply
        assert loader.config == {}

        loader.apply_to_manager(manager)

        # Config should be loaded after apply
        assert loader.config == {}  # Empty config but loaded

    def test_import_server_stdio(self, tmp_path):
        """Test _import_server with stdio server."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()
        manager.parent_server = MagicMock()

        server_config = {
            "name": "github",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": "test"},
            "prefix": "gh_",
        }

        loader._import_server(manager, server_config)

        # Verify import_from_config was called with correct arguments
        manager.import_from_config.assert_called_once()
        call_args = manager.import_from_config.call_args
        assert call_args[0][0] == "github"  # server_name
        assert call_args[0][1]["type"] == "stdio"  # config
        assert call_args[1]["prefix"] == "gh_"  # prefix kwarg

    def test_import_server_http(self, tmp_path):
        """Test _import_server with http server."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()
        manager.parent_server = MagicMock()

        server_config = {
            "name": "api",
            "type": "http",
            "url": "http://localhost:8001",
            "timeout": 60,
            "headers": {"Authorization": "Bearer token"},
        }

        loader._import_server(manager, server_config)

        # Verify import_from_config was called with correct arguments
        manager.import_from_config.assert_called_once()
        call_args = manager.import_from_config.call_args
        assert call_args[0][0] == "api"  # server_name
        assert call_args[0][1]["type"] == "http"  # config
        assert call_args[0][1]["url"] == "http://localhost:8001"

    def test_mount_server_http(self, tmp_path):
        """Test _mount_server with http server."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()

        server_config = {
            "name": "api",
            "type": "http",
            "url": "http://localhost:8001",
            "prefix": "api_",
            "as_proxy": True,
            "timeout": 45,
            "headers": {"X-API-Key": "secret"},
        }

        loader._mount_server(manager, server_config)

        # Verify mount was called with correct config
        manager.mount.assert_called_once()
        call_args = manager.mount.call_args
        assert call_args[1]["prefix"] == "api_"
        assert call_args[1]["as_proxy"] is True

    def test_mount_server_sse(self, tmp_path):
        """Test _mount_server with sse server."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        loader = CompositionConfigLoader(config_path)
        manager = MagicMock()

        server_config = {
            "name": "legacy",
            "type": "sse",
            "url": "http://localhost:8002",
            "sse_path": "/sse",
            "message_path": "/message",
            "prefix": "legacy_",
            "as_proxy": False,
        }

        loader._mount_server(manager, server_config)

        manager.mount.assert_called_once()
        call_args = manager.mount.call_args
        assert call_args[0][0]["type"] == "sse"
        assert call_args[1]["as_proxy"] is False

    def test_get_server_config(self, tmp_path):
        """Test get_server_config method."""
        config_path = tmp_path / "config.yaml"
        config_data = {"server": {"name": "test-server", "port": 8000}}
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        server_config = loader.get_server_config()

        assert server_config == {"name": "test-server", "port": 8000}

    def test_get_server_config_loads_if_needed(self, tmp_path):
        """Test get_server_config loads config if not already loaded."""
        config_path = tmp_path / "config.yaml"
        config_data = {"server": {"name": "test-server"}}
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        # Config not loaded yet
        assert loader.config == {}

        server_config = loader.get_server_config()

        # Config should be loaded now
        assert loader.config != {}
        assert server_config == {"name": "test-server"}

    def test_get_logging_config(self, tmp_path):
        """Test get_logging_config method."""
        config_path = tmp_path / "config.yaml"
        config_data = {"logging": {"level": "INFO", "format": "json"}}
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        logging_config = loader.get_logging_config()

        assert logging_config == {"level": "INFO", "format": "json"}

    def test_get_logging_config_empty(self, tmp_path):
        """Test get_logging_config with no logging section."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        loader = CompositionConfigLoader(config_path)
        logging_config = loader.get_logging_config()

        assert logging_config == {}

    def test_get_composition_config(self, tmp_path):
        """Test get_composition_config method."""
        config_path = tmp_path / "config.yaml"
        config_data = {"composition": {"import": [], "mount": []}}
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        composition_config = loader.get_composition_config()

        assert composition_config == {"import": [], "mount": []}

    def test_get_composition_config_empty(self, tmp_path):
        """Test get_composition_config with no composition section."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        loader = CompositionConfigLoader(config_path)
        composition_config = loader.get_composition_config()

        assert composition_config == {}

    def test_get_modules_config(self, tmp_path):
        """Test get_modules_config method."""
        config_path = tmp_path / "config.yaml"
        config_data = {"modules": {"custom": {"module": "my_tools"}}}
        config_path.write_text(yaml.dump(config_data))

        loader = CompositionConfigLoader(config_path)
        modules_config = loader.get_modules_config()

        assert modules_config == {"custom": {"module": "my_tools"}}

    def test_get_modules_config_empty(self, tmp_path):
        """Test get_modules_config with no modules section."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({}))

        loader = CompositionConfigLoader(config_path)
        modules_config = loader.get_modules_config()

        assert modules_config == {}


class TestLoadFromConfig:
    """Test load_from_config convenience function."""

    def test_load_from_config_without_manager(self, tmp_path):
        """Test load_from_config without manager."""
        config_path = tmp_path / "config.yaml"
        config_data = {"server": {"name": "test-server"}}
        config_path.write_text(yaml.dump(config_data))

        config, stats = load_from_config(config_path)

        assert config == config_data
        assert stats == {}

    def test_load_from_config_with_manager(self, tmp_path):
        """Test load_from_config with manager."""
        config_path = tmp_path / "config.yaml"
        config_data = {
            "composition": {
                "import": [{"name": "github", "enabled": True, "type": "stdio", "command": "npx", "args": []}]
            }
        }
        config_path.write_text(yaml.dump(config_data))

        manager = MagicMock()
        manager.parent_server = MagicMock()

        with patch("chuk_mcp_server.proxy.manager.ProxyManager"):
            config, stats = load_from_config(config_path, manager)

            assert config == config_data
            assert stats["imported"] == 1

    def test_load_from_config_default_path(self, tmp_path, monkeypatch):
        """Test load_from_config with default path."""
        # Change to tmp directory
        monkeypatch.chdir(tmp_path)

        config_path = tmp_path / "config.yaml"
        config_data = {"server": {"name": "test-server"}}
        config_path.write_text(yaml.dump(config_data))

        config, stats = load_from_config()

        assert config == config_data
        assert stats == {}

    def test_load_from_config_with_path_string(self, tmp_path):
        """Test load_from_config with string path."""
        config_path = tmp_path / "config.yaml"
        config_data = {"server": {"name": "test-server"}}
        config_path.write_text(yaml.dump(config_data))

        config, stats = load_from_config(str(config_path))

        assert config == config_data
        assert stats == {}
