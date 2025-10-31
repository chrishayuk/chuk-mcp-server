"""Tests for OAuth models."""

from chuk_mcp_server.oauth.models import (
    AuthorizationParams,
    AuthorizeError,
    OAuthClientInfo,
    OAuthError,
    OAuthToken,
    RegistrationError,
    TokenError,
)


class TestAuthorizationParams:
    """Test AuthorizationParams dataclass."""

    def test_authorization_params_basic(self):
        """Test basic AuthorizationParams creation."""
        params = AuthorizationParams(
            response_type="code",
            client_id="test_client",
            redirect_uri="http://localhost/callback",
        )
        assert params.response_type == "code"
        assert params.client_id == "test_client"
        assert params.redirect_uri == "http://localhost/callback"
        assert params.scope is None
        assert params.state is None
        assert params.code_challenge is None
        assert params.code_challenge_method is None

    def test_authorization_params_with_pkce(self):
        """Test AuthorizationParams with PKCE."""
        params = AuthorizationParams(
            response_type="code",
            client_id="test_client",
            redirect_uri="http://localhost/callback",
            code_challenge="test_challenge",
            code_challenge_method="S256",
        )
        assert params.code_challenge == "test_challenge"
        assert params.code_challenge_method == "S256"

    def test_authorization_params_with_state(self):
        """Test AuthorizationParams with state."""
        params = AuthorizationParams(
            response_type="code",
            client_id="test_client",
            redirect_uri="http://localhost/callback",
            state="random_state",
            scope="read write",
        )
        assert params.state == "random_state"
        assert params.scope == "read write"


class TestOAuthToken:
    """Test OAuthToken dataclass."""

    def test_oauth_token_basic(self):
        """Test basic OAuthToken creation."""
        token = OAuthToken(access_token="test_access_token")
        assert token.access_token == "test_access_token"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600
        assert token.refresh_token is None
        assert token.scope is None

    def test_oauth_token_with_refresh(self):
        """Test OAuthToken with refresh token."""
        token = OAuthToken(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_in=7200,
            scope="read write",
        )
        assert token.refresh_token == "test_refresh_token"
        assert token.expires_in == 7200
        assert token.scope == "read write"

    def test_oauth_token_custom_type(self):
        """Test OAuthToken with custom token type."""
        token = OAuthToken(access_token="test_token", token_type="MAC")
        assert token.token_type == "MAC"


class TestOAuthClientInfo:
    """Test OAuthClientInfo dataclass."""

    def test_oauth_client_info(self):
        """Test OAuthClientInfo creation."""
        client = OAuthClientInfo(
            client_id="test_client_id",
            client_secret="test_client_secret",
            client_name="Test Client",
            redirect_uris=["http://localhost/callback"],
        )
        assert client.client_id == "test_client_id"
        assert client.client_secret == "test_client_secret"
        assert client.client_name == "Test Client"
        assert client.redirect_uris == ["http://localhost/callback"]

    def test_oauth_client_info_multiple_uris(self):
        """Test OAuthClientInfo with multiple redirect URIs."""
        uris = ["http://localhost/callback1", "http://localhost/callback2"]
        client = OAuthClientInfo(
            client_id="client",
            client_secret="secret",
            client_name="Client",
            redirect_uris=uris,
        )
        assert len(client.redirect_uris) == 2
        assert client.redirect_uris == uris


class TestOAuthErrors:
    """Test OAuth error classes."""

    def test_oauth_error_basic(self):
        """Test basic OAuthError."""
        error = OAuthError("invalid_request")
        assert error.error == "invalid_request"
        assert error.error_description is None
        assert str(error) == "invalid_request"

    def test_oauth_error_with_description(self):
        """Test OAuthError with description."""
        error = OAuthError("invalid_request", "Missing required parameter")
        assert error.error == "invalid_request"
        assert error.error_description == "Missing required parameter"
        assert str(error) == "invalid_request: Missing required parameter"

    def test_authorize_error(self):
        """Test AuthorizeError."""
        error = AuthorizeError("access_denied", "User denied access")
        assert isinstance(error, OAuthError)
        assert error.error == "access_denied"
        assert error.error_description == "User denied access"

    def test_token_error(self):
        """Test TokenError."""
        error = TokenError("invalid_grant", "Authorization code is invalid")
        assert isinstance(error, OAuthError)
        assert error.error == "invalid_grant"
        assert error.error_description == "Authorization code is invalid"

    def test_registration_error(self):
        """Test RegistrationError."""
        error = RegistrationError("invalid_redirect_uri", "Invalid redirect URI")
        assert isinstance(error, OAuthError)
        assert error.error == "invalid_redirect_uri"
        assert error.error_description == "Invalid redirect URI"

    def test_error_inheritance(self):
        """Test that all errors inherit from OAuthError."""
        assert issubclass(AuthorizeError, OAuthError)
        assert issubclass(TokenError, OAuthError)
        assert issubclass(RegistrationError, OAuthError)
