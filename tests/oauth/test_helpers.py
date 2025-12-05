"""Tests for OAuth helper functions."""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestSetupGoogleDriveOAuth:
    """Tests for setup_google_drive_oauth helper."""

    @pytest.fixture
    def mock_mcp_server(self):
        """Create a mock MCP server."""
        server = MagicMock()
        server.name = "test-server"
        return server

    def test_no_credentials_returns_none(self, mock_mcp_server):
        """Test that function returns None when no credentials are provided."""
        from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

        # No credentials in params or environment
        with patch.dict(os.environ, {}, clear=True):
            result = setup_google_drive_oauth(mock_mcp_server)

        assert result is None

    def test_missing_client_id_returns_none(self, mock_mcp_server):
        """Test that function returns None when client_id is missing."""
        from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

        # Only client_secret, no client_id
        with patch.dict(os.environ, {"GOOGLE_CLIENT_SECRET": "secret"}, clear=True):
            result = setup_google_drive_oauth(mock_mcp_server)

        assert result is None

    def test_missing_client_secret_returns_none(self, mock_mcp_server):
        """Test that function returns None when client_secret is missing."""
        from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

        # Only client_id, no client_secret
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "id"}, clear=True):
            result = setup_google_drive_oauth(mock_mcp_server)

        assert result is None

    def test_credentials_from_environment(self, mock_mcp_server):
        """Test that credentials are read from environment variables."""
        from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

        with patch.dict(
            os.environ,
            {
                "GOOGLE_CLIENT_ID": "test-id",
                "GOOGLE_CLIENT_SECRET": "test-secret",
                "GOOGLE_REDIRECT_URI": "http://test/callback",
                "OAUTH_SERVER_URL": "http://test",
            },
            clear=True,
        ):
            # Mock the imports inside the function (they're dynamically imported)
            mock_provider_cls = Mock()
            mock_middleware_cls = Mock()
            mock_middleware_instance = Mock()
            mock_middleware_cls.return_value = mock_middleware_instance

            # Patch the module imports
            modules_patch = {
                "chuk_mcp_server.oauth.providers.google_drive": Mock(GoogleDriveOAuthProvider=mock_provider_cls),
                "chuk_mcp_server.oauth.middleware": Mock(OAuthMiddleware=mock_middleware_cls),
            }

            with patch.dict("sys.modules", modules_patch):
                result = setup_google_drive_oauth(mock_mcp_server)

                # Should return a function
                assert callable(result)

                # Call the hook to verify it works
                hook_result = result()

                # Verify GoogleDriveOAuthProvider was called with correct params
                mock_provider_cls.assert_called_once()
                call_kwargs = mock_provider_cls.call_args[1]
                assert call_kwargs["google_client_id"] == "test-id"
                assert call_kwargs["google_client_secret"] == "test-secret"
                assert call_kwargs["google_redirect_uri"] == "http://test/callback"
                assert call_kwargs["oauth_server_url"] == "http://test"

                # Verify OAuthMiddleware was called
                mock_middleware_cls.assert_called_once()

                # Should return the middleware instance
                assert hook_result == mock_middleware_instance

    def test_credentials_from_parameters(self, mock_mcp_server):
        """Test that credentials from parameters take precedence over environment."""
        from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

        with patch.dict(
            os.environ,
            {
                "GOOGLE_CLIENT_ID": "env-id",
                "GOOGLE_CLIENT_SECRET": "env-secret",
            },
            clear=True,
        ):
            mock_provider_cls = Mock()
            mock_middleware_cls = Mock()

            modules_patch = {
                "chuk_mcp_server.oauth.providers.google_drive": Mock(GoogleDriveOAuthProvider=mock_provider_cls),
                "chuk_mcp_server.oauth.middleware": Mock(OAuthMiddleware=mock_middleware_cls),
            }

            with patch.dict("sys.modules", modules_patch):
                result = setup_google_drive_oauth(
                    mock_mcp_server,
                    client_id="param-id",
                    client_secret="param-secret",
                )

                assert callable(result)
                result()

                # Verify parameters were used, not environment
                call_kwargs = mock_provider_cls.call_args[1]
                assert call_kwargs["google_client_id"] == "param-id"
                assert call_kwargs["google_client_secret"] == "param-secret"

    def test_default_redirect_uri_and_server_url(self, mock_mcp_server):
        """Test that default redirect_uri and oauth_server_url are used."""
        from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

        with patch.dict(
            os.environ,
            {
                "GOOGLE_CLIENT_ID": "test-id",
                "GOOGLE_CLIENT_SECRET": "test-secret",
            },
            clear=True,
        ):
            mock_provider_cls = Mock()
            mock_middleware_cls = Mock()

            modules_patch = {
                "chuk_mcp_server.oauth.providers.google_drive": Mock(GoogleDriveOAuthProvider=mock_provider_cls),
                "chuk_mcp_server.oauth.middleware": Mock(OAuthMiddleware=mock_middleware_cls),
            }

            with patch.dict("sys.modules", modules_patch):
                result = setup_google_drive_oauth(mock_mcp_server)

                assert callable(result)
                result()

                # Verify defaults were used
                call_kwargs = mock_provider_cls.call_args[1]
                assert call_kwargs["google_redirect_uri"] == "http://localhost:8000/oauth/callback"
                assert call_kwargs["oauth_server_url"] == "http://localhost:8000"

    def test_import_error_returns_none(self, mock_mcp_server):
        """Test that ImportError when loading dependencies returns None."""
        import sys

        from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

        with patch.dict(
            os.environ,
            {
                "GOOGLE_CLIENT_ID": "test-id",
                "GOOGLE_CLIENT_SECRET": "test-secret",
            },
            clear=True,
        ):
            # Remove the module to force ImportError
            original_modules = sys.modules.copy()
            if "chuk_mcp_server.oauth.providers.google_drive" in sys.modules:
                del sys.modules["chuk_mcp_server.oauth.providers.google_drive"]
            if "chuk_mcp_server.oauth.middleware" in sys.modules:
                del sys.modules["chuk_mcp_server.oauth.middleware"]

            # Mock import to fail
            def import_side_effect(name, *args, **kwargs):
                if "google_drive" in name or ("middleware" in name and "oauth" in name):
                    raise ImportError("test")
                return original_modules.get(name)

            with patch("builtins.__import__", side_effect=import_side_effect):
                result = setup_google_drive_oauth(mock_mcp_server)

                # Should return None when dependencies not installed
                assert result is None

            # Restore modules
            sys.modules.update(original_modules)


class TestConfigureStorageFromOAuth:
    """Tests for configure_storage_from_oauth helper."""

    def test_extracts_credentials_from_token_data(self):
        """Test that function extracts Google Drive credentials correctly."""
        from chuk_mcp_server.oauth.helpers import configure_storage_from_oauth

        token_data = {
            "external_access_token": "test-access-token",
            "external_refresh_token": "test-refresh-token",
            "user_id": "test-user-123",
        }

        with patch.dict(
            os.environ,
            {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-client-secret",
            },
            clear=True,
        ):
            result = configure_storage_from_oauth(token_data)

        assert "credentials" in result
        assert result["credentials"]["token"] == "test-access-token"
        assert result["credentials"]["refresh_token"] == "test-refresh-token"
        assert result["credentials"]["token_uri"] == "https://oauth2.googleapis.com/token"
        assert result["credentials"]["client_id"] == "test-client-id"
        assert result["credentials"]["client_secret"] == "test-client-secret"
        assert result["user_id"] == "test-user-123"
        assert result["root_folder"] == "CHUK"

    def test_uses_custom_root_folder_from_env(self):
        """Test that custom root folder from environment is used."""
        from chuk_mcp_server.oauth.helpers import configure_storage_from_oauth

        token_data = {
            "external_access_token": "test-access-token",
            "external_refresh_token": "test-refresh-token",
            "user_id": "test-user-123",
        }

        with patch.dict(
            os.environ,
            {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-client-secret",
                "GOOGLE_DRIVE_ROOT_FOLDER": "CustomFolder",
            },
            clear=True,
        ):
            result = configure_storage_from_oauth(token_data)

        assert result["root_folder"] == "CustomFolder"

    def test_includes_required_scopes(self):
        """Test that required Google Drive scopes are included."""
        from chuk_mcp_server.oauth.helpers import configure_storage_from_oauth

        token_data = {
            "external_access_token": "test-access-token",
            "external_refresh_token": "test-refresh-token",
        }

        with patch.dict(
            os.environ,
            {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-client-secret",
            },
            clear=True,
        ):
            result = configure_storage_from_oauth(token_data)

        scopes = result["credentials"]["scopes"]
        assert "https://www.googleapis.com/auth/drive.file" in scopes
        assert "https://www.googleapis.com/auth/userinfo.profile" in scopes
