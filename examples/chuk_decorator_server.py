"""
Shot 5: The Decorator Version — the payoff.

Same language popularity data, but using @chart_tool from chuk-view-schemas.
No HTML. No JavaScript. No resource registration. No CallToolResult boilerplate.

This is the chuk-mcp-server equivalent of decorator_server.py.
The only difference from the FastMCP version is the import path:
  FastMCP:        from chuk_view_schemas.fastmcp import chart_tool
  ChukMCPServer:  from chuk_view_schemas.chuk_mcp import chart_tool

Run locally:  uv run examples/chuk_decorator_server.py
"""

from chuk_view_schemas.chart import ChartContent, ChartDataset
from chuk_view_schemas.chuk_mcp import chart_tool

from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(
    name="language-stats",
    version="1.0.0",
    description="Decorator-based MCP Apps demo",
)


@chart_tool(mcp, "show_popularity")
async def show_popularity(chart_type: str = "bar") -> ChartContent:
    """Show programming language popularity as an interactive chart.
    chart_type: bar, pie, line, doughnut, or area."""
    return ChartContent(
        chartType=chart_type,
        title="Programming Language Popularity (2026)",
        data=[
            ChartDataset(
                label="Usage %",
                values=[
                    {"label": "Python", "value": 31.0},
                    {"label": "JavaScript", "value": 25.2},
                    {"label": "Rust", "value": 18.1},
                    {"label": "Go", "value": 14.3},
                    {"label": "TypeScript", "value": 11.4},
                ],
            )
        ],
    )


if __name__ == "__main__":
    mcp.run()
