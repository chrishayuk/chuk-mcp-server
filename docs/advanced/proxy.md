# Proxy and Reverse Proxy

Deploy ChukMCPServer behind a proxy or load balancer.

## Nginx Reverse Proxy

Basic Nginx configuration:

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # SSE support (for MCP streaming)
        proxy_buffering off;
        proxy_set_header X-Accel-Buffering no;
    }
}
```

With SSL:

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE support
        proxy_buffering off;
        proxy_set_header X-Accel-Buffering no;
    }
}
```

## Apache Reverse Proxy

Enable required modules:

```bash
a2enmod proxy
a2enmod proxy_http
a2enmod proxy_wstunnel
a2enmod ssl
systemctl restart apache2
```

Configuration:

```apache
<VirtualHost *:443>
    ServerName api.example.com

    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem

    ProxyPreserveHost On
    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/
    
    # SSE support
    ProxyPass / http://localhost:8000/ disablereuse=on
</VirtualHost>
```

## Traefik

Docker Compose with Traefik:

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  mcp-server:
    image: your-mcp-server
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp.rule=Host(`api.example.com`)"
      - "traefik.http.routers.mcp.entrypoints=websecure"
      - "traefik.http.routers.mcp.tls=true"
      - "traefik.http.services.mcp.loadbalancer.server.port=8000"
```

## Caddy

Simplest option with automatic HTTPS:

```caddy
api.example.com {
    reverse_proxy localhost:8000 {
        # SSE support
        flush_interval -1
    }
}
```

Run Caddy:

```bash
caddy run --config Caddyfile
```

## Load Balancing

Nginx with multiple backend servers:

```nginx
upstream mcp_servers {
    least_conn;  # Use least connections algorithm
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://mcp_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # SSE support
        proxy_buffering off;
        proxy_set_header X-Accel-Buffering no;
    }
}
```

Start multiple ChukMCPServer instances:

```bash
# Terminal 1
PORT=8000 python server.py

# Terminal 2
PORT=8001 python server.py

# Terminal 3
PORT=8002 python server.py

# Terminal 4
PORT=8003 python server.py
```

## Health Checks

Add health endpoint:

```python
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(name="my-server")

@mcp.app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

mcp.run()
```

Nginx health check:

```nginx
upstream mcp_servers {
    server localhost:8000 max_fails=3 fail_timeout=30s;
    server localhost:8001 max_fails=3 fail_timeout=30s;
}
```

## CORS with Proxy

ChukMCPServer handles CORS automatically, but if needed:

```python
from chuk_mcp_server import ChukMCPServer
from starlette.middleware.cors import CORSMiddleware

mcp = ChukMCPServer(name="my-server")

mcp.app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp.run()
```

## Next Steps

- [Production](../deployment/production.md) - Production best practices
- [Docker](../deployment/docker.md) - Containerization
- [Cloud](../deployment/cloud.md) - Cloud deployment
