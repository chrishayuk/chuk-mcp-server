"""
Base token store interface for OAuth tokens.

Defines the interface that all token store implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTokenStore(ABC):
    """
    Abstract base class for token storage implementations.

    All methods are async to support both file-based and Redis-based storage.
    """

    # ============================================================================
    # MCP Authorization Codes
    # ============================================================================

    @abstractmethod
    async def create_authorization_code(
        self,
        user_id: str,
        client_id: str,
        redirect_uri: str,
        scope: str | None = None,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> str:
        """Create authorization code for MCP client."""
        pass

    @abstractmethod
    async def validate_authorization_code(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> dict[str, Any] | None:
        """Validate authorization code and return user info."""
        pass

    # ============================================================================
    # MCP Access Tokens
    # ============================================================================

    @abstractmethod
    async def create_access_token(
        self,
        user_id: str,
        client_id: str,
        scope: str | None = None,
    ) -> tuple[str, str]:
        """Create MCP access token and refresh token."""
        pass

    @abstractmethod
    async def validate_access_token(self, token: str) -> dict[str, Any] | None:
        """Validate MCP access token."""
        pass

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str] | None:
        """Refresh MCP access token using refresh token."""
        pass

    # ============================================================================
    # External Provider Tokens (e.g., LinkedIn, GitHub, Google)
    # ============================================================================

    @abstractmethod
    async def link_external_token(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_in: int | None = None,
        provider: str = "external",
    ) -> None:
        """Link external OAuth provider tokens to MCP user."""
        pass

    @abstractmethod
    async def get_external_token(self, user_id: str, provider: str = "external") -> dict[str, Any] | None:
        """Get external provider token for MCP user."""
        pass

    @abstractmethod
    async def update_external_token(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_in: int | None = None,
        provider: str = "external",
    ) -> None:
        """Update external provider token (after refresh)."""
        pass

    @abstractmethod
    async def is_external_token_expired(self, user_id: str, provider: str = "external") -> bool:
        """Check if external provider token is expired."""
        pass

    # ============================================================================
    # Client Registration
    # ============================================================================

    @abstractmethod
    async def register_client(
        self,
        client_name: str,
        redirect_uris: list[str],
    ) -> dict[str, str]:
        """Register a new MCP client."""
        pass

    @abstractmethod
    async def validate_client(
        self,
        client_id: str,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
    ) -> bool:
        """Validate MCP client credentials."""
        pass
