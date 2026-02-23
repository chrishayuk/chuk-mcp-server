"""
Shot 4: The @mcp.view_tool() Way — built-in chuk-mcp-server decorator.

One decorator handles all the MCP Apps plumbing:
  - Builds _meta.ui with resourceUri and viewUrl
  - Sets readOnlyHint=True
  - Auto-registers the ui:// resource (fetches HTML from viewUrl CDN)
  - Enables the experimental MCP Apps capability

No HTML. No JavaScript. No manual resource registration.
You just return content + structuredContent.

This is the chuk-mcp-server equivalent of manual_server.py.

Run locally:  uv run examples/chuk_manual_server.py
"""

from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(
    name="language-stats",
    version="1.0.0",
    description="MCP Apps with @mcp.view_tool()",
)


@mcp.view_tool(
    resource_uri="ui://language-stats/chart",
    view_url="https://chuk-mcp-ui-views.fly.dev/chart/v1",
    description="Show programming language popularity as an interactive chart.",
)
async def show_chart(chart_type: str = "bar") -> dict:
    """Show programming language popularity as an interactive chart.
    chart_type: bar, pie, line, doughnut, or area."""

    data = {
        "Python": 31.0,
        "JavaScript": 25.2,
        "Rust": 18.1,
        "Go": 14.3,
        "TypeScript": 11.4,
    }

    return {
        # What the LLM sees — text summary for reasoning
        "content": [
            {
                "type": "text",
                "text": f"Programming language popularity ({chart_type} chart).",
            }
        ],
        # What the UI sees — full data, hydrates the chart component
        "structuredContent": {
            "type": "chart",
            "version": "1.0",
            "title": "Programming Language Popularity (2026)",
            "chartType": chart_type,
            "data": [
                {
                    "label": "Usage %",
                    "values": [{"label": lang, "value": pct} for lang, pct in data.items()],
                }
            ],
        },
    }


if __name__ == "__main__":
    mcp.run()
