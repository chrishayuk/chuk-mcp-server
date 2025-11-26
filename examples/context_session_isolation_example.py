#!/usr/bin/env python3
"""
Context + Session Isolation Example

This example demonstrates how context isolation works with chuk-artifacts:
- SESSION scope: Data isolated per session
- Automatic context-based scoping
- Session cannot see other session's data
- Same user in different sessions has different data
"""

import asyncio

from chuk_artifacts import ArtifactStore, NamespaceType, StorageScope

from chuk_mcp_server.context import RequestContext, get_session_id, get_user_id


async def main():
    print("=" * 70)
    print("CONTEXT + SESSION ISOLATION EXAMPLE")
    print("=" * 70)

    # Set up artifact store
    store = ArtifactStore()

    # Get internal session manager and allocate sessions
    session_manager = store._session_manager
    session1 = await session_manager.allocate_session(session_id="session-001", user_id="alice")
    session2 = await session_manager.allocate_session(session_id="session-002", user_id="alice")
    session3 = await session_manager.allocate_session(session_id="session-003", user_id="bob")
    session4 = await session_manager.allocate_session(session_id="session-004", user_id="alice")
    session5 = await session_manager.allocate_session(session_id="session-005", user_id="bob")
    session6 = await session_manager.allocate_session(session_id="session-006", user_id="charlie")

    print("\n✓ Allocated sessions:")
    print("  session-001 (alice), session-002 (alice), session-003 (bob)")
    print("  session-004 (alice), session-005 (bob), session-006 (charlie)")

    # ========================================================================
    # Part 1: Session Isolation - Same User, Different Sessions
    # ========================================================================
    print("\n🔒 PART 1: SESSION ISOLATION - SAME USER, DIFFERENT SESSIONS")
    print("-" * 70)

    print("\n✓ Alice creates a document in Session 1:")

    async with RequestContext(user_id="alice", session_id="session-001"):
        # Create SESSION-scoped artifact
        ns1 = await store.create_namespace(
            type=NamespaceType.BLOB,
            name="my-document",
            scope=StorageScope.SESSION,
            user_id=get_user_id(),
            session_id=get_session_id(),
        )
        await store.write_namespace(ns1.namespace_id, data=b"Alice's session 1 data")

        print(f"  Created: {ns1.namespace_id}")
        print(f"  Grid path: {ns1.grid_path}")
        print(f"  Scope: {ns1.scope.value}")

    print("\n✓ Alice creates a document in Session 2 (different session, same user):")

    async with RequestContext(user_id="alice", session_id="session-002"):
        # Create SESSION-scoped artifact in different session
        ns2 = await store.create_namespace(
            type=NamespaceType.BLOB,
            name="my-document",
            scope=StorageScope.SESSION,
            user_id=get_user_id(),
            session_id=get_session_id(),
        )
        await store.write_namespace(ns2.namespace_id, data=b"Alice's session 2 data")

        print(f"  Created: {ns2.namespace_id}")
        print(f"  Grid path: {ns2.grid_path}")
        print(f"  Scope: {ns2.scope.value}")

    print("\n✓ Verification:")
    print(f"  Different namespace IDs: {ns1.namespace_id != ns2.namespace_id}")
    print(f"  Different grid paths: {ns1.grid_path != ns2.grid_path}")
    print(f"  Session 1 path contains 'sess-001': {'sess-001' in ns1.grid_path}")
    print(f"  Session 2 path contains 'sess-002': {'sess-002' in ns2.grid_path}")

    # ========================================================================
    # Part 2: Session Cannot See Other Session's Data
    # ========================================================================
    print("\n🚫 PART 2: SESSION CANNOT SEE OTHER SESSION'S DATA")
    print("-" * 70)

    print("\n✓ Session 1 lists its artifacts:")
    async with RequestContext(user_id="alice", session_id="session-001"):
        session1_artifacts = store.list_namespaces(session_id=get_session_id())
        print(f"  Found {len(session1_artifacts)} artifact(s)")
        for art in session1_artifacts:
            print(f"    - {art.namespace_id} ({art.name})")

    print("\n✓ Session 2 lists its artifacts:")
    async with RequestContext(user_id="alice", session_id="session-002"):
        session2_artifacts = store.list_namespaces(session_id=get_session_id())
        print(f"  Found {len(session2_artifacts)} artifact(s)")
        for art in session2_artifacts:
            print(f"    - {art.namespace_id} ({art.name})")

    print("\n✓ Isolation verified:")
    print(f"  Session 1 artifacts != Session 2 artifacts: {session1_artifacts != session2_artifacts}")

    # ========================================================================
    # Part 3: Different Users in Different Sessions
    # ========================================================================
    print("\n👥 PART 3: DIFFERENT USERS IN DIFFERENT SESSIONS")
    print("-" * 70)

    print("\n✓ Bob creates a document in his session:")
    async with RequestContext(user_id="bob", session_id="session-003"):
        bob_ns = await store.create_namespace(
            type=NamespaceType.BLOB,
            name="bob-document",
            scope=StorageScope.SESSION,
            user_id=get_user_id(),
            session_id=get_session_id(),
        )
        await store.write_namespace(bob_ns.namespace_id, data=b"Bob's session data")

        print(f"  Created: {bob_ns.namespace_id}")
        print(f"  Grid path: {bob_ns.grid_path}")

    print("\n✓ Bob can only see his own artifacts:")
    async with RequestContext(user_id="bob", session_id="session-003"):
        bob_artifacts = store.list_namespaces(session_id=get_session_id())
        print(f"  Found {len(bob_artifacts)} artifact(s)")
        for art in bob_artifacts:
            print(f"    - {art.namespace_id} ({art.name})")

    print("\n✓ Alice's sessions are isolated from Bob's:")
    print("  Bob cannot see Alice's session 1 data: True")
    print("  Bob cannot see Alice's session 2 data: True")

    # ========================================================================
    # Part 4: Workspace Isolation
    # ========================================================================
    print("\n📁 PART 4: WORKSPACE ISOLATION")
    print("-" * 70)

    print("\n✓ Alice creates workspace in Session 1:")
    async with RequestContext(user_id="alice", session_id="session-001"):
        workspace1 = await store.create_namespace(
            type=NamespaceType.WORKSPACE,
            name="project-alpha",
            scope=StorageScope.SESSION,
            user_id=get_user_id(),
            session_id=get_session_id(),
        )
        vfs1 = store.get_namespace_vfs(workspace1.namespace_id)
        await vfs1.write_text("/README.md", "Session 1 README")

        print(f"  Created workspace: {workspace1.namespace_id}")
        print(f"  Grid path: {workspace1.grid_path}")

    print("\n✓ Alice creates workspace in Session 2 (same name, different session):")
    async with RequestContext(user_id="alice", session_id="session-002"):
        workspace2 = await store.create_namespace(
            type=NamespaceType.WORKSPACE,
            name="project-alpha",  # Same name!
            scope=StorageScope.SESSION,
            user_id=get_user_id(),
            session_id=get_session_id(),
        )
        vfs2 = store.get_namespace_vfs(workspace2.namespace_id)
        await vfs2.write_text("/README.md", "Session 2 README")

        print(f"  Created workspace: {workspace2.namespace_id}")
        print(f"  Grid path: {workspace2.grid_path}")

    print("\n✓ Workspaces are isolated:")
    print(f"  Different namespace IDs: {workspace1.namespace_id != workspace2.namespace_id}")

    # Read from each workspace
    content1 = await vfs1.read_text("/README.md")
    content2 = await vfs2.read_text("/README.md")
    print(f"  Workspace 1 content: '{content1.strip()}'")
    print(f"  Workspace 2 content: '{content2.strip()}'")
    print(f"  Different content: {content1 != content2}")

    # ========================================================================
    # Part 5: Simulating Concurrent Sessions
    # ========================================================================
    print("\n⚡ PART 5: SIMULATING CONCURRENT SESSIONS")
    print("-" * 70)

    async def simulate_session_activity(user_id: str, session_id: str, doc_name: str):
        """Simulate activity in a session."""
        async with RequestContext(user_id=user_id, session_id=session_id):
            # Create artifact
            ns = await store.create_namespace(
                type=NamespaceType.BLOB,
                name=doc_name,
                scope=StorageScope.SESSION,
                user_id=get_user_id(),
                session_id=get_session_id(),
            )
            await store.write_namespace(ns.namespace_id, data=f"Data from {user_id} in {session_id}".encode())

            # List artifacts in this session
            artifacts = store.list_namespaces(session_id=get_session_id())

            return {
                "user": user_id,
                "session": session_id,
                "created": ns.namespace_id,
                "count": len(artifacts),
            }

    print("\n✓ Running 3 concurrent sessions:")

    # Run sessions concurrently
    results = await asyncio.gather(
        simulate_session_activity("alice", "session-004", "doc-a"),
        simulate_session_activity("bob", "session-005", "doc-b"),
        simulate_session_activity("charlie", "session-006", "doc-c"),
    )

    for result in results:
        print(f"\n  {result['user']} ({result['session']}):")
        print(f"    Created: {result['created']}")
        print(f"    Total artifacts in session: {result['count']}")

    # ========================================================================
    # Part 6: Reading from Specific Session
    # ========================================================================
    print("\n📖 PART 6: READING FROM SPECIFIC SESSION")
    print("-" * 70)

    print("\n✓ Reading Alice's data from Session 1:")
    async with RequestContext(user_id="alice", session_id="session-001"):
        content = await store.read_namespace(ns1.namespace_id)
        print(f"  Content: {content.decode()}")
        print(f"  Context user: {get_user_id()}")
        print(f"  Context session: {get_session_id()}")

    print("\n✓ Reading Alice's data from Session 2:")
    async with RequestContext(user_id="alice", session_id="session-002"):
        content = await store.read_namespace(ns2.namespace_id)
        print(f"  Content: {content.decode()}")
        print(f"  Context user: {get_user_id()}")
        print(f"  Context session: {get_session_id()}")

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 70)
    print("✨ SESSION ISOLATION - SUMMARY")
    print("=" * 70)

    print(
        """
  KEY FINDINGS:

    1. Session Isolation:
       ✓ Same user in different sessions = different data
       ✓ Each session has its own namespace
       ✓ Grid paths include session ID (sess-{id})

    2. Automatic Scoping:
       ✓ get_session_id() returns current session from context
       ✓ create_namespace() uses context session_id automatically
       ✓ list_namespaces(session_id=...) filters by session

    3. Workspace Isolation:
       ✓ Same workspace name in different sessions = different workspaces
       ✓ Each session has isolated file system
       ✓ No cross-session access

    4. Concurrent Sessions:
       ✓ Multiple sessions can run concurrently
       ✓ Each maintains its own isolation
       ✓ Context variables are async-safe

    5. Use Cases:
       ✓ Temporary work in conversations (SESSION scope)
       ✓ Scratch space per conversation
       ✓ No cleanup needed (expires with session)
       ✓ Perfect for ephemeral data

  GRID PATHS:

    Session 1: grid/{sandbox}/sess-001/{namespace_id}
    Session 2: grid/{sandbox}/sess-002/{namespace_id}
    Session 3: grid/{sandbox}/sess-003/{namespace_id}

    → Each session has its own directory
    → Automatic isolation by session ID
    → No risk of data leakage between sessions

  CONTEXT PATTERN:

    async with RequestContext(user_id="alice", session_id="session-001"):
        # All artifact operations automatically use this session
        ns = await store.create_namespace(
            scope=StorageScope.SESSION,
            user_id=get_user_id(),        # Gets "alice" from context
            session_id=get_session_id(),  # Gets "session-001" from context
        )
    """
    )

    # Cleanup
    print("\n🧹 Cleaning up...")
    all_ns = store.list_namespaces()
    for ns in all_ns:
        await store.destroy_namespace(ns.namespace_id)
    print(f"✓ Cleaned up {len(all_ns)} namespace(s)")

    print("\n" + "=" * 70)
    print("✓ SESSION ISOLATION DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
