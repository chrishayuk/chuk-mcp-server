# Cloud Deployment

Deploy to AWS, GCP, Azure, or edge platforms.

## Auto-Detection

ChukMCPServer automatically detects cloud platforms:

```python
from chuk_mcp_server import tool, run

@tool
def my_tool():
    return "Hello"

run()  # Automatically optimizes for detected platform
```

## Google Cloud Functions

```python
# main.py
from chuk_mcp_server import tool

@tool
def my_tool():
    return "Hello"

# Automatically exports 'handler' for GCF
```

Deploy:
```bash
gcloud functions deploy my-mcp \
  --runtime python311 \
  --trigger-http \
  --entry-point handler
```

## AWS Lambda

```python
# Automatic Lambda handler export
from chuk_mcp_server import tool, run

@tool
def my_tool():
    return "Hello"

run()
```

## Vercel

```python
# api/index.py
from chuk_mcp_server import tool

@tool
def my_tool():
    return "Hello"

# Auto-detected and configured
```

## Next Steps

- [HTTP Mode](http-mode.md) - Configuration
- [Docker](docker.md) - Containerization
- [Deployment Guide](production.md) - Best practices
