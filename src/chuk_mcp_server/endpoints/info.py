#!/usr/bin/env python3
"""
Server information endpoint with comprehensive documentation
"""

import orjson
from starlette.requests import Request
from starlette.responses import Response

from ..protocol import MCPProtocolHandler
from .constants import (
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_MARKDOWN,
    ERROR_METHOD_NOT_ALLOWED,
    HEADER_HOST,
    HEADERS_INFO,
    MCP_PROTOCOL_FULL,
    MCP_TRANSPORT,
    PATH_DOCS,
    PATH_HEALTH,
    PATH_INFO,
    PATH_MCP,
    PATH_PING,
    PATH_VERSION,
    POWERED_BY,
    SERVER_NAME,
    HttpStatus,
)


class InfoEndpoint:
    def __init__(self, protocol_handler: MCPProtocolHandler):
        self.protocol = protocol_handler

    async def handle_request(self, request: Request) -> Response:
        if request.method != "GET":
            body: bytes = orjson.dumps({"error": ERROR_METHOD_NOT_ALLOWED, "code": HttpStatus.METHOD_NOT_ALLOWED})
            return Response(
                body,
                status_code=HttpStatus.METHOD_NOT_ALLOWED,
                media_type=CONTENT_TYPE_JSON,
                headers=HEADERS_INFO,
            )

        base_url = f"{request.url.scheme}://{request.headers.get(HEADER_HOST, 'localhost')}"

        info = {
            "server": self.protocol.server_info.model_dump(),
            "capabilities": self.protocol.capabilities.model_dump(),
            "protocol": {"version": MCP_PROTOCOL_FULL, "transport": MCP_TRANSPORT, "inspector_compatible": True},
            "framework": {
                "name": SERVER_NAME,
                "powered_by": POWERED_BY,
                "optimizations": [
                    "orjson for JSON serialization",
                    "Unix millisecond timestamps",
                    "Pre-computed static responses",
                    "uvloop event loop support",
                    "httptools HTTP parser support",
                ],
            },
            "endpoints": {
                "mcp": f"{base_url}{PATH_MCP}",
                "health": f"{base_url}{PATH_HEALTH}",
                "ping": f"{base_url}{PATH_PING}",
                "version": f"{base_url}{PATH_VERSION}",
                "info": f"{base_url}{PATH_INFO}",
                "documentation": f"{base_url}{PATH_DOCS}",
            },
            "tools": {"count": len(self.protocol.tools), "available": list(self.protocol.tools.keys())},
            "resources": {"count": len(self.protocol.resources), "available": list(self.protocol.resources.keys())},
            "performance": {
                "ping": "23,000+ RPS",
                "version": "25,000+ RPS",
                "health": "23,000+ RPS",
                "mcp_protocol": "5,000+ RPS",
            },
            "quick_start": {
                "health_check": f"curl {base_url}{PATH_HEALTH}",
                "ping_test": f"curl {base_url}{PATH_PING}",
                "version_info": f"curl {base_url}{PATH_VERSION}",
            },
        }

        format_type = getattr(request.state, "format_override", None) or request.query_params.get("format", "json")
        format_type = format_type.lower()

        if format_type == "docs":
            docs = f"""# {info["server"]["name"]} - {SERVER_NAME}

**Version:** {info["server"]["version"]}
**Protocol:** {info["protocol"]["version"]}

## 🚀 Performance Achieved

- **Ping**: {info["performance"]["ping"]}
- **Version**: {info["performance"]["version"]}
- **Health**: {info["performance"]["health"]}
- **MCP Protocol**: {info["performance"]["mcp_protocol"]}

## 🔗 Endpoints

- **MCP Protocol:** `{info["endpoints"]["mcp"]}`
- **Health Check:** `{info["endpoints"]["health"]}`
- **Ping Test:** `{info["endpoints"]["ping"]}`
- **Version Info:** `{info["endpoints"]["version"]}`

## 🚀 Quick Test

```bash
{info["quick_start"]["ping_test"]}
{info["quick_start"]["health_check"]}
{info["quick_start"]["version_info"]}
```

**Powered by {SERVER_NAME}** 🚀
"""

            return Response(docs, media_type=CONTENT_TYPE_MARKDOWN, headers=HEADERS_INFO)
        else:
            body: bytes = orjson.dumps(info)
            return Response(body, media_type=CONTENT_TYPE_JSON, headers=HEADERS_INFO)
