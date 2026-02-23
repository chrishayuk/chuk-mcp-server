# MCP Apps — Interactive Views in Claude.ai

MCP Apps let your server tools render rich, interactive HTML UIs (charts, maps, tables, etc.) directly inside Claude.ai and other supporting hosts. When Claude calls a tool that declares a view, the host renders the view HTML in an iframe and passes your tool's data payload to it.

This guide covers how to build MCP Apps view tools with ChukMCPServer.

---

## Quick Start

The `@mcp.view_tool()` decorator is the recommended way to create view tools:

```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(name="my-views", version="1.0.0")

@mcp.view_tool(
    resource_uri="ui://my-views/chart",
    view_url="https://your-cdn.example.com/chart/v1",
    description="Show a bar chart of sales data.",
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

That's it. ChukMCPServer handles the rest automatically:
- Builds `_meta.ui` with `resourceUri` and `viewUrl`
- Sets `readOnlyHint=True`
- Auto-registers a `ui://` resource that serves the view HTML
- Enables `experimental` capability and `io.modelcontextprotocol/ui` extension

---

## How It Works

### Three-Party Architecture

MCP Apps involve three parties communicating via two protocols:

```
View (iframe)  ←— ext-apps postMessage —→  Host (Claude.ai)  ←— MCP JSON-RPC —→  Server
```

- **Server ↔ Host**: Standard MCP protocol (`tools/call`, `resources/read`)
- **Host ↔ View**: The ext-apps protocol (`@modelcontextprotocol/ext-apps`) over `window.postMessage`

The Python MCP server does **not** directly handle ext-apps messages. The host (Claude.ai) proxies between views and the server using standard MCP.

### Registration-Time Setup

When you register a tool with `@mcp.view_tool()`, three things happen:

1. **`experimental: {}` capability** is enabled (backward compatibility for Claude.ai)
2. **`io.modelcontextprotocol/ui` extension** is advertised in server capabilities
3. **A resource handler** is auto-registered at the `resourceUri` that fetches the view HTML from `viewUrl`

### Runtime Flow

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
    |                                    |
    |   View ←→ Host (ext-apps postMessage, handled by host)
```

---

## `@view_tool` Decorator

### Instance Decorator (Recommended)

```python
@mcp.view_tool(
    resource_uri="ui://my-server/chart",
    view_url="https://cdn.example.com/chart/v1",
    csp={"connectDomains": ["api.example.com"]},
    visibility=["model", "app"],
    prefers_border=True,
    permissions={"camera": {}, "microphone": {}},
)
async def show_chart(chart_type: str = "bar") -> dict:
    ...
```

### Standalone Decorator

```python
from chuk_mcp_server import view_tool

@view_tool(
    resource_uri="ui://my-server/chart",
    view_url="https://cdn.example.com/chart/v1",
)
def show_chart() -> dict:
    ...
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `resource_uri` | `str` | **Required.** A `ui://` URI identifying the view. |
| `view_url` | `str` | **Required.** HTTPS URL serving the view HTML/JS bundle. |
| `name` | `str \| None` | Custom tool name (defaults to function name). |
| `description` | `str \| None` | Tool description (defaults to docstring). |
| `csp` | `dict \| None` | Content Security Policy with `connectDomains`, `resourceDomains`, `frameDomains`. |
| `visibility` | `list[str] \| None` | Who sees the tool: `["model"]`, `["app"]`, or `["model", "app"]`. |
| `prefers_border` | `bool \| None` | Whether the view prefers a border in the host UI. |
| `permissions` | `dict \| None` | Ext-apps permissions for the iframe (e.g., `{"camera": {}, "clipboard-write": {}}`). |
| `icons` | `list[dict] \| None` | Tool icons. |
| `output_schema` | `dict \| None` | JSON Schema for structured output. |

---

## Permissions

Views can request browser permissions for their iframe sandbox. Declare them via the `permissions` parameter:

```python
@mcp.view_tool(
    resource_uri="ui://my-server/video-recorder",
    view_url="https://cdn.example.com/recorder/v1",
    permissions={"camera": {}, "microphone": {}},
)
async def record_video() -> dict:
    return {
        "content": [{"type": "text", "text": "Video recorder ready."}],
        "structuredContent": {"mode": "record"},
    }
```

Permissions are serialized into `_meta.ui.permissions` and passed through to the auto-registered resource's metadata. The host uses these to configure the iframe's `allow` attribute.

Common permissions:
- `camera` — Access the device camera
- `microphone` — Access the device microphone
- `geolocation` — Access the device location
- `clipboard-write` — Write to the system clipboard

---

## Display Modes

Views can request different display modes from the host via the ext-apps SDK:

| Mode | Description |
|------|-------------|
| `inline` | Default. View renders inline within the conversation. |
| `fullscreen` | View expands to fill the available screen area. |
| `pip` | Picture-in-picture mode (view floats over the conversation). |

Display modes are requested by the view at runtime using `app.requestDisplayMode("fullscreen")`, not configured on the server. The server provides constants for reference:

```python
from chuk_mcp_server.constants import (
    MCP_APPS_DISPLAY_INLINE,
    MCP_APPS_DISPLAY_FULLSCREEN,
    MCP_APPS_DISPLAY_PIP,
)
```

---

## Visibility

Control who sees the tool — the model (LLM), the app (view iframe), or both:

```python
from chuk_mcp_server.constants import (
    MCP_APPS_VISIBILITY_APP_ONLY,
    MCP_APPS_VISIBILITY_MODEL_ONLY,
    MCP_APPS_VISIBILITY_DEFAULT,
)

# Only visible to views (hidden from tools/list for the LLM)
@mcp.view_tool(
    resource_uri="ui://my-server/helper",
    view_url="https://cdn.example.com/helper/v1",
    visibility=MCP_APPS_VISIBILITY_APP_ONLY,
)
async def app_helper() -> dict:
    ...

# Only visible to the model (not exposed to views via callServerTool)
@mcp.view_tool(
    resource_uri="ui://my-server/analysis",
    view_url="https://cdn.example.com/analysis/v1",
    visibility=MCP_APPS_VISIBILITY_MODEL_ONLY,
)
async def model_analysis() -> dict:
    ...
```

App-only tools are hidden from `tools/list` but remain callable via `tools/call`. This lets views use `callServerTool()` to invoke server-side logic without exposing those tools to the LLM.

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
4. Passes through `prefersBorder`, `csp`, and `permissions` metadata to the resource

This means you don't need to manually register a resource — the `@mcp.view_tool()` decorator handles everything.

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

## Ext-Apps Protocol (Host ↔ View)

The ext-apps protocol defines communication between the iframe view and the host (Claude.ai) via `window.postMessage`. It uses JSON-RPC 2.0 format.

### Key Methods

| Method | Direction | Purpose |
|--------|-----------|---------|
| `ui/initialize` | View → Host | Initialize the ext-apps connection |
| `ui/getContext` | View → Host | Get host context (theme, display mode) |
| `ui/notifications/tool-result` | Host → View | Deliver tool result data |
| `ui/notifications/tool-input` | Host → View | Deliver tool input parameters |
| `ui/notifications/size-changed` | View → Host | Report view size change |
| `ui/update-model-context` | View → Host | Push context updates to the model |
| `ui/message` | View → Host | Send a message to trigger a model turn |
| `ui/request-display-mode` | View → Host | Request fullscreen/pip/inline mode |
| `ui/open-link` | View → Host | Open a link in the host browser |
| `ui/resource-teardown` | Host → View | Notify view it's being removed |

These methods are all handled by the host, not by the MCP server. The server provides constants for these method names for reference and logging:

```python
from chuk_mcp_server.constants import (
    MCP_APPS_METHOD_UI_INITIALIZE,
    MCP_APPS_METHOD_UI_TOOL_RESULT,
    MCP_APPS_METHOD_UI_UPDATE_CONTEXT,
    MCP_APPS_METHOD_UI_SEND_MESSAGE,
    # ... etc.
)
```

### Defensive Handling

If the server receives a `ui/*` method (e.g., due to misconfigured routing), it responds with a clear `METHOD_NOT_FOUND` error explaining the method is handled by the host, not the server.

---

## View HTML and the Ext-Apps SDK

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

### Using the Ext-Apps SDK (Recommended)

For production views, use the official `@anthropic/ext-apps` SDK:

```html
<script type="module">
  import { App } from "https://cdn.jsdelivr.net/npm/@anthropic/ext-apps/+esm";

  const app = new App();

  // Receive tool result data
  app.ontoolresult = (result) => {
    renderChart(result.structuredContent);
  };

  // Receive tool input (parameters the model chose)
  app.ontoolinput = (input) => {
    console.log("Tool called with:", input);
  };

  // Connect to the host
  await app.connect();
</script>
```

### SDK Features

The ext-apps SDK provides:

- **Theme integration**: Automatic dark/light mode via CSS variables (`--primary`, `--background`, etc.)
- **Auto-resize**: Reports view size changes to the host via `ResizeObserver`
- **`callServerTool(name, args)`**: Call another MCP tool from the view (bidirectional interaction)
- **`updateModelContext(context)`**: Push context updates to the model (e.g., user selections)
- **`sendMessage(text)`**: Trigger a new model turn with a message
- **`requestDisplayMode(mode)`**: Request fullscreen, pip, or inline display
- **`openLink(url)`**: Open a link in the host's browser

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
    assert "ui://my-views/chart" in server.protocol.resources
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
