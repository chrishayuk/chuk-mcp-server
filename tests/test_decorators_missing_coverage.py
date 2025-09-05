#!/usr/bin/env python3
"""Tests for missing coverage in decorators module."""

from chuk_mcp_server.decorators import (
    clear_global_registry,
    get_global_prompts,
    get_global_resources,
    get_global_tools,
    get_prompt_from_function,
    get_resource_from_function,
    get_tool_from_function,
    is_prompt,
    is_resource,
    is_tool,
    prompt,
    resource,
    tool,
)


class TestMissingGlobalRegistryFunctions:
    """Test missing global registry functions for coverage."""

    def setup_method(self):
        """Clear global registry before each test."""
        clear_global_registry()

    def test_get_global_tools_copy(self):
        """Test get_global_tools returns a copy (line 24)."""

        @tool
        def test_tool():
            return "test"

        tools1 = get_global_tools()
        tools2 = get_global_tools()

        # Should be separate copies
        assert tools1 == tools2
        assert tools1 is not tools2  # Different objects

        # Modifying one doesn't affect the other
        tools1.clear()
        tools2_after = get_global_tools()
        assert len(tools2_after) == 1  # Original still intact

    def test_get_global_resources_copy(self):
        """Test get_global_resources returns a copy (line 29)."""

        @resource("test://resource")
        def test_resource():
            return "test"

        resources1 = get_global_resources()
        resources2 = get_global_resources()

        # Should be separate copies
        assert resources1 == resources2
        assert resources1 is not resources2  # Different objects

        # Modifying one doesn't affect the other
        resources1.clear()
        resources2_after = get_global_resources()
        assert len(resources2_after) == 1  # Original still intact

    def test_get_global_prompts_copy(self):
        """Test get_global_prompts returns a copy (line 34)."""

        @prompt
        def test_prompt():
            return "test"

        prompts1 = get_global_prompts()
        prompts2 = get_global_prompts()

        # Should be separate copies
        assert prompts1 == prompts2
        assert prompts1 is not prompts2  # Different objects

        # Modifying one doesn't affect the other
        prompts1.clear()
        prompts2_after = get_global_prompts()
        assert len(prompts2_after) == 1  # Original still intact

    def test_clear_global_registry_globals(self):
        """Test clear_global_registry handles global variables (lines 45-47)."""

        # Add items to all registries
        @tool
        def test_tool():
            return "tool"

        @resource("test://resource")
        def test_resource():
            return "resource"

        @prompt
        def test_prompt():
            return "prompt"

        # Verify items are registered
        assert len(get_global_tools()) == 1
        assert len(get_global_resources()) == 1
        assert len(get_global_prompts()) == 1

        # Clear registry
        clear_global_registry()

        # Verify all are cleared
        assert len(get_global_tools()) == 0
        assert len(get_global_resources()) == 0
        assert len(get_global_prompts()) == 0


class TestHelperFunctions:
    """Test helper functions for missing coverage."""

    def test_is_tool_function(self):
        """Test is_tool function (line 193)."""

        # Regular function - should be False
        def regular_func():
            return "test"

        assert is_tool(regular_func) is False

        # Decorated function - should be True
        @tool
        def tool_func():
            return "test"

        assert is_tool(tool_func) is True

    def test_is_resource_function(self):
        """Test is_resource function (line 198)."""

        # Regular function - should be False
        def regular_func():
            return "test"

        assert is_resource(regular_func) is False

        # Decorated function - should be True
        @resource("test://resource")
        def resource_func():
            return "test"

        assert is_resource(resource_func) is True

    def test_is_prompt_function(self):
        """Test is_prompt function (line 203)."""

        # Regular function - should be False
        def regular_func():
            return "test"

        assert is_prompt(regular_func) is False

        # Decorated function - should be True
        @prompt
        def prompt_func():
            return "test"

        assert is_prompt(prompt_func) is True

    def test_get_tool_from_function(self):
        """Test get_tool_from_function (line 208)."""

        # Regular function - should return None
        def regular_func():
            return "test"

        assert get_tool_from_function(regular_func) is None

        # Decorated function - should return handler
        @tool
        def tool_func():
            return "test"

        tool_handler = get_tool_from_function(tool_func)
        assert tool_handler is not None
        assert tool_handler.name == "tool_func"

    def test_get_resource_from_function(self):
        """Test get_resource_from_function (line 213)."""

        # Regular function - should return None
        def regular_func():
            return "test"

        assert get_resource_from_function(regular_func) is None

        # Decorated function - should return handler
        @resource("test://resource")
        def resource_func():
            return "test"

        resource_handler = get_resource_from_function(resource_func)
        assert resource_handler is not None
        assert resource_handler.uri == "test://resource"

    def test_get_prompt_from_function(self):
        """Test get_prompt_from_function (line 218)."""

        # Regular function - should return None
        def regular_func():
            return "test"

        assert get_prompt_from_function(regular_func) is None

        # Decorated function - should return handler
        @prompt
        def prompt_func():
            return "test"

        prompt_handler = get_prompt_from_function(prompt_func)
        assert prompt_handler is not None
        assert prompt_handler.name == "prompt_func"


class TestDecoratorComplexCases:
    """Test complex decorator cases for additional coverage."""

    def test_tool_decorator_direct_callable(self):
        """Test tool decorator with callable as first argument."""

        def test_func():
            return "test"

        # Test the case where tool() receives a callable directly
        # This triggers the branch at lines 86-93
        decorated_func = tool(test_func)

        assert decorated_func() == "test"
        assert is_tool(decorated_func) is True

        # Verify it was registered
        tools = get_global_tools()
        tool_handler = next((t for t in tools if t.name == "test_func"), None)
        assert tool_handler is not None

    def test_prompt_decorator_direct_callable(self):
        """Test prompt decorator with callable as first argument."""

        def test_func():
            return "test"

        # Test the case where prompt() receives a callable directly
        # This triggers the branch at lines 176-183
        decorated_func = prompt(test_func)

        assert decorated_func() == "test"
        assert is_prompt(decorated_func) is True

        # Verify it was registered
        prompts = get_global_prompts()
        prompt_handler = next((p for p in prompts if p.name == "test_func"), None)
        assert prompt_handler is not None

    def test_multiple_decorations_same_function(self):
        """Test what happens when multiple decorators are applied."""

        @prompt
        @tool
        def multi_decorated():
            return "test"

        # Function should work
        assert multi_decorated() == "test"

        # Should be recognized as both
        assert is_tool(multi_decorated) is True
        assert is_prompt(multi_decorated) is True

        # Should have both handlers
        tool_handler = get_tool_from_function(multi_decorated)
        prompt_handler = get_prompt_from_function(multi_decorated)

        assert tool_handler is not None
        assert prompt_handler is not None

    def test_function_metadata_preservation(self):
        """Test that function metadata is preserved through helpers."""

        @tool("custom_name", "custom description")
        def test_function(param: int) -> str:
            """Original docstring."""
            return f"result: {param}"

        # Function should work normally
        assert test_function(42) == "result: 42"

        # Metadata should be preserved
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Original docstring."

        # Handler should have custom name and description
        tool_handler = get_tool_from_function(test_function)
        assert tool_handler.name == "custom_name"
        assert tool_handler.description == "custom description"

    def test_edge_case_empty_strings(self):
        """Test decorators with empty strings."""

        @tool("", "")
        def empty_strings_tool():
            return "test"

        assert empty_strings_tool() == "test"

        tool_handler = get_tool_from_function(empty_strings_tool)
        assert tool_handler is not None
        # Empty string name falls back to function name
        assert tool_handler.name == "" or tool_handler.name == "empty_strings_tool"
        # Empty string description falls back to default pattern
        assert tool_handler.description == "Execute empty_strings_tool"

    def test_resource_name_parameter(self):
        """Test resource decorator with name parameter."""

        @resource("test://resource", name="Custom Resource Name")
        def named_resource():
            return "data"

        assert named_resource() == "data"

        resource_handler = get_resource_from_function(named_resource)
        assert resource_handler is not None
        assert resource_handler.name == "Custom Resource Name"
