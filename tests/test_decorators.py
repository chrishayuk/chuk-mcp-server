#!/usr/bin/env python3
"""Tests for the decorators module."""

import pytest

from chuk_mcp_server.decorators import get_global_registry, prompt, resource, tool
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
