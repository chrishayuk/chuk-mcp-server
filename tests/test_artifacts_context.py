"""
Tests for artifacts_context module.

These tests verify the artifact store context management functionality.
"""

import pytest

# Try to import artifacts dependencies
try:
    from chuk_artifacts import ArtifactStore, NamespaceType, StorageScope

    ARTIFACTS_AVAILABLE = True
except ImportError:
    ARTIFACTS_AVAILABLE = False

from chuk_mcp_server.artifacts_context import (
    clear_artifact_store,
    get_artifact_store,
    has_artifact_store,
    set_artifact_store,
    set_global_artifact_store,
)


class TestArtifactsNotAvailable:
    """Tests for when chuk-artifacts is not installed."""

    def test_has_artifact_store_false_when_not_available(self):
        """Test has_artifact_store returns False when artifacts not installed."""
        if ARTIFACTS_AVAILABLE:
            pytest.skip("Artifacts is available, skipping unavailable test")
        assert has_artifact_store() is False

    def test_get_artifact_store_raises_when_not_available(self):
        """Test get_artifact_store raises when artifacts not installed."""
        if ARTIFACTS_AVAILABLE:
            pytest.skip("Artifacts is available, skipping unavailable test")
        with pytest.raises(RuntimeError, match="chuk-artifacts"):
            get_artifact_store()


@pytest.mark.skipif(not ARTIFACTS_AVAILABLE, reason="chuk-artifacts not installed")
class TestArtifactsContext:
    """Tests for artifact store context management."""

    def teardown_method(self):
        """Clean up after each test."""
        clear_artifact_store()

    def test_has_artifact_store_false_initially(self):
        """Test has_artifact_store returns False when no store set."""
        clear_artifact_store()
        assert has_artifact_store() is False

    def test_set_and_get_artifact_store(self):
        """Test setting and getting artifact store from context."""
        store = ArtifactStore()
        set_artifact_store(store)

        assert has_artifact_store() is True
        retrieved = get_artifact_store()
        assert retrieved is store

    def test_set_global_artifact_store(self):
        """Test setting global artifact store."""
        store = ArtifactStore()
        set_global_artifact_store(store)

        # Should be retrievable via get_artifact_store
        retrieved = get_artifact_store()
        assert retrieved is store

    def test_context_store_takes_precedence_over_global(self):
        """Test that context store takes precedence over global store."""
        global_store = ArtifactStore()
        context_store = ArtifactStore()

        set_global_artifact_store(global_store)
        set_artifact_store(context_store)

        retrieved = get_artifact_store()
        assert retrieved is context_store
        assert retrieved is not global_store

    def test_clear_artifact_store(self):
        """Test clearing artifact store from context."""
        store = ArtifactStore()
        set_artifact_store(store)

        assert has_artifact_store() is True

        clear_artifact_store()

        assert has_artifact_store() is False

    def test_get_artifact_store_without_store_raises(self):
        """Test get_artifact_store raises when no store available."""
        clear_artifact_store()

        with pytest.raises(RuntimeError, match="No artifact store"):
            get_artifact_store()


@pytest.mark.skipif(not ARTIFACTS_AVAILABLE, reason="chuk-artifacts not installed")
class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def setup_method(self):
        """Set up artifact store for tests."""
        self.store = ArtifactStore()
        set_artifact_store(self.store)

    def teardown_method(self):
        """Clean up after tests."""
        clear_artifact_store()

    async def test_create_blob_namespace(self):
        """Test create_blob_namespace convenience function."""
        from chuk_mcp_server.artifacts_context import create_blob_namespace

        ns = await create_blob_namespace(scope=StorageScope.SANDBOX)

        assert ns is not None
        assert ns.type == NamespaceType.BLOB
        assert ns.scope == StorageScope.SANDBOX

    async def test_create_workspace_namespace(self):
        """Test create_workspace_namespace convenience function."""
        from chuk_mcp_server.artifacts_context import create_workspace_namespace

        ns = await create_workspace_namespace(
            name="test-workspace", scope=StorageScope.SANDBOX
        )

        assert ns is not None
        assert ns.type == NamespaceType.WORKSPACE
        assert ns.scope == StorageScope.SANDBOX
        assert ns.name == "test-workspace"

    async def test_write_blob(self):
        """Test write_blob convenience function."""
        from chuk_mcp_server.artifacts_context import create_blob_namespace, write_blob

        ns = await create_blob_namespace(scope=StorageScope.SANDBOX)
        await write_blob(ns.namespace_id, b"test data", mime="text/plain")

        # Verify it was written
        content = await self.store.read_namespace(ns.namespace_id)
        assert content == b"test data"

    async def test_read_blob(self):
        """Test read_blob convenience function."""
        from chuk_mcp_server.artifacts_context import create_blob_namespace, read_blob

        ns = await create_blob_namespace(scope=StorageScope.SANDBOX)
        await self.store.write_namespace(ns.namespace_id, data=b"test content")

        content = await read_blob(ns.namespace_id)
        assert content == b"test content"

    async def test_write_workspace_file(self):
        """Test write_workspace_file convenience function."""
        from chuk_mcp_server.artifacts_context import (
            create_workspace_namespace,
            write_workspace_file,
        )

        ns = await create_workspace_namespace(
            name="test-ws", scope=StorageScope.SANDBOX
        )
        await write_workspace_file(ns.namespace_id, "/test.txt", b"workspace data")

        # Verify it was written
        vfs = self.store.get_namespace_vfs(ns.namespace_id)
        content = await vfs.read_file("/test.txt")
        assert content == b"workspace data"

    async def test_read_workspace_file(self):
        """Test read_workspace_file convenience function."""
        from chuk_mcp_server.artifacts_context import (
            create_workspace_namespace,
            read_workspace_file,
        )

        ns = await create_workspace_namespace(
            name="test-ws", scope=StorageScope.SANDBOX
        )
        vfs = self.store.get_namespace_vfs(ns.namespace_id)
        await vfs.write_file("/test.txt", b"file content")

        content = await read_workspace_file(ns.namespace_id, "/test.txt")
        assert content == b"file content"

    def test_get_namespace_vfs(self):
        """Test get_namespace_vfs convenience function."""
        from chuk_mcp_server.artifacts_context import get_namespace_vfs

        # Create a namespace
        import asyncio

        async def create_ns():
            from chuk_mcp_server.artifacts_context import create_workspace_namespace

            return await create_workspace_namespace(
                name="vfs-test", scope=StorageScope.SANDBOX
            )

        ns = asyncio.run(create_ns())

        # Get VFS
        vfs = get_namespace_vfs(ns.namespace_id)
        assert vfs is not None


@pytest.mark.skipif(not ARTIFACTS_AVAILABLE, reason="chuk-artifacts not installed")
class TestDefaultScopes:
    """Tests for default scope handling."""

    def setup_method(self):
        """Set up artifact store for tests."""
        self.store = ArtifactStore()
        set_artifact_store(self.store)

    def teardown_method(self):
        """Clean up after tests."""
        clear_artifact_store()

    async def test_create_blob_namespace_default_scope(self):
        """Test create_blob_namespace uses SESSION scope by default."""
        from chuk_mcp_server.artifacts_context import create_blob_namespace

        # Need to allocate a session first
        session_manager = self.store._session_manager
        await session_manager.allocate_session(session_id="test-session")

        ns = await create_blob_namespace(session_id="test-session")

        assert ns.scope == StorageScope.SESSION

    async def test_create_workspace_namespace_default_scope(self):
        """Test create_workspace_namespace uses SESSION scope by default."""
        from chuk_mcp_server.artifacts_context import create_workspace_namespace

        # Need to allocate a session first
        session_manager = self.store._session_manager
        await session_manager.allocate_session(session_id="test-session-2")

        ns = await create_workspace_namespace(
            name="test-ws", session_id="test-session-2"
        )

        assert ns.scope == StorageScope.SESSION
