#!/usr/bin/env python3
# src/chuk_mcp_server/component_registry.py
"""
Dual component registry: bridges MCPProtocolHandler and mcp_registry.

Provides unified registration, search, and clear operations that keep
both the protocol handler's internal registries and the discovery registry
in sync.
"""

import logging
from typing import Any

from .mcp_registry import MCPComponentType, mcp_registry
from .types import PromptHandler, ResourceHandler, ToolHandler
from .types.resources import ResourceTemplateHandler

logger = logging.getLogger(__name__)


class ComponentRegistry:
    """Manages dual registration of tools/resources/prompts in both
    the protocol handler and the discovery registry."""

    def __init__(self, protocol: Any) -> None:
        self._protocol = protocol

    # --- Tool registration ---

    def register_tool(self, tool_handler: ToolHandler, **kwargs: Any) -> None:
        """Register tool in both protocol and registry."""
        self._protocol.register_tool(tool_handler)
        mcp_registry.register_tool(tool_handler.name, tool_handler, **kwargs)
        logger.debug(f"Registered tool: {tool_handler.name}")

    # --- Resource registration ---

    def register_resource(self, resource_handler: ResourceHandler, **kwargs: Any) -> None:
        """Register resource in both protocol and registry."""
        self._protocol.register_resource(resource_handler)
        mcp_registry.register_resource(resource_handler.uri, resource_handler, **kwargs)
        logger.debug(f"Registered resource: {resource_handler.uri}")

    # --- Prompt registration ---

    def register_prompt(self, prompt_handler: PromptHandler, **kwargs: Any) -> None:
        """Register prompt in both protocol and registry."""
        self._protocol.register_prompt(prompt_handler)
        mcp_registry.register_prompt(prompt_handler.name, prompt_handler, **kwargs)
        logger.debug(f"Registered prompt: {prompt_handler.name}")

    # --- Template registration ---

    def register_resource_template(self, template_handler: ResourceTemplateHandler) -> None:
        """Register resource template in protocol."""
        self._protocol.register_resource_template(template_handler)

    # --- Search ---

    def search_tools_by_tag(self, tag: str) -> list[ToolHandler]:
        """Search tools by tag."""
        configs = mcp_registry.search_by_tag(tag)
        return [config.component for config in configs if config.component_type.value == "tool"]

    def search_resources_by_tag(self, tag: str) -> list[ResourceHandler]:
        """Search resources by tag."""
        configs = mcp_registry.search_by_tag(tag)
        return [config.component for config in configs if config.component_type.value == "resource"]

    def search_prompts_by_tag(self, tag: str) -> list[PromptHandler]:
        """Search prompts by tag."""
        configs = mcp_registry.search_by_tag(tag)
        return [config.component for config in configs if config.component_type.value == "prompt"]

    def search_components_by_tags(self, tags: list[str], match_all: bool = False) -> Any:
        """Search components by multiple tags."""
        return mcp_registry.search_by_tags(tags, match_all=match_all)

    def get_component_info(self, name: str) -> dict[str, Any] | None:
        """Get detailed information about an MCP component."""
        return mcp_registry.get_component_info(name)

    # --- Clear ---

    def clear_tools(self) -> None:
        """Clear all tools from both registries."""
        self._protocol.tools.clear()
        mcp_registry.clear_type(MCPComponentType.TOOL)

    def clear_resources(self) -> None:
        """Clear all resources from both registries."""
        self._protocol.resources.clear()
        mcp_registry.clear_type(MCPComponentType.RESOURCE)

    def clear_prompts(self) -> None:
        """Clear all prompts from both registries."""
        self._protocol.prompts.clear()
        mcp_registry.clear_type(MCPComponentType.PROMPT)

    def clear_all(self) -> None:
        """Clear all component types."""
        self.clear_tools()
        self.clear_resources()
        self.clear_prompts()
