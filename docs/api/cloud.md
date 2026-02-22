# Cloud API

API reference for cloud platform support.

## Auto-Detection

Cloud platforms are detected automatically:

```python
from chuk_mcp_server import run

run()  # Auto-detects and optimizes
```

## Detected Platforms

- Google Cloud Platform (GCF, Cloud Run)
- AWS (Lambda, ECS, Fargate)
- Azure (Functions, Container Apps)
- Vercel, Netlify, Cloudflare Workers

## Cloud Adapters

Advanced usage:

```python
from chuk_mcp_server.cloud import get_cloud_adapter

adapter = get_cloud_adapter()
if adapter:
    print(f"Running on: {adapter.platform}")
```

## Next Steps

- [Cloud Deployment](../deployment/cloud.md) - Deploy guide
- [Docker](../deployment/docker.md) - Containers
- [Deployment Guide](../deployment/production.md) - Best practices
