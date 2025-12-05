# Token Management

Understanding how ChukMCPServer manages OAuth tokens.

## Token Types

### 1. Authorization Codes
Temporary codes exchanged for access tokens.

**Lifetime**: 10 minutes (default)

```bash
export OAUTH_AUTH_CODE_TTL=600  # 10 minutes
```

### 2. Access Tokens
Short-lived tokens for API calls.

**Lifetime**: 15 minutes (default)

```bash
export OAUTH_ACCESS_TOKEN_TTL=900  # 15 minutes
```

### 3. Refresh Tokens
Used to obtain new access tokens.

**Lifetime**: 1 day (default)

```bash
export OAUTH_REFRESH_TOKEN_TTL=86400  # 1 day
```

### 4. External Tokens
Tokens from external providers (Google, LinkedIn, etc.).

**Lifetime**: 60 days (default, auto-refreshed)

```bash
export OAUTH_EXTERNAL_TOKEN_TTL=5184000  # 60 days
```

## Token Storage

### Development (Memory)

```python
from chuk_mcp_server.oauth import TokenStore

# Automatic - no configuration needed
token_store = TokenStore(sandbox_id="my-app")
```

### Production (Redis)

```bash
export SESSION_PROVIDER=redis
export SESSION_REDIS_URL=redis://localhost:6379/0
```

```python
# Automatically uses Redis
token_store = TokenStore(sandbox_id="my-app")
```

## Token Lifecycle

### 1. Authorization Flow

```
Client → /oauth/authorize
  ↓
Server generates auth code (10 min TTL)
  ↓
Client → /oauth/token (exchanges code)
  ↓
Server returns access + refresh tokens
```

### 2. Token Refresh

```
Client → /oauth/token (with refresh token)
  ↓
Server validates refresh token
  ↓
Server returns new access + refresh tokens
```

### 3. External Token Refresh

```
Tool call → validate access token
  ↓
Check external token expiry
  ↓
If expired: refresh with external provider
  ↓
Update stored token
  ↓
Inject into tool
```

## Configuration

All TTLs are configurable via environment variables:

```bash
# Authorization codes
export OAUTH_AUTH_CODE_TTL=600              # 10 minutes

# Access tokens
export OAUTH_ACCESS_TOKEN_TTL=900           # 15 minutes

# Refresh tokens
export OAUTH_REFRESH_TOKEN_TTL=86400        # 1 day

# External tokens
export OAUTH_EXTERNAL_TOKEN_TTL=5184000     # 60 days
```

## Security Best Practices

### 1. Short Access Token TTL
Keep access tokens short-lived:

```bash
export OAUTH_ACCESS_TOKEN_TTL=900  # 15 minutes max
```

### 2. Rotate Refresh Tokens
New refresh token issued on each refresh:

```python
# Automatic - new refresh token returned
```

### 3. Secure Storage
Use Redis in production:

```bash
export SESSION_PROVIDER=redis
export SESSION_REDIS_URL=redis://localhost:6379/0
```

### 4. Sandbox Isolation
Isolate tokens by tenant:

```python
token_store = TokenStore(sandbox_id=f"app-{tenant_id}")
```

## Monitoring

### Check Token Stats

```python
# In your provider
stats = await token_store.get_stats()
print(f"Active tokens: {stats['active_tokens']}")
```

### Cleanup Expired Tokens

Automatic in Redis (uses TTL).
Manual cleanup for memory store:

```python
# Called automatically, but can trigger manually
await token_store.cleanup_expired()
```

## Next Steps

- [Protected Tools](protected-tools.md) - Using tokens in tools
- [Custom Providers](custom-providers.md) - Implementing providers
- [OAuth Overview](overview.md) - Complete guide
