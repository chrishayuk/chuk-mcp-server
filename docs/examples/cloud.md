# Example: Cloud Deployment

Deploy to Google Cloud Functions.

## Server Code

```python
# main.py
from chuk_mcp_server import tool

@tool
def hello(name: str = "World") -> str:
    """Greet someone."""
    return f"Hello, {name}!"

# Handler automatically exported for GCF
```

## Deploy to GCF

```bash
gcloud functions deploy my-mcp-server \
  --runtime python311 \
  --trigger-http \
  --entry-point handler \
  --allow-unauthenticated
```

## Test

```bash
curl https://REGION-PROJECT.cloudfunctions.net/my-mcp-server/health
```

## Next Steps

- [Cloud Deployment Guide](../deployment/cloud.md) - All platforms
- [Docker Deployment](../deployment/docker.md) - Containers
- [Deployment Guide](../deployment/production.md) - Best practices
