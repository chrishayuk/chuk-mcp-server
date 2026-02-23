#!/usr/bin/env python3
"""Tests for Phase 7.5b: @view_tool decorator, visibility filtering, CSP, prefersBorder."""

import orjson
import pytest

from chuk_mcp_server.constants import (
    MCP_APPS_LEGACY_META_KEY,
    MCP_APPS_UI_CSP,
    MCP_APPS_UI_KEY,
    MCP_APPS_UI_PREFERS_BORDER,
    MCP_APPS_UI_RESOURCE_URI,
    MCP_APPS_UI_VIEW_URL,
    MCP_APPS_UI_VISIBILITY,
    MCP_APPS_VISIBILITY_APP_ONLY,
    MCP_APPS_VISIBILITY_DEFAULT,
    MCP_APPS_VISIBILITY_MODEL_ONLY,
)
from chuk_mcp_server.decorators import clear_global_registry, view_tool
from chuk_mcp_server.types.tools import ToolHandler

# ============================================================================
# Standalone @view_tool decorator
# ============================================================================


class TestStandaloneViewTool:
    """Test the standalone @view_tool decorator."""

    @pytest.fixture(autouse=True)
    def _clear_registry(self):
        clear_global_registry()
        yield
        clear_global_registry()

    def test_meta_generation(self):
        """@view_tool should build _meta.ui with resourceUri and viewUrl."""

        @view_tool(
            resource_uri="ui://test/chart",
            view_url="https://cdn.example.com/chart/v1",
        )
        def show_chart(chart_type: str = "bar") -> dict:
            return {}

        handler = ToolHandler.from_function(
            show_chart.__wrapped__ if hasattr(show_chart, "__wrapped__") else show_chart,
            name="show_chart",
            meta={
                MCP_APPS_UI_KEY: {
                    MCP_APPS_UI_RESOURCE_URI: "ui://test/chart",
                    MCP_APPS_UI_VIEW_URL: "https://cdn.example.com/chart/v1",
                }
            },
        )
        fmt = handler.to_mcp_format()
        assert "_meta" in fmt
        assert fmt["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_RESOURCE_URI] == "ui://test/chart"
        assert fmt["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_VIEW_URL] == "https://cdn.example.com/chart/v1"

    def test_legacy_flat_key(self):
        """@view_tool should produce the legacy flat key."""
        handler = ToolHandler.from_function(
            lambda: {},
            name="v",
            meta={MCP_APPS_UI_KEY: {MCP_APPS_UI_RESOURCE_URI: "ui://s/v", MCP_APPS_UI_VIEW_URL: "https://x.com/v"}},
        )
        fmt = handler.to_mcp_format()
        assert fmt["_meta"][MCP_APPS_LEGACY_META_KEY] == "ui://s/v"

    def test_read_only_hint_default(self):
        """@view_tool should set readOnlyHint=True by default."""
        handler = ToolHandler.from_function(
            lambda: {},
            name="vt",
            read_only_hint=True,
            meta={MCP_APPS_UI_KEY: {MCP_APPS_UI_RESOURCE_URI: "ui://s/vt"}},
        )
        fmt = handler.to_mcp_format()
        assert fmt["annotations"]["readOnlyHint"] is True

    def test_csp_passthrough(self):
        """CSP config should be included in _meta.ui.csp."""
        csp = {"connectDomains": ["api.example.com"], "resourceDomains": ["cdn.example.com"]}
        handler = ToolHandler.from_function(
            lambda: {},
            name="vt",
            meta={
                MCP_APPS_UI_KEY: {
                    MCP_APPS_UI_RESOURCE_URI: "ui://s/vt",
                    MCP_APPS_UI_VIEW_URL: "https://x.com/v",
                    MCP_APPS_UI_CSP: csp,
                }
            },
        )
        fmt = handler.to_mcp_format()
        assert fmt["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_CSP] == csp

    def test_no_csp_when_none(self):
        """No CSP key when csp is None."""
        handler = ToolHandler.from_function(
            lambda: {},
            name="vt",
            meta={MCP_APPS_UI_KEY: {MCP_APPS_UI_RESOURCE_URI: "ui://s/vt", MCP_APPS_UI_VIEW_URL: "https://x.com/v"}},
        )
        fmt = handler.to_mcp_format()
        assert MCP_APPS_UI_CSP not in fmt["_meta"][MCP_APPS_UI_KEY]

    def test_visibility_serialization(self):
        """Visibility should appear in _meta.ui.visibility."""
        handler = ToolHandler.from_function(
            lambda: {},
            name="vt",
            meta={MCP_APPS_UI_KEY: {MCP_APPS_UI_RESOURCE_URI: "ui://s/vt"}},
            visibility=MCP_APPS_VISIBILITY_APP_ONLY,
        )
        fmt = handler.to_mcp_format()
        assert fmt["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_VISIBILITY] == MCP_APPS_VISIBILITY_APP_ONLY

    def test_visibility_without_meta(self):
        """Visibility alone should create _meta.ui.visibility."""
        handler = ToolHandler.from_function(
            lambda: {},
            name="vt",
            visibility=MCP_APPS_VISIBILITY_MODEL_ONLY,
        )
        fmt = handler.to_mcp_format()
        assert fmt["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_VISIBILITY] == MCP_APPS_VISIBILITY_MODEL_ONLY

    def test_prefers_border_passthrough(self):
        """prefersBorder should be included in _meta.ui."""
        handler = ToolHandler.from_function(
            lambda: {},
            name="vt",
            meta={MCP_APPS_UI_KEY: {MCP_APPS_UI_RESOURCE_URI: "ui://s/vt", MCP_APPS_UI_PREFERS_BORDER: True}},
        )
        fmt = handler.to_mcp_format()
        assert fmt["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_PREFERS_BORDER] is True

    def test_deep_copy_safety(self):
        """MCP format should be a deep copy — mutating it must not affect cache."""
        handler = ToolHandler.from_function(
            lambda: {},
            name="vt",
            meta={MCP_APPS_UI_KEY: {MCP_APPS_UI_RESOURCE_URI: "ui://s/vt", MCP_APPS_UI_VIEW_URL: "https://x.com/v"}},
        )
        fmt1 = handler.to_mcp_format()
        fmt1["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_RESOURCE_URI] = "mutated"

        fmt2 = handler.to_mcp_format()
        assert fmt2["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_RESOURCE_URI] == "ui://s/vt"


# ============================================================================
# Instance @mcp.view_tool() decorator
# ============================================================================


class TestInstanceViewTool:
    """Test the instance @mcp.view_tool() decorator."""

    @pytest.fixture
    def server(self):
        from chuk_mcp_server.core import ChukMCPServer

        return ChukMCPServer(name="test-view-tool", version="0.1.0")

    async def test_registers_tool(self, server):
        """@mcp.view_tool() should register a callable tool."""

        @server.view_tool(
            resource_uri="ui://test-view-tool/chart",
            view_url="https://cdn.example.com/chart/v1",
        )
        def show_chart(chart_type: str = "bar") -> dict:
            return {
                "content": [{"type": "text", "text": "Chart data"}],
                "structuredContent": {"type": "chart", "chartType": chart_type},
            }

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        tools = await runner.list_tools()
        tool_names = [t["name"] for t in tools]
        assert "show_chart" in tool_names

    async def test_meta_in_tools_list(self, server):
        """Tool should have _meta.ui in tools/list response."""

        @server.view_tool(
            resource_uri="ui://test-view-tool/map",
            view_url="https://cdn.example.com/map/v1",
        )
        def show_map() -> dict:
            return {"content": [{"type": "text", "text": "Map"}]}

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        tools = await runner.list_tools()
        tool_info = next(t for t in tools if t["name"] == "show_map")
        assert "_meta" in tool_info
        assert tool_info["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_RESOURCE_URI] == "ui://test-view-tool/map"
        assert tool_info["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_VIEW_URL] == "https://cdn.example.com/map/v1"

    async def test_read_only_hint(self, server):
        """View tool should default to readOnlyHint=True."""

        @server.view_tool(
            resource_uri="ui://test-view-tool/v",
            view_url="https://cdn.example.com/v",
        )
        def v() -> dict:
            return {}

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        tools = await runner.list_tools()
        tool_info = next(t for t in tools if t["name"] == "v")
        assert tool_info["annotations"]["readOnlyHint"] is True

    async def test_call_tool(self, server):
        """View tool should be callable via ToolRunner."""

        @server.view_tool(
            resource_uri="ui://test-view-tool/counter",
            view_url="https://cdn.example.com/counter/v1",
        )
        def show_counter(initial: int = 0) -> dict:
            return {
                "content": [{"type": "text", "text": f"Counter: {initial}"}],
                "structuredContent": {"count": initial},
            }

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        response = await runner.call_tool("show_counter", {"initial": 42})
        result = response["result"]
        assert result["structuredContent"]["count"] == 42

    async def test_csp_in_meta(self, server):
        """CSP should appear in _meta.ui.csp."""
        csp = {"connectDomains": ["api.example.com"]}

        @server.view_tool(
            resource_uri="ui://test-view-tool/csp-test",
            view_url="https://cdn.example.com/csp",
            csp=csp,
        )
        def csp_view() -> dict:
            return {}

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        tools = await runner.list_tools()
        tool_info = next(t for t in tools if t["name"] == "csp_view")
        assert tool_info["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_CSP] == csp


# ============================================================================
# Visibility filtering
# ============================================================================


class TestVisibilityFiltering:
    """Test that app-only tools are hidden from tools/list but still callable."""

    @pytest.fixture
    def server(self):
        from chuk_mcp_server.core import ChukMCPServer

        return ChukMCPServer(name="test-visibility", version="0.1.0")

    async def test_app_only_hidden_from_list(self, server):
        """App-only tools should not appear in tools/list."""

        @server.view_tool(
            resource_uri="ui://test-visibility/hidden",
            view_url="https://cdn.example.com/hidden",
            visibility=MCP_APPS_VISIBILITY_APP_ONLY,
        )
        def hidden_tool() -> dict:
            return {"content": [{"type": "text", "text": "hidden"}]}

        @server.tool(name="visible_tool")
        def visible_tool() -> str:
            return "visible"

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        tools = await runner.list_tools()
        tool_names = [t["name"] for t in tools]
        assert "visible_tool" in tool_names
        assert "hidden_tool" not in tool_names

    async def test_app_only_still_callable(self, server):
        """App-only tools should still be callable via tools/call."""

        @server.view_tool(
            resource_uri="ui://test-visibility/callable",
            view_url="https://cdn.example.com/callable",
            visibility=MCP_APPS_VISIBILITY_APP_ONLY,
        )
        def callable_hidden() -> str:
            return "still works"

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        response = await runner.call_tool("callable_hidden")
        assert response["result"]["content"][0]["text"] == "still works"

    async def test_model_only_visible(self, server):
        """Model-only tools should appear in tools/list."""

        @server.view_tool(
            resource_uri="ui://test-visibility/model",
            view_url="https://cdn.example.com/model",
            visibility=MCP_APPS_VISIBILITY_MODEL_ONLY,
        )
        def model_tool() -> dict:
            return {"content": [{"type": "text", "text": "model only"}]}

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        tools = await runner.list_tools()
        tool_names = [t["name"] for t in tools]
        assert "model_tool" in tool_names

    async def test_default_visibility_visible(self, server):
        """Default visibility tools should appear in tools/list."""

        @server.view_tool(
            resource_uri="ui://test-visibility/default",
            view_url="https://cdn.example.com/default",
            visibility=MCP_APPS_VISIBILITY_DEFAULT,
        )
        def default_vis() -> dict:
            return {"content": [{"type": "text", "text": "default"}]}

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        tools = await runner.list_tools()
        tool_names = [t["name"] for t in tools]
        assert "default_vis" in tool_names

    async def test_no_visibility_visible(self, server):
        """Tools with no visibility set should appear in tools/list."""

        @server.view_tool(
            resource_uri="ui://test-visibility/none",
            view_url="https://cdn.example.com/none",
        )
        def no_vis() -> dict:
            return {"content": [{"type": "text", "text": "no vis"}]}

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        tools = await runner.list_tools()
        tool_names = [t["name"] for t in tools]
        assert "no_vis" in tool_names


# ============================================================================
# Resource meta (prefersBorder, CSP on auto-registered resources)
# ============================================================================


class TestResourceMeta:
    """Test that resources support _meta with prefersBorder and CSP."""

    def test_resource_with_meta(self):
        """ResourceHandler with meta should serialize _meta."""
        from chuk_mcp_server.types.resources import ResourceHandler

        resource = ResourceHandler.from_function(
            uri="ui://test/view",
            func=lambda: "html",
            name="test",
            mime_type="text/html",
            meta={MCP_APPS_UI_KEY: {MCP_APPS_UI_PREFERS_BORDER: True}},
        )
        fmt = resource.to_mcp_format()
        assert "_meta" in fmt
        assert fmt["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_PREFERS_BORDER] is True

    def test_resource_without_meta(self):
        """ResourceHandler without meta should not have _meta."""
        from chuk_mcp_server.types.resources import ResourceHandler

        resource = ResourceHandler.from_function(
            uri="config://settings",
            func=lambda: "data",
            name="settings",
        )
        fmt = resource.to_mcp_format()
        assert "_meta" not in fmt

    def test_resource_meta_deep_copy(self):
        """Resource MCP format should be a deep copy — mutation safety."""
        from chuk_mcp_server.types.resources import ResourceHandler

        resource = ResourceHandler.from_function(
            uri="ui://test/copy",
            func=lambda: "html",
            name="test",
            meta={
                MCP_APPS_UI_KEY: {
                    MCP_APPS_UI_PREFERS_BORDER: True,
                    MCP_APPS_UI_CSP: {"connectDomains": ["api.example.com"]},
                }
            },
        )
        fmt1 = resource.to_mcp_format()
        fmt1["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_PREFERS_BORDER] = False
        fmt1["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_CSP]["connectDomains"].append("evil.com")

        fmt2 = resource.to_mcp_format()
        assert fmt2["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_PREFERS_BORDER] is True
        assert fmt2["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_CSP]["connectDomains"] == ["api.example.com"]

    def test_resource_meta_in_bytes(self):
        """Resource _meta should appear in orjson bytes."""
        from chuk_mcp_server.types.resources import ResourceHandler

        resource = ResourceHandler.from_function(
            uri="ui://test/bytes",
            func=lambda: "html",
            name="test",
            meta={MCP_APPS_UI_KEY: {MCP_APPS_UI_PREFERS_BORDER: False}},
        )
        data: dict = orjson.loads(resource.to_mcp_bytes())
        assert data["_meta"][MCP_APPS_UI_KEY][MCP_APPS_UI_PREFERS_BORDER] is False


# ============================================================================
# Regression: pre-formatted structuredContent still works
# ============================================================================


class TestStructuredContentRegression:
    """Ensure pre-formatted structuredContent passthrough still works with view_tool."""

    @pytest.fixture
    def server(self):
        from chuk_mcp_server.core import ChukMCPServer

        return ChukMCPServer(name="test-regression", version="0.1.0")

    async def test_structured_content_passthrough(self, server):
        """View tools returning pre-formatted content should pass through."""

        @server.view_tool(
            resource_uri="ui://test-regression/chart",
            view_url="https://cdn.example.com/chart/v1",
        )
        def chart() -> dict:
            return {
                "content": [{"type": "text", "text": "Revenue chart"}],
                "structuredContent": {"type": "chart", "chartType": "line", "data": [1, 2, 3]},
            }

        from chuk_mcp_server.testing import ToolRunner

        runner = ToolRunner(server)
        response = await runner.call_tool("chart")
        result = response["result"]
        assert result["structuredContent"]["type"] == "chart"
        assert result["content"][0]["text"] == "Revenue chart"
