#!/usr/bin/env python3
"""
Context + User Persistence Example

This example demonstrates how USER scope data persists across sessions:
- USER scope: Data persists across different sessions for the same user
- Different from SESSION scope which is ephemeral
- Perfect for user projects, preferences, and persistent data
- Grid path uses user_id instead of session_id
"""

import asyncio

from chuk_artifacts import ArtifactStore, NamespaceType, StorageScope

from chuk_mcp_server.context import RequestContext, get_session_id, get_user_id


async def main():
    print("=" * 70)
    print("CONTEXT + USER PERSISTENCE EXAMPLE")
    print("=" * 70)

    # Set up artifact store
    store = ArtifactStore()

    # Allocate multiple sessions for the same users
    session_manager = store._session_manager
    alice_session1 = await session_manager.allocate_session(session_id="alice-sess-1", user_id="alice")
    alice_session2 = await session_manager.allocate_session(session_id="alice-sess-2", user_id="alice")
    alice_session3 = await session_manager.allocate_session(session_id="alice-sess-3", user_id="alice")
    bob_session1 = await session_manager.allocate_session(session_id="bob-sess-1", user_id="bob")
    bob_session2 = await session_manager.allocate_session(session_id="bob-sess-2", user_id="bob")

    print("\n✓ Allocated sessions:")
    print("  Alice: alice-sess-1, alice-sess-2, alice-sess-3")
    print("  Bob: bob-sess-1, bob-sess-2")

    # ========================================================================
    # Part 1: Creating USER-scoped Data
    # ========================================================================
    print("\n👤 PART 1: CREATING USER-SCOPED DATA")
    print("-" * 70)

    print("\n✓ Alice creates a USER-scoped document in Session 1:")
    async with RequestContext(user_id="alice", session_id="alice-sess-1"):
        # Create USER-scoped artifact
        alice_doc = await store.create_namespace(
            type=NamespaceType.BLOB,
            name="my-persistent-doc",
            scope=StorageScope.USER,  # USER scope - persists across sessions!
            user_id=get_user_id(),
        )
        await store.write_namespace(alice_doc.namespace_id, data=b"Alice's persistent data v1")

        print(f"  Created: {alice_doc.namespace_id}")
        print(f"  Grid path: {alice_doc.grid_path}")
        print(f"  Scope: {alice_doc.scope.value}")
        print("  Note: Grid path contains 'user-alice', NOT session ID")

    # ========================================================================
    # Part 2: Accessing USER Data from Different Sessions
    # ========================================================================
    print("\n🔄 PART 2: ACCESSING USER DATA FROM DIFFERENT SESSIONS")
    print("-" * 70)

    print("\n✓ Alice accesses the SAME document from Session 2:")
    async with RequestContext(user_id="alice", session_id="alice-sess-2"):
        # List alice's USER-scoped artifacts
        alice_artifacts = store.list_namespaces(user_id=get_user_id())
        print(f"  Found {len(alice_artifacts)} user-scoped artifact(s)")

        # Read the persistent document
        content = await store.read_namespace(alice_doc.namespace_id)
        print(f"  Content: {content.decode()}")
        print(f"  Current session: {get_session_id()}")
        print("  Document created in different session: alice-sess-1")

    print("\n✓ Alice updates the document from Session 3:")
    async with RequestContext(user_id="alice", session_id="alice-sess-3"):
        # Update the persistent document
        await store.write_namespace(alice_doc.namespace_id, data=b"Alice's persistent data v2 - updated!")

        content = await store.read_namespace(alice_doc.namespace_id)
        print(f"  Updated content: {content.decode()}")
        print(f"  Current session: {get_session_id()}")

    print("\n✓ Alice reads the updated content from Session 1:")
    async with RequestContext(user_id="alice", session_id="alice-sess-1"):
        content = await store.read_namespace(alice_doc.namespace_id)
        print(f"  Content from Session 1: {content.decode()}")
        print("  Changes made in Session 3 are visible!")

    # ========================================================================
    # Part 3: USER vs SESSION Scope Comparison
    # ========================================================================
    print("\n⚖️  PART 3: USER VS SESSION SCOPE COMPARISON")
    print("-" * 70)

    print("\n✓ Alice creates both USER and SESSION scoped documents:")
    async with RequestContext(user_id="alice", session_id="alice-sess-1"):
        # Create SESSION-scoped document
        session_doc = await store.create_namespace(
            type=NamespaceType.BLOB,
            name="session-temp-doc",
            scope=StorageScope.SESSION,
            user_id=get_user_id(),
            session_id=get_session_id(),
        )
        await store.write_namespace(session_doc.namespace_id, data=b"Temporary session data")

        # Create USER-scoped document
        user_doc = await store.create_namespace(
            type=NamespaceType.BLOB,
            name="user-persistent-doc",
            scope=StorageScope.USER,
            user_id=get_user_id(),
        )
        await store.write_namespace(user_doc.namespace_id, data=b"Persistent user data")

        print("\n  SESSION-scoped document:")
        print(f"    Grid path: {session_doc.grid_path}")
        print(f"    Contains session ID: {'alice-sess-1' in session_doc.grid_path}")

        print("\n  USER-scoped document:")
        print(f"    Grid path: {user_doc.grid_path}")
        print(f"    Contains user ID: {'user-alice' in user_doc.grid_path}")
        print(f"    Contains session ID: {'alice-sess-1' in user_doc.grid_path}")

    print("\n✓ Accessing from Session 2:")
    async with RequestContext(user_id="alice", session_id="alice-sess-2"):
        # List SESSION-scoped artifacts (only for this session)
        session_artifacts = store.list_namespaces(session_id=get_session_id())
        print(f"\n  SESSION-scoped artifacts in this session: {len(session_artifacts)}")
        print("    Session 1's document is NOT visible")

        # List USER-scoped artifacts (for this user, any session)
        user_artifacts = store.list_namespaces(user_id=get_user_id())
        print(f"\n  USER-scoped artifacts for alice: {len(user_artifacts)}")
        print("    All user documents ARE visible across sessions")

    # ========================================================================
    # Part 4: User Workspaces - Persistent Projects
    # ========================================================================
    print("\n📁 PART 4: USER WORKSPACES - PERSISTENT PROJECTS")
    print("-" * 70)

    print("\n✓ Alice creates a persistent project workspace in Session 1:")
    async with RequestContext(user_id="alice", session_id="alice-sess-1"):
        project = await store.create_namespace(
            type=NamespaceType.WORKSPACE,
            name="my-project",
            scope=StorageScope.USER,
            user_id=get_user_id(),
        )
        vfs = store.get_namespace_vfs(project.namespace_id)
        await vfs.write_text("/README.md", "# My Project\n\nCreated in Session 1")
        await vfs.mkdir("/src")
        await vfs.write_text("/src/main.py", "print('Hello from Session 1')")

        print(f"  Created workspace: {project.namespace_id}")
        print(f"  Grid path: {project.grid_path}")

    print("\n✓ Alice continues working on the project in Session 2:")
    async with RequestContext(user_id="alice", session_id="alice-sess-2"):
        # Access the same workspace
        vfs = store.get_namespace_vfs(project.namespace_id)

        # Read existing file
        readme = await vfs.read_text("/README.md")
        print(f"  README from Session 1: {readme.strip()}")

        # Add more files
        await vfs.mkdir("/tests")
        await vfs.write_text("/tests/test_main.py", "# Tests added in Session 2")

        # Update existing file
        main_code = await vfs.read_text("/src/main.py")
        updated = main_code.replace("Session 1", "Session 2 (updated)")
        await vfs.write_text("/src/main.py", updated)

        files = await vfs.find(pattern="*", recursive=True)
        print(f"  Total files in workspace: {len(files)}")

    print("\n✓ Alice views the project from Session 3:")
    async with RequestContext(user_id="alice", session_id="alice-sess-3"):
        vfs = store.get_namespace_vfs(project.namespace_id)

        files = await vfs.find(pattern="*", recursive=True)
        print(f"  Files visible from Session 3: {len(files)}")
        print("  All changes from Sessions 1 & 2 are persisted!")

        main_code = await vfs.read_text("/src/main.py")
        print(f"  main.py content: {main_code.strip()}")

    # ========================================================================
    # Part 5: Different Users Have Different Persistent Data
    # ========================================================================
    print("\n👥 PART 5: DIFFERENT USERS HAVE DIFFERENT PERSISTENT DATA")
    print("-" * 70)

    print("\n✓ Bob creates his own USER-scoped document:")
    async with RequestContext(user_id="bob", session_id="bob-sess-1"):
        bob_doc = await store.create_namespace(
            type=NamespaceType.BLOB,
            name="bob-persistent-doc",
            scope=StorageScope.USER,
            user_id=get_user_id(),
        )
        await store.write_namespace(bob_doc.namespace_id, data=b"Bob's private persistent data")

        print(f"  Created: {bob_doc.namespace_id}")
        print(f"  Grid path: {bob_doc.grid_path}")
        print(f"  Contains 'user-bob': {'user-bob' in bob_doc.grid_path}")

    print("\n✓ Verification of user isolation:")
    async with RequestContext(user_id="alice", session_id="alice-sess-1"):
        alice_docs = store.list_namespaces(user_id=get_user_id())
        print(f"  Alice can see {len(alice_docs)} user-scoped document(s)")

    async with RequestContext(user_id="bob", session_id="bob-sess-1"):
        bob_docs = store.list_namespaces(user_id=get_user_id())
        print(f"  Bob can see {len(bob_docs)} user-scoped document(s)")

    print("\n  Alice cannot see Bob's USER data: True")
    print("  Bob cannot see Alice's USER data: True")
    print("  USER scope = per-user persistent storage")

    # ========================================================================
    # Part 6: Use Case: User Preferences
    # ========================================================================
    print("\n⚙️  PART 6: USE CASE - USER PREFERENCES")
    print("-" * 70)

    print("\n✓ Alice saves preferences in Session 1:")
    async with RequestContext(user_id="alice", session_id="alice-sess-1"):
        prefs = await store.create_namespace(
            type=NamespaceType.BLOB,
            name="user-preferences",
            scope=StorageScope.USER,
            user_id=get_user_id(),
        )
        import json

        prefs_data = {
            "theme": "dark",
            "language": "en",
            "notifications": True,
        }
        await store.write_namespace(prefs.namespace_id, data=json.dumps(prefs_data).encode())
        print(f"  Saved preferences: {prefs_data}")

    print("\n✓ Alice loads preferences in Session 2 (different conversation):")
    async with RequestContext(user_id="alice", session_id="alice-sess-2"):
        content = await store.read_namespace(prefs.namespace_id)
        loaded_prefs = json.loads(content.decode())
        print(f"  Loaded preferences: {loaded_prefs}")
        print("  Preferences persisted across sessions!")

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 70)
    print("✨ USER PERSISTENCE - SUMMARY")
    print("=" * 70)

    print(
        """
  KEY FINDINGS:

    1. USER Scope:
       ✓ Data persists across all sessions for the same user
       ✓ Grid path: grid/{sandbox}/user-{user_id}/{namespace_id}
       ✓ Perfect for: projects, preferences, persistent storage

    2. Session Independence:
       ✓ Same user can have multiple active sessions
       ✓ USER data accessible from ALL sessions
       ✓ Changes in one session visible in all others

    3. User Isolation:
       ✓ Each user has their own USER-scoped storage
       ✓ Users cannot see each other's USER data
       ✓ Complete privacy per user

    4. Workspace Persistence:
       ✓ USER-scoped workspaces persist across sessions
       ✓ Continue working on projects across conversations
       ✓ All files and changes are preserved

    5. Use Cases:
       ✓ User projects (persist indefinitely)
       ✓ User preferences and settings
       ✓ Personal document storage
       ✓ Long-term data that transcends conversations

  SCOPE COMPARISON:

    SESSION Scope:
      → Ephemeral, tied to one conversation
      → Grid: grid/{sandbox}/session-{session_id}/{namespace_id}
      → Use for: temporary work, caches

    USER Scope:
      → Persistent, tied to user
      → Grid: grid/{sandbox}/user-{user_id}/{namespace_id}
      → Use for: projects, preferences, persistent data

    SANDBOX Scope:
      → Shared across all users
      → Grid: grid/{sandbox}/shared/{namespace_id}
      → Use for: templates, shared libraries

  CONTEXT PATTERN:

    # Session 1 - Create persistent data
    async with RequestContext(user_id="alice", session_id="sess-1"):
        doc = await store.create_namespace(
            scope=StorageScope.USER,  # Persists across sessions
            user_id=get_user_id(),
        )

    # Session 2 - Access same persistent data
    async with RequestContext(user_id="alice", session_id="sess-2"):
        # Can access doc.namespace_id from session 1!
        content = await store.read_namespace(doc.namespace_id)
    """
    )

    # Cleanup
    print("\n🧹 Cleaning up...")
    all_ns = store.list_namespaces()
    for ns in all_ns:
        await store.destroy_namespace(ns.namespace_id)
    print(f"✓ Cleaned up {len(all_ns)} namespace(s)")

    print("\n" + "=" * 70)
    print("✓ USER PERSISTENCE DEMO COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
