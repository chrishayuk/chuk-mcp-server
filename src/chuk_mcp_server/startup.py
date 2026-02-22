#!/usr/bin/env python3
# src/chuk_mcp_server/startup.py
"""
Server startup utilities: banner printing and global function registration.
"""

import logging
import sys
from collections.abc import Callable
from typing import Any

from .decorators import (
    clear_global_registry,
    get_global_prompts,
    get_global_resource_templates,
    get_global_resources,
    get_global_tools,
)
from .mcp_registry import mcp_registry

logger = logging.getLogger(__name__)


def print_smart_config(
    smart_environment: str,
    smart_host: str,
    smart_port: int,
    smart_workers: int,
    smart_max_connections: int,
    smart_containerized: bool,
    smart_performance_mode: str,
    smart_log_level: str,
    actual_log_level: str | None = None,
) -> None:
    """Print smart configuration summary using modular config."""
    output = sys.stderr
    log_level_display = actual_log_level or smart_log_level
    print("🧠 ChukMCPServer - Modular Zero Configuration Mode", file=output)
    print("=" * 60, file=output)
    print(f"📊 Environment: {smart_environment}", file=output)
    print(f"🌐 Network: {smart_host}:{smart_port}", file=output)
    print(f"🔧 Workers: {smart_workers}", file=output)
    print(f"🔗 Max Connections: {smart_max_connections}", file=output)
    print(f"🐳 Container: {smart_containerized}", file=output)
    print(f"⚡ Performance Mode: {smart_performance_mode}", file=output)
    print(f"📝 Log Level: {log_level_display}", file=output)
    print("=" * 60, file=output)


def print_startup_info(
    host: str,
    port: int,
    debug: bool,
    info_fn: Callable[[], dict[str, Any]],
    smart_performance_mode: str,
    smart_workers: int,
    smart_max_connections: int,
    smart_transport_mode: str,
    actual_log_level: str | None = None,
) -> None:
    """Print comprehensive startup information using modular config."""
    # Use stderr if in stdio mode to keep stdout clean
    output = sys.stderr if smart_transport_mode == "stdio" else sys.stdout
    print("🚀 ChukMCPServer - Modular Smart Configuration", file=output)
    print("=" * 60, file=output)

    # Server information
    info = info_fn()
    print(f"Server: {info['server']['name']}", file=output)
    print(f"Version: {info['server']['version']}", file=output)
    print("Framework: ChukMCPServer with Modular Zero Configuration", file=output)
    print(file=output)

    # Smart configuration summary from modular system (with actual log level override)
    detection_summary = info["smart_detection_summary"].copy()
    if actual_log_level:
        detection_summary["logging"] = f"{actual_log_level} level, debug={debug}"
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
    print(f"   Mode: {smart_performance_mode}", file=output)
    print(f"   Workers: {smart_workers}", file=output)
    print(f"   Max Connections: {smart_max_connections}", file=output)
    print(file=output)

    # Inspector compatibility
    print("🔍 MCP Inspector:", file=output)
    print(f"   URL: http://{host}:{port}/mcp", file=output)
    print("   Transport: Streamable HTTP", file=output)
    print("=" * 60, file=output)


def register_global_functions(protocol: Any) -> None:
    """Register globally decorated functions in both protocol and registries."""
    for tool_handler in get_global_tools():
        protocol.register_tool(tool_handler)
        mcp_registry.register_tool(tool_handler.name, tool_handler)

    for resource_handler in get_global_resources():
        protocol.register_resource(resource_handler)
        mcp_registry.register_resource(resource_handler.uri, resource_handler)

    for prompt_handler in get_global_prompts():
        protocol.register_prompt(prompt_handler)
        mcp_registry.register_prompt(prompt_handler.name, prompt_handler)

    for template_handler in get_global_resource_templates():
        protocol.register_resource_template(template_handler)

    # Clear global registry to avoid duplicate registrations
    clear_global_registry()
