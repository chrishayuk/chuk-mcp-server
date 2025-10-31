# OAuth 2.1 Support

ChukMCPServer provides a complete OAuth 2.1 authorization server implementation with support for external OAuth providers (LinkedIn, GitHub, Google, etc.).

## Features

- **OAuth 2.1 compliant** with PKCE (RFC 7636)
- **Dynamic client registration** (RFC 7591)
- **Pluggable provider support** - Integrate any OAuth provider
- **Session-based token storage** via [chuk-sessions](https://github.com/chrishayuk/chuk-sessions)
- **Production-ready** - Memory backend for dev, Redis for production
- **Multi-tenant** - Sandbox isolation for token storage

## Quick Start

### 1. Install Dependencies

```bash
# OAuth support is built into chuk-mcp-server
pip install chuk-mcp-server

# For production, install Redis backend
pip install chuk-sessions[redis]
```

### 2. Implement Your OAuth Provider

Create a provider that implements `BaseOAuthProvider`:

```python
from chuk_mcp_server.oauth import BaseOAuthProvider, TokenStore
from typing import Dict, Any, Optional

class MyOAuthProvider(BaseOAuthProvider):
    """OAuth provider for MyService."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        oauth_server_url: str = "http://localhost:8000",
        sandbox_id: str = "my-service",
    ):
        self.oauth_server_url = oauth_server_url
        self.token_store = TokenStore(sandbox_id=sandbox_id)

        # Initialize your service's OAuth client
        self.service_client = MyServiceOAuthClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )

        # Track pending authorization flows
        self._pending_authorizations: Dict[str, Dict[str, Any]] = {}

    async def authorize(self, params) -> Dict[str, Any]:
        """Handle authorization request from MCP client."""
        # Validate MCP client
        if not await self.token_store.validate_client(
            params.client_id,
            redirect_uri=params.redirect_uri,
        ):
            raise AuthorizeError(
                error="invalid_client",
                error_description="Invalid client_id or redirect_uri",
            )

        # Check if user already has token
        # ... implementation ...

        # Need external authorization - redirect to your service
        import secrets
        state = secrets.token_urlsafe(32)

        # Store pending authorization details
        self._pending_authorizations[state] = {
            "mcp_client_id": params.client_id,
            "mcp_redirect_uri": params.redirect_uri,
            "mcp_state": params.state,
            "mcp_scope": params.scope,
            "mcp_code_challenge": params.code_challenge,
            "mcp_code_challenge_method": params.code_challenge_method,
        }

        # Generate authorization URL for your service
        auth_url = self.service_client.get_authorization_url(state=state)

        return {
            "authorization_url": auth_url,
            "state": state,
            "requires_external_authorization": True,
        }

    async def handle_external_callback(
        self,
        code: str,
        state: str,
    ) -> Dict[str, Any]:
        """Handle callback from external service."""
        # Get pending authorization
        pending = self._pending_authorizations.get(state)
        if not pending:
            raise ValueError("Invalid or expired state parameter")

        # Exchange service code for token
        service_token = await self.service_client.exchange_code_for_token(code)

        # Get user info
        user_info = await self.service_client.get_user_info(
            service_token["access_token"]
        )
        user_id = user_info["sub"]

        # Store service token
        await self.token_store.link_external_token(
            user_id=user_id,
            access_token=service_token["access_token"],
            refresh_token=service_token.get("refresh_token"),
            expires_in=service_token.get("expires_in", 3600),
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

        # Clean up
        del self._pending_authorizations[state]

        return {
            "code": mcp_code,
            "state": pending["mcp_state"],
            "redirect_uri": pending["mcp_redirect_uri"],
        }

    # Implement other required methods:
    # - exchange_authorization_code
    # - exchange_refresh_token
    # - validate_access_token
    # - register_client
```

### 3. Add OAuth Middleware to Your Server

```python
from chuk_mcp_server import ChukMCPServer
from chuk_mcp_server.oauth import OAuthMiddleware

# Create your MCP server
mcp = ChukMCPServer("my-service")

# ... register your tools ...

def setup_oauth():
    """Set up OAuth middleware."""
    # Create your OAuth provider
    provider = MyOAuthProvider(
        client_id="your_service_client_id",
        client_secret="your_service_client_secret",
        redirect_uri="http://localhost:8000/oauth/callback",
        oauth_server_url="http://localhost:8000",
    )

    # Add OAuth middleware
    oauth = OAuthMiddleware(
        mcp_server=mcp,
        provider=provider,
        oauth_server_url="http://localhost:8000",
        callback_path="/oauth/callback",
        scopes_supported=[
            "your.scope.1",
            "your.scope.2",
        ],
        service_documentation="https://github.com/yourusername/your-mcp-server",
        provider_name="Your Service Name",
    )

    return oauth

# Run server with OAuth
mcp.run(
    host="0.0.0.0",
    port=8000,
    post_register_hook=setup_oauth,
)
```

## OAuth Endpoints

When OAuth is enabled, these endpoints are automatically registered:

### Discovery Endpoint
```
GET /.well-known/oauth-authorization-server
```

Returns OAuth server metadata (RFC 8414):
```json
{
  "issuer": "http://localhost:8000",
  "authorization_endpoint": "http://localhost:8000/oauth/authorize",
  "token_endpoint": "http://localhost:8000/oauth/token",
  "registration_endpoint": "http://localhost:8000/oauth/register",
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "response_types_supported": ["code"],
  "code_challenge_methods_supported": ["S256", "plain"],
  "scopes_supported": ["your.scope.1", "your.scope.2"]
}
```

### Authorization Endpoint
```
GET /oauth/authorize?client_id={id}&redirect_uri={uri}&response_type=code&code_challenge={challenge}&code_challenge_method=S256&state={state}
```

Initiates OAuth flow. May redirect to external provider for authentication.

### Token Endpoint
```
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code={code}&client_id={id}&redirect_uri={uri}&code_verifier={verifier}
```

Exchanges authorization code for access token with PKCE validation.

### Client Registration Endpoint
```
POST /oauth/register
Content-Type: application/json

{
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:8080/callback"]
}
```

Registers a new MCP client (RFC 7591).

### External Provider Callback
```
GET /oauth/callback?code={code}&state={state}
```

Handles callback from external OAuth provider.

## Token Storage

### Development (Memory Backend)

By default, tokens are stored in memory:

```python
# No configuration needed - works out of the box
provider = MyOAuthProvider(...)
```

### Production (Redis Backend)

For production, use Redis for persistent, scalable token storage:

```bash
# Install Redis backend
pip install chuk-sessions[redis]

# Set environment variables
export SESSION_PROVIDER=redis
export SESSION_REDIS_URL=redis://localhost:6379/0
```

Tokens are automatically stored in Redis with proper TTLs.

### Token TTL Configuration

All token expiration times can be configured via environment variables (values in seconds):

```bash
# Authorization code lifetime (default: 300 = 5 minutes)
# Short-lived codes exchanged for access tokens during OAuth flow
# Keep short for security - user should complete OAuth flow quickly
export OAUTH_AUTH_CODE_TTL=300

# Access token lifetime (default: 900 = 15 minutes)
# Used by MCP clients to authenticate API requests
# Should be short-lived and refreshed regularly for security
export OAUTH_ACCESS_TOKEN_TTL=900

# Refresh token lifetime (default: 86400 = 1 day)
# Tokens that obtain new access tokens without re-authentication
# Short lifetime requires daily re-authorization for maximum security
export OAUTH_REFRESH_TOKEN_TTL=86400

# Client registration lifetime (default: 31536000 = 1 year)
# How long dynamically registered MCP clients remain valid
# Can be longer since clients are typically persistent
export OAUTH_CLIENT_REGISTRATION_TTL=31536000

# External provider token lifetime (default: 86400 = 1 day)
# Access and refresh tokens from external providers (LinkedIn, GitHub, etc.)
# Stored server-side and auto-refreshed when expired
# Short lifetime minimizes risk if tokens are compromised
export OAUTH_EXTERNAL_TOKEN_TTL=86400
```

Example for even shorter-lived tokens in high-security environments:

```bash
# 2 minute auth codes
export OAUTH_AUTH_CODE_TTL=120

# 5 minute access tokens (very aggressive refresh)
export OAUTH_ACCESS_TOKEN_TTL=300

# 12 hour refresh tokens (force re-auth twice daily)
export OAUTH_REFRESH_TOKEN_TTL=43200
```

## Security Features

### PKCE (Proof Key for Code Exchange)

All authorization flows support PKCE (RFC 7636) with S256 and plain methods:

```python
# MCP client generates code verifier
import secrets
import hashlib
import base64

code_verifier = secrets.token_urlsafe(32)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip('=')

# Request authorization with code_challenge
# ...

# Exchange code with code_verifier
# Token endpoint validates PKCE automatically
```

### Multi-Tenant Isolation

Use sandbox IDs to isolate tokens between tenants:

```python
provider = MyOAuthProvider(
    sandbox_id="tenant-123",  # All tokens prefixed with this ID
    ...
)
```

### Token Expiration

Default TTLs (all configurable via environment variables - see [Token TTL Configuration](#token-ttl-configuration)):

- Authorization codes: 5 minutes (`OAUTH_AUTH_CODE_TTL`)
- Access tokens: 15 minutes (`OAUTH_ACCESS_TOKEN_TTL`)
- Refresh tokens: 1 day (`OAUTH_REFRESH_TOKEN_TTL`)
- Client registrations: 1 year (`OAUTH_CLIENT_REGISTRATION_TTL`)
- External provider tokens: 1 day (`OAUTH_EXTERNAL_TOKEN_TTL`)

## Examples

See working examples:

- **LinkedIn OAuth**: [chuk-mcp-linkedin](https://github.com/chrishayuk/chuk-mcp-linkedin)
  - Full LinkedIn OAuth integration
  - Production-ready implementation
  - Shows complete provider implementation

## API Reference

### OAuthMiddleware

```python
class OAuthMiddleware:
    def __init__(
        self,
        mcp_server: ChukMCPServer,
        provider: BaseOAuthProvider,
        oauth_server_url: str = "http://localhost:8000",
        callback_path: str = "/oauth/callback",
        scopes_supported: Optional[list[str]] = None,
        service_documentation: Optional[str] = None,
        provider_name: str = "OAuth Provider",
    ):
        """
        Generic OAuth middleware for ChukMCPServer.

        Args:
            mcp_server: ChukMCPServer instance
            provider: OAuth provider instance (implements BaseOAuthProvider)
            oauth_server_url: OAuth server base URL
            callback_path: Path for external provider callback
            scopes_supported: List of supported scopes for metadata
            service_documentation: URL to service documentation
            provider_name: Human-readable name of the OAuth provider
        """
```

### TokenStore

```python
class TokenStore(BaseTokenStore):
    def __init__(self, sandbox_id: str = "default"):
        """
        Session-based token store with automatic TTL.

        Args:
            sandbox_id: Sandbox ID for multi-tenant isolation

        Backend Configuration:
            Memory (default):
                - No configuration needed
                - Great for development

            Redis (production):
                - Set SESSION_PROVIDER=redis
                - Set SESSION_REDIS_URL=redis://localhost:6379/0
        """
```

### BaseOAuthProvider

```python
class BaseOAuthProvider:
    """Base interface for OAuth providers."""

    async def authorize(
        self, params: AuthorizationParams
    ) -> Dict[str, Any]:
        """Handle authorization request from MCP client."""
        raise NotImplementedError

    async def exchange_authorization_code(
        self, code: str, client_id: str, redirect_uri: str, code_verifier: Optional[str]
    ) -> OAuthToken:
        """Exchange authorization code for access token."""
        raise NotImplementedError

    async def exchange_refresh_token(
        self, refresh_token: str, client_id: str, scope: Optional[str]
    ) -> OAuthToken:
        """Refresh access token using refresh token."""
        raise NotImplementedError

    async def validate_access_token(
        self, token: str
    ) -> Dict[str, Any]:
        """Validate and load access token."""
        raise NotImplementedError

    async def register_client(
        self, client_metadata: Dict[str, Any]
    ) -> OAuthClientInfo:
        """Register a new MCP client."""
        raise NotImplementedError

    async def handle_external_callback(
        self, code: str, state: str
    ) -> Dict[str, Any]:
        """Handle callback from external OAuth provider."""
        raise NotImplementedError
```

## Troubleshooting

### OAuth Discovery Fails

**Problem**: `404 Not Found` on `/.well-known/oauth-authorization-server`

**Solution**: Ensure OAuth middleware is registered via `post_register_hook`:

```python
mcp.run(post_register_hook=setup_oauth)  # ✓ Correct
# NOT: setup_oauth() at module level before mcp.run()
```

### Token Exchange Fails with 400

**Problem**: `invalid_grant: Invalid or expired authorization code`

**Possible causes**:
1. PKCE validation failing - check code_verifier matches code_challenge
2. Redirect URI mismatch - must match exactly
3. Authorization code expired (5 min TTL by default)
4. Code already used (one-time use)

### External Callback Not Working

**Problem**: External provider redirects to wrong URL

**Solution**: Check redirect_uri in your service client initialization:

```python
# Should match your OAuth server's callback
service_client = MyServiceOAuthClient(
    redirect_uri="http://localhost:8000/oauth/callback",  # ✓ OAuth server
    # NOT: "http://localhost:8080/callback"  # ✗ MCP client
)
```

## Best Practices

1. **Use PKCE** - Always require code_challenge for public clients
2. **Validate redirect URIs** - Only allow registered redirect URIs
3. **Use Redis in production** - Memory backend is for development only
4. **Set proper TTLs** - Short-lived access tokens (15min), daily refresh tokens for security
5. **Log OAuth flows** - Aid debugging with detailed logging
6. **Handle token refresh** - Automatically refresh expired external tokens
7. **Sandbox isolation** - Use unique sandbox IDs for multi-tenancy

## License

MIT - See [LICENSE](../LICENSE)
