#!/usr/bin/env python3
"""Tests to achieve 90%+ coverage for oauth/token_store.py"""

import base64
import hashlib
from unittest.mock import patch

import orjson
import pytest

from chuk_mcp_server.oauth.token_store import TokenStore


class MockSession:
    """Mock session object for testing."""

    def __init__(self):
        self.data = {}
        self.ttls = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def setex(self, key, ttl, value):
        """Set key with expiration."""
        self.data[key] = value
        self.ttls[key] = ttl

    async def get(self, key):
        """Get value by key."""
        return self.data.get(key)

    async def delete(self, key):
        """Delete key."""
        if key in self.data:
            del self.data[key]
        if key in self.ttls:
            del self.ttls[key]


@pytest.fixture
def mock_session():
    """Fixture that provides a mock session."""
    session = MockSession()
    with patch("chuk_mcp_server.oauth.token_store.get_session", return_value=session):
        yield session


class TestPKCEValidation:
    """Test PKCE validation scenarios."""

    @pytest.mark.asyncio
    async def test_validate_code_pkce_missing_verifier(self, mock_session):
        """Test validation fails when code_verifier is missing for PKCE (line 162)."""
        store = TokenStore()

        # Create auth code with PKCE challenge
        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            scope="read write",
            code_challenge="test_challenge",
            code_challenge_method="S256",
        )

        # Try to validate without code_verifier - should fail
        result = await store.validate_authorization_code(
            code=code,
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            code_verifier=None,  # Missing verifier
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_code_pkce_s256_invalid_verifier(self, mock_session):
        """Test PKCE S256 validation with invalid verifier (lines 172)."""
        store = TokenStore()

        # Create correct challenge
        correct_verifier = "correct_verifier_12345678901234567890123456789012345678901234567890"
        verifier_hash = hashlib.sha256(correct_verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(verifier_hash).decode().rstrip("=")

        # Create auth code with PKCE S256
        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            scope="read write",
            code_challenge=challenge,
            code_challenge_method="S256",
        )

        # Try with wrong verifier
        result = await store.validate_authorization_code(
            code=code,
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            code_verifier="wrong_verifier",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_code_pkce_s256_valid_verifier(self, mock_session):
        """Test PKCE S256 validation with valid verifier."""
        store = TokenStore()

        # Create correct challenge
        verifier = "test_verifier_12345678901234567890123456789012345678901234567890"
        verifier_hash = hashlib.sha256(verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(verifier_hash).decode().rstrip("=")

        # Create auth code with PKCE S256
        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            scope="read write",
            code_challenge=challenge,
            code_challenge_method="S256",
        )

        # Validate with correct verifier
        result = await store.validate_authorization_code(
            code=code,
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            code_verifier=verifier,
        )

        assert result is not None
        assert result["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_validate_code_pkce_plain_invalid_verifier(self, mock_session):
        """Test PKCE plain validation with invalid verifier (lines 174-175)."""
        store = TokenStore()

        # Create auth code with PKCE plain
        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            scope="read write",
            code_challenge="plain_challenge_value",
            code_challenge_method="plain",
        )

        # Try with wrong verifier
        result = await store.validate_authorization_code(
            code=code,
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            code_verifier="wrong_verifier",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_code_pkce_plain_valid_verifier(self, mock_session):
        """Test PKCE plain validation with valid verifier."""
        store = TokenStore()

        # Create auth code with PKCE plain
        challenge = "plain_challenge_value_1234567890"
        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            scope="read write",
            code_challenge=challenge,
            code_challenge_method="plain",
        )

        # Validate with correct verifier (same as challenge for plain)
        result = await store.validate_authorization_code(
            code=code,
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            code_verifier=challenge,
        )

        assert result is not None
        assert result["user_id"] == "user123"


class TestRefreshTokenRotation:
    """Test refresh token rotation with old access token deletion."""

    @pytest.mark.asyncio
    async def test_refresh_access_token_with_old_token_deletion(self, mock_session):
        """Test refresh token deletes old access token (lines 293-294)."""
        store = TokenStore()

        # Create initial access and refresh tokens
        access_token, refresh_token = await store.create_access_token(
            user_id="user123",
            client_id="client123",
            scope="read write",
        )

        # Verify old access token exists
        old_access_key = f"{store.sandbox_id}:access_token:{access_token}"
        assert old_access_key in mock_session.data

        # Refresh to get new tokens
        new_access, new_refresh = await store.refresh_access_token(refresh_token)

        # Verify old access token was deleted
        assert old_access_key not in mock_session.data

        # Verify new tokens are different
        assert new_access != access_token
        assert new_refresh != refresh_token

        # Verify new tokens work
        new_access_data = await store.validate_access_token(new_access)
        assert new_access_data is not None
        assert new_access_data["user_id"] == "user123"


class TestPendingAuthorization:
    """Test pending authorization storage methods."""

    @pytest.mark.asyncio
    async def test_store_pending_authorization(self, mock_session):
        """Test store_pending_authorization method (lines 499-500)."""
        store = TokenStore()

        # Store pending authorization
        state = "test_state_12345"
        auth_data = {
            "client_id": "client123",
            "redirect_uri": "http://localhost:8080/callback",
            "scope": "read write",
            "code_challenge": "challenge123",
            "code_challenge_method": "S256",
        }

        await store.store_pending_authorization(state, auth_data)

        # Verify data was stored with correct TTL
        key = f"{store.sandbox_id}:pending_auth:{state}"
        assert key in mock_session.data
        assert key in mock_session.ttls
        assert mock_session.ttls[key] == store.pending_auth_ttl

        # Verify data integrity
        stored_data = orjson.loads(mock_session.data[key])
        assert stored_data == auth_data

    @pytest.mark.asyncio
    async def test_get_pending_authorization_exists(self, mock_session):
        """Test get_pending_authorization when data exists (lines 519-524)."""
        store = TokenStore()

        # Store pending authorization
        state = "test_state_67890"
        auth_data = {
            "client_id": "client456",
            "redirect_uri": "http://localhost:9000/callback",
            "scope": "admin",
        }

        await store.store_pending_authorization(state, auth_data)

        # Retrieve pending authorization
        retrieved_data = await store.get_pending_authorization(state)

        assert retrieved_data is not None
        assert retrieved_data["client_id"] == "client456"
        assert retrieved_data["redirect_uri"] == "http://localhost:9000/callback"
        assert retrieved_data["scope"] == "admin"

    @pytest.mark.asyncio
    async def test_get_pending_authorization_not_found(self, mock_session):
        """Test get_pending_authorization when data doesn't exist (line 522)."""
        store = TokenStore()

        # Try to get non-existent pending authorization
        result = await store.get_pending_authorization("nonexistent_state")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_pending_authorization_exists(self, mock_session):
        """Test delete_pending_authorization when data exists (lines 539-545)."""
        store = TokenStore()

        # Store pending authorization
        state = "state_to_delete"
        auth_data = {"client_id": "client789", "redirect_uri": "http://test.com/callback"}

        await store.store_pending_authorization(state, auth_data)

        # Verify it exists
        key = f"{store.sandbox_id}:pending_auth:{state}"
        assert key in mock_session.data

        # Delete it
        result = await store.delete_pending_authorization(state)

        assert result is True
        assert key not in mock_session.data

    @pytest.mark.asyncio
    async def test_delete_pending_authorization_not_found(self, mock_session):
        """Test delete_pending_authorization when data doesn't exist (line 545)."""
        store = TokenStore()

        # Try to delete non-existent pending authorization
        result = await store.delete_pending_authorization("nonexistent_state")

        assert result is False

    @pytest.mark.asyncio
    async def test_pending_authorization_workflow(self, mock_session):
        """Test complete pending authorization workflow."""
        store = TokenStore()

        state = "workflow_state_123"
        auth_data = {
            "client_id": "workflow_client",
            "redirect_uri": "http://workflow.test/callback",
            "scope": "read write admin",
            "code_challenge": "workflow_challenge",
            "code_challenge_method": "S256",
        }

        # 1. Store pending authorization
        await store.store_pending_authorization(state, auth_data)

        # 2. Retrieve it
        retrieved = await store.get_pending_authorization(state)
        assert retrieved == auth_data

        # 3. Delete it (after successful callback)
        deleted = await store.delete_pending_authorization(state)
        assert deleted is True

        # 4. Verify it's gone
        retrieved_again = await store.get_pending_authorization(state)
        assert retrieved_again is None

        # 5. Try to delete again
        deleted_again = await store.delete_pending_authorization(state)
        assert deleted_again is False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_pkce_without_challenge(self, mock_session):
        """Test that authorization works without PKCE."""
        store = TokenStore()

        # Create auth code without PKCE
        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            scope="read write",
            code_challenge=None,
            code_challenge_method=None,
        )

        # Validate without verifier (should work)
        result = await store.validate_authorization_code(
            code=code,
            client_id="client123",
            redirect_uri="http://localhost:8080/callback",
            code_verifier=None,
        )

        assert result is not None
        assert result["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_pending_auth_ttl_configuration(self):
        """Test pending_auth_ttl is configured from environment."""
        with patch.dict("os.environ", {"OAUTH_PENDING_AUTH_TTL": "1200"}):
            store = TokenStore()
            assert store.pending_auth_ttl == 1200

    @pytest.mark.asyncio
    async def test_multiple_pending_authorizations(self, mock_session):
        """Test storing multiple pending authorizations."""
        store = TokenStore()

        # Store multiple pending auths
        states_and_data = [
            ("state1", {"client_id": "client1", "redirect_uri": "http://test1.com"}),
            ("state2", {"client_id": "client2", "redirect_uri": "http://test2.com"}),
            ("state3", {"client_id": "client3", "redirect_uri": "http://test3.com"}),
        ]

        for state, data in states_and_data:
            await store.store_pending_authorization(state, data)

        # Verify all are retrievable
        for state, expected_data in states_and_data:
            retrieved = await store.get_pending_authorization(state)
            assert retrieved == expected_data

        # Delete one
        await store.delete_pending_authorization("state2")

        # Verify state2 is gone but others remain
        assert await store.get_pending_authorization("state2") is None
        assert await store.get_pending_authorization("state1") is not None
        assert await store.get_pending_authorization("state3") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
