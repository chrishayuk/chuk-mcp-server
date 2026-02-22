#!/usr/bin/env python3
"""Tests for automatic task creation during tool execution."""

import pytest

from chuk_mcp_server.constants import McpMethod
from chuk_mcp_server.protocol import MCPProtocolHandler
from chuk_mcp_server.types.base import ServerCapabilities, ServerInfo
from chuk_mcp_server.types.tools import ToolHandler


@pytest.fixture
def handler():
    """Create protocol handler with a simple tool."""
    info = ServerInfo(name="test", version="1.0")
    caps = ServerCapabilities()
    h = MCPProtocolHandler(info, caps)

    async def add_tool(a: int = 0, b: int = 0) -> int:
        return a + b

    h.tools["add"] = ToolHandler.from_function(add_tool, name="add", description="Add two numbers")
    return h


@pytest.fixture
def error_handler():
    """Create protocol handler with a tool that raises."""
    info = ServerInfo(name="test", version="1.0")
    caps = ServerCapabilities()
    h = MCPProtocolHandler(info, caps)

    async def failing_tool() -> str:
        raise ValueError("test failure")

    h.tools["fail"] = ToolHandler.from_function(failing_tool, name="fail", description="Always fails")
    return h


class TestTaskAutoWire:
    """Test that tool execution automatically creates and updates tasks."""

    @pytest.mark.asyncio
    async def test_successful_tool_creates_completed_task(self, handler):
        """Successful tool call should create a task and mark it completed."""
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.TOOLS_CALL,
            "params": {"name": "add", "arguments": {"a": 2, "b": 3}},
        }
        response, _ = await handler.handle_request(msg)
        assert "result" in response

        # Check that a task was created
        assert len(handler._task_store) == 1
        task = list(handler._task_store.values())[0]
        assert task["status"] == "completed"
        assert task["toolName"] == "add"
        assert task["result"] is not None

    @pytest.mark.asyncio
    async def test_failed_tool_creates_failed_task(self, error_handler):
        """Failed tool call should create a task and mark it failed."""
        msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.TOOLS_CALL,
            "params": {"name": "fail", "arguments": {}},
        }
        response, _ = await error_handler.handle_request(msg)
        assert "error" in response

        # Check that a task was created and marked failed
        assert len(error_handler._task_store) == 1
        task = list(error_handler._task_store.values())[0]
        assert task["status"] == "failed"
        assert task["toolName"] == "fail"
        assert task["error"] is not None
        assert "Error" in task["error"]["type"]

    @pytest.mark.asyncio
    async def test_task_has_request_id(self, handler):
        """Task should reference the original request ID."""
        msg = {
            "jsonrpc": "2.0",
            "id": 42,
            "method": McpMethod.TOOLS_CALL,
            "params": {"name": "add", "arguments": {"a": 1, "b": 1}},
        }
        await handler.handle_request(msg)

        task = list(handler._task_store.values())[0]
        assert task["requestId"] == 42

    @pytest.mark.asyncio
    async def test_multiple_calls_create_multiple_tasks(self, handler):
        """Each tool call should create its own task."""
        for i in range(3):
            msg = {
                "jsonrpc": "2.0",
                "id": i + 1,
                "method": McpMethod.TOOLS_CALL,
                "params": {"name": "add", "arguments": {"a": i, "b": i}},
            }
            await handler.handle_request(msg)

        assert len(handler._task_store) == 3
        for task in handler._task_store.values():
            assert task["status"] == "completed"

    @pytest.mark.asyncio
    async def test_tasks_list_returns_auto_created_tasks(self, handler):
        """tasks/list should return tasks created by tool calls."""
        # Execute a tool
        call_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": McpMethod.TOOLS_CALL,
            "params": {"name": "add", "arguments": {"a": 1, "b": 2}},
        }
        await handler.handle_request(call_msg)

        # List tasks
        list_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tasks/list",
            "params": {},
        }
        response, _ = await handler.handle_request(list_msg)
        assert "result" in response
        tasks = response["result"]["tasks"]
        assert len(tasks) == 1
        assert tasks[0]["status"] == "completed"
        assert tasks[0]["toolName"] == "add"
