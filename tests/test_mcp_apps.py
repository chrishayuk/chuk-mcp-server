#!/usr/bin/env python3
"""Tests for MCP Apps support (_meta, structuredContent, ext-apps constants, ui/* handling)."""

import orjson
import pytest

from chuk_mcp_server.constants import (
    MCP_APPS_DISPLAY_FULLSCREEN,
    MCP_APPS_DISPLAY_INLINE,
    MCP_APPS_DISPLAY_PIP,
    MCP_APPS_METHOD_UI_CONTEXT_CHANGED,
    MCP_APPS_METHOD_UI_GET_CONTEXT,
    MCP_APPS_METHOD_UI_INITIALIZE,
    MCP_APPS_METHOD_UI_OPEN_LINK,
    MCP_APPS_METHOD_UI_REQUEST_DISPLAY_MODE,
    MCP_APPS_METHOD_UI_SEND_MESSAGE,
    MCP_APPS_METHOD_UI_SIZE_CHANGED,
    MCP_APPS_METHOD_UI_TEARDOWN,
    MCP_APPS_METHOD_UI_TOOL_CANCELLED,
    MCP_APPS_METHOD_UI_TOOL_INPUT,
    MCP_APPS_METHOD_UI_TOOL_INPUT_PARTIAL,
    MCP_APPS_METHOD_UI_TOOL_RESULT,
    MCP_APPS_METHOD_UI_UPDATE_CONTEXT,
    MCP_APPS_UI_KEY,
    MCP_APPS_UI_PERMISSIONS,
    JsonRpcError,
)
from chuk_mcp_server.types.tools import ToolHandler


class TestMetaFieldOnToolHandler:
    """Test the meta field on ToolHandler for MCP Apps."""

    def test_meta_in_mcp_format(self):
        """_meta should appear in MCP format when meta is set."""

        def view_tool() -> dict:
            return {"type": "chart"}

        meta = {"ui": {"resourceUri": "https://cdn.example.com/chart.html"}}
        handler = ToolHandler.from_function(view_tool, meta=meta)
        fmt = handler.to_mcp_format()
        assert "_meta" in fmt
        assert fmt["_meta"]["ui"] == meta["ui"]

    def test_meta_includes_legacy_flat_key(self):
        """_meta should include ui/resourceUri flat key when nested ui.resourceUri is set."""

        def view_tool() -> dict:
            return {"type": "chart"}

        meta = {"ui": {"resourceUri": "ui://test/chart", "viewUrl": "https://example.com/chart/v1"}}
        handler = ToolHandler.from_function(view_tool, meta=meta)
        fmt = handler.to_mcp_format()
        assert fmt["_meta"]["ui/resourceUri"] == "ui://test/chart"
        assert fmt["_meta"]["ui"]["resourceUri"] == "ui://test/chart"

    def test_no_meta_by_default(self):
        """Tools without meta should not include _meta."""

        def simple(x: int) -> int:
            return x

        handler = ToolHandler.from_function(simple)
        fmt = handler.to_mcp_format()
        assert "_meta" not in fmt

    def test_meta_in_bytes(self):
        """_meta should be in orjson bytes."""
        meta = {"ui": {"resourceUri": "https://cdn.example.com/map.html"}}

        def map_view() -> dict:
            return {"layers": []}

        handler = ToolHandler.from_function(map_view, meta=meta)
        data = orjson.loads(handler.to_mcp_bytes())
        assert data["_meta"]["ui"] == meta["ui"]

    def test_meta_is_copied_not_referenced(self):
        """_meta in MCP format should be a copy, not a reference."""
        meta = {"ui": {"resourceUri": "https://cdn.example.com/view.html"}}

        def view() -> dict:
            return {}

        handler = ToolHandler.from_function(view, meta=meta)
        fmt = handler.to_mcp_format()
        fmt["_meta"]["ui"]["resourceUri"] = "mutated"

        # Original should be unchanged
        fmt2 = handler.to_mcp_format()
        assert fmt2["_meta"]["ui"]["resourceUri"] == "https://cdn.example.com/view.html"

    def test_meta_with_annotations(self):
        """_meta and annotations can coexist."""

        def view_tool() -> dict:
            return {}

        meta = {"ui": {"resourceUri": "https://cdn.example.com/view.html"}}
        handler = ToolHandler.from_function(
            view_tool,
            meta=meta,
            read_only_hint=True,
        )
        fmt = handler.to_mcp_format()
        assert "_meta" in fmt
        assert "annotations" in fmt
        assert fmt["annotations"]["readOnlyHint"] is True

    def test_meta_with_output_schema(self):
        """_meta and outputSchema can coexist."""

        def view_tool() -> dict:
            return {"count": 1}

        meta = {"ui": {"resourceUri": "https://cdn.example.com/counter.html"}}
        schema = {"type": "object", "properties": {"count": {"type": "integer"}}}
        handler = ToolHandler.from_function(view_tool, meta=meta, output_schema=schema)
        fmt = handler.to_mcp_format()
        assert "_meta" in fmt
        assert "outputSchema" in fmt

    def test_meta_with_icons(self):
        """_meta and icons can coexist."""

        def view_tool() -> dict:
            return {}

        meta = {"ui": {"resourceUri": "https://cdn.example.com/view.html"}}
        icons = [{"uri": "https://example.com/icon.png", "mediaType": "image/png"}]
        handler = ToolHandler.from_function(view_tool, meta=meta, icons=icons)
        fmt = handler.to_mcp_format()
        assert "_meta" in fmt
        assert "icons" in fmt

    def test_meta_cache_invalidation(self):
        """Invalidating cache should clear and rebuild _meta."""

        def view_tool() -> dict:
            return {}

        meta = {"ui": {"resourceUri": "https://cdn.example.com/view.html"}}
        handler = ToolHandler.from_function(view_tool, meta=meta)

        # Verify it's cached
        assert handler._cached_mcp_format is not None
        assert handler._cached_mcp_bytes is not None

        # Invalidate
        handler.invalidate_cache()
        assert handler._cached_mcp_format is None
        assert handler._cached_mcp_bytes is None

        # Rebuild should still include _meta
        fmt = handler.to_mcp_format()
        assert fmt["_meta"]["ui"] == meta["ui"]


class TestMetaInToolsListViaProtocol:
    """Test that _meta appears in tools/list responses through the protocol."""

    @pytest.fixture
    def server(self):
        from chuk_mcp_server.core import ChukMCPServer

        return ChukMCPServer(name="test-meta", version="0.1.0")

    async def test_meta_in_tools_list(self, server):
        """_meta should appear in tools/list response when set via decorator."""
        meta = {"ui": {"resourceUri": "https://cdn.example.com/view.html"}}

        @server.tool(name="view_data", meta=meta, read_only_hint=True)
        def view_data() -> dict:
            return {"data": [1, 2, 3]}

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        tools = await runner.list_tools()

        tool_info = next(t for t in tools if t["name"] == "view_data")
        assert "_meta" in tool_info
        assert tool_info["_meta"]["ui"]["resourceUri"] == "https://cdn.example.com/view.html"


class TestPreFormattedResultPassthrough:
    """Test that pre-formatted MCP results (from view tools) pass through unchanged."""

    @pytest.fixture
    def server(self):
        from chuk_mcp_server.core import ChukMCPServer

        return ChukMCPServer(name="test-passthrough", version="0.1.0")

    async def test_structured_content_passthrough(self, server):
        """Pre-formatted results with structuredContent should pass through."""
        meta = {"ui": {"resourceUri": "https://cdn.example.com/chart.html"}}

        @server.tool(name="chart_view", meta=meta)
        def chart_view() -> dict:
            return {
                "content": [{"type": "text", "text": "Chart: Revenue by Quarter"}],
                "structuredContent": {
                    "type": "chart",
                    "chartType": "bar",
                    "data": [{"label": "Q1", "value": 100}],
                },
            }

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        response = await runner.call_tool("chart_view")
        result = response["result"]

        assert "structuredContent" in result
        assert result["structuredContent"]["type"] == "chart"
        assert result["content"][0]["text"] == "Chart: Revenue by Quarter"

    async def test_meta_passthrough(self, server):
        """Pre-formatted results with _meta should pass through."""
        meta = {"ui": {"resourceUri": "https://cdn.example.com/view.html"}}

        @server.tool(name="meta_view", meta=meta)
        def meta_view() -> dict:
            return {
                "content": [{"type": "text", "text": "View data"}],
                "_meta": {"ui": {"state": "loaded"}},
            }

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        response = await runner.call_tool("meta_view")
        result = response["result"]

        assert "_meta" in result
        assert result["_meta"]["ui"]["state"] == "loaded"

    async def test_normal_dict_still_formatted(self, server):
        """Normal dict results (without structuredContent) should still use format_content."""

        @server.tool(name="normal_tool")
        def normal_tool() -> dict:
            return {"key": "value", "count": 42}

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        response = await runner.call_tool("normal_tool")
        result = response["result"]

        # Normal result should have content but NOT structuredContent (no output_schema)
        assert "content" in result
        assert isinstance(result["content"], list)


# ============================================================================
# Ext-apps constants (Phase 7.5c/d/e)
# ============================================================================


class TestExtAppsConstants:
    """Verify all ext-apps constants are importable and have correct values."""

    def test_method_ui_initialize(self):
        assert MCP_APPS_METHOD_UI_INITIALIZE == "ui/initialize"

    def test_method_ui_get_context(self):
        assert MCP_APPS_METHOD_UI_GET_CONTEXT == "ui/getContext"

    def test_method_ui_size_changed(self):
        assert MCP_APPS_METHOD_UI_SIZE_CHANGED == "ui/notifications/size-changed"

    def test_method_ui_tool_result(self):
        assert MCP_APPS_METHOD_UI_TOOL_RESULT == "ui/notifications/tool-result"

    def test_method_ui_tool_input(self):
        assert MCP_APPS_METHOD_UI_TOOL_INPUT == "ui/notifications/tool-input"

    def test_method_ui_tool_input_partial(self):
        assert MCP_APPS_METHOD_UI_TOOL_INPUT_PARTIAL == "ui/notifications/tool-input-partial"

    def test_method_ui_context_changed(self):
        assert MCP_APPS_METHOD_UI_CONTEXT_CHANGED == "ui/notifications/host-context-changed"

    def test_method_ui_update_context(self):
        assert MCP_APPS_METHOD_UI_UPDATE_CONTEXT == "ui/update-model-context"

    def test_method_ui_send_message(self):
        assert MCP_APPS_METHOD_UI_SEND_MESSAGE == "ui/message"

    def test_method_ui_request_display_mode(self):
        assert MCP_APPS_METHOD_UI_REQUEST_DISPLAY_MODE == "ui/request-display-mode"

    def test_method_ui_open_link(self):
        assert MCP_APPS_METHOD_UI_OPEN_LINK == "ui/open-link"

    def test_method_ui_teardown(self):
        assert MCP_APPS_METHOD_UI_TEARDOWN == "ui/resource-teardown"

    def test_method_ui_tool_cancelled(self):
        assert MCP_APPS_METHOD_UI_TOOL_CANCELLED == "ui/notifications/tool-cancelled"

    def test_display_modes(self):
        assert MCP_APPS_DISPLAY_INLINE == "inline"
        assert MCP_APPS_DISPLAY_FULLSCREEN == "fullscreen"
        assert MCP_APPS_DISPLAY_PIP == "pip"

    def test_permissions_constant(self):
        assert MCP_APPS_UI_PERMISSIONS == "permissions"

    def test_all_methods_start_with_ui_slash(self):
        """Every ext-apps method constant should start with 'ui/'."""
        methods = [
            MCP_APPS_METHOD_UI_INITIALIZE,
            MCP_APPS_METHOD_UI_GET_CONTEXT,
            MCP_APPS_METHOD_UI_SIZE_CHANGED,
            MCP_APPS_METHOD_UI_TOOL_RESULT,
            MCP_APPS_METHOD_UI_TOOL_INPUT,
            MCP_APPS_METHOD_UI_TOOL_INPUT_PARTIAL,
            MCP_APPS_METHOD_UI_CONTEXT_CHANGED,
            MCP_APPS_METHOD_UI_UPDATE_CONTEXT,
            MCP_APPS_METHOD_UI_SEND_MESSAGE,
            MCP_APPS_METHOD_UI_REQUEST_DISPLAY_MODE,
            MCP_APPS_METHOD_UI_OPEN_LINK,
            MCP_APPS_METHOD_UI_TEARDOWN,
            MCP_APPS_METHOD_UI_TOOL_CANCELLED,
        ]
        for method in methods:
            assert method.startswith("ui/"), f"{method} does not start with 'ui/'"


# ============================================================================
# Defensive ui/* method handling in protocol handler
# ============================================================================


class TestDefensiveUiMethodHandling:
    """Test that ui/* methods are handled defensively by the protocol handler."""

    @pytest.fixture
    def handler(self):
        from chuk_mcp_server.protocol.handler import MCPProtocolHandler
        from chuk_mcp_server.types import ServerInfo, create_server_capabilities

        server_info = ServerInfo(name="test-ui-defensive", version="0.1.0")
        capabilities = create_server_capabilities(tools=True, resources=True)
        return MCPProtocolHandler(server_info, capabilities)

    async def test_ui_notification_returns_none(self, handler):
        """A ui/* notification (no id) should return (None, None)."""
        message = {"jsonrpc": "2.0", "method": "ui/notifications/size-changed", "params": {"height": 500}}
        response, session_id = await handler.handle_request(message)
        assert response is None
        assert session_id is None

    async def test_ui_request_returns_method_not_found(self, handler):
        """A ui/* request (with id) should return METHOD_NOT_FOUND."""
        message = {"jsonrpc": "2.0", "id": 42, "method": "ui/initialize", "params": {}}
        response, session_id = await handler.handle_request(message)
        assert response is not None
        assert response["error"]["code"] == JsonRpcError.METHOD_NOT_FOUND
        assert "ext-apps" in response["error"]["message"]

    async def test_ui_initialize_not_confused_with_mcp_initialize(self, handler):
        """'ui/initialize' must NOT be confused with MCP 'initialize'."""
        # MCP initialize should create a session
        mcp_init = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"clientInfo": {"name": "test"}, "protocolVersion": "2025-06-18"},
        }
        mcp_resp, mcp_session = await handler.handle_request(mcp_init)
        assert mcp_resp is not None
        assert "result" in mcp_resp
        assert mcp_session is not None  # Session created

        # ui/initialize should NOT create a session
        ui_init = {"jsonrpc": "2.0", "id": 2, "method": "ui/initialize", "params": {}}
        ui_resp, ui_session = await handler.handle_request(ui_init)
        assert ui_resp is not None
        assert "error" in ui_resp
        assert ui_session is None  # No session created

    async def test_ui_get_context_request(self, handler):
        """ui/getContext with id should return METHOD_NOT_FOUND."""
        message = {"jsonrpc": "2.0", "id": 99, "method": "ui/getContext", "params": {}}
        response, _ = await handler.handle_request(message)
        assert response["error"]["code"] == JsonRpcError.METHOD_NOT_FOUND
        assert "ext-apps" in response["error"]["message"]

    async def test_ui_tool_result_notification(self, handler):
        """ui/notifications/tool-result without id should return (None, None)."""
        message = {
            "jsonrpc": "2.0",
            "method": "ui/notifications/tool-result",
            "params": {"result": {"structuredContent": {}}},
        }
        response, session_id = await handler.handle_request(message)
        assert response is None
        assert session_id is None

    async def test_unknown_ui_method_request(self, handler):
        """Unknown ui/* method with id should return METHOD_NOT_FOUND with ext-apps message."""
        message = {"jsonrpc": "2.0", "id": 77, "method": "ui/some-future-method", "params": {}}
        response, _ = await handler.handle_request(message)
        assert response["error"]["code"] == JsonRpcError.METHOD_NOT_FOUND
        assert "ext-apps" in response["error"]["message"]

    async def test_non_ui_unknown_method(self, handler):
        """Non-ui/* unknown method should return generic METHOD_NOT_FOUND."""
        message = {"jsonrpc": "2.0", "id": 88, "method": "some/unknown/method", "params": {}}
        response, _ = await handler.handle_request(message)
        assert response["error"]["code"] == JsonRpcError.METHOD_NOT_FOUND
        assert "Method not found" in response["error"]["message"]
        assert "ext-apps" not in response["error"]["message"]


# ============================================================================
# Permissions passthrough to auto-registered resource
# ============================================================================


class TestPermissionsOnAutoResource:
    """Test that permissions are passed through to auto-registered view resources."""

    @pytest.fixture
    def server(self):
        from chuk_mcp_server.core import ChukMCPServer

        return ChukMCPServer(name="test-perm-resource", version="0.1.0")

    def test_permissions_on_auto_registered_resource(self, server):
        """Auto-registered resource should include permissions in its _meta.ui."""
        perms = {"camera": {}, "microphone": {}}

        @server.view_tool(
            resource_uri="ui://test-perm-resource/recorder",
            view_url="https://cdn.example.com/recorder/v1",
            permissions=perms,
        )
        def recorder() -> dict:
            return {"content": [{"type": "text", "text": "rec"}], "structuredContent": {"mode": "video"}}

        # Check the auto-registered resource has permissions
        resource_handler = server.protocol.resources.get("ui://test-perm-resource/recorder")
        assert resource_handler is not None
        fmt = resource_handler.to_mcp_format()
        assert "_meta" in fmt
        assert fmt["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_PERMISSIONS] == perms

    def test_no_permissions_on_resource_when_none(self, server):
        """Auto-registered resource should not have permissions when not set."""

        @server.view_tool(
            resource_uri="ui://test-perm-resource/simple",
            view_url="https://cdn.example.com/simple/v1",
        )
        def simple() -> dict:
            return {"content": [{"type": "text", "text": "s"}], "structuredContent": {}}

        resource_handler = server.protocol.resources.get("ui://test-perm-resource/simple")
        assert resource_handler is not None
        fmt = resource_handler.to_mcp_format()
        # No _meta at all (no csp, no prefersBorder, no permissions)
        assert "_meta" not in fmt
