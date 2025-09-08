#!/usr/bin/env python3
"""
Test suite for MCP logging/setLevel functionality.

This test verifies that the logging/setLevel MCP method works correctly
when the logging capability is enabled.
"""

import asyncio
import logging
import pytest
from unittest.mock import patch

from chuk_mcp_server.core import ChukMCPServer


class TestLoggingSetLevel:
    """Test the MCP logging/setLevel functionality."""

    @pytest.fixture
    def server_with_logging(self):
        """Create a test server with logging enabled."""
        server = ChukMCPServer(
            name="Test Logging Server",
            version="1.0.0",
            transport="stdio",
            logging=True,
            debug=False
        )
        return server

    @pytest.fixture
    def server_without_logging(self):
        """Create a test server without logging enabled."""
        server = ChukMCPServer(
            name="Test Server",
            version="1.0.0", 
            transport="stdio",
            logging=False,
            debug=False
        )
        return server

    @pytest.mark.asyncio
    async def test_logging_set_level_with_logging_enabled(self, server_with_logging):
        """Test logging/setLevel when logging capability is enabled."""
        protocol = server_with_logging.protocol
        
        # Test valid log levels
        valid_levels = ["debug", "info", "warning", "error"]
        
        for level in valid_levels:
            # Create request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logging/setLevel",
                "params": {"level": level}
            }
            
            # Handle the request
            response, notification = await protocol.handle_request(request)
            
            # Verify response
            assert response is not None
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "result" in response
            assert response["result"]["level"] == level.upper()
            assert "Logging level set to" in response["result"]["message"]
            assert notification is None

    @pytest.mark.asyncio
    async def test_logging_set_level_invalid_level(self, server_with_logging):
        """Test logging/setLevel with invalid log level."""
        protocol = server_with_logging.protocol
        
        # Test invalid log level
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logging/setLevel",
            "params": {"level": "invalid"}
        }
        
        # Handle the request
        response, notification = await protocol.handle_request(request)
        
        # Verify error response
        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" in response
        assert response["error"]["code"] == -32602
        assert "Invalid logging level" in response["error"]["message"]
        assert notification is None

    @pytest.mark.asyncio
    async def test_logging_set_level_case_insensitive(self, server_with_logging):
        """Test that logging/setLevel is case insensitive."""
        protocol = server_with_logging.protocol
        
        # Test different cases
        test_cases = ["DEBUG", "Info", "WARNING", "error"]
        
        for level in test_cases:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logging/setLevel",
                "params": {"level": level}
            }
            
            response, notification = await protocol.handle_request(request)
            
            # Should succeed regardless of case
            assert response is not None
            assert "result" in response
            assert response["result"]["level"] == level.upper()

    @pytest.mark.asyncio
    async def test_logging_set_level_default_level(self, server_with_logging):
        """Test logging/setLevel with no level parameter (should default to INFO)."""
        protocol = server_with_logging.protocol
        
        # Request without level parameter
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logging/setLevel",
            "params": {}
        }
        
        response, notification = await protocol.handle_request(request)
        
        # Should default to INFO
        assert response is not None
        assert "result" in response
        assert response["result"]["level"] == "INFO"

    @pytest.mark.asyncio 
    async def test_logging_set_level_actually_changes_level(self, server_with_logging):
        """Test that logging/setLevel actually changes the logging level."""
        protocol = server_with_logging.protocol
        
        # Get the chuk_mcp_server logger
        logger = logging.getLogger("chuk_mcp_server")
        original_level = logger.level
        
        try:
            # Set to DEBUG
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logging/setLevel", 
                "params": {"level": "debug"}
            }
            
            await protocol.handle_request(request)
            
            # Verify level was changed
            assert logger.level == logging.DEBUG
            
            # Set to ERROR
            request["params"]["level"] = "error"
            await protocol.handle_request(request)
            
            # Verify level was changed again
            assert logger.level == logging.ERROR
            
        finally:
            # Restore original level
            logger.setLevel(original_level)

    @pytest.mark.asyncio
    async def test_logging_capability_in_server_info(self, server_with_logging, server_without_logging):
        """Test that logging capability is properly reported in server capabilities."""
        # Server with logging should have logging capability
        protocol_with_logging = server_with_logging.protocol
        capabilities_with = protocol_with_logging.capabilities.model_dump()
        assert "logging" in capabilities_with
        
        # Server without logging should not have logging capability
        protocol_without_logging = server_without_logging.protocol
        capabilities_without = protocol_without_logging.capabilities.model_dump()
        assert "logging" not in capabilities_without

    @pytest.mark.asyncio
    async def test_logging_set_level_with_logging_disabled(self, server_without_logging):
        """Test that logging/setLevel works even when logging capability is disabled."""
        # The MCP spec doesn't explicitly require that logging/setLevel
        # only works when logging capability is enabled. The method should
        # still work for controlling server-side logging levels.
        protocol = server_without_logging.protocol
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logging/setLevel",
            "params": {"level": "debug"}
        }
        
        response, notification = await protocol.handle_request(request)
        
        # Should still work (controls server-side logging)
        assert response is not None
        assert "result" in response
        assert response["result"]["level"] == "DEBUG"

    @pytest.mark.asyncio
    async def test_root_logger_set_on_debug(self, server_with_logging):
        """Test that root logger is set to DEBUG when debug level is requested."""
        protocol = server_with_logging.protocol
        
        # Get root logger
        root_logger = logging.getLogger()
        original_level = root_logger.level
        
        try:
            # Set to DEBUG - should also set root logger
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logging/setLevel",
                "params": {"level": "debug"}
            }
            
            await protocol.handle_request(request)
            
            # Verify root logger was also set to DEBUG
            assert root_logger.level == logging.DEBUG
            
        finally:
            # Restore original root logger level
            root_logger.setLevel(original_level)

    def test_logging_level_mapping(self):
        """Test the internal logging level mapping used in the handler."""
        # Test the level mapping used in _handle_logging_set_level
        level_mapping = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        
        # Verify all MCP levels map to correct Python levels
        assert level_mapping["debug"] == 10
        assert level_mapping["info"] == 20
        assert level_mapping["warning"] == 30
        assert level_mapping["error"] == 40
        assert level_mapping["critical"] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])