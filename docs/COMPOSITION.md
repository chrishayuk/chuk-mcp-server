# Server Composition & Deployment

ChukMCPServer supports composing multiple MCP servers into a single unified server through configuration. This enables you to aggregate tools, resources, and prompts from multiple sources without writing code.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [Composition Strategies](#composition-strategies)
- [Examples](#examples)

## Quick Start

### 1. Configuration-Only Deployment

Create a `config.yaml` file:

```yaml
server:
  name: "my-composed-server"
  transport: "http"
  http:
    host: "0.0.0.0"
    port: 8000

composition:
  import:
    - name: "github"
      enabled: true
      type: "stdio"
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-github"]
      prefix: "github"
      env:
        GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"

    - name: "weather"
      enabled: true
      type: "stdio"
      command: "python"
      args: ["-m", "mcp_server_weather"]
      prefix: "weather"
```

### 2. Deploy with Docker

```bash
# One-time setup
./deploy.sh setup

# Edit .env with your credentials
vim .env

# Start the server
./deploy.sh start

# View logs
./deploy.sh logs
```

Your composed server is now running at `http://localhost:8000` with tools from both GitHub and Weather servers!

## Configuration

### Server Section

```yaml
server:
  name: "my-server"           # Server name
  version: "1.0.0"            # Version
  description: "My Server"    # Description
  transport: "http"           # "http" or "stdio"

  # HTTP configuration
  http:
    host: "0.0.0.0"
    port: 8000
    workers: 4

  # STDIO configuration
  stdio:
    log_to_stderr: true
```

### Composition Section

The `composition` section defines how to combine multiple servers:

#### Import (Static Copy)

Import creates a one-time copy of components from another server. Changes to the source server after import won't be reflected.

```yaml
composition:
  import:
    - name: "github"                    # Server identifier
      enabled: true                     # Enable/disable
      type: "stdio"                     # "stdio", "http", or "sse"
      command: "npx"                    # Command to run
      args: ["-y", "@modelcontextprotocol/server-github"]
      prefix: "github"                  # Namespace prefix
      components: ["tools", "resources"] # What to import
      tags: ["public"]                  # Optional tag filtering
      env:                              # Environment variables
        GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
```

**Supported Types:**
- `stdio`: Standard MCP protocol over stdin/stdout
- `http`: HTTP-based MCP server
- `sse`: Server-Sent Events transport

#### Mount (Dynamic Delegation)

Mount creates a live link to another server. Changes are reflected in real-time.

```yaml
composition:
  mount:
    - name: "api_service"
      enabled: true
      type: "http"
      url: "http://api.example.com/mcp"
      prefix: "api"
      as_proxy: true
      timeout: 30
      headers:
        Authorization: "Bearer ${API_TOKEN}"
```

### Modules Section

Load Python modules with tools directly:

```yaml
modules:
  math:
    enabled: true
    location: "./modules"
    module: "math_tools.tools"
    namespace: "math"

  database:
    enabled: false
    location: "./modules"
    module: "db_tools.tools"
    namespace: "db"
```

### Logging Section

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

  # Per-logger configuration
  loggers:
    "chuk_mcp_server.proxy": "WARNING"
    "chuk_mcp_server.composition": "INFO"
```

## Docker Deployment

### Single Server

```bash
# Build and start
docker-compose up -d mcp-server

# View logs
docker-compose logs -f mcp-server

# Stop
docker-compose down
```

### Multiple Profiles

```bash
# Production with Nginx
docker-compose --profile production up -d

# Development with hot reload
docker-compose --profile dev up

# With Redis cache
docker-compose --profile cache up -d
```

### Custom Dockerfile Build

```bash
# Build
docker build -t my-mcp-server .

# Run
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/.env:/app/.env \
  --name mcp-server \
  my-mcp-server
```

## Composition Strategies

### 1. Aggregation Pattern

Combine multiple specialized servers into one unified API:

```yaml
composition:
  import:
    - name: "github"
      prefix: "github"
      ...
    - name: "slack"
      prefix: "slack"
      ...
    - name: "notion"
      prefix: "notion"
      ...
```

**Result:** Single server with `github.*`, `slack.*`, and `notion.*` tools.

### 2. Gateway Pattern

Mount remote servers as proxy for centralized access:

```yaml
composition:
  mount:
    - name: "team_a_server"
      url: "http://team-a.internal:8000"
      prefix: "team_a"
      as_proxy: true

    - name: "team_b_server"
      url: "http://team-b.internal:8000"
      prefix: "team_b"
      as_proxy: true
```

**Result:** Gateway server that delegates to team servers.

### 3. Hybrid Pattern

Mix imported and mounted servers:

```yaml
composition:
  import:
    # Static servers (stable, version-controlled)
    - name: "core_tools"
      type: "stdio"
      ...

  mount:
    # Dynamic servers (frequently updated)
    - name: "experimental_features"
      url: "http://dev.internal:8000"
      as_proxy: true
```

## Examples

### Example 1: Developer Productivity Suite

Combine GitHub, Slack, and Jira:

```yaml
server:
  name: "dev-productivity"
  transport: "http"

composition:
  import:
    - name: "github"
      type: "stdio"
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-github"]
      prefix: "github"
      env:
        GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"

    - name: "slack"
      type: "stdio"
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-slack"]
      prefix: "slack"
      env:
        SLACK_BOT_TOKEN: "${SLACK_TOKEN}"

modules:
  jira:
    enabled: true
    location: "./modules"
    module: "jira_tools.tools"
    namespace: "jira"
```

**Deploy:**

```bash
# Set tokens in .env
export GITHUB_TOKEN=ghp_yourtoken
export SLACK_TOKEN=xoxb-yourtoken

# Start
./deploy.sh start
```

### Example 2: Multi-Region API Gateway

```yaml
server:
  name: "api-gateway"
  transport: "http"

composition:
  mount:
    - name: "us_east"
      url: "http://us-east-api.internal"
      prefix: "us_east"
      as_proxy: true

    - name: "eu_west"
      url: "http://eu-west-api.internal"
      prefix: "eu_west"
      as_proxy: true

    - name: "ap_south"
      url: "http://ap-south-api.internal"
      prefix: "ap_south"
      as_proxy: true
```

### Example 3: Microservices Aggregator

```yaml
composition:
  mount:
    - name: "user_service"
      url: "http://users:8000"
      prefix: "users"

    - name: "payment_service"
      url: "http://payments:8000"
      prefix: "payments"

    - name: "notification_service"
      url: "http://notifications:8000"
      prefix: "notifications"
```

## Environment Variables

Use `${VAR_NAME}` syntax in configuration:

```yaml
composition:
  import:
    - name: "github"
      env:
        GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
        API_URL: "${GITHUB_API_URL:-https://api.github.com}"
```

Create `.env` file:

```bash
GITHUB_TOKEN=ghp_yourtoken
GITHUB_API_URL=https://api.github.com
```

## Programmatic Usage

Use the composition API in Python:

```python
from chuk_mcp_server import ChukMCPServer
from chuk_mcp_server.composition import load_from_config

# Create server
mcp = ChukMCPServer()

# Load composition from config
config, stats = load_from_config("config.yaml", mcp.composition)

print(f"Loaded: {stats}")
# {"imported": 2, "mounted": 1, "modules": 1}

# Run server
mcp.run()
```

## Best Practices

### 1. Namespacing

Always use prefixes to avoid name collisions:

```yaml
composition:
  import:
    - name: "github"
      prefix: "github"  # Tools: github.create_issue

    - name: "gitlab"
      prefix: "gitlab"  # Tools: gitlab.create_issue
```

### 2. Security

- Store secrets in `.env` files
- Never commit `.env` to version control
- Use environment-specific configurations

```yaml
# Production config.yaml
composition:
  import:
    - name: "github"
      env:
        GITHUB_TOKEN: "${PROD_GITHUB_TOKEN}"

# Development config.yaml
composition:
  import:
    - name: "github"
      env:
        GITHUB_TOKEN: "${DEV_GITHUB_TOKEN}"
```

### 3. Resource Management

Enable only what you need:

```yaml
composition:
  import:
    - name: "large_server"
      enabled: false  # Disable when not needed
      components: ["tools"]  # Only import tools, not resources
```

### 4. Health Monitoring

Use health checks in production:

```yaml
# docker-compose.yaml
services:
  mcp-server:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Troubleshooting

### Server Won't Start

1. Check configuration syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. Check logs:
   ```bash
   ./deploy.sh logs
   ```

3. Verify environment variables:
   ```bash
   grep -v '^#' .env | grep -v '^$'
   ```

### Tool Not Found

1. Check prefix is correct
2. Verify server is enabled in config
3. Check import/mount succeeded in logs

### Connection Issues

1. Verify URL is accessible
2. Check firewall rules
3. Verify credentials in `.env`

## Next Steps

- [Configuration Reference](./CONFIG_REFERENCE.md)
- [Security Guide](./SECURITY.md)
- [Performance Tuning](./PERFORMANCE.md)
- [Examples](../examples/)
