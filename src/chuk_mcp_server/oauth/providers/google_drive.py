"""Google Drive OAuth provider for chuk-mcp-server.

Provides OAuth 2.0 integration with Google Drive API for MCP servers.
Can be used by any MCP server that needs Google Drive storage or access.

Usage:
    from chuk_mcp_server.oauth.providers import GoogleDriveOAuthProvider

    provider = GoogleDriveOAuthProvider(
        google_client_id="your_client_id",
        google_client_secret="your_client_secret",
        google_redirect_uri="http://localhost:8000/oauth/callback",
    )
"""

import logging
from typing import Any

import httpx

from ..base_provider import BaseOAuthProvider
from ..models import (
    AuthorizationParams,
    AuthorizeError,
    OAuthClientInfo,
    OAuthToken,
    RegistrationError,
    TokenError,
)
from ..token_store import TokenStore

logger = logging.getLogger(__name__)


class GoogleDriveOAuthClient:
    """Google Drive OAuth 2.0 client.

    Handles OAuth flow with Google Drive API.
    """

    # Google OAuth endpoints
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    # Required scopes for Drive access
    SCOPES = [
        "https://www.googleapis.com/auth/drive.file",  # Create and access own files
        "https://www.googleapis.com/auth/userinfo.profile",  # Get user ID
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ):
        """Initialize Google Drive OAuth client.

        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            redirect_uri: OAuth callback URL
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL.

        Args:
            state: State parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent to get refresh token
        }

        # Build URL manually to avoid encoding issues
        query_string = "&".join(f"{k}={httpx.QueryParams({k: v}).get(k)}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Google

        Returns:
            Token response with access_token, refresh_token, etc.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Google refresh token

        Returns:
            New token response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Get user info from Google.

        Args:
            access_token: Google access token

        Returns:
            User info with 'sub' (user ID), 'email', 'name', etc.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result


class GoogleDriveOAuthProvider(BaseOAuthProvider):
    """OAuth Authorization Server for MCP clients with Google Drive integration.

    This provider:
    - Authenticates MCP clients
    - Links MCP users to Google Drive accounts
    - Manages token lifecycle for both layers
    - Auto-refreshes Google Drive tokens

    Can be used by any MCP server that needs Google Drive access.
    """

    def __init__(
        self,
        google_client_id: str,
        google_client_secret: str,
        google_redirect_uri: str,
        oauth_server_url: str = "http://localhost:8000",
        sandbox_id: str = "default",
        token_store: Any | None = None,
    ):
        """Initialize OAuth provider.

        Args:
            google_client_id: Google OAuth client ID
            google_client_secret: Google OAuth client secret
            google_redirect_uri: Google OAuth callback URL
            oauth_server_url: This OAuth server's base URL
            sandbox_id: Sandbox ID for chuk-sessions isolation
            token_store: Token store instance (if None, creates default TokenStore)
        """
        self.oauth_server_url = oauth_server_url

        # Use provided token store or create default one
        if token_store is not None:
            self.token_store = token_store
        else:
            self.token_store = TokenStore(sandbox_id=sandbox_id)

        self.google_client = GoogleDriveOAuthClient(
            client_id=google_client_id,
            client_secret=google_client_secret,
            redirect_uri=google_redirect_uri,
        )

        # Track ongoing authorization flows
        self._pending_authorizations: dict[str, dict[str, Any]] = {}

    # ============================================================================
    # MCP OAuth Server Implementation
    # ============================================================================

    async def authorize(
        self,
        params: AuthorizationParams,
    ) -> dict[str, Any]:
        """Handle authorization request from MCP client.

        If user doesn't have Google Drive token, initiates Google OAuth flow.
        Otherwise, returns authorization code directly.

        Args:
            params: Authorization parameters from MCP client

        Returns:
            Dict with authorization_code or redirect information
        """
        # Validate client
        if not await self.token_store.validate_client(
            params.client_id,
            redirect_uri=params.redirect_uri,
        ):
            raise AuthorizeError(
                error="invalid_client",
                error_description="Invalid client_id or redirect_uri",
            )

        # Generate state for this authorization flow
        state = params.state or ""

        # Check if we have a Google Drive token for this state
        user_id = self._pending_authorizations.get(state, {}).get("user_id")

        if user_id:
            # User already linked to Google Drive
            google_token = await self.token_store.get_external_token(user_id, "google_drive")

            if google_token and not await self.token_store.is_external_token_expired(user_id, "google_drive"):
                # Have valid Google Drive token, create authorization code
                code = await self.token_store.create_authorization_code(
                    user_id=user_id,
                    client_id=params.client_id,
                    redirect_uri=params.redirect_uri,
                    scope=params.scope,
                    code_challenge=params.code_challenge,
                    code_challenge_method=params.code_challenge_method,
                )

                # Clean up pending authorization
                if state in self._pending_authorizations:
                    del self._pending_authorizations[state]

                return {
                    "code": code,
                    "state": state,
                }

        # Need Google Drive authorization - redirect to Google
        import secrets

        google_state = secrets.token_urlsafe(32)
        self._pending_authorizations[google_state] = {
            "mcp_client_id": params.client_id,
            "mcp_redirect_uri": params.redirect_uri,
            "mcp_state": state,
            "mcp_scope": params.scope,
            "mcp_code_challenge": params.code_challenge,
            "mcp_code_challenge_method": params.code_challenge_method,
        }

        google_auth_url = self.google_client.get_authorization_url(state=google_state)

        logger.debug(f"🔗 Generated Google authorization URL: {google_auth_url}")
        logger.debug(f"🔗 Google redirect_uri configured as: {self.google_client.redirect_uri}")
        logger.info("🔗 Redirecting to Google Drive for authorization")

        return {
            "authorization_url": google_auth_url,
            "state": google_state,
            "requires_external_authorization": True,
        }

    async def exchange_authorization_code(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> OAuthToken:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code
            client_id: MCP client ID
            redirect_uri: Redirect URI (must match)
            code_verifier: PKCE code verifier

        Returns:
            OAuth token with access_token and refresh_token
        """
        logger.info("🔄 Exchanging authorization code for access token")
        logger.debug(f"Authorization code (redacted): {code[:8]}...")

        # Validate authorization code
        code_data = await self.token_store.validate_authorization_code(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
        )

        if not code_data:
            logger.error("❌ Authorization code validation failed")
            raise TokenError(
                error="invalid_grant",
                error_description="Invalid or expired authorization code",
            )

        logger.info("✓ Authorization code validated successfully")
        logger.debug(f"User ID: {code_data['user_id']}")

        # Create access token and refresh token
        access_token, refresh_token = await self.token_store.create_access_token(
            user_id=code_data["user_id"],
            client_id=client_id,
            scope=code_data["scope"],
        )

        logger.info("✓ Created access token successfully (expires in 3600s)")

        return OAuthToken(
            access_token=access_token,
            token_type="Bearer",
            expires_in=3600,  # 1 hour
            refresh_token=refresh_token,
            scope=code_data["scope"],
        )

    async def exchange_refresh_token(
        self,
        refresh_token: str,
        client_id: str,
        scope: str | None = None,
    ) -> OAuthToken:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token
            client_id: MCP client ID
            scope: Optional scope (must be subset of original)

        Returns:
            New OAuth token
        """
        result = await self.token_store.refresh_access_token(refresh_token)

        if not result:
            raise TokenError(
                error="invalid_grant",
                error_description="Invalid refresh token",
            )

        new_access_token, new_refresh_token = result

        return OAuthToken(
            access_token=new_access_token,
            token_type="Bearer",
            expires_in=3600,
            refresh_token=new_refresh_token,
            scope=scope,
        )

    async def validate_access_token(
        self,
        token: str,
    ) -> dict[str, Any]:
        """Validate and load access token.

        Also checks Google Drive token and refreshes if needed.

        Args:
            token: MCP access token

        Returns:
            Token data with user_id and Google Drive token
        """
        logger.info("🔍 Validating access token")
        logger.debug(f"Access token (redacted): {token[:8]}...")

        # Validate MCP token
        token_data = await self.token_store.validate_access_token(token)
        if not token_data:
            logger.error(
                f"❌ Token validation failed: token not found in store (sandbox_id: {self.token_store.sandbox_id})"
            )
            raise TokenError(
                error="invalid_token",
                error_description="Invalid or expired access token",
            )

        logger.info("✓ Access token validated successfully")
        logger.debug(f"User ID: {token_data.get('user_id')}")

        user_id = token_data["user_id"]

        # Get Google Drive token
        google_token_data = await self.token_store.get_external_token(user_id, "google_drive")
        if not google_token_data:
            raise TokenError(
                error="insufficient_scope",
                error_description="Google Drive account not linked",
            )

        # Check if Google Drive token needs refresh
        if await self.token_store.is_external_token_expired(user_id, "google_drive"):
            # Refresh Google Drive token
            refresh_token = google_token_data.get("refresh_token")
            if refresh_token:
                try:
                    new_token = await self.google_client.refresh_access_token(refresh_token)
                    await self.token_store.update_external_token(
                        user_id=user_id,
                        access_token=new_token["access_token"],
                        refresh_token=new_token.get("refresh_token", refresh_token),
                        expires_in=new_token.get("expires_in", 3600),
                        provider="google_drive",
                    )
                    google_token_data = await self.token_store.get_external_token(user_id, "google_drive")
                except Exception as e:
                    raise TokenError(
                        error="invalid_token",
                        error_description=f"Failed to refresh Google Drive token: {e}",
                    )
            else:
                raise TokenError(
                    error="invalid_token",
                    error_description="Google Drive token expired and no refresh token available",
                )

        return {
            **token_data,
            "external_access_token": google_token_data["access_token"],
            "external_refresh_token": google_token_data.get("refresh_token"),
        }

    async def register_client(
        self,
        client_metadata: dict[str, Any],
    ) -> OAuthClientInfo:
        """Register a new MCP client.

        Args:
            client_metadata: Client registration metadata

        Returns:
            Client information with credentials
        """
        client_name = client_metadata.get("client_name", "Unknown Client")
        redirect_uris = client_metadata.get("redirect_uris", [])

        if not redirect_uris:
            raise RegistrationError(
                error="invalid_redirect_uri",
                error_description="At least one redirect URI required",
            )

        credentials = await self.token_store.register_client(
            client_name=client_name,
            redirect_uris=redirect_uris,
        )

        return OAuthClientInfo(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            client_name=client_name,
            redirect_uris=redirect_uris,
        )

    # ============================================================================
    # External OAuth Callback Handler
    # ============================================================================

    async def handle_external_callback(
        self,
        code: str,
        state: str,
    ) -> dict[str, Any]:
        """Handle Google Drive OAuth callback.

        This completes the Google OAuth flow and creates MCP authorization code.

        Args:
            code: Google authorization code
            state: State parameter (links to pending authorization)

        Returns:
            Dict with MCP authorization code and redirect info
        """
        # Get pending authorization
        pending = self._pending_authorizations.get(state)
        if not pending:
            raise ValueError("Invalid or expired state parameter")

        # Exchange Google code for token
        try:
            google_token = await self.google_client.exchange_code_for_token(code)
        except Exception as e:
            raise ValueError(f"Google token exchange failed: {e}")

        # Get Google user info to use as user_id
        try:
            user_info = await self.google_client.get_user_info(google_token["access_token"])
            user_id = user_info["sub"]  # Google user ID
        except Exception as e:
            raise ValueError(f"Failed to get Google user info: {e}")

        # Store Google Drive token
        await self.token_store.link_external_token(
            user_id=user_id,
            access_token=google_token["access_token"],
            refresh_token=google_token.get("refresh_token"),
            expires_in=google_token.get("expires_in", 3600),
            provider="google_drive",
        )

        # Create MCP authorization code
        mcp_code = await self.token_store.create_authorization_code(
            user_id=user_id,
            client_id=pending["mcp_client_id"],
            redirect_uri=pending["mcp_redirect_uri"],
            scope=pending["mcp_scope"],
            code_challenge=pending["mcp_code_challenge"],
            code_challenge_method=pending["mcp_code_challenge_method"],
        )

        # Clean up pending authorization
        del self._pending_authorizations[state]

        return {
            "code": mcp_code,
            "state": pending["mcp_state"],
            "redirect_uri": pending["mcp_redirect_uri"],
        }
