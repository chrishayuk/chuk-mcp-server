#!/usr/bin/env python3
# src/chuk_mcp_server/types/tools.py
"""
Tools - ToolHandler with orjson optimization and schema caching

This module provides the ToolHandler class with aggressive performance optimizations
including schema caching, orjson serialization, and type-safe parameter validation.
"""

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import orjson

from .base import MCPTool, MCPToolInputSchema, ValidationError
from .errors import ParameterValidationError, ToolExecutionError
from .parameters import ToolParameter

# ============================================================================
# ToolHandler with Maximum Performance Optimization
# ============================================================================


@dataclass
class ToolHandler:
    """Framework tool handler with orjson optimization and schema caching for world-class performance."""

    mcp_tool: MCPTool  # The actual MCP tool
    handler: Callable[..., Any]
    parameters: list[ToolParameter]
    _cached_mcp_format: dict[str, Any] | None = None  # Cache the MCP format dict
    _cached_mcp_bytes: bytes | None = None  # 🚀 Cache orjson-serialized bytes
    requires_auth: bool = False  # Whether this tool requires OAuth authorization
    auth_scopes: list[str] | None = None  # Optional list of required scopes

    @classmethod
    def from_function(
        cls, func: Callable[..., Any], name: str | None = None, description: str | None = None
    ) -> "ToolHandler":
        """Create ToolHandler from a function with orjson optimization."""
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Execute {tool_name}"

        # Check for authorization metadata (set by @requires_auth decorator)
        requires_auth = getattr(func, "_requires_auth", False)
        auth_scopes = getattr(func, "_auth_scopes", None)

        # Extract parameters from function signature
        sig = inspect.signature(func)
        parameters: list[ToolParameter] = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":  # Skip self parameter for methods
                continue

            # Skip internal OAuth parameter (injected by protocol handler)
            if param_name == "_external_access_token":
                continue

            tool_param = ToolParameter.from_annotation(
                name=param_name,
                annotation=param.annotation if param.annotation != inspect.Parameter.empty else str,
                default=param.default,
            )
            parameters.append(tool_param)

        # Build JSON schema for the MCP tool using the proper schema type
        properties = {}
        required = []

        for tool_param in parameters:
            properties[tool_param.name] = tool_param.to_json_schema()
            if tool_param.required:
                required.append(tool_param.name)

        # Create the proper MCP ToolInputSchema
        input_schema = MCPToolInputSchema(type="object", properties=properties, required=required if required else None)

        # Create the MCP tool with the proper schema
        mcp_tool = MCPTool(
            name=tool_name, description=tool_description, inputSchema=input_schema.model_dump(exclude_none=True)
        )

        # Create instance and pre-cache both dict and orjson formats
        instance = cls(
            mcp_tool=mcp_tool,
            handler=func,
            parameters=parameters,
            _cached_mcp_format=None,  # Will be computed immediately
            _cached_mcp_bytes=None,  # Will be computed immediately
            requires_auth=requires_auth,
            auth_scopes=auth_scopes,
        )

        # Pre-compute and cache both formats during creation for maximum performance
        instance._ensure_cached_formats()

        return instance

    def _ensure_cached_formats(self) -> None:
        """Ensure both dict and orjson formats are cached."""
        if self._cached_mcp_format is None:
            # Cache the expensive schema generation once
            self._cached_mcp_format = self.mcp_tool.model_dump(exclude_none=True)

        if self._cached_mcp_bytes is None:
            # Pre-serialize with orjson for maximum speed
            self._cached_mcp_bytes = orjson.dumps(self._cached_mcp_format)

    @property
    def name(self) -> str:
        """Get the tool name."""
        return self.mcp_tool.name  # type: ignore[no-any-return]

    @property
    def description(self) -> str | None:
        """Get the tool description."""
        return self.mcp_tool.description  # type: ignore[no-any-return]

    def to_mcp_format(self) -> dict[str, Any]:
        """Convert to MCP tool format using cached version for maximum performance."""
        if self._cached_mcp_format is None:
            self._ensure_cached_formats()
        return self._cached_mcp_format.copy()  # type: ignore[union-attr] # Return copy to prevent mutation

    def to_mcp_bytes(self) -> bytes:
        """🚀 Get orjson-serialized MCP format bytes for ultimate performance."""
        if self._cached_mcp_bytes is None:
            self._ensure_cached_formats()
        return self._cached_mcp_bytes  # type: ignore[return-value]

    def invalidate_cache(self) -> None:
        """Invalidate all cached formats (if schema changes at runtime)."""
        self._cached_mcp_format = None
        self._cached_mcp_bytes = None

    def _validate_and_convert_arguments(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validate and convert arguments with specific error types."""
        validated_args = {}

        for param in self.parameters:
            value = arguments.get(param.name)

            if value is None:
                if param.required:
                    raise ParameterValidationError(param.name, param.type, None)
                value = param.default

            # Skip validation if value is still None after default assignment
            if value is not None:
                try:
                    validated_value = self._convert_type(value, param)
                    validated_args[param.name] = validated_value
                except (ValueError, TypeError) as e:
                    raise ParameterValidationError(param.name, param.type, value) from e

        return validated_args

    def _convert_type(self, value: Any, param: ToolParameter) -> Any:
        """Convert value to the expected parameter type with orjson optimization."""
        # If value is already the correct type, return as-is
        if param.type == "integer":
            if isinstance(value, int):
                return value
            elif isinstance(value, float):
                # Handle float-to-int conversion (e.g., 5.0 -> 5)
                if value.is_integer():
                    return int(value)
                else:
                    raise ValueError(f"Cannot convert float {value} to integer without precision loss")
            elif isinstance(value, str):
                # Handle string-to-int conversion
                try:
                    # First try direct int conversion
                    return int(value)
                except ValueError:
                    try:
                        # Try float first then int (handles "5.0" strings)
                        float_val = float(value)
                        if float_val.is_integer():
                            return int(float_val)
                        else:
                            raise ValueError(f"Cannot convert string '{value}' to integer without precision loss")
                    except ValueError as exc:
                        raise ValueError(f"Cannot convert string '{value}' to integer") from exc
            else:
                # Try direct int conversion for other types
                return int(value)

        elif param.type == "number":
            if isinstance(value, int | float):
                return float(value)
            elif isinstance(value, str):
                try:
                    return float(value)
                except ValueError as exc:
                    raise ValueError(f"Cannot convert string '{value}' to number") from exc
            else:
                return float(value)

        elif param.type == "boolean":
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                # Handle string boolean conversion with enhanced edge case handling
                lower_val = value.lower().strip()
                # Handle empty string and null string - use parameter default or False
                if lower_val == "" or lower_val == "null":
                    # For empty/null strings, use the parameter default if available, otherwise False
                    return param.default if param.default is not None else False
                elif lower_val in ("true", "1", "yes", "on", "t", "y"):
                    return True
                elif lower_val in ("false", "0", "no", "off", "f", "n"):
                    return False
                else:
                    # For unrecognized strings, use parameter default if available, otherwise False
                    # This handles cases where UI allows free-form text input for boolean params
                    return param.default if param.default is not None else False
            elif isinstance(value, int | float):
                # Handle numeric boolean conversion
                return bool(value)
            elif value is None:
                # Handle None explicitly - use parameter default or False
                return param.default if param.default is not None else False
            else:
                # Try converting to bool as last resort
                try:
                    return bool(value)
                except Exception as e:
                    raise ValueError(f"Cannot convert {type(value).__name__} '{value}' to boolean") from e

        elif param.type == "string":
            if isinstance(value, str):
                return value
            else:
                # Convert other types to string
                return str(value)

        elif param.type == "array":
            if isinstance(value, list):
                return value
            elif isinstance(value, tuple | set):
                return list(value)
            elif isinstance(value, str):
                # 🚀 Use orjson for 2x faster JSON parsing
                try:
                    parsed = orjson.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                    else:
                        raise ValueError(f"String '{value}' does not represent an array")
                except orjson.JSONDecodeError as exc:
                    raise ValueError(f"Cannot convert string '{value}' to array") from exc
            else:
                raise ValueError(f"Cannot convert {type(value).__name__} to array")

        elif param.type == "object":
            if isinstance(value, dict):
                return value
            elif isinstance(value, str):
                # 🚀 Use orjson for 2x faster JSON parsing
                try:
                    parsed = orjson.loads(value)
                    if isinstance(parsed, dict):
                        return parsed
                    else:
                        raise ValueError(f"String '{value}' does not represent an object")
                except orjson.JSONDecodeError as exc:
                    raise ValueError(f"Cannot convert string '{value}' to object") from exc
            else:
                raise ValueError(f"Cannot convert {type(value).__name__} to object")

        # Check enum values if specified
        if param.enum and value not in param.enum:
            raise ValueError(f"Value '{value}' must be one of {param.enum}")

        return value

    async def execute(self, arguments: dict[str, Any]) -> Any:
        """Execute the tool with enhanced error handling."""
        try:
            validated_args = self._validate_and_convert_arguments(arguments)

            if inspect.iscoroutinefunction(self.handler):
                return await self.handler(**validated_args)
            else:
                return self.handler(**validated_args)

        except (ParameterValidationError, ValidationError):
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            # Wrap other errors in ToolExecutionError
            raise ToolExecutionError(self.name, e) from e


# ============================================================================
# Tool Creation Utilities
# ============================================================================


def create_tool_from_function(
    func: Callable[..., Any], name: str | None = None, description: str | None = None
) -> ToolHandler:
    """Create a ToolHandler from a function - convenience function."""
    return ToolHandler.from_function(func, name=name, description=description)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ToolHandler",
    "create_tool_from_function",
]
