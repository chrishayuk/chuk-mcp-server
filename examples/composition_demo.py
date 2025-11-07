#!/usr/bin/env python3
"""
Server Composition Demo

Demonstrates the new import_server() and mount() methods for composing
multiple MCP servers together.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chuk_mcp_server import ChukMCPServer

# ============================================================================
# Create Sub-Servers
# ============================================================================

# Weather Server
weather_server = ChukMCPServer(name="Weather Service", version="1.0.0")


@weather_server.tool
def get_forecast(city: str, days: int = 3) -> dict:
    """Get weather forecast for a city."""
    return {"city": city, "days": days, "forecast": "Sunny", "temp": 72}


@weather_server.tool
def get_alerts(city: str) -> dict:
    """Get weather alerts for a city."""
    return {"city": city, "alerts": ["No alerts"], "severity": "none"}


# Data Server
data_server = ChukMCPServer(name="Data Service", version="1.0.0")


@data_server.tool
def fetch_data(endpoint: str) -> dict:
    """Fetch data from an endpoint."""
    return {"endpoint": endpoint, "status": "success", "data": {"key": "value"}}


@data_server.tool
def transform_data(data: dict, operation: str = "uppercase") -> dict:
    """Transform data."""
    return {"operation": operation, "result": data, "status": "transformed"}


# ============================================================================
# Main Server with Composition
# ============================================================================

main_server = ChukMCPServer(name="Composite Service", version="1.0.0", debug=True, port=8002)


# Local tool on main server
@main_server.tool
def main_health() -> dict:
    """Check health of main server."""
    stats = main_server.get_composition_stats()
    return {"status": "healthy", "composition": stats}


# ============================================================================
# Demonstrate import_server() - Static Composition
# ============================================================================

print("=" * 70)
print("Server Composition Demo")
print("=" * 70)
print()
print("1. Static Composition (import_server):")
print("   - One-time copy of server components")
print("   - Changes to original server NOT reflected")
print()

# Import weather server with prefix
main_server.import_server(weather_server, prefix="weather")
print("   ✓ Imported weather_server with prefix 'weather'")
print("     Tools: weather.get_forecast, weather.get_alerts")
print()

# Import data server, only tools component
main_server.import_server(data_server, prefix="data", components=["tools"])
print("   ✓ Imported data_server with prefix 'data' (tools only)")
print("     Tools: data.fetch_data, data.transform_data")
print()

# ============================================================================
# Demonstrate mount() - Dynamic Composition
# ============================================================================

print("2. Dynamic Composition (mount):")
print("   - Live link to server")
print("   - Changes to mounted server reflected immediately")
print("   - (Not fully implemented yet - placeholder)")
print()

# Note: mount() is partially implemented
# main_server.mount(another_server, prefix="live")

# ============================================================================
# Show Composition Statistics
# ============================================================================

print("3. Composition Statistics:")
stats = main_server.get_composition_stats()
print(f"   Imported servers: {stats['stats']['imported']}")
print(f"   Mounted servers: {stats['stats']['mounted']}")
print(f"   Total components: {stats['total_components']}")
print(f"   Servers: {', '.join(stats['imported_servers'])}")
print()

print("=" * 70)
print("Server Starting...")
print("=" * 70)
print()
print("Available Tools:")
print("  Local:")
print("    - main_health")
print("  Imported from weather_server:")
print("    - weather.get_forecast")
print("    - weather.get_alerts")
print("  Imported from data_server:")
print("    - data.fetch_data")
print("    - data.transform_data")
print()
print("Test with:")
print("  curl -X POST http://localhost:8002/mcp \\")
print('    -H "Content-Type: application/json" \\')
print('    -H "Mcp-Session-Id: demo" \\')
print('    -d \'{"jsonrpc":"2.0","id":1,"method":"tools/list"}\'')
print()
print("  curl -X POST http://localhost:8002/mcp \\")
print('    -H "Content-Type: application/json" \\')
print('    -H "Mcp-Session-Id: demo" \\')
print('    -d \'{"jsonrpc":"2.0","id":2,"method":"tools/call",')
print('         "params":{"name":"weather.get_forecast","arguments":{"city":"NYC"}}}\'')
print()
print("=" * 70)
print()

if __name__ == "__main__":
    main_server.run(log_level="info")
