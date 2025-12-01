# Example: Weather Server

Async tools with external API integration.

## Complete Server

```python
from chuk_mcp_server import ChukMCPServer, tool
import httpx
import os

mcp = ChukMCPServer("weather")

API_KEY = os.getenv("WEATHER_API_KEY", "demo")

@mcp.tool
async def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": API_KEY, "units": "imperial"}
        )
        data = response.json()
        return {
            "city": city,
            "temperature": data["main"]["temp"],
            "condition": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"]
        }

@mcp.tool
def convert_temp(temp: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between C and F."""
    if from_unit == "F" and to_unit == "C":
        return (temp - 32) * 5/9
    elif from_unit == "C" and to_unit == "F":
        return (temp * 9/5) + 32
    return temp

if __name__ == "__main__":
    mcp.run()
```

## Next Steps

- [Calculator Example](calculator.md) - Basic tools
- [Database Example](database.md) - CRUD operations
- [OAuth Example](oauth.md) - Authentication
