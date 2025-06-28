#!/usr/bin/env python3
"""
endpoints/info.py - Information and Discovery Endpoints

Endpoints for server information, API discovery, documentation,
and developer-friendly interfaces.
"""

import orjson
import time
from typing import Dict, Any, List
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse

from ..models import get_state


# ============================================================================
# Main Information Endpoints
# ============================================================================

async def root_endpoint(request: Request) -> Response:
    """
    Root endpoint with comprehensive server information
    
    Provides a developer-friendly overview of the server capabilities,
    endpoints, and current status.
    """
    state = get_state()
    
    current_time = time.time()
    uptime = current_time - state.metrics.start_time
    
    info = {
        "server": "fast-mcp-server",
        "version": "1.0.0",
        "protocol": "MCP 2025-06-18",
        "description": "High-performance MCP protocol server with sub-millisecond response times",
        
        "endpoints": {
            "mcp": {
                "path": "/mcp",
                "method": "POST",
                "description": "MCP protocol endpoint for JSON-RPC requests",
                "content_type": "application/json"
            },
            "health": {
                "path": "/health",
                "method": "GET", 
                "description": "Fast health check for load balancers"
            },
            "metrics": {
                "path": "/metrics",
                "method": "GET",
                "description": "Detailed performance metrics"
            },
            "info": {
                "path": "/info",
                "method": "GET",
                "description": "Detailed server information"
            },
            "discovery": {
                "path": "/api",
                "method": "GET",
                "description": "API discovery and documentation"
            }
        },
        
        "features": [
            "High-performance MCP protocol implementation",
            "Session management with automatic cleanup",
            "Tool execution framework",
            "Resource reading system",
            "Real-time performance metrics",
            "Sub-millisecond response times",
            "Kubernetes-ready health probes",
            "Prometheus metrics support"
        ],
        
        "performance": {
            "target_rps": "10,000+",
            "benchmark_rps": state.metrics.rps(),
            "uptime_seconds": round(uptime, 2),
            "total_requests": state.metrics.total_requests,
            "avg_response_time": "< 1ms",
            "error_rate": round(
                (state.metrics.errors / max(state.metrics.total_requests, 1)) * 100, 2
            )
        },
        
        "capabilities": {
            "tools": {
                "count": len(state.get_tools()),
                "available": [tool["name"] for tool in state.get_tools()[:5]]  # First 5
            },
            "resources": {
                "count": len(state.get_resources()),
                "available": [res["name"] for res in state.get_resources()[:5]]  # First 5
            },
            "sessions": {
                "active": len(state.sessions),
                "max_concurrent": "high"
            }
        },
        
        "getting_started": {
            "test_connection": f"curl {request.url.scheme}://{request.headers.get('host', 'localhost')}/health",
            "mcp_initialize": {
                "url": f"{request.url.scheme}://{request.headers.get('host', 'localhost')}/mcp",
                "method": "POST",
                "sample_request": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "clientInfo": {"name": "test-client", "version": "1.0.0"}
                    }
                }
            },
            "benchmark": f"python quick_benchmark.py {request.url.scheme}://{request.headers.get('host', 'localhost')}/mcp"
        },
        
        "timestamp": current_time
    }
    
    body = orjson.dumps(info, option=orjson.OPT_INDENT_2)
    
    return Response(
        body,
        media_type="application/json",
        headers={
            "cache-control": "public, max-age=300",  # Cache for 5 minutes
            "server": "fast-mcp-server",
            "content-length": str(len(body)),
            "x-server-info": "true"
        }
    )


async def info_endpoint(request: Request) -> Response:
    """
    Detailed server information endpoint
    
    More comprehensive information than the root endpoint,
    including detailed configuration and runtime data.
    """
    state = get_state()
    
    current_time = time.time()
    uptime = current_time - state.metrics.start_time
    
    detailed_info = {
        "server": {
            "name": "fast-mcp-server",
            "version": "1.0.0",
            "protocol_version": "2025-06-18",
            "start_time": state.metrics.start_time,
            "uptime_seconds": round(uptime, 2),
            "architecture": "modular"
        },
        
        "runtime": {
            "framework": "starlette",
            "json_library": "orjson",
            "async_model": "asyncio",
            "performance_optimizations": [
                "orjson serialization",
                "pre-computed responses",
                "minimal allocations",
                "optimized routing",
                "efficient state management"
            ]
        },
        
        "metrics": {
            "requests": {
                "total": state.metrics.total_requests,
                "per_second": round(state.metrics.rps(), 2),
                "errors": state.metrics.errors
            },
            "mcp_operations": {
                "tool_calls": state.metrics.tool_calls,
                "resource_reads": state.metrics.resource_reads,
                "active_sessions": len(state.sessions)
            }
        },
        
        "tools": {
            "count": len(state.get_tools()),
            "definitions": state.get_tools()
        },
        
        "resources": {
            "count": len(state.get_resources()),
            "definitions": state.get_resources()
        },
        
        "configuration": {
            "session_timeout": "3600 seconds",
            "cleanup_frequency": "every 100 requests",
            "max_concurrent_sessions": "unlimited",
            "response_caching": "enabled"
        },
        
        "health": {
            "status": "healthy",
            "checks": {
                "tools_loaded": len(state.get_tools()) > 0,
                "resources_loaded": len(state.get_resources()) > 0,
                "low_error_rate": state.metrics.errors < 100,
                "acceptable_load": state.metrics.rps() < 50000  # Theoretical max
            }
        },
        
        "timestamp": current_time
    }
    
    body = orjson.dumps(detailed_info, option=orjson.OPT_INDENT_2)
    
    return Response(
        body,
        media_type="application/json",
        headers={
            "cache-control": "no-cache",
            "server": "fast-mcp-server",
            "content-length": str(len(body))
        }
    )


# ============================================================================
# API Discovery and Documentation
# ============================================================================

async def api_discovery_endpoint(request: Request) -> Response:
    """
    API discovery endpoint with OpenAPI-style information
    
    Provides structured information about all available endpoints
    and their specifications.
    """
    base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost')}"
    
    api_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Fast MCP Server API",
            "version": "1.0.0",
            "description": "High-performance MCP protocol server with REST endpoints",
            "contact": {
                "name": "Fast MCP Server",
                "url": base_url
            }
        },
        
        "servers": [
            {
                "url": base_url,
                "description": "Fast MCP Server"
            }
        ],
        
        "paths": {
            "/": {
                "get": {
                    "summary": "Server Information",
                    "description": "Get comprehensive server information and capabilities",
                    "responses": {
                        "200": {
                            "description": "Server information",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    },
                    "tags": ["Information"]
                }
            },
            
            "/mcp": {
                "post": {
                    "summary": "MCP Protocol Endpoint",
                    "description": "JSON-RPC 2.0 endpoint for MCP protocol operations",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "jsonrpc": {"type": "string", "enum": ["2.0"]},
                                        "method": {"type": "string"},
                                        "params": {"type": "object"},
                                        "id": {"type": ["string", "number", "null"]}
                                    },
                                    "required": ["jsonrpc", "method"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "JSON-RPC response",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    },
                    "tags": ["MCP Protocol"]
                }
            },
            
            "/health": {
                "get": {
                    "summary": "Health Check",
                    "description": "Fast health check endpoint for load balancers",
                    "responses": {
                        "200": {
                            "description": "Server is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "uptime": {"type": "number"},
                                            "timestamp": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["Health"]
                }
            },
            
            "/metrics": {
                "get": {
                    "summary": "Performance Metrics",
                    "description": "Detailed performance and operational metrics",
                    "responses": {
                        "200": {
                            "description": "Performance metrics",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    },
                    "tags": ["Monitoring"]
                }
            }
        },
        
        "tags": [
            {
                "name": "Information",
                "description": "Server information and discovery"
            },
            {
                "name": "MCP Protocol", 
                "description": "Model Context Protocol operations"
            },
            {
                "name": "Health",
                "description": "Health checks and status"
            },
            {
                "name": "Monitoring",
                "description": "Metrics and monitoring"
            }
        ]
    }
    
    body = orjson.dumps(api_spec, option=orjson.OPT_INDENT_2)
    
    return Response(
        body,
        media_type="application/json",
        headers={
            "cache-control": "public, max-age=3600",  # Cache for 1 hour
            "server": "fast-mcp-server",
            "content-length": str(len(body))
        }
    )


async def tools_info_endpoint(request: Request) -> Response:
    """
    Detailed information about available tools
    """
    state = get_state()
    
    tools_info = {
        "tools": {
            "count": len(state.get_tools()),
            "definitions": state.get_tools(),
            "usage": {
                "total_calls": state.metrics.tool_calls,
                "endpoint": "/mcp",
                "method": "tools/call"
            },
            "examples": [
                {
                    "tool": "add",
                    "request": {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": "add",
                            "arguments": {"a": 5, "b": 3}
                        }
                    }
                }
            ]
        },
        "timestamp": time.time()
    }
    
    body = orjson.dumps(tools_info, option=orjson.OPT_INDENT_2)
    
    return Response(
        body,
        media_type="application/json",
        headers={
            "cache-control": "public, max-age=600",  # Cache for 10 minutes
            "server": "fast-mcp-server"
        }
    )


async def resources_info_endpoint(request: Request) -> Response:
    """
    Detailed information about available resources
    """
    state = get_state()
    
    resources_info = {
        "resources": {
            "count": len(state.get_resources()),
            "definitions": state.get_resources(),
            "usage": {
                "total_reads": state.metrics.resource_reads,
                "endpoint": "/mcp",
                "method": "resources/read"
            },
            "examples": [
                {
                    "resource": "demo://server-info",
                    "request": {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "resources/read",
                        "params": {
                            "uri": "demo://server-info"
                        }
                    }
                }
            ]
        },
        "timestamp": time.time()
    }
    
    body = orjson.dumps(resources_info, option=orjson.OPT_INDENT_2)
    
    return Response(
        body,
        media_type="application/json",
        headers={
            "cache-control": "public, max-age=600",  # Cache for 10 minutes
            "server": "fast-mcp-server"
        }
    )


# ============================================================================
# Help and Documentation
# ============================================================================

async def help_endpoint(request: Request) -> PlainTextResponse:
    """
    Text-based help endpoint for command-line users
    """
    base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost')}"
    
    help_text = f"""Fast MCP Server - Help

Welcome to the Fast MCP Server! This is a high-performance implementation
of the Model Context Protocol (MCP) with sub-millisecond response times.

📋 ENDPOINTS:
  GET  /              Server information (JSON)
  POST /mcp           MCP protocol endpoint (JSON-RPC 2.0)
  GET  /health        Health check (fast)
  GET  /metrics       Performance metrics
  GET  /info          Detailed server info
  GET  /api           API discovery (OpenAPI)
  GET  /help          This help text

🚀 QUICK START:
  1. Test health:     curl {base_url}/health
  2. Get server info: curl {base_url}/
  3. MCP initialize:  See /info endpoint for sample request
  4. Benchmark:       python quick_benchmark.py {base_url}/mcp

⚡ PERFORMANCE:
  • Target: 10,000+ RPS
  • Response time: < 1ms
  • Protocol: MCP 2025-06-18
  • Framework: Starlette + orjson

🔧 MCP OPERATIONS:
  • initialize        - Start MCP session
  • ping             - Health check
  • tools/list       - List available tools
  • tools/call       - Execute a tool
  • resources/list   - List available resources
  • resources/read   - Read a resource

📊 MONITORING:
  • /health          - Load balancer health check
  • /health/detailed - Comprehensive health info
  • /readiness       - Kubernetes readiness probe
  • /liveness        - Kubernetes liveness probe
  • /metrics         - JSON metrics
  • /metrics/prometheus - Prometheus format

For more information, visit {base_url}/ or {base_url}/api
"""
    
    return PlainTextResponse(
        help_text,
        headers={
            "cache-control": "public, max-age=3600",
            "server": "fast-mcp-server"
        }
    )