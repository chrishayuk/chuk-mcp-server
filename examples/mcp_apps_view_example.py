#!/usr/bin/env python3
"""
MCP Apps View Example — render rich UI views in Claude.ai

This example shows how to create tools that render interactive views
(charts, maps, tables, etc.) using MCP Apps structured content.

When Claude.ai calls a tool with `_meta.ui`, it:
1. Reads the view HTML via `resources/read` on the `resourceUri`
2. Renders it in an iframe
3. Passes `structuredContent` as the data payload

ChukMCPServer handles step 1 automatically — when you register a tool
with `_meta.ui.resourceUri` (ui:// scheme) and `_meta.ui.viewUrl`,
the server auto-creates a resource that fetches the HTML from the CDN.

Requirements:
    pip install chuk-mcp-server httpx
"""

from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(
    name="view-example",
    version="1.0.0",
    description="MCP Apps view example server",
)


# ---------------------------------------------------------------------------
# A tool that renders a chart view in Claude.ai
# ---------------------------------------------------------------------------
#
# The `meta` dict tells Claude.ai this tool produces a rich view:
#   - resourceUri: a ui:// URI identifying the view (used for resources/read)
#   - viewUrl: the HTTPS URL serving the view's HTML/JS bundle
#
# ChukMCPServer automatically:
#   - Registers a resource at the resourceUri that fetches HTML from viewUrl
#   - Enables the `experimental` capability
#
@mcp.tool(
    name="show_chart",
    description="Show programming language popularity as a chart.",
    read_only_hint=True,
    meta={
        "ui": {
            "resourceUri": "ui://view-example/chart",
            "viewUrl": "https://chuk-mcp-ui-views.fly.dev/chart/v1",
        }
    },
)
async def show_chart(chart_type: str = "bar") -> dict:
    """Render a chart. Returns structured content for the view iframe."""
    return {
        "content": [{"type": "text", "text": "Programming language popularity chart."}],
        "structuredContent": {
            "type": "chart",
            "version": "1.0",
            "title": "Programming Language Popularity 2025",
            "chartType": chart_type,
            "data": [
                {
                    "label": "Popularity (%)",
                    "values": [
                        {"label": "Python", "value": 28.1},
                        {"label": "JavaScript", "value": 21.3},
                        {"label": "TypeScript", "value": 12.7},
                        {"label": "Java", "value": 10.5},
                        {"label": "C#", "value": 7.8},
                        {"label": "Go", "value": 5.2},
                        {"label": "Rust", "value": 3.9},
                    ],
                }
            ],
        },
    }


# ---------------------------------------------------------------------------
# A tool that renders a markdown view
# ---------------------------------------------------------------------------
@mcp.tool(
    name="show_readme",
    description="Show a rich markdown document.",
    read_only_hint=True,
    meta={
        "ui": {
            "resourceUri": "ui://view-example/markdown",
            "viewUrl": "https://chuk-mcp-ui-views.fly.dev/markdown/v1",
        }
    },
)
async def show_readme() -> dict:
    """Render a markdown document in a rich view."""
    return {
        "content": [{"type": "text", "text": "Project README document."}],
        "structuredContent": {
            "type": "markdown",
            "version": "1.0",
            "title": "My Project",
            "content": (
                "# My Project\n\n"
                "A sample project demonstrating **MCP Apps** views.\n\n"
                "## Features\n\n"
                "- Interactive charts\n"
                "- Rich markdown rendering\n"
                "- Data tables with sorting\n\n"
                "```python\n"
                'mcp.tool(meta={"ui": {...}})\n'
                "```\n"
            ),
        },
    }


if __name__ == "__main__":
    mcp.run()
