# Example: Database Server

CRUD operations with SQLite.

## Complete Server

```python
from chuk_mcp_server import ChukMCPServer, tool
import aiosqlite

mcp = ChukMCPServer("database")

@mcp.tool
async def create_user(name: str, email: str) -> dict:
    """Create a new user."""
    async with aiosqlite.connect("app.db") as db:
        cursor = await db.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (name, email)
        )
        await db.commit()
        return {"id": cursor.lastrowid, "name": name, "email": email}

@mcp.tool
async def get_user(user_id: int) -> dict:
    """Get user by ID."""
    async with aiosqlite.connect("app.db") as db:
        cursor = await db.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return {"status": "not_found"}
        return {"id": row[0], "name": row[1], "email": row[2]}

if __name__ == "__main__":
    mcp.run()
```

## Next Steps

- [Calculator Example](calculator.md) - Basic tools
- [Weather Example](weather.md) - Async operations
- [OAuth Example](oauth.md) - Authentication
