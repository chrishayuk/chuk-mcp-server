#!/usr/bin/env python3
# src/chuk_mcp_server/core.py
"""
Core - Main ChukMCP Server class with modular smart configuration
"""

import logging
from collections.abc import Callable
from typing import Any

# Import the modular smart configuration system
from .config import SmartConfig
from .decorators import (
    clear_global_registry,
    get_global_prompts,
    get_global_resources,
    get_global_tools,
)
from .endpoint_registry import http_endpoint_registry
from .http_server import create_server
from .mcp_registry import mcp_registry
from .protocol import MCPProtocolHandler

# Updated imports for clean types API
from .types import (
    PromptHandler,
    ResourceHandler,
    # Direct chuk_mcp types
    ServerInfo,
    # Framework handlers
    ToolHandler,
    create_server_capabilities,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Main ChukMCPServer Class with Modular Smart Configuration
# ============================================================================


class ChukMCPServer:
    """
    ChukMCPServer - Zero configuration MCP framework with modular smart configuration.

    Usage:
        # Zero config - everything auto-detected using modular system
        mcp = ChukMCPServer()

        @mcp.tool
        def hello(name: str) -> str:
            return f"Hello, {name}!"

        mcp.run()  # Auto-detects host, port, performance settings using SmartConfig
    """

    def __init__(
        self,
        name: str | None = None,
        version: str = "1.0.0",
        title: str | None = None,
        description: str | None = None,  # noqa: ARG002
        capabilities=None,
        tools: bool = True,
        resources: bool = True,
        prompts: bool = False,
        logging: bool = False,
        experimental: dict[str, Any] | None = None,
        # Smart defaults (all optional - will use SmartConfig)
        host: str | None = None,
        port: int | None = None,
        debug: bool | None = None,
        **kwargs,  # noqa: ARG002
    ):
        """
        Initialize ChukMCP Server with modular smart configuration.

        Args:
            name: Server name (auto-detected if None)
            version: Server version
            title: Optional server title
            description: Optional server description
            capabilities: ServerCapabilities object (auto-configured if None)
            tools: Enable tools capability
            resources: Enable resources capability
            prompts: Enable prompts capability
            logging: Enable logging capability
            experimental: Experimental capabilities
            host: Host to bind to (auto-detected if None)
            port: Port to bind to (auto-detected if None)
            debug: Debug mode (auto-detected if None)
            **kwargs: Additional keyword arguments
        """
        # Initialize the modular smart configuration system
        self.smart_config = SmartConfig()

        # Get all smart defaults in one efficient call
        smart_defaults = self.smart_config.get_all_defaults()

        # Auto-detect name if not provided
        if name is None:
            name = smart_defaults["project_name"]

        # Use chuk_mcp ServerInfo directly
        self.server_info = ServerInfo(name=name, version=version, title=title)

        # Handle capabilities flexibly
        if capabilities is not None:
            self.capabilities = capabilities
        else:
            self.capabilities = create_server_capabilities(
                tools=tools, resources=resources, prompts=prompts, logging=logging, experimental=experimental
            )

        # Store smart defaults for run() - using modular config
        self.smart_host = host or smart_defaults["host"]
        self.smart_port = port or smart_defaults["port"]
        self.smart_debug = debug if debug is not None else smart_defaults["debug"]

        # Store additional smart configuration
        self.smart_environment = smart_defaults["environment"]
        self.smart_workers = smart_defaults["workers"]
        self.smart_max_connections = smart_defaults["max_connections"]
        self.smart_log_level = smart_defaults["log_level"]
        self.smart_performance_mode = smart_defaults["performance_mode"]
        self.smart_containerized = smart_defaults["containerized"]
        self.smart_transport_mode = smart_defaults.get("transport_mode", "http")

        # Create protocol handler with direct chuk_mcp types
        self.protocol = MCPProtocolHandler(self.server_info, self.capabilities)

        # Register any globally decorated functions
        self._register_global_functions()

        # HTTP server will be created when needed
        self._server = None

        # Print smart configuration info in debug mode
        if self.smart_debug:
            self._print_smart_config()

        logger.info(f"Initialized ChukMCP Server: {name} v{version}")

    def _print_smart_config(self):
        """Print smart configuration summary using modular config."""
        import sys

        # Always use stderr for debug output to keep stdout clean
        output = sys.stderr
        print("🧠 ChukMCPServer - Modular Zero Configuration Mode", file=output)
        print("=" * 60, file=output)
        print(f"📊 Environment: {self.smart_environment}", file=output)
        print(f"🌐 Network: {self.smart_host}:{self.smart_port}", file=output)
        print(f"🔧 Workers: {self.smart_workers}", file=output)
        print(f"🔗 Max Connections: {self.smart_max_connections}", file=output)
        print(f"🐳 Container: {self.smart_containerized}", file=output)
        print(f"⚡ Performance Mode: {self.smart_performance_mode}", file=output)
        print(f"📝 Log Level: {self.smart_log_level}", file=output)
        print("=" * 60, file=output)

    def _register_global_functions(self):
        """Register globally decorated functions in both protocol and registries."""
        # Register global tools
        for tool in get_global_tools():
            if hasattr(tool, "handler"):
                tool_handler = tool
            else:
                tool_handler = ToolHandler.from_function(tool.handler, name=tool.name, description=tool.description)

            self.protocol.register_tool(tool_handler)
            mcp_registry.register_tool(tool_handler.name, tool_handler)

        # Register global resources
        for resource in get_global_resources():
            if hasattr(resource, "handler"):
                resource_handler = resource
            else:
                resource_handler = ResourceHandler.from_function(
                    resource.uri,
                    resource.handler,
                    name=resource.name,
                    description=resource.description,
                    mime_type=resource.mime_type,
                )

            self.protocol.register_resource(resource_handler)
            mcp_registry.register_resource(resource_handler.uri, resource_handler)

        # Register global prompts
        for prompt in get_global_prompts():
            if hasattr(prompt, "handler"):
                prompt_handler = prompt
            else:
                prompt_handler = PromptHandler.from_function(
                    prompt.handler, name=prompt.name, description=prompt.description
                )

            self.protocol.register_prompt(prompt_handler)
            mcp_registry.register_prompt(prompt_handler.name, prompt_handler)

        # Clear global registry to avoid duplicate registrations
        clear_global_registry()

    # ============================================================================
    # Tool Registration
    # ============================================================================

    def tool(self, name: str | None = None, description: str | None = None, **kwargs):
        """
        Tool decorator with simple registration.

        Usage:
            @mcp.tool
            def hello(name: str) -> str:
                return f"Hello, {name}!"

            @mcp.tool(tags=["custom"])
            def advanced_tool(data: dict) -> dict:
                return {"processed": data}
        """

        def decorator(func: Callable) -> Callable:
            # Simple tool creation
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or f"Execute {tool_name}"

            # Create tool handler from function
            tool_handler = ToolHandler.from_function(func, name=tool_name, description=tool_description)

            # Register in protocol handler (for MCP functionality)
            self.protocol.register_tool(tool_handler)

            # Simple metadata for registry
            metadata = {"function_name": func.__name__, "parameter_count": len(tool_handler.parameters)}

            # Simple tags
            tags = ["tool"]
            if "tags" in kwargs:
                tags.extend(kwargs.pop("tags"))

            # Register in MCP registry
            mcp_registry.register_tool(tool_handler.name, tool_handler, metadata=metadata, tags=tags, **kwargs)

            # Add tool metadata to function
            func._mcp_tool = tool_handler

            logger.debug(f"Registered tool: {tool_handler.name}")
            return func

        # Handle both @mcp.tool and @mcp.tool() usage
        if callable(name):
            func = name
            name = None
            return decorator(func)
        else:
            return decorator

    def resource(
        self, uri: str, name: str | None = None, description: str | None = None, mime_type: str | None = None, **kwargs
    ):
        """
        Resource decorator with simple registration.

        Usage:
            @mcp.resource("config://settings")
            def get_settings() -> dict:
                return {"app": "my_app"}
        """

        def decorator(func: Callable) -> Callable:
            # Simple resource creation
            resource_name = name or func.__name__.replace("_", " ").title()
            resource_description = description or func.__doc__ or f"Resource: {uri}"
            resource_mime_type = mime_type or "application/json"  # Simple default

            # Create resource handler from function
            resource_handler = ResourceHandler.from_function(
                uri=uri, func=func, name=resource_name, description=resource_description, mime_type=resource_mime_type
            )

            # Register in protocol handler (for MCP functionality)
            self.protocol.register_resource(resource_handler)

            # Simple metadata for registry
            metadata = {
                "function_name": func.__name__,
                "mime_type": resource_mime_type,
                "uri_scheme": uri.split("://")[0] if "://" in uri else "unknown",
            }

            # Simple tags
            tags = ["resource"]
            if "tags" in kwargs:
                tags.extend(kwargs.pop("tags"))

            # Register in MCP registry
            mcp_registry.register_resource(
                resource_handler.uri, resource_handler, metadata=metadata, tags=tags, **kwargs
            )

            # Add resource metadata to function
            func._mcp_resource = resource_handler

            logger.debug(f"Registered resource: {resource_handler.uri}")
            return func

        return decorator

    def prompt(self, name: str | None = None, description: str | None = None, **kwargs):
        """
        Prompt decorator with simple registration.

        Usage:
            @mcp.prompt
            def code_review(code: str, language: str = "python") -> str:
                return f"Please review this {language} code:\\n\\n{code}"

            @mcp.prompt(name="custom_prompt", description="Custom prompt template")
            def my_prompt(topic: str, style: str = "formal") -> str:
                return f"Write about {topic} in a {style} style"
        """

        def decorator(func: Callable) -> Callable:
            # Simple prompt creation
            prompt_name = name or func.__name__
            prompt_description = description or func.__doc__ or f"Prompt: {prompt_name}"

            # Create prompt handler from function
            prompt_handler = PromptHandler.from_function(func, name=prompt_name, description=prompt_description)

            # Register in protocol handler (for MCP functionality)
            self.protocol.register_prompt(prompt_handler)

            # Simple metadata for registry
            metadata = {"function_name": func.__name__, "parameter_count": len(prompt_handler.parameters)}

            # Simple tags
            tags = ["prompt"]
            if "tags" in kwargs:
                tags.extend(kwargs.pop("tags"))

            # Register in MCP registry
            mcp_registry.register_prompt(prompt_handler.name, prompt_handler, metadata=metadata, tags=tags, **kwargs)

            # Add prompt metadata to function
            func._mcp_prompt = prompt_handler

            logger.debug(f"Registered prompt: {prompt_handler.name}")
            return func

        # Handle both @mcp.prompt and @mcp.prompt() usage
        if callable(name):
            func = name
            name = None
            return decorator(func)
        else:
            return decorator

    # ============================================================================
    # HTTP Endpoint Registration
    # ============================================================================

    def endpoint(self, path: str, methods: list[str] = None, **kwargs):
        """
        Decorator to register a custom HTTP endpoint.

        Usage:
            @mcp.endpoint("/api/data", methods=["GET", "POST"])
            async def data_handler(request):
                return Response('{"data": "example"}')
        """

        def decorator(handler: Callable):
            http_endpoint_registry.register_endpoint(path, handler, methods=methods, **kwargs)
            logger.debug(f"Registered endpoint: {path}")
            return handler

        return decorator

    # ============================================================================
    # Manual Registration Methods
    # ============================================================================

    def add_tool(self, tool_handler: ToolHandler, **kwargs):
        """Manually add an MCP tool handler."""
        self.protocol.register_tool(tool_handler)
        mcp_registry.register_tool(tool_handler.name, tool_handler, **kwargs)
        logger.debug(f"Added tool: {tool_handler.name}")

    def add_resource(self, resource_handler: ResourceHandler, **kwargs):
        """Manually add an MCP resource handler."""
        self.protocol.register_resource(resource_handler)
        mcp_registry.register_resource(resource_handler.uri, resource_handler, **kwargs)
        logger.debug(f"Added resource: {resource_handler.uri}")

    def add_prompt(self, prompt_handler: PromptHandler, **kwargs):
        """Manually add an MCP prompt handler."""
        self.protocol.register_prompt(prompt_handler)
        mcp_registry.register_prompt(prompt_handler.name, prompt_handler, **kwargs)
        logger.debug(f"Added prompt: {prompt_handler.name}")

    def add_endpoint(self, path: str, handler: Callable, methods: list[str] = None, **kwargs):
        """Manually add a custom HTTP endpoint."""
        http_endpoint_registry.register_endpoint(path, handler, methods=methods, **kwargs)
        logger.debug(f"Added endpoint: {path}")

    def register_function_as_tool(
        self, func: Callable, name: str | None = None, description: str | None = None, **kwargs
    ):
        """Register an existing function as an MCP tool."""
        tool_handler = ToolHandler.from_function(func, name=name, description=description)
        self.add_tool(tool_handler, **kwargs)
        return tool_handler

    def register_function_as_resource(
        self,
        func: Callable,
        uri: str,
        name: str | None = None,
        description: str | None = None,
        mime_type: str = "text/plain",
        **kwargs,
    ):
        """Register an existing function as an MCP resource."""
        resource_handler = ResourceHandler.from_function(
            uri=uri, func=func, name=name, description=description, mime_type=mime_type
        )
        self.add_resource(resource_handler, **kwargs)
        return resource_handler

    def register_function_as_prompt(
        self, func: Callable, name: str | None = None, description: str | None = None, **kwargs
    ):
        """Register an existing function as an MCP prompt."""
        prompt_handler = PromptHandler.from_function(func, name=name, description=description)
        self.add_prompt(prompt_handler, **kwargs)
        return prompt_handler

    # ============================================================================
    # Component Search and Discovery
    # ============================================================================

    def search_tools_by_tag(self, tag: str) -> list[ToolHandler]:
        """Search tools by tag."""
        configs = mcp_registry.search_by_tag(tag)
        return [config.component for config in configs if config.component_type.value == "tool"]

    def search_resources_by_tag(self, tag: str) -> list[ResourceHandler]:
        """Search resources by tag."""
        configs = mcp_registry.search_by_tag(tag)
        return [config.component for config in configs if config.component_type.value == "resource"]

    def search_prompts_by_tag(self, tag: str) -> list[PromptHandler]:
        """Search prompts by tag."""
        configs = mcp_registry.search_by_tag(tag)
        return [config.component for config in configs if config.component_type.value == "prompt"]

    def search_components_by_tags(self, tags: list[str], match_all: bool = False):
        """Search components by multiple tags."""
        return mcp_registry.search_by_tags(tags, match_all=match_all)

    # ============================================================================
    # Information and Introspection
    # ============================================================================

    def get_tools(self) -> list[ToolHandler]:
        """Get all registered MCP tool handlers."""
        return list(self.protocol.tools.values())

    def get_resources(self) -> list[ResourceHandler]:
        """Get all registered MCP resource handlers."""
        return list(self.protocol.resources.values())

    def get_prompts(self) -> list[PromptHandler]:
        """Get all registered MCP prompt handlers."""
        return list(self.protocol.prompts.values())

    def get_endpoints(self) -> list[dict[str, Any]]:
        """Get all registered custom HTTP endpoints."""
        return [
            {
                "path": config.path,
                "name": config.name,
                "methods": config.methods,
                "description": config.description,
                "registered_at": config.registered_at,
            }
            for config in http_endpoint_registry.list_endpoints()
        ]

    def get_component_info(self, name: str) -> dict[str, Any] | None:
        """Get detailed information about an MCP component."""
        return mcp_registry.get_component_info(name)

    def info(self) -> dict[str, Any]:
        """Get comprehensive server information using modular smart config."""
        # Get comprehensive smart config summary
        smart_summary = self.smart_config.get_summary()

        return {
            "server": self.server_info.model_dump(exclude_none=True),
            "capabilities": self.capabilities.model_dump(exclude_none=True),
            "smart_config": smart_summary["full_config"],
            "smart_detection_summary": smart_summary["detection_summary"],
            "mcp_components": {
                "tools": {"count": len(self.protocol.tools), "names": list(self.protocol.tools.keys())},
                "resources": {"count": len(self.protocol.resources), "uris": list(self.protocol.resources.keys())},
                "prompts": {"count": len(self.protocol.prompts), "names": list(self.protocol.prompts.keys())},
                "stats": mcp_registry.get_stats(),
            },
            "http_endpoints": {
                "count": len(http_endpoint_registry.list_endpoints()),
                "custom": self.get_endpoints(),
                "stats": http_endpoint_registry.get_stats(),
            },
        }

    # ============================================================================
    # Registry Management
    # ============================================================================

    def clear_tools(self):
        """Clear all registered tools."""
        self.protocol.tools.clear()
        mcp_registry.clear_type(mcp_registry.MCPComponentType.TOOL)
        logger.info("Cleared all tools")

    def clear_resources(self):
        """Clear all registered resources."""
        self.protocol.resources.clear()
        mcp_registry.clear_type(mcp_registry.MCPComponentType.RESOURCE)
        logger.info("Cleared all resources")

    def clear_prompts(self):
        """Clear all registered prompts."""
        self.protocol.prompts.clear()
        mcp_registry.clear_type(mcp_registry.MCPComponentType.PROMPT)
        logger.info("Cleared all prompts")

    def clear_endpoints(self):
        """Clear all custom HTTP endpoints."""
        http_endpoint_registry.clear_endpoints()
        logger.info("Cleared all custom endpoints")

    def clear_all(self):
        """Clear all registered components and endpoints."""
        self.clear_tools()
        self.clear_resources()
        self.clear_prompts()
        self.clear_endpoints()
        logger.info("Cleared all components and endpoints")

    # ============================================================================
    # Smart Server Management with Modular Configuration
    # ============================================================================

    def run(
        self, host: str | None = None, port: int | None = None, debug: bool | None = None, stdio: bool | None = None
    ):
        """
        Run the MCP server with modular smart defaults.

        Args:
            host: Host to bind to (uses smart default if None)
            port: Port to bind to (uses smart default if None)
            debug: Enable debug logging (uses smart default if None)
            stdio: Run in stdio mode instead of HTTP server (auto-detects if None)
        """
        # Use smart defaults if not overridden
        final_host = host or self.smart_host
        final_port = port or self.smart_port
        final_debug = debug if debug is not None else self.smart_debug

        # Auto-detect stdio mode if not explicitly set
        if stdio is None:
            # Only use stdio if explicitly requested via environment
            stdio = (
                self.smart_config.environment_detector.get_env_var("MCP_STDIO")
                or self.smart_config.environment_detector.get_env_var("USE_STDIO")
                or self.smart_config.environment_detector.get_env_var("MCP_TRANSPORT") == "stdio"
            )
            stdio = bool(stdio)

        if final_debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            # Use the smart log level from modular config
            log_level = getattr(logging, self.smart_log_level.upper(), logging.INFO)
            logging.basicConfig(level=log_level)

        # Check if stdio mode is requested
        if stdio:
            # Run in stdio mode
            from .stdio_transport import run_stdio_server

            logger.info("🔄 Running in stdio mode")
            run_stdio_server(self.protocol)
        else:
            # Create HTTP server
            if self._server is None:
                self._server = create_server(self.protocol)

            # Show startup information
            self._print_startup_info(final_host, final_port, final_debug)

            # Run the server
            try:
                self._server.run(host=final_host, port=final_port, debug=final_debug)
            except KeyboardInterrupt:
                logger.info("\n👋 Server shutting down gracefully...")
            except Exception as e:
                logger.error(f"❌ Server error: {e}")
                raise

    def _print_startup_info(self, host: str, port: int, debug: bool):
        """Print comprehensive startup information using modular config."""
        import sys

        # Use stderr if in stdio mode to keep stdout clean
        output = sys.stderr if self.smart_transport_mode == "stdio" else sys.stdout
        print("🚀 ChukMCPServer - Modular Smart Configuration", file=output)
        print("=" * 60, file=output)

        # Server information
        info = self.info()
        print(f"Server: {info['server']['name']}", file=output)
        print(f"Version: {info['server']['version']}", file=output)
        print("Framework: ChukMCPServer with Modular Zero Configuration", file=output)
        print(file=output)

        # Smart configuration summary from modular system
        detection_summary = info["smart_detection_summary"]
        print("🧠 Smart Detection Summary:", file=output)
        for key, value in detection_summary.items():
            print(f"   {key.replace('_', ' ').title()}: {value}", file=output)
        print(file=output)

        # MCP Components
        mcp_info = info["mcp_components"]
        print(f"🔧 MCP Tools: {mcp_info['tools']['count']}", file=output)
        for tool_name in mcp_info["tools"]["names"]:
            print(f"   - {tool_name}", file=output)
        print(file=output)

        print(f"📂 MCP Resources: {mcp_info['resources']['count']}", file=output)
        for resource_uri in mcp_info["resources"]["uris"]:
            print(f"   - {resource_uri}", file=output)
        print(file=output)

        print(f"💬 MCP Prompts: {mcp_info['prompts']['count']}", file=output)
        for prompt_name in mcp_info["prompts"]["names"]:
            print(f"   - {prompt_name}", file=output)
        print(file=output)

        # Connection information
        print("🌐 Server Information:", file=output)
        print(f"   URL: http://{host}:{port}", file=output)
        print(f"   MCP Endpoint: http://{host}:{port}/mcp", file=output)
        print(f"   Debug: {debug}", file=output)
        print(file=output)

        # Performance mode information
        print("⚡ Performance Configuration:", file=output)
        print(f"   Mode: {self.smart_performance_mode}", file=output)
        print(f"   Workers: {self.smart_workers}", file=output)
        print(f"   Max Connections: {self.smart_max_connections}", file=output)
        print(file=output)

        # Inspector compatibility
        print("🔍 MCP Inspector:", file=output)
        print(f"   URL: http://{host}:{port}/mcp", file=output)
        print("   Transport: Streamable HTTP", file=output)
        print("=" * 60, file=output)

    # ============================================================================
    # Configuration Management
    # ============================================================================

    def get_smart_config(self) -> dict[str, Any]:
        """Get the current smart configuration."""
        return self.smart_config.get_all_defaults()

    def get_smart_config_summary(self) -> dict[str, Any]:
        """Get a summary of smart configuration detection."""
        return self.smart_config.get_summary()

    def refresh_smart_config(self):
        """Refresh the smart configuration (clear cache and re-detect)."""
        self.smart_config.clear_cache()
        smart_defaults = self.smart_config.get_all_defaults()

        # Update stored values
        self.smart_environment = smart_defaults["environment"]
        self.smart_workers = smart_defaults["workers"]
        self.smart_max_connections = smart_defaults["max_connections"]
        self.smart_log_level = smart_defaults["log_level"]
        self.smart_performance_mode = smart_defaults["performance_mode"]
        self.smart_containerized = smart_defaults["containerized"]

        logger.info("🔄 Smart configuration refreshed")

    # ============================================================================
    # Context Manager Support
    # ============================================================================

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass


# ============================================================================
# Factory Functions
# ============================================================================


def create_mcp_server(name: str | None = None, **kwargs) -> ChukMCPServer:
    """Factory function to create a ChukMCP Server with modular zero config."""
    return ChukMCPServer(name=name, **kwargs)


def quick_server(name: str | None = None) -> ChukMCPServer:
    """Create a server with minimal configuration for quick prototyping."""
    return ChukMCPServer(name=name or "Quick Server", version="0.1.0")
