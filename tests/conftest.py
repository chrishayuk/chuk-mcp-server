"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture(autouse=True)
def clear_cloud_registry():
    """Clear cloud registry before each test to prevent test pollution."""
    # This runs before each test
    yield
    # Cleanup after test if needed
    try:
        from chuk_mcp_server.cloud import cloud_registry

        # Clear the cache after each test
        cloud_registry.clear_cache()
    except ImportError:
        # Cloud module not imported, nothing to clean
        pass


@pytest.fixture(autouse=True)
def isolate_cloud_tests(request):
    """Isolate cloud provider tests from affecting other tests."""
    # Only apply to non-cloud tests
    if "cloud" not in str(request.fspath):
        try:
            from chuk_mcp_server.cloud import cloud_registry

            # Store current providers
            original_providers = cloud_registry._providers.copy()
            original_cache = cloud_registry._detection_cache

            # Clear for the test
            cloud_registry._providers.clear()
            cloud_registry._detection_cache = None

            yield

            # Restore after test
            cloud_registry._providers = original_providers
            cloud_registry._detection_cache = original_cache
        except ImportError:
            yield
    else:
        # For cloud tests, don't isolate
        yield
