#!/usr/bin/env python3
"""Tests for the protocol module."""

from unittest.mock import AsyncMock, Mock

import pytest

from chuk_mcp_server.protocol import MCPProtocolHandler, SessionManager
from chuk_mcp_server.types import PromptHandler, ResourceHandler, ServerCapabilities, ServerInfo, ToolHandler


class TestSessionManager:
    """Test the SessionManager class."""

    def test_create_session(self):
        """Test creating a new session."""
        manager = SessionManager()
        client_info = {"name": "test-client", "version": "1.0"}
        protocol_version = "2025-06-18"

        session_id = manager.create_session(client_info, protocol_version)

        assert session_id is not None
        assert len(session_id) == 32  # UUID without hyphens
        assert session_id in manager.sessions

        session = manager.sessions[session_id]
        assert session["client_info"] == client_info
        assert session["protocol_version"] == protocol_version
        assert "created_at" in session
        assert "last_activity" in session

    def test_get_session(self):
        """Test getting an existing session."""
        manager = SessionManager()
        session_id = manager.create_session({"name": "test"}, "2025-06-18")

        session = manager.get_session(session_id)
        assert session is not None
        assert session["id"] == session_id

        # Non-existent session
        assert manager.get_session("invalid") is None

    def test_update_activity(self):
        """Test updating session activity."""
        manager = SessionManager()
        session_id = manager.create_session({"name": "test"}, "2025-06-18")

        original_activity = manager.sessions[session_id]["last_activity"]

        # Small delay to ensure time difference
        import time

        time.sleep(0.01)

        manager.update_activity(session_id)
        new_activity = manager.sessions[session_id]["last_activity"]

        assert new_activity > original_activity

        # Non-existent session should not error
        manager.update_activity("invalid")

    def test_cleanup_expired(self):
        """Test cleaning up expired sessions."""
        manager = SessionManager()

        # Create sessions with different ages
        session1 = manager.create_session({"name": "old"}, "2025-06-18")
        session2 = manager.create_session({"name": "new"}, "2025-06-18")

        # Make session1 old
        import time

        manager.sessions[session1]["last_activity"] = time.time() - 7200  # 2 hours old

        # Cleanup with 1 hour max age
        manager.cleanup_expired(max_age=3600)

        assert session1 not in manager.sessions
        assert session2 in manager.sessions


class TestMCPProtocolHandler:
    """Test the MCPProtocolHandler class."""

    def test_initialization(self):
        """Test protocol handler initialization."""
        server_info = ServerInfo(name="test-server", version="1.0.0")
        capabilities = ServerCapabilities(
            tools={"listChanged": False},
            resources={"subscribe": False, "listChanged": False},
            prompts={"listChanged": False},
        )

        handler = MCPProtocolHandler(server_info, capabilities)

        assert handler.server_info == server_info
        assert handler.capabilities == capabilities
        assert handler.session_manager is not None
        assert len(handler.tools) == 0
        assert len(handler.resources) == 0
        assert len(handler.prompts) == 0

    def test_register_tool(self):
        """Test registering a tool."""
        handler = self._create_handler()

        tool = Mock(spec=ToolHandler)
        tool.name = "test_tool"

        handler.register_tool(tool)

        assert "test_tool" in handler.tools
        assert handler.tools["test_tool"] == tool

    def test_register_resource(self):
        """Test registering a resource."""
        handler = self._create_handler()

        resource = Mock(spec=ResourceHandler)
        resource.uri = "test://resource"

        handler.register_resource(resource)

        assert "test://resource" in handler.resources
        assert handler.resources["test://resource"] == resource

    def test_register_prompt(self):
        """Test registering a prompt."""
        handler = self._create_handler()

        prompt = Mock(spec=PromptHandler)
        prompt.name = "test_prompt"

        handler.register_prompt(prompt)

        assert "test_prompt" in handler.prompts
        assert handler.prompts["test_prompt"] == prompt

    def test_get_tools_list(self):
        """Test getting tools list in MCP format."""
        handler = self._create_handler()

        tool1 = Mock(spec=ToolHandler)
        tool1.name = "tool1"
        tool1.to_mcp_format.return_value = {"name": "tool1", "description": "Tool 1"}

        tool2 = Mock(spec=ToolHandler)
        tool2.name = "tool2"
        tool2.to_mcp_format.return_value = {"name": "tool2", "description": "Tool 2"}

        handler.register_tool(tool1)
        handler.register_tool(tool2)

        tools_list = handler.get_tools_list()

        assert len(tools_list) == 2
        assert {"name": "tool1", "description": "Tool 1"} in tools_list
        assert {"name": "tool2", "description": "Tool 2"} in tools_list

    def test_get_resources_list(self):
        """Test getting resources list in MCP format."""
        handler = self._create_handler()

        resource = Mock(spec=ResourceHandler)
        resource.uri = "test://res"
        resource.to_mcp_format.return_value = {"uri": "test://res", "name": "Test Resource"}

        handler.register_resource(resource)

        resources_list = handler.get_resources_list()

        assert len(resources_list) == 1
        assert resources_list[0] == {"uri": "test://res", "name": "Test Resource"}

    def test_get_prompts_list(self):
        """Test getting prompts list in MCP format."""
        handler = self._create_handler()

        prompt = Mock(spec=PromptHandler)
        prompt.name = "test_prompt"
        prompt.to_mcp_format.return_value = {"name": "test_prompt", "description": "Test Prompt"}

        handler.register_prompt(prompt)

        prompts_list = handler.get_prompts_list()

        assert len(prompts_list) == 1
        assert prompts_list[0] == {"name": "test_prompt", "description": "Test Prompt"}

    def test_get_performance_stats(self):
        """Test getting performance statistics."""
        handler = self._create_handler()

        # Add some items
        handler.register_tool(Mock(spec=ToolHandler, name="tool1"))
        handler.register_resource(Mock(spec=ResourceHandler, uri="res1"))
        handler.register_prompt(Mock(spec=PromptHandler, name="prompt1"))

        stats = handler.get_performance_stats()

        assert stats["tools"]["count"] == 1
        assert stats["resources"]["count"] == 1
        assert stats["prompts"]["count"] == 1
        assert stats["sessions"]["active"] == 0
        assert stats["status"] == "operational"

    @pytest.mark.asyncio
    async def test_handle_initialize(self):
        """Test handling initialize request."""
        handler = self._create_handler()

        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"clientInfo": {"name": "test-client"}, "protocolVersion": "2025-06-18"},
        }

        response, session_id = await handler.handle_request(message)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["protocolVersion"] == "2025-06-18"
        assert response["result"]["serverInfo"]["name"] == "test-server"
        assert session_id is not None

    @pytest.mark.asyncio
    async def test_handle_ping(self):
        """Test handling ping request."""
        handler = self._create_handler()

        message = {"jsonrpc": "2.0", "id": 2, "method": "ping"}

        response, session_id = await handler.handle_request(message)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert response["result"] == {}

    @pytest.mark.asyncio
    async def test_handle_tools_list(self):
        """Test handling tools/list request."""
        handler = self._create_handler()

        tool = Mock(spec=ToolHandler)
        tool.name = "test_tool"
        tool.to_mcp_format.return_value = {"name": "test_tool"}
        handler.register_tool(tool)

        message = {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}

        response, _ = await handler.handle_request(message)

        assert response is not None
        assert response["result"]["tools"] == [{"name": "test_tool"}]

    @pytest.mark.asyncio
    async def test_handle_tools_call(self):
        """Test handling tools/call request."""
        handler = self._create_handler()

        tool = AsyncMock(spec=ToolHandler)
        tool.name = "add"
        tool.requires_auth = False  # Tool does not require OAuth
        tool.execute.return_value = {"result": 5}
        handler.register_tool(tool)

        message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "add", "arguments": {"a": 2, "b": 3}},
        }

        response, _ = await handler.handle_request(message)

        assert response is not None
        assert "result" in response
        assert "content" in response["result"]
        tool.execute.assert_called_once_with({"a": 2, "b": 3})

    @pytest.mark.asyncio
    async def test_handle_tools_call_unknown_tool(self):
        """Test handling tools/call with unknown tool."""
        handler = self._create_handler()

        message = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "unknown_tool", "arguments": {}},
        }

        response, _ = await handler.handle_request(message)

        assert response is not None
        assert "error" in response
        assert "Unknown tool" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_resources_list(self):
        """Test handling resources/list request."""
        handler = self._create_handler()

        resource = Mock(spec=ResourceHandler)
        resource.uri = "test://res"
        resource.to_mcp_format.return_value = {"uri": "test://res"}
        handler.register_resource(resource)

        message = {"jsonrpc": "2.0", "id": 6, "method": "resources/list"}

        response, _ = await handler.handle_request(message)

        assert response is not None
        assert response["result"]["resources"] == [{"uri": "test://res"}]

    @pytest.mark.asyncio
    async def test_handle_resources_read(self):
        """Test handling resources/read request."""
        handler = self._create_handler()

        resource = AsyncMock(spec=ResourceHandler)
        resource.uri = "test://res"
        resource.mime_type = "text/plain"
        resource.read.return_value = "Resource content"
        handler.register_resource(resource)

        message = {"jsonrpc": "2.0", "id": 7, "method": "resources/read", "params": {"uri": "test://res"}}

        response, _ = await handler.handle_request(message)

        assert response is not None
        assert "result" in response
        assert "contents" in response["result"]
        assert response["result"]["contents"][0]["uri"] == "test://res"
        assert response["result"]["contents"][0]["text"] == "Resource content"

    @pytest.mark.asyncio
    async def test_handle_prompts_list(self):
        """Test handling prompts/list request."""
        handler = self._create_handler()

        prompt = Mock(spec=PromptHandler)
        prompt.name = "test_prompt"
        prompt.to_mcp_format.return_value = {"name": "test_prompt"}
        handler.register_prompt(prompt)

        message = {"jsonrpc": "2.0", "id": 8, "method": "prompts/list"}

        response, _ = await handler.handle_request(message)

        assert response is not None
        assert response["result"]["prompts"] == [{"name": "test_prompt"}]

    @pytest.mark.asyncio
    async def test_handle_prompts_get(self):
        """Test handling prompts/get request."""
        handler = self._create_handler()

        prompt = AsyncMock(spec=PromptHandler)
        prompt.name = "greeting"
        prompt.description = "Greeting prompt"
        prompt.get_prompt.return_value = "Hello, World!"
        handler.register_prompt(prompt)

        message = {"jsonrpc": "2.0", "id": 9, "method": "prompts/get", "params": {"name": "greeting", "arguments": {}}}

        response, _ = await handler.handle_request(message)

        assert response is not None
        assert "result" in response
        assert response["result"]["description"] == "Greeting prompt"
        assert "messages" in response["result"]

    @pytest.mark.asyncio
    async def test_handle_unknown_method(self):
        """Test handling unknown method."""
        handler = self._create_handler()

        message = {"jsonrpc": "2.0", "id": 10, "method": "unknown/method"}

        response, _ = await handler.handle_request(message)

        assert response is not None
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_notification(self):
        """Test handling notification (no ID)."""
        handler = self._create_handler()

        message = {"jsonrpc": "2.0", "method": "notifications/initialized"}

        response, _ = await handler.handle_request(message)

        assert response is None

    @pytest.mark.asyncio
    async def test_handle_request_with_session(self):
        """Test that session activity is updated."""
        handler = self._create_handler()

        # Create a session first
        session_id = handler.session_manager.create_session({"name": "test"}, "2025-06-18")
        original_activity = handler.session_manager.sessions[session_id]["last_activity"]

        import time

        time.sleep(0.01)

        message = {"jsonrpc": "2.0", "id": 11, "method": "ping"}

        await handler.handle_request(message, session_id=session_id)

        new_activity = handler.session_manager.sessions[session_id]["last_activity"]
        assert new_activity > original_activity

    @pytest.mark.asyncio
    async def test_handle_request_error_handling(self):
        """Test error handling in request processing."""
        handler = self._create_handler()

        # Register a tool that will raise an error
        tool = AsyncMock(spec=ToolHandler)
        tool.name = "error_tool"
        tool.requires_auth = False  # Tool does not require OAuth
        tool.execute.side_effect = Exception("Tool execution failed")
        handler.register_tool(tool)

        message = {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "error_tool", "arguments": {}},
        }

        response, _ = await handler.handle_request(message)

        assert response is not None
        assert "error" in response
        assert "Tool execution error" in response["error"]["message"]

    def test_create_error_response(self):
        """Test creating error response."""
        handler = self._create_handler()

        error_response = handler._create_error_response(123, -32600, "Invalid request")

        assert error_response["jsonrpc"] == "2.0"
        assert error_response["id"] == 123
        assert error_response["error"]["code"] == -32600
        assert error_response["error"]["message"] == "Invalid request"

    def _create_handler(self):
        """Helper to create a handler instance."""
        server_info = ServerInfo(name="test-server", version="1.0.0")
        capabilities = ServerCapabilities(
            tools={"listChanged": False},
            resources={"subscribe": False, "listChanged": False},
            prompts={"listChanged": False},
        )
        return MCPProtocolHandler(server_info, capabilities)
