#!/usr/bin/env python3
"""Integration tests for end-to-end HTTP and protocol flows.

Tests the full stack from request to response through the protocol handler
with real tool/resource/prompt registrations.
"""

import pytest

from chuk_mcp_server.constants import McpMethod, McpTaskMethod
from chuk_mcp_server.context import clear_all
from chuk_mcp_server.protocol import MCPProtocolHandler
from chuk_mcp_server.types.base import ServerCapabilities, ServerInfo
from chuk_mcp_server.types.prompts import PromptHandler
from chuk_mcp_server.types.resources import ResourceHandler
from chuk_mcp_server.types.tools import ToolHandler


@pytest.fixture(autouse=True)
def cleanup():
    """Clear context before and after each test."""
    clear_all()
    yield
    clear_all()


@pytest.fixture
def full_server():
    """Create a fully-configured protocol handler with tools, resources, and prompts."""
    info = ServerInfo(name="integration-test", version="1.0.0")
    caps = ServerCapabilities()
    h = MCPProtocolHandler(info, caps, strict_init=True)

    # Register tools
    async def add(a: int = 0, b: int = 0) -> int:
        """Add two numbers."""
        return a + b

    async def greet(name: str = "world") -> str:
        """Greet someone."""
        return f"Hello, {name}!"

    async def failing_tool() -> str:
        """Always fails."""
        raise ValueError("something went wrong")

    h.tools["add"] = ToolHandler.from_function(add, name="add", description="Add two numbers")
    h.tools["greet"] = ToolHandler.from_function(greet, name="greet", description="Greet someone")
    h.tools["fail"] = ToolHandler.from_function(failing_tool, name="fail", description="Always fails")

    # Register resources
    async def get_config() -> dict:
        return {"theme": "dark", "version": "1.0"}

    resource = ResourceHandler.from_function("config://settings", get_config, name="Settings")
    h.resources["config://settings"] = resource

    # Register prompts
    async def code_review(code: str = "", language: str = "python") -> str:
        return f"Review this {language} code:\n{code}"

    prompt = PromptHandler.from_function(code_review, name="code_review", description="Code review prompt")
    h.prompts["code_review"] = prompt

    return h


async def initialize_session(handler):
    """Helper: perform the initialize handshake."""
    msg = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": McpMethod.INITIALIZE,
        "params": {
            "protocolVersion": "2025-11-25",
            "clientInfo": {"name": "test-client", "version": "1.0"},
            "capabilities": {"sampling": {}},
        },
    }
    response, session_id = await handler.handle_request(msg)
    assert "result" in response
    assert session_id is not None
    return session_id


class TestFullLifecycle:
    """Test complete MCP session lifecycle."""

    @pytest.mark.asyncio
    async def test_initialize_then_list_tools(self, full_server):
        """Initialize → list tools → verify registered tools."""
        session_id = await initialize_session(full_server)

        msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.TOOLS_LIST, "params": {}}
        response, _ = await full_server.handle_request(msg, session_id=session_id)

        assert "result" in response
        tools = response["result"]["tools"]
        tool_names = {t["name"] for t in tools}
        assert tool_names == {"add", "greet", "fail"}

    @pytest.mark.asyncio
    async def test_initialize_call_tool_verify_task(self, full_server):
        """Initialize → call tool → verify task was created."""
        session_id = await initialize_session(full_server)

        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.TOOLS_CALL,
            "params": {"name": "add", "arguments": {"a": 10, "b": 20}},
        }
        response, _ = await full_server.handle_request(msg, session_id=session_id)

        assert "result" in response
        assert "30" in response["result"]["content"][0]["text"]

        # Verify task was created and completed
        tasks_msg = {"jsonrpc": "2.0", "id": 2, "method": McpTaskMethod.TASKS_LIST, "params": {}}
        tasks_response, _ = await full_server.handle_request(tasks_msg, session_id=session_id)
        assert "result" in tasks_response
        tasks = tasks_response["result"]["tasks"]
        assert len(tasks) == 1
        assert tasks[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_initialize_list_resources(self, full_server):
        """Initialize → list resources."""
        session_id = await initialize_session(full_server)

        msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.RESOURCES_LIST, "params": {}}
        response, _ = await full_server.handle_request(msg, session_id=session_id)

        assert "result" in response
        resources = response["result"]["resources"]
        assert len(resources) == 1
        assert resources[0]["uri"] == "config://settings"

    @pytest.mark.asyncio
    async def test_initialize_list_prompts(self, full_server):
        """Initialize → list prompts."""
        session_id = await initialize_session(full_server)

        msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.PROMPTS_LIST, "params": {}}
        response, _ = await full_server.handle_request(msg, session_id=session_id)

        assert "result" in response
        prompts = response["result"]["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["name"] == "code_review"

    @pytest.mark.asyncio
    async def test_full_session_flow(self, full_server):
        """Full flow: init → list → call → task check → read resource → get prompt."""
        session_id = await initialize_session(full_server)

        # 1. List tools
        list_msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.TOOLS_LIST, "params": {}}
        response, _ = await full_server.handle_request(list_msg, session_id=session_id)
        assert len(response["result"]["tools"]) == 3

        # 2. Call a tool
        call_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": McpMethod.TOOLS_CALL,
            "params": {"name": "greet", "arguments": {"name": "Claude"}},
        }
        response, _ = await full_server.handle_request(call_msg, session_id=session_id)
        assert "Hello, Claude!" in response["result"]["content"][0]["text"]

        # 3. Read a resource
        read_msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": McpMethod.RESOURCES_READ,
            "params": {"uri": "config://settings"},
        }
        response, _ = await full_server.handle_request(read_msg, session_id=session_id)
        assert "result" in response

        # 4. Get a prompt
        prompt_msg = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": McpMethod.PROMPTS_GET,
            "params": {"name": "code_review", "arguments": {"code": "print('hi')", "language": "python"}},
        }
        response, _ = await full_server.handle_request(prompt_msg, session_id=session_id)
        assert "result" in response

        # 5. Verify tasks
        tasks_msg = {"jsonrpc": "2.0", "id": 5, "method": McpTaskMethod.TASKS_LIST, "params": {}}
        tasks_response, _ = await full_server.handle_request(tasks_msg, session_id=session_id)
        assert len(tasks_response["result"]["tasks"]) == 1  # Only tool calls create tasks


class TestStrictInitEnforcement:
    """Test strict_init=True with full server."""

    @pytest.mark.asyncio
    async def test_reject_before_init(self, full_server):
        """Requests with invalid session should be rejected in strict mode."""
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.TOOLS_LIST,
            "params": {},
        }
        response, _ = await full_server.handle_request(msg, session_id="invalid-session")
        assert "error" in response
        assert "not initialized" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_allow_after_init(self, full_server):
        """After initialization, same requests should work."""
        session_id = await initialize_session(full_server)

        msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.TOOLS_LIST, "params": {}}
        response, _ = await full_server.handle_request(msg, session_id=session_id)
        assert "result" in response


class TestErrorHandling:
    """Test error handling in integration context."""

    @pytest.mark.asyncio
    async def test_tool_error_creates_failed_task(self, full_server):
        """Failed tool should create a failed task entry."""
        session_id = await initialize_session(full_server)

        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.TOOLS_CALL,
            "params": {"name": "fail", "arguments": {}},
        }
        response, _ = await full_server.handle_request(msg, session_id=session_id)
        assert "error" in response

        # Task should exist and be failed
        tasks_msg = {"jsonrpc": "2.0", "id": 2, "method": McpTaskMethod.TASKS_LIST, "params": {}}
        tasks_response, _ = await full_server.handle_request(tasks_msg, session_id=session_id)
        tasks = tasks_response["result"]["tasks"]
        assert len(tasks) == 1
        assert tasks[0]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_nonexistent_tool(self, full_server):
        """Calling nonexistent tool should return error."""
        session_id = await initialize_session(full_server)

        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.TOOLS_CALL,
            "params": {"name": "nonexistent", "arguments": {}},
        }
        response, _ = await full_server.handle_request(msg, session_id=session_id)
        assert "error" in response

    @pytest.mark.asyncio
    async def test_nonexistent_resource(self, full_server):
        """Reading nonexistent resource should return error."""
        session_id = await initialize_session(full_server)

        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.RESOURCES_READ,
            "params": {"uri": "nonexistent://resource"},
        }
        response, _ = await full_server.handle_request(msg, session_id=session_id)
        assert "error" in response

    @pytest.mark.asyncio
    async def test_nonexistent_prompt(self, full_server):
        """Getting nonexistent prompt should return error."""
        session_id = await initialize_session(full_server)

        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.PROMPTS_GET,
            "params": {"name": "nonexistent"},
        }
        response, _ = await full_server.handle_request(msg, session_id=session_id)
        assert "error" in response

    @pytest.mark.asyncio
    async def test_unknown_method(self, full_server):
        """Unknown method should return method_not_found error."""
        session_id = await initialize_session(full_server)

        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "unknown/method",
            "params": {},
        }
        response, _ = await full_server.handle_request(msg, session_id=session_id)
        assert "error" in response
        assert response["error"]["code"] == -32601  # METHOD_NOT_FOUND


class TestMultipleSessions:
    """Test multiple concurrent sessions."""

    @pytest.mark.asyncio
    async def test_independent_sessions(self, full_server):
        """Two sessions should see the same tools but have independent tasks."""
        session1 = await initialize_session(full_server)
        session2 = await initialize_session(full_server)
        assert session1 != session2

        # Both should see the same tools
        for session_id in [session1, session2]:
            msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.TOOLS_LIST, "params": {}}
            response, _ = await full_server.handle_request(msg, session_id=session_id)
            assert len(response["result"]["tools"]) == 3

    @pytest.mark.asyncio
    async def test_ping_always_works(self, full_server):
        """Ping should work regardless of session state."""
        msg = {"jsonrpc": "2.0", "id": 1, "method": McpMethod.PING}

        # Without session
        response, _ = await full_server.handle_request(msg)
        assert "result" in response

        # With invalid session
        response, _ = await full_server.handle_request(msg, session_id="bad")
        assert "result" in response

        # With valid session
        session_id = await initialize_session(full_server)
        response, _ = await full_server.handle_request(msg, session_id=session_id)
        assert "result" in response
