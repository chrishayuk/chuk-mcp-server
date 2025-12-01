# Your First Server

A step-by-step tutorial to build your first MCP server with ChukMCPServer.

## What We'll Build

A weather information server with:
- Current weather lookup
- Temperature conversion
- Weather alerts

Estimated time: **10 minutes**

## Step 1: Create the Project

Using the scaffolder (recommended):

```bash
uvx chuk-mcp-server init weather-server
cd weather-server
```

This creates:
```
weather-server/
├── pyproject.toml
├── src/
│   └── weather_server/
│       ├── __init__.py
│       └── server.py
├── tests/
│   └── test_server.py
└── README.md
```

## Step 2: Define Your Tools

Edit `src/weather_server/server.py`:

```python
from chuk_mcp_server import ChukMCPServer, tool

mcp = ChukMCPServer("weather-server")

@mcp.tool
def get_weather(city: str) -> dict:
    """
    Get current weather for a city.

    Args:
        city: Name of the city

    Returns:
        Weather information including temperature and conditions
    """
    # In production, call a real weather API
    # For demo, return mock data
    return {
        "city": city,
        "temperature": 72,
        "condition": "sunny",
        "humidity": 45,
        "wind_speed": 5
    }

@mcp.tool
def convert_temperature(temp: float, from_unit: str, to_unit: str) -> float:
    """
    Convert temperature between Celsius and Fahrenheit.

    Args:
        temp: Temperature value
        from_unit: Source unit ('C' or 'F')
        to_unit: Target unit ('C' or 'F')

    Returns:
        Converted temperature
    """
    if from_unit == 'F' and to_unit == 'C':
        return (temp - 32) * 5/9
    elif from_unit == 'C' and to_unit == 'F':
        return (temp * 9/5) + 32
    else:
        return temp

if __name__ == "__main__":
    mcp.run()
```

## Step 3: Run the Server

```bash
uv run weather-server
```

You should see:
```
ChukMCPServer initialized
📋 2 tools registered
🚀 Server running on stdio transport
```

## Step 4: Test the Server

### Option A: Command Line Test

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | uv run weather-server
```

You should see your tools listed.

### Option B: HTTP Mode (for testing)

Modify `server.py`:

```python
if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
```

Then test with curl:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/tools/list
```

## Step 5: Add Type Safety

ChukMCPServer automatically validates types. Try it:

```python
@mcp.tool
def calculate_heat_index(temperature: float, humidity: int) -> dict:
    """
    Calculate heat index.

    Args:
        temperature: Temperature in Fahrenheit (must be float)
        humidity: Relative humidity (must be int, 0-100)

    Returns:
        Heat index calculation results
    """
    if not 0 <= humidity <= 100:
        raise ValueError("Humidity must be between 0 and 100")

    # Simplified heat index formula
    heat_index = temperature + (0.5 * humidity)

    return {
        "temperature": temperature,
        "humidity": humidity,
        "heat_index": round(heat_index, 1),
        "warning": "extreme" if heat_index > 105 else "normal"
    }
```

The types are automatically validated - if someone calls with a string instead of a number, they'll get a clear error message.

## Step 6: Add Async Tools

For external API calls, use async:

```python
import httpx

@mcp.tool
async def fetch_forecast(city: str, days: int = 5) -> dict:
    """
    Fetch weather forecast from external API.

    Args:
        city: City name
        days: Number of days to forecast (default: 5)

    Returns:
        Forecast data
    """
    # Example: Call real weather API
    async with httpx.AsyncClient() as client:
        # Replace with real API
        url = f"https://api.weather.com/forecast?city={city}&days={days}"
        response = await client.get(url)
        return response.json()
```

## Step 7: Add Resources

Resources provide data that tools can read:

```python
from chuk_mcp_server import resource

@mcp.resource("weather://config")
def get_config() -> dict:
    """Server configuration."""
    return {
        "api_key": "your-api-key",  # In production, use env vars!
        "default_units": "imperial",
        "cache_timeout": 300
    }

@mcp.resource("weather://cities")
def get_supported_cities() -> list:
    """List of supported cities."""
    return [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix"
    ]
```

## Step 8: Add Error Handling

```python
from typing import Optional

@mcp.tool
def get_weather_safe(city: str) -> dict:
    """Get weather with error handling."""
    try:
        # Your weather API call here
        if city.lower() == "invalid":
            raise ValueError(f"City '{city}' not found")

        return {
            "city": city,
            "status": "success",
            "data": {"temperature": 72, "condition": "sunny"}
        }
    except ValueError as e:
        return {
            "city": city,
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        return {
            "city": city,
            "status": "error",
            "error": "An unexpected error occurred"
        }
```

## Step 9: Write Tests

Edit `tests/test_server.py`:

```python
import pytest
from weather_server.server import mcp

def test_temperature_conversion():
    """Test temperature conversion tool."""
    # Get the tool function
    tool_func = mcp._tool_handlers["convert_temperature"].func

    # Test F to C
    result = tool_func(temp=32, from_unit='F', to_unit='C')
    assert result == 0

    # Test C to F
    result = tool_func(temp=0, from_unit='C', to_unit='F')
    assert result == 32

def test_heat_index():
    """Test heat index calculation."""
    tool_func = mcp._tool_handlers["calculate_heat_index"].func

    result = tool_func(temperature=90, humidity=60)
    assert "heat_index" in result
    assert result["temperature"] == 90
    assert result["humidity"] == 60
```

Run tests:

```bash
uv run pytest
```

## Complete Example

Here's the complete server:

```python
from chuk_mcp_server import ChukMCPServer, tool, resource
import httpx
from typing import Optional

mcp = ChukMCPServer("weather-server")

@mcp.tool
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    return {
        "city": city,
        "temperature": 72,
        "condition": "sunny",
        "humidity": 45
    }

@mcp.tool
def convert_temperature(temp: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between C and F."""
    if from_unit == 'F' and to_unit == 'C':
        return (temp - 32) * 5/9
    elif from_unit == 'C' and to_unit == 'F':
        return (temp * 9/5) + 32
    return temp

@mcp.tool
def calculate_heat_index(temperature: float, humidity: int) -> dict:
    """Calculate heat index from temperature and humidity."""
    if not 0 <= humidity <= 100:
        raise ValueError("Humidity must be 0-100")

    heat_index = temperature + (0.5 * humidity)
    return {
        "heat_index": round(heat_index, 1),
        "warning": "extreme" if heat_index > 105 else "normal"
    }

@mcp.resource("weather://config")
def get_config() -> dict:
    """Server configuration."""
    return {
        "default_units": "imperial",
        "cache_timeout": 300
    }

if __name__ == "__main__":
    mcp.run()
```

## Next Steps

- [Add to Claude Desktop](claude-desktop.md) - Use your server with Claude
- [Building Tools](../tools/basic.md) - Learn advanced tool patterns
- [Deployment](../deployment/http-mode.md) - Deploy to production
- [Examples](../examples/weather.md) - See the complete weather server

## Common Issues

**Tools not appearing?**

Make sure you're using `@mcp.tool` not just `@tool` if using the server-based API.

**Type validation errors?**

Check that your type hints match the actual data you're passing.

**Async tools not working?**

Make sure you're using `async def` and `await` for async operations.
