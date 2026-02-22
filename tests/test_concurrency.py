#!/usr/bin/env python3
"""Concurrency tests for tool execution, context isolation, and race conditions."""

import asyncio

import pytest

from chuk_mcp_server.constants import McpMethod
from chuk_mcp_server.context import clear_all, get_session_id, set_session_id
from chuk_mcp_server.protocol import MCPProtocolHandler
from chuk_mcp_server.types.base import ServerCapabilities, ServerInfo
from chuk_mcp_server.types.tools import ToolHandler


@pytest.fixture(autouse=True)
def cleanup():
    """Clear context before and after each test."""
    clear_all()
    yield
    clear_all()


@pytest.fixture
def handler():
    """Create protocol handler with async tools."""
    info = ServerInfo(name="test", version="1.0")
    caps = ServerCapabilities()
    h = MCPProtocolHandler(info, caps)

    async def slow_tool(delay: float = 0.05) -> str:
        await asyncio.sleep(delay)
        return f"done-{delay}"

    async def counter_tool(n: int = 1) -> int:
        total = 0
        for i in range(n):
            await asyncio.sleep(0.001)
            total += 1
        return total

    async def echo_tool(message: str = "hello") -> str:
        return message

    h.tools["slow"] = ToolHandler.from_function(slow_tool, name="slow", description="Slow tool")
    h.tools["counter"] = ToolHandler.from_function(counter_tool, name="counter", description="Counter tool")
    h.tools["echo"] = ToolHandler.from_function(echo_tool, name="echo", description="Echo tool")
    return h


class TestConcurrentToolExecution:
    """Test that multiple tools can execute concurrently."""

    @pytest.mark.asyncio
    async def test_parallel_tool_calls(self, handler):
        """Multiple tool calls should execute concurrently."""
        messages = [
            {
                "jsonrpc": "2.0",
                "id": i,
                "method": McpMethod.TOOLS_CALL,
                "params": {"name": "slow", "arguments": {"delay": 0.02}},
            }
            for i in range(5)
        ]

        # Run all tool calls concurrently
        tasks = [handler.handle_request(msg) for msg in messages]
        results = await asyncio.gather(*tasks)

        # All should succeed
        for response, _ in results:
            assert "result" in response
            assert response["result"]["content"][0]["text"] == "done-0.02"

    @pytest.mark.asyncio
    async def test_parallel_different_tools(self, handler):
        """Different tools running in parallel should not interfere."""
        messages = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": McpMethod.TOOLS_CALL,
                "params": {"name": "slow", "arguments": {"delay": 0.02}},
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": McpMethod.TOOLS_CALL,
                "params": {"name": "counter", "arguments": {"n": 3}},
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": McpMethod.TOOLS_CALL,
                "params": {"name": "echo", "arguments": {"message": "test"}},
            },
        ]

        tasks = [handler.handle_request(msg) for msg in messages]
        results = await asyncio.gather(*tasks)

        # Verify each returned the correct result
        responses = {r[0]["id"]: r[0] for r in results}
        assert "done-0.02" in responses[1]["result"]["content"][0]["text"]
        assert "3" in responses[2]["result"]["content"][0]["text"]
        assert "test" in responses[3]["result"]["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_tasks_created_for_concurrent_calls(self, handler):
        """Each concurrent tool call should create its own task."""
        messages = [
            {
                "jsonrpc": "2.0",
                "id": i,
                "method": McpMethod.TOOLS_CALL,
                "params": {"name": "echo", "arguments": {"message": f"msg-{i}"}},
            }
            for i in range(10)
        ]

        tasks = [handler.handle_request(msg) for msg in messages]
        await asyncio.gather(*tasks)

        # Should have 10 tasks, all completed
        assert len(handler._task_store) == 10
        for task in handler._task_store.values():
            assert task["status"] == "completed"


class TestContextIsolation:
    """Test that context variables are properly isolated between concurrent requests."""

    @pytest.mark.asyncio
    async def test_session_id_isolation(self):
        """Session IDs should not leak between concurrent coroutines."""
        results = {}

        async def set_and_check(session_id: str):
            set_session_id(session_id)
            await asyncio.sleep(0.01)  # Yield to other coroutines
            actual = get_session_id()
            results[session_id] = actual

        # Run multiple coroutines concurrently setting different session IDs
        tasks = [set_and_check(f"session-{i}") for i in range(10)]
        await asyncio.gather(*tasks)

        # Each coroutine should see its own session ID
        for i in range(10):
            expected = f"session-{i}"
            assert results[expected] == expected, f"Session ID leaked: expected {expected}, got {results[expected]}"

    @pytest.mark.asyncio
    async def test_concurrent_requests_with_different_sessions(self, handler):
        """Requests with different session IDs should not interfere."""
        # Initialize sessions first
        sessions = []
        for i in range(3):
            init_msg = {
                "jsonrpc": "2.0",
                "id": i * 100,
                "method": McpMethod.INITIALIZE,
                "params": {
                    "protocolVersion": "2025-11-25",
                    "clientInfo": {"name": f"client-{i}", "version": "1.0"},
                    "capabilities": {},
                },
            }
            _, session_id = await handler.handle_request(init_msg)
            sessions.append(session_id)

        # Send tool calls with different sessions concurrently
        messages = [
            (
                {
                    "jsonrpc": "2.0",
                    "id": i + 1,
                    "method": McpMethod.TOOLS_CALL,
                    "params": {"name": "echo", "arguments": {"message": f"from-{sessions[i]}"}},
                },
                sessions[i],
            )
            for i in range(3)
        ]

        tasks = [handler.handle_request(msg, session_id=sid) for msg, sid in messages]
        results = await asyncio.gather(*tasks)

        # All should succeed
        for response, _ in results:
            assert "result" in response


class TestRaceConditions:
    """Test for race conditions in shared state."""

    @pytest.mark.asyncio
    async def test_concurrent_tool_registration(self):
        """Concurrent tool registrations should not corrupt state."""
        info = ServerInfo(name="test", version="1.0")
        caps = ServerCapabilities()
        h = MCPProtocolHandler(info, caps)

        async def register_tool(n: int):
            async def tool_fn(x: int = 0) -> int:
                return x + n

            handler = ToolHandler.from_function(tool_fn, name=f"tool_{n}", description=f"Tool {n}")
            h.register_tool(handler)

        # Register many tools concurrently
        tasks = [register_tool(i) for i in range(20)]
        await asyncio.gather(*tasks)

        # All tools should be registered
        assert len(h.tools) == 20
        for i in range(20):
            assert f"tool_{i}" in h.tools

    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self):
        """Concurrent session creation should not corrupt session manager."""
        info = ServerInfo(name="test", version="1.0")
        caps = ServerCapabilities()
        h = MCPProtocolHandler(info, caps)

        async def create_session(n: int):
            msg = {
                "jsonrpc": "2.0",
                "id": n,
                "method": McpMethod.INITIALIZE,
                "params": {
                    "protocolVersion": "2025-11-25",
                    "clientInfo": {"name": f"client-{n}", "version": "1.0"},
                    "capabilities": {},
                },
            }
            response, session_id = await h.handle_request(msg)
            return session_id

        # Create many sessions concurrently
        tasks = [create_session(i) for i in range(15)]
        session_ids = await asyncio.gather(*tasks)

        # All sessions should be unique
        assert len(set(session_ids)) == 15
        assert len(h.session_manager.sessions) == 15
