#!/usr/bin/env python3
# src/chuk_mcp_server/composition/config_loader.py
"""
Configuration Loader - Load and apply composition configuration from YAML

This module handles loading configuration files and applying them to the
composition manager to create unified multi-server deployments.
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class CompositionConfigLoader:
    """Loads and applies composition configuration from YAML files."""

    def __init__(self, config_path: str | Path | None = None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Path to config.yaml file. If None, looks for config.yaml in current directory.
        """
        self.config_path = Path(config_path) if config_path else Path("config.yaml")
        self.config: dict[str, Any] = {}

    def load(self) -> dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Dictionary containing configuration

        Raises:
            FileNotFoundError: If config file not found
            yaml.YAMLError: If config file is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        logger.info(f"Loading configuration from {self.config_path}")

        with open(self.config_path) as f:
            raw_config = yaml.safe_load(f)

        # Substitute environment variables
        self.config = self._substitute_env_vars(raw_config)

        return self.config

    async def apply_to_manager(self, manager: Any) -> dict[str, Any]:
        """
        Apply configuration to a CompositionManager.

        Args:
            manager: CompositionManager instance

        Returns:
            Dictionary with statistics about what was loaded
        """
        if not self.config:
            import asyncio

            await asyncio.to_thread(self.load)

        stats = {
            "imported": 0,
            "mounted": 0,
            "modules": 0,
            "skipped": 0,
        }

        # Apply composition.import configuration
        import_configs = self.config.get("composition", {}).get("import", [])
        for server_config in import_configs:
            if not server_config.get("enabled", True):
                stats["skipped"] += 1
                logger.info(f"Skipping disabled server: {server_config.get('name')}")
                continue

            try:
                await self._import_server(manager, server_config)
                stats["imported"] += 1
            except Exception as e:
                logger.error(f"Failed to import server {server_config.get('name')}: {e}")

        # Apply composition.mount configuration
        mount_configs = self.config.get("composition", {}).get("mount", [])
        for server_config in mount_configs:
            if not server_config.get("enabled", True):
                stats["skipped"] += 1
                logger.info(f"Skipping disabled mount: {server_config.get('name')}")
                continue

            try:
                self._mount_server(manager, server_config)
                stats["mounted"] += 1
            except Exception as e:
                logger.error(f"Failed to mount server {server_config.get('name')}: {e}")

        # Apply modules configuration
        modules_config = self.config.get("modules", {})
        if modules_config:
            try:
                # Filter enabled modules
                enabled_modules = {
                    name: config for name, config in modules_config.items() if config.get("enabled", True)
                }

                if enabled_modules:
                    result = manager.load_module(enabled_modules)
                    stats["modules"] = len(result)
            except Exception as e:
                logger.error(f"Failed to load modules: {e}")

        logger.info(f"Configuration applied: {stats}")
        return stats

    async def _import_server(self, manager: Any, config: dict[str, Any]) -> None:
        """
        Import a server based on configuration.

        Args:
            manager: CompositionManager instance
            config: Server configuration dictionary
        """
        server_name = config.get("name", "unknown")
        server_type = config.get("type", "module")
        prefix = config.get("prefix")

        logger.info(f"Importing server '{server_name}' (type={server_type})")

        # Create server configuration for the manager
        server_config = {
            "type": server_type,
            "module": config.get("module"),
            "command": config.get("command"),
            "args": config.get("args", []),
            "env": config.get("env", {}),
            "url": config.get("url"),
            "timeout": config.get("timeout", 30),
            "headers": config.get("headers", {}),
        }

        # Use the manager's import_from_config method (async)
        await manager.import_from_config(server_name, server_config, prefix=prefix)

        logger.info(f"Imported server '{server_name}' with prefix '{prefix}'")

    def _mount_server(self, manager: Any, config: dict[str, Any]) -> None:
        """
        Mount a server based on configuration.

        Args:
            manager: CompositionManager instance
            config: Server configuration dictionary
        """
        server_name = config.get("name", "unknown")
        server_type = config.get("type", "http")
        prefix = config.get("prefix")
        as_proxy = config.get("as_proxy", True)

        logger.info(f"Mounting server '{server_name}' (type={server_type}, as_proxy={as_proxy})")

        # Create server configuration
        server_config = {
            "type": server_type,
            "url": config.get("url"),
            "sse_path": config.get("sse_path"),
            "message_path": config.get("message_path"),
            "timeout": config.get("timeout", 30),
            "headers": config.get("headers", {}),
        }

        # Mount the server
        # Note: This is simplified - you'd create an actual server instance
        manager.mount(server_config, prefix=prefix, as_proxy=as_proxy)

        logger.info(f"Mounted server '{server_name}' with prefix '{prefix}'")

    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in configuration.

        Supports ${VAR_NAME} syntax.

        Args:
            config: Configuration value (dict, list, str, or other)

        Returns:
            Configuration with substituted environment variables
        """
        if isinstance(config, dict):
            return {key: self._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Simple environment variable substitution
            if config.startswith("${") and config.endswith("}"):
                var_name = config[2:-1]
                return os.environ.get(var_name, config)
            return config
        else:
            return config

    def get_server_config(self) -> dict[str, Any]:
        """Get server configuration section."""
        if not self.config:
            self.load()
        return self.config.get("server", {})

    def get_logging_config(self) -> dict[str, Any]:
        """Get logging configuration section."""
        if not self.config:
            self.load()
        return self.config.get("logging", {})

    def get_composition_config(self) -> dict[str, Any]:
        """Get composition configuration section."""
        if not self.config:
            self.load()
        return self.config.get("composition", {})

    def get_modules_config(self) -> dict[str, Any]:
        """Get modules configuration section."""
        if not self.config:
            self.load()
        return self.config.get("modules", {})


async def load_from_config(
    config_path: str | Path | None = None,
    manager: Any | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Convenience function to load configuration and optionally apply to manager.

    Args:
        config_path: Path to config.yaml file
        manager: Optional CompositionManager to apply configuration to

    Returns:
        Tuple of (configuration dict, application statistics)
    """
    loader = CompositionConfigLoader(config_path)
    config = loader.load()

    stats = {}
    if manager:
        stats = await loader.apply_to_manager(manager)

    return config, stats
