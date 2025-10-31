"""Tests for OAuth TokenStore."""

import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch

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
        import base64

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
