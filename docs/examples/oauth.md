# Example: OAuth Integration

Protected tools with OAuth authentication.

## Complete Server

```python
from chuk_mcp_server import ChukMCPServer, requires_auth
from chuk_mcp_server.oauth import OAuthMiddleware
from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

mcp = ChukMCPServer("oauth-example")

@mcp.tool
@requires_auth()
async def get_profile(_external_access_token: str | None = None) -> dict:
    """Get user profile (requires auth)."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {_external_access_token}"}
        )
        return response.json()

# Setup OAuth
oauth_hook = setup_google_drive_oauth(mcp)

if __name__ == "__main__":
    mcp.run(transport="http", port=8000, post_register_hook=oauth_hook)
```

## Next Steps

- [OAuth Overview](../oauth/overview.md) - Complete guide
- [Protected Tools](../oauth/protected-tools.md) - Auth patterns
- [Google Drive](../oauth/google-drive.md) - Provider setup
