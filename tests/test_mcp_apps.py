#!/usr/bin/env python3
"""Tests for MCP Apps support (_meta on tools, structuredContent passthrough)."""

import orjson
import pytest

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
        assert fmt["_meta"] == meta

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
        assert data["_meta"] == meta

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
        assert fmt["_meta"] == meta


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
