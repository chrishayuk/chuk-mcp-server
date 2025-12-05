# Server Composition

Compose multiple MCP servers or integrate with existing applications.

## Multiple Tool Sets

Organize tools across modules:

```python
# tools/math.py
from chuk_mcp_server import tool

@tool
def add(a: int, b: int) -> int:
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    return a * b
```

```python
# tools/text.py
from chuk_mcp_server import tool

@tool
def uppercase(text: str) -> str:
    return text.upper()

@tool
def reverse(text: str) -> str:
    return text[::-1]
```

```python
# main.py
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(name="composite-server")

# Import all tool modules
import tools.math
import tools.text

mcp.run()
```

## Composing Servers

Combine multiple server configurations:

```python
from chuk_mcp_server import ChukMCPServer

# Base server
base_mcp = ChukMCPServer(name="base-server")

@base_mcp.tool
def core_function():
    return "core"

# Extended server (inherits base tools)
extended_mcp = ChukMCPServer(name="extended-server")

# Copy tools from base
for tool_name, tool_handler in base_mcp._tool_handlers.items():
    extended_mcp._tool_handlers[tool_name] = tool_handler

@extended_mcp.tool
def extended_function():
    return "extended"

extended_mcp.run()
```

## Integration with FastAPI

Integrate ChukMCPServer into existing FastAPI app:

```python
from fastapi import FastAPI
from chuk_mcp_server import ChukMCPServer

# Existing FastAPI app
app = FastAPI()

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI"}

# Add MCP server
mcp = ChukMCPServer(name="my-server")

@mcp.tool
def mcp_tool():
    return "MCP tool result"

# Mount MCP routes
app.mount("/mcp", mcp.app)

# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Integration with Starlette

Direct Starlette integration:

```python
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from chuk_mcp_server import ChukMCPServer

async def homepage(request):
    return JSONResponse({'hello': 'world'})

# Create MCP server
mcp = ChukMCPServer(name="my-server")

@mcp.tool
def my_tool():
    return "result"

# Compose routes
routes = [
    Route('/', homepage),
    Mount('/mcp', app=mcp.app),
]

app = Starlette(routes=routes)
```

## Plugin Architecture

Create a plugin system:

```python
# plugin_base.py
from abc import ABC, abstractmethod
from chuk_mcp_server import ChukMCPServer

class MCPPlugin(ABC):
    @abstractmethod
    def register(self, mcp: ChukMCPServer):
        """Register plugin tools with MCP server."""
        pass
```

```python
# plugins/calculator.py
from plugin_base import MCPPlugin
from chuk_mcp_server import ChukMCPServer

class CalculatorPlugin(MCPPlugin):
    def register(self, mcp: ChukMCPServer):
        @mcp.tool
        def add(a: int, b: int) -> int:
            return a + b
        
        @mcp.tool
        def subtract(a: int, b: int) -> int:
            return a - b
```

```python
# plugins/weather.py
from plugin_base import MCPPlugin
from chuk_mcp_server import ChukMCPServer

class WeatherPlugin(MCPPlugin):
    def register(self, mcp: ChukMCPServer):
        @mcp.tool
        def get_weather(city: str) -> dict:
            return {"city": city, "temp": 72}
```

```python
# main.py
from chuk_mcp_server import ChukMCPServer
from plugins.calculator import CalculatorPlugin
from plugins.weather import WeatherPlugin

mcp = ChukMCPServer(name="plugin-server")

# Register plugins
plugins = [
    CalculatorPlugin(),
    WeatherPlugin(),
]

for plugin in plugins:
    plugin.register(mcp)

mcp.run()
```

## Dynamic Tool Loading

Load tools dynamically:

```python
import importlib
import pkgutil
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(name="dynamic-server")

# Discover and load all modules in 'tools' package
import tools
for importer, modname, ispkg in pkgutil.iter_modules(tools.__path__):
    module = importlib.import_module(f'tools.{modname}')
    print(f"Loaded tools from {modname}")

mcp.run()
```

## Shared State

Share state between tools:

```python
from chuk_mcp_server import ChukMCPServer
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServerState:
    user_count: int = 0
    cache: dict = None
    
    def __post_init__(self):
        if self.cache is None:
            self.cache = {}

# Create shared state
state = ServerState()

mcp = ChukMCPServer(name="stateful-server")

@mcp.tool
def increment_users() -> int:
    state.user_count += 1
    return state.user_count

@mcp.tool
def get_users() -> int:
    return state.user_count

@mcp.tool
def cache_value(key: str, value: str) -> str:
    state.cache[key] = value
    return f"Cached {key}"

@mcp.tool
def get_cached(key: str) -> Optional[str]:
    return state.cache.get(key)

mcp.run()
```

## Next Steps

- [Configuration](configuration.md) - Advanced configuration
- [Performance](performance.md) - Optimization
- [Production](../deployment/production.md) - Deployment
