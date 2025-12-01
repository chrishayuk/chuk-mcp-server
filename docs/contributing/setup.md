# Development Setup

Get your development environment ready for contributing to ChukMCPServer.

## Prerequisites

- Python 3.11 or higher
- Git
- uv (recommended) or pip

## Install uv

ChukMCPServer uses **uv** for ultra-fast dependency management:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# With pip
pip install uv
```

## Clone Repository

```bash
git clone https://github.com/chrishayuk/chuk-mcp-server.git
cd chuk-mcp-server
```

## Install Dependencies

```bash
# Sync all dependencies (including dev tools)
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

This installs:
- Runtime dependencies
- Development tools (ruff, mypy, pytest)
- Testing frameworks
- Documentation tools

## Verify Installation

```bash
# Run tests
make test
# or
uv run pytest

# Check linting
make lint
# or
uv run ruff check .

# Check types
make typecheck
# or
uv run mypy src
```

## Install Pre-commit Hooks

Automatically run checks before commits:

```bash
pre-commit install
```

Now quality checks run automatically when you commit.

## IDE Setup

### VS Code

Install recommended extensions:
- Python
- Pylance
- Ruff
- MyPy Type Checker

Add to `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false
}
```

### PyCharm

1. Open Settings → Project → Python Interpreter
2. Add interpreter → System Interpreter
3. Select Python from your virtual environment
4. Enable ruff: Settings → Tools → External Tools
5. Enable pytest: Settings → Tools → Python Integrated Tools

## Project Structure

```
chuk-mcp-server/
├── src/chuk_mcp_server/    # Main package
│   ├── __init__.py          # Public API
│   ├── core.py              # Core server
│   ├── types/               # Type system
│   ├── transport/           # HTTP/STDIO
│   ├── oauth/               # OAuth support
│   └── config/              # Smart config
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest fixtures
│   ├── test_core.py         # Core tests
│   └── ...
├── examples/                # Example servers
├── benchmarks/              # Performance tests
├── docs/                    # Documentation
├── pyproject.toml           # Project config
├── uv.lock                  # Dependency lock
└── Makefile                 # Convenience commands
```

## Next Steps

- [Style Guide](style.md) - Code standards
- [Testing](testing.md) - Writing tests
- [Pull Requests](pull-requests.md) - Contribution workflow
