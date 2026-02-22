# OAuth & Authentication

ChukMCPServer provides full OAuth 2.1 support with PKCE, automatic token management, and RFC-compliant endpoints. Perfect for building authenticated MCP servers that integrate with LinkedIn, GitHub, Google, and other OAuth providers.

## What is OAuth in MCP?

OAuth allows your MCP server to:

- Authenticate users before they can use tools
- Access external APIs on behalf of users
- Implement fine-grained permissions with scopes
- Securely manage user sessions and tokens

## Quick Start

### Protected Tools

Mark tools as requiring authentication:

```python
from chuk_mcp_server import ChukMCPServer, tool, requires_auth

mcp = ChukMCPServer("my-oauth-server")

@mcp.tool
@requires_auth()
async def publish_post(
    content: str,
    visibility: str = "PUBLIC",
    _external_access_token: str | None = None
) -> dict:
    """Publish content using external OAuth provider."""
    # Token is automatically validated and injected
    import httpx

    headers = {"Authorization": f"Bearer {_external_access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/v1/posts",
            headers=headers,
            json={"content": content, "visibility": visibility}
        )
        return response.json()
```

### Setup OAuth Middleware

```python
from chuk_mcp_server.oauth import OAuthMiddleware
from my_provider import MyOAuthProvider

def setup_oauth():
    provider = MyOAuthProvider(
        client_id="your_client_id",
        client_secret="your_client_secret",
        redirect_uri="http://localhost:8000/oauth/callback"
    )

    return OAuthMiddleware(
        mcp_server=mcp,
        provider=provider,
        oauth_server_url="http://localhost:8000",
        scopes_supported=["posts.write", "profile.read"],
        provider_name="My Service"
    )

if __name__ == "__main__":
    mcp.run(host="0.0.0.0", port=8000, post_register_hook=setup_oauth)
```

## OAuth Features

### Standards Compliance

- **OAuth 2.1** - Latest OAuth standard with security improvements
- **PKCE** - [RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636) - Proof Key for Code Exchange
- **Authorization Server Discovery** - [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414)
- **Protected Resource Metadata** - [RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728)
- **JWT Access Tokens** - [RFC 9068](https://datatracker.ietf.org/doc/html/rfc9068)
- **Dynamic Client Registration** - [RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591)

### Built-In Features

- ✅ Automatic token refresh
- ✅ Token validation
- ✅ Scope-based access control
- ✅ Multi-tenant support with sandbox isolation
- ✅ Session management
- ✅ Redis backend for distributed deployments

## OAuth Endpoints

When you enable OAuth, these endpoints are automatically registered:

### Discovery Endpoints

```bash
# Authorization Server Discovery (RFC 8414)
GET /.well-known/oauth-authorization-server

# Protected Resource Metadata (RFC 9728)
GET /.well-known/oauth-protected-resource
```

### OAuth Flow Endpoints

```bash
# Authorization - Start OAuth flow
GET /oauth/authorize?client_id={id}&redirect_uri={uri}&response_type=code&code_challenge={challenge}&code_challenge_method=S256

# Token - Exchange code for access token
POST /oauth/token
Content-Type: application/x-www-form-urlencoded
grant_type=authorization_code&code={code}&client_id={id}&redirect_uri={uri}&code_verifier={verifier}

# Client Registration (RFC 7591)
POST /oauth/register
Content-Type: application/json
{"client_name": "My Client", "redirect_uris": ["http://localhost:8080/callback"]}

# External Provider Callback
GET /oauth/callback?code={code}&state={state}
```

## How It Works

### Two-Layer Authentication

ChukMCPServer uses a two-layer OAuth architecture:

```
┌─────────────┐       OAuth        ┌──────────────┐      OAuth       ┌─────────────┐
│   Claude    │ ←─────────────────→ │ Your MCP     │ ←───────────────→ │  External   │
│  Desktop    │   (MCP Layer)       │   Server     │  (Provider Layer)│  Provider   │
└─────────────┘                     └──────────────┘                  └─────────────┘
     MCP Client                      OAuth Server                      (Google, etc.)
```

**Layer 1 - MCP Layer**: Claude Desktop ↔ Your MCP Server
- Short-lived access tokens (15 min default)
- Refresh tokens (1 day default)
- MCP client authentication

**Layer 2 - Provider Layer**: Your MCP Server ↔ External Service
- External provider tokens (Google, LinkedIn, etc.)
- Stored server-side
- Auto-refreshed when expired

### OAuth Flow

1. **MCP Client Requests Authorization**
   ```
   Claude Desktop → /oauth/authorize → MCP Server
   ```

2. **Redirect to External Provider**
   ```
   MCP Server → Redirect → Google/LinkedIn/etc.
   ```

3. **User Authorizes**
   ```
   User logs in and grants permissions
   ```

4. **Callback & Token Exchange**
   ```
   Provider → /oauth/callback → MCP Server
   MCP Server stores external token
   ```

5. **Return MCP Auth Code**
   ```
   MCP Server → auth code → Claude Desktop
   ```

6. **Exchange for Access Token**
   ```
   Claude Desktop → /oauth/token → MCP Server
   MCP Server → access token + refresh token
   ```

7. **Use Protected Tools**
   ```
   Claude calls tools with access token
   Server validates token and injects external token
   ```

## Using OAuth Providers

### Built-In Providers

ChukMCPServer includes ready-to-use providers:

=== "Google Drive"

    ```python
    from chuk_mcp_server import get_mcp_server, run
    from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

    # One line to add Google Drive OAuth!
    oauth_hook = setup_google_drive_oauth(get_mcp_server())

    run(transport="http", port=8000, post_register_hook=oauth_hook)
    ```

    See [Google Drive Provider](google-drive.md) for complete guide.

=== "Custom Provider"

    ```python
    from chuk_mcp_server.oauth import BaseOAuthProvider

    class MyOAuthProvider(BaseOAuthProvider):
        # Implement required methods
        async def authorize(self, params):
            ...

        async def exchange_authorization_code(self, code, ...):
            ...
    ```

    See [Custom Providers](custom-providers.md) for implementation guide.

## Token Management

### Token Storage

ChukMCPServer uses a flexible token storage system:

**Development (Memory Backend)**
```python
# Zero configuration - works out of the box
from chuk_mcp_server.oauth import TokenStore

token_store = TokenStore(sandbox_id="my-app")
```

**Distributed Deployment (Redis Backend)**
```python
# Set environment variables
import os
os.environ["SESSION_PROVIDER"] = "redis"
os.environ["SESSION_REDIS_URL"] = "redis://localhost:6379/0"

# TokenStore automatically uses Redis
token_store = TokenStore(sandbox_id="my-app")
```

### Token Lifecycle

Configure token TTLs via environment variables:

```bash
# Authorization codes - temporary codes for token exchange
export OAUTH_AUTH_CODE_TTL=600              # 10 minutes (default)

# Access tokens - short-lived tokens for API calls
export OAUTH_ACCESS_TOKEN_TTL=900           # 15 minutes (default)

# Refresh tokens - used to get new access tokens
export OAUTH_REFRESH_TOKEN_TTL=86400        # 1 day (default)

# Client registrations - how long registered clients remain valid
export OAUTH_CLIENT_REGISTRATION_TTL=31536000  # 1 year (default)

# External tokens - tokens from external providers (auto-refreshed)
export OAUTH_EXTERNAL_TOKEN_TTL=5184000     # 60 days (default)
```

## Security Best Practices

### 1. Use PKCE

Always require PKCE for public clients:

```python
oauth = OAuthMiddleware(
    mcp_server=mcp,
    provider=provider,
    # PKCE is enabled by default
)
```

### 2. Validate Redirect URIs

Only allow registered redirect URIs:

```python
class MyOAuthProvider(BaseOAuthProvider):
    async def authorize(self, params):
        # Validate redirect_uri is registered
        if not await self.token_store.validate_client(
            params.client_id,
            redirect_uri=params.redirect_uri
        ):
            raise AuthorizeError("invalid_client")
```

### 3. Short-Lived Tokens

Use short TTLs for access tokens:

```bash
export OAUTH_ACCESS_TOKEN_TTL=900  # 15 minutes
```

### 4. Environment Variables

Never hardcode credentials:

```python
import os

provider = MyOAuthProvider(
    client_id=os.getenv("OAUTH_CLIENT_ID"),
    client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
    redirect_uri=os.getenv("OAUTH_REDIRECT_URI")
)
```

### 5. HTTPS for Deployed Servers

Use HTTPS for all OAuth endpoints:

```python
if __name__ == "__main__":
    mcp.run(
        host="0.0.0.0",
        port=443,  # HTTPS port
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        post_register_hook=setup_oauth
    )
```

### 6. Sandbox Isolation

Use unique sandbox IDs for multi-tenancy:

```python
token_store = TokenStore(
    sandbox_id=f"app-{tenant_id}"  # Isolate by tenant
)
```

## Examples

### LinkedIn Integration

See [chuk-mcp-linkedin](https://github.com/chrishayuk/chuk-mcp-linkedin) for a complete LinkedIn OAuth implementation.

### Google Drive Integration

See [chuk-mcp-stage](https://github.com/chrishayuk/chuk-mcp-stage) for Google Drive OAuth with file storage.

## Next Steps

- [Google Drive Provider](google-drive.md) - Ready-to-use Google Drive OAuth
- [Custom Providers](custom-providers.md) - Build your own OAuth provider
- [Protected Tools](protected-tools.md) - Using `@requires_auth`
- [Token Management](tokens.md) - Deep dive into token lifecycle
- [API Reference](api-reference.md) - Complete OAuth API docs

## Troubleshooting

### OAuth not working in STDIO mode?

OAuth requires HTTP transport (browser-based flow):

```python
mcp.run(transport="http", port=8000, post_register_hook=setup_oauth)
```

### Tokens expiring too quickly?

Adjust TTLs:

```bash
export OAUTH_ACCESS_TOKEN_TTL=3600  # 1 hour
export OAUTH_REFRESH_TOKEN_TTL=604800  # 7 days
```

### Redis connection errors?

Check Redis is running and URL is correct:

```bash
redis-cli ping  # Should return PONG
export SESSION_REDIS_URL="redis://localhost:6379/0"
```

### External provider callback not working?

Verify redirect URI matches exactly:

```python
# Must match what's registered with provider
redirect_uri="http://localhost:8000/oauth/callback"  # Exact match!
```
