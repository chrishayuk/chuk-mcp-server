#!/usr/bin/env python3
"""Tests for the decorators module."""

import pytest

from chuk_mcp_server.decorators import (
    clear_global_registry,
    get_global_prompts,
    get_global_registry,
    get_global_resources,
    get_global_tools,
    get_prompt_from_function,
    get_resource_from_function,
    get_tool_from_function,
    is_prompt,
    is_resource,
    is_tool,
    prompt,
    requires_auth,
    resource,
    tool,
)
from chuk_mcp_server.types import PromptHandler, ResourceHandler, ToolHandler


class TestToolDecorator:
    """Test the @tool decorator."""

    def test_tool_decorator_basic(self):
        """Test basic tool decorator usage."""

        @tool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        # Function should still work normally
        assert add(2, 3) == 5

        # Check that it was registered globally
        registry = get_global_registry()
        assert len(registry["tools"]) > 0

        # Find our tool
        tool_handler = next((t for t in registry["tools"] if t.name == "add"), None)
        assert tool_handler is not None
        assert isinstance(tool_handler, ToolHandler)
        assert tool_handler.description == "Add two numbers."

    def test_tool_decorator_with_name(self):
        """Test tool decorator with custom name."""

        @tool(name="custom_subtract")
        def subtract(a: int, b: int) -> int:
            """Subtract b from a."""
            return a - b

        assert subtract(5, 3) == 2

        registry = get_global_registry()
        tool_handler = next((t for t in registry["tools"] if t.name == "custom_subtract"), None)
        assert tool_handler is not None
        assert tool_handler.description == "Subtract b from a."

    def test_tool_decorator_with_description(self):
        """Test tool decorator with custom description."""

        @tool(description="Custom multiplication description")
        def multiply(a: int, b: int) -> int:
            return a * b

        assert multiply(3, 4) == 12

        registry = get_global_registry()
        tool_handler = next((t for t in registry["tools"] if t.name == "multiply"), None)
        assert tool_handler is not None
        assert tool_handler.description == "Custom multiplication description"

    def test_tool_decorator_with_both_params(self):
        """Test tool decorator with name and description."""

        @tool(name="div", description="Divide two numbers")
        def divide(a: float, b: float) -> float:
            """This docstring is ignored."""
            return a / b

        assert divide(10, 2) == 5.0

        registry = get_global_registry()
        tool_handler = next((t for t in registry["tools"] if t.name == "div"), None)
        assert tool_handler is not None
        assert tool_handler.description == "Divide two numbers"

    @pytest.mark.asyncio
    async def test_tool_decorator_async_function(self):
        """Test tool decorator with async function."""

        @tool
        async def async_process(data: str) -> str:
            """Process data asynchronously."""
            return f"processed: {data}"

        result = await async_process("test")
        assert result == "processed: test"

        registry = get_global_registry()
        tool_handler = next((t for t in registry["tools"] if t.name == "async_process"), None)
        assert tool_handler is not None
        assert tool_handler.description == "Process data asynchronously."


class TestResourceDecorator:
    """Test the @resource decorator."""

    def test_resource_decorator_basic(self):
        """Test basic resource decorator usage."""

        @resource("config://settings")
        def get_settings() -> dict:
            """Get application settings."""
            return {"debug": True, "port": 8000}

        assert get_settings() == {"debug": True, "port": 8000}

        registry = get_global_registry()
        assert len(registry["resources"]) > 0

        resource_handler = next((r for r in registry["resources"] if r.uri == "config://settings"), None)
        assert resource_handler is not None
        assert isinstance(resource_handler, ResourceHandler)
        assert resource_handler.description == "Get application settings."

    def test_resource_decorator_with_description(self):
        """Test resource decorator with custom description."""

        @resource("data://users", description="User database")
        def get_users() -> list:
            return ["alice", "bob"]

        assert get_users() == ["alice", "bob"]

        registry = get_global_registry()
        resource_handler = next((r for r in registry["resources"] if r.uri == "data://users"), None)
        assert resource_handler is not None
        assert resource_handler.description == "User database"

    def test_resource_decorator_with_mime_type(self):
        """Test resource decorator with MIME type."""

        @resource("file://readme", mime_type="text/markdown")
        def get_readme() -> str:
            """Get README content."""
            return "# Project README"

        assert get_readme() == "# Project README"

        registry = get_global_registry()
        resource_handler = next((r for r in registry["resources"] if r.uri == "file://readme"), None)
        assert resource_handler is not None
        assert resource_handler.mime_type == "text/markdown"

    @pytest.mark.asyncio
    async def test_resource_decorator_async_function(self):
        """Test resource decorator with async function."""

        @resource("api://data")
        async def fetch_data() -> dict:
            """Fetch data from API."""
            return {"status": "ok"}

        result = await fetch_data()
        assert result == {"status": "ok"}

        registry = get_global_registry()
        resource_handler = next((r for r in registry["resources"] if r.uri == "api://data"), None)
        assert resource_handler is not None
        assert resource_handler.description == "Fetch data from API."


class TestPromptDecorator:
    """Test the @prompt decorator."""

    def test_prompt_decorator_basic(self):
        """Test basic prompt decorator usage."""

        @prompt
        def greeting_prompt(name: str) -> str:
            """Generate a greeting prompt."""
            return f"Hello, {name}! How can I help you today?"

        assert greeting_prompt("Alice") == "Hello, Alice! How can I help you today?"

        registry = get_global_registry()
        assert len(registry["prompts"]) > 0

        prompt_handler = next((p for p in registry["prompts"] if p.name == "greeting_prompt"), None)
        assert prompt_handler is not None
        assert isinstance(prompt_handler, PromptHandler)
        assert prompt_handler.description == "Generate a greeting prompt."

    def test_prompt_decorator_with_name(self):
        """Test prompt decorator with custom name."""

        @prompt(name="custom_farewell")
        def farewell(name: str) -> str:
            """Say goodbye."""
            return f"Goodbye, {name}!"

        assert farewell("Bob") == "Goodbye, Bob!"

        registry = get_global_registry()
        prompt_handler = next((p for p in registry["prompts"] if p.name == "custom_farewell"), None)
        assert prompt_handler is not None
        assert prompt_handler.description == "Say goodbye."

    def test_prompt_decorator_with_description(self):
        """Test prompt decorator with custom description."""

        @prompt(description="Custom question prompt")
        def question_prompt(topic: str) -> str:
            return f"What do you think about {topic}?"

        assert question_prompt("AI") == "What do you think about AI?"

        registry = get_global_registry()
        prompt_handler = next((p for p in registry["prompts"] if p.name == "question_prompt"), None)
        assert prompt_handler is not None
        assert prompt_handler.description == "Custom question prompt"

    def test_prompt_decorator_returning_dict(self):
        """Test prompt decorator with function returning dict."""

        @prompt
        def structured_prompt(task: str) -> dict:
            """Create a structured prompt."""
            return {"role": "user", "content": f"Please complete this task: {task}"}

        result = structured_prompt("Write code")
        assert result == {"role": "user", "content": "Please complete this task: Write code"}

        registry = get_global_registry()
        prompt_handler = next((p for p in registry["prompts"] if p.name == "structured_prompt"), None)
        assert prompt_handler is not None

    @pytest.mark.asyncio
    async def test_prompt_decorator_async_function(self):
        """Test prompt decorator with async function."""

        @prompt
        async def async_prompt(query: str) -> str:
            """Generate prompt asynchronously."""
            return f"Query: {query}"

        result = await async_prompt("test query")
        assert result == "Query: test query"

        registry = get_global_registry()
        prompt_handler = next((p for p in registry["prompts"] if p.name == "async_prompt"), None)
        assert prompt_handler is not None


class TestGlobalRegistry:
    """Test the global registry functionality."""

    def test_get_global_registry_structure(self):
        """Test that global registry has correct structure."""
        registry = get_global_registry()

        assert isinstance(registry, dict)
        assert "tools" in registry
        assert "resources" in registry
        assert "prompts" in registry

        assert isinstance(registry["tools"], list)
        assert isinstance(registry["resources"], list)
        assert isinstance(registry["prompts"], list)

    def test_registry_accumulates_items(self):
        """Test that registry accumulates decorated items."""
        initial_registry = get_global_registry()
        initial_tool_count = len(initial_registry["tools"])

        @tool
        def test_tool_1() -> str:
            return "tool1"

        @tool
        def test_tool_2() -> str:
            return "tool2"

        registry = get_global_registry()
        assert len(registry["tools"]) == initial_tool_count + 2

    def test_mixed_decorators_registration(self):
        """Test that all decorator types register correctly."""
        initial_registry = get_global_registry()
        initial_tools = len(initial_registry["tools"])
        initial_resources = len(initial_registry["resources"])
        initial_prompts = len(initial_registry["prompts"])

        @tool
        def mixed_tool() -> str:
            return "tool"

        @resource("mixed://resource")
        def mixed_resource() -> str:
            return "resource"

        @prompt
        def mixed_prompt() -> str:
            return "prompt"

        registry = get_global_registry()
        assert len(registry["tools"]) == initial_tools + 1
        assert len(registry["resources"]) == initial_resources + 1
        assert len(registry["prompts"]) == initial_prompts + 1


class TestDecoratorEdgeCases:
    """Test edge cases and error handling."""

    def test_tool_without_docstring(self):
        """Test tool decorator on function without docstring."""

        @tool
        def no_doc_tool(x: int) -> int:
            return x * 2

        assert no_doc_tool(5) == 10

        registry = get_global_registry()
        tool_handler = next((t for t in registry["tools"] if t.name == "no_doc_tool"), None)
        assert tool_handler is not None
        # Should use function name as fallback description
        assert tool_handler.description is not None

    def test_resource_without_docstring(self):
        """Test resource decorator on function without docstring."""

        @resource("test://nodoc")
        def no_doc_resource():
            return "data"

        assert no_doc_resource() == "data"

        registry = get_global_registry()
        resource_handler = next((r for r in registry["resources"] if r.uri == "test://nodoc"), None)
        assert resource_handler is not None

    def test_prompt_without_docstring(self):
        """Test prompt decorator on function without docstring."""

        @prompt
        def no_doc_prompt():
            return "prompt"

        assert no_doc_prompt() == "prompt"

        registry = get_global_registry()
        prompt_handler = next((p for p in registry["prompts"] if p.name == "no_doc_prompt"), None)
        assert prompt_handler is not None

    def test_decorator_preserves_function_metadata(self):
        """Test that decorators preserve function metadata."""

        @tool
        def metadata_test(x: int) -> int:
            """Test function."""
            return x

        assert metadata_test.__name__ == "metadata_test"
        assert metadata_test.__doc__ == "Test function."

    def test_decorator_on_method(self):
        """Test decorator on class method."""

        class TestClass:
            @tool
            def method_tool(self, x: int) -> int:
                """Class method tool."""
                return x * 2

        obj = TestClass()
        assert obj.method_tool(3) == 6

        registry = get_global_registry()
        tool_handler = next((t for t in registry["tools"] if t.name == "method_tool"), None)
        assert tool_handler is not None


class TestRequiresAuthDecorator:
    """Test the @requires_auth decorator."""

    @pytest.mark.asyncio
    async def test_requires_auth_basic(self):
        """Test basic requires_auth decorator usage (no parentheses)."""

        @requires_auth
        async def auth_tool(_external_access_token: str | None = None) -> str:
            """Tool requiring auth."""
            return f"token: {_external_access_token}"

        # Function should have auth metadata
        assert hasattr(auth_tool, "_requires_auth")
        assert auth_tool._requires_auth is True
        assert hasattr(auth_tool, "_auth_scopes")
        assert auth_tool._auth_scopes is None

        # Function should still execute
        result = await auth_tool(_external_access_token="test_token")
        assert result == "token: test_token"

    @pytest.mark.asyncio
    async def test_requires_auth_with_scopes(self):
        """Test requires_auth decorator with scopes."""

        @requires_auth(scopes=["posts.write", "profile.read"])
        async def scoped_tool(_external_access_token: str | None = None) -> str:
            """Tool with scopes."""
            return "authorized"

        assert hasattr(scoped_tool, "_requires_auth")
        assert scoped_tool._requires_auth is True
        assert hasattr(scoped_tool, "_auth_scopes")
        assert scoped_tool._auth_scopes == ["posts.write", "profile.read"]

        result = await scoped_tool(_external_access_token="token")
        assert result == "authorized"

    @pytest.mark.asyncio
    async def test_requires_auth_with_empty_parentheses(self):
        """Test requires_auth decorator with empty parentheses."""

        @requires_auth()
        async def empty_parens_tool(_external_access_token: str | None = None) -> str:
            """Tool with empty parens."""
            return "ok"

        assert hasattr(empty_parens_tool, "_requires_auth")
        assert empty_parens_tool._requires_auth is True
        assert empty_parens_tool._auth_scopes is None

        result = await empty_parens_tool()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_requires_auth_sync_function(self):
        """Test requires_auth decorator on synchronous function."""

        @requires_auth(scopes=["read"])
        def sync_auth_tool(_external_access_token: str | None = None) -> str:
            """Sync tool requiring auth."""
            return f"sync: {_external_access_token}"

        assert hasattr(sync_auth_tool, "_requires_auth")
        assert sync_auth_tool._requires_auth is True
        assert sync_auth_tool._auth_scopes == ["read"]

        # Even sync functions get wrapped in async by requires_auth
        result = await sync_auth_tool(_external_access_token="sync_token")
        assert result == "sync: sync_token"

    @pytest.mark.asyncio
    async def test_requires_auth_async_coroutine(self):
        """Test requires_auth preserves async coroutine behavior."""

        @requires_auth
        async def async_coroutine(_external_access_token: str | None = None) -> str:
            """Async coroutine."""
            return "async_result"

        # Should be awaitable
        result = await async_coroutine()
        assert result == "async_result"


class TestHelperFunctions:
    """Test helper functions for checking decorated functions."""

    def test_is_tool(self):
        """Test is_tool helper function."""

        @tool
        def test_tool() -> str:
            return "tool"

        def regular_func() -> str:
            return "not a tool"

        assert is_tool(test_tool) is True
        assert is_tool(regular_func) is False

    def test_is_resource(self):
        """Test is_resource helper function."""

        @resource("test://uri")
        def test_resource() -> str:
            return "resource"

        def regular_func() -> str:
            return "not a resource"

        assert is_resource(test_resource) is True
        assert is_resource(regular_func) is False

    def test_is_prompt(self):
        """Test is_prompt helper function."""

        @prompt
        def test_prompt() -> str:
            return "prompt"

        def regular_func() -> str:
            return "not a prompt"

        assert is_prompt(test_prompt) is True
        assert is_prompt(regular_func) is False

    def test_get_tool_from_function(self):
        """Test get_tool_from_function helper."""

        @tool(name="test_get_tool")
        def test_tool() -> str:
            """Tool for testing."""
            return "tool"

        def regular_func() -> str:
            return "not a tool"

        tool_handler = get_tool_from_function(test_tool)
        assert tool_handler is not None
        assert isinstance(tool_handler, ToolHandler)
        assert tool_handler.name == "test_get_tool"

        assert get_tool_from_function(regular_func) is None

    def test_get_resource_from_function(self):
        """Test get_resource_from_function helper."""

        @resource("test://get_resource")
        def test_resource() -> str:
            """Resource for testing."""
            return "resource"

        def regular_func() -> str:
            return "not a resource"

        resource_handler = get_resource_from_function(test_resource)
        assert resource_handler is not None
        assert isinstance(resource_handler, ResourceHandler)
        assert resource_handler.uri == "test://get_resource"

        assert get_resource_from_function(regular_func) is None

    def test_get_prompt_from_function(self):
        """Test get_prompt_from_function helper."""

        @prompt(name="test_get_prompt")
        def test_prompt() -> str:
            """Prompt for testing."""
            return "prompt"

        def regular_func() -> str:
            return "not a prompt"

        prompt_handler = get_prompt_from_function(test_prompt)
        assert prompt_handler is not None
        assert isinstance(prompt_handler, PromptHandler)
        assert prompt_handler.name == "test_get_prompt"

        assert get_prompt_from_function(regular_func) is None


class TestGlobalRegistryFunctions:
    """Test global registry getter functions."""

    def test_get_global_tools(self):
        """Test get_global_tools function."""
        # Clear and add a test tool
        clear_global_registry()

        @tool
        def registry_test_tool() -> str:
            return "test"

        tools = get_global_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert any(t.name == "registry_test_tool" for t in tools)

    def test_get_global_resources(self):
        """Test get_global_resources function."""
        clear_global_registry()

        @resource("test://registry_resource")
        def registry_test_resource() -> str:
            return "test"

        resources = get_global_resources()
        assert isinstance(resources, list)
        assert len(resources) > 0
        assert any(r.uri == "test://registry_resource" for r in resources)

    def test_get_global_prompts(self):
        """Test get_global_prompts function."""
        clear_global_registry()

        @prompt
        def registry_test_prompt() -> str:
            return "test"

        prompts = get_global_prompts()
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        assert any(p.name == "registry_test_prompt" for p in prompts)

    def test_clear_global_registry(self):
        """Test clear_global_registry function."""

        # Add some items
        @tool
        def clear_test_tool() -> str:
            return "test"

        @resource("test://clear")
        def clear_test_resource() -> str:
            return "test"

        @prompt
        def clear_test_prompt() -> str:
            return "test"

        # Clear the registry
        clear_global_registry()

        # Verify all are empty
        registry = get_global_registry()
        assert len(registry["tools"]) == 0
        assert len(registry["resources"]) == 0
        assert len(registry["prompts"]) == 0

    def test_registry_returns_copies(self):
        """Test that registry getters return copies, not originals."""
        clear_global_registry()

        @tool
        def copy_test_tool() -> str:
            return "test"

        tools1 = get_global_tools()
        tools2 = get_global_tools()

        # Should be equal but not the same object
        assert tools1 == tools2
        assert tools1 is not tools2


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


class TestHelperFunctionsCoverage:
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
