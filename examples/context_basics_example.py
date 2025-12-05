#!/usr/bin/env python3
"""
Context Basics Example

This example demonstrates the fundamentals of chuk-mcp-server's context system:
- Setting and getting user_id and session_id
- Context isolation across requests
- RequestContext manager usage
- require_user_id() and require_session_id() for auth checks
"""

import asyncio

from chuk_mcp_server.context import (
    RequestContext,
    clear_all,
    get_current_context,
    get_session_id,
    get_user_id,
    require_session_id,
    require_user_id,
    set_session_id,
    set_user_id,
)


async def main():
    print("=" * 70)
    print("CONTEXT BASICS EXAMPLE")
    print("=" * 70)

    # ========================================================================
    # Part 1: Basic Context Access
    # ========================================================================
    print("\n📋 PART 1: BASIC CONTEXT ACCESS")
    print("-" * 70)

    # Initially, context is empty
    print("\n✓ Initial context state:")
    print(f"  user_id: {get_user_id()}")
    print(f"  session_id: {get_session_id()}")
    print(f"  full context: {get_current_context()}")

    # Set context values
    set_user_id("alice")
    set_session_id("session-001")

    print("\n✓ After setting context:")
    print(f"  user_id: {get_user_id()}")
    print(f"  session_id: {get_session_id()}")

    # ========================================================================
    # Part 2: RequestContext Manager
    # ========================================================================
    print("\n🔒 PART 2: REQUEST CONTEXT MANAGER")
    print("-" * 70)

    # Clear context first
    clear_all()

    print("\n✓ Using RequestContext manager:")

    async with RequestContext(user_id="bob", session_id="session-002"):
        print(f"  Inside context - user_id: {get_user_id()}")
        print(f"  Inside context - session_id: {get_session_id()}")

    print(f"  Outside context - user_id: {get_user_id()}")
    print(f"  Outside context - session_id: {get_session_id()}")

    # ========================================================================
    # Part 3: Nested Contexts
    # ========================================================================
    print("\n🪆 PART 3: NESTED CONTEXTS")
    print("-" * 70)

    print("\n✓ Demonstrating nested contexts:")

    async with RequestContext(user_id="alice", session_id="session-001"):
        print(f"  Outer context - user: {get_user_id()}, session: {get_session_id()}")

        async with RequestContext(user_id="bob", session_id="session-002"):
            print(f"  Inner context - user: {get_user_id()}, session: {get_session_id()}")

        print(f"  Back to outer - user: {get_user_id()}, session: {get_session_id()}")

    print(f"  Outside all - user: {get_user_id()}, session: {get_session_id()}")

    # ========================================================================
    # Part 4: Partial Context (only user or only session)
    # ========================================================================
    print("\n🎯 PART 4: PARTIAL CONTEXT")
    print("-" * 70)

    print("\n✓ Setting only user_id:")
    async with RequestContext(user_id="charlie"):
        print(f"  user_id: {get_user_id()}")
        print(f"  session_id: {get_session_id()}")

    print("\n✓ Setting only session_id:")
    async with RequestContext(session_id="session-003"):
        print(f"  user_id: {get_user_id()}")
        print(f"  session_id: {get_session_id()}")

    # ========================================================================
    # Part 5: Authentication Checks
    # ========================================================================
    print("\n🔐 PART 5: AUTHENTICATION CHECKS")
    print("-" * 70)

    print("\n✓ Using require_user_id() and require_session_id():")

    # Without context - should raise
    clear_all()
    try:
        user = require_user_id()
        print(f"  This shouldn't print: {user}")
    except PermissionError as e:
        print(f"  ✓ require_user_id() raised: {type(e).__name__}")

    try:
        session = require_session_id()
        print(f"  This shouldn't print: {session}")
    except RuntimeError as e:
        print(f"  ✓ require_session_id() raised: {type(e).__name__}")

    # With context - should work
    async with RequestContext(user_id="alice", session_id="session-001"):
        user = require_user_id()
        session = require_session_id()
        print("\n✓ With context:")
        print(f"  require_user_id() returned: {user}")
        print(f"  require_session_id() returned: {session}")

    # ========================================================================
    # Part 6: Simulating Request Handlers
    # ========================================================================
    print("\n🔧 PART 6: SIMULATING REQUEST HANDLERS")
    print("-" * 70)

    async def handle_tool_call(tool_name: str) -> dict:
        """
        Simulate a tool that requires authentication.

        In a real MCP server, the context would be set by the protocol handler
        before calling the tool.
        """
        user_id = require_user_id()
        session_id = get_session_id()

        return {
            "tool": tool_name,
            "user": user_id,
            "session": session_id,
            "result": f"Executed {tool_name} for {user_id}",
        }

    async def handle_request(user_id: str, session_id: str, tool_name: str):
        """
        Simulate the MCP protocol handler that sets up context.

        This is similar to what happens in the actual MCP server framework.
        """
        async with RequestContext(user_id=user_id, session_id=session_id):
            result = await handle_tool_call(tool_name)
            return result

    print("\n✓ Simulating multiple requests:")

    # Request 1: Alice
    result1 = await handle_request(user_id="alice", session_id="session-001", tool_name="create_file")
    print("\n  Request 1 (Alice):")
    print(f"    Result: {result1['result']}")

    # Request 2: Bob
    result2 = await handle_request(user_id="bob", session_id="session-002", tool_name="read_file")
    print("\n  Request 2 (Bob):")
    print(f"    Result: {result2['result']}")

    # Request 3: Alice again (different session)
    result3 = await handle_request(user_id="alice", session_id="session-003", tool_name="delete_file")
    print("\n  Request 3 (Alice, new session):")
    print(f"    Result: {result3['result']}")

    # ========================================================================
    # Part 7: Context Metadata
    # ========================================================================
    print("\n📦 PART 7: CONTEXT METADATA")
    print("-" * 70)

    print("\n✓ Using context metadata:")

    async with RequestContext(
        user_id="alice",
        session_id="session-001",
        metadata={"ip": "192.168.1.1", "client": "Claude Desktop"},
    ):
        context = get_current_context()
        print(f"  Full context: {context}")
        print(f"  Metadata: {context['metadata']}")

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 70)
    print("✨ CONTEXT BASICS - SUMMARY")
    print("=" * 70)

    print(
        """
  KEY CONCEPTS:

    1. Context Variables:
       ✓ user_id - OAuth user identifier
       ✓ session_id - MCP session identifier
       ✓ progress_token - For progress notifications
       ✓ metadata - Custom request data

    2. Access Functions:
       ✓ get_user_id() - Returns user_id or None
       ✓ get_session_id() - Returns session_id or None
       ✓ require_user_id() - Returns user_id or raises PermissionError
       ✓ require_session_id() - Returns session_id or raises RuntimeError

    3. Setting Context:
       ✓ set_user_id(id) - Set user_id directly
       ✓ set_session_id(id) - Set session_id directly
       ✓ RequestContext(...) - Async context manager (preferred)

    4. RequestContext Manager:
       ✓ Automatic setup and cleanup
       ✓ Supports nested contexts
       ✓ Restores previous context on exit
       ✓ Can set partial context (only user or session)

    5. Typical Usage Pattern:
       ✓ Protocol handler sets context via RequestContext
       ✓ Tools use get_user_id() and get_session_id()
       ✓ Auth-required tools use require_user_id()
       ✓ Context is automatically isolated per request

  WHEN TO USE:

    → In MCP protocol handlers: Use RequestContext manager
    → In tools/resources: Use get_user_id(), get_session_id()
    → For auth checks: Use require_user_id(), require_session_id()
    → For cleanup: Use clear_all() (mainly in tests)

  BENEFITS:

    → Thread-safe and async-safe (uses ContextVar)
    → No manual parameter passing needed
    → Automatic isolation between requests
    → Clean context lifecycle management
    → Works seamlessly with chuk-artifacts for scoping
    """
    )

    print("\n" + "=" * 70)
    print("✓ CONTEXT BASICS DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
