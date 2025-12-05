"""OAuth setup helpers for MCP servers.

Makes it easy to add OAuth to any MCP server with minimal configuration.
"""

import logging
import os
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def setup_google_drive_oauth(
    mcp_server: Any,
    client_id: str | None = None,
    client_secret: str | None = None,
    redirect_uri: str | None = None,
    oauth_server_url: str | None = None,
    sandbox_id: str | None = None,
) -> Callable[[], Any] | None:
    """Set up Google Drive OAuth for an MCP server.

    This function creates a post_register_hook that can be passed to mcp.run().
    It automatically configures Google Drive OAuth if credentials are provided
    (either as parameters or via environment variables).

    Args:
        mcp_server: ChukMCPServer instance
        client_id: Google OAuth client ID (or env: GOOGLE_CLIENT_ID)
        client_secret: Google OAuth client secret (or env: GOOGLE_CLIENT_SECRET)
        redirect_uri: OAuth callback URL (or env: GOOGLE_REDIRECT_URI)
            Default: http://localhost:8000/oauth/callback
        oauth_server_url: OAuth server base URL (or env: OAUTH_SERVER_URL)
            Default: http://localhost:8000
        sandbox_id: Sandbox ID for token isolation
            Default: <server_name>

    Returns:
        Post-register hook function or None if OAuth not configured

    Environment Variables:
        GOOGLE_CLIENT_ID: Google OAuth client ID
        GOOGLE_CLIENT_SECRET: Google OAuth client secret
        GOOGLE_REDIRECT_URI: OAuth callback URL
        OAUTH_SERVER_URL: OAuth server base URL

    Example:
        from chuk_mcp_server import ChukMCPServer, run
        from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

        mcp = ChukMCPServer("my-server")

        # ... register tools ...

        # Add Google Drive OAuth support
        oauth_hook = setup_google_drive_oauth(mcp)

        # Run server with OAuth if configured
        run(transport="http", port=8000, post_register_hook=oauth_hook)
    """
    # Try to get credentials from parameters or environment
    client_id = client_id or os.getenv("GOOGLE_CLIENT_ID")
    client_secret = client_secret or os.getenv("GOOGLE_CLIENT_SECRET")

    # If no credentials, OAuth is not configured
    if not client_id or not client_secret:
        logger.info("Google Drive OAuth not configured (missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET)")
        return None

    # Get other config from parameters or environment with defaults
    final_redirect_uri = redirect_uri or os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/callback")
    final_oauth_server_url = oauth_server_url or os.getenv("OAUTH_SERVER_URL", "http://localhost:8000")
    sandbox_id = sandbox_id or f"chuk-mcp-{mcp_server.name}" if hasattr(mcp_server, "name") else "default"

    # Import OAuth components (only if google_drive extra is installed)
    try:
        from .middleware import OAuthMiddleware
        from .providers.google_drive import GoogleDriveOAuthProvider
    except ImportError as e:
        logger.error(
            f"Google Drive OAuth dependencies not installed: {e}\n"
            "Install with: pip install chuk-mcp-server[google_drive]"
        )
        return None

    def post_register_hook() -> OAuthMiddleware:
        """Create and register OAuth middleware."""
        logger.info("Setting up Google Drive OAuth...")

        # Type assertions - these are guaranteed to be non-None due to defaults above
        assert client_id is not None
        assert client_secret is not None
        assert final_redirect_uri is not None
        assert final_oauth_server_url is not None

        # Create Google Drive OAuth provider
        provider = GoogleDriveOAuthProvider(
            google_client_id=client_id,
            google_client_secret=client_secret,
            google_redirect_uri=final_redirect_uri,
            oauth_server_url=final_oauth_server_url,
            sandbox_id=sandbox_id,
        )

        # Add OAuth middleware
        oauth = OAuthMiddleware(
            mcp_server=mcp_server,
            provider=provider,
            oauth_server_url=final_oauth_server_url,
            callback_path="/oauth/callback",
            scopes_supported=[
                "drive.file",
                "userinfo.profile",
            ],
            service_documentation=f"https://github.com/chrishayuk/{mcp_server.name}"
            if hasattr(mcp_server, "name")
            else None,
            provider_name="Google Drive",
        )

        logger.info(
            f"✓ Google Drive OAuth configured:\n"
            f"  - Authorization endpoint: {final_oauth_server_url}/oauth/authorize\n"
            f"  - Token endpoint: {final_oauth_server_url}/oauth/token\n"
            f"  - Callback: {final_redirect_uri}\n"
            f"  - Discovery: {final_oauth_server_url}/.well-known/oauth-authorization-server"
        )

        return oauth

    return post_register_hook


def configure_storage_from_oauth(access_token_data: dict[str, Any]) -> dict[str, Any]:
    """Configure storage provider from OAuth token data.

    Extracts Google Drive credentials from OAuth token data and returns
    configuration for chuk-virtual-fs GoogleDriveProvider.

    Args:
        access_token_data: Token data from OAuth provider's validate_access_token()

    Returns:
        Dict with credentials for GoogleDriveProvider

    Example:
        from chuk_mcp_server.oauth.helpers import configure_storage_from_oauth
        from chuk_virtual_fs.providers import GoogleDriveProvider

        # Get token data from OAuth provider
        token_data = await oauth_provider.validate_access_token(access_token)

        # Configure storage from token
        storage_config = configure_storage_from_oauth(token_data)

        # Create Google Drive provider
        provider = GoogleDriveProvider(
            credentials=storage_config["credentials"],
            root_folder=storage_config.get("root_folder", "CHUK"),
        )
    """
    return {
        "credentials": {
            "token": access_token_data.get("external_access_token"),
            "refresh_token": access_token_data.get("external_refresh_token"),
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "scopes": [
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
        },
        "root_folder": os.getenv("GOOGLE_DRIVE_ROOT_FOLDER", "CHUK"),
        "user_id": access_token_data.get("user_id"),
    }
