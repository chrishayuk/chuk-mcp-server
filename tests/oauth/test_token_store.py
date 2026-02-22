"""Tests for OAuth TokenStore."""

import base64
import hashlib
from datetime import datetime, timedelta
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


class TestTokenStore:
    """Test TokenStore class."""

    def test_init_default(self):
        """Test TokenStore initialization with defaults."""
        store = TokenStore()
        assert store.sandbox_id == "chuk-mcp-linkedin"
        assert store.auth_code_ttl == 300  # 5 minutes
        assert store.access_token_ttl == 900  # 15 minutes
        assert store.refresh_token_ttl == 86400  # 1 day
        assert store.client_registration_ttl == 31536000  # 1 year
        assert store.external_token_ttl == 86400  # 1 day

    def test_init_custom_sandbox(self):
        """Test TokenStore initialization with custom sandbox_id."""
        store = TokenStore(sandbox_id="custom-sandbox")
        assert store.sandbox_id == "custom-sandbox"

    def test_init_custom_ttls(self, monkeypatch):
        """Test TokenStore initialization with custom TTLs from environment."""
        monkeypatch.setenv("OAUTH_AUTH_CODE_TTL", "600")
        monkeypatch.setenv("OAUTH_ACCESS_TOKEN_TTL", "1800")
        monkeypatch.setenv("OAUTH_REFRESH_TOKEN_TTL", "172800")
        monkeypatch.setenv("OAUTH_CLIENT_REGISTRATION_TTL", "63072000")
        monkeypatch.setenv("OAUTH_EXTERNAL_TOKEN_TTL", "172800")

        store = TokenStore()
        assert store.auth_code_ttl == 600
        assert store.access_token_ttl == 1800
        assert store.refresh_token_ttl == 172800
        assert store.client_registration_ttl == 63072000
        assert store.external_token_ttl == 172800

    @pytest.mark.asyncio
    async def test_create_authorization_code(self, mock_session):
        """Test creating authorization code."""
        store = TokenStore()

        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
            scope="read write",
        )

        assert code is not None
        assert len(code) > 0

        # Verify it was stored in session
        key = f"{store.sandbox_id}:auth_code:{code}"
        assert key in mock_session.data
        assert mock_session.ttls[key] == 300  # Default TTL

    @pytest.mark.asyncio
    async def test_create_authorization_code_with_pkce(self, mock_session):
        """Test creating authorization code with PKCE."""
        store = TokenStore()

        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
            code_challenge="test_challenge",
            code_challenge_method="S256",
        )

        assert code is not None
        key = f"{store.sandbox_id}:auth_code:{code}"
        assert key in mock_session.data

    @pytest.mark.asyncio
    async def test_validate_authorization_code_success(self, mock_session):
        """Test validating authorization code successfully."""
        store = TokenStore()

        # Create a code first
        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
        )

        # Validate it
        result = await store.validate_authorization_code(
            code=code,
            client_id="client456",
            redirect_uri="http://localhost/callback",
        )

        assert result is not None
        assert result["user_id"] == "user123"
        assert result["client_id"] == "client456"

    @pytest.mark.asyncio
    async def test_validate_authorization_code_invalid(self, mock_session):
        """Test validating invalid authorization code."""
        store = TokenStore()

        result = await store.validate_authorization_code(
            code="invalid_code",
            client_id="client456",
            redirect_uri="http://localhost/callback",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_authorization_code_wrong_client(self, mock_session):
        """Test validating code with wrong client_id."""
        store = TokenStore()

        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
        )

        result = await store.validate_authorization_code(
            code=code,
            client_id="wrong_client",
            redirect_uri="http://localhost/callback",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_authorization_code_wrong_redirect(self, mock_session):
        """Test validating code with wrong redirect_uri."""
        store = TokenStore()

        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
        )

        result = await store.validate_authorization_code(
            code=code,
            client_id="client456",
            redirect_uri="http://wrong/uri",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_authorization_code_with_pkce(self, mock_session):
        """Test validating code with PKCE verifier."""
        store = TokenStore()

        # Create code with challenge using proper base64url encoding
        verifier = b"test_verifier"
        verifier_hash = hashlib.sha256(verifier).digest()
        challenge = base64.urlsafe_b64encode(verifier_hash).decode().rstrip("=")

        code = await store.create_authorization_code(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
            code_challenge=challenge,
            code_challenge_method="S256",
        )

        # Validate with verifier
        result = await store.validate_authorization_code(
            code=code,
            client_id="client456",
            redirect_uri="http://localhost/callback",
            code_verifier="test_verifier",
        )

        assert result is not None
        assert result["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_create_access_token(self, mock_session):
        """Test creating MCP access token."""
        store = TokenStore()

        access_token, refresh_token = await store.create_access_token(
            user_id="user123",
            client_id="client456",
            scope="read write",
        )

        assert access_token is not None
        assert refresh_token is not None
        assert len(access_token) > 0
        assert len(refresh_token) > 0

        # Verify stored in session
        access_key = f"{store.sandbox_id}:access_token:{access_token}"
        refresh_key = f"{store.sandbox_id}:refresh_token:{refresh_token}"
        assert access_key in mock_session.data
        assert refresh_key in mock_session.data

    @pytest.mark.asyncio
    async def test_validate_access_token_success(self, mock_session):
        """Test validating access token successfully."""
        store = TokenStore()

        access_token, _ = await store.create_access_token(
            user_id="user123",
            client_id="client456",
        )

        result = await store.validate_access_token(access_token)

        assert result is not None
        assert result["user_id"] == "user123"
        assert result["client_id"] == "client456"

    @pytest.mark.asyncio
    async def test_validate_access_token_invalid(self, mock_session):
        """Test validating invalid access token."""
        store = TokenStore()

        result = await store.validate_access_token("invalid_token")

        assert result is None

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, mock_session):
        """Test refreshing access token successfully."""
        store = TokenStore()

        # Create initial tokens
        _, refresh_token = await store.create_access_token(
            user_id="user123",
            client_id="client456",
        )

        # Refresh
        new_access, new_refresh = await store.refresh_access_token(refresh_token)

        assert new_access is not None
        assert new_refresh is not None
        assert new_access != refresh_token
        assert new_refresh != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(self, mock_session):
        """Test refreshing with invalid refresh token."""
        store = TokenStore()

        result = await store.refresh_access_token("invalid_refresh_token")

        assert result is None

    @pytest.mark.asyncio
    async def test_link_external_token(self, mock_session):
        """Test linking external OAuth provider token."""
        store = TokenStore()

        await store.link_external_token(
            user_id="user123",
            access_token="external_access_token",
            refresh_token="external_refresh_token",
            expires_in=3600,
            provider="linkedin",
        )

        # Verify stored
        key = f"{store.sandbox_id}:linkedin_token:user123"
        assert key in mock_session.data

    @pytest.mark.asyncio
    async def test_get_external_token_success(self, mock_session):
        """Test getting external token successfully."""
        store = TokenStore()

        # Link token first
        await store.link_external_token(
            user_id="user123",
            access_token="external_token",
            expires_in=3600,
            provider="linkedin",
        )

        # Get it back
        result = await store.get_external_token("user123", provider="linkedin")

        assert result is not None
        assert result["access_token"] == "external_token"

    @pytest.mark.asyncio
    async def test_get_external_token_not_found(self, mock_session):
        """Test getting non-existent external token."""
        store = TokenStore()

        result = await store.get_external_token("nonexistent_user", provider="linkedin")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_external_token(self, mock_session):
        """Test updating external token."""
        store = TokenStore()

        # Link initial token
        await store.link_external_token(
            user_id="user123",
            access_token="old_token",
            expires_in=3600,
            provider="linkedin",
        )

        # Update it
        await store.update_external_token(
            user_id="user123",
            access_token="new_token",
            expires_in=7200,
            provider="linkedin",
        )

        # Verify updated
        result = await store.get_external_token("user123", provider="linkedin")
        assert result["access_token"] == "new_token"

    @pytest.mark.asyncio
    async def test_is_external_token_expired_false(self, mock_session):
        """Test checking if external token is not expired."""
        store = TokenStore()

        # Link token that expires in 1 hour
        await store.link_external_token(
            user_id="user123",
            access_token="token",
            expires_in=3600,
            provider="linkedin",
        )

        is_expired = await store.is_external_token_expired("user123", provider="linkedin")

        assert is_expired is False

    @pytest.mark.asyncio
    async def test_is_external_token_expired_true(self, mock_session):
        """Test checking if external token is expired."""
        store = TokenStore()

        # Link token with very short TTL (1 second)
        await store.link_external_token(
            user_id="user123",
            access_token="token",
            expires_in=1,
            provider="linkedin",
        )

        # Manually update the stored token to have an expired timestamp
        from chuk_mcp_server.oauth.token_models import ExternalTokenData

        expired_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        token_data = ExternalTokenData(
            access_token="token",
            expires_at=expired_time,
            expires_in=3600,
        )

        # Replace with expired token
        key = f"{store.sandbox_id}:linkedin_token:user123"
        mock_session.data[key] = token_data.to_json_bytes()

        is_expired = await store.is_external_token_expired("user123", provider="linkedin")

        assert is_expired is True

    @pytest.mark.asyncio
    async def test_is_external_token_expired_not_found(self, mock_session):
        """Test checking expiration of non-existent token."""
        store = TokenStore()

        is_expired = await store.is_external_token_expired("nonexistent", provider="linkedin")

        assert is_expired is True  # Should be considered expired if not found

    @pytest.mark.asyncio
    async def test_register_client(self, mock_session):
        """Test registering a new MCP client."""
        store = TokenStore()

        result = await store.register_client(
            client_name="Test Client",
            redirect_uris=["http://localhost/callback"],
        )

        assert "client_id" in result
        assert "client_secret" in result
        assert len(result["client_id"]) > 0
        assert len(result["client_secret"]) > 0

        # Verify stored
        client_id = result["client_id"]
        key = f"{store.sandbox_id}:client:{client_id}"
        assert key in mock_session.data

    @pytest.mark.asyncio
    async def test_validate_client_success(self, mock_session):
        """Test validating client credentials successfully."""
        store = TokenStore()

        # Register client first
        client_info = await store.register_client(
            client_name="Test Client",
            redirect_uris=["http://localhost/callback"],
        )

        # Validate it
        is_valid = await store.validate_client(
            client_id=client_info["client_id"],
            client_secret=client_info["client_secret"],
        )

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_client_wrong_secret(self, mock_session):
        """Test validating client with wrong secret."""
        store = TokenStore()

        client_info = await store.register_client(
            client_name="Test Client",
            redirect_uris=["http://localhost/callback"],
        )

        is_valid = await store.validate_client(
            client_id=client_info["client_id"],
            client_secret="wrong_secret",
        )

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_client_not_found(self, mock_session):
        """Test validating non-existent client."""
        store = TokenStore()

        is_valid = await store.validate_client(
            client_id="nonexistent_client",
            client_secret="secret",
        )

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_client_redirect_uri(self, mock_session):
        """Test validating client with redirect URI check."""
        store = TokenStore()

        client_info = await store.register_client(
            client_name="Test Client",
            redirect_uris=["http://localhost/callback", "http://localhost/callback2"],
        )

        # Valid redirect URI
        is_valid = await store.validate_client(
            client_id=client_info["client_id"],
            redirect_uri="http://localhost/callback",
        )
        assert is_valid is True

        # Invalid redirect URI
        is_valid = await store.validate_client(
            client_id=client_info["client_id"],
            redirect_uri="http://wrong/uri",
        )
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_client_without_secret(self, mock_session):
        """Test validating client without secret (public client)."""
        store = TokenStore()

        client_info = await store.register_client(
            client_name="Public Client",
            redirect_uris=["http://localhost/callback"],
        )

        # Validate without secret
        is_valid = await store.validate_client(
            client_id=client_info["client_id"],
        )

        assert is_valid is True


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
