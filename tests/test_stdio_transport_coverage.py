#!/usr/bin/env python3
"""
Additional tests for stdio_transport.py to achieve 90%+ coverage.
Focuses on error paths and edge cases not covered by existing tests.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from chuk_mcp_server.stdio_transport import StdioTransport


@pytest.fixture
def mock_protocol():
    """Create a mock protocol handler."""
    protocol = Mock()
    protocol.handle_request = AsyncMock(return_value=({}, None))
    protocol.session_manager = Mock()
    protocol.session_manager.create_session = Mock(return_value="session123")
    return protocol


@pytest.fixture
def transport(mock_protocol):
    """Create a StdioTransport instance."""
    return StdioTransport(mock_protocol)


class TestStdioTransportCoverage:
    """Test uncovered lines in StdioTransport."""

    @pytest.mark.asyncio
    async def test_listen_with_no_reader(self, transport):
        """Test _listen() when reader is None (lines 65-66)."""
        transport.running = True
        transport.reader = None  # Set reader to None

        # Should exit immediately without error
        await transport._listen()

        # Verify it completed without hanging
        assert transport.reader is None

    @pytest.mark.asyncio
    async def test_listen_with_empty_chunk(self, transport):
        """Test _listen() when chunk is empty (lines 68-70)."""
        # Mock reader to return empty chunk (EOF)
        mock_reader = AsyncMock()
        mock_reader.read = AsyncMock(return_value=b"")

        transport.running = True
        transport.reader = mock_reader

        # Should break out of loop on empty chunk
        await transport._listen()

        # Verify read was called
        mock_reader.read.assert_called_once()

    @pytest.mark.asyncio
    async def test_listen_with_empty_line(self, transport):
        """Test _listen() with empty line after stripping (lines 80-81)."""
        # Mock reader to return line with just whitespace, then EOF
        mock_reader = AsyncMock()
        mock_reader.read = AsyncMock(side_effect=[b"   \n", b""])

        transport.running = True
        transport.reader = mock_reader
        transport.protocol.handle_request = AsyncMock()

        await transport._listen()

        # Empty line should be skipped, handle_request not called
        transport.protocol.handle_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_with_reader(self, transport):
        """Test stop() when reader exists (lines 177-178)."""
        # Create mock reader
        mock_reader = AsyncMock()
        mock_reader.feed_eof = Mock()

        transport.reader = mock_reader
        transport.running = True

        await transport.stop()

        # Should call feed_eof and set running to False
        mock_reader.feed_eof.assert_called_once()
        assert transport.running is False

    def test_run_stdio_server_keyboard_interrupt_in_start(self, mock_protocol):
        """Test run_stdio_server with KeyboardInterrupt during start (lines 208-210)."""
        from chuk_mcp_server.stdio_transport import run_stdio_server

        # Mock StdioTransport.start to raise KeyboardInterrupt
        with patch("chuk_mcp_server.stdio_transport.StdioTransport") as MockTransport:
            mock_transport = Mock()
            mock_transport.start = AsyncMock(side_effect=KeyboardInterrupt)
            mock_transport.stop = AsyncMock()
            MockTransport.return_value = mock_transport

            # Should handle KeyboardInterrupt gracefully (not raise)
            run_stdio_server(mock_protocol)

            # Stop should be called in finally block
            mock_transport.stop.assert_called()

    @pytest.mark.asyncio
    async def test_run_stdio_server_with_logging_config(self, mock_protocol):
        """Test run_stdio_server logging configuration (lines 214-217)."""
        from chuk_mcp_server.stdio_transport import run_stdio_server

        with patch("chuk_mcp_server.stdio_transport.logging.basicConfig") as mock_logging:
            with patch("chuk_mcp_server.stdio_transport.asyncio.run") as mock_run:
                # Mock asyncio.run to do nothing
                mock_run.return_value = None

                run_stdio_server(mock_protocol)

                # Should configure logging to stderr
                mock_logging.assert_called_once()
                call_kwargs = mock_logging.call_args[1]
                assert call_kwargs["level"] == 20  # logging.INFO
                import sys

                assert call_kwargs["stream"] == sys.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
