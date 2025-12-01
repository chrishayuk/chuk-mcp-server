# Types API

Type definitions and interfaces.

## OAuth Types

### AuthorizationParams

```python
from chuk_mcp_server.oauth.models import AuthorizationParams

params = AuthorizationParams(
    client_id="client-123",
    redirect_uri="http://localhost:8000/callback",
    response_type="code",
    state="state-123",
    scope="read write",
    code_challenge="challenge",
    code_challenge_method="S256"
)
```

### OAuthToken

```python
from chuk_mcp_server.oauth.models import OAuthToken

token = OAuthToken(
    access_token="token",
    token_type="Bearer",
    expires_in=3600,
    refresh_token="refresh",
    scope="read write"
)
```

### OAuthClientInfo

```python
from chuk_mcp_server.oauth.models import OAuthClientInfo

client = OAuthClientInfo(
    client_id="client-123",
    client_secret="secret",
    client_name="My Client",
    redirect_uris=["http://localhost:8000/callback"]
)
```

## Next Steps

- [OAuth API](oauth.md) - OAuth classes
- [Server API](server.md) - Server class
- [Decorators](decorators.md) - Decorator API
