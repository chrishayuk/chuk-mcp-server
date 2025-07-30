#!/usr/bin/env python3
# src/chuk_mcp_server/types/errors.py
"""
Errors - Custom error classes for ChukMCPServer

This module provides specialized error classes with enhanced error reporting
and debugging information for tool execution and parameter validation.
"""

from typing import Any, Dict
from .base import MCPError, ValidationError

class ParameterValidationError(ValidationError):
    """Specific error for parameter validation."""
    def __init__(self, parameter: str, expected_type: str, received: Any):
        message = f"Invalid parameter '{parameter}': expected {expected_type}, got {type(received).__name__}"
        data = {
            "parameter": parameter, 
            "expected": expected_type, 
            "received": type(received).__name__
        }
        super().__init__(message, data=data)

class ToolExecutionError(MCPError):
    """Error during tool execution."""
    def __init__(self, tool_name: str, error: Exception):
        message = f"Tool '{tool_name}' execution failed: {str(error)}"
        data = {
            "tool": tool_name, 
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        super().__init__(message, data=data)

__all__ = ["ParameterValidationError", "ToolExecutionError"]