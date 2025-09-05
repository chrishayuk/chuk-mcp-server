#!/usr/bin/env python3
# src/chuk_mcp_server/__init__.py (Enhanced with Modular Cloud Support)
"""
ChukMCPServer - Zero Configuration MCP Framework with Modular Cloud Support

The world's smartest MCP framework with zero configuration and automatic cloud detection.

ULTIMATE ZERO CONFIG (Works everywhere):
    from chuk_mcp_server import tool, resource, run

    @tool
    def hello(name: str) -> str:
        return f"Hello, {name}!"

    @resource("config://settings")
    def get_settings() -> dict:
        return {"app": "my_app", "magic": True}

    if __name__ == "__main__":
        run()  # Auto-detects EVERYTHING!

CLOUD EXAMPLES:

Google Cloud Functions:
    # main.py
    from chuk_mcp_server import ChukMCPServer, tool

    mcp = ChukMCPServer()  # Auto-detects GCF!

    @mcp.tool
    def hello_gcf(name: str) -> str:
        return f"Hello from GCF, {name}!"

    # Handler auto-created as 'mcp_gcf_handler'
    # Deploy: gcloud functions deploy my-server --entry-point mcp_gcf_handler

AWS Lambda:
    # lambda_function.py
    from chuk_mcp_server import ChukMCPServer, tool

    mcp = ChukMCPServer()  # Auto-detects Lambda!

    @mcp.tool
    def hello_lambda(name: str) -> str:
        return f"Hello from Lambda, {name}!"

    # Handler auto-created as 'lambda_handler'

Azure Functions:
    # function_app.py
    from chuk_mcp_server import ChukMCPServer, tool

    mcp = ChukMCPServer()  # Auto-detects Azure!

    @mcp.tool
    def hello_azure(name: str) -> str:
        return f"Hello from Azure, {name}!"

    # Handler auto-created as 'main'

All platforms work with ZERO configuration! 🚀
"""

import sys

# Import cloud functionality
from .cloud import detect_cloud_provider, is_cloud_environment
from .core import ChukMCPServer, create_mcp_server, quick_server

# Import traditional decorators for global usage
from .decorators import prompt, resource, tool
from .types import (
    MCPPrompt,
    ServerInfo,
    ToolParameter,
    create_server_capabilities,
)
from .types import (
    PromptHandler as Prompt,
)
from .types import (
    ResourceHandler as Resource,
)

# Import types for advanced usage
from .types import (
    ToolHandler as Tool,
)


# Create backward compatibility
def Capabilities(**kwargs):
    """Legacy capabilities function for backward compatibility."""
    return create_server_capabilities(**kwargs)


__version__ = "2.1.0"  # Enhanced cloud support version

# ============================================================================
# Global Magic with Cloud Support
# ============================================================================

_global_server: ChukMCPServer | None = None


def get_or_create_global_server() -> ChukMCPServer:
    """Get or create the global server instance with cloud detection."""
    global _global_server
    if _global_server is None:
        _global_server = ChukMCPServer()  # Auto-detects cloud environment
    return _global_server


def run(**kwargs):
    """Run the global smart server with cloud detection."""
    server = get_or_create_global_server()
    server.run(**kwargs)


# ============================================================================
# Cloud Magic Functions
# ============================================================================


def get_cloud_handler():
    """Magic function to get cloud-specific handler."""
    server = get_or_create_global_server()
    handler = server.get_cloud_handler()

    if handler is None:
        cloud_provider = detect_cloud_provider()
        if cloud_provider:
            raise RuntimeError(
                f"Detected {cloud_provider.display_name} but no handler available. "
                f"Install with: pip install 'chuk-mcp-server[{cloud_provider.name}]'"
            )
        else:
            raise RuntimeError("Not in a cloud environment or no cloud provider detected.")

    return handler


def get_gcf_handler():
    """Get Google Cloud Functions handler."""
    server = get_or_create_global_server()
    adapter = server.get_cloud_adapter()

    if adapter and hasattr(adapter, "get_handler"):
        from .cloud.providers.gcp import GCPProvider

        cloud_provider = detect_cloud_provider()
        if cloud_provider and isinstance(cloud_provider, GCPProvider):
            return adapter.get_handler()

    raise RuntimeError(
        "Not in Google Cloud Functions environment or functions-framework not installed. "
        "Install with: pip install 'chuk-mcp-server[gcf]'"
    )


def get_lambda_handler():
    """Get AWS Lambda handler."""
    server = get_or_create_global_server()
    adapter = server.get_cloud_adapter()

    if adapter and hasattr(adapter, "get_handler"):
        from .cloud.providers.aws import AWSProvider

        cloud_provider = detect_cloud_provider()
        if cloud_provider and isinstance(cloud_provider, AWSProvider):
            return adapter.get_handler()

    raise RuntimeError("Not in AWS Lambda environment.")


def get_azure_handler():
    """Get Azure Functions handler."""
    server = get_or_create_global_server()
    adapter = server.get_cloud_adapter()

    if adapter and hasattr(adapter, "get_handler"):
        from .cloud.providers.azure import AzureProvider

        cloud_provider = detect_cloud_provider()
        if cloud_provider and isinstance(cloud_provider, AzureProvider):
            return adapter.get_handler()

    raise RuntimeError("Not in Azure Functions environment.")


def is_cloud() -> bool:
    """Check if running in any cloud environment."""
    return is_cloud_environment()


def is_gcf() -> bool:
    """Check if running in Google Cloud Functions."""
    cloud_provider = detect_cloud_provider()
    return cloud_provider and cloud_provider.name == "gcp"


def is_lambda() -> bool:
    """Check if running in AWS Lambda."""
    cloud_provider = detect_cloud_provider()
    return cloud_provider and cloud_provider.name == "aws"


def is_azure() -> bool:
    """Check if running in Azure Functions."""
    cloud_provider = detect_cloud_provider()
    return cloud_provider and cloud_provider.name == "azure"


def get_deployment_info() -> dict:
    """Get deployment information for current environment."""
    server = get_or_create_global_server()
    return server.get_cloud_deployment_info()


# ============================================================================
# Auto-Cloud Handler Export
# ============================================================================


def _auto_export_cloud_handlers():
    """Automatically export cloud handlers based on environment detection."""
    import sys

    current_module = sys.modules[__name__]

    try:
        cloud_provider = detect_cloud_provider()
        if not cloud_provider:
            return

        # Get the global server and its cloud adapter
        server = get_or_create_global_server()
        adapter = server.get_cloud_adapter()

        if not adapter:
            return

        handler = adapter.get_handler()
        if not handler:
            return

        # Export handler with standard names for each platform
        if cloud_provider.name == "gcp":
            # GCF expects 'mcp_gcf_handler' or custom entry point
            current_module.mcp_gcf_handler = handler

        elif cloud_provider.name == "aws":
            # Lambda expects 'lambda_handler' by default
            current_module.lambda_handler = handler
            current_module.handler = handler  # Alternative name

        elif cloud_provider.name == "azure":
            # Azure Functions expects 'main' by default
            current_module.main = handler
            current_module.azure_handler = handler  # Alternative name

        elif cloud_provider.name in ["vercel", "netlify", "cloudflare"]:
            # Edge functions often expect 'handler' or 'main'
            current_module.handler = handler
            current_module.main = handler

        # Always export generic names
        current_module.cloud_handler = handler
        current_module.mcp_handler = handler

    except Exception:
        # Silently ignore errors during auto-export
        pass


# Auto-export handlers when module is imported
_auto_export_cloud_handlers()

# ============================================================================
# Enhanced Exports
# ============================================================================

__all__ = [
    # 🧠 PRIMARY INTERFACE (Zero Config)
    "ChukMCPServer",
    # 🪄 MAGIC DECORATORS
    "tool",
    "resource",
    "prompt",
    "run",
    # 🏭 FACTORY FUNCTIONS
    "create_mcp_server",
    "quick_server",
    # ☁️ CLOUD MAGIC
    "get_cloud_handler",  # Generic cloud handler
    "get_gcf_handler",  # Google Cloud Functions
    "get_lambda_handler",  # AWS Lambda
    "get_azure_handler",  # Azure Functions
    # 🔍 CLOUD DETECTION
    "is_cloud",  # Any cloud environment
    "is_gcf",  # Google Cloud Functions
    "is_lambda",  # AWS Lambda
    "is_azure",  # Azure Functions
    "get_deployment_info",  # Deployment information
    # 📚 TYPES & UTILITIES
    "Tool",
    "Resource",
    "Prompt",
    "MCPPrompt",
    "ToolParameter",
    "ServerInfo",
    "Capabilities",
]

# ============================================================================
# Enhanced Examples Documentation
# ============================================================================


def show_cloud_examples():
    """Show cloud-specific zero configuration examples."""
    examples = """
☁️ ChukMCPServer - Cloud Zero Configuration Examples

1️⃣ GOOGLE CLOUD FUNCTIONS:

   # main.py
   from chuk_mcp_server import ChukMCPServer, tool

   mcp = ChukMCPServer()  # 🧠 Auto-detects GCF!

   @mcp.tool
   def hello_gcf(name: str) -> str:
       return f"Hello from GCF, {name}!"

   # ✨ Handler auto-created as 'mcp_gcf_handler'
   # Deploy: gcloud functions deploy my-server --entry-point mcp_gcf_handler

2️⃣ AWS LAMBDA:

   # lambda_function.py
   from chuk_mcp_server import ChukMCPServer, tool

   mcp = ChukMCPServer()  # 🧠 Auto-detects Lambda!

   @mcp.tool
   def hello_lambda(name: str) -> str:
       return f"Hello from Lambda, {name}!"

   # ✨ Handler auto-created as 'lambda_handler'
   # Deploy: AWS CLI or SAM

3️⃣ AZURE FUNCTIONS:

   # function_app.py
   from chuk_mcp_server import ChukMCPServer, tool

   mcp = ChukMCPServer()  # 🧠 Auto-detects Azure!

   @mcp.tool
   def hello_azure(name: str) -> str:
       return f"Hello from Azure, {name}!"

   # ✨ Handler auto-created as 'main'
   # Deploy: Azure CLI or VS Code

4️⃣ VERCEL EDGE:

   # api/mcp.py
   from chuk_mcp_server import tool, get_cloud_handler

   @tool
   def hello_edge(name: str) -> str:
       return f"Hello from Vercel Edge, {name}!"

   # ✨ Handler auto-exported
   handler = get_cloud_handler()

5️⃣ MULTI-CLOUD (Works everywhere):

   # server.py
   from chuk_mcp_server import ChukMCPServer, tool, is_cloud

   mcp = ChukMCPServer()  # 🧠 Auto-detects ANY cloud!

   @mcp.tool
   def universal_tool(data: str) -> dict:
       cloud_info = "cloud" if is_cloud() else "local"
       return {"data": data, "environment": cloud_info}

   if __name__ == "__main__":
       if is_cloud():
           print("🌟 Cloud environment detected - handler auto-created!")
       else:
           mcp.run()  # Local development

🚀 ALL PLATFORMS SUPPORTED WITH ZERO CONFIG:
   ✅ Google Cloud Functions (Gen 1 & 2)
   ✅ AWS Lambda (x86 & ARM64)
   ✅ Azure Functions (Python)
   ✅ Vercel Edge Functions
   ✅ Netlify Edge Functions
   ✅ Cloudflare Workers
   ✅ Local Development
   ✅ Docker Containers
   ✅ Kubernetes
"""
    print(examples)


# Show enhanced examples in interactive environments

if hasattr(sys, "ps1"):  # Interactive Python
    print("🌟 ChukMCPServer v2.1.0 - Enhanced Cloud Support")
    print("Type show_cloud_examples() to see cloud deployment examples!")
