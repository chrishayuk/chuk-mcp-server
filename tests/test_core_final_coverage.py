#!/usr/bin/env python3
"""Final tests to push core.py coverage above 95%"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chuk_mcp_server.core import ChukMCPServer


class TestStdioModeDetailed:
    """Test STDIO mode configuration in detail."""

    def test_run_with_stdio_env_var_MCP_STDIO(self):
        """Test run() detecting stdio via MCP_STDIO env var."""
        server = ChukMCPServer()

        with (
            patch("chuk_mcp_server.core.logging.basicConfig"),
            patch.object(
                server.smart_config.environment_detector,
                "get_env_var",
                side_effect=lambda key: "1" if key == "MCP_STDIO" else None,
            ),
            patch("chuk_mcp_server.stdio_transport.run_stdio_server") as mock_stdio,
        ):
            server.run()
            mock_stdio.assert_called_once_with(server.protocol)

    def test_run_with_stdio_env_var_USE_STDIO(self):
        """Test run() detecting stdio via USE_STDIO env var."""
        server = ChukMCPServer()

        with (
            patch("chuk_mcp_server.core.logging.basicConfig"),
            patch.object(
                server.smart_config.environment_detector,
                "get_env_var",
                side_effect=lambda key: "1" if key == "USE_STDIO" else None,
            ),
            patch("chuk_mcp_server.stdio_transport.run_stdio_server") as mock_stdio,
        ):
            server.run()
            mock_stdio.assert_called_once_with(server.protocol)

    def test_run_with_stdio_env_var_MCP_TRANSPORT(self):
        """Test run() detecting stdio via MCP_TRANSPORT=stdio env var."""
        server = ChukMCPServer()

        with (
            patch("chuk_mcp_server.core.logging.basicConfig"),
            patch.object(
                server.smart_config.environment_detector,
                "get_env_var",
                side_effect=lambda key: "stdio" if key == "MCP_TRANSPORT" else None,
            ),
            patch("chuk_mcp_server.stdio_transport.run_stdio_server") as mock_stdio,
        ):
            server.run()
            mock_stdio.assert_called_once_with(server.protocol)

    def test_run_stdio_mode_logging_suppression(self):
        """Test that stdio mode suppresses logging to CRITICAL."""
        server = ChukMCPServer()
        import logging

        with (
            patch("chuk_mcp_server.core.logging.basicConfig") as mock_basic,
            patch.object(
                server.smart_config.environment_detector,
                "get_env_var",
                side_effect=lambda key: "1" if key == "MCP_STDIO" else None,
            ),
            patch("chuk_mcp_server.stdio_transport.run_stdio_server"),
        ):
            server.run()

            # Second basicConfig call should set CRITICAL for stdio mode
            calls = mock_basic.call_args_list
            assert any(call.kwargs.get("level") == logging.CRITICAL for call in calls)


class TestProxyStartupErrors:
    """Test proxy startup error handling."""

    def test_run_with_proxy_startup_error(self):
        """Test run() with proxy startup error."""
        server = ChukMCPServer()

        mock_proxy = MagicMock()
        server.proxy_manager = mock_proxy

        with (
            patch("chuk_mcp_server.core.create_server"),
            patch("chuk_mcp_server.core.logging.basicConfig"),
            patch("asyncio.run", side_effect=RuntimeError("Proxy connection failed")),
            patch("chuk_mcp_server.core.logger") as mock_logger,
        ):
            try:
                with patch("uvicorn.run") as mock_uvicorn:
                    mock_uvicorn.side_effect = KeyboardInterrupt()
                    server.run()
            except KeyboardInterrupt:
                pass

            # Should log the error
            assert any("Failed to start proxy manager" in str(call) for call in mock_logger.error.call_args_list)


class TestModuleLoaderErrors:
    """Test module loader error handling."""

    def test_run_with_module_loader_error(self):
        """Test run() with module loader error."""
        server = ChukMCPServer()

        mock_loader = MagicMock()
        mock_loader.load_modules.side_effect = ImportError("Module not found")
        server.module_loader = mock_loader

        with (
            patch("chuk_mcp_server.core.create_server"),
            patch("chuk_mcp_server.core.logging.basicConfig"),
            patch("chuk_mcp_server.core.logger") as mock_logger,
        ):
            try:
                with patch("uvicorn.run") as mock_uvicorn:
                    mock_uvicorn.side_effect = KeyboardInterrupt()
                    server.run()
            except KeyboardInterrupt:
                pass

            # Should log the error
            assert any("Failed to load tool modules" in str(call) for call in mock_logger.error.call_args_list)


class TestDebugModeBranches:
    """Test debug mode specific branches."""

    def test_run_without_debug_no_banner(self):
        """Test run() without debug mode doesn't print banner."""
        server = ChukMCPServer(debug=False)

        with (
            patch("chuk_mcp_server.core.create_server"),
            patch("chuk_mcp_server.core.logging.basicConfig"),
            patch.object(server, "_print_smart_config") as mock_print_config,
        ):
            try:
                with patch("uvicorn.run") as mock_uvicorn:
                    mock_uvicorn.side_effect = KeyboardInterrupt()
                    server.run()
            except KeyboardInterrupt:
                pass

            # Banner should NOT be printed when debug is False
            mock_print_config.assert_not_called()


class TestProxyManagerNoneBranches:
    """Test branches when proxy_manager is None."""

    @pytest.mark.asyncio
    async def test_start_proxy_when_none(self):
        """Test _start_proxy_if_enabled when proxy_manager is None."""
        server = ChukMCPServer()
        server.proxy_manager = None

        # Should not raise error, just return early
        await server._start_proxy_if_enabled()

    @pytest.mark.asyncio
    async def test_stop_proxy_when_none(self):
        """Test _stop_proxy_if_enabled when proxy_manager is None."""
        server = ChukMCPServer()
        server.proxy_manager = None

        # Should not raise error, just return early
        await server._stop_proxy_if_enabled()


class TestShutdownAll:
    """Test the _shutdown_all method."""

    @pytest.mark.asyncio
    async def test_shutdown_all_with_proxy(self):
        """Test _shutdown_all shuts down protocol and proxy."""
        server = ChukMCPServer()

        mock_proxy = MagicMock()
        mock_proxy.stop_servers = AsyncMock()
        server.proxy_manager = mock_proxy

        with patch.object(server.protocol, "shutdown", new_callable=AsyncMock) as mock_shutdown:
            await server._shutdown_all()

            mock_shutdown.assert_awaited_once()
            mock_proxy.stop_servers.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_shutdown_all_without_proxy(self):
        """Test _shutdown_all without proxy manager."""
        server = ChukMCPServer()
        server.proxy_manager = None

        with patch.object(server.protocol, "shutdown", new_callable=AsyncMock) as mock_shutdown:
            await server._shutdown_all()

            mock_shutdown.assert_awaited_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
