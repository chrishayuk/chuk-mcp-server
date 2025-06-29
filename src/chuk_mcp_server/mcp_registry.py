#!/usr/bin/env python3
"""
MCP Registry - Registry for MCP protocol components (tools, resources, prompts)
"""

import logging
import time
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass
from enum import Enum

from starlette.requests import Request
from starlette.responses import Response

from .types import Tool, Resource

logger = logging.getLogger(__name__)


# ============================================================================
# MCP Component Types and Data Structures
# ============================================================================

class MCPComponentType(Enum):
    """Types of MCP components that can be registered."""
    TOOL = "tool"
    RESOURCE = "resource"
    PROMPT = "prompt"


@dataclass
class MCPComponentConfig:
    """Configuration for a registered MCP component."""
    name: str
    component_type: MCPComponentType
    component: Any
    metadata: Dict[str, Any]
    registered_at: float
    tags: Set[str]
    version: str = "1.0.0"
    
    def __post_init__(self):
        if isinstance(self.tags, list):
            self.tags = set(self.tags)


# ============================================================================
# MCP Component Registry
# ============================================================================

class MCPComponentRegistry:
    """Registry for MCP protocol components like tools, resources, and prompts."""
    
    def __init__(self):
        self.components: Dict[MCPComponentType, Dict[str, MCPComponentConfig]] = {
            MCPComponentType.TOOL: {},
            MCPComponentType.RESOURCE: {},
            MCPComponentType.PROMPT: {}
        }
        
        # Indexes for fast lookups
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> set of component names
        self._name_index: Dict[str, MCPComponentConfig] = {}  # name -> config (across all types)
        
        logger.debug("MCP component registry initialized")
    
    def register_component(
        self,
        component_type: MCPComponentType,
        name: str,
        component: Any,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None,
        version: str = "1.0.0"
    ):
        """
        Register an MCP component.
        
        Args:
            component_type: Type of component (TOOL, RESOURCE, PROMPT)
            name: Unique name for the component
            component: The actual component object
            metadata: Additional metadata about the component
            tags: Tags for categorization and search
            version: Component version
        """
        if metadata is None:
            metadata = {}
        
        if tags is None:
            tags = []
        
        # Check for name conflicts across all component types
        if name in self._name_index:
            existing_config = self._name_index[name]
            logger.warning(
                f"⚠️ Component name conflict: '{name}' already registered as "
                f"{existing_config.component_type.value}. Overwriting."
            )
            self._remove_from_indexes(existing_config)
        
        config = MCPComponentConfig(
            name=name,
            component_type=component_type,
            component=component,
            metadata=metadata,
            registered_at=time.time(),
            tags=set(tags),
            version=version
        )
        
        # Store in main registry
        self.components[component_type][name] = config
        
        # Update indexes
        self._update_indexes(config)
        
        logger.info(f"🔧 Registered {component_type.value}: {name} (v{version})")
        if tags:
            logger.debug(f"   Tags: {', '.join(tags)}")
    
    def register_tool(self, name: str, tool: Tool, **kwargs):
        """Convenience method to register a tool."""
        # Extract metadata from tool if not provided
        if 'metadata' not in kwargs:
            kwargs['metadata'] = {
                'description': tool.description,
                'parameter_count': len(tool.parameters),
                'schema': tool.to_mcp_format()
            }
        
        if 'tags' not in kwargs:
            kwargs['tags'] = ['tool']
        
        self.register_component(MCPComponentType.TOOL, name, tool, **kwargs)
    
    def register_resource(self, name: str, resource: Resource, **kwargs):
        """Convenience method to register a resource."""
        # Extract metadata from resource if not provided
        if 'metadata' not in kwargs:
            kwargs['metadata'] = {
                'description': resource.description,
                'mime_type': resource.mime_type,
                'uri': resource.uri,
                'schema': resource.to_mcp_format()
            }
        
        if 'tags' not in kwargs:
            kwargs['tags'] = ['resource']
        
        self.register_component(MCPComponentType.RESOURCE, name, resource, **kwargs)
    
    def register_prompt(self, name: str, prompt: Any, **kwargs):
        """Convenience method to register a prompt."""
        if 'tags' not in kwargs:
            kwargs['tags'] = ['prompt']
        
        self.register_component(MCPComponentType.PROMPT, name, prompt, **kwargs)
    
    def unregister_component(self, component_type: MCPComponentType, name: str):
        """Unregister an MCP component."""
        if name in self.components[component_type]:
            config = self.components[component_type].pop(name)
            self._remove_from_indexes(config)
            logger.info(f"🗑️ Unregistered {component_type.value}: {name}")
            return True
        else:
            logger.warning(f"⚠️ Attempted to unregister non-existent {component_type.value}: {name}")
            return False
    
    def unregister_tool(self, name: str):
        """Convenience method to unregister a tool."""
        return self.unregister_component(MCPComponentType.TOOL, name)
    
    def unregister_resource(self, name: str):
        """Convenience method to unregister a resource."""
        return self.unregister_component(MCPComponentType.RESOURCE, name)
    
    def unregister_prompt(self, name: str):
        """Convenience method to unregister a prompt."""
        return self.unregister_component(MCPComponentType.PROMPT, name)
    
    def get_component(self, component_type: MCPComponentType, name: str) -> Any:
        """Get a component by type and name."""
        config = self.components.get(component_type, {}).get(name)
        return config.component if config else None
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.get_component(MCPComponentType.TOOL, name)
    
    def get_resource(self, name: str) -> Optional[Resource]:
        """Get a resource by name."""
        return self.get_component(MCPComponentType.RESOURCE, name)
    
    def get_prompt(self, name: str) -> Any:
        """Get a prompt by name."""
        return self.get_component(MCPComponentType.PROMPT, name)
    
    def list_components(self, component_type: Optional[MCPComponentType] = None) -> Dict[str, Any]:
        """List components by type or all components."""
        if component_type:
            return {
                name: config.component 
                for name, config in self.components[component_type].items()
            }
        
        result = {}
        for comp_type, components in self.components.items():
            result[comp_type.value] = {
                name: config.component 
                for name, config in components.items()
            }
        return result
    
    def list_tools(self) -> Dict[str, Tool]:
        """List all registered tools."""
        return self.list_components(MCPComponentType.TOOL)
    
    def list_resources(self) -> Dict[str, Resource]:
        """List all registered resources."""
        return self.list_components(MCPComponentType.RESOURCE)
    
    def list_prompts(self) -> Dict[str, Any]:
        """List all registered prompts."""
        return self.list_components(MCPComponentType.PROMPT)
    
    def search_by_tag(self, tag: str) -> List[MCPComponentConfig]:
        """Search components by tag."""
        component_names = self._tag_index.get(tag, set())
        return [self._name_index[name] for name in component_names if name in self._name_index]
    
    def search_by_tags(self, tags: List[str], match_all: bool = False) -> List[MCPComponentConfig]:
        """Search components by multiple tags."""
        if not tags:
            return []
        
        if match_all:
            # Intersection: components that have ALL tags
            matching_names = self._tag_index.get(tags[0], set()).copy()
            for tag in tags[1:]:
                matching_names &= self._tag_index.get(tag, set())
        else:
            # Union: components that have ANY of the tags
            matching_names = set()
            for tag in tags:
                matching_names |= self._tag_index.get(tag, set())
        
        return [self._name_index[name] for name in matching_names if name in self._name_index]
    
    def get_component_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a component."""
        if name not in self._name_index:
            return None
        
        config = self._name_index[name]
        return {
            "name": config.name,
            "type": config.component_type.value,
            "version": config.version,
            "registered_at": config.registered_at,
            "tags": list(config.tags),
            "metadata": config.metadata
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_components = sum(len(components) for components in self.components.values())
        
        return {
            "total_components": total_components,
            "by_type": {
                comp_type.value: len(components)
                for comp_type, components in self.components.items()
            },
            "tags": {
                "total_unique": len(self._tag_index),
                "most_used": self._get_most_used_tags(5)
            },
            "recent_registrations": self._get_recent_registrations(5)
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive registry information."""
        return {
            "components": {
                comp_type.value: {
                    "count": len(components),
                    "registered": [
                        {
                            "name": config.name,
                            "version": config.version,
                            "registered_at": config.registered_at,
                            "tags": list(config.tags),
                            "metadata_keys": list(config.metadata.keys())
                        }
                        for config in components.values()
                    ]
                }
                for comp_type, components in self.components.items()
            },
            "stats": self.get_stats()
        }
    
    def clear_type(self, component_type: MCPComponentType):
        """Clear all components of a specific type."""
        count = len(self.components[component_type])
        
        # Remove from indexes
        for config in self.components[component_type].values():
            self._remove_from_indexes(config)
        
        # Clear the type
        self.components[component_type].clear()
        
        logger.info(f"🗑️ Cleared {count} {component_type.value}s from registry")
    
    def clear_all(self):
        """Clear all registered components."""
        total_count = sum(len(components) for components in self.components.values())
        
        for comp_type in MCPComponentType:
            self.components[comp_type].clear()
        
        self._tag_index.clear()
        self._name_index.clear()
        
        logger.info(f"🗑️ Cleared all {total_count} components from registry")
    
    def _update_indexes(self, config: MCPComponentConfig):
        """Update internal indexes when adding a component."""
        # Update name index
        self._name_index[config.name] = config
        
        # Update tag index
        for tag in config.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(config.name)
    
    def _remove_from_indexes(self, config: MCPComponentConfig):
        """Remove component from internal indexes."""
        # Remove from name index
        if config.name in self._name_index:
            del self._name_index[config.name]
        
        # Remove from tag index
        for tag in config.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(config.name)
                # Clean up empty tag entries
                if not self._tag_index[tag]:
                    del self._tag_index[tag]
    
    def _get_most_used_tags(self, limit: int) -> List[Dict[str, Any]]:
        """Get the most frequently used tags."""
        tag_counts = [(tag, len(names)) for tag, names in self._tag_index.items()]
        tag_counts.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {"tag": tag, "count": count}
            for tag, count in tag_counts[:limit]
        ]
    
    def _get_recent_registrations(self, limit: int) -> List[Dict[str, Any]]:
        """Get recently registered components."""
        all_configs = list(self._name_index.values())
        all_configs.sort(key=lambda x: x.registered_at, reverse=True)
        
        return [
            {
                "name": config.name,
                "type": config.component_type.value,
                "registered_at": config.registered_at
            }
            for config in all_configs[:limit]
        ]


# ============================================================================
# Global Registry Instance
# ============================================================================

# Global instance for use throughout the application
mcp_registry = MCPComponentRegistry()


# ============================================================================
# Convenience Functions
# ============================================================================

def register_tool(name: str, tool: Tool, **kwargs):
    """Convenience function to register a tool."""
    return mcp_registry.register_tool(name, tool, **kwargs)


def register_resource(name: str, resource: Resource, **kwargs):
    """Convenience function to register a resource."""
    return mcp_registry.register_resource(name, resource, **kwargs)


def register_prompt(name: str, prompt: Any, **kwargs):
    """Convenience function to register a prompt."""
    return mcp_registry.register_prompt(name, prompt, **kwargs)


def get_tool(name: str) -> Optional[Tool]:
    """Convenience function to get a tool."""
    return mcp_registry.get_tool(name)


def get_resource(name: str) -> Optional[Resource]:
    """Convenience function to get a resource."""
    return mcp_registry.get_resource(name)


def list_tools() -> Dict[str, Tool]:
    """Convenience function to list all tools."""
    return mcp_registry.list_tools()


def list_resources() -> Dict[str, Resource]:
    """Convenience function to list all resources."""
    return mcp_registry.list_resources()


def search_components_by_tag(tag: str):
    """Convenience function to search components by tag."""
    return mcp_registry.search_by_tag(tag)


# ============================================================================
# MCP Registry Information Endpoint
# ============================================================================

async def mcp_registry_info_handler(request: Request) -> Response:
    """Handler for MCP registry information."""
    import orjson
    
    info = {
        "registry_type": "MCP Component Registry",
        "description": "Manages MCP protocol components (tools, resources, prompts)",
        "data": mcp_registry.get_info()
    }
    
    return Response(
        orjson.dumps(info, option=orjson.OPT_INDENT_2),
        media_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )


# Auto-register the registry info endpoint (this will be imported by endpoint_registry)
def get_mcp_registry_endpoint():
    """Get the MCP registry info endpoint for registration."""
    return {
        "path": "/registry/mcp",
        "handler": mcp_registry_info_handler,
        "methods": ["GET"],
        "name": "mcp_registry_info",
        "description": "Information about registered MCP components (tools, resources, prompts)"
    }