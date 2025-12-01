# Pull Request Workflow

How to contribute code to ChukMCPServer.

## Before You Start

1. **Check existing issues** - Is there already an issue for this?
2. **Create an issue** - Describe what you want to add/fix
3. **Get feedback** - Discuss approach before coding
4. **Fork the repository** - Work on your own fork

## Development Workflow

### 1. Create a Branch

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

Branch naming:
- `feature/oauth-google-drive` - New features
- `fix/sse-connection-drops` - Bug fixes
- `docs/update-quickstart` - Documentation
- `test/oauth-providers` - Tests only
- `refactor/type-system` - Refactoring

### 2. Make Changes

```bash
# Make your changes
vim src/chuk_mcp_server/your_file.py

# Run quality checks frequently
make check

# Format code
make format
```

### 3. Write Tests

Every change needs tests:

```python
# tests/test_your_feature.py
def test_your_feature():
    """Test your new feature."""
    # Arrange
    mcp = ChukMCPServer(name="test")
    
    # Act
    result = your_feature()
    
    # Assert
    assert result == expected
```

Ensure coverage:

```bash
make test-cov
# Target: 90%+ for new code
```

### 4. Update Documentation

If needed:
- Update README
- Add/update docs pages
- Update CHANGELOG.md
- Add docstrings

### 5. Commit Changes

Follow conventional commits:

```bash
git add .
git commit -m "feat(oauth): Add Google Drive provider

Implements OAuth 2.1 with PKCE for Google Drive integration.

- Automatic token refresh
- Secure token storage
- Drive API scopes

Fixes #42"
```

### 6. Push to Fork

```bash
git push origin feature/your-feature-name
```

### 7. Create Pull Request

On GitHub:
1. Click "New Pull Request"
2. Select your fork and branch
3. Fill in PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Coverage maintained/improved

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Related Issues
Fixes #42
```

## PR Requirements

Your PR must:

✅ **Pass all checks**
```bash
make check  # Must succeed
```

✅ **Maintain coverage**
- Overall: 80% minimum
- New code: 90% minimum

✅ **Follow style guide**
- Type hints required
- Docstrings required
- ruff formatting

✅ **Include tests**
- Unit tests for all functions
- Integration tests for features

✅ **Update docs**
- If API changes
- If behavior changes

## Review Process

1. **Automated checks** run first
   - Linting (ruff)
   - Type checking (mypy)
   - Tests (pytest)
   - Coverage report

2. **Code review** by maintainers
   - Design feedback
   - Code quality
   - Test coverage
   - Documentation

3. **Address feedback**
   - Make requested changes
   - Push updates
   - Re-request review

4. **Merge**
   - Approved by maintainer
   - All checks passing
   - Squash and merge

## After Merge

Your PR:
- Appears in CHANGELOG.md
- Included in next release
- You're added to contributors!

## Common Issues

### Tests Failing

```bash
# Run locally
make test

# Check specific test
pytest tests/test_file.py::test_name -v

# Debug
pytest --pdb
```

### Type Errors

```bash
# Run mypy
make typecheck

# Fix common issues
# - Add type hints
# - Import from typing
# - Use | instead of Union
```

### Coverage Too Low

```bash
# Check coverage
make test-cov

# View report
open htmlcov/index.html

# Add tests for uncovered lines
```

### Merge Conflicts

```bash
# Update your branch
git checkout main
git pull origin main
git checkout feature/your-branch
git rebase main

# Resolve conflicts
# Edit conflicted files
git add .
git rebase --continue

# Force push
git push --force-with-lease
```

## Getting Help

- **Documentation**: Read the docs
- **Issues**: Search existing issues
- **Discussions**: Ask in GitHub Discussions
- **Discord**: Join our Discord server

## Code of Conduct

Be respectful and constructive:
- Assume good intentions
- Provide helpful feedback
- Welcome newcomers
- Focus on the code, not the person

## Recognition

Contributors are recognized:
- CONTRIBUTORS.md
- Release notes
- Project README

Thank you for contributing! 🎉

## Next Steps

- [Setup](setup.md) - Development environment
- [Style Guide](style.md) - Code standards
- [Testing](testing.md) - Writing tests
