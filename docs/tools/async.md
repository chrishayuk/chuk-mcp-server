# Async Tools

Handle asynchronous operations like HTTP requests, database queries, and file I/O.

## Basic Async Tool

```python
from chuk_mcp_server import tool
import httpx

@tool
async def fetch_data(url: str) -> dict:
    """Fetch data from a URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

## Why Use Async?

- **HTTP requests** - Non-blocking API calls
- **Database queries** - Concurrent database access
- **File I/O** - Async file operations
- **Multiple operations** - Parallel execution

## HTTP Requests

```python
import httpx

@tool
async def get_weather(city: str) -> dict:
    """Get weather for a city."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.weather.com/v1/weather?city={city}"
        )
        return response.json()
```

## Database Operations

```python
import aiosqlite

@tool
async def get_user(user_id: int) -> dict:
    """Get user from database."""
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return {"id": row[0], "name": row[1]}
```

## Parallel Operations

```python
import asyncio
import httpx

@tool
async def fetch_multiple(urls: list[str]) -> list:
    """Fetch multiple URLs in parallel."""
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

## Error Handling

```python
@tool
async def safe_fetch(url: str) -> dict:
    """Fetch with error handling."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
    except httpx.TimeoutException:
        return {"status": "error", "error": "Request timed out"}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error": f"HTTP {e.response.status_code}"}
```

## Next Steps

- [Basic Tools](basic.md) - Synchronous tools
- [Type Validation](types.md) - Type system
- [Error Handling](errors.md) - Error patterns
