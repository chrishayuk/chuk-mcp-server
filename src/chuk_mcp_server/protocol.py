#!/usr/bin/env python3
# src/chuk_mcp_server/protocol.py
"""
ChukMCPServer Protocol Handler - Core MCP protocol implementation with chuk_mcp
"""

import logging
import time
import uuid
from typing import Any

from .constants import (
    JSONRPC_KEY,
    JSONRPC_VERSION,
    KEY_CAPABILITIES,
    KEY_CLIENT_INFO,
    KEY_ERROR,
    KEY_ID,
    KEY_METHOD,
    KEY_PARAMS,
    KEY_PROTOCOL_VERSION,
    KEY_RESULT,
    KEY_SERVER_INFO,
    LOG_CRITICAL,
    LOG_DEBUG,
    LOG_ERROR,
    LOG_INFO,
    LOG_WARNING,
    MCP_DEFAULT_PROTOCOL_VERSION,
    PACKAGE_LOGGER,
    PARAM_EXTERNAL_ACCESS_TOKEN,
    PARAM_USER_ID,
    JsonRpcError,
    McpMethod,
)
from .types import (
    PromptHandler,
    ResourceHandler,
    ServerCapabilities,
    # Direct chuk_mcp types (no conversion needed)
    ServerInfo,
    # Framework handlers
    ToolHandler,
    format_content,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Session Management
# ============================================================================


class SessionManager:
    """Manage MCP sessions."""

    def __init__(self, max_sessions: int = 1000, cleanup_interval: int = 100):
        self.sessions: dict[str, dict[str, Any]] = {}
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        self._creation_count = 0

    def create_session(self, client_info: dict[str, Any], protocol_version: str) -> str:
        """Create a new session."""
        self._creation_count += 1

        # Periodic cleanup of expired sessions
        if self._creation_count % self.cleanup_interval == 0:
            self.cleanup_expired()

        # Evict oldest session if at capacity
        if len(self.sessions) >= self.max_sessions:
            oldest_sid = min(self.sessions, key=lambda sid: self.sessions[sid]["last_activity"])
            del self.sessions[oldest_sid]
            logger.debug(f"Evicted oldest session {oldest_sid[:8]}... (max_sessions reached)")

        session_id = str(uuid.uuid4()).replace("-", "")
        self.sessions[session_id] = {
            "id": session_id,
            "client_info": client_info,
            "protocol_version": protocol_version,
            "created_at": time.time(),
            "last_activity": time.time(),
        }
        logger.debug(f"Created session {session_id[:8]}... for {client_info.get('name', 'unknown')}")
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def update_activity(self, session_id: str) -> None:
        """Update session last activity."""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = time.time()

    def cleanup_expired(self, max_age: int = 3600) -> None:
        """Remove expired sessions."""
        now = time.time()
        expired = [sid for sid, session in self.sessions.items() if now - session["last_activity"] > max_age]
        for sid in expired:
            del self.sessions[sid]
            logger.debug(f"Cleaned up expired session {sid[:8]}...")


# ============================================================================
# Protocol Handler with chuk_mcp Integration
# ============================================================================


class MCPProtocolHandler:
    """Core MCP protocol handler powered by chuk_mcp."""

    def __init__(self, server_info: ServerInfo, capabilities: ServerCapabilities, oauth_provider_getter=None):
        # Use chuk_mcp types directly - no conversion needed
        self.server_info = server_info
        self.capabilities = capabilities
        self.session_manager = SessionManager()

        # Tool, resource, and prompt registries (now use handlers)
        self.tools: dict[str, ToolHandler] = {}
        self.resources: dict[str, ResourceHandler] = {}
        self.prompts: dict[str, PromptHandler] = {}

        # OAuth provider getter function (optional)
        self.oauth_provider_getter = oauth_provider_getter

        # Don't log during init to keep stdio mode clean
        logger.debug("MCP protocol handler initialized with chuk_mcp")

    def register_tool(self, tool: ToolHandler) -> None:
        """Register a tool handler."""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def register_resource(self, resource: ResourceHandler) -> None:
        """Register a resource handler."""
        self.resources[resource.uri] = resource
        logger.debug(f"Registered resource: {resource.uri}")

    def register_prompt(self, prompt: PromptHandler) -> None:
        """Register a prompt handler."""
        self.prompts[prompt.name] = prompt
        logger.debug(f"Registered prompt: {prompt.name}")

    def get_tools_list(self) -> list[dict[str, Any]]:
        """Get list of tools in MCP format."""
        tools_list = []

        for tool_handler in self.tools.values():
            tools_list.append(tool_handler.to_mcp_format())

        return tools_list

    def get_resources_list(self) -> list[dict[str, Any]]:
        """Get list of resources in MCP format."""
        resources_list = []

        for resource_handler in self.resources.values():
            resources_list.append(resource_handler.to_mcp_format())

        return resources_list

    def get_prompts_list(self) -> list[dict[str, Any]]:
        """Get list of prompts in MCP format."""
        prompts_list = []

        for prompt_handler in self.prompts.values():
            prompts_list.append(prompt_handler.to_mcp_format())

        return prompts_list

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics for monitoring.

        Note: Cache-related metrics are not yet instrumented and return None.
        """

        return {
            "tools": {
                "count": len(self.tools),
                "cache_hit_ratio": None,  # Not yet instrumented
            },
            "resources": {
                "count": len(self.resources),
                "cache_hit_ratio": None,  # Not yet instrumented
            },
            "prompts": {
                "count": len(self.prompts),
                "cache_hit_ratio": None,  # Not yet instrumented
            },
            "sessions": {"active": len(self.session_manager.sessions), "total": len(self.session_manager.sessions)},
            "cache": {
                "tools_cached": None,  # Not yet instrumented
                "resources_cached": None,  # Not yet instrumented
                "cache_age": None,  # Not yet instrumented
            },
            "status": "operational",
        }

    async def handle_request(
        self, message: dict[str, Any], session_id: str | None = None, oauth_token: str | None = None
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Handle an MCP request."""
        try:
            method = message.get(KEY_METHOD)
            params = message.get(KEY_PARAMS, {})
            msg_id = message.get(KEY_ID)

            logger.debug(f"Handling {method} (ID: {msg_id})")

            # Set session context for this request
            if session_id:
                from .context import set_session_id

                set_session_id(session_id)
                self.session_manager.update_activity(session_id)

            # Route to appropriate handler
            if method == McpMethod.INITIALIZE:
                return await self._handle_initialize(params, msg_id)
            elif method == McpMethod.INITIALIZED:
                logger.debug("✅ Initialized notification received")
                return None, None  # Notifications don't return responses
            elif method == McpMethod.PING:
                return await self._handle_ping(msg_id)
            elif method == McpMethod.TOOLS_LIST:
                return await self._handle_tools_list(msg_id)
            elif method == McpMethod.TOOLS_CALL:
                return await self._handle_tools_call(params, msg_id, oauth_token)
            elif method == McpMethod.RESOURCES_LIST:
                return await self._handle_resources_list(msg_id)
            elif method == McpMethod.RESOURCES_READ:
                return await self._handle_resources_read(params, msg_id)
            elif method == McpMethod.PROMPTS_LIST:
                return await self._handle_prompts_list(msg_id)
            elif method == McpMethod.PROMPTS_GET:
                return await self._handle_prompts_get(params, msg_id)
            elif method == McpMethod.LOGGING_SET_LEVEL:
                return await self._handle_logging_set_level(params, msg_id)
            else:
                return self._create_error_response(
                    msg_id, JsonRpcError.METHOD_NOT_FOUND, f"Method not found: {method}"
                ), None

        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return self._create_error_response(msg_id, JsonRpcError.INTERNAL_ERROR, f"Internal error: {str(e)}"), None

    async def _handle_initialize(self, params: dict[str, Any], msg_id: Any) -> tuple[dict[str, Any], str]:
        """Handle initialize request using chuk_mcp."""
        client_info = params.get(KEY_CLIENT_INFO, {})
        protocol_version = params.get(KEY_PROTOCOL_VERSION, MCP_DEFAULT_PROTOCOL_VERSION)

        # Create session
        session_id = self.session_manager.create_session(client_info, protocol_version)

        # Build response using chuk_mcp types directly
        result = {
            KEY_PROTOCOL_VERSION: protocol_version,
            KEY_SERVER_INFO: self.server_info.model_dump(exclude_none=True),
            KEY_CAPABILITIES: self.capabilities.model_dump(exclude_none=True),
        }

        response = {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: result}

        client_name = client_info.get("name", "unknown")
        logger.debug(f"🤝 Initialized session {session_id[:8]}... for {client_name} (v{protocol_version})")
        return response, session_id

    async def _handle_ping(self, msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle ping request."""
        return {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: {}}, None

    async def _handle_tools_list(self, msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle tools/list request."""
        tools_list = self.get_tools_list()
        result = {"tools": tools_list}

        response = {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: result}

        logger.debug(f"📋 Returning {len(tools_list)} tools")
        return response, None

    async def _handle_tools_call(
        self, params: dict[str, Any], msg_id: Any, oauth_token: str | None = None
    ) -> tuple[dict[str, Any], None]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            return self._create_error_response(msg_id, JsonRpcError.INVALID_PARAMS, f"Unknown tool: {tool_name}"), None

        try:
            tool_handler = self.tools[tool_name]

            # Check if tool requires OAuth authorization
            if tool_handler.requires_auth:
                # Tool requires auth - validate OAuth token
                if not oauth_token:
                    return self._create_error_response(
                        msg_id,
                        JsonRpcError.INTERNAL_ERROR,
                        f"Tool '{tool_name}' requires OAuth authorization. Please authenticate first.",
                    ), None

                if not self.oauth_provider_getter:
                    return self._create_error_response(
                        msg_id,
                        JsonRpcError.INTERNAL_ERROR,
                        f"Tool '{tool_name}' requires OAuth but OAuth is not configured on this server.",
                    ), None

                # Validate OAuth token and get external provider token
                try:
                    provider = self.oauth_provider_getter()
                    if not provider:
                        return self._create_error_response(
                            msg_id, JsonRpcError.INTERNAL_ERROR, "OAuth provider not available."
                        ), None

                    token_data = await provider.validate_access_token(oauth_token)
                    logger.debug(f"📦 Token data received for {tool_name}: {list(token_data.keys())}")
                    external_token = token_data.get("external_access_token")
                    user_id = token_data.get("user_id")

                    logger.debug(
                        f"🔑 Token data for {tool_name}: external_token={'present' if external_token else 'NONE'}, user_id={user_id}"
                    )

                    if not external_token:
                        return self._create_error_response(
                            msg_id,
                            JsonRpcError.INTERNAL_ERROR,
                            "OAuth token is valid but external provider token is missing.",
                        ), None

                    # Inject external provider token and user_id into arguments
                    arguments[PARAM_EXTERNAL_ACCESS_TOKEN] = external_token
                    logger.debug(f"✅ Injected OAuth token into {tool_name} arguments")
                    if user_id:
                        arguments[PARAM_USER_ID] = user_id

                        # Also set user_id in context for application code to access
                        # This allows apps to use get_current_user_id() instead of passing _user_id everywhere
                        from .context import set_user_id

                        set_user_id(user_id)

                    logger.debug(f"OAuth token validated for tool {tool_name}, user_id: {user_id}")

                except Exception as e:
                    # OAuth validation failed for a tool that requires it
                    logger.error(f"OAuth validation failed for {tool_name}: {e}")
                    return self._create_error_response(
                        msg_id, JsonRpcError.INTERNAL_ERROR, f"OAuth validation failed: {str(e)}"
                    ), None

            # Execute the tool
            result = await tool_handler.execute(arguments)

            # Format response content using chuk_mcp content formatting
            content = format_content(result)

            response = {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: {"content": content}}

            logger.debug(f"🔧 Executed tool {tool_name}")
            return response, None

        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            return self._create_error_response(
                msg_id, JsonRpcError.INTERNAL_ERROR, f"Tool execution error: {str(e)}"
            ), None

    async def _handle_resources_list(self, msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle resources/list request."""
        resources_list = self.get_resources_list()
        result = {"resources": resources_list}

        response = {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: result}

        logger.debug(f"📂 Returning {len(resources_list)} resources")
        return response, None

    async def _handle_resources_read(self, params: dict[str, Any], msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle resources/read request."""
        uri = params.get("uri")

        if uri not in self.resources:
            return self._create_error_response(msg_id, JsonRpcError.INVALID_PARAMS, f"Unknown resource: {uri}"), None

        try:
            resource_handler = self.resources[uri]
            content = await resource_handler.read()

            # Build resource content response
            resource_content = {"uri": uri, "mimeType": resource_handler.mime_type, "text": content}

            response = {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: {"contents": [resource_content]}}

            logger.debug(f"📖 Read resource {uri}")
            return response, None

        except Exception as e:
            logger.error(f"Resource read error for {uri}: {e}")
            return self._create_error_response(
                msg_id, JsonRpcError.INTERNAL_ERROR, f"Resource read error: {str(e)}"
            ), None

    async def _handle_prompts_list(self, msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle prompts/list request."""
        prompts_list = self.get_prompts_list()
        result = {"prompts": prompts_list}

        response = {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: result}

        logger.info(f"💬 Returning {len(prompts_list)} prompts")
        return response, None

    async def _handle_prompts_get(self, params: dict[str, Any], msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle prompts/get request."""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})

        if prompt_name not in self.prompts:
            return self._create_error_response(
                msg_id, JsonRpcError.INVALID_PARAMS, f"Unknown prompt: {prompt_name}"
            ), None

        try:
            prompt_handler = self.prompts[prompt_name]
            result = await prompt_handler.get_prompt(arguments)

            # Format response content
            if isinstance(result, str):
                # If result is a string, wrap it as MCP content
                content = format_content(result)
            elif isinstance(result, dict):
                # If result is a dict, it should contain the prompt messages
                content = [result] if not isinstance(result.get("messages"), list) else result.get("messages", [])
            else:
                # Convert other types to string content
                content = format_content(str(result))

            # Ensure proper message format for MCP Inspector
            if isinstance(content, list) and len(content) > 0:
                # Convert content format to proper MCP message format
                messages = []
                for item in content:
                    if isinstance(item, dict):
                        if "role" in item and "content" in item:
                            # Already properly formatted
                            messages.append(item)
                        else:
                            # Convert content item to proper message format
                            messages.append({"role": "user", "content": item})
                    else:
                        # Convert string or other types to proper message format
                        messages.append({"role": "user", "content": {"type": "text", "text": str(item)}})
            else:
                # Fallback to properly formatted message structure
                messages = [{"role": "user", "content": {"type": "text", "text": str(result)}}]

            response = {
                JSONRPC_KEY: JSONRPC_VERSION,
                KEY_ID: msg_id,
                KEY_RESULT: {
                    "description": prompt_handler.description or f"Prompt: {prompt_name}",
                    "messages": messages,
                },
            }

            logger.debug(f"💬 Generated prompt {prompt_name}")
            logger.debug(f"🔍 DEBUG Response messages: {messages}")
            return response, None

        except Exception as e:
            logger.error(f"Prompt generation error for {prompt_name}: {e}")
            return self._create_error_response(
                msg_id, JsonRpcError.INTERNAL_ERROR, f"Prompt generation error: {str(e)}"
            ), None

    async def _handle_logging_set_level(self, params: dict[str, Any], msg_id: Any) -> tuple[dict[str, Any], None]:
        """Handle logging/setLevel request."""
        level = params.get("level", "INFO")

        # Map MCP logging levels to Python logging levels
        level_mapping = {
            LOG_DEBUG: logging.DEBUG,
            LOG_INFO: logging.INFO,
            LOG_WARNING: logging.WARNING,
            LOG_ERROR: logging.ERROR,
            LOG_CRITICAL: logging.CRITICAL,
        }

        level_lower = level.lower()
        if level_lower not in level_mapping:
            return self._create_error_response(
                msg_id,
                JsonRpcError.INVALID_PARAMS,
                f"Invalid logging level: {level}. Must be one of: debug, info, warning, error",
            ), None

        # Set the logging level for the chuk_mcp_server logger
        numeric_level = level_mapping[level_lower]
        logging.getLogger(PACKAGE_LOGGER).setLevel(numeric_level)

        # Also set the level for the root logger if needed
        if level_lower == LOG_DEBUG:
            logging.getLogger().setLevel(logging.DEBUG)

        logger.debug(f"Logging level set to {level.upper()}")

        response = {
            JSONRPC_KEY: JSONRPC_VERSION,
            KEY_ID: msg_id,
            KEY_RESULT: {"level": level.upper(), "message": f"Logging level set to {level.upper()}"},
        }

        return response, None

    def _create_error_response(self, msg_id: Any, code: int, message: str) -> dict[str, Any]:
        """Create error response."""
        return {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_ERROR: {"code": code, "message": message}}
