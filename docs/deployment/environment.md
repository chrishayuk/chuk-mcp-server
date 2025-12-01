# Environment Variables

Configure ChukMCPServer with environment variables.

## Server Configuration

```bash
# Server settings
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
export MCP_LOG_LEVEL=info
export MCP_WORKERS=4
```

## OAuth Configuration

```bash
# Session storage
export SESSION_PROVIDER=redis
export SESSION_REDIS_URL=redis://localhost:6379/0

# Token TTLs
export OAUTH_AUTH_CODE_TTL=600
export OAUTH_ACCESS_TOKEN_TTL=900
export OAUTH_REFRESH_TOKEN_TTL=86400
export OAUTH_EXTERNAL_TOKEN_TTL=5184000
```

## Google Drive OAuth

```bash
export GOOGLE_CLIENT_ID=your-client-id
export GOOGLE_CLIENT_SECRET=your-client-secret
export GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback
export OAUTH_SERVER_URL=http://localhost:8000
```

## Next Steps

- [Production Guide](production.md) - Best practices
- [OAuth Overview](../oauth/overview.md) - Authentication
- [HTTP Mode](http-mode.md) - HTTP configuration
