# Docker Deployment

Deploy your MCP server with Docker.

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install dependencies
RUN uv pip install --system .

# Run server
CMD ["python", "-m", "my_server"]
```

## Docker Compose

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MCP_LOG_LEVEL=info
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Build and Run

```bash
# Build image
docker build -t my-mcp-server .

# Run container
docker run -p 8000:8000 my-mcp-server

# With Docker Compose
docker-compose up
```

## Next Steps

- [HTTP Mode](http-mode.md) - HTTP configuration
- [Cloud Deployment](cloud.md) - Cloud platforms
- [Production Guide](production.md) - Best practices
