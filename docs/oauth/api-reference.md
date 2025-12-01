# OAuth Types and Exports

Complete reference for OAuth types, classes, and functions exported from chuk-mcp-server.

## Core OAuth Module

### Importing OAuth Components

```python
# Import OAuth components from oauth module
from chuk_mcp_server.oauth import (
    OAuthMiddleware,          # OAuth middleware for MCP server
    TokenStore,               # Session-based token storage
    BaseOAuthProvider,        # Base class for OAuth providers
    BaseTokenStore,           # Base class for token stores

    # OAuth models
    AuthorizationParams,      # Authorization request parameters
    OAuthToken,               # OAuth token response
    OAuthClientInfo,          # Client registration info

    # OAuth errors
    AuthorizeError,           # Authorization errors
    TokenError,               # Token errors
    RegistrationError,        # Client registration errors

    # Helper functions
    setup_google_drive_oauth,       # One-line Google Drive OAuth setup
    configure_storage_from_oauth,   # Convert OAuth tokens to storage config
)
```

## OAuth Provider Types

### BaseOAuthProvider

Abstract base class for implementing OAuth providers.

```python
from chuk_mcp_server.oauth import BaseOAuthProvider, AuthorizationParams, OAuthToken

class MyOAuthProvider(BaseOAuthProvider):
    async def authorize(self, params: AuthorizationParams) -> dict[str, Any]:
        """Handle authorization request from MCP client."""
        ...

    async def exchange_authorization_code(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> OAuthToken:
        """Exchange authorization code for access token."""
        ...

    async def exchange_refresh_token(
        self,
        refresh_token: str,
        client_id: str,
        scope: str | None = None,
    ) -> OAuthToken:
        """Refresh access token."""
        ...

    async def validate_access_token(self, token: str) -> dict[str, Any]:
        """Validate and load access token."""
        ...

    async def register_client(self, client_metadata: dict[str, Any]) -> OAuthClientInfo:
        """Register a new MCP client."""
        ...

    async def handle_external_callback(self, code: str, state: str) -> dict[str, Any]:
        """Handle callback from external OAuth provider."""
        ...
```

### Google Drive Provider (Optional)

Available when `google_drive` extra is installed.

```python
from chuk_mcp_server.oauth.providers import (
    GoogleDriveOAuthProvider,    # Google Drive OAuth provider
    GoogleDriveOAuthClient,      # Google Drive OAuth client
)

# Create provider
provider = GoogleDriveOAuthProvider(
    google_client_id="...",
    google_client_secret="...",
    google_redirect_uri="http://localhost:8000/oauth/callback",
    oauth_server_url="http://localhost:8000",
    sandbox_id="my-app",
)
```

## OAuth Model Types

### AuthorizationParams

Parameters for OAuth authorization requests.

```python
from chuk_mcp_server.oauth import AuthorizationParams

params = AuthorizationParams(
    response_type: str,                           # "code"
    client_id: str,                               # Client ID
    redirect_uri: str,                            # Redirect URI
    scope: str | None = None,                     # Requested scopes
    state: str | None = None,                     # CSRF protection
    code_challenge: str | None = None,            # PKCE challenge
    code_challenge_method: Literal["S256", "plain"] | None = None,
)
```

### OAuthToken

OAuth token response.

```python
from chuk_mcp_server.oauth import OAuthToken

token = OAuthToken(
    access_token: str,           # Access token
    token_type: str,             # "Bearer"
    expires_in: int,             # Expiration time in seconds
    refresh_token: str | None,   # Refresh token (optional)
    scope: str | None,           # Granted scopes (optional)
)
```

### OAuthClientInfo

Client registration information.

```python
from chuk_mcp_server.oauth import OAuthClientInfo

client_info = OAuthClientInfo(
    client_id: str,              # Client ID
    client_secret: str,          # Client secret
    client_name: str,            # Client name
    redirect_uris: list[str],    # Registered redirect URIs
)
```

## OAuth Error Types

### AuthorizeError

Raised during authorization flow.

```python
from chuk_mcp_server.oauth import AuthorizeError

raise AuthorizeError(
    error: str,                  # Error code ("invalid_client", etc.)
    error_description: str,      # Human-readable description
)
```

### TokenError

Raised during token operations.

```python
from chuk_mcp_server.oauth import TokenError

raise TokenError(
    error: str,                  # Error code ("invalid_grant", etc.)
    error_description: str,      # Human-readable description
)
```

### RegistrationError

Raised during client registration.

```python
from chuk_mcp_server.oauth import RegistrationError

raise RegistrationError(
    error: str,                  # Error code
    error_description: str,      # Human-readable description
)
```

## OAuth Middleware

### OAuthMiddleware

Adds OAuth endpoints to MCP server.

```python
from chuk_mcp_server import ChukMCPServer
from chuk_mcp_server.oauth import OAuthMiddleware, BaseOAuthProvider

mcp = ChukMCPServer("my-server")
provider: BaseOAuthProvider = ...  # Your OAuth provider

oauth = OAuthMiddleware(
    mcp_server=mcp,
    provider=provider,
    oauth_server_url: str = "http://localhost:8000",
    callback_path: str = "/oauth/callback",
    scopes_supported: list[str] | None = None,
    service_documentation: str | None = None,
    provider_name: str = "OAuth Provider",
)
```

Automatically registers these endpoints:
- `GET /.well-known/oauth-authorization-server` - OAuth metadata
- `GET /.well-known/oauth-protected-resource` - Protected resource metadata
- `GET /oauth/authorize` - Authorization endpoint
- `POST /oauth/token` - Token endpoint
- `POST /oauth/register` - Client registration
- `GET /oauth/callback` - External provider callback

## Token Storage

### TokenStore

Session-based token storage using chuk-sessions.

```python
from chuk_mcp_server.oauth import TokenStore

store = TokenStore(sandbox_id: str = "default")

# Client management
await store.register_client(client_name, redirect_uris)
await store.validate_client(client_id, redirect_uri)

# Authorization codes
await store.create_authorization_code(
    user_id, client_id, redirect_uri, scope,
    code_challenge, code_challenge_method
)
await store.validate_authorization_code(
    code, client_id, redirect_uri, code_verifier
)

# Access tokens
await store.create_access_token(user_id, client_id, scope)
await store.validate_access_token(token)
await store.refresh_access_token(refresh_token)

# External provider tokens
await store.link_external_token(
    user_id, access_token, refresh_token, expires_in, provider
)
await store.get_external_token(user_id, provider)
await store.is_external_token_expired(user_id, provider)
await store.update_external_token(
    user_id, access_token, refresh_token, expires_in, provider
)
```

## Helper Functions

### setup_google_drive_oauth()

One-line Google Drive OAuth setup.

```python
from chuk_mcp_server import get_mcp_server, run
from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

# Setup OAuth (reads from environment)
oauth_hook = setup_google_drive_oauth(
    mcp_server=get_mcp_server(),
    client_id: str | None = None,        # Or env: GOOGLE_CLIENT_ID
    client_secret: str | None = None,    # Or env: GOOGLE_CLIENT_SECRET
    redirect_uri: str | None = None,     # Or env: GOOGLE_REDIRECT_URI
    oauth_server_url: str | None = None, # Or env: OAUTH_SERVER_URL
    sandbox_id: str | None = None,       # Defaults to server name
)

# Run with OAuth
run(transport="http", port=8000, post_register_hook=oauth_hook)
```

Returns `None` if credentials not configured, or a callable that creates OAuth middleware.

### configure_storage_from_oauth()

Convert OAuth token data to storage credentials.

```python
from chuk_mcp_server.oauth.helpers import configure_storage_from_oauth

# Get token data from OAuth provider
token_data = await oauth_provider.validate_access_token(access_token)

# Convert to storage config
storage_config = configure_storage_from_oauth(token_data)

# Returns:
{
    "credentials": {
        "token": "...",
        "refresh_token": "...",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "...",
        "client_secret": "...",
        "scopes": ["..."],
    },
    "root_folder": "CHUK",
    "user_id": "user-123",
}
```

## MCP Server Helper

### get_mcp_server()

Get the global MCP server instance.

```python
from chuk_mcp_server import get_mcp_server

# Get global server instance
server = get_mcp_server()

# Use with OAuth setup
from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth
oauth_hook = setup_google_drive_oauth(get_mcp_server())
```

## Type Checking

All OAuth types are fully typed and support static type checking:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chuk_mcp_server.oauth import (
        BaseOAuthProvider,
        OAuthToken,
        AuthorizationParams,
        OAuthClientInfo,
    )
```

## Complete Example

```python
from chuk_mcp_server import ChukMCPServer, tool, run, get_mcp_server
from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

# Create MCP server
mcp = ChukMCPServer("my-app")

# Register tools
@mcp.tool
def my_tool(data: str) -> dict:
    """Example tool."""
    return {"data": data}

# Setup Google Drive OAuth (one line!)
oauth_hook = setup_google_drive_oauth(get_mcp_server())

# Run server with OAuth
if __name__ == "__main__":
    run(transport="http", port=8000, post_register_hook=oauth_hook)
```

## Environment Variables

Required for `setup_google_drive_oauth()`:
```bash
export GOOGLE_CLIENT_ID="..."
export GOOGLE_CLIENT_SECRET="..."
```

Optional (with defaults):
```bash
export GOOGLE_REDIRECT_URI="http://localhost:8000/oauth/callback"
export OAUTH_SERVER_URL="http://localhost:8000"
export GOOGLE_DRIVE_ROOT_FOLDER="CHUK"
```

## See Also

- [OAUTH.md](OAUTH.md) - Complete OAuth implementation guide
- [OAUTH_PROVIDERS.md](OAUTH_PROVIDERS.md) - Provider documentation
- [API Reference](https://github.com/chrishayuk/chuk-mcp-server) - Full API docs
