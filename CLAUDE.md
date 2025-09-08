# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Standards

### Package Management
This project uses **uv** for ultra-fast dependency management. The `uv.lock` file ensures reproducible builds.

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip sync

# Add new dependencies
uv pip install package-name

# Update lock file
uv pip compile pyproject.toml -o uv.lock
```

### Code Quality Requirements

#### Mandatory Tools
- **ruff**: Fast Python linter (replaces flake8, isort, etc.)
- **black**: Code formatter (integrated with ruff format)
- **mypy**: Static type checker
- **pytest**: Testing framework with coverage

#### Quality Standards
- Minimum 80% test coverage target
- Full type annotations required (enforced by mypy)
- All code must pass ruff checks
- Code formatting with ruff format (black-compatible)

### Development Workflow

```bash
# Initial setup
uv sync --dev  # Install all dependencies including dev tools
pre-commit install  # Set up git hooks

# Before committing - run all checks
make check  # Runs lint, typecheck, and tests
pre-commit run --all-files  # Run all pre-commit hooks

# Individual quality checks
make lint       # Run ruff linter
make format     # Format code with ruff
make typecheck  # Run mypy type checking
make test-cov   # Run tests with coverage report

# Quick development cycle
make dev-install  # Install in editable mode
make test        # Run tests quickly
```

## Commands

### Building & Installation
```bash
# Build the package
make build
uv build  # Alternative using uv

# Install the package
make install
uv pip install .  # Alternative using uv

# Install in development mode
make dev-install
uv pip install -e .  # Alternative using uv
```

### Testing
```bash
# Run all tests
make test
pytest  # Direct pytest
uv run pytest  # Via uv

# Run tests with coverage
make test-cov
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/path/to/test_file.py -v

# Run tests matching pattern
pytest -k "test_pattern" -v

# Run async tests
pytest -m asyncio
```

### Code Quality
```bash
# Run all quality checks
make check  # lint + typecheck + test

# Linting with ruff
make lint
ruff check .
ruff check --fix .  # Auto-fix issues

# Format code
make format
ruff format .
ruff format --check .  # Check without modifying

# Type checking with mypy
make typecheck
mypy src
mypy src --strict  # Strict mode

# Pre-commit hooks (if configured)
pre-commit run --all-files
```

### Cleaning
```bash
# Basic clean (Python bytecode and build artifacts)
make clean

# Deep clean (everything including cache)
make clean-all

# Clean specific artifacts
rm -rf .pytest_cache/
rm -rf .mypy_cache/
rm -rf .ruff_cache/
rm -rf dist/ build/
```

### Publishing
```bash
# Build and publish to PyPI
make publish

# Publish to test PyPI
make publish-test

# Build distributions only
make build
uv build
```

### Running Examples & Benchmarks

#### HTTP Transport (Default)
```bash
# Zero config example (HTTP transport)
python examples/zero_config_example.py
uv run python examples/zero_config_example.py

# Performance mode (39,000+ RPS)
python examples/zero_config_example.py --performance

# Development mode (full logging)
python examples/zero_config_example.py --development

# Run performance benchmarks
python benchmarks/ultra_minimal_mcp_performance_test.py
python benchmarks/quick_benchmark.py

# Run with custom settings
python benchmarks/ultra_minimal_mcp_performance_test.py localhost:8001 --concurrency 500 --duration 10
```

#### STDIO Transport (MCP Standard)
```bash
# Method 1: Global decorators with transport parameter
python -c "
from chuk_mcp_server import tool, run

@tool
def hello(name: str = 'World') -> str:
    return f'Hello, {name}!'

run(transport='stdio')
"

# Method 2: Constructor-based transport selection
python -c "
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer(transport='stdio')

@mcp.tool
def hello(name: str = 'World') -> str:
    return f'Hello, {name}!'

mcp.run()  # Automatically uses STDIO transport
"

# Method 3: Dedicated run_stdio() method
python -c "
from chuk_mcp_server import ChukMCPServer

mcp = ChukMCPServer()

@mcp.tool
def hello(name: str = 'World') -> str:
    return f'Hello, {name}!'

mcp.run_stdio()  # Direct STDIO method call
"

# Test STDIO server manually
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test","version":"1.0"},"protocolVersion":"2025-06-18"}}' | python your_server.py

# Example STDIO server
python examples/stdio_example.py

# STDIO transport testing
python tests/transport/test_stdio_complete.py
```

#### Transport Methods Summary
1. **Global Decorators**: `run(transport="stdio")` - Simplest approach
2. **Constructor Parameter**: `ChukMCPServer(transport="stdio")` - Clean class-based API  
3. **Dedicated Method**: `mcp.run_stdio()` - Explicit method call

#### Transport Comparison
- **HTTP Transport**: Web-based, REST endpoints, browser compatible, 39,000+ RPS
- **STDIO Transport**: Process-based, standard MCP protocol, subprocess communication
- **Use Cases**:
  - HTTP: Web apps, APIs, development servers, cloud deployment
  - STDIO: MCP clients, subprocess integration, Claude Desktop, editor plugins

## Architecture

### High-Level Architecture
ChukMCPServer is a high-performance MCP (Model Context Protocol) framework that provides zero-configuration deployment with automatic environment detection and optimization. It achieves world-class performance (39,000+ RPS) through intelligent defaults and modular architecture.

### Core Components

1. **Smart Configuration System** (`src/chuk_mcp_server/config/`)
   - Modular detection system that auto-configures based on environment
   - `SmartConfig` orchestrates multiple detectors:
     - `ProjectDetector`: Auto-detects project name from directory/package files
     - `EnvironmentDetector`: Identifies dev/prod/container/serverless environments  
     - `NetworkDetector`: Determines optimal host/port bindings
     - `SystemDetector`: Optimizes performance based on hardware
     - `ContainerDetector`: Detects Docker/Kubernetes environments
     - `CloudDetector`: Identifies cloud platforms (AWS, GCP, Azure, Edge)

2. **Core Framework** (`src/chuk_mcp_server/core.py`)
   - Main `ChukMCPServer` class with decorator-based API
   - Integrates smart configuration for zero-config operation
   - Manages tool/resource registration and protocol handling

3. **Type System** (`src/chuk_mcp_server/types/`)
   - Type-safe handlers for tools and resources
   - Automatic schema generation from Python type hints
   - High-performance serialization with orjson
   - Direct integration with underlying chuk_mcp library

4. **Registry System**
   - `mcp_registry.py`: Manages MCP tools, resources, and prompts
   - `endpoint_registry.py`: HTTP endpoint management
   - Pre-cached schema generation for performance

5. **Protocol Layer** (`src/chuk_mcp_server/protocol.py`)
   - MCP JSON-RPC protocol implementation
   - Session management and SSE streaming support
   - Error handling and request/response processing

6. **Transport Layer** (`src/chuk_mcp_server/transport/`)
   - **HTTP Transport**: Starlette + uvloop for maximum performance (39,000+ RPS)
   - **STDIO Transport**: Standard MCP protocol over stdin/stdout
   - Auto-registered endpoints with CORS support (HTTP)
   - Optimized for high concurrency (1,000+ connections)

7. **HTTP Server** (`src/chuk_mcp_server/http_server.py`)
   - Built on Starlette + uvloop for maximum performance
   - Auto-registered endpoints with CORS support
   - Optimized for high concurrency (1,000+ connections)

8. **Cloud Support** (`src/chuk_mcp_server/cloud/`)
   - Auto-detection of cloud environments
   - Platform-specific adapters for serverless deployment
   - Support for GCP, AWS Lambda, Azure Functions, Edge platforms

### Key Design Patterns

- **Zero Configuration**: Everything auto-detected through modular SmartConfig system
- **Decorator-Based API**: Clean, FastAPI-like interface for defining tools/resources
- **Registry Pattern**: Centralized management of components
- **Type Safety**: Automatic validation and schema generation
- **Performance First**: orjson, uvloop, pre-caching for 39,000+ RPS
- **Modular Architecture**: Each component is independently testable

### Entry Points

- Global decorators: `@tool`, `@resource` with `run()` for ultimate simplicity
- Class-based: `ChukMCPServer()` for traditional usage
- Cloud handlers: Auto-exported based on detected environment
- **HTTP Transport**: `/mcp` endpoint for MCP protocol over HTTP with SSE
- **STDIO Transport**: Standard MCP protocol over stdin/stdout for process communication

### Transport Support

ChukMCPServer supports both standard MCP transports:

1. **HTTP Transport** (Default)
   - High-performance web server (39,000+ RPS)
   - RESTful endpoints with CORS support
   - Server-Sent Events (SSE) for streaming
   - Perfect for web apps, APIs, and cloud deployment
   
2. **STDIO Transport** (MCP Standard)
   - Standard MCP protocol over stdin/stdout
   - Process-based communication
   - Perfect for MCP clients, Claude Desktop, editor plugins
   - Zero network overhead, direct process integration