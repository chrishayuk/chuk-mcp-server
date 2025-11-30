# OAuth Providers

ChukMCPServer provides pluggable OAuth providers that can be reused across different MCP servers. Instead of implementing OAuth from scratch for each service, you can use pre-built providers or create your own.

## Available Providers

### Google Drive Provider

OAuth 2.1 integration with Google Drive API, providing secure access to user's Google Drive storage.

**Installation:**

```bash
pip install chuk-mcp-server[google_drive]
```

**Quick Setup (Using Helper):**

```python
from chuk_mcp_server import ChukMCPServer, run
from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

mcp = ChukMCPServer("my-server")

# ... register your tools ...

# Setup Google Drive OAuth (reads from environment variables)
oauth_hook = setup_google_drive_oauth(mcp)

# Run server with OAuth
run(transport="http", port=8000, post_register_hook=oauth_hook)
```

**Environment Variables:**

```bash
# Required
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"

# Optional (with defaults)
export GOOGLE_REDIRECT_URI="http://localhost:8000/oauth/callback"
export OAUTH_SERVER_URL="http://localhost:8000"
export GOOGLE_DRIVE_ROOT_FOLDER="CHUK"  # Folder in user's Drive
```

**Manual Setup (Full Control):**

```python
from chuk_mcp_server import ChukMCPServer, run
from chuk_mcp_server.oauth import OAuthMiddleware
from chuk_mcp_server.oauth.providers import GoogleDriveOAuthProvider

mcp = ChukMCPServer("my-server")

def setup_oauth():
    """Set up Google Drive OAuth."""
    provider = GoogleDriveOAuthProvider(
        google_client_id="your-client-id",
        google_client_secret="your-client-secret",
        google_redirect_uri="http://localhost:8000/oauth/callback",
        oauth_server_url="http://localhost:8000",
        sandbox_id="my-server-sandbox",
    )

    oauth = OAuthMiddleware(
        mcp_server=mcp,
        provider=provider,
        oauth_server_url="http://localhost:8000",
        callback_path="/oauth/callback",
        scopes_supported=["drive.file", "userinfo.profile"],
        service_documentation="https://github.com/yourusername/my-server",
        provider_name="Google Drive",
    )

    return oauth

run(transport="http", port=8000, post_register_hook=setup_oauth)
```

**Accessing Google Drive from Tools:**

```python
from chuk_mcp_server.oauth.helpers import configure_storage_from_oauth
from chuk_virtual_fs.providers import GoogleDriveProvider

# In your tool that requires authentication
@tool
async def my_tool():
    """Tool that needs Google Drive access."""
    # Get token from request context (automatically injected by OAuth middleware)
    access_token = get_access_token()  # From your request context

    # Validate token and get user credentials
    token_data = await oauth_provider.validate_access_token(access_token)

    # Configure storage from OAuth token
    storage_config = configure_storage_from_oauth(token_data)

    # Create Google Drive provider
    drive = GoogleDriveProvider(
        credentials=storage_config["credentials"],
        root_folder=storage_config["root_folder"],
    )

    await drive.initialize()

    # Use Google Drive...
    await drive.write_file("/myfile.txt", b"content")
```

**How It Works:**

1. **Two-Layer Authentication:**
   - **MCP Layer**: Claude Desktop ↔ Your MCP Server (OAuth tokens)
   - **Google Layer**: Your MCP Server ↔ Google Drive (Google tokens)

2. **Token Management:**
   - MCP client gets short-lived access tokens (15 min) and refresh tokens (1 day)
   - Google Drive tokens stored server-side, auto-refreshed when expired
   - User only authorizes once via browser

3. **OAuth Flow:**
   ```
   Claude Desktop → /oauth/authorize → Redirect to Google
   User authorizes on Google → Google callback → Token exchange
   Server stores Google token → Returns MCP auth code → Claude gets access token
   ```

**Creating Google OAuth Credentials:**

1. Go to https://console.cloud.google.com/
2. Create project (or select existing)
3. Enable Google Drive API
4. OAuth consent screen:
   - User Type: External
   - Add test users
5. Credentials → Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/oauth/callback`
6. Copy Client ID and Client Secret

## Creating Custom Providers

You can create your own OAuth provider for any service (GitHub, LinkedIn, Dropbox, etc.).

**Example: Custom Provider**

```python
from chuk_mcp_server.oauth import (
    BaseOAuthProvider,
    AuthorizationParams,
    OAuthToken,
    OAuthClientInfo,
    TokenStore,
)

class MyServiceOAuthProvider(BaseOAuthProvider):
    """OAuth provider for MyService."""

    def __init__(
        self,
        service_client_id: str,
        service_client_secret: str,
        service_redirect_uri: str,
        oauth_server_url: str = "http://localhost:8000",
        sandbox_id: str = "my-service",
    ):
        self.oauth_server_url = oauth_server_url
        self.token_store = TokenStore(sandbox_id=sandbox_id)

        # Initialize your service's OAuth client
        self.service_client = MyServiceOAuthClient(
            client_id=service_client_id,
            client_secret=service_client_secret,
            redirect_uri=service_redirect_uri,
        )

        self._pending_authorizations = {}

    async def authorize(self, params: AuthorizationParams) -> dict:
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

        # Check if user has external token
        # ... (similar to Google Drive provider)

        # Need external authorization - redirect to your service
        import secrets
        state = secrets.token_urlsafe(32)

        self._pending_authorizations[state] = {
            "mcp_client_id": params.client_id,
            "mcp_redirect_uri": params.redirect_uri,
            "mcp_state": params.state,
            "mcp_scope": params.scope,
            "mcp_code_challenge": params.code_challenge,
            "mcp_code_challenge_method": params.code_challenge_method,
        }

        auth_url = self.service_client.get_authorization_url(state=state)

        return {
            "authorization_url": auth_url,
            "state": state,
            "requires_external_authorization": True,
        }

    async def handle_external_callback(self, code: str, state: str) -> dict:
        """Handle callback from external service."""
        pending = self._pending_authorizations.get(state)
        if not pending:
            raise ValueError("Invalid or expired state parameter")

        # Exchange service code for token
        service_token = await self.service_client.exchange_code_for_token(code)

        # Get user info
        user_info = await self.service_client.get_user_info(
            service_token["access_token"]
        )
        user_id = user_info["id"]  # Or "sub" for OIDC

        # Store service token
        await self.token_store.link_external_token(
            user_id=user_id,
            access_token=service_token["access_token"],
            refresh_token=service_token.get("refresh_token"),
            expires_in=service_token.get("expires_in", 3600),
            provider="my-service",
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

See [OAUTH.md](OAUTH.md) for complete OAuth implementation guide.

## Examples

**chuk-mcp-stage**: Uses Google Drive provider for persistent scene storage
- See: https://github.com/chrishayuk/chuk-mcp-stage

**chuk-mcp-linkedin**: Uses custom LinkedIn provider for profile/post access
- See: https://github.com/chrishayuk/chuk-mcp-linkedin

## Security Best Practices

1. **Use PKCE** - Always require code_challenge for public clients
2. **Validate Redirect URIs** - Only allow registered redirect URIs
3. **Short-Lived Tokens** - MCP access tokens expire in 15 minutes
4. **Auto-Refresh** - External provider tokens refreshed automatically
5. **Sandbox Isolation** - Use unique sandbox IDs for multi-tenancy
6. **Environment Variables** - Never hardcode credentials
7. **HTTPS in Production** - Use HTTPS for all OAuth endpoints

## Troubleshooting

**OAuth provider not loading:**
```
ImportError: cannot import name 'GoogleDriveOAuthProvider'
```
**Fix**: Install the google_drive extra:
```bash
pip install chuk-mcp-server[google_drive]
```

**Browser doesn't open during OAuth flow:**
- OAuth only works in **HTTP mode** (not STDIO)
- Run server with: `uv run my-server http`
- Check that port 8000 is not blocked

**Invalid redirect URI error:**
- Ensure redirect URI in Google Cloud Console matches exactly
- Should be: `http://localhost:8000/oauth/callback`
- Protocol (http vs https) must match

**Token expired errors:**
- Tokens auto-refresh, but may need manual re-authorization
- Check server logs for refresh errors
- User may need to re-authorize via browser

## License

MIT - See [LICENSE](../LICENSE)
