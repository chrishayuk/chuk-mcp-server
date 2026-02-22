#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/exports.py
"""
Cloud handler getters, detection helpers, and examples.

All functions use lazy ``import chuk_mcp_server`` inside the function body
so that test patches on ``chuk_mcp_server.detect_cloud_provider`` and
``chuk_mcp_server._global_server`` are respected.
"""

from __future__ import annotations

import logging
from typing import Any


def get_cloud_handler() -> object:
    """Magic function to get cloud-specific handler."""
    import chuk_mcp_server

    server = chuk_mcp_server.get_or_create_global_server()
    handler = server.get_cloud_handler()  # type: ignore

    if handler is None:
        cloud_provider = chuk_mcp_server.detect_cloud_provider()
        if cloud_provider:
            raise RuntimeError(
                f"Detected {cloud_provider.display_name} but no handler available. "
                f"Install with: pip install 'chuk-mcp-server[{cloud_provider.name}]'"
            )
        else:
            raise RuntimeError("Not in a cloud environment or no cloud provider detected.")

    return handler


def get_gcf_handler() -> object:
    """Get Google Cloud Functions handler."""
    import chuk_mcp_server

    server = chuk_mcp_server.get_or_create_global_server()
    adapter = server.get_cloud_adapter()  # type: ignore

    if adapter and hasattr(adapter, "get_handler"):
        from ..cloud.providers.gcp import GCPProvider

        cloud_provider = chuk_mcp_server.detect_cloud_provider()
        if cloud_provider and isinstance(cloud_provider, GCPProvider):
            return adapter.get_handler()

    raise RuntimeError(
        "Not in Google Cloud Functions environment or functions-framework not installed. "
        "Install with: pip install 'chuk-mcp-server[gcf]'"
    )


def get_lambda_handler() -> object:
    """Get AWS Lambda handler."""
    import chuk_mcp_server

    server = chuk_mcp_server.get_or_create_global_server()
    adapter = server.get_cloud_adapter()  # type: ignore

    if adapter and hasattr(adapter, "get_handler"):
        from ..cloud.providers.aws import AWSProvider

        cloud_provider = chuk_mcp_server.detect_cloud_provider()
        if cloud_provider and isinstance(cloud_provider, AWSProvider):
            return adapter.get_handler()

    raise RuntimeError("Not in AWS Lambda environment.")


def get_azure_handler() -> object:
    """Get Azure Functions handler."""
    import chuk_mcp_server

    server = chuk_mcp_server.get_or_create_global_server()
    adapter = server.get_cloud_adapter()  # type: ignore

    if adapter and hasattr(adapter, "get_handler"):
        from ..cloud.providers.azure import AzureProvider

        cloud_provider = chuk_mcp_server.detect_cloud_provider()
        if cloud_provider and isinstance(cloud_provider, AzureProvider):
            return adapter.get_handler()

    raise RuntimeError("Not in Azure Functions environment.")


def is_cloud() -> bool:
    """Check if running in any cloud environment."""
    import chuk_mcp_server

    return chuk_mcp_server.is_cloud_environment()


def is_gcf() -> bool:
    """Check if running in Google Cloud Functions."""
    import chuk_mcp_server

    cloud_provider = chuk_mcp_server.detect_cloud_provider()
    return bool(cloud_provider and cloud_provider.name == "gcp")


def is_lambda() -> bool:
    """Check if running in AWS Lambda."""
    import chuk_mcp_server

    cloud_provider = chuk_mcp_server.detect_cloud_provider()
    return bool(cloud_provider and cloud_provider.name == "aws")


def is_azure() -> bool:
    """Check if running in Azure Functions."""
    import chuk_mcp_server

    cloud_provider = chuk_mcp_server.detect_cloud_provider()
    return bool(cloud_provider and cloud_provider.name == "azure")


def get_deployment_info() -> dict[str, Any]:
    """Get deployment information for current environment."""
    import chuk_mcp_server

    server = chuk_mcp_server.get_or_create_global_server()
    return server.get_cloud_deployment_info()  # type: ignore


def _auto_export_cloud_handlers() -> None:
    """Automatically export cloud handlers based on environment detection."""
    import sys

    import chuk_mcp_server

    current_module = sys.modules["chuk_mcp_server"]

    try:
        cloud_provider = chuk_mcp_server.detect_cloud_provider()
        if not cloud_provider:
            return

        # Get the global server and its cloud adapter
        server = chuk_mcp_server.get_or_create_global_server()
        adapter = server.get_cloud_adapter()  # type: ignore

        if not adapter:
            return

        handler = adapter.get_handler()
        if not handler:
            return

        # Export handler with standard names for each platform
        if cloud_provider.name == "gcp":
            current_module.mcp_gcf_handler = handler  # type: ignore

        elif cloud_provider.name == "aws":
            current_module.lambda_handler = handler  # type: ignore
            current_module.handler = handler  # type: ignore

        elif cloud_provider.name == "azure":
            current_module.main = handler  # type: ignore
            current_module.azure_handler = handler  # type: ignore

        elif cloud_provider.name in ["vercel", "netlify", "cloudflare"]:
            current_module.handler = handler  # type: ignore
            current_module.main = handler  # type: ignore

        # Always export generic names
        current_module.cloud_handler = handler  # type: ignore
        current_module.mcp_handler = handler  # type: ignore

    except Exception as e:
        logging.getLogger(__name__).debug(f"Cloud handler auto-export skipped: {e}")


def show_cloud_examples() -> None:
    """Show cloud-specific zero configuration examples."""
    examples = """
Cloud ChukMCPServer - Zero Configuration Examples

1. GOOGLE CLOUD FUNCTIONS:

   # main.py
   from chuk_mcp_server import ChukMCPServer, tool

   mcp = ChukMCPServer()  # Auto-detects GCF!

   @mcp.tool
   def hello_gcf(name: str) -> str:
       return f"Hello from GCF, {name}!"

   # Handler auto-created as 'mcp_gcf_handler'
   # Deploy: gcloud functions deploy my-server --entry-point mcp_gcf_handler

2. AWS LAMBDA:

   # lambda_function.py
   from chuk_mcp_server import ChukMCPServer, tool

   mcp = ChukMCPServer()  # Auto-detects Lambda!

   @mcp.tool
   def hello_lambda(name: str) -> str:
       return f"Hello from Lambda, {name}!"

   # Handler auto-created as 'lambda_handler'
   # Deploy: AWS CLI or SAM

3. AZURE FUNCTIONS:

   # function_app.py
   from chuk_mcp_server import ChukMCPServer, tool

   mcp = ChukMCPServer()  # Auto-detects Azure!

   @mcp.tool
   def hello_azure(name: str) -> str:
       return f"Hello from Azure, {name}!"

   # Handler auto-created as 'main'
   # Deploy: Azure CLI or VS Code

4. VERCEL EDGE:

   # api/mcp.py
   from chuk_mcp_server import tool, get_cloud_handler

   @tool
   def hello_edge(name: str) -> str:
       return f"Hello from Vercel Edge, {name}!"

   # Handler auto-exported
   handler = get_cloud_handler()

5. MULTI-CLOUD (Works everywhere):

   # server.py
   from chuk_mcp_server import ChukMCPServer, tool, is_cloud

   mcp = ChukMCPServer()  # Auto-detects ANY cloud!

   @mcp.tool
   def universal_tool(data: str) -> dict:
       cloud_info = "cloud" if is_cloud() else "local"
       return {"data": data, "environment": cloud_info}

   if __name__ == "__main__":
       if is_cloud():
           print("Cloud environment detected - handler auto-created!")
       else:
           mcp.run()  # Local development

ALL PLATFORMS SUPPORTED WITH ZERO CONFIG:
   Google Cloud Functions (Gen 1 & 2)
   AWS Lambda (x86 & ARM64)
   Azure Functions (Python)
   Vercel Edge Functions
   Netlify Edge Functions
   Cloudflare Workers
   Local Development
   Docker Containers
   Kubernetes
"""
    print(examples)
