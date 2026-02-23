# MCP Apps — Interactive Views in Claude.ai

MCP Apps let your server tools render rich, interactive HTML UIs (charts, maps, tables, etc.) directly inside Claude.ai and other supporting hosts. When Claude calls a tool that declares a view, the host renders the view HTML in an iframe and passes your tool's data payload to it.

This guide covers how to build MCP Apps view tools with ChukMCPServer.

---

## Quick Start

```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(name="my-views", version="1.0.0")

@mcp.tool(
    name="show_chart",
    description="Show a bar chart of sales data.",
    read_only_hint=True,
    meta={
        "ui": {
            "resourceUri": "ui://my-views/chart",
            "viewUrl": "https://your-cdn.example.com/chart/v1",
        }
    },
)
async def show_chart() -> dict:
    return {
        "content": [{"type": "text", "text": "Sales chart by quarter."}],
        "structuredContent": {
            "type": "chart",
            "chartType": "bar",
            "title": "Q1-Q4 Sales",
            "data": [
                {"label": "Q1", "value": 120},
                {"label": "Q2", "value": 185},
                {"label": "Q3", "value": 210},
                {"label": "Q4", "value": 175},
            ],
        },
    }
```

That's it. ChukMCPServer handles the rest automatically.

---

## How It Works

When you register a tool with `meta.ui`, three things happen at registration time:

1. **`experimental: {}` capability** is enabled (backward compatibility for Claude.ai)
2. **`io.modelcontextprotocol/ui` extension** is advertised in server capabilities
3. **A resource handler** is auto-registered at the `resourceUri` that fetches the view HTML from `viewUrl`

At runtime, when Claude calls your tool:

1. The host reads the view HTML via `resources/read` on the `resourceUri`
2. The host renders the HTML in a sandboxed iframe
3. Your tool's `structuredContent` dict is passed to the iframe as the data payload

```
Client (Claude.ai)                    Server
    |                                    |
    |-- tools/list ---------------------->|  (sees _meta.ui on tool)
    |                                    |
    |-- tools/call "show_chart" -------->|  (returns structuredContent)
    |                                    |
    |-- resources/read "ui://..." ------>|  (returns view HTML)
    |                                    |
    |   [renders iframe with HTML + data]
```

---

## Tool Metadata (`meta`)

The `meta` parameter on `@mcp.tool()` maps to `_meta` in the MCP `tools/list` response.

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `ui.resourceUri` | A `ui://` scheme URI identifying the view. Used by the host to call `resources/read`. | `"ui://my-server/chart"` |
| `ui.viewUrl` | The HTTPS URL serving the view's HTML/JS bundle. The server fetches this to serve via `resources/read`. | `"https://cdn.example.com/chart/v1"` |

### Example

```python
meta={
    "ui": {
        "resourceUri": "ui://my-server/chart",
        "viewUrl": "https://cdn.example.com/chart/v1",
    }
}
```

### URI Scheme

- `resourceUri` **must** use the `ui://` scheme. This is a virtual URI — it doesn't resolve to a network address. The server maps it to the view HTML served from `viewUrl`.
- The path structure is up to you. Convention: `ui://{server-name}/{view-name}`.

### Legacy Flat Key

For compatibility with the ext-apps SDK, the server automatically adds a flat key `_meta["ui/resourceUri"]` alongside the nested `_meta.ui.resourceUri`. You don't need to set this manually.

---

## Structured Content

View tools return a dict with two top-level keys:

```python
return {
    "content": [{"type": "text", "text": "Fallback text for non-visual clients."}],
    "structuredContent": {
        # Your view-specific data payload
        "type": "chart",
        "chartType": "bar",
        "data": [...]
    },
}
```

| Key | Purpose |
|-----|---------|
| `content` | Standard MCP text content. Shown by clients that don't support views. |
| `structuredContent` | The data payload passed to the view iframe. Structure depends on your view HTML. |

The protocol handler detects the `structuredContent` key and passes the result through directly — it does **not** re-wrap it via `format_content()`.

---

## Auto-Resource Registration

When a tool has both `resourceUri` (with `ui://` scheme) and `viewUrl` in its metadata, the server automatically:

1. Creates an async resource handler that fetches the HTML from `viewUrl` via `httpx`
2. Registers it at the `resourceUri` with MIME type `text/html;profile=mcp-app`
3. Caches the HTML for 1 hour (`cache_ttl=3600`)

This means you don't need to manually register a resource — the `@mcp.tool()` decorator handles everything.

### Requirements

- `httpx` must be installed (it's a transitive dependency of chuk-mcp-server)
- The `viewUrl` must be publicly accessible (the server fetches it at request time)

### Manual Resource Registration

If you need custom behavior (e.g., inline HTML, different caching), register the resource yourself before the tool:

```python
@mcp.resource(
    uri="ui://my-server/chart",
    name="chart",
    mime_type="text/html;profile=mcp-app",
)
async def chart_html() -> str:
    return "<html>...</html>"

@mcp.tool(
    name="show_chart",
    meta={"ui": {"resourceUri": "ui://my-server/chart"}},
)
async def show_chart() -> dict:
    return {"content": [...], "structuredContent": {...}}
```

When the resource already exists, auto-registration is skipped.

---

## Server Capabilities

When a tool with `_meta.ui` is registered, the server enables two capabilities:

### `experimental: {}`

Required by Claude.ai to know the server supports structured content. Enabled automatically when any tool has `meta` set.

### `extensions.io.modelcontextprotocol/ui`

The official MCP Apps extension ID. Advertised in `capabilities.extensions` when a tool has a `ui://` resourceUri. This tells hosts that the server can serve MCP Apps views.

```json
{
  "capabilities": {
    "tools": {"listChanged": true},
    "resources": {"listChanged": true, "subscribe": true},
    "experimental": {},
    "extensions": {
      "io.modelcontextprotocol/ui": {
        "mimeTypes": ["text/html;profile=mcp-app"]
      }
    }
  }
}
```

---

## View HTML

The view HTML is a standalone page that receives data from the host. At minimum, it needs to:

1. Listen for a `message` event containing the `structuredContent` data
2. Render the data into the DOM

### Minimal Example

```html
<!DOCTYPE html>
<html>
<head><title>My View</title></head>
<body>
  <div id="root"></div>
  <script>
    window.addEventListener("message", (event) => {
      const data = event.data;
      if (data && data.type === "chart") {
        document.getElementById("root").textContent = JSON.stringify(data);
      }
    });
  </script>
</body>
</html>
```

### Using the ext-apps SDK

For production views, use the official `@anthropic/ext-apps` SDK:

```html
<script type="module">
  import { App } from "https://cdn.jsdelivr.net/npm/@anthropic/ext-apps/+esm";

  const app = new App();
  app.ontoolresult = (result) => {
    // result.structuredContent contains your data
    renderChart(result.structuredContent);
  };
  await app.connect();
</script>
```

The ext-apps SDK provides:
- Automatic theme integration (dark/light mode, host CSS variables)
- Auto-resize reporting via `ResizeObserver`
- `callServerTool()` for bidirectional interaction
- `updateModelContext()` to push context updates to the model
- `sendMessage()` to trigger new model turns

---

## Tool Annotations

View tools should typically set `read_only_hint=True` since they only display data:

```python
@mcp.tool(
    name="show_chart",
    read_only_hint=True,
    meta={"ui": {...}},
)
async def show_chart() -> dict:
    ...
```

---

## Testing View Tools

Use `ToolRunner` to test view tools without transport overhead:

```python
import pytest
from chuk_mcp_server.testing import ToolRunner

@pytest.fixture
def runner(server):
    return ToolRunner(server)

async def test_chart_returns_structured_content(runner):
    response = await runner.call_tool("show_chart")
    result = response["result"]

    assert "structuredContent" in result
    assert result["structuredContent"]["type"] == "chart"
    assert result["content"][0]["text"] == "Sales chart by quarter."

async def test_chart_tool_has_meta(runner):
    tools = await runner.list_tools()
    chart = next(t for t in tools if t["name"] == "show_chart")

    assert "_meta" in chart
    assert chart["_meta"]["ui"]["resourceUri"] == "ui://my-views/chart"

async def test_view_resource_auto_registered(server):
    handler = server.protocol_handler
    assert "ui://my-views/chart" in handler.resources
```

---

## Deployment

### View HTML Hosting

The view HTML (`viewUrl`) must be served over HTTPS. Options:

- **CDN**: Deploy to Cloudflare Pages, Netlify, Vercel, or similar
- **Same server**: Serve static files alongside your MCP server (not recommended for production)
- **Fly.io**: Deploy a static site app

### MCP Server

Deploy your MCP server as usual:

```bash
# HTTP mode (for Claude.ai remote MCP)
python server.py --transport http --port 8000

# STDIO mode (for Claude Desktop)
python server.py
```

### Claude.ai Configuration

Add your server as a remote MCP server in Claude.ai settings. The server URL should be the `/mcp` endpoint:

```
https://your-server.example.com/mcp
```

---

## Complete Example

See [`examples/mcp_apps_view_example.py`](../../examples/mcp_apps_view_example.py) for a complete working example with chart and markdown views.

---

## Related

- [ARCHITECTURE.md](../../ARCHITECTURE.md) — Architecture principles (Principle 9: Full MCP Protocol Conformance)
- [ROADMAP.md](../../ROADMAP.md) — Phase 7.5: MCP Apps Extension Protocol
- [Tool Features Example](../../examples/tool_features_example.py) — Tool annotations, structured output, icons
- [MCP Apps Specification](https://modelcontextprotocol.io/extensions/apps/overview) — Official ext-apps protocol spec
