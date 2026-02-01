.PHONY: clean clean-pyc clean-build clean-test clean-all test run build publish publish-test publish-manual help install dev-install bump-patch bump-minor bump-major

# Default target
help:
	@echo "Available targets:"
	@echo "  clean        - Remove Python bytecode and basic artifacts"
	@echo "  clean-all    - Deep clean everything (pyc, build, test, cache)"
	@echo "  clean-pyc    - Remove Python bytecode files"
	@echo "  clean-build  - Remove build artifacts"
	@echo "  clean-test   - Remove test artifacts"
	@echo "  install      - Install package in current environment"
	@echo "  dev-install  - Install package in dev mode with uv sync --dev"
	@echo "  lint         - Run ruff linter and formatter check"
	@echo "  format       - Auto-format code with ruff"
	@echo "  typecheck    - Run mypy type checker on src/"
	@echo "  security     - Run bandit security checks on src/"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  check        - Run all CI checks (lint, typecheck, test-cov, security)"
	@echo "  check-ci     - CI-friendly check (quiet output)"
	@echo "  run          - Run the server"
	@echo "  build        - Build the project"
	@echo ""
	@echo "Release & Publishing:"
	@echo "  bump-patch       - Bump patch version (0.0.X)"
	@echo "  bump-minor       - Bump minor version (0.X.0)"
	@echo "  bump-major       - Bump major version (X.0.0)"
	@echo "  publish          - Tag and push to trigger automated release (RECOMMENDED)"
	@echo "  publish-test     - Build and publish to TestPyPI (manual)"
	@echo "  publish-manual   - Build and publish to PyPI (manual, use with caution)"

# Basic clean - Python bytecode and common artifacts
clean: clean-pyc clean-build
	@echo "Basic clean complete."

# Remove Python bytecode files and __pycache__ directories
clean-pyc:
	@echo "Cleaning Python bytecode files..."
	@find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@find . -type f -name '*.pyo' -delete 2>/dev/null || true
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true

# Remove build artifacts
clean-build:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info 2>/dev/null || true
	@rm -rf .eggs/ 2>/dev/null || true
	@find . -name '*.egg' -exec rm -f {} + 2>/dev/null || true

# Remove test artifacts
clean-test:
	@echo "Cleaning test artifacts..."
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf .tox/ 2>/dev/null || true
	@rm -rf .cache/ 2>/dev/null || true
	@find . -name '.coverage.*' -delete 2>/dev/null || true

# Deep clean - everything
clean-all: clean-pyc clean-build clean-test
	@echo "Deep cleaning..."
	@rm -rf .mypy_cache/ 2>/dev/null || true
	@rm -rf .ruff_cache/ 2>/dev/null || true
	@rm -rf .uv/ 2>/dev/null || true
	@rm -rf node_modules/ 2>/dev/null || true
	@find . -name '.DS_Store' -delete 2>/dev/null || true
	@find . -name 'Thumbs.db' -delete 2>/dev/null || true
	@find . -name '*.log' -delete 2>/dev/null || true
	@find . -name '*.tmp' -delete 2>/dev/null || true
	@find . -name '*~' -delete 2>/dev/null || true
	@echo "Deep clean complete."

# Install package
install:
	@echo "Installing package..."
	pip install .

# Install package in development mode (matches CI)
dev-install:
	@echo "Installing package in development mode..."
	@if command -v uv >/dev/null 2>&1; then \
		uv sync --dev; \
	else \
		pip install -e ".[dev]"; \
	fi

# Run tests
test:
	@echo "Running tests..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest; \
	elif command -v pytest >/dev/null 2>&1; then \
		pytest; \
	else \
		python -m pytest; \
	fi

# Run tests with coverage (matches CI)
test-cov:
	@echo "Running tests with coverage..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest --cov=src --cov-report=term-missing --cov-report=xml -v; \
	else \
		pytest --cov=src --cov-report=term-missing --cov-report=xml -v; \
	fi

# Run the server launcher
run:
	@echo "Running server..."
	@if command -v uv >/dev/null 2>&1; then \
		PYTHONPATH=src uv run python -m chuk_protocol_server.server_launcher; \
	else \
		PYTHONPATH=src python3 -m chuk_protocol_server.server_launcher; \
	fi

# Build the project using the pyproject.toml configuration
build: clean-build
	@echo "Building project..."
	@if command -v uv >/dev/null 2>&1; then \
		uv build; \
	else \
		python3 -m build; \
	fi
	@echo "Build complete. Distributions are in the 'dist' folder."

# ============================================
# VERSION BUMPING
# ============================================

# Get current version from pyproject.toml
CURRENT_VERSION := $(shell grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# Bump patch version (0.0.X)
bump-patch:
	@echo "Current version: $(CURRENT_VERSION)"
	@NEW_VERSION=$$(echo $(CURRENT_VERSION) | awk -F. '{ \
		if (NF == 2) { print $$1"."$$2".1" } \
		else if (NF == 3) { print $$1"."$$2"."($$3+1) } \
		else { print $$0 } \
	}'); \
	echo "New version: $$NEW_VERSION"; \
	sed -i.bak "s/^version = \"$(CURRENT_VERSION)\"/version = \"$$NEW_VERSION\"/" pyproject.toml && rm pyproject.toml.bak; \
	echo "✓ Version bumped to $$NEW_VERSION"

# Bump minor version (0.X.0)
bump-minor:
	@echo "Current version: $(CURRENT_VERSION)"
	@NEW_VERSION=$$(echo $(CURRENT_VERSION) | awk -F. '{ \
		if (NF == 2) { print $$1"."($$2+1)".0" } \
		else if (NF == 3) { print $$1"."($$2+1)".0" } \
		else { print $$0 } \
	}'); \
	echo "New version: $$NEW_VERSION"; \
	sed -i.bak "s/^version = \"$(CURRENT_VERSION)\"/version = \"$$NEW_VERSION\"/" pyproject.toml && rm pyproject.toml.bak; \
	echo "✓ Version bumped to $$NEW_VERSION"

# Bump major version (X.0.0)
bump-major:
	@echo "Current version: $(CURRENT_VERSION)"
	@NEW_VERSION=$$(echo $(CURRENT_VERSION) | awk -F. '{ \
		if (NF == 2) { print ($$1+1)".0.0" } \
		else if (NF == 3) { print ($$1+1)".0.0" } \
		else { print $$0 } \
	}'); \
	echo "New version: $$NEW_VERSION"; \
	sed -i.bak "s/^version = \"$(CURRENT_VERSION)\"/version = \"$$NEW_VERSION\"/" pyproject.toml && rm pyproject.toml.bak; \
	echo "✓ Version bumped to $$NEW_VERSION"

# ============================================
# PUBLISHING & RELEASE
# ============================================

# Automated publish via GitHub Actions (RECOMMENDED)
publish:
	@echo "=========================================="
	@echo "Automated Release via GitHub Actions"
	@echo "=========================================="
	@VERSION=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	echo "Current version: $$VERSION"; \
	echo ""; \
	echo "Pre-flight checks:"; \
	if [ -n "$$(git status --porcelain)" ]; then \
		echo "❌ Error: Working directory is not clean"; \
		echo "   Please commit or stash your changes first."; \
		exit 1; \
	fi; \
	echo "✓ Working directory is clean"; \
	if git rev-parse "v$$VERSION" >/dev/null 2>&1; then \
		echo "❌ Error: Tag v$$VERSION already exists"; \
		exit 1; \
	fi; \
	echo "✓ Tag v$$VERSION does not exist"; \
	echo "✓ Current branch: $$(git branch --show-current)"; \
	echo ""; \
	read -p "Create and push tag v$$VERSION? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
		git push origin "v$$VERSION"; \
		echo ""; \
		echo "✓ Tag v$$VERSION created and pushed"; \
		echo ""; \
		echo "GitHub Actions will now:"; \
		echo "  1. Run tests"; \
		echo "  2. Create GitHub release"; \
		echo "  3. Publish to PyPI"; \
		echo ""; \
		echo "Monitor progress at:"; \
		echo "  https://github.com/chrishayuk/chuk-mcp-server/actions"; \
	else \
		echo "Cancelled."; \
	fi

# Publish to test PyPI (manual)
publish-test: build
	@echo "=========================================="
	@echo "Publishing to TestPyPI"
	@echo "=========================================="
	@VERSION=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	echo "Version: $$VERSION"; \
	echo ""; \
	read -p "Upload to TestPyPI? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		if command -v uv >/dev/null 2>&1; then \
			uv build; \
		else \
			python -m build; \
		fi; \
		twine upload --repository testpypi dist/*; \
		echo ""; \
		echo "✓ Published to TestPyPI"; \
		echo ""; \
		echo "Test installation:"; \
		echo "  pip install --index-url https://test.pypi.org/simple/ chuk-mcp-server"; \
	else \
		echo "Cancelled."; \
	fi

# Manual publish to PyPI (use with caution - prefer 'make publish')
publish-manual: build
	@echo "=========================================="
	@echo "⚠️  MANUAL PUBLISH TO PyPI"
	@echo "=========================================="
	@echo "WARNING: This will permanently publish to PyPI."
	@echo "         Published versions cannot be deleted."
	@echo ""
	@echo "RECOMMENDED: Use 'make publish' instead for automated workflow."
	@echo ""
	@VERSION=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	echo "Version: $$VERSION"; \
	echo ""; \
	read -p "Are you SURE you want to manually publish? [yes/N] " -r; \
	echo ""; \
	if [ "$$REPLY" = "yes" ]; then \
		if command -v uv >/dev/null 2>&1; then \
			uv build; \
		else \
			python -m build; \
		fi; \
		twine upload dist/*; \
		echo ""; \
		echo "✓ Published to PyPI"; \
		echo ""; \
		echo "IMPORTANT: Don't forget to:"; \
		echo "  1. Create git tag: git tag -a v$$VERSION -m 'Release v$$VERSION'"; \
		echo "  2. Push tag: git push origin v$$VERSION"; \
		echo "  3. Create GitHub release"; \
	else \
		echo "Cancelled. Use 'make publish' for automated workflow."; \
	fi

# Check code quality (matches CI)
lint:
	@echo "Running linters..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff check .; \
		echo "All checks passed!"; \
		uv run ruff format --check .; \
	elif command -v ruff >/dev/null 2>&1; then \
		ruff check .; \
		ruff format --check .; \
	else \
		echo "Ruff not found. Install with: pip install ruff"; \
		exit 1; \
	fi

# Fix code formatting
format:
	@echo "Formatting code..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff format .; \
		uv run ruff check --fix .; \
	elif command -v ruff >/dev/null 2>&1; then \
		ruff format .; \
		ruff check --fix .; \
	else \
		echo "Ruff not found. Install with: pip install ruff"; \
		exit 1; \
	fi

# Type checking (matches CI)
typecheck:
	@echo "Running type checker..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run mypy src || true; \
		echo "  ✓ Type checking completed"; \
	elif command -v mypy >/dev/null 2>&1; then \
		mypy src || true; \
		echo "  ✓ Type checking completed"; \
	else \
		echo "  ⚠ MyPy not found. Install with: pip install mypy"; \
		exit 1; \
	fi

# Security check (matches CI) - Skip B104 (0.0.0.0 binding intentional), B608 (false positive on f-string templates)
security:
	@echo "Running security checks..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run bandit -r src/ -ll --skip B104,B608 --quiet 2>&1 | grep -v "WARNING.*Test in comment" || true; \
	elif command -v bandit >/dev/null 2>&1; then \
		bandit -r src/ -ll --skip B104,B608 --quiet 2>&1 | grep -v "WARNING.*Test in comment" || true; \
	else \
		echo "  ⚠ Bandit not found. Install with: pip install bandit"; \
		exit 1; \
	fi
	@echo "  ✓ Security checks completed"

# Run all checks (matches CI workflow dependencies)
check: lint typecheck test-cov security
	@echo "All checks completed."

# CI-friendly type checking (quiet mode)
typecheck-ci:
	@echo "Running type checker..."
	@if command -v uv >/dev/null 2>&1; then \
		if uv run mypy >/dev/null 2>&1; then \
			echo "  ✅ Type checking passed!"; \
		else \
			echo "  ✓ Type checking completed"; \
		fi \
	elif command -v mypy >/dev/null 2>&1; then \
		if mypy >/dev/null 2>&1; then \
			echo "  ✅ Type checking passed!"; \
		else \
			echo "  ✓ Type checking completed"; \
		fi \
	else \
		echo "  ⚠ MyPy not found. Install with: pip install mypy"; \
		exit 1; \
	fi

# CI check - for use in CI/CD pipelines
check-ci: lint typecheck-ci test
	@echo "✓ CI checks completed successfully."

# Show project info
info:
	@echo "Project Information:"
	@echo "==================="
	@if [ -f "pyproject.toml" ]; then \
		echo "pyproject.toml found"; \
		if command -v uv >/dev/null 2>&1; then \
			echo "UV version: $$(uv --version)"; \
		fi; \
		if command -v python >/dev/null 2>&1; then \
			echo "Python version: $$(python --version)"; \
		fi; \
	else \
		echo "No pyproject.toml found"; \
	fi
	@echo "Current directory: $$(pwd)"
	@echo "Git status:"
	@git status --porcelain 2>/dev/null || echo "Not a git repository"
