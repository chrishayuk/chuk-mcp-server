"""
MCP Apps Record — three demo servers composed into one.

This is the chuk-mcp-server equivalent of server.py.

Instead of Starlette path mounts, chuk-mcp-server uses import_server()
to compose multiple servers into a single MCP endpoint. Tools get
namespaced with a prefix:

  simple.get_language_popularity    — Shot 3: plain text, no MCP Apps
  manual.show_chart                 — Shot 4: @mcp.view_tool() decorator
  decorator.show_popularity         — Shot 5: @chart_tool from chuk-view-schemas

Run locally:  uv run examples/chuk_server.py
"""

from chuk_decorator_server import mcp as decorator_mcp
from chuk_manual_server import mcp as manual_mcp
from chuk_simple_server import mcp as simple_mcp

from chuk_mcp_server import ChukMCPServer

app = ChukMCPServer(
    name="language-stats-combined",
    version="1.0.0",
    description="Combined MCP Apps demo — plain, manual, and decorator",
)

# Compose all three servers into one, each with a namespace prefix.
# import_server copies tools (and resources/prompts) at init time.
app.import_server(simple_mcp, prefix="simple")
app.import_server(manual_mcp, prefix="manual")
app.import_server(decorator_mcp, prefix="decorator")

if __name__ == "__main__":
    app.run()
