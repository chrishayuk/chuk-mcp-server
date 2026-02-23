"""
Shot 3: The "Before" — a plain MCP server with no MCP Apps.
Returns programming language popularity as plain text.

This is the chuk-mcp-server equivalent of simple_server.py.
Same behavior, different framework.

Run locally:  uv run examples/chuk_simple_server.py
"""

from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(
    name="language-stats",
    version="1.0.0",
    description="Plain text language popularity stats",
)


@mcp.tool
async def get_language_popularity() -> str:
    """Get programming language popularity from latest survey data."""
    data = {
        "Python": 31.0,
        "JavaScript": 25.2,
        "Rust": 18.1,
        "Go": 14.3,
        "TypeScript": 11.4,
    }
    lines = [f"  {lang}: {pct}%" for lang, pct in data.items()]
    return "Programming Language Popularity (2026):\n" + "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
