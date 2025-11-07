"""Tests for composition manager."""

from unittest.mock import MagicMock, patch


class TestCompositionManager:
    """Test CompositionManager class."""

    def test_initialization(self):
        """Test manager initialization."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        manager = CompositionManager(parent_server)

        assert manager.parent_server == parent_server
        assert manager.imported_servers == {}
        assert manager.mounted_servers == {}
        assert manager.composition_stats == {
            "imported": 0,
            "mounted": 0,
            "modules": 0,
            "proxied": 0,
        }

    def test_import_server_all_components(self):
        """Test importing all components from a server."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        parent_server.protocol.register_tool = MagicMock()
        parent_server.protocol.register_resource = MagicMock()

        # Create mock source server
        source_server = MagicMock()
        source_server.server_info = {"name": "test_server"}
        source_server.protocol.tools = {}
        source_server.protocol.resources = {}
        source_server.protocol.prompts = {}

        manager = CompositionManager(parent_server)
        manager.import_server(source_server)  # No prefix, so will use server_info name

        assert "test_server" in manager.imported_servers
        assert manager.composition_stats["imported"] == 1

    def test_import_server_with_prefix(self):
        """Test importing server with prefix."""
        from chuk_mcp_server.composition.manager import CompositionManager
        from chuk_mcp_server.types import ToolHandler

        parent_server = MagicMock()
        parent_server.protocol.register_tool = MagicMock()

        # Create mock tool handler
        mock_tool_handler = MagicMock()
        mock_tool_handler.handler = MagicMock()
        mock_tool_handler.mcp_tool.description = "Test tool"

        # Create mock source server with tools
        source_server = MagicMock()
        source_server.server_info = {"name": "api"}
        source_server.protocol.tools = {"get_data": mock_tool_handler}
        source_server.protocol.resources = {}
        source_server.protocol.prompts = {}

        manager = CompositionManager(parent_server)

        with patch.object(ToolHandler, "from_function", return_value=mock_tool_handler):
            manager.import_server(source_server, prefix="api", components=["tools"])

        assert "api" in manager.imported_servers
        assert manager.imported_servers["api"]["prefix"] == "api"
        assert parent_server.protocol.register_tool.called

    def test_import_server_filtered_components(self):
        """Test importing only specific components."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        parent_server.protocol.register_tool = MagicMock()

        source_server = MagicMock()
        source_server.server_info = {"name": "api"}
        source_server.protocol.tools = {}
        source_server.protocol.resources = {}
        source_server.protocol.prompts = {}

        manager = CompositionManager(parent_server)
        manager.import_server(source_server, prefix="api", components=["tools"])

        assert "api" in manager.imported_servers
        assert manager.imported_servers["api"]["components"] == ["tools"]

    def test_import_server_with_tags(self):
        """Test importing server with tag filtering."""
        from chuk_mcp_server.composition.manager import CompositionManager
        from chuk_mcp_server.types import ToolHandler

        parent_server = MagicMock()
        parent_server.protocol.register_tool = MagicMock()

        # Create mock tool handlers with tags
        mock_tool1 = MagicMock()
        mock_tool1.handler = MagicMock()
        mock_tool1.mcp_tool.description = "Tool 1"
        mock_tool1.tags = ["api"]

        mock_tool2 = MagicMock()
        mock_tool2.handler = MagicMock()
        mock_tool2.mcp_tool.description = "Tool 2"
        mock_tool2.tags = ["internal"]

        source_server = MagicMock()
        source_server.server_info = {"name": "api"}
        source_server.protocol.tools = {"tool1": mock_tool1, "tool2": mock_tool2}
        source_server.protocol.resources = {}
        source_server.protocol.prompts = {}

        manager = CompositionManager(parent_server)

        with patch.object(ToolHandler, "from_function", return_value=mock_tool1):
            manager.import_server(source_server, prefix="api", components=["tools"], tags=["api"])

        # Only tool1 with "api" tag should be imported
        assert parent_server.protocol.register_tool.call_count == 1

    def test_mount_as_dynamic(self):
        """Test mounting server dynamically."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock()
        source_server.server_info = {"name": "dynamic"}

        manager = CompositionManager(parent_server)
        manager.mount(source_server, prefix="dynamic", as_proxy=False)

        assert "dynamic" in manager.mounted_servers
        assert manager.mounted_servers["dynamic"]["as_proxy"] is False
        assert manager.composition_stats["mounted"] == 1

    def test_mount_as_proxy(self):
        """Test mounting server as proxy."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock()
        source_server.server_info = {"name": "remote"}

        manager = CompositionManager(parent_server)
        manager.mount(source_server, prefix="remote", as_proxy=True)

        assert "remote" in manager.mounted_servers
        assert manager.mounted_servers["remote"]["as_proxy"] is True
        assert manager.composition_stats["mounted"] == 1

    def test_load_module(self):
        """Test loading modules."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        manager = CompositionManager(parent_server)

        module_config = {
            "math": {
                "enabled": True,
                "location": "./modules",
                "module": "math_tools.tools",
                "namespace": "math",
            }
        }

        with patch("chuk_mcp_server.modules.ModuleLoader") as mock_loader:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load_modules.return_value = {"math": ["add", "subtract"]}
            mock_loader.return_value = mock_loader_instance

            result = manager.load_module(module_config)

        assert result == {"math": ["add", "subtract"]}
        assert manager.composition_stats["modules"] == 1

    def test_import_tools(self):
        """Test _import_tools method."""
        from chuk_mcp_server.composition.manager import CompositionManager
        from chuk_mcp_server.types import ToolHandler

        parent_server = MagicMock()
        parent_server.protocol.register_tool = MagicMock()

        mock_tool_handler = MagicMock()
        mock_tool_handler.handler = MagicMock()
        mock_tool_handler.mcp_tool.description = "Test tool"

        source_server = MagicMock()
        source_server.protocol.tools = {"get_data": mock_tool_handler}

        manager = CompositionManager(parent_server)

        with patch.object(ToolHandler, "from_function", return_value=mock_tool_handler):
            count = manager._import_tools(source_server, "api", None)

        assert count == 1
        assert parent_server.protocol.register_tool.called

    def test_import_tools_no_prefix(self):
        """Test _import_tools without prefix."""
        from chuk_mcp_server.composition.manager import CompositionManager
        from chuk_mcp_server.types import ToolHandler

        parent_server = MagicMock()
        parent_server.protocol.register_tool = MagicMock()

        mock_tool_handler = MagicMock()
        mock_tool_handler.handler = MagicMock()
        mock_tool_handler.mcp_tool.description = "Test tool"

        source_server = MagicMock()
        source_server.protocol.tools = {"get_data": mock_tool_handler}

        manager = CompositionManager(parent_server)

        with patch.object(ToolHandler, "from_function", return_value=mock_tool_handler):
            count = manager._import_tools(source_server, None, None)

        assert count == 1

    def test_import_tools_no_protocol(self):
        """Test _import_tools with server without protocol."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock(spec=[])  # No protocol attribute

        manager = CompositionManager(parent_server)
        count = manager._import_tools(source_server, "api", None)

        assert count == 0

    def test_import_resources(self):
        """Test _import_resources method."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        parent_server.protocol.register_resource = MagicMock()

        mock_resource_handler = MagicMock()

        source_server = MagicMock()
        source_server.protocol.resources = {"file://data": mock_resource_handler}

        manager = CompositionManager(parent_server)
        count = manager._import_resources(source_server, None, None)

        assert count == 1
        assert parent_server.protocol.register_resource.called

    def test_import_resources_no_protocol(self):
        """Test _import_resources with server without protocol."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock(spec=[])

        manager = CompositionManager(parent_server)
        count = manager._import_resources(source_server, "api", None)

        assert count == 0

    def test_import_prompts(self):
        """Test _import_prompts method."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()

        mock_prompt_handler = MagicMock()

        source_server = MagicMock()
        source_server.protocol.prompts = {"greeting": mock_prompt_handler}

        manager = CompositionManager(parent_server)
        count = manager._import_prompts(source_server, None, None)

        assert count == 1

    def test_import_prompts_no_protocol(self):
        """Test _import_prompts with server without protocol."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock(spec=[])

        manager = CompositionManager(parent_server)
        count = manager._import_prompts(source_server, "api", None)

        assert count == 0

    def test_matches_tags_with_tags(self):
        """Test _matches_tags method with matching tags."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        manager = CompositionManager(parent_server)

        handler = MagicMock()
        handler.tags = ["api", "public"]

        assert manager._matches_tags(handler, ["api"]) is True
        assert manager._matches_tags(handler, ["public"]) is True
        assert manager._matches_tags(handler, ["internal"]) is False

    def test_matches_tags_no_handler_tags(self):
        """Test _matches_tags with handler without tags."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        manager = CompositionManager(parent_server)

        handler = MagicMock(spec=[])  # No tags attribute

        # Should match all when handler has no tags
        assert manager._matches_tags(handler, ["api"]) is True

    def test_matches_tags_empty_handler_tags(self):
        """Test _matches_tags with empty handler tags."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        manager = CompositionManager(parent_server)

        handler = MagicMock()
        handler.tags = []

        # Should match all when handler tags are empty
        assert manager._matches_tags(handler, ["api"]) is True

    def test_get_composition_stats(self):
        """Test get_composition_stats method."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        manager = CompositionManager(parent_server)

        # Add some data
        manager.imported_servers["api"] = {
            "server": MagicMock(),
            "prefix": "api",
            "components": ["tools"],
            "imported_count": 5,
        }
        manager.mounted_servers["remote"] = {
            "server": MagicMock(),
            "prefix": "remote",
            "as_proxy": True,
        }
        manager.composition_stats["imported"] = 1
        manager.composition_stats["mounted"] = 1

        stats = manager.get_composition_stats()

        assert stats["stats"]["imported"] == 1
        assert stats["stats"]["mounted"] == 1
        assert "api" in stats["imported_servers"]
        assert "remote" in stats["mounted_servers"]
        assert stats["total_components"] == 5

    def test_get_composition_stats_empty(self):
        """Test get_composition_stats with no servers."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        manager = CompositionManager(parent_server)

        stats = manager.get_composition_stats()

        assert stats["stats"]["imported"] == 0
        assert stats["stats"]["mounted"] == 0
        assert stats["imported_servers"] == []
        assert stats["mounted_servers"] == []
        assert stats["total_components"] == 0

    def test_import_server_without_server_info(self):
        """Test importing server without server_info attribute."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock(spec=["protocol"])
        source_server.protocol.tools = {}
        source_server.protocol.resources = {}
        source_server.protocol.prompts = {}

        manager = CompositionManager(parent_server)
        manager.import_server(source_server, prefix="test")

        # Should use prefix as name
        assert "test" in manager.imported_servers

    def test_import_server_no_prefix_no_server_info(self):
        """Test importing server without prefix or server_info."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock(spec=["protocol"])
        source_server.protocol.tools = {}
        source_server.protocol.resources = {}
        source_server.protocol.prompts = {}

        manager = CompositionManager(parent_server)
        manager.import_server(source_server)

        # Should use "unknown" as fallback name
        assert "unknown" in manager.imported_servers

    def test_mount_without_server_info(self):
        """Test mounting server without server_info."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock(spec=[])

        manager = CompositionManager(parent_server)
        manager.mount(source_server, prefix="test")

        assert "test" in manager.mounted_servers

    def test_mount_no_prefix_no_server_info(self):
        """Test mounting server without prefix or server_info."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock(spec=[])

        manager = CompositionManager(parent_server)
        manager.mount(source_server)

        assert "unknown" in manager.mounted_servers

    def test_import_tools_with_tag_filtering(self):
        """Test importing tools with tag filtering."""
        from chuk_mcp_server.composition.manager import CompositionManager
        from chuk_mcp_server.types import ToolHandler

        parent_server = MagicMock()
        parent_server.protocol.register_tool = MagicMock()

        mock_tool1 = MagicMock()
        mock_tool1.handler = MagicMock()
        mock_tool1.mcp_tool.description = "Tool 1"
        mock_tool1.tags = ["api"]

        mock_tool2 = MagicMock()
        mock_tool2.handler = MagicMock()
        mock_tool2.mcp_tool.description = "Tool 2"
        mock_tool2.tags = ["internal"]

        source_server = MagicMock()
        source_server.protocol.tools = {"tool1": mock_tool1, "tool2": mock_tool2}

        manager = CompositionManager(parent_server)

        with patch.object(ToolHandler, "from_function", return_value=mock_tool1):
            count = manager._import_tools(source_server, "api", ["api"])

        # Only tool1 should be imported
        assert count == 1

    def test_import_resources_with_tag_filtering(self):
        """Test importing resources with tag filtering."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        parent_server.protocol.register_resource = MagicMock()

        mock_resource1 = MagicMock()
        mock_resource1.tags = ["public"]

        mock_resource2 = MagicMock()
        mock_resource2.tags = ["private"]

        source_server = MagicMock()
        source_server.protocol.resources = {"res1": mock_resource1, "res2": mock_resource2}

        manager = CompositionManager(parent_server)
        count = manager._import_resources(source_server, None, ["public"])

        # Only res1 should be imported
        assert count == 1

    def test_import_prompts_with_tag_filtering(self):
        """Test importing prompts with tag filtering."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()

        mock_prompt1 = MagicMock()
        mock_prompt1.tags = ["user"]

        mock_prompt2 = MagicMock()
        mock_prompt2.tags = ["system"]

        source_server = MagicMock()
        source_server.protocol.prompts = {"prompt1": mock_prompt1, "prompt2": mock_prompt2}

        manager = CompositionManager(parent_server)
        count = manager._import_prompts(source_server, None, ["user"])

        # Only prompt1 should be imported
        assert count == 1

    def test_mount_dynamic_warning(self):
        """Test that mount_dynamic logs a warning."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock()

        manager = CompositionManager(parent_server)

        with patch("chuk_mcp_server.composition.manager.logger") as mock_logger:
            manager._mount_dynamic(source_server, "test")
            mock_logger.warning.assert_called_once()

    def test_mount_as_proxy_warning(self):
        """Test that mount_as_proxy logs a warning."""
        from chuk_mcp_server.composition.manager import CompositionManager

        parent_server = MagicMock()
        source_server = MagicMock()

        manager = CompositionManager(parent_server)

        with patch("chuk_mcp_server.composition.manager.logger") as mock_logger:
            manager._mount_as_proxy(source_server, "test")
            mock_logger.warning.assert_called_once()
