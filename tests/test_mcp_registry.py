#!/usr/bin/env python3
"""Comprehensive tests for MCP Registry module."""

import time
from unittest.mock import Mock

import pytest
from starlette.requests import Request

from chuk_mcp_server.mcp_registry import (
    MCPComponentConfig,
    MCPComponentRegistry,
    MCPComponentType,
    get_mcp_registry_endpoint,
    get_resource,
    get_tool,
    list_resources,
    list_tools,
    mcp_registry,
    mcp_registry_info_handler,
    register_prompt,
    register_resource,
    register_tool,
    search_components_by_tag,
)
from chuk_mcp_server.types import ResourceHandler, ToolHandler


class TestMCPComponentConfig:
    """Test MCPComponentConfig dataclass."""

    def test_post_init_converts_list_to_set(self):
        """Test that __post_init__ converts list tags to set."""
        config = MCPComponentConfig(
            name="test",
            component_type=MCPComponentType.TOOL,
            component=Mock(),
            metadata={},
            registered_at=time.time(),
            tags=["tag1", "tag2"],  # List instead of set
        )
        assert isinstance(config.tags, set)
        assert config.tags == {"tag1", "tag2"}

    def test_post_init_preserves_set(self):
        """Test that __post_init__ preserves set tags."""
        config = MCPComponentConfig(
            name="test",
            component_type=MCPComponentType.TOOL,
            component=Mock(),
            metadata={},
            registered_at=time.time(),
            tags={"tag1", "tag2"},  # Already a set
        )
        assert isinstance(config.tags, set)
        assert config.tags == {"tag1", "tag2"}


class TestMCPComponentRegistry:
    """Test MCPComponentRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        reg = MCPComponentRegistry()
        yield reg
        reg.clear_all()

    @pytest.fixture
    def sample_tool(self):
        """Create a sample tool handler."""

        def test_func():
            return "result"

        return ToolHandler.from_function(test_func, name="test_tool", description="A test tool")

    @pytest.fixture
    def sample_resource(self):
        """Create a sample resource handler."""

        def test_func():
            return "content"

        return ResourceHandler.from_function(
            uri="test://resource",
            func=test_func,
            name="test_resource",
            description="A test resource",
            mime_type="text/plain",
        )

    def test_register_component_with_tags_none(self, registry, sample_tool):
        """Test registering component with tags=None."""
        registry.register_component(
            MCPComponentType.TOOL,
            "test_tool",
            sample_tool,
            tags=None,  # Explicitly None
        )
        config = registry.components[MCPComponentType.TOOL]["test_tool"]
        assert config.tags == set()

    def test_register_component_name_conflict(self, registry, sample_tool):
        """Test registering component with duplicate name warns and overwrites."""
        # Register first component
        registry.register_component(MCPComponentType.TOOL, "duplicate", sample_tool, tags=["tag1"])

        # Register second component with same name
        def new_func():
            return "new result"

        new_tool = ToolHandler.from_function(new_func, name="duplicate", description="New tool")
        registry.register_component(MCPComponentType.RESOURCE, "duplicate", new_tool, tags=["tag2"])

        # Should have overwritten
        assert "duplicate" in registry._name_index
        config = registry._name_index["duplicate"]
        assert config.component_type == MCPComponentType.RESOURCE
        assert config.tags == {"tag2"}

    def test_register_component_with_tags_and_logging(self, registry, sample_tool):
        """Test registering component with tags triggers debug logging."""
        registry.register_component(
            MCPComponentType.TOOL,
            "tagged_tool",
            sample_tool,
            tags=["important", "experimental"],
        )
        config = registry.components[MCPComponentType.TOOL]["tagged_tool"]
        assert "important" in config.tags
        assert "experimental" in config.tags

    def test_unregister_component_success(self, registry, sample_tool):
        """Test unregistering an existing component."""
        registry.register_tool("to_remove", sample_tool)
        result = registry.unregister_component(MCPComponentType.TOOL, "to_remove")
        assert result is True
        assert "to_remove" not in registry.components[MCPComponentType.TOOL]

    def test_unregister_component_not_found(self, registry):
        """Test unregistering a non-existent component."""
        result = registry.unregister_component(MCPComponentType.TOOL, "nonexistent")
        assert result is False

    def test_unregister_tool(self, registry, sample_tool):
        """Test unregister_tool convenience method."""
        registry.register_tool("tool_to_remove", sample_tool)
        result = registry.unregister_tool("tool_to_remove")
        assert result is True

    def test_unregister_resource(self, registry, sample_resource):
        """Test unregister_resource convenience method."""
        registry.register_resource("resource_to_remove", sample_resource)
        result = registry.unregister_resource("resource_to_remove")
        assert result is True

    def test_unregister_prompt(self, registry):
        """Test unregister_prompt convenience method."""
        prompt = Mock()
        registry.register_prompt("prompt_to_remove", prompt)
        result = registry.unregister_prompt("prompt_to_remove")
        assert result is True

    def test_get_component_not_found(self, registry):
        """Test getting a non-existent component returns None."""
        result = registry.get_component(MCPComponentType.TOOL, "nonexistent")
        assert result is None

    def test_get_tool(self, registry, sample_tool):
        """Test get_tool convenience method."""
        registry.register_tool("my_tool", sample_tool)
        result = registry.get_tool("my_tool")
        assert result == sample_tool

    def test_get_resource(self, registry, sample_resource):
        """Test get_resource convenience method."""
        registry.register_resource("my_resource", sample_resource)
        result = registry.get_resource("my_resource")
        assert result == sample_resource

    def test_get_prompt(self, registry):
        """Test get_prompt convenience method."""
        prompt = Mock()
        registry.register_prompt("my_prompt", prompt)
        result = registry.get_prompt("my_prompt")
        assert result == prompt

    def test_list_components_all_types(self, registry, sample_tool, sample_resource):
        """Test list_components without specifying type returns all."""
        registry.register_tool("tool1", sample_tool)
        registry.register_resource("resource1", sample_resource)

        result = registry.list_components()
        assert "tool" in result
        assert "resource" in result
        assert "prompt" in result
        assert "tool1" in result["tool"]
        assert "resource1" in result["resource"]

    def test_list_components_specific_type(self, registry, sample_tool):
        """Test list_components with specific type."""
        registry.register_tool("tool1", sample_tool)
        result = registry.list_components(MCPComponentType.TOOL)
        assert "tool1" in result
        assert result["tool1"] == sample_tool

    def test_list_tools(self, registry, sample_tool):
        """Test list_tools convenience method."""
        registry.register_tool("tool1", sample_tool)
        result = registry.list_tools()
        assert "tool1" in result

    def test_list_resources(self, registry, sample_resource):
        """Test list_resources convenience method."""
        registry.register_resource("resource1", sample_resource)
        result = registry.list_resources()
        assert "resource1" in result

    def test_list_prompts(self, registry):
        """Test list_prompts convenience method."""
        prompt = Mock()
        registry.register_prompt("prompt1", prompt)
        result = registry.list_prompts()
        assert "prompt1" in result

    def test_search_by_tags_empty_list(self, registry):
        """Test search_by_tags with empty tags list returns empty."""
        result = registry.search_by_tags([])
        assert result == []

    def test_search_by_tags_match_all(self, registry, sample_tool):
        """Test search_by_tags with match_all=True."""
        registry.register_component(MCPComponentType.TOOL, "tool1", sample_tool, tags=["api", "v1"])
        registry.register_component(MCPComponentType.TOOL, "tool2", sample_tool, tags=["api", "v2"])

        # Should only return tool1 which has both tags
        result = registry.search_by_tags(["api", "v1"], match_all=True)
        assert len(result) == 1
        assert result[0].name == "tool1"

    def test_search_by_tags_union(self, registry, sample_tool):
        """Test search_by_tags with match_all=False (union mode)."""
        registry.register_component(MCPComponentType.TOOL, "tool1", sample_tool, tags=["api", "v1"])
        registry.register_component(MCPComponentType.TOOL, "tool2", sample_tool, tags=["database", "v2"])

        # Should return both tools since each has at least one of the tags
        result = registry.search_by_tags(["api", "database"], match_all=False)
        assert len(result) == 2
        names = {r.name for r in result}
        assert names == {"tool1", "tool2"}

    def test_get_component_info_not_found(self, registry):
        """Test get_component_info for non-existent component."""
        result = registry.get_component_info("nonexistent")
        assert result is None

    def test_clear_type(self, registry, sample_tool, sample_resource):
        """Test clear_type removes all components of specific type."""
        registry.register_tool("tool1", sample_tool)
        registry.register_tool("tool2", sample_tool)
        registry.register_resource("resource1", sample_resource)

        registry.clear_type(MCPComponentType.TOOL)

        assert len(registry.components[MCPComponentType.TOOL]) == 0
        assert len(registry.components[MCPComponentType.RESOURCE]) == 1

    def test_clear_all(self, registry, sample_tool, sample_resource):
        """Test clear_all removes all components."""
        registry.register_tool("tool1", sample_tool)
        registry.register_resource("resource1", sample_resource)
        prompt = Mock()
        registry.register_prompt("prompt1", prompt)

        registry.clear_all()

        assert len(registry.components[MCPComponentType.TOOL]) == 0
        assert len(registry.components[MCPComponentType.RESOURCE]) == 0
        assert len(registry.components[MCPComponentType.PROMPT]) == 0
        assert len(registry._tag_index) == 0
        assert len(registry._name_index) == 0


class TestGlobalConvenienceFunctions:
    """Test global convenience functions."""

    def setup_method(self):
        """Clear global registry before each test."""
        mcp_registry.clear_all()

    def teardown_method(self):
        """Clear global registry after each test."""
        mcp_registry.clear_all()

    def test_register_tool_global(self):
        """Test global register_tool function."""

        def global_func():
            return "result"

        tool = ToolHandler.from_function(global_func, name="global_tool", description="A global tool")
        register_tool("global_tool", tool)
        assert "global_tool" in mcp_registry.components[MCPComponentType.TOOL]

    def test_register_resource_global(self):
        """Test global register_resource function."""

        def global_func():
            return "content"

        resource = ResourceHandler.from_function(
            uri="test://global",
            func=global_func,
            name="global_resource",
            description="A global resource",
            mime_type="text/plain",
        )
        register_resource("global_resource", resource)
        assert "global_resource" in mcp_registry.components[MCPComponentType.RESOURCE]

    def test_register_prompt_global(self):
        """Test global register_prompt function."""
        prompt = Mock()
        register_prompt("global_prompt", prompt)
        assert "global_prompt" in mcp_registry.components[MCPComponentType.PROMPT]

    def test_get_tool_global(self):
        """Test global get_tool function."""

        def test_func():
            return "result"

        tool = ToolHandler.from_function(test_func, name="test_tool", description="Test")
        register_tool("test_tool", tool)
        result = get_tool("test_tool")
        assert result == tool

    def test_get_resource_global(self):
        """Test global get_resource function."""

        def test_func():
            return "content"

        resource = ResourceHandler.from_function(
            uri="test://resource", func=test_func, name="test_resource", description="Test", mime_type="text/plain"
        )
        register_resource("test_resource", resource)
        result = get_resource("test_resource")
        assert result == resource

    def test_list_tools_global(self):
        """Test global list_tools function."""

        def test_func():
            return "result"

        tool = ToolHandler.from_function(test_func, name="tool1", description="Test")
        register_tool("tool1", tool)
        result = list_tools()
        assert "tool1" in result

    def test_list_resources_global(self):
        """Test global list_resources function."""

        def test_func():
            return "content"

        resource = ResourceHandler.from_function(
            uri="test://resource", func=test_func, name="resource1", description="Test", mime_type="text/plain"
        )
        register_resource("resource1", resource)
        result = list_resources()
        assert "resource1" in result

    def test_search_components_by_tag_global(self):
        """Test global search_components_by_tag function."""

        def test_func():
            return "result"

        tool = ToolHandler.from_function(test_func, name="tagged_tool", description="Test")
        register_tool("tagged_tool", tool, tags=["searchable"])
        result = search_components_by_tag("searchable")
        assert len(result) > 0
        assert result[0].name == "tagged_tool"


class TestMCPRegistryEndpoint:
    """Test MCP registry endpoint handlers."""

    def setup_method(self):
        """Clear registry before each test."""
        mcp_registry.clear_all()

    def teardown_method(self):
        """Clear registry after each test."""
        mcp_registry.clear_all()

    @pytest.mark.asyncio
    async def test_mcp_registry_info_handler(self):
        """Test mcp_registry_info_handler endpoint."""

        # Register some components
        def test_func():
            return "result"

        tool = ToolHandler.from_function(test_func, name="test_tool", description="Test tool")
        register_tool("test_tool", tool)

        # Create mock request
        request = Mock(spec=Request)

        # Call handler
        response = await mcp_registry_info_handler(request)

        # Verify response
        assert response.status_code == 200
        assert response.media_type == "application/json"
        assert "Access-Control-Allow-Origin" in response.headers

        # Verify content
        import orjson

        content = orjson.loads(response.body)
        assert content["registry_type"] == "MCP Component Registry"
        assert "data" in content
        assert "components" in content["data"]

    def test_get_mcp_registry_endpoint(self):
        """Test get_mcp_registry_endpoint returns proper config."""
        endpoint = get_mcp_registry_endpoint()

        assert endpoint["path"] == "/registry/mcp"
        assert endpoint["handler"] == mcp_registry_info_handler
        assert "GET" in endpoint["methods"]
        assert endpoint["name"] == "mcp_registry_info"
        assert "description" in endpoint


class TestMCPRegistryAdvanced:
    """Advanced test cases for comprehensive coverage."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        reg = MCPComponentRegistry()
        yield reg
        reg.clear_all()

    def test_get_stats(self, registry):
        """Test get_stats method."""

        # Add various components
        def tool_func():
            return "result"

        def resource_func():
            return "content"

        tool = ToolHandler.from_function(tool_func, name="tool1", description="Test")
        resource = ResourceHandler.from_function(
            uri="test://res", func=resource_func, name="res1", description="Test", mime_type="text/plain"
        )

        registry.register_tool("tool1", tool, tags=["api", "v1"])
        registry.register_resource("res1", resource, tags=["api", "storage"])

        stats = registry.get_stats()

        assert stats["total_components"] == 2
        assert stats["by_type"]["tool"] == 1
        assert stats["by_type"]["resource"] == 1
        assert stats["tags"]["total_unique"] >= 3
        assert len(stats["recent_registrations"]) == 2

    def test_get_info(self, registry):
        """Test get_info method returns comprehensive data."""

        def tool_func():
            return "result"

        tool = ToolHandler.from_function(tool_func, name="tool1", description="Test")
        registry.register_tool("tool1", tool, tags=["test"])

        info = registry.get_info()

        assert "components" in info
        assert "stats" in info
        assert "tool" in info["components"]
        assert info["components"]["tool"]["count"] == 1
        assert len(info["components"]["tool"]["registered"]) == 1

    def test_search_by_tag(self, registry):
        """Test search_by_tag finds components correctly."""

        def tool_func():
            return "result"

        tool = ToolHandler.from_function(tool_func, name="tool1", description="Test")
        registry.register_tool("tool1", tool, tags=["searchable", "test"])

        results = registry.search_by_tag("searchable")

        assert len(results) == 1
        assert results[0].name == "tool1"

    def test_get_component_info_found(self, registry):
        """Test get_component_info returns proper structure."""

        def tool_func():
            return "result"

        tool = ToolHandler.from_function(tool_func, name="tool1", description="Test")
        registry.register_tool("tool1", tool, tags=["test"], version="2.0.0")

        info = registry.get_component_info("tool1")

        assert info is not None
        assert info["name"] == "tool1"
        assert info["type"] == "tool"
        assert info["version"] == "2.0.0"
        assert "test" in info["tags"]
        assert "metadata" in info

    def test_register_tool_without_custom_metadata(self, registry):
        """Test register_tool auto-generates metadata."""

        def auto_func():
            return "result"

        tool = ToolHandler.from_function(auto_func, name="auto_tool", description="Auto test")
        registry.register_tool("auto_tool", tool)

        config = registry.components[MCPComponentType.TOOL]["auto_tool"]
        assert "description" in config.metadata
        assert config.metadata["description"] == "Auto test"

    def test_register_resource_without_custom_metadata(self, registry):
        """Test register_resource auto-generates metadata."""

        def auto_func():
            return "{}"

        resource = ResourceHandler.from_function(
            uri="test://auto",
            func=auto_func,
            name="auto_resource",
            description="Auto test",
            mime_type="application/json",
        )
        registry.register_resource("auto_resource", resource)

        config = registry.components[MCPComponentType.RESOURCE]["auto_resource"]
        assert "description" in config.metadata
        assert config.metadata["mime_type"] == "application/json"
