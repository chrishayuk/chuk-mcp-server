"""Tests for OAuth __init__ module exports."""


class TestOAuthInit:
    """Test OAuth module initialization and exports."""

    def test_imports_base_provider(self):
        """Test that BaseOAuthProvider is importable."""
        from chuk_mcp_server.oauth import BaseOAuthProvider

        assert BaseOAuthProvider is not None

    def test_imports_base_token_store(self):
        """Test that BaseTokenStore is importable."""
        from chuk_mcp_server.oauth import BaseTokenStore

        assert BaseTokenStore is not None

    def test_imports_middleware(self):
        """Test that OAuthMiddleware is importable."""
        from chuk_mcp_server.oauth import OAuthMiddleware

        assert OAuthMiddleware is not None

    def test_imports_models(self):
        """Test that model classes are importable."""
        from chuk_mcp_server.oauth import (
            AuthorizationParams,
            AuthorizeError,
            OAuthClientInfo,
            OAuthToken,
            RegistrationError,
            TokenError,
        )

        assert AuthorizationParams is not None
        assert OAuthToken is not None
        assert OAuthClientInfo is not None
        assert AuthorizeError is not None
        assert TokenError is not None
        assert RegistrationError is not None

    def test_imports_token_store(self):
        """Test that TokenStore is importable."""
        from chuk_mcp_server.oauth import TokenStore

        assert TokenStore is not None

    def test_all_exports(self):
        """Test __all__ contains expected exports."""
        from chuk_mcp_server import oauth

        expected = [
            "OAuthMiddleware",
            "AuthorizationParams",
            "OAuthToken",
            "OAuthClientInfo",
            "AuthorizeError",
            "TokenError",
            "RegistrationError",
            "TokenStore",
            "BaseOAuthProvider",
            "BaseTokenStore",
        ]
        for item in expected:
            assert item in oauth.__all__
            assert hasattr(oauth, item)

    def test_module_docstring(self):
        """Test that module has documentation."""
        from chuk_mcp_server import oauth

        assert oauth.__doc__ is not None
        assert "OAuth 2.1" in oauth.__doc__
        assert "PKCE" in oauth.__doc__
