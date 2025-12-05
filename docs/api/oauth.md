# OAuth API

API reference for OAuth components.

## OAuthMiddleware

```python
from chuk_mcp_server.oauth import OAuthMiddleware

oauth = OAuthMiddleware(
    mcp_server=mcp,
    provider=provider,
    oauth_server_url="http://localhost:8000",
    callback_path="/oauth/callback",
    scopes_supported=["read", "write"],
    service_documentation="https://docs.example.com",
    provider_name="My Service"
)
```

## BaseOAuthProvider

Base class for OAuth providers.

```python
from chuk_mcp_server.oauth import BaseOAuthProvider

class MyProvider(BaseOAuthProvider):
    async def authorize(self, params):
        ...
    
    async def exchange_authorization_code(self, code, ...):
        ...
    
    async def exchange_refresh_token(self, refresh_token, ...):
        ...
    
    async def validate_access_token(self, token):
        ...
    
    async def register_client(self, metadata):
        ...
```

## TokenStore

```python
from chuk_mcp_server.oauth import TokenStore

store = TokenStore(sandbox_id="my-app")
```

## Next Steps

- [OAuth Overview](../oauth/overview.md) - Complete guide
- [Custom Providers](../oauth/custom-providers.md) - Build providers
- [API Reference](api-reference.md) - Type definitions
