# Production Guide

Best practices for deploying MCP servers to production.

## Configuration

Use environment variables:

```bash
export MCP_LOG_LEVEL=info
export MCP_WORKERS=4
export SESSION_PROVIDER=redis
export SESSION_REDIS_URL=redis://localhost:6379
```

## Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

mcp.run(log_level="info")
```

## Health Checks

```bash
curl http://localhost:8000/health
```

## Monitoring

- Use `/health` endpoint
- Monitor response times
- Track error rates
- Set up alerts

## Security

1. Use HTTPS
2. Validate inputs
3. Rate limiting
4. Authentication required
5. Keep dependencies updated

## Next Steps

- [HTTP Mode](http-mode.md) - HTTP setup
- [Docker](docker.md) - Containerization
- [Cloud](cloud.md) - Cloud deployment
