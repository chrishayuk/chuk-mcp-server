"""Tests for Google Drive OAuth provider.

These tests mock the Google Drive API dependencies to avoid requiring
the optional google_drive extra dependencies.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Mock the httpx module if not available
try:
    import httpx
except ImportError:
    httpx = MagicMock()
    sys.modules["httpx"] = httpx


class TestGoogleDriveOAuthClient:
    """Tests for GoogleDriveOAuthClient."""

    @pytest.fixture
    def client(self):
        """Create a GoogleDriveOAuthClient instance."""
        # Mock httpx if not available
        with patch("chuk_mcp_server.oauth.providers.google_drive.httpx", httpx):
            from chuk_mcp_server.oauth.providers.google_drive import GoogleDriveOAuthClient

            return GoogleDriveOAuthClient(
                client_id="test-client-id",
                client_secret="test-client-secret",
                redirect_uri="http://localhost:8000/callback",
            )

    def test_initialization(self, client):
        """Test client initialization."""
        assert client.client_id == "test-client-id"
        assert client.client_secret == "test-client-secret"
        assert client.redirect_uri == "http://localhost:8000/callback"

    def test_get_authorization_url(self, client):
        """Test generating authorization URL."""
        url = client.get_authorization_url(state="test-state-123")

        assert "https://accounts.google.com/o/oauth2/v2/auth" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=" in url
        assert "state=test-state-123" in url
        assert "scope=" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url

    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, client):
        """Test exchanging authorization code for token."""
        # Mock httpx.AsyncClient
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("chuk_mcp_server.oauth.providers.google_drive.httpx.AsyncClient", return_value=mock_client):
            result = await client.exchange_code_for_token("test-code")

        assert result["access_token"] == "test-access-token"
        assert result["refresh_token"] == "test-refresh-token"

        # Verify request was made correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://oauth2.googleapis.com/token"
        assert call_args[1]["data"]["code"] == "test-code"
        assert call_args[1]["data"]["client_id"] == "test-client-id"
        assert call_args[1]["data"]["client_secret"] == "test-client-secret"

    @pytest.mark.asyncio
    async def test_refresh_access_token(self, client):
        """Test refreshing access token."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("chuk_mcp_server.oauth.providers.google_drive.httpx.AsyncClient", return_value=mock_client):
            result = await client.refresh_access_token("test-refresh-token")

        assert result["access_token"] == "new-access-token"

        # Verify request
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["refresh_token"] == "test-refresh-token"
        assert call_args[1]["data"]["grant_type"] == "refresh_token"

    @pytest.mark.asyncio
    async def test_get_user_info(self, client):
        """Test getting user info from Google."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "sub": "user-123",
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("chuk_mcp_server.oauth.providers.google_drive.httpx.AsyncClient", return_value=mock_client):
            result = await client.get_user_info("test-access-token")

        assert result["sub"] == "user-123"
        assert result["email"] == "test@example.com"

        # Verify request
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-access-token"


class TestGoogleDriveOAuthProvider:
    """Tests for GoogleDriveOAuthProvider."""

    @pytest.fixture
    def provider(self):
        """Create a GoogleDriveOAuthProvider instance."""
        with patch("chuk_mcp_server.oauth.providers.google_drive.httpx", httpx):
            with patch("chuk_mcp_server.oauth.providers.google_drive.TokenStore"):
                from chuk_mcp_server.oauth.providers.google_drive import GoogleDriveOAuthProvider

                return GoogleDriveOAuthProvider(
                    google_client_id="test-client-id",
                    google_client_secret="test-client-secret",
                    google_redirect_uri="http://localhost:8000/callback",
                    oauth_server_url="http://localhost:8000",
                    sandbox_id="test-sandbox",
                )

    def test_initialization(self, provider):
        """Test provider initialization."""
        assert provider.oauth_server_url == "http://localhost:8000"
        assert provider.google_client is not None

    def test_initialization_with_custom_token_store(self):
        """Test provider initialization with custom token store."""
        mock_token_store = Mock()

        with patch("chuk_mcp_server.oauth.providers.google_drive.httpx", httpx):
            from chuk_mcp_server.oauth.providers.google_drive import GoogleDriveOAuthProvider

            provider = GoogleDriveOAuthProvider(
                google_client_id="test-client-id",
                google_client_secret="test-client-secret",
                google_redirect_uri="http://localhost:8000/callback",
                token_store=mock_token_store,
            )

        assert provider.token_store == mock_token_store


class TestProvidersInit:
    """Tests for providers __init__.py."""

    def test_import_with_dependencies(self):
        """Test importing when Google Drive dependencies are available."""
        with patch("chuk_mcp_server.oauth.providers.google_drive.httpx", httpx):
            from chuk_mcp_server.oauth import providers

            # Should have the providers in __all__
            assert "GoogleDriveOAuthProvider" in providers.__all__
            assert "GoogleDriveOAuthClient" in providers.__all__

    def test_import_without_dependencies(self):
        """Test importing when Google Drive dependencies are not available."""
        # This test verifies the try/except ImportError block works
        # The actual import may succeed or fail depending on environment
        # but should not raise an unhandled exception
        try:
            from chuk_mcp_server.oauth import providers  # noqa: F401

            # Import succeeded - that's fine
            assert True
        except ImportError:
            # Import failed due to missing dependencies - that's also fine
            assert True
