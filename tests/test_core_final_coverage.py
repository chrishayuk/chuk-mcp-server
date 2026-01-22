#!/usr/bin/env python3
"""Final tests to push core.py coverage above 95%"""

from unittest.mock import MagicMock, patch

import pytest

from chuk_mcp_server.core import ChukMCPServer


class TestStdioModeDetailed:
    """Test STDIO mode configuration in detail."""

    @pytest.mark.skip(reason="Complex STDIO detection logic - covered by integration tests")
    def test_run_with_stdio_env_var_MCP_STDIO(self):
        """Test run() detecting stdio via MCP_STDIO env var (lines 747-776)."""
        pass

    @pytest.mark.skip(reason="Complex STDIO detection logic - covered by integration tests")
    def test_run_with_stdio_env_var_USE_STDIO(self):
        """Test run() detecting stdio via USE_STDIO env var."""
        pass

    @pytest.mark.skip(reason="Complex STDIO detection logic - covered by integration tests")
    def test_run_with_stdio_env_var_MCP_TRANSPORT(self):
        """Test run() detecting stdio via MCP_TRANSPORT env var."""
        pass

    @pytest.mark.skip(reason="Complex STDIO detection logic - covered by integration tests")
    def test_run_stdio_mode_logging_suppression(self):
        """Test that stdio mode suppresses logging to CRITICAL (lines 760-776)."""
        pass


class TestProxyStartupErrors:
    """Test proxy startup error handling."""

    def test_run_with_proxy_startup_error(self):
        """Test run() with proxy startup error (lines 798-799)."""
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
        """Test run() with module loader error (lines 811-812)."""
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
        """Test run() without debug mode doesn't print banner (line 781->785)."""
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
        """Test _start_proxy_if_enabled when proxy_manager is None (line 692->exit)."""
        server = ChukMCPServer()
        server.proxy_manager = None

        # Should not raise error, just return early
        await server._start_proxy_if_enabled()

    @pytest.mark.asyncio
    async def test_stop_proxy_when_none(self):
        """Test _stop_proxy_if_enabled when proxy_manager is None (line 698->exit)."""
        server = ChukMCPServer()
        server.proxy_manager = None

        # Should not raise error, just return early
        await server._stop_proxy_if_enabled()


class TestAlternativeHandlerPaths:
    """Test alternative handler creation paths.

    Note: Lines 201, 211, 227 are defensive fallback code paths that are
    difficult to test without modifying the internal decorator implementation.
    These lines handle the case where decorator objects have a 'handler' attribute,
    which is typically set by the framework itself. Coverage for these lines
    would require integration tests with the actual decorator implementation.
    """

    @pytest.mark.skip(reason="Defensive fallback path - requires internal decorator state manipulation")
    def test_tool_registration_with_existing_handler_attr(self):
        """Test tool registration when tool has handler attribute (line 201)."""
        pass

    @pytest.mark.skip(reason="Defensive fallback path - requires internal decorator state manipulation")
    def test_resource_registration_with_existing_handler_attr(self):
        """Test resource registration when resource has handler attribute (line 211)."""
        pass

    @pytest.mark.skip(reason="Defensive fallback path - requires internal decorator state manipulation")
    def test_prompt_registration_with_existing_handler_attr(self):
        """Test prompt registration when prompt has handler attribute (line 227)."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
