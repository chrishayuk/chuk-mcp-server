"""Tests for BaseOAuthProvider abstract base class."""

import pytest

from chuk_mcp_server.oauth.base_provider import BaseOAuthProvider
from chuk_mcp_server.oauth.models import (
    AuthorizationParams,
    OAuthClientInfo,
    OAuthToken,
)


class TestBaseOAuthProvider:
    """Test BaseOAuthProvider abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test that BaseOAuthProvider cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseOAuthProvider()
        assert "abstract" in str(exc_info.value).lower()

    def test_subclass_must_implement_authorize(self):
        """Test that subclass must implement authorize method."""

        class IncompleteProvider(BaseOAuthProvider):
            async def exchange_authorization_code(self, code, client_id, redirect_uri, code_verifier=None):
                pass

            async def exchange_refresh_token(self, refresh_token, client_id, scope=None):
                pass

            async def register_client(self, client_name, client_metadata):
                pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_subclass_must_implement_exchange_code(self):
        """Test that subclass must implement exchange_authorization_code."""

        class IncompleteProvider(BaseOAuthProvider):
            async def authorize(self, params):
                pass

            async def exchange_refresh_token(self, refresh_token, client_id, scope=None):
                pass

            async def register_client(self, client_name, client_metadata):
                pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_subclass_must_implement_exchange_refresh(self):
        """Test that subclass must implement exchange_refresh_token."""

        class IncompleteProvider(BaseOAuthProvider):
            async def authorize(self, params):
                pass

            async def exchange_authorization_code(self, code, client_id, redirect_uri, code_verifier=None):
                pass

            async def register_client(self, client_name, client_metadata):
                pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_subclass_must_implement_register_client(self):
        """Test that subclass must implement register_client."""

        class IncompleteProvider(BaseOAuthProvider):
            async def authorize(self, params):
                pass

            async def exchange_authorization_code(self, code, client_id, redirect_uri, code_verifier=None):
                pass

            async def exchange_refresh_token(self, refresh_token, client_id, scope=None):
                pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_complete_subclass_can_be_instantiated(self):
        """Test that a complete subclass can be instantiated."""

        class CompleteProvider(BaseOAuthProvider):
            async def authorize(self, params):
                return {"code": "test_code"}

            async def exchange_authorization_code(self, code, client_id, redirect_uri, code_verifier=None):
                return OAuthToken(access_token="test_token")

            async def exchange_refresh_token(self, refresh_token, client_id, scope=None):
                return OAuthToken(access_token="new_token")

            async def validate_access_token(self, token):
                return {"user_id": "user123", "client_id": "client456"}

            async def register_client(self, client_metadata):
                return OAuthClientInfo(
                    client_id="test_client",
                    client_secret="test_secret",
                    client_name="Test Client",
                    redirect_uris=["http://localhost/callback"],
                )

            async def revoke_token(self, token, token_type_hint=None):
                return None

        provider = CompleteProvider()
        assert isinstance(provider, BaseOAuthProvider)

    @pytest.mark.asyncio
    async def test_complete_subclass_methods_work(self):
        """Test that complete subclass methods are callable."""

        class CompleteProvider(BaseOAuthProvider):
            async def authorize(self, params):
                return {"code": "auth_code_123"}

            async def exchange_authorization_code(self, code, client_id, redirect_uri, code_verifier=None):
                return OAuthToken(access_token="access_token_123")

            async def exchange_refresh_token(self, refresh_token, client_id, scope=None):
                return OAuthToken(access_token="new_access_token")

            async def validate_access_token(self, token):
                return {"user_id": "user123", "client_id": "client456", "token": token}

            async def register_client(self, client_metadata):
                return OAuthClientInfo(
                    client_id="client_123",
                    client_secret="secret_123",
                    client_name="Test Client",
                    redirect_uris=["http://localhost/callback"],
                )

            async def revoke_token(self, token, token_type_hint=None):
                return None

        provider = CompleteProvider()

        # Test authorize
        params = AuthorizationParams(
            response_type="code",
            client_id="test_client",
            redirect_uri="http://localhost/callback",
        )
        result = await provider.authorize(params)
        assert result["code"] == "auth_code_123"

        # Test exchange_authorization_code
        token = await provider.exchange_authorization_code(
            code="test_code",
            client_id="test_client",
            redirect_uri="http://localhost/callback",
        )
        assert token.access_token == "access_token_123"

        # Test exchange_refresh_token
        new_token = await provider.exchange_refresh_token(
            refresh_token="refresh_123",
            client_id="test_client",
        )
        assert new_token.access_token == "new_access_token"

        # Test validate_access_token
        token_data = await provider.validate_access_token("test_token_xyz")
        assert token_data["user_id"] == "user123"
        assert token_data["token"] == "test_token_xyz"

        # Test register_client
        client = await provider.register_client(
            client_metadata={"redirect_uris": ["http://localhost/callback"]},
        )
        assert client.client_id == "client_123"

        # Test revoke_token (optional method)
        result = await provider.revoke_token("token_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_token_default_implementation(self):
        """Test that default revoke_token returns None."""

        class MinimalProvider(BaseOAuthProvider):
            async def authorize(self, params):
                return {"code": "test"}

            async def exchange_authorization_code(self, code, client_id, redirect_uri, code_verifier=None):
                return OAuthToken(access_token="test")

            async def exchange_refresh_token(self, refresh_token, client_id, scope=None):
                return OAuthToken(access_token="test")

            async def validate_access_token(self, token):
                return {"user_id": "test"}

            async def register_client(self, client_metadata):
                return OAuthClientInfo(
                    client_id="test",
                    client_secret="secret",
                    client_name="Test",
                    redirect_uris=["http://localhost"],
                )

        provider = MinimalProvider()

        # Test default revoke_token implementation
        result = await provider.revoke_token("token_123")
        assert result is None

        # Test with token_type_hint
        result = await provider.revoke_token("token_456", token_type_hint="access_token")
        assert result is None
