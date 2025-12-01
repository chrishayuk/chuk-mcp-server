# Protected Tools

Use the `@requires_auth` decorator to create tools that require OAuth authentication.

## Basic Protected Tool

```python
from chuk_mcp_server import ChukMCPServer, tool, requires_auth

mcp = ChukMCPServer("my-app")

@mcp.tool
@requires_auth()
async def publish_post(
    content: str,
    _external_access_token: str | None = None
) -> dict:
    """Publish a post (requires authentication)."""
    import httpx

    headers = {"Authorization": f"Bearer {_external_access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/posts",
            headers=headers,
            json={"content": content}
        )
        return response.json()
```

## How It Works

1. User calls tool from Claude
2. MCP server validates OAuth token
3. External access token is injected into `_external_access_token`
4. Tool uses token to call external API

## Token Injection

The `_external_access_token` parameter is special:
- Always optional (`str | None`)
- Automatically injected by OAuth middleware
- Contains the external provider's access token

```python
@mcp.tool
@requires_auth()
async def get_profile(_external_access_token: str | None = None) -> dict:
    """Get user profile."""
    # Token is automatically injected
    assert _external_access_token is not None

    headers = {"Authorization": f"Bearer {_external_access_token}"}
    # Use token to call API...
```

## Scope-Based Access

Require specific scopes:

```python
@mcp.tool
@requires_auth(scopes=["posts.write"])
async def publish_post(content: str, _external_access_token: str | None = None):
    """Publish post (requires posts.write scope)."""
    ...

@mcp.tool
@requires_auth(scopes=["profile.read"])
async def get_profile(_external_access_token: str | None = None):
    """Get profile (requires profile.read scope)."""
    ...
```

## Error Handling

```python
@mcp.tool
@requires_auth()
async def call_api(
    endpoint: str,
    _external_access_token: str | None = None
) -> dict:
    """Call external API."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.example.com/{endpoint}",
                headers={"Authorization": f"Bearer {_external_access_token}"}
            )
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return {"status": "error", "error": "Unauthorized - token may be expired"}
        return {"status": "error", "error": str(e)}
```

## Complete Example

```python
from chuk_mcp_server import ChukMCPServer, requires_auth
from chuk_mcp_server.oauth import OAuthMiddleware
from my_provider import MyOAuthProvider

mcp = ChukMCPServer("social-app")

@mcp.tool
@requires_auth(scopes=["posts.write"])
async def create_post(
    content: str,
    visibility: str = "PUBLIC",
    _external_access_token: str | None = None
) -> dict:
    """Create a new post."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/v1/posts",
            headers={"Authorization": f"Bearer {_external_access_token}"},
            json={"content": content, "visibility": visibility}
        )
        return response.json()

@mcp.tool
@requires_auth(scopes=["profile.read"])
async def get_my_profile(_external_access_token: str | None = None) -> dict:
    """Get current user's profile."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/v1/me",
            headers={"Authorization": f"Bearer {_external_access_token}"}
        )
        return response.json()

# Setup OAuth
def setup_oauth():
    provider = MyOAuthProvider(
        client_id="your-client-id",
        client_secret="your-client-secret",
        redirect_uri="http://localhost:8000/oauth/callback"
    )

    return OAuthMiddleware(
        mcp_server=mcp,
        provider=provider,
        oauth_server_url="http://localhost:8000",
        scopes_supported=["posts.write", "profile.read"],
    )

mcp.run(transport="http", port=8000, post_register_hook=setup_oauth)
```

## Next Steps

- [Token Management](tokens.md) - Understanding token lifecycle
- [Custom Providers](custom-providers.md) - Build your own provider
- [OAuth Overview](overview.md) - Complete OAuth guide
