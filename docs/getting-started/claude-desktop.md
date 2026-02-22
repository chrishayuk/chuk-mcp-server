# Claude Desktop Setup

Integrate your ChukMCPServer with Claude Desktop for seamless AI-powered tool usage.

## Prerequisites

- [Claude Desktop](https://claude.ai/download) installed
- ChukMCPServer installed (`pip install chuk-mcp-server`)
- A working MCP server

## Quick Setup (Automatic)

The easiest way is to use the scaffolder with `--claude` flag:

```bash
uvx chuk-mcp-server init my-server --claude
```

This automatically:
1. Creates your server
2. Adds configuration to Claude Desktop
3. Sets up the correct paths

**Restart Claude Desktop** and your tools will be available!

## Manual Setup

### Step 1: Locate Config File

Find your Claude Desktop config file:

=== "macOS"

    ```
    ~/Library/Application Support/Claude/claude_desktop_config.json
    ```

=== "Windows"

    ```
    %APPDATA%\Claude\claude_desktop_config.json
    ```

=== "Linux"

    ```
    ~/.config/Claude/claude_desktop_config.json
    ```

### Step 2: Add Your Server

Edit `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/path/to/your/server.py"]
    }
  }
}
```

Or if using uv:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "my-server"]
    }
  }
}
```

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop for changes to take effect.

## Verifying It Works

1. Open Claude Desktop
2. Start a new conversation
3. Look for the 🔌 icon indicating tools are available
4. Ask Claude to use one of your tools:

> "Can you use the my-server tools to greet me?"

Claude should be able to see and call your tools!

## Example Configurations

### Basic Server

```json
{
  "mcpServers": {
    "calculator": {
      "command": "python",
      "args": ["calculator.py"]
    }
  }
}
```

### Server with Environment Variables

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["weather_server.py"],
      "env": {
        "WEATHER_API_KEY": "your-api-key-here",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

### Multiple Servers

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["run", "weather-server"]
    },
    "calculator": {
      "command": "python",
      "args": ["/Users/you/servers/calc.py"]
    },
    "database": {
      "command": "uv",
      "args": ["run", "db-server"],
      "env": {
        "DATABASE_URL": "postgresql://localhost/mydb"
      }
    }
  }
}
```

### Using Poetry

```json
{
  "mcpServers": {
    "my-server": {
      "command": "poetry",
      "args": ["run", "python", "server.py"]
    }
  }
}
```

### Using Virtual Environment

```json
{
  "mcpServers": {
    "my-server": {
      "command": "/path/to/venv/bin/python",
      "args": ["server.py"]
    }
  }
}
```

## Troubleshooting

### Tools Not Appearing

**Check the config file is valid JSON:**

```bash
# macOS/Linux
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool

# Windows
type %APPDATA%\Claude\claude_desktop_config.json | python -m json.tool
```

**Verify the server runs standalone:**

```bash
python your_server.py
```

You should see:
```
ChukMCPServer initialized
📋 X tools registered
🚀 Server running on stdio transport
```

**Check Claude Desktop logs:**

=== "macOS"

    ```bash
    tail -f ~/Library/Logs/Claude/mcp*.log
    ```

=== "Windows"

    ```
    %USERPROFILE%\AppData\Local\Claude\Logs\mcp*.log
    ```

### Server Crashes on Startup

**Check Python version:**

```bash
python --version  # Should be 3.10+
```

**Test with minimal server:**

```python
from chuk_mcp_server import tool, run

@tool
def test() -> str:
    return "It works!"

run()
```

**Check for import errors:**

```bash
python -c "import chuk_mcp_server; print('OK')"
```

### Environment Variables Not Working

Make sure env vars are in the config:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "API_KEY": "your-key",
        "DEBUG": "true"
      }
    }
  }
}
```

### Path Issues

Use absolute paths:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/Users/yourname/projects/server.py"]
    }
  }
}
```

## Best Practices

### 1. Use Project Structure

Organize your server as a package:

```
my-server/
├── pyproject.toml
├── src/
│   └── my_server/
│       ├── __init__.py
│       └── server.py
└── README.md
```

Then use `uv run`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "my-server"]
    }
  }
}
```

### 2. Environment Variables

Store secrets in environment variables, not in code:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "API_KEY": "${API_KEY}",  // Read from system env
        "DATABASE_URL": "postgresql://localhost/mydb"
      }
    }
  }
}
```

### 3. Logging

Enable logging to debug issues:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "MCP_LOG_LEVEL": "debug"
      }
    }
  }
}
```

### 4. Multiple Servers

Keep servers focused on single domains:

```json
{
  "mcpServers": {
    "weather": { ... },      // Weather tools
    "database": { ... },     // Database tools
    "calculator": { ... }    // Math tools
  }
}
```

## Testing Your Server

Before adding to Claude Desktop, test standalone:

```bash
# Test that tools are registered
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python server.py

# Test calling a tool
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"my_tool","arguments":{}}}' | python server.py
```

## Example: Complete Weather Server

**server.py:**

```python
from chuk_mcp_server import tool, run
import os

API_KEY = os.getenv("WEATHER_API_KEY", "demo-key")

@tool
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    # Use API_KEY to call weather API
    return {"city": city, "temp": 72, "condition": "sunny"}

run()
```

**claude_desktop_config.json:**

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/Users/you/weather/server.py"],
      "env": {
        "WEATHER_API_KEY": "your-actual-api-key"
      }
    }
  }
}
```

## Next Steps

- [Building Tools](../tools/basic.md) - Create more sophisticated tools
- [OAuth Authentication](../oauth/overview.md) - Add authentication
- [Deployment](../deployment/http-mode.md) - Deploy your server

## Support

**Having issues?**

1. Check [Troubleshooting](#troubleshooting) section above
2. Review Claude Desktop logs
3. Test server standalone
4. Check [GitHub Issues](https://github.com/chrishayuk/chuk-mcp-server/issues)
