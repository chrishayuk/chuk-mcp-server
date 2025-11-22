#!/usr/bin/env python3
# src/chuk_mcp_server/modules/loader.py
"""
Module Loader - Dynamic loading of tool modules

This module handles loading and managing multiple tool collections
from external Python modules, enabling multi-tool hosting within
a single ChukMCPServer instance.
"""

import importlib
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Any

from ..types import ToolHandler

logger = logging.getLogger(__name__)


class ModuleLoader:
    """Loads and manages multiple tool modules."""

    def __init__(self, config: dict[str, Any] | None = None, server: Any | None = None):
        """
        Initialize the module loader.

        Args:
            config: Configuration dictionary with tool_modules section
            server: ChukMCPServer instance to register tools with
        """
        self.config = config or {}
        self.server = server
        self.loaded_modules: dict[str, Any] = {}
        self.loaded_tools: dict[str, ToolHandler] = {}
        self.module_paths: dict[str, str] = {}

    def load_modules(self) -> dict[str, list[str]]:
        """
        Load all configured tool modules.

        Returns:
            Dictionary mapping module names to lists of loaded tool names
        """
        tool_modules_config = self.config.get("tool_modules", {})

        if not tool_modules_config:
            logger.debug("No tool_modules configuration found")
            return {}

        results: dict[str, list[str]] = {}

        for module_name, module_config in tool_modules_config.items():
            if not isinstance(module_config, dict):
                logger.warning(f"Invalid configuration for module {module_name}")
                continue

            # Check if module is enabled
            if not module_config.get("enabled", True):
                logger.debug(f"Module {module_name} is disabled")
                continue

            # Load the module
            tools = self._load_module(module_name, module_config)
            if tools:
                results[module_name] = tools

        return results

    def _load_module(self, module_name: str, module_config: dict[str, Any]) -> list[str]:
        """
        Load a single module and its tools.

        Args:
            module_name: Name of the module
            module_config: Configuration for the module

        Returns:
            List of loaded tool names
        """
        try:
            # Get module path and package
            location = module_config.get("location")
            module_path = module_config.get("module")

            if not module_path:
                logger.warning(f"No module path specified for {module_name}")
                return []

            # Add location to sys.path if specified
            if location:
                resolved_location = self._resolve_path(location)
                if resolved_location and resolved_location not in sys.path:
                    sys.path.insert(0, str(resolved_location))
                    self.module_paths[module_name] = str(resolved_location)
                    logger.debug(f"Added {resolved_location} to sys.path")

            # Import the module
            logger.debug(f"Importing module: {module_path}")
            module = importlib.import_module(module_path)
            self.loaded_modules[module_name] = module

            # Scan for tools in the module
            tools = self._scan_module_for_tools(module_name, module, module_config)

            logger.info(f"Loaded module {module_name}: {len(tools)} tools")
            return tools

        except ImportError as e:
            logger.error(f"Failed to import module {module_name} ({module_path}): {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading module {module_name}: {e}", exc_info=True)
            return []

    def _resolve_path(self, location: str) -> Path | None:
        """
        Resolve a path that may be relative or absolute.

        Args:
            location: Path to resolve

        Returns:
            Resolved Path object or None if invalid
        """
        path = Path(location)

        # Handle absolute paths
        if path.is_absolute():
            if path.exists():
                return path
            logger.warning(f"Path does not exist: {location}")
            return None

        # Handle relative paths - try relative to current working directory
        cwd_path = Path.cwd() / path
        if cwd_path.exists():
            return cwd_path

        # Try relative to project root (parent of current directory)
        project_root = Path.cwd()
        while project_root.parent != project_root:
            test_path = project_root / path
            if test_path.exists():
                return test_path
            project_root = project_root.parent

        logger.warning(f"Could not resolve path: {location}")
        return None

    def _scan_module_for_tools(self, module_name: str, module: Any, module_config: dict[str, Any]) -> list[str]:
        """
        Scan a module for tool functions and register them.

        Args:
            module_name: Name of the module
            module: The imported module
            module_config: Configuration for the module

        Returns:
            List of registered tool names
        """
        tools_config = module_config.get("tools", {})
        namespace = module_config.get("namespace", module_name)
        loaded_tools = []

        # Get all members of the module
        for name, obj in inspect.getmembers(module):
            # Check if it's a tool (has _mcp_tool_metadata or _tool_metadata attribute)
            tool_metadata = getattr(obj, "_mcp_tool_metadata", None) or getattr(obj, "_tool_metadata", None)

            if tool_metadata and callable(obj):
                tool_name = tool_metadata.get("name", name)

                # Check if this specific tool is enabled
                tool_config = tools_config.get(tool_name, {})
                if isinstance(tool_config, dict):
                    if not tool_config.get("enabled", True):
                        logger.debug(f"Tool {tool_name} is disabled")
                        continue

                # Create namespaced tool name
                namespaced_name = f"{namespace}.{tool_name}"

                # Register the tool
                if self._register_tool(namespaced_name, obj, tool_metadata):
                    loaded_tools.append(namespaced_name)

        return loaded_tools

    def _register_tool(self, tool_name: str, tool_func: Any, metadata: dict[str, Any]) -> bool:
        """
        Register a tool with the server.

        Args:
            tool_name: Name for the tool (with namespace)
            tool_func: The tool function
            metadata: Tool metadata

        Returns:
            True if registration succeeded
        """
        try:
            # Extract description from metadata or docstring
            description = metadata.get("description")
            if not description and tool_func.__doc__:
                description = tool_func.__doc__.strip().split("\n")[0]

            # Create tool handler using from_function factory method
            tool_handler = ToolHandler.from_function(
                tool_func, name=tool_name, description=description or f"Tool: {tool_name}"
            )

            # Register with server if available
            if self.server:
                # Register in protocol handler (for MCP functionality)
                self.server.protocol.register_tool(tool_handler)

                # Register in MCP registry for introspection
                from ..mcp_registry import mcp_registry

                mcp_registry.register_tool(
                    tool_handler.name, tool_handler, metadata={"source": "module_loader"}, tags=["module", "dynamic"]
                )

            self.loaded_tools[tool_name] = tool_handler
            logger.debug(f"Registered tool: {tool_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register tool {tool_name}: {e}", exc_info=True)
            return False

    def get_loaded_tools(self) -> dict[str, ToolHandler]:
        """Get all loaded tools."""
        return self.loaded_tools.copy()

    def get_loaded_modules(self) -> dict[str, Any]:
        """Get all loaded modules."""
        return self.loaded_modules.copy()

    def get_module_info(self) -> dict[str, Any]:
        """
        Get information about loaded modules.

        Returns:
            Dictionary with module statistics
        """
        return {
            "total_modules": len(self.loaded_modules),
            "total_tools": len(self.loaded_tools),
            "modules": {
                name: {
                    "path": self.module_paths.get(name),
                    "tools": [tool_name for tool_name in self.loaded_tools if tool_name.startswith(f"{name}.")],
                }
                for name in self.loaded_modules
            },
        }
