#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/adapters/gcf.py
"""
Google Cloud Functions Adapter

Modular adapter that automatically configures ChukMCPServer for Google Cloud Functions.
"""

import logging
import os
from collections.abc import Callable
from typing import Any

from chuk_mcp_server.constants import (
    CONTENT_TYPE_JSON,
    CORS_ALLOW_ALL,
    HEADER_CONTENT_TYPE,
    HEADER_CORS_HEADERS,
    HEADER_CORS_MAX_AGE,
    HEADER_CORS_METHODS,
    HEADER_CORS_ORIGIN,
    HEADER_MCP_SESSION_ID,
    JSONRPC_KEY,
    JSONRPC_VERSION,
    JsonRpcError,
    McpMethod,
)

from . import CloudAdapter, cloud_adapter

logger = logging.getLogger(__name__)


@cloud_adapter("gcf")
class GCFAdapter(CloudAdapter):
    """Google Cloud Functions adapter with zero configuration."""

    def __init__(self, server):
        super().__init__(server)
        self._handler_function = None
        self._is_setup = False

    def is_compatible(self) -> bool:
        """Check if current environment is Google Cloud Functions."""
        gcf_indicators = [
            "GOOGLE_CLOUD_FUNCTION_NAME",  # Gen 1
            "FUNCTION_NAME",  # Gen 2
            "FUNCTION_TARGET",  # Gen 2
            "K_SERVICE",  # Cloud Run (GCF Gen 2)
        ]

        detected = any(os.environ.get(var) for var in gcf_indicators)
        if detected:
            logger.debug("🌟 Google Cloud Functions environment detected")
        return detected

    def setup(self) -> bool:
        """Setup ChukMCPServer for Google Cloud Functions."""
        try:
            # Verify functions-framework is available
            try:
                import functions_framework  # noqa: F401
            except ImportError:
                logger.error(
                    "functions-framework is required for GCF support. Install with: pip install 'chuk-mcp-server[gcf]'"
                )
                return False

            # Create the GCF handler
            self._create_gcf_handler()

            # Apply GCF-specific optimizations
            self._apply_gcf_optimizations()

            self._is_setup = True
            logger.info("✅ GCF adapter setup complete")
            return True

        except Exception as e:
            logger.error(f"Failed to setup GCF adapter: {e}")
            return False

    def get_handler(self) -> Callable | None:
        """Get the GCF handler function."""
        return self._handler_function

    def get_deployment_info(self) -> dict[str, Any]:
        """Get GCF deployment information."""
        return {
            "platform": "Google Cloud Functions",
            "entry_point": "mcp_gcf_handler",
            "runtime": "python311",
            "deployment_command": self._get_deployment_command(),
            "test_urls": self._get_test_urls(),
            "configuration": self._get_gcf_config_info(),
        }

    def _create_gcf_handler(self):
        """Create the GCF handler function."""
        import functions_framework

        @functions_framework.http
        def mcp_gcf_handler(request):
            """Auto-generated GCF handler for ChukMCPServer."""
            return self._handle_gcf_request(request)

        # Store reference to the handler
        self._handler_function = mcp_gcf_handler

        # Make handler globally available for GCF
        import sys

        current_module = sys.modules[__name__]
        current_module.mcp_gcf_handler = mcp_gcf_handler

        logger.info("📦 Created GCF handler: mcp_gcf_handler")

    def _handle_gcf_request(self, request):
        """Handle GCF HTTP request and convert to MCP."""
        # Auto-handle CORS preflight
        if request.method == "OPTIONS":
            return self._cors_preflight_response()

        try:
            # Convert GCF request to MCP format
            mcp_request = self._convert_gcf_to_mcp_request(request)

            # Process through MCP protocol (async handling)
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                response_data, session_id = loop.run_until_complete(
                    self.server.protocol.handle_request(mcp_request, session_id=None)
                )
            finally:
                loop.close()

            # Convert response back to GCF format
            return self._convert_mcp_to_gcf_response(response_data, session_id)

        except Exception as e:
            logger.error(f"GCF request handling error: {e}")
            return self._error_response(str(e))

    def _convert_gcf_to_mcp_request(self, request) -> dict[str, Any]:
        """Convert GCF request to MCP JSON-RPC format."""
        if request.method == "GET":
            # Handle GET requests as simple commands
            path = request.path.strip("/")
            path_mapping = {
                "ping": {"method": McpMethod.PING, "id": "gcf_ping"},
                "health": {"method": McpMethod.TOOLS_LIST, "id": "gcf_health"},
                "tools": {"method": McpMethod.TOOLS_LIST, "id": "gcf_tools"},
                "resources": {"method": McpMethod.RESOURCES_LIST, "id": "gcf_resources"},
            }
            return path_mapping.get(path, {"method": McpMethod.TOOLS_LIST, "id": "gcf_default"})

        elif request.method == "POST":
            # Handle JSON-RPC requests
            try:
                data = request.get_json(force=True)
                if data and isinstance(data, dict):
                    return data
                else:
                    return {"method": McpMethod.TOOLS_LIST, "id": "gcf_invalid_json"}
            except Exception:
                return {"method": McpMethod.TOOLS_LIST, "id": "gcf_parse_error"}

        else:
            return {"method": McpMethod.TOOLS_LIST, "id": "gcf_unsupported_method"}

    def _convert_mcp_to_gcf_response(self, response_data: dict | None, session_id: str | None):
        """Convert MCP response to GCF HTTP response."""
        import json

        headers = {
            HEADER_CONTENT_TYPE: CONTENT_TYPE_JSON,
            HEADER_CORS_ORIGIN: CORS_ALLOW_ALL,
            HEADER_CORS_METHODS: "GET, POST, OPTIONS",
            HEADER_CORS_HEADERS: "Content-Type, Authorization",
        }

        if session_id:
            headers[HEADER_MCP_SESSION_ID] = session_id

        if response_data:
            body = json.dumps(response_data, separators=(",", ":"))
            return (body, 200, headers)
        else:
            return ('{"status": "ok"}', 200, headers)

    def _cors_preflight_response(self):
        """Auto-generated CORS preflight response."""
        headers = {
            HEADER_CORS_ORIGIN: CORS_ALLOW_ALL,
            HEADER_CORS_METHODS: "GET, POST, OPTIONS",
            HEADER_CORS_HEADERS: "Content-Type, Authorization",
            HEADER_CORS_MAX_AGE: "3600",
        }
        return ("", 204, headers)

    def _error_response(self, error_message: str):
        """Generate error response."""
        import json

        headers = {
            HEADER_CONTENT_TYPE: CONTENT_TYPE_JSON,
            HEADER_CORS_ORIGIN: CORS_ALLOW_ALL,
        }

        body = json.dumps(
            {
                JSONRPC_KEY: JSONRPC_VERSION,
                "error": {"code": JsonRpcError.INTERNAL_ERROR, "message": f"GCF Handler Error: {error_message}"},
                "id": "gcf_error",
            },
            separators=(",", ":"),
        )

        return (body, 500, headers)

    def _apply_gcf_optimizations(self):
        """Apply GCF-specific optimizations to the server."""
        # Set logging level for performance
        import logging

        logging.getLogger("chuk_mcp_server").setLevel(logging.WARNING)

        logger.info("⚡ Applied GCF performance optimizations")

    def _get_deployment_command(self) -> str:
        """Get the GCF deployment command."""
        function_name = os.environ.get("FUNCTION_NAME", "my-mcp-server")

        return f"""gcloud functions deploy {function_name} \\
  --gen2 \\
  --runtime python311 \\
  --source . \\
  --entry-point mcp_gcf_handler \\
  --trigger-http \\
  --allow-unauthenticated \\
  --memory 1GB \\
  --timeout 540s"""

    def _get_test_urls(self) -> dict[str, str]:
        """Get test URLs for the deployed function."""
        region = os.environ.get("FUNCTION_REGION", "us-central1")
        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "YOUR-PROJECT")
        function_name = os.environ.get("FUNCTION_NAME", "my-mcp-server")

        base_url = f"https://{region}-{project}.cloudfunctions.net/{function_name}"

        return {
            "health_check": f"{base_url}/ping",
            "tools_list": base_url,
            "mcp_endpoint": base_url,
        }

    def _get_gcf_config_info(self) -> dict[str, Any]:
        """Get GCF configuration information."""
        return {
            "function_name": os.environ.get("FUNCTION_NAME", "unknown"),
            "memory_mb": int(os.environ.get("FUNCTION_MEMORY_MB", 512)),
            "timeout_sec": int(os.environ.get("FUNCTION_TIMEOUT_SEC", 60)),
            "region": os.environ.get("FUNCTION_REGION", "unknown"),
            "project": os.environ.get("GOOGLE_CLOUD_PROJECT", "unknown"),
            "generation": self._detect_gcf_generation(),
        }

    def _detect_gcf_generation(self) -> str:
        """Detect GCF generation."""
        if os.environ.get("GOOGLE_CLOUD_FUNCTION_NAME"):
            return "gen1"
        elif os.environ.get("FUNCTION_TARGET") or os.environ.get("K_SERVICE"):
            return "gen2"
        else:
            return "unknown"


# ============================================================================
# Module-level exports for GCF
# ============================================================================

# Global reference to handler (set when adapter is created)
mcp_gcf_handler = None


def get_gcf_handler():
    """Get the GCF handler function."""
    from . import adapter_registry

    adapter = adapter_registry.get_active_adapter()
    if adapter and isinstance(adapter, GCFAdapter):
        return adapter.get_handler()

    # Try to auto-setup if not already done
    from ... import get_or_create_global_server

    server = get_or_create_global_server()

    gcf_adapter = GCFAdapter(server)
    if gcf_adapter.is_compatible() and gcf_adapter.setup():
        adapter_registry._active_adapter = gcf_adapter
        return gcf_adapter.get_handler()

    return None


# Auto-export handler when module is imported in GCF environment
if any(os.environ.get(var) for var in ["GOOGLE_CLOUD_FUNCTION_NAME", "FUNCTION_NAME", "FUNCTION_TARGET", "K_SERVICE"]):
    handler = get_gcf_handler()
    if handler:
        mcp_gcf_handler = handler
