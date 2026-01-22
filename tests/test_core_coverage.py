#!/usr/bin/env python3
"""Tests to achieve 90%+ coverage for core.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chuk_mcp_server.core import ChukMCPServer


class TestProxyConfiguration:
    """Test proxy manager configuration and operations."""

    def test_init_with_proxy_config(self):
        """Test initialization with proxy_config (line 154)."""
        proxy_config = {
            "servers": {
                "time": {
                    "transport": "http",
                    "url": "http://localhost:8001",
                    "namespace": "time",
                }
            }
        }

        with patch("chuk_mcp_server.core.ProxyManager") as mock_proxy_manager:
            server = ChukMCPServer(proxy_config=proxy_config)

            # ProxyManager should be instantiated
            mock_proxy_manager.assert_called_once()
            assert server.proxy_manager is not None

    def test_enable_proxy(self):
        """Test enable_proxy method (lines 975-976)."""
        server = ChukMCPServer()

        proxy_config = {"servers": {}}

        with patch("chuk_mcp_server.core.ProxyManager") as mock_proxy_manager:
            server.enable_proxy(proxy_config)

            mock_proxy_manager.assert_called_once_with(proxy_config, server.protocol)
            assert server.proxy_manager is not None

    def test_get_proxy_stats_with_proxy(self):
        """Test get_proxy_stats with proxy manager (lines 980-981)."""
        server = ChukMCPServer()

        mock_proxy = MagicMock()
        mock_proxy.get_stats.return_value = {"servers": 1, "tools": 5}
        server.proxy_manager = mock_proxy

        stats = server.get_proxy_stats()

        assert stats is not None
        assert stats["servers"] == 1
        assert stats["tools"] == 5

    def test_get_proxy_stats_without_proxy(self):
        """Test get_proxy_stats without proxy manager (line 982)."""
        server = ChukMCPServer()

        stats = server.get_proxy_stats()

        assert stats is None

    @pytest.mark.asyncio
    async def test_call_proxied_tool_with_proxy(self):
        """Test call_proxied_tool with proxy manager."""
        server = ChukMCPServer()

        mock_proxy = MagicMock()
        mock_proxy.call_tool = AsyncMock(return_value={"result": "success"})
        server.proxy_manager = mock_proxy

        result = await server.call_proxied_tool("proxy.time.get_time", tz="UTC")

        assert result["result"] == "success"
        mock_proxy.call_tool.assert_awaited_once_with("proxy.time.get_time", tz="UTC")

    @pytest.mark.asyncio
    async def test_call_proxied_tool_without_proxy(self):
        """Test call_proxied_tool without proxy manager (lines 995-996)."""
        server = ChukMCPServer()

        with pytest.raises(RuntimeError, match="Proxy mode not enabled"):
            await server.call_proxied_tool("some.tool")

    @pytest.mark.asyncio
    async def test_start_proxy_if_enabled(self):
        """Test _start_proxy_if_enabled (lines 692-694)."""
        server = ChukMCPServer()

        mock_proxy = MagicMock()
        mock_proxy.start_servers = AsyncMock()
        mock_proxy.get_stats.return_value = {"servers": 1}
        server.proxy_manager = mock_proxy

        await server._start_proxy_if_enabled()

        mock_proxy.start_servers.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_proxy_if_enabled(self):
        """Test _stop_proxy_if_enabled (lines 698-700)."""
        server = ChukMCPServer()

        mock_proxy = MagicMock()
        mock_proxy.stop_servers = AsyncMock()
        server.proxy_manager = mock_proxy

        await server._stop_proxy_if_enabled()

        mock_proxy.stop_servers.assert_awaited_once()


class TestToolModulesConfiguration:
    """Test tool modules configuration."""

    def test_init_with_tool_modules_config(self):
        """Test initialization with tool_modules_config (lines 159-163)."""
        tool_modules_config = {
            "math": {
                "enabled": True,
                "module": "math_tools",
            }
        }

        # ModuleLoader is imported inside the __init__, so patch it in modules module
        with patch("chuk_mcp_server.modules.ModuleLoader") as mock_loader:
            server = ChukMCPServer(tool_modules_config=tool_modules_config)

            # ModuleLoader should be instantiated
            mock_loader.assert_called_once()
            assert server.module_loader is not None

            # Check config is wrapped properly
            call_args = mock_loader.call_args
            assert "tool_modules" in call_args[0][0]


class TestCompositionMethods:
    """Test composition-related methods."""

    def test_import_server(self):
        """Test import_server method (line 426)."""
        server = ChukMCPServer()

        other_server = ChukMCPServer()

        with patch.object(server.composition, "import_server") as mock_import:
            server.import_server(other_server, prefix="api", components=["tools"])

            mock_import.assert_called_once_with(other_server, "api", ["tools"], None)

    def test_mount(self):
        """Test mount method (line 455)."""
        server = ChukMCPServer()

        other_server = ChukMCPServer()

        with patch.object(server.composition, "mount") as mock_mount:
            server.mount(other_server, prefix="data", as_proxy=False)

            mock_mount.assert_called_once_with(other_server, "data", False)

    def test_load_module(self):
        """Test load_module method (line 479)."""
        server = ChukMCPServer()

        module_config = {"math": {"enabled": True}}

        with patch.object(server.composition, "load_module", return_value={"math": ["add", "subtract"]}) as mock_load:
            result = server.load_module(module_config)

            mock_load.assert_called_once_with(module_config)
            assert result == {"math": ["add", "subtract"]}

    def test_get_composition_stats(self):
        """Test get_composition_stats method (line 488)."""
        server = ChukMCPServer()

        with patch.object(
            server.composition, "get_composition_stats", return_value={"imported": 2, "mounted": 1}
        ) as mock_stats:
            result = server.get_composition_stats()

            mock_stats.assert_called_once()
            assert result == {"imported": 2, "mounted": 1}


class TestClearMethods:
    """Test clear methods."""

    def test_clear_all(self):
        """Test clear_all method (lines 680-684)."""
        server = ChukMCPServer()

        # Mock the clear methods to test clear_all calls them
        with (
            patch.object(server, "clear_tools") as mock_clear_tools,
            patch.object(server, "clear_resources") as mock_clear_resources,
            patch.object(server, "clear_prompts") as mock_clear_prompts,
            patch.object(server, "clear_endpoints") as mock_clear_endpoints,
        ):
            server.clear_all()

            # Verify all clear methods were called
            mock_clear_tools.assert_called_once()
            mock_clear_resources.assert_called_once()
            mock_clear_prompts.assert_called_once()
            mock_clear_endpoints.assert_called_once()


class TestAlternativeHandlerCreation:
    """Test alternative handler creation paths."""

    def test_register_global_tool_without_handler_attr(self):
        """Test global tool registration when tool doesn't have handler attr (line 201)."""
        from chuk_mcp_server.decorators import clear_global_registry, tool

        # Create a global tool using decorator
        @tool()
        def global_test_tool(x: int) -> int:
            """Test tool."""
            return x * 2

        server = ChukMCPServer()

        # The tool should be registered
        tools = server.get_tools()
        assert any(t.name == "global_test_tool" for t in tools)

        # Clean up
        clear_global_registry()

    def test_register_global_resource_without_handler_attr(self):
        """Test global resource registration when resource doesn't have handler attr (line 211)."""
        from chuk_mcp_server.decorators import clear_global_registry, resource

        # Create a global resource using decorator
        @resource("test://global_resource")
        def global_test_resource() -> str:
            """Test resource."""
            return "test data"

        server = ChukMCPServer()

        # The resource should be registered
        resources = server.get_resources()
        assert any(r.uri == "test://global_resource" for r in resources)

        # Clean up
        clear_global_registry()

    def test_register_global_prompt_without_handler_attr(self):
        """Test global prompt registration when prompt doesn't have handler attr (line 227)."""
        from chuk_mcp_server.decorators import clear_global_registry, prompt

        # Create a global prompt using decorator
        @prompt()
        def global_test_prompt() -> str:
            """Test prompt."""
            return "test prompt"

        server = ChukMCPServer()

        # The prompt should be registered
        prompts = server.get_prompts()
        assert any(p.name == "global_test_prompt" for p in prompts)

        # Clean up
        clear_global_registry()


class TestStdioTransport:
    """Test STDIO transport functionality."""

    def test_run_stdio_transport_requested(self):
        """Test run() with stdio transport (line 739)."""
        server = ChukMCPServer(transport="stdio")

        with patch.object(server, "run_stdio") as mock_run_stdio:
            server.run()

            mock_run_stdio.assert_called_once()

    def test_run_stdio_method(self):
        """Test run_stdio method (lines 845-873)."""
        server = ChukMCPServer()

        with (
            patch("chuk_mcp_server.core.StdioSyncTransport") as mock_transport_class,
            patch("chuk_mcp_server.core.logging.basicConfig") as mock_basic_config,
        ):
            mock_transport = MagicMock()
            mock_transport_class.return_value = mock_transport

            # Test normal execution
            mock_transport.run.side_effect = KeyboardInterrupt()

            server.run_stdio(debug=False)

            mock_transport_class.assert_called_once_with(server.protocol)
            mock_transport.run.assert_called_once()
            mock_basic_config.assert_called()

    def test_run_stdio_with_debug(self):
        """Test run_stdio with debug=True."""
        server = ChukMCPServer()

        with (
            patch("chuk_mcp_server.core.StdioSyncTransport") as mock_transport_class,
            patch("chuk_mcp_server.core.logging.basicConfig") as mock_basic_config,
        ):
            mock_transport = MagicMock()
            mock_transport_class.return_value = mock_transport
            mock_transport.run.side_effect = KeyboardInterrupt()

            server.run_stdio(debug=True)

            # Should configure debug logging
            mock_basic_config.assert_called()
            assert any(
                call[1].get("level") == pytest.importorskip("logging").DEBUG
                for call in mock_basic_config.call_args_list
            )

    def test_run_stdio_with_exception(self):
        """Test run_stdio with exception."""
        server = ChukMCPServer()

        with (
            patch("chuk_mcp_server.core.StdioSyncTransport") as mock_transport_class,
            patch("chuk_mcp_server.core.logging.basicConfig"),
        ):
            mock_transport = MagicMock()
            mock_transport_class.return_value = mock_transport
            mock_transport.run.side_effect = RuntimeError("Transport error")

            with pytest.raises(RuntimeError, match="Transport error"):
                server.run_stdio()


class TestDebugMode:
    """Test debug mode and logging configurations."""

    def test_run_with_debug_banner(self):
        """Test run() with debug mode showing banner (lines 781-782)."""
        server = ChukMCPServer(debug=True)

        with (
            patch("chuk_mcp_server.core.create_server") as mock_create,
            patch.object(server, "_print_smart_config") as mock_print_config,
            patch("chuk_mcp_server.core.logging.basicConfig"),
        ):
            mock_app = MagicMock()
            mock_create.return_value = mock_app

            try:
                # Use a very short-lived server
                with patch("uvicorn.run") as mock_uvicorn:
                    mock_uvicorn.side_effect = KeyboardInterrupt()
                    server.run(host="localhost", port=8000)
            except KeyboardInterrupt:
                pass

            # Banner should be printed in debug mode
            mock_print_config.assert_called()

    def test_run_with_proxy_manager_startup(self):
        """Test run() with proxy manager startup (lines 788-799)."""
        server = ChukMCPServer()

        mock_proxy = MagicMock()
        mock_proxy.start_servers = AsyncMock()
        mock_proxy.get_stats.return_value = {"servers": 1, "tools": 5}
        server.proxy_manager = mock_proxy

        with (
            patch("chuk_mcp_server.core.create_server"),
            patch("chuk_mcp_server.core.logging.basicConfig"),
            patch("asyncio.run") as mock_asyncio_run,
        ):
            try:
                with patch("uvicorn.run") as mock_uvicorn:
                    mock_uvicorn.side_effect = KeyboardInterrupt()
                    server.run()
            except KeyboardInterrupt:
                pass

            # Proxy manager should be started
            mock_asyncio_run.assert_called()

    def test_run_with_module_loader_startup(self):
        """Test run() with module loader startup (lines 803-812)."""
        server = ChukMCPServer()

        mock_loader = MagicMock()
        mock_loader.load_modules.return_value = {"math": ["add", "sub"]}
        mock_loader.get_module_info.return_value = {"total_modules": 1, "total_tools": 2}
        server.module_loader = mock_loader

        with (
            patch("chuk_mcp_server.core.create_server"),
            patch("chuk_mcp_server.core.logging.basicConfig"),
        ):
            try:
                with patch("uvicorn.run") as mock_uvicorn:
                    mock_uvicorn.side_effect = KeyboardInterrupt()
                    server.run()
            except KeyboardInterrupt:
                pass

            # Module loader should load modules
            mock_loader.load_modules.assert_called_once()
            mock_loader.get_module_info.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
