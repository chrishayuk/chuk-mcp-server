"""Tests for module loader."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from chuk_mcp_server.modules import ModuleLoader


class MockServer:
    """Mock server for testing."""

    def __init__(self):
        self.protocol = MagicMock()


class TestModuleLoader:
    """Test ModuleLoader class."""

    def test_init_no_config(self):
        """Test initialization without configuration."""
        loader = ModuleLoader()
        assert loader.config == {}
        assert loader.server is None
        assert loader.loaded_modules == {}
        assert loader.loaded_tools == {}

    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = {"tool_modules": {"test": {"enabled": True}}}
        server = MockServer()
        loader = ModuleLoader(config, server)
        assert loader.config == config
        assert loader.server == server

    def test_load_modules_no_config(self):
        """Test loading modules with no configuration."""
        loader = ModuleLoader({})
        result = loader.load_modules()
        assert result == {}

    def test_load_modules_disabled_module(self):
        """Test loading with disabled module."""
        config = {"tool_modules": {"test": {"enabled": False, "module": "test.tools"}}}
        loader = ModuleLoader(config)
        result = loader.load_modules()
        assert result == {}

    def test_load_modules_no_module_path(self):
        """Test loading module without module path."""
        config = {"tool_modules": {"test": {"enabled": True}}}
        loader = ModuleLoader(config)
        result = loader.load_modules()
        assert result == {}

    def test_resolve_path_absolute(self):
        """Test resolving absolute path."""
        loader = ModuleLoader()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            resolved = loader._resolve_path(str(path))
            assert resolved == path

    def test_resolve_path_nonexistent_absolute(self):
        """Test resolving nonexistent absolute path."""
        loader = ModuleLoader()
        resolved = loader._resolve_path("/nonexistent/path/that/does/not/exist")
        assert resolved is None

    def test_resolve_path_relative(self):
        """Test resolving relative path."""
        loader = ModuleLoader()
        # Use current directory as it exists
        resolved = loader._resolve_path(".")
        assert resolved is not None
        assert resolved.exists()

    def test_resolve_path_nonexistent_relative(self):
        """Test resolving nonexistent relative path."""
        loader = ModuleLoader()
        resolved = loader._resolve_path("nonexistent_directory_xyz")
        assert resolved is None

    def test_scan_module_for_tools_no_tools(self):
        """Test scanning module with no tools."""
        loader = ModuleLoader()

        # Create a simple module-like object
        class FakeModule:
            some_var = 123

        module = FakeModule()
        tools = loader._scan_module_for_tools("test", module, {})
        assert tools == []

    def test_scan_module_for_tools_with_metadata(self):
        """Test scanning module with tool metadata."""
        loader = ModuleLoader(server=MockServer())

        # Create a module-like class with test tool
        class FakeModule:
            @staticmethod
            def test_tool(a: int) -> int:
                return a * 2

        # Add metadata to the function
        FakeModule.test_tool._mcp_tool_metadata = {"name": "test_tool", "description": "A test tool"}

        module = FakeModule()
        tools = loader._scan_module_for_tools("test", module, {"namespace": "test"})
        assert len(tools) == 1
        assert tools[0] == "test.test_tool"

    def test_scan_module_disabled_tool(self):
        """Test scanning module with disabled tool."""
        loader = ModuleLoader(server=MockServer())

        class FakeModule:
            @staticmethod
            def test_tool() -> str:
                return "test"

        FakeModule.test_tool._mcp_tool_metadata = {"name": "test_tool"}

        module = FakeModule()
        config = {"tools": {"test_tool": {"enabled": False}}, "namespace": "test"}

        tools = loader._scan_module_for_tools("test", module, config)
        assert len(tools) == 0

    def test_register_tool_success(self):
        """Test successful tool registration."""
        server = MockServer()
        loader = ModuleLoader(server=server)

        def test_func(x: int) -> int:
            """Test function."""
            return x * 2

        metadata = {"name": "test", "description": "Test tool"}
        result = loader._register_tool("test.tool", test_func, metadata)
        assert result is True
        assert "test.tool" in loader.loaded_tools

    def test_register_tool_without_server(self):
        """Test tool registration without server."""
        loader = ModuleLoader()

        def test_func() -> str:
            return "test"

        metadata = {"name": "test"}
        result = loader._register_tool("test.tool", test_func, metadata)
        assert result is True
        assert "test.tool" in loader.loaded_tools

    def test_get_loaded_tools(self):
        """Test getting loaded tools."""
        loader = ModuleLoader()
        loader.loaded_tools = {"tool1": MagicMock(), "tool2": MagicMock()}
        tools = loader.get_loaded_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_get_loaded_modules(self):
        """Test getting loaded modules."""
        loader = ModuleLoader()
        loader.loaded_modules = {"module1": MagicMock(), "module2": MagicMock()}
        modules = loader.get_loaded_modules()
        assert len(modules) == 2
        assert "module1" in modules
        assert "module2" in modules

    def test_get_module_info(self):
        """Test getting module information."""
        loader = ModuleLoader()
        loader.loaded_modules = {"test_module": MagicMock()}
        loader.loaded_tools = {"test_module.tool1": MagicMock(), "test_module.tool2": MagicMock()}
        loader.module_paths = {"test_module": "/path/to/module"}

        info = loader.get_module_info()
        assert info["total_modules"] == 1
        assert info["total_tools"] == 2
        assert "test_module" in info["modules"]
        assert info["modules"]["test_module"]["path"] == "/path/to/module"
        assert len(info["modules"]["test_module"]["tools"]) == 2

    def test_get_module_info_empty(self):
        """Test getting module info when nothing loaded."""
        loader = ModuleLoader()
        info = loader.get_module_info()
        assert info["total_modules"] == 0
        assert info["total_tools"] == 0
        assert info["modules"] == {}

    def test_load_module_invalid_config(self):
        """Test loading module with invalid config structure."""
        loader = ModuleLoader()
        # Pass a string instead of dict
        result = loader._load_module("test", "invalid_config")
        assert result == []

    def test_load_modules_with_location(self):
        """Test loading modules with location specified."""
        # Create a temporary module
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create module directory
            module_dir = Path(tmpdir) / "test_module"
            module_dir.mkdir()

            # Create __init__.py
            (module_dir / "__init__.py").write_text("")

            # Create tools.py with a simple tool
            tools_content = '''
def example_tool():
    """An example tool."""
    return "example"

example_tool._mcp_tool_metadata = {"name": "example_tool", "description": "Example"}
'''
            (module_dir / "tools.py").write_text(tools_content)

            # Configure loader
            config = {
                "tool_modules": {
                    "test": {"enabled": True, "location": tmpdir, "module": "test_module.tools", "namespace": "test"}
                }
            }

            loader = ModuleLoader(config, MockServer())
            result = loader.load_modules()

            # Should successfully load
            assert "test" in result
            assert len(result["test"]) > 0

    def test_load_modules_import_error(self):
        """Test handling of import errors."""
        config = {
            "tool_modules": {"test": {"enabled": True, "module": "nonexistent_module_xyz.tools", "namespace": "test"}}
        }

        loader = ModuleLoader(config)
        result = loader.load_modules()

        # Should handle error gracefully
        assert result == {}
