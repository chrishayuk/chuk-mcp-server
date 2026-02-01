#!/usr/bin/env python3
"""
Top-level constants shared across the chuk_mcp_server package.
"""

from enum import IntEnum

# ---------------------------------------------------------------------------
# JSON-RPC
# ---------------------------------------------------------------------------
JSONRPC_VERSION = "2.0"
JSONRPC_KEY = "jsonrpc"

# JSON-RPC message keys
KEY_METHOD = "method"
KEY_PARAMS = "params"
KEY_ID = "id"
KEY_RESULT = "result"
KEY_ERROR = "error"


class JsonRpcError(IntEnum):
    """Standard JSON-RPC 2.0 error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


# ---------------------------------------------------------------------------
# MCP protocol
# ---------------------------------------------------------------------------
MCP_PROTOCOL_VERSION_2025_06 = "2025-06-18"
MCP_PROTOCOL_VERSION_2025_03 = "2025-03-26"
MCP_DEFAULT_PROTOCOL_VERSION = MCP_PROTOCOL_VERSION_2025_06


# MCP method names
class McpMethod:
    INITIALIZE = "initialize"
    INITIALIZED = "notifications/initialized"
    PING = "ping"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    LOGGING_SET_LEVEL = "logging/setLevel"


# MCP initialize parameter keys
KEY_CLIENT_INFO = "clientInfo"
KEY_PROTOCOL_VERSION = "protocolVersion"
KEY_SERVER_INFO = "serverInfo"
KEY_CAPABILITIES = "capabilities"


# ---------------------------------------------------------------------------
# MCP metadata attributes (set by decorators, read by core)
# ---------------------------------------------------------------------------
ATTR_MCP_TOOL = "_mcp_tool"
ATTR_MCP_RESOURCE = "_mcp_resource"
ATTR_MCP_PROMPT = "_mcp_prompt"
ATTR_REQUIRES_AUTH = "_requires_auth"
ATTR_AUTH_SCOPES = "_auth_scopes"

# OAuth injection parameter names
PARAM_EXTERNAL_ACCESS_TOKEN = "_external_access_token"
PARAM_USER_ID = "_user_id"


# ---------------------------------------------------------------------------
# Component types
# ---------------------------------------------------------------------------
COMPONENT_TOOL = "tool"
COMPONENT_RESOURCE = "resource"
COMPONENT_PROMPT = "prompt"
DEFAULT_COMPONENT_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Content types
# ---------------------------------------------------------------------------
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_PLAIN = "text/plain"
CONTENT_TYPE_MARKDOWN = "text/markdown"
CONTENT_TYPE_SSE = "text/event-stream"


# ---------------------------------------------------------------------------
# Common HTTP headers
# ---------------------------------------------------------------------------
HEADER_CORS_ORIGIN = "Access-Control-Allow-Origin"
HEADER_CORS_METHODS = "Access-Control-Allow-Methods"
HEADER_CORS_HEADERS = "Access-Control-Allow-Headers"
HEADER_CORS_MAX_AGE = "Access-Control-Max-Age"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_MCP_SESSION_ID = "Mcp-Session-Id"
CORS_ALLOW_ALL = "*"


# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------
ENV_MCP_LOG_LEVEL = "MCP_LOG_LEVEL"
ENV_MCP_TRANSPORT = "MCP_TRANSPORT"
ENV_MCP_STDIO = "MCP_STDIO"
ENV_USE_STDIO = "USE_STDIO"
ENV_MCP_SERVER_NAME = "MCP_SERVER_NAME"
ENV_MCP_SERVER_VERSION = "MCP_SERVER_VERSION"
ENV_PORT = "PORT"


# ---------------------------------------------------------------------------
# Logging level strings
# ---------------------------------------------------------------------------
LOG_DEBUG = "debug"
LOG_INFO = "info"
LOG_WARNING = "warning"
LOG_ERROR = "error"
LOG_CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Network defaults
# ---------------------------------------------------------------------------
DEFAULT_HOST = "0.0.0.0"
DEFAULT_ENCODING = "utf-8"
DEFAULT_PORT = 8000


# ---------------------------------------------------------------------------
# Server identity
# ---------------------------------------------------------------------------
SERVER_NAME = "ChukMCPServer"
POWERED_BY = "chuk_mcp"
FRAMEWORK_DESCRIPTION = "ChukMCPServer with chuk_mcp"
PACKAGE_LOGGER = "chuk_mcp_server"
