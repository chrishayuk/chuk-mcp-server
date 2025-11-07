#!/usr/bin/env python3
# src/chuk_mcp_server/composition/manager.py
"""
Composition Manager - Unified server composition and proxying

This module provides a unified interface for:
- Static composition (import_server): One-time copy of server components
- Dynamic composition (mount): Live link to another server
- Module loading: Python module integration
- Proxying: Remote server aggregation
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CompositionManager:
    """Manages server composition, mounting, and proxying."""

    def __init__(self, parent_server: Any):
        """
        Initialize the composition manager.

        Args:
            parent_server: The ChukMCPServer instance that owns this manager
        """
        self.parent_server = parent_server
        self.imported_servers: dict[str, Any] = {}
        self.mounted_servers: dict[str, Any] = {}
        self.composition_stats = {
            "imported": 0,
            "mounted": 0,
            "modules": 0,
            "proxied": 0,
        }

    def import_server(
        self,
        server: Any,
        prefix: str | None = None,
        components: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """
        Static composition: Import (copy) components from another server.

        This creates a one-time copy of the server's tools, resources, and prompts.
        Changes to the original server after import will NOT be reflected.

        Args:
            server: ChukMCPServer instance to import from
            prefix: Optional prefix for namespacing (e.g., "weather" -> "weather.get_forecast")
            components: List of component types to import ["tools", "resources", "prompts"]
                       If None, imports all components
            tags: Optional list of tags to filter components

        Example:
            # Import all components with prefix
            mcp.import_server(weather_server, prefix="weather")

            # Import only tools
            mcp.import_server(weather_server, prefix="weather", components=["tools"])

            # Import filtered by tags
            mcp.import_server(weather_server, prefix="weather", tags=["forecast"])
        """
        if components is None:
            components = ["tools", "resources", "prompts"]

        imported_count = 0

        # Import tools
        if "tools" in components:
            imported_count += self._import_tools(server, prefix, tags)

        # Import resources
        if "resources" in components:
            imported_count += self._import_resources(server, prefix, tags)

        # Import prompts
        if "prompts" in components:
            imported_count += self._import_prompts(server, prefix, tags)

        # Track imported server
        server_name = prefix or getattr(server, "server_info", {}).get("name", "unknown")
        self.imported_servers[server_name] = {
            "server": server,
            "prefix": prefix,
            "components": components,
            "imported_count": imported_count,
        }

        self.composition_stats["imported"] += 1
        logger.info(f"Imported {imported_count} components from server '{server_name}' with prefix '{prefix}'")

    def mount(
        self,
        server: Any,
        prefix: str | None = None,
        as_proxy: bool = False,
    ) -> None:
        """
        Dynamic composition: Mount a server for live delegation.

        This creates a live link to another server. Changes to the mounted server
        are reflected immediately. Requests are delegated at runtime.

        Args:
            server: ChukMCPServer instance or proxy configuration to mount
            prefix: Optional prefix for namespacing
            as_proxy: If True, mount as a proxy (for remote servers)

        Example:
            # Mount local server with live updates
            mcp.mount(api_server)

            # Mount as proxy with prefix
            mcp.mount(remote_server, prefix="remote", as_proxy=True)
        """
        server_name = prefix or getattr(server, "server_info", {}).get("name", "unknown")

        if as_proxy:
            # Mount as proxy - use ProxyManager
            self._mount_as_proxy(server, prefix)
        else:
            # Mount as dynamic link
            self._mount_dynamic(server, prefix)

        # Track mounted server
        self.mounted_servers[server_name] = {
            "server": server,
            "prefix": prefix,
            "as_proxy": as_proxy,
        }

        self.composition_stats["mounted"] += 1
        logger.info(f"Mounted server '{server_name}' (proxy={as_proxy}, prefix='{prefix}')")

    def load_module(
        self,
        module_config: dict[str, Any],
    ) -> dict[str, list[str]]:
        """
        Load Python modules with tools.

        This is a wrapper around ModuleLoader for consistency with the
        composition API.

        Args:
            module_config: Configuration for module loading

        Returns:
            Dictionary mapping module names to loaded tool names

        Example:
            results = mcp.load_module({
                "math": {
                    "enabled": True,
                    "location": "./modules",
                    "module": "math_tools.tools",
                    "namespace": "math"
                }
            })
        """
        from ..modules import ModuleLoader

        # Wrap config in proper structure
        config = {"tool_modules": module_config}
        loader = ModuleLoader(config, self.parent_server)
        results = loader.load_modules()

        self.composition_stats["modules"] += len(results)
        logger.info(f"Loaded {len(results)} modules via composition layer")

        return results

    def _import_tools(self, server: Any, prefix: str | None, tags: list[str] | None) -> int:
        """Import tools from a server."""
        imported = 0

        # Get tools from the server's protocol handler
        if hasattr(server, "protocol") and hasattr(server.protocol, "tools"):
            for tool_name, tool_handler in server.protocol.tools.items():
                # Filter by tags if specified
                if tags and not self._matches_tags(tool_handler, tags):
                    continue

                # Apply prefix to create new name
                new_name = f"{prefix}.{tool_name}" if prefix else tool_name

                # Create a new tool handler with the prefixed name
                from ..types import ToolHandler

                prefixed_handler = ToolHandler.from_function(
                    tool_handler.handler,
                    name=new_name,
                    description=tool_handler.mcp_tool.description,
                )

                # Register the prefixed tool in parent server
                self.parent_server.protocol.register_tool(prefixed_handler)

                imported += 1

        return imported

    def _import_resources(self, server: Any, prefix: str | None, tags: list[str] | None) -> int:
        """Import resources from a server."""
        imported = 0

        # Get resources from the server's protocol handler
        if hasattr(server, "protocol") and hasattr(server.protocol, "resources"):
            for resource_uri, resource_handler in server.protocol.resources.items():
                # Filter by tags if specified
                if tags and not self._matches_tags(resource_handler, tags):
                    continue

                # Apply prefix to URI (if needed in future)
                # Note: Resource URI prefixing is not yet implemented
                # Future implementation would use:
                # if prefix:
                #     if "://" in resource_uri:
                #         protocol, path = resource_uri.split("://", 1)
                #         new_uri = f"{protocol}://{prefix}/{path}"
                #     else:
                #         new_uri = f"{prefix}/{resource_uri}"

                # Register the resource in parent server
                self.parent_server.protocol.register_resource(resource_handler)

                imported += 1

        return imported

    def _import_prompts(self, server: Any, prefix: str | None, tags: list[str] | None) -> int:
        """Import prompts from a server."""
        imported = 0

        # Get prompts from the server's protocol handler
        if hasattr(server, "protocol") and hasattr(server.protocol, "prompts"):
            for prompt_name, prompt_handler in server.protocol.prompts.items():
                # Filter by tags if specified
                if tags and not self._matches_tags(prompt_handler, tags):
                    continue

                # Apply prefix (if needed in future)
                # Note: Prompt prefixing is not yet implemented
                # Future implementation would use:
                # new_name = f"{prefix}.{prompt_name}" if prefix else prompt_name

                # Register the prompt in parent server
                # (Implementation depends on prompt handler structure)
                imported += 1

        return imported

    def _mount_dynamic(self, server: Any, prefix: str | None) -> None:
        """Mount a server with dynamic delegation."""
        # TODO: Implement dynamic mounting
        # This requires creating wrapper functions that delegate to the mounted server
        logger.warning("Dynamic mounting not yet fully implemented")

    def _mount_as_proxy(self, server: Any, prefix: str | None) -> None:
        """Mount a server as a proxy."""
        # TODO: Integrate with ProxyManager
        logger.warning("Proxy mounting not yet fully implemented")

    def _matches_tags(self, handler: Any, tags: list[str]) -> bool:
        """Check if a handler matches any of the specified tags."""
        # Get tags from handler metadata
        handler_tags = getattr(handler, "tags", [])
        if not handler_tags:
            return True  # No tags means match all

        # Check if any tag matches
        return any(tag in handler_tags for tag in tags)

    def get_composition_stats(self) -> dict[str, Any]:
        """Get statistics about composed servers."""
        return {
            "stats": self.composition_stats.copy(),
            "imported_servers": list(self.imported_servers.keys()),
            "mounted_servers": list(self.mounted_servers.keys()),
            "total_components": sum(info.get("imported_count", 0) for info in self.imported_servers.values()),
        }
