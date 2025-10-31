"""Tests for OAuth token models using dataclasses."""

from datetime import datetime, timedelta

import pytest

from chuk_mcp_server.oauth.token_models import (
    AccessTokenData,
    AuthorizationCodeData,
    ClientData,
    ExternalTokenData,
    RefreshTokenData,
)


class TestAuthorizationCodeData:
    """Test AuthorizationCodeData model."""

    def test_authorization_code_data_basic(self):
        """Test basic AuthorizationCodeData creation."""
        data = AuthorizationCodeData(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
        )
        assert data.user_id == "user123"
        assert data.client_id == "client456"
        assert data.redirect_uri == "http://localhost/callback"
        assert data.scope is None
        assert data.code_challenge is None
        assert data.code_challenge_method is None
        assert data.created_at is not None

    def test_authorization_code_data_with_pkce(self):
        """Test AuthorizationCodeData with PKCE."""
        data = AuthorizationCodeData(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
            code_challenge="challenge123",
            code_challenge_method="S256",
            scope="read write",
        )
        assert data.code_challenge == "challenge123"
        assert data.code_challenge_method == "S256"
        assert data.scope == "read write"

    def test_authorization_code_data_created_at(self):
        """Test that created_at is set automatically."""
        data = AuthorizationCodeData(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
        )
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(data.created_at)

    def test_authorization_code_data_to_dict(self):
        """Test converting to dictionary."""
        data = AuthorizationCodeData(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
            scope="read",
        )
        result = data.to_dict()
        assert result["user_id"] == "user123"
        assert result["client_id"] == "client456"
        assert result["scope"] == "read"

    def test_authorization_code_data_to_json_bytes(self):
        """Test orjson serialization."""
        data = AuthorizationCodeData(
            user_id="user123",
            client_id="client456",
            redirect_uri="http://localhost/callback",
        )
        json_bytes = data.to_json_bytes()
        assert isinstance(json_bytes, bytes)

    def test_authorization_code_data_from_dict(self):
        """Test creating from dictionary."""
        dict_data = {
            "user_id": "user123",
            "client_id": "client456",
            "redirect_uri": "http://localhost/callback",
            "scope": "read write",
        }
        data = AuthorizationCodeData.from_dict(dict_data)
        assert data.user_id == "user123"
        assert data.scope == "read write"


class TestAccessTokenData:
    """Test AccessTokenData model."""

    def test_access_token_data_basic(self):
        """Test basic AccessTokenData creation."""
        data = AccessTokenData(
            user_id="user123",
            client_id="client456",
        )
        assert data.user_id == "user123"
        assert data.client_id == "client456"
        assert data.scope is None
        assert data.created_at is not None

    def test_access_token_data_with_scope(self):
        """Test AccessTokenData with scope."""
        data = AccessTokenData(
            user_id="user123",
            client_id="client456",
            scope="read write",
        )
        assert data.scope == "read write"

    def test_access_token_data_created_at(self):
        """Test that created_at is set automatically."""
        data = AccessTokenData(
            user_id="user123",
            client_id="client456",
        )
        datetime.fromisoformat(data.created_at)

    def test_access_token_data_to_dict(self):
        """Test converting to dictionary."""
        data = AccessTokenData(
            user_id="user123",
            client_id="client456",
            scope="read",
        )
        result = data.to_dict()
        assert result["user_id"] == "user123"
        assert result["scope"] == "read"

    def test_access_token_data_from_dict(self):
        """Test creating from dictionary."""
        dict_data = {
            "user_id": "user123",
            "client_id": "client456",
            "scope": "read",
        }
        data = AccessTokenData.from_dict(dict_data)
        assert data.user_id == "user123"
        assert data.scope == "read"


class TestRefreshTokenData:
    """Test RefreshTokenData model."""

    def test_refresh_token_data_basic(self):
        """Test basic RefreshTokenData creation."""
        data = RefreshTokenData(
            user_id="user123",
            client_id="client456",
            access_token="access123",
        )
        assert data.user_id == "user123"
        assert data.client_id == "client456"
        assert data.access_token == "access123"
        assert data.scope is None
        assert data.created_at is not None

    def test_refresh_token_data_with_scope(self):
        """Test RefreshTokenData with scope."""
        data = RefreshTokenData(
            user_id="user123",
            client_id="client456",
            access_token="access123",
            scope="read write",
        )
        assert data.scope == "read write"

    def test_refresh_token_data_to_dict(self):
        """Test converting to dictionary."""
        data = RefreshTokenData(
            user_id="user123",
            client_id="client456",
            access_token="access123",
            scope="read",
        )
        result = data.to_dict()
        assert result["user_id"] == "user123"
        assert result["access_token"] == "access123"

    def test_refresh_token_data_from_dict(self):
        """Test creating from dictionary."""
        dict_data = {
            "user_id": "user123",
            "client_id": "client456",
            "access_token": "access123",
            "scope": "read",
        }
        data = RefreshTokenData.from_dict(dict_data)
        assert data.access_token == "access123"


class TestExternalTokenData:
    """Test ExternalTokenData model."""

    def test_external_token_data_basic(self):
        """Test basic ExternalTokenData creation."""
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        data = ExternalTokenData(
            access_token="external_token_123",
            expires_at=expires_at,
            expires_in=3600,
        )
        assert data.access_token == "external_token_123"
        assert data.refresh_token is None
        assert data.expires_in == 3600
        assert data.created_at is not None

    def test_external_token_data_with_refresh(self):
        """Test ExternalTokenData with refresh token."""
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        data = ExternalTokenData(
            access_token="access123",
            refresh_token="refresh456",
            expires_at=expires_at,
            expires_in=3600,
        )
        assert data.refresh_token == "refresh456"

    def test_external_token_data_invalid_expires_at(self):
        """Test ExternalTokenData with invalid expires_at."""
        with pytest.raises(ValueError) as exc_info:
            ExternalTokenData(
                access_token="token",
                expires_at="invalid-timestamp",
                expires_in=3600,
            )
        assert "expires_at must be valid ISO format timestamp" in str(exc_info.value)

    def test_external_token_data_invalid_expires_in(self):
        """Test ExternalTokenData with invalid expires_in."""
        expires_at = datetime.now().isoformat()
        with pytest.raises(ValueError) as exc_info:
            ExternalTokenData(
                access_token="token",
                expires_at=expires_at,
                expires_in=0,  # Must be > 0
            )
        assert "expires_in must be positive" in str(exc_info.value)

    def test_external_token_data_negative_expires_in(self):
        """Test ExternalTokenData with negative expires_in."""
        expires_at = datetime.now().isoformat()
        with pytest.raises(ValueError):
            ExternalTokenData(
                access_token="token",
                expires_at=expires_at,
                expires_in=-100,
            )

    def test_external_token_is_expired_true(self):
        """Test is_expired returns True for expired token."""
        # Token expired 10 minutes ago
        expires_at = (datetime.now() - timedelta(minutes=10)).isoformat()
        data = ExternalTokenData(
            access_token="token",
            expires_at=expires_at,
            expires_in=3600,
        )
        assert data.is_expired() is True

    def test_external_token_is_expired_false(self):
        """Test is_expired returns False for valid token."""
        # Token expires in 1 hour
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        data = ExternalTokenData(
            access_token="token",
            expires_at=expires_at,
            expires_in=3600,
        )
        assert data.is_expired() is False

    def test_external_token_is_expired_with_buffer(self):
        """Test is_expired with buffer time."""
        # Token expires in 3 minutes
        expires_at = (datetime.now() + timedelta(minutes=3)).isoformat()
        data = ExternalTokenData(
            access_token="token",
            expires_at=expires_at,
            expires_in=3600,
        )
        # Default buffer is 5 minutes, so should be considered expired
        assert data.is_expired() is True
        # With 1 minute buffer, should not be expired
        assert data.is_expired(buffer_minutes=1) is False

    def test_external_token_data_to_dict(self):
        """Test converting to dictionary."""
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        data = ExternalTokenData(
            access_token="token123",
            expires_at=expires_at,
            expires_in=3600,
            refresh_token="refresh123",
        )
        result = data.to_dict()
        assert result["access_token"] == "token123"
        assert result["refresh_token"] == "refresh123"

    def test_external_token_data_from_dict(self):
        """Test creating from dictionary."""
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        dict_data = {
            "access_token": "token123",
            "expires_at": expires_at,
            "expires_in": 3600,
            "refresh_token": "refresh123",
        }
        data = ExternalTokenData.from_dict(dict_data)
        assert data.access_token == "token123"
        assert data.refresh_token == "refresh123"


class TestClientData:
    """Test ClientData model."""

    def test_client_data_basic(self):
        """Test basic ClientData creation."""
        data = ClientData(
            client_name="Test Client",
            client_secret="secret123",
            redirect_uris=["http://localhost/callback"],
        )
        assert data.client_name == "Test Client"
        assert data.client_secret == "secret123"
        assert data.redirect_uris == ["http://localhost/callback"]
        assert data.created_at is not None

    def test_client_data_multiple_uris(self):
        """Test ClientData with multiple redirect URIs."""
        uris = ["http://localhost/callback1", "http://localhost/callback2"]
        data = ClientData(
            client_name="Test Client",
            client_secret="secret123",
            redirect_uris=uris,
        )
        assert len(data.redirect_uris) == 2
        assert data.redirect_uris == uris

    def test_client_data_empty_name(self):
        """Test ClientData with empty name."""
        with pytest.raises(ValueError) as exc_info:
            ClientData(
                client_name="",
                client_secret="secret123",
                redirect_uris=["http://localhost/callback"],
            )
        assert "client_name must not be empty" in str(exc_info.value)

    def test_client_data_whitespace_name(self):
        """Test ClientData with whitespace-only name."""
        with pytest.raises(ValueError):
            ClientData(
                client_name="   ",
                client_secret="secret123",
                redirect_uris=["http://localhost/callback"],
            )

    def test_client_data_empty_redirect_uris(self):
        """Test ClientData with empty redirect_uris."""
        with pytest.raises(ValueError) as exc_info:
            ClientData(
                client_name="Test Client",
                client_secret="secret123",
                redirect_uris=[],
            )
        assert "At least one redirect URI is required" in str(exc_info.value)

    def test_client_data_empty_uri_string(self):
        """Test ClientData with empty URI string."""
        with pytest.raises(ValueError) as exc_info:
            ClientData(
                client_name="Test Client",
                client_secret="secret123",
                redirect_uris=["http://localhost/callback", "  "],
            )
        assert "Redirect URIs cannot be empty" in str(exc_info.value)

    def test_client_data_to_dict(self):
        """Test converting to dictionary."""
        data = ClientData(
            client_name="Test Client",
            client_secret="secret123",
            redirect_uris=["http://localhost/callback"],
        )
        result = data.to_dict()
        assert result["client_name"] == "Test Client"
        assert result["client_secret"] == "secret123"

    def test_client_data_from_dict(self):
        """Test creating from dictionary."""
        dict_data = {
            "client_name": "Test Client",
            "client_secret": "secret123",
            "redirect_uris": ["http://localhost/callback"],
        }
        data = ClientData.from_dict(dict_data)
        assert data.client_name == "Test Client"
        assert len(data.redirect_uris) == 1
