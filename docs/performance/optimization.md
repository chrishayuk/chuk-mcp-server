# Performance Optimization

Optimize your MCP server for maximum throughput.

## Use Multiple Workers

```python
mcp.run(workers=4)
```

## Enable uvloop

Automatically enabled on Linux/macOS:

```bash
pip install uvloop
```

## Use Async Tools

For I/O-bound operations:

```python
@tool
async def fetch_data(url: str):
    async with httpx.AsyncClient() as client:
        return await client.get(url)
```

## Redis for Sessions

In production:

```bash
export SESSION_PROVIDER=redis
export SESSION_REDIS_URL=redis://localhost:6379
```

## Next Steps

- [Benchmarks](benchmarks.md) - Performance results
- [Production Guide](../deployment/production.md) - Best practices
- [HTTP Mode](../deployment/http-mode.md) - Configuration
