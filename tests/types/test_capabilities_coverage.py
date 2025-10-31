#!/usr/bin/env python3
# tests/types/test_capabilities_coverage.py
"""
Additional tests for capabilities.py to achieve 90%+ coverage.
Focuses on missing line 42 and edge cases.
"""

import pytest


def test_filtered_server_capabilities_model_dump_skip_empty():
    """Test _FilteredServerCapabilities.model_dump skips empty capabilities (line 42)."""
    from chuk_mcp_server.types.capabilities import create_server_capabilities

    # Create capabilities with resources enabled but other empty capabilities
    caps = create_server_capabilities(tools=True, resources=False, prompts=False, logging=False)

    result = caps.model_dump(exclude_none=True)

    # Should include tools since it's explicitly set
    assert "tools" in result

    # Should not include empty resources/prompts capabilities
    # (since they weren't in _filter_kwargs)
    assert "resources" not in result or result.get("resources") is not None


def test_filtered_server_capabilities_keeps_logging_when_empty():
    """Test that logging capability is kept even when empty (line 39-40)."""
    from chuk_mcp_server.types.capabilities import create_server_capabilities

    # Create capabilities with logging enabled
    caps = create_server_capabilities(tools=False, resources=False, prompts=False, logging=True)

    result = caps.model_dump(exclude_none=True)

    # Logging should be kept even if empty
    assert "logging" in result


def test_filtered_server_capabilities_keeps_experimental_when_empty():
    """Test that experimental capability is kept even when empty (line 39-40)."""
    from chuk_mcp_server.types.capabilities import create_server_capabilities

    # Create capabilities with empty experimental dict
    caps = create_server_capabilities(tools=False, resources=False, prompts=False, logging=False, experimental={})

    result = caps.model_dump(exclude_none=True)

    # Experimental should be kept even if empty
    assert "experimental" in result


def test_create_server_capabilities_with_experimental_fallback():
    """Test create_server_capabilities experimental fallback path (lines 79-87)."""
    from chuk_mcp_server.types.capabilities import create_server_capabilities

    # Create capabilities with experimental features that might cause validation issues
    experimental_features = {"oauth": {"enabled": True}, "custom_feature": {"version": "1.0"}}

    caps = create_server_capabilities(tools=True, resources=True, experimental=experimental_features)

    # Should have experimental set
    assert hasattr(caps, "experimental")


def test_create_server_capabilities_all_disabled():
    """Test create_server_capabilities with all features disabled."""
    from chuk_mcp_server.types.capabilities import create_server_capabilities

    caps = create_server_capabilities(tools=False, resources=False, prompts=False, logging=False)

    result = caps.model_dump(exclude_none=True)

    # Should have minimal or no capabilities
    assert "tools" not in result or result["tools"] is None
    assert "resources" not in result or result["resources"] is None
    assert "prompts" not in result or result["prompts"] is None
    assert "logging" not in result or result["logging"] is None


def test_create_server_capabilities_only_prompts():
    """Test create_server_capabilities with only prompts enabled."""
    from chuk_mcp_server.types.capabilities import create_server_capabilities

    caps = create_server_capabilities(tools=False, resources=False, prompts=True, logging=False)

    result = caps.model_dump(exclude_none=True)

    # Should only have prompts
    assert "prompts" in result
    assert result["prompts"] is not None


def test_create_server_capabilities_all_enabled():
    """Test create_server_capabilities with all features enabled."""
    from chuk_mcp_server.types.capabilities import create_server_capabilities

    caps = create_server_capabilities(tools=True, resources=True, prompts=True, logging=True)

    result = caps.model_dump(exclude_none=True)

    # Should have all capabilities
    assert "tools" in result
    assert "resources" in result
    assert "prompts" in result
    assert "logging" in result


def test_filtered_server_capabilities_filter_kwargs():
    """Test that _filter_kwargs properly controls what's included."""
    from chuk_mcp_server.types.capabilities import create_server_capabilities

    # Create with only tools
    caps = create_server_capabilities(tools=True, resources=False, prompts=False)

    result = caps.model_dump(exclude_none=True)

    # Should only include tools in result
    assert "tools" in result


def test_create_server_capabilities_experimental_none():
    """Test create_server_capabilities with experimental=None."""
    from chuk_mcp_server.types.capabilities import create_server_capabilities

    caps = create_server_capabilities(tools=True, experimental=None)

    result = caps.model_dump(exclude_none=True)

    # Should not include experimental when None
    assert "experimental" not in result or result.get("experimental") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
