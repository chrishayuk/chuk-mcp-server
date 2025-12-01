# Performance Optimization

Get the most out of ChukMCPServer's 39,000+ RPS capability.

## Built-in Optimizations

ChukMCPServer is optimized by default:

✅ **uvloop** - 2-4x faster than standard asyncio
✅ **orjson** - 2-3x faster JSON serialization
✅ **Pre-cached schemas** - Zero overhead at runtime
✅ **Smart worker count** - Optimized for your CPU
✅ **Connection pooling** - Efficient resource usage

## Worker Configuration

Optimize worker count for your workload:

```python
from chuk_mcp_server import ChukMCPServer
import os

mcp = ChukMCPServer(name="my-server")

# Auto-detect (recommended)
mcp.run()  # Uses (CPU count * 2) + 1

# Manual override
mcp.run(workers=16)

# Environment variable
# export CHUK_WORKERS=16
mcp.run()
```

Worker count guidelines:
- **I/O bound** (databases, APIs): `(CPU count * 2) + 1`
- **CPU bound**: `CPU count`
- **Mixed**: `CPU count * 1.5`

## Async Everything

Use async for I/O operations:

```python
from chuk_mcp_server import tool
import httpx

# ❌ Slow: blocking I/O
@tool
def fetch_data(url: str) -> dict:
    import requests
    return requests.get(url).json()

# ✅ Fast: async I/O
@tool
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

## Connection Pooling

Reuse connections for databases and APIs:

```python
from chuk_mcp_server import ChukMCPServer
import httpx
import asyncpg

mcp = ChukMCPServer(name="my-server")

# Global connection pool
http_client = httpx.AsyncClient()
db_pool = None

async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(
        'postgresql://user:pass@localhost/db',
        min_size=10,
        max_size=20
    )

@mcp.tool
async def query_database(query: str) -> list:
    async with db_pool.acquire() as conn:
        return await conn.fetch(query)

@mcp.tool
async def fetch_api(url: str) -> dict:
    response = await http_client.get(url)
    return response.json()

if __name__ == "__main__":
    import asyncio
    asyncio.run(startup())
    mcp.run()
```

## Caching

Cache expensive computations:

```python
from chuk_mcp_server import tool
from functools import lru_cache
import asyncio

# Sync caching
@lru_cache(maxsize=1000)
def expensive_computation(x: int) -> int:
    return x ** 2

@tool
def compute(x: int) -> int:
    return expensive_computation(x)

# Async caching
from aiocache import cached

@tool
@cached(ttl=60)  # Cache for 60 seconds
async def fetch_expensive_data(key: str) -> dict:
    # Expensive operation
    await asyncio.sleep(1)
    return {"data": key}
```

## Batching

Batch requests for efficiency:

```python
from chuk_mcp_server import tool
from typing import List

@tool
async def batch_query(ids: List[int]) -> List[dict]:
    """Query multiple records at once."""
    async with db_pool.acquire() as conn:
        # Single query instead of N queries
        results = await conn.fetch(
            "SELECT * FROM items WHERE id = ANY($1)",
            ids
        )
        return [dict(r) for r in results]
```

## Profiling

Identify bottlenecks:

```python
from chuk_mcp_server import tool
import time
import logging

logger = logging.getLogger(__name__)

@tool
async def slow_tool():
    start = time.perf_counter()
    
    # Your logic
    result = await compute_something()
    
    duration = time.perf_counter() - start
    logger.info(f"slow_tool took {duration:.3f}s")
    
    return result
```

## Memory Optimization

Reduce memory usage:

```python
from chuk_mcp_server import tool
from typing import Iterator

# ❌ Memory intensive
@tool
def process_large_file(path: str) -> list:
    with open(path) as f:
        return [line.strip() for line in f]

# ✅ Memory efficient
@tool
def process_large_file(path: str) -> str:
    count = 0
    with open(path) as f:
        for line in f:
            count += 1
    return f"Processed {count} lines"
```

## Load Testing

Benchmark your server:

```bash
# Using Apache Bench
ab -n 10000 -c 100 http://localhost:8000/mcp

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/mcp

# Using hey
hey -n 10000 -c 100 http://localhost:8000/mcp
```

ChukMCPServer benchmark:

```bash
python benchmarks/ultra_minimal_mcp_performance_test.py
```

Expected results:
- Simple tools: 35,000-40,000 RPS
- Database queries: 15,000-25,000 RPS
- External APIs: 5,000-15,000 RPS

## Monitoring

Track performance in production:

```python
from chuk_mcp_server import ChukMCPServer
from prometheus_client import Counter, Histogram
import time

# Metrics
request_count = Counter('mcp_requests_total', 'Total requests')
request_duration = Histogram('mcp_request_duration_seconds', 'Request duration')

mcp = ChukMCPServer(name="my-server")

@mcp.app.middleware("http")
async def metrics_middleware(request, call_next):
    request_count.inc()
    
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    
    request_duration.observe(duration)
    
    return response

mcp.run()
```

## Next Steps

- [Benchmarks](../performance/benchmarks.md) - Performance testing
- [Optimization](../performance/optimization.md) - More tips
- [Production](../deployment/production.md) - Deployment
