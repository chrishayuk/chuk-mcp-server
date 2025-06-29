#!/usr/bin/env python3
# chuk_mcp_server/endpoints/__init__.py
"""
Endpoints - Modular endpoint handlers

This module provides clean, focused endpoint handlers for different aspects
of the MCP server functionality:

- MCPEndpoint: Core MCP protocol handling with SSE support
- HealthEndpoint: Health checks and monitoring
- InfoEndpoint: Server information and documentation

Each endpoint is self-contained and follows single responsibility principle.
"""

from .mcp import MCPEndpoint
from .health import HealthEndpoint
from .info import InfoEndpoint

__all__ = [
    "MCPEndpoint",
    "HealthEndpoint", 
    "InfoEndpoint"
]

# Endpoint metadata for introspection
ENDPOINT_INFO = {
    "mcp": {
        "class": MCPEndpoint,
        "description": "Core MCP protocol endpoint with SSE support",
        "methods": ["GET", "POST", "OPTIONS"],
        "features": [
            "JSON-RPC protocol handling",
            "SSE streaming for Inspector",
            "Session management",
            "CORS support"
        ]
    },
    "health": {
        "class": HealthEndpoint,
        "description": "Health check and monitoring endpoint",
        "methods": ["GET"],
        "features": [
            "Server health status",
            "Capability information",
            "Session statistics",
            "Detailed diagnostics"
        ]
    },
    "info": {
        "class": InfoEndpoint,
        "description": "Server information and documentation endpoint",
        "methods": ["GET"],
        "features": [
            "Comprehensive server info",
            "Tool and resource details",
            "Usage examples",
            "Markdown documentation"
        ]
    }
}


def get_endpoint_info(endpoint_name: str = None):
    """Get information about available endpoints."""
    if endpoint_name:
        return ENDPOINT_INFO.get(endpoint_name)
    return ENDPOINT_INFO


def list_endpoints():
    """List all available endpoint names."""
    return list(ENDPOINT_INFO.keys())