# Releasing chuk-mcp-server

This document describes the release process for chuk-mcp-server.

## Prerequisites

Before releasing, ensure:

- [ ] All tests pass: `make test` or `uv run pytest`
- [ ] Type checking passes: `make typecheck` or `uv run mypy src`
- [ ] Linting passes: `make lint` or `uv run ruff check .`
- [ ] Security checks pass: `make security` or `uv run bandit -r src/`
- [ ] Documentation is up to date
- [ ] CHANGELOG is updated (if you maintain one)
- [ ] You are on the `main` branch
- [ ] Your working directory is clean

## Release Workflow (Recommended)

The easiest way to release is using the automated GitHub Actions workflow:

### Step 1: Bump Version

```bash
# For a patch release (0.0.X) - bug fixes
make bump-patch

# For a minor release (0.X.0) - new features, backward compatible
make bump-minor

# For a major release (X.0.0) - breaking changes
make bump-major
```

This will update the version in `pyproject.toml`.

### Step 2: Commit Version Change

```bash
git add pyproject.toml
git commit -m "Bump version to $(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')"
git push origin main
```

### Step 3: Create Release

```bash
make publish
```

This will:
1. ✅ Verify working directory is clean
2. ✅ Verify tag doesn't already exist
3. ✅ Create annotated git tag (e.g., `v0.5.1`)
4. ✅ Push tag to GitHub
5. ✅ Trigger automated workflows

### Step 4: Monitor GitHub Actions

The tag push triggers two automated workflows:

1. **Release Workflow** (`release.yml`)
   - Validates version matches `pyproject.toml`
   - Generates changelog from git commits
   - Creates GitHub release

2. **Publish Workflow** (`publish.yml`)
   - Runs full test suite
   - Builds package distributions
   - Publishes to PyPI via OIDC (no API token needed!)

Monitor progress at: `https://github.com/chrishayuk/chuk-mcp-server/actions`

### Step 5: Verify Release

Once workflows complete:

```bash
# Check PyPI
pip install --upgrade chuk-mcp-server
python -c "import chuk_mcp_server; print(chuk_mcp_server.__version__)"

# Check GitHub release
# Visit: https://github.com/chrishayuk/chuk-mcp-server/releases
```

## Manual Release (Alternative)

If you need to release manually (not recommended):

### Build and Test

```bash
# Clean previous builds
make clean-build

# Build package
make build

# Check distributions
ls -lh dist/
```

### Publish to Test PyPI (Optional)

```bash
make publish-test
```

Then test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ chuk-mcp-server
```

### Publish to PyPI

```bash
make publish-manual
```

⚠️ **Warning**: Manual publishing requires you to create git tags and GitHub releases separately.

## Versioning

We follow [Semantic Versioning](https://semver.org/):

- **Major (X.0.0)**: Breaking changes to public APIs
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes, backward compatible

### Version Bumping Examples

```bash
# Current: 0.5.0

make bump-patch   # → 0.5.1 (bug fix)
make bump-minor   # → 0.6.0 (new feature)
make bump-major   # → 1.0.0 (breaking change)
```

## Hotfix Process

For urgent bug fixes to production:

1. Create hotfix branch from the release tag:
   ```bash
   git checkout -b hotfix/v0.5.1 v0.5.0
   ```

2. Apply and test the fix:
   ```bash
   # Make changes
   git add .
   git commit -m "Fix critical bug in X"
   ```

3. Bump patch version:
   ```bash
   make bump-patch
   git add pyproject.toml
   git commit -m "Bump version to 0.5.1"
   ```

4. Merge to main:
   ```bash
   git checkout main
   git merge hotfix/v0.5.1
   git push origin main
   ```

5. Release the hotfix:
   ```bash
   make publish
   ```

6. Clean up:
   ```bash
   git branch -d hotfix/v0.5.1
   ```

## Rollback

If a release has critical issues:

### Option 1: Yank from PyPI

You cannot delete a version from PyPI, but you can "yank" it to prevent new installations:

```bash
# Using twine
twine upload --skip-existing --repository pypi dist/*
# Then yank the bad version via PyPI web UI
```

### Option 2: Release a Fixed Version

1. Fix the issue
2. Bump the patch version
3. Release as normal

## Checklist

Use this checklist for each release:

- [ ] Tests pass (`make check`)
- [ ] Version bumped (`make bump-patch|minor|major`)
- [ ] Version committed and pushed
- [ ] `make publish` executed successfully
- [ ] GitHub Actions workflows completed
- [ ] GitHub release created
- [ ] PyPI package published
- [ ] Installation verified (`pip install --upgrade chuk-mcp-server`)
- [ ] Version verified in Python

## Troubleshooting

### "Tag already exists"

Delete the tag locally and remotely:
```bash
git tag -d v0.5.1
git push origin :refs/tags/v0.5.1
```

### "Working directory not clean"

Commit or stash changes:
```bash
git status
git add .
git commit -m "Your commit message"
# OR
git stash
```

### "Version mismatch between tag and pyproject.toml"

Ensure you've committed the version bump:
```bash
git add pyproject.toml
git commit -m "Bump version to X.Y.Z"
git push origin main
```

### "PyPI upload failed"

Check if version already exists on PyPI:
- https://pypi.org/project/chuk-mcp-server/

If it exists, bump to the next version.

### GitHub Actions workflow failed

1. Check the Actions tab: https://github.com/chrishayuk/chuk-mcp-server/actions
2. Review error logs
3. Fix the issue
4. Delete the tag: `git push origin :refs/tags/vX.Y.Z`
5. Delete the GitHub release (if created)
6. Try again with a new patch version

## PyPI Configuration

### OIDC Publishing (Recommended)

The publish workflow uses PyPI's Trusted Publisher feature (OIDC). No API tokens needed!

To set this up (one-time):

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher:
   - **PyPI Project Name**: `chuk-mcp-server`
   - **Owner**: `chrishayuk`
   - **Repository name**: `chuk-mcp-server`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

### API Token (Alternative)

If not using OIDC, create a PyPI API token:

1. Go to https://pypi.org/manage/account/token/
2. Create a new token with scope for `chuk-mcp-server`
3. Add as GitHub secret: `PYPI_API_TOKEN`
4. Update publish.yml to use token authentication

## Support

Questions? Issues?

- 📖 [Documentation](https://github.com/chrishayuk/chuk-mcp-server)
- 🐛 [Issues](https://github.com/chrishayuk/chuk-mcp-server/issues)
- 💬 [Discussions](https://github.com/chrishayuk/chuk-mcp-server/discussions)
