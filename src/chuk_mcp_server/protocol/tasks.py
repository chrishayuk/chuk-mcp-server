#!/usr/bin/env python3
# src/chuk_mcp_server/protocol/tasks.py
"""
MCP Tasks system (MCP 2025-11-25).

Manages durable long-running task state machines with create, update,
get, list, cancel, and status notification operations.
"""

import logging
import time
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from ..constants import (
    JSONRPC_KEY,
    JSONRPC_VERSION,
    KEY_ID,
    KEY_METHOD,
    KEY_PARAMS,
    KEY_RESULT,
    JsonRpcError,
    McpTaskMethod,
)

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages the MCP tasks store and task lifecycle operations."""

    def __init__(self) -> None:
        self._task_store: dict[str, dict[str, Any]] = {}

    def create_task(self, request_id: Any, tool_name: str) -> str:
        """Create a task for a tool execution."""
        task_id = str(uuid.uuid4()).replace("-", "")[:16]
        self._task_store[task_id] = {
            "id": task_id,
            "status": "working",
            "requestId": request_id,
            "toolName": tool_name,
            "createdAt": time.time(),
            "updatedAt": time.time(),
            "result": None,
            "error": None,
            "message": None,
        }
        return task_id

    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> None:
        """Update a task's status."""
        task = self._task_store.get(task_id)
        if task is None:
            return
        task["status"] = status
        task["updatedAt"] = time.time()
        if result is not None:
            task["result"] = result
        if error is not None:
            task["error"] = error
        if message is not None:
            task["message"] = message

    async def handle_tasks_get(
        self,
        params: dict[str, Any],
        msg_id: Any,
        create_error: Callable[..., dict[str, Any]],
    ) -> tuple[dict[str, Any], None]:
        """Handle tasks/get request."""
        task_id = params.get("id", "")
        task = self._task_store.get(task_id)
        if task is None:
            return create_error(msg_id, JsonRpcError.INVALID_PARAMS, f"Unknown task: {task_id}"), None
        return {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: task}, None

    async def handle_tasks_result(
        self,
        params: dict[str, Any],
        msg_id: Any,
        create_error: Callable[..., dict[str, Any]],
    ) -> tuple[dict[str, Any], None]:
        """Handle tasks/result request."""
        task_id = params.get("id", "")
        task = self._task_store.get(task_id)
        if task is None:
            return create_error(msg_id, JsonRpcError.INVALID_PARAMS, f"Unknown task: {task_id}"), None
        if task["status"] not in ("completed", "failed"):
            return create_error(
                msg_id, JsonRpcError.INVALID_PARAMS, f"Task {task_id} is not yet complete (status: {task['status']})"
            ), None
        return {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: task}, None

    async def handle_tasks_list(
        self,
        params: dict[str, Any],
        msg_id: Any,
        paginate: Callable[..., dict[str, Any]],
    ) -> tuple[dict[str, Any], None]:
        """Handle tasks/list request with pagination."""
        tasks_list = list(self._task_store.values())
        result = paginate(tasks_list, "tasks", params)
        return {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: result}, None

    async def handle_tasks_cancel(
        self,
        params: dict[str, Any],
        msg_id: Any,
        create_error: Callable[..., dict[str, Any]],
        in_flight_requests: dict[Any, Any],
    ) -> tuple[dict[str, Any], None]:
        """Handle tasks/cancel request."""
        task_id = params.get("id", "")
        task = self._task_store.get(task_id)
        if task is None:
            return create_error(msg_id, JsonRpcError.INVALID_PARAMS, f"Unknown task: {task_id}"), None
        if task["status"] in ("completed", "failed", "cancelled"):
            return create_error(
                msg_id,
                JsonRpcError.INVALID_PARAMS,
                f"Task {task_id} is already in terminal state: {task['status']}",
            ), None
        self.update_task_status(task_id, "cancelled")
        # Also cancel the in-flight request if tracked
        request_id = task.get("requestId")
        if request_id is not None:
            in_flight = in_flight_requests.pop(request_id, None)
            if in_flight is not None:
                in_flight.cancel()
        return {JSONRPC_KEY: JSONRPC_VERSION, KEY_ID: msg_id, KEY_RESULT: task}, None

    async def send_task_status_notification(
        self,
        task_id: str,
        send_to_client: Callable[..., Coroutine[Any, Any, None]] | None,
    ) -> None:
        """Send a notifications/tasks/status to the client."""
        if send_to_client is None:
            return
        task = self._task_store.get(task_id)
        if task is None:
            return
        notification = {
            JSONRPC_KEY: JSONRPC_VERSION,
            KEY_METHOD: McpTaskMethod.NOTIFICATIONS_TASKS_STATUS,
            KEY_PARAMS: task,
        }
        try:
            await send_to_client(notification)
        except Exception as e:
            logger.debug(f"Failed to send task status notification: {e}")

    def clear(self) -> None:
        """Clear all tasks."""
        self._task_store.clear()
