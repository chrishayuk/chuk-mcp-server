# Installation

Get ChukMCPServer up and running in minutes.

## Requirements

- Python 3.10 or higher
- pip or uv package manager

## Basic Installation

=== "Using pip"

    ```bash
    pip install chuk-mcp-server
    ```

=== "Using uv (recommended)"

    ```bash
    uv pip install chuk-mcp-server
    ```

## Optional Dependencies

ChukMCPServer offers optional feature sets:

### Google Drive OAuth

For Google Drive authentication and storage:

```bash
pip install chuk-mcp-server[google_drive]
```

Includes:
- `google-auth>=2.23.0`
- `google-auth-oauthlib>=1.1.0`
- `google-api-python-client>=2.100.0`

### All Features

Install everything:

```bash
pip install chuk-mcp-server[google_drive]
```

## Development Installation

For contributing to ChukMCPServer:

```bash
# Clone the repository
git clone https://github.com/chrishayuk/chuk-mcp-server.git
cd chuk-mcp-server

# Install with development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

Development dependencies include:
- Testing: `pytest`, `pytest-asyncio`, `pytest-cov`
- Linting: `ruff`, `mypy`
- Formatting: `black` (via ruff)

## Verify Installation

Check that ChukMCPServer is installed correctly:

```bash
python -c "import chuk_mcp_server; print(chuk_mcp_server.__version__)"
```

You should see the version number (e.g., `0.4.4`).

## Upgrading

=== "Using pip"

    ```bash
    pip install --upgrade chuk-mcp-server
    ```

=== "Using uv"

    ```bash
    uv pip install --upgrade chuk-mcp-server
    ```

## Troubleshooting

### Import Errors

If you see import errors, ensure you're using Python 3.10+:

```bash
python --version  # Should be 3.10 or higher
```

### Optional Dependencies

If OAuth features aren't working:

```bash
pip install chuk-mcp-server[google_drive]
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Create your first server
- [Your First Server](first-server.md) - Detailed walkthrough
- [Claude Desktop Setup](claude-desktop.md) - Integrate with Claude
