# ChukMCPServer

[![PyPI](https://img.shields.io/pypi/v/chuk-mcp-server)](https://pypi.org/project/chuk-mcp-server/)
[![Python](https://img.shields.io/pypi/pyversions/chuk-mcp-server)](https://pypi.org/project/chuk-mcp-server/)
[![License](https://img.shields.io/pypi/l/chuk-mcp-server)](https://github.com/chrishayuk/chuk-mcp-server/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/tests-859%20passing-success)](https://github.com/chrishayuk/chuk-mcp-server)
[![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)](https://github.com/chrishayuk/chuk-mcp-server)

**Build MCP servers for Claude Desktop in 30 seconds.** The fastest, simplest way to create custom tools for LLMs using Python decorators.

---

## 🚀 Get Started in 30 Seconds

### Option 1: Use the Scaffolder (Easiest!)

Create a complete MCP server project with one command:

```bash
# Create a new project
uvx chuk-mcp-server init my-awesome-server

# Set it up
cd my-awesome-server
uv sync

# Run it
uv run python server.py
```

That's it! You now have a working MCP server with:
- 3 example tools (hello, add_numbers, calculate)
- 1 example resource (server info)
- Full project structure with pyproject.toml
- README with Claude Desktop config
- Production-ready Dockerfile + docker-compose.yml
- Development tools (pytest, mypy, ruff)

**Connect to Claude Desktop:** Open the generated `README.md` for the exact config to add.

**Or deploy with Docker:**
```bash
cd my-awesome-server
docker-compose up
```

---

### Option 2: Manual Setup (More Control)

### Step 1: Install
```bash
# Using uv (recommended - fastest)
uv pip install chuk-mcp-server

# Or use uvx (no installation needed)
uvx chuk-mcp-server --help
```

### Step 2: Create a server
Create `my_server.py`:
```python
from chuk_mcp_server import tool, run

@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@tool
def get_weather(city: str) -> str:
    """Get the weather for a city."""
    return f"The weather in {city} is sunny! ☀️"

if __name__ == "__main__":
    run()
```

### Step 3: Connect to Claude Desktop
Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
{
  "mcpServers": {
    "my-tools": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/project", "run", "my_server.py"]
    }
  }
}
```

**That's it!** Restart Claude Desktop and your tools will appear. Claude can now add numbers and check the weather.

---

## 🎯 Why ChukMCPServer?

- **Dead Simple**: Just add `@tool` decorator and you're done
- **Claude Desktop Ready**: Works out of the box, no configuration needed
- **Type Safe**: Automatic schema generation from Python type hints
- **Fast**: 39,000+ requests/second (but you won't notice because it "just works")
- **Flexible**: Supports both Claude Desktop (stdio) and web apps (HTTP)

---

## 📚 Building Real Tools

### File System Tools
```python
from chuk_mcp_server import tool, run
from pathlib import Path

@tool
def read_file(filepath: str) -> str:
    """Read the contents of a file."""
    return Path(filepath).read_text()

@tool
def list_files(directory: str = ".") -> list[str]:
    """List all files in a directory."""
    return [f.name for f in Path(directory).iterdir() if f.is_file()]

@tool
def write_file(filepath: str, content: str) -> str:
    """Write content to a file."""
    Path(filepath).write_text(content)
    return f"Wrote {len(content)} characters to {filepath}"

if __name__ == "__main__":
    run()
```

### API Integration Tools
```python
from chuk_mcp_server import tool, run
import httpx

@tool
async def fetch_url(url: str) -> dict:
    """Fetch data from a URL and return status and preview."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return {
            "status": response.status_code,
            "preview": response.text[:200],
            "size": len(response.content)
        }

@tool
def search_github(query: str, limit: int = 5) -> list[dict]:
    """Search GitHub repositories."""
    response = httpx.get(
        "https://api.github.com/search/repositories",
        params={"q": query, "per_page": limit}
    )
    repos = response.json()["items"]
    return [{
        "name": r["full_name"],
        "stars": r["stargazers_count"],
        "url": r["html_url"]
    } for r in repos]

if __name__ == "__main__":
    run()
```

### Data Processing Tools
```python
from chuk_mcp_server import tool, run
import json

@tool
def json_to_csv(json_data: str) -> str:
    """Convert JSON array to CSV format."""
    data = json.loads(json_data)
    if not data:
        return ""

    # Get headers from first item
    headers = ",".join(data[0].keys())
    rows = [",".join(str(item[k]) for k in data[0].keys()) for item in data]

    return headers + "\n" + "\n".join(rows)

@tool
def count_words(text: str) -> dict:
    """Count words, characters, and lines in text."""
    return {
        "words": len(text.split()),
        "characters": len(text),
        "lines": len(text.split("\n"))
    }

if __name__ == "__main__":
    run()
```

---

## 🧩 Resources (Optional)

Resources provide data that Claude can read. They're like tools, but for fetching information instead of performing actions:

```python
from chuk_mcp_server import resource, run

@resource("config://app")
def get_config() -> dict:
    """Application configuration."""
    return {
        "version": "1.0.0",
        "environment": "production",
        "features": ["search", "export"]
    }

@resource("docs://readme", mime_type="text/markdown")
def get_readme() -> str:
    """Project documentation."""
    return "# My Project\n\nThis is the readme..."

if __name__ == "__main__":
    run()
```

---

## ⚙️ Advanced: HTTP Mode (For Web Apps)

Want to call your MCP server from a web app or API? Use HTTP mode:

```python
# Create server.py
from chuk_mcp_server import tool, run

@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

if __name__ == "__main__":
    # Start HTTP server on port 8000
    run(host="0.0.0.0", port=8000)
```

Run the server:
```bash
uv run python server.py
```

Test it:
```bash
# List available tools
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# Call a tool
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"add_numbers","arguments":{"a":5,"b":3}},"id":2}'
```

---

## 🔧 Testing Your Server

### Test Stdio Mode (Claude Desktop)
```bash
# Test that your server responds correctly
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | uv run python my_server.py

# You should see a JSON response listing your tools
```

### Test HTTP Mode
```bash
# Start server
uv run python server.py --http

# In another terminal, test it
curl http://localhost:8000/health
```

---

## ⚙️ Configuration & Logging

### Controlling Log Levels

By default, ChukMCPServer uses **WARNING** level logging to minimize noise during production and benchmarking. You can control logging in three ways:

#### 1. Command-Line Parameter (Recommended)

```python
from chuk_mcp_server import tool, run

@tool
def hello(name: str = "World") -> str:
    """Say hello."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    # Suppress INFO/DEBUG logs (default)
    run(log_level="warning")

    # Or show all logs
    run(log_level="debug")
```

#### 2. Environment Variable

```bash
# Warning level (default - quiet, only warnings/errors)
MCP_LOG_LEVEL=warning python server.py --http --port 8000

# Info level (show INFO, WARNING, ERROR)
MCP_LOG_LEVEL=info python server.py --http --port 8000

# Debug level (show everything)
MCP_LOG_LEVEL=debug python server.py --http --port 8000

# Error level (very quiet - errors only)
MCP_LOG_LEVEL=error python server.py --http --port 8000
```

#### 3. Using the CLI

```bash
# Warning level (default - suppresses INFO/DEBUG)
uvx chuk-mcp-server http --port 8000 --log-level warning

# Debug level (show all logs)
uvx chuk-mcp-server http --port 8000 --log-level debug

# Error level (very quiet)
uvx chuk-mcp-server http --port 8000 --log-level error
```

### Available Log Levels

- **`debug`**: Show all logs (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **`info`**: Show INFO and above (INFO, WARNING, ERROR, CRITICAL)
- **`warning`** ⭐ (default): Show warnings and errors only (WARNING, ERROR, CRITICAL)
- **`error`**: Show errors only (ERROR, CRITICAL)
- **`critical`**: Show only critical errors

### What Gets Suppressed

With the default `warning` level, you won't see:

```
# These are hidden ✅
INFO:     ::1:49723 - "POST /mcp HTTP/1.1" 200 OK
DEBUG:chuk_mcp_server.endpoints.mcp:Processing ping request
DEBUG:chuk_mcp_server.protocol:Handling ping (ID: 2)

# These still show ⚠️
WARNING:chuk_mcp_server:Connection limit reached
ERROR:chuk_mcp_server:Failed to process request
```

### For Benchmarking

When running performance tests, use `warning` or `error` level to eliminate logging overhead:

```bash
# Minimal logging for maximum performance
python server.py --http --port 8000 --log-level warning

# Or via environment
MCP_LOG_LEVEL=warning python server.py --http --port 8000
```

---

## 💡 More Examples

### Calculator with Error Handling
```python
from chuk_mcp_server import tool, run

@tool
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # Only allow safe operations
        allowed = {'+', '-', '*', '/', '(', ')', '.', ' '} | set('0123456789')
        if not all(c in allowed for c in expression):
            return "Error: Invalid characters in expression"

        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    run()
```

### System Information
```python
from chuk_mcp_server import tool, resource, run
import platform
import psutil

@tool
def get_system_info() -> dict:
    """Get current system information."""
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2)
    }

@resource("system://status")
def system_status() -> dict:
    """Real-time system status."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

if __name__ == "__main__":
    run()
```

---

## ⚡ Performance Benchmarks

Want to see how fast your MCP server is? ChukMCPServer includes built-in benchmarks:

### Quick Benchmark

```bash
# Start your server in one terminal
uv run python my_server.py --port 8000

# Run the quick benchmark in another terminal
uv run python benchmarks/quick_benchmark.py http://localhost:8000/mcp
```

**Sample Output:**
```
⚡ Quick MCP Benchmark: MCP Server
🔗 URL: http://localhost:8000/mcp
==================================================
✅ Session initialized: a3f4b2c1...
🔧 Tools discovered: 5
   - hello
   - calculate
   - add_numbers

📊 QUICK BENCHMARK RESULTS
==================================================
Test                      Avg(ms)  Min(ms)  Max(ms)  RPS   Count
------------------------------------------------------------
Connection                   2.3      1.8      3.1    434   5
Tools List                   3.5      2.9      4.2    285   8
Tool Call (hello)            5.2      4.1      6.8    192   3

📈 SUMMARY
Total RPS (across all tests): 911.2
Average Response Time: 3.7ms
Performance Rating: 🚀 Excellent
```

### Ultra-Minimal Performance Test

This test measures raw MCP protocol performance with zero client overhead:

```bash
# Default test (localhost:8000)
uv run python benchmarks/ultra_minimal_mcp_performance_test.py

# Custom port
uv run python benchmarks/ultra_minimal_mcp_performance_test.py 8001

# Custom host and port
uv run python benchmarks/ultra_minimal_mcp_performance_test.py localhost:8001

# With options
uv run python benchmarks/ultra_minimal_mcp_performance_test.py --duration 10 --concurrency 500

# Quick test
uv run python benchmarks/ultra_minimal_mcp_performance_test.py --quick
```

**Sample Output:**
```
🚀 ChukMCPServer Ultra-Minimal MCP Protocol Test
============================================================
ZERO client overhead - raw sockets + pre-built MCP requests
Target: Measure true MCP JSON-RPC performance

✅ MCP session initialized: a3f4b2c1...

🎯 Testing MCP Ping (JSON-RPC)...
      39,651 RPS |   2.54ms avg |  98.7% success
🔧 Testing MCP Tools List...
      28,342 RPS |   3.53ms avg |  99.1% success
👋 Testing Hello Tool Call...
      15,234 RPS |   6.56ms avg |  99.8% success

============================================================
📊 ULTRA-MINIMAL MCP PROTOCOL RESULTS
============================================================
🚀 Maximum MCP Performance:
   Peak RPS:       39,651
   Avg Latency:      2.54ms
   Success Rate:     98.7%
   Operation: MCP Ping

🔍 MCP Performance Analysis:
   🏆 EXCEPTIONAL MCP performance!
   🚀 Your ChukMCPServer is world-class
```

### What the Numbers Mean

- **RPS (Requests Per Second)**: How many operations the server can handle
  - `> 30,000 RPS`: Exceptional (world-class performance)
  - `> 10,000 RPS`: Excellent (production-ready)
  - `> 5,000 RPS`: Good (suitable for most applications)

- **Latency (ms)**: How long each operation takes
  - `< 5ms`: Excellent (sub-millisecond response)
  - `< 10ms`: Very Good (instant user experience)
  - `< 50ms`: Good (acceptable for most use cases)

### Creating Your Own Benchmark

```python
# benchmark_my_server.py
import asyncio
import time
from chuk_mcp_server import tool, run

@tool
def my_fast_tool(value: int) -> int:
    """A simple, fast tool for benchmarking."""
    return value * 2

async def run_benchmark():
    """Simple DIY benchmark."""
    import httpx

    # Make 100 rapid-fire requests
    start = time.time()
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(100):
            task = client.post(
                "http://localhost:8000/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": i,
                    "method": "tools/call",
                    "params": {
                        "name": "my_fast_tool",
                        "arguments": {"value": i}
                    }
                }
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

    duration = time.time() - start
    rps = len(responses) / duration

    print(f"✅ {len(responses)} requests in {duration:.2f}s")
    print(f"⚡ {rps:.0f} requests/second")
    print(f"📊 {duration/len(responses)*1000:.2f}ms average latency")

if __name__ == "__main__":
    # Start server in background or separate terminal first
    # Then run: asyncio.run(run_benchmark())
    run()
```

---

## 🎓 Understanding Transport Modes

ChukMCPServer supports two ways to communicate:

### Stdio Mode (Default for Claude Desktop)
- **What it is**: Communicates via stdin/stdout (like piping commands)
- **Use for**: Claude Desktop, command-line tools, subprocess integration
- **Benefits**: Most secure, zero network configuration, lowest latency

### HTTP Mode (For Web Apps)
- **What it is**: RESTful HTTP server with Server-Sent Events (SSE)
- **Use for**: Web apps, APIs, remote access, browser integration
- **Benefits**: Multiple clients, network accessible, built-in endpoints

**The framework auto-detects the right mode**, but you can also specify explicitly:

```python
# Force stdio mode
run(transport="stdio")

# Force HTTP mode
run(transport="http", port=8000)
```

---

## 🏗️ Project Scaffolder

The fastest way to start a new MCP server project:

### Create a New Project

```bash
# Basic usage
uvx chuk-mcp-server init my-server

# Custom directory
uvx chuk-mcp-server init my-server --dir /path/to/projects
```

### What Gets Created

```
my-server/
├── server.py           # Your MCP server with 3 example tools
├── pyproject.toml      # Dependencies & project config (uv-compatible)
├── README.md           # Complete docs (local + Docker setup)
├── Dockerfile          # Production-ready HTTP server
├── docker-compose.yml  # One-command Docker deployment
└── .gitignore          # Standard Python gitignore
```

### Generated server.py

The scaffolder creates a fully functional server that **defaults to stdio mode** for Claude Desktop:

```python
from chuk_mcp_server import tool, resource, run

@tool
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@tool
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    # ... implementation

@resource("config://info")
def server_info() -> dict:
    """Get server information."""
    return {"name": "my-server", "version": "0.1.0"}

if __name__ == "__main__":
    import sys

    # Support explicit transport selection
    if "--stdio" in sys.argv or "--transport=stdio" in sys.argv:
        run(transport="stdio")
    elif "--port" in sys.argv or "--host" in sys.argv or "--http" in sys.argv:
        run()  # HTTP mode
    else:
        run(transport="stdio")  # Default: stdio for Claude Desktop
```

**Usage:**
```bash
# Default: stdio mode (Claude Desktop)
python server.py

# Explicit stdio mode
python server.py --stdio
python server.py --transport=stdio

# HTTP mode
python server.py --http
python server.py --port 8000
python server.py --transport=http
```

### Next Steps After Scaffolding

#### Option 1: Local Development (Claude Desktop)

```bash
cd my-server

# Install dependencies
uv pip install --system chuk-mcp-server

# Test stdio mode (default behavior)
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python server.py

# The server defaults to stdio mode for Claude Desktop
# No flags needed!
```

Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["--directory", "/full/path/to/my-server", "run", "server.py"]
    }
  }
}
```

#### Option 2: Docker Deployment (Production)

```bash
cd my-server

# One-command deployment
docker-compose up

# Or manually
docker build -t my-server .
docker run -p 8000:8000 my-server

# Test it
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

The Docker version runs in **HTTP mode** on port 8000, perfect for:
- Cloud deployments (AWS, GCP, Azure)
- Kubernetes clusters
- API integrations
- Remote access

### Scaffolder Performance

The scaffolded server delivers **production-ready performance** out of the box.

**Real benchmark results from a freshly scaffolded server:**

<details>
<summary>📊 How these benchmarks were generated</summary>

```bash
# Create a scaffolded server
uvx chuk-mcp-server init benchmark-server
cd benchmark-server

# Deploy with Docker (HTTP mode)
docker-compose up -d

# Clone the repo to access benchmarks (from another directory)
git clone https://github.com/chrishayuk/chuk-mcp-server
cd chuk-mcp-server

# Run benchmarks against the scaffolded server
uv run python benchmarks/quick_benchmark.py http://localhost:8000/mcp
uv run python benchmarks/ultra_minimal_mcp_performance_test.py localhost:8000 --quick
```

</details>

**Results:**

```
📊 QUICK BENCHMARK RESULTS
============================================================
Server: benchmark-server (scaffolded with 3 tools)
Tools Found: 3 (hello, add_numbers, calculate)
Resources Found: 1 (config://info)

Test                      Avg(ms)  Min(ms)  Max(ms)  RPS    Count
------------------------------------------------------------
Connection                  15.1   14.5   15.9 66.1   5
Tools List                  15.5   14.3   20.3 64.7   8
Tool Call (hello)           16.4   14.5   19.9 61.0   3
Resource Read               14.5   14.1   14.9 69.1   3

📈 SUMMARY
Total RPS: 459.8
Average Response Time: 15.2ms
Performance Rating: 🚀 Excellent
```

**Ultra-minimal test (max throughput):**
```
🚀 Maximum MCP Performance:
   Peak RPS:       31,353
   Avg Latency:      1.7ms
   Success Rate:    100.0%

🔧 Tool Performance (scaffolded tools):
   MCP Ping:        29,525 RPS |  1.7ms
   Tools List:      28,527 RPS |  1.7ms
   Hello Tool:      26,555 RPS |  1.9ms
   Calculate Tool:  24,484 RPS |  2.0ms

📂 Resource Performance (scaffolded resources):
   Resources List:  29,366 RPS |  1.7ms
   Config Resource: 29,856 RPS |  1.7ms

🏆 EXCEPTIONAL performance - world-class MCP server!
   All operations: 100% success rate
   Average: 26,000+ RPS per operation
```

**What this means:**
- ✅ Your scaffolded server handles **31,000+ requests/second**
- ✅ Sub-2ms latency for most operations
- ✅ Zero configuration required
- ✅ Production-ready out of the box

---

## 📦 CLI Usage (Optional)

ChukMCPServer includes a CLI if you want to test without writing Python:

```bash
# Run with uvx (no installation)
uvx chuk-mcp-server --help

# Test stdio mode
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | uvx chuk-mcp-server

# Start HTTP server
uvx chuk-mcp-server --http --port 8000
```

---

## 📚 API Reference

### Tools
Define functions that Claude can call:
```python
from chuk_mcp_server import tool

@tool
def my_function(param: str, count: int = 1) -> str:
    """This docstring explains what the tool does."""
    return f"Result: {param} x {count}"
```

### Resources
Provide data that Claude can read:
```python
from chuk_mcp_server import resource

@resource("mydata://info")
def get_info() -> dict:
    """This docstring explains what data is available."""
    return {"key": "value"}
```

### Async Support
Both tools and resources can be async:
```python
import httpx

@tool
async def fetch_data(url: str) -> dict:
    """Fetch data from a URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

---

## 🔍 Troubleshooting

### Claude Desktop not showing tools?
1. **Check your config path is absolute**: `/full/path/to/my_server.py` not `~/my_server.py`
2. **Test your server manually**:
   ```bash
   echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | uv run python my_server.py
   ```
3. **Check Claude Desktop logs** (Help → Show Logs in Claude Desktop)
4. **Restart Claude Desktop** after changing the config

### Port already in use?
```bash
# Use a different port
uv run python server.py --port 8001

# Or find what's using it
lsof -i :8000  # macOS/Linux
```

### Need to see what's happening?
The framework uses stderr for logs (stdout is reserved for MCP protocol):
```python
import sys
import logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
```

---

## 🐳 Docker Support

The scaffolder automatically creates production-ready Docker files:

**Dockerfile** (HTTP mode, optimized with uv):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY server.py ./

# Install dependencies using uv
RUN uv pip install --system --no-cache chuk-mcp-server>=0.4.4

# Expose HTTP port
EXPOSE 8000

# Run server in HTTP mode for web/API access
CMD ["python", "server.py", "--port", "8000", "--host", "0.0.0.0"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  my-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MCP_TRANSPORT=http
    restart: unless-stopped
```

**Deploy in seconds:**
```bash
docker-compose up
# Server running at http://localhost:8000
```

**Or manually:**
```bash
# Build
docker build -t my-server .

# Run
docker run -p 8000:8000 my-server

# Test
curl http://localhost:8000/health
```

---

## 🧪 Testing Your Tools

```python
# test_server.py
from chuk_mcp_server import ChukMCPServer

def test_my_tool():
    mcp = ChukMCPServer()

    @mcp.tool
    def add(a: int, b: int) -> int:
        return a + b

    # Get tool metadata
    tools = mcp.get_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "add"
```

Run tests:
```bash
uv run pytest
```

---

## 🤝 Contributing

Contributions welcome!

```bash
# Setup development environment
git clone https://github.com/chrishayuk/chuk-mcp-server
cd chuk-mcp-server
uv sync --dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Type checking
uv run mypy src
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

Built on top of the [Model Context Protocol](https://modelcontextprotocol.io) specification by Anthropic.

## 🔗 Links

- [Documentation](https://github.com/chrishayuk/chuk-mcp-server/docs)
- [PyPI Package](https://pypi.org/project/chuk-mcp-server/)
- [GitHub Repository](https://github.com/chrishayuk/chuk-mcp-server)
- [Issue Tracker](https://github.com/chrishayuk/chuk-mcp-server/issues)

---

**Made with ❤️ for the MCP community**