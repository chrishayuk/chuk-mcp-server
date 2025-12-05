#!/usr/bin/env python3
# src/chuk_mcp_server/types/parameters.py
"""
Parameters - Tool parameter definitions and JSON Schema generation

This module handles tool parameter type inference, JSON Schema generation,
and orjson optimization for maximum performance in schema operations.
"""

import inspect
from dataclasses import dataclass
from types import UnionType
from typing import Any, Union

import orjson

# ============================================================================
# Pre-computed orjson Schema Fragments for Maximum Performance
# ============================================================================

# Pre-serialize common JSON schema fragments with orjson for maximum speed
_SCHEMA_FRAGMENTS = {
    "string": orjson.dumps({"type": "string"}),
    "integer": orjson.dumps({"type": "integer"}),
    "number": orjson.dumps({"type": "number"}),
    "boolean": orjson.dumps({"type": "boolean"}),
    "array": orjson.dumps({"type": "array"}),
    "object": orjson.dumps({"type": "object"}),
}

# Pre-computed base schemas for common parameter patterns
_BASE_SCHEMAS = {
    ("string", True, None): orjson.dumps({"type": "string"}),
    ("string", False, None): orjson.dumps({"type": "string"}),
    ("integer", True, None): orjson.dumps({"type": "integer"}),
    ("integer", False, None): orjson.dumps({"type": "integer"}),
    ("number", True, None): orjson.dumps({"type": "number"}),
    ("number", False, None): orjson.dumps({"type": "number"}),
    ("boolean", True, None): orjson.dumps({"type": "boolean"}),
    ("boolean", False, None): orjson.dumps({"type": "boolean"}),
}

# ============================================================================
# Tool Parameter with orjson Optimization
# ============================================================================


@dataclass
class ToolParameter:
    """Tool parameter definition with orjson-optimized schema generation."""

    name: str
    type: str
    description: str | None = None
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None
    items_type: str | None = None  # For array types: the type of items in the array
    _cached_schema: bytes | None = None  # 🚀 Cache orjson-serialized schema

    @classmethod
    def from_annotation(cls, name: str, annotation: Any, default: Any = inspect.Parameter.empty) -> "ToolParameter":
        """Create parameter from function annotation with modern typing support."""
        import typing
        from typing import Union  # Add explicit imports

        # Enhanced type mapping for modern Python
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        param_type = "string"  # default
        enum_values = None
        items_type = None  # Track array item type

        # First check for direct basic types (most common case)
        if annotation in type_map:
            param_type = type_map[annotation]
        # Handle modern typing features
        elif hasattr(typing, "get_origin") and hasattr(typing, "get_args"):
            origin = typing.get_origin(annotation)
            args = typing.get_args(annotation)

            # Handle both typing.Union and types.UnionType (Python 3.10+ X | Y syntax)
            if origin is Union or (UnionType is not None and origin is UnionType):
                # Handle Optional[T] and Union types (including T | None syntax)
                if len(args) == 2 and type(None) in args:
                    # Optional[T] case
                    non_none_type = next(arg for arg in args if arg is not type(None))
                    param_type = type_map.get(non_none_type, "string")
                else:
                    # Multiple union types - default to string
                    param_type = "string"

            # Handle Literal types for enums
            elif hasattr(typing, "Literal") and origin is typing.Literal:
                param_type = "string"
                enum_values = list(args)

            # Handle generic containers
            elif origin in (list, list):
                param_type = "array"
                # Extract item type from List[T] or list[T]
                if args:
                    items_type = type_map.get(args[0], "string")
            elif origin in (dict, dict):
                param_type = "object"
            else:
                param_type = type_map.get(origin, "string")

        # Fallback for older typing or direct types (Python 3.7-3.8 compatibility)
        elif hasattr(annotation, "__origin__"):  # pragma: no cover - Python 3.7-3.8 compatibility
            origin = annotation.__origin__
            if origin is Union:
                args = annotation.__args__
                if len(args) == 2 and type(None) in args:
                    non_none_type = next(arg for arg in args if arg is not type(None))
                    param_type = type_map.get(non_none_type, "string")
                else:
                    param_type = "string"
            elif origin in (list, list):
                param_type = "array"
                # Extract item type from List[T] or list[T]
                if hasattr(annotation, "__args__") and annotation.__args__:
                    items_type = type_map.get(annotation.__args__[0], "string")
            elif origin in (dict, dict):
                param_type = "object"
            else:
                param_type = type_map.get(origin, "string")
        else:
            # Handle direct type annotations (int, str, bool, etc.)
            param_type = type_map.get(annotation, "string")

        # Check if it has a default value
        required = default is inspect.Parameter.empty
        actual_default = None if default is inspect.Parameter.empty else default

        return cls(
            name=name,
            type=param_type,
            description=None,
            required=required,
            default=actual_default,
            enum=enum_values,
            items_type=items_type,
            _cached_schema=None,  # Will be computed on first access
        )

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format with orjson optimization."""
        # Check if we can use a pre-computed base schema
        cache_key = (self.type, self.required, self.default)
        if cache_key in _BASE_SCHEMAS and not self.description and not self.enum and not self.items_type:
            # Return pre-computed schema for maximum speed
            return orjson.loads(_BASE_SCHEMAS[cache_key])  # type: ignore[no-any-return]

        # Build custom schema
        schema: dict[str, Any] = {"type": self.type}

        # Add items field for array types
        if self.type == "array" and self.items_type:
            schema["items"] = {"type": self.items_type}

        if self.description:
            schema["description"] = self.description
        if self.enum:
            schema["enum"] = self.enum
        if self.default is not None:
            schema["default"] = self.default

        return schema

    def to_json_schema_bytes(self) -> bytes:
        """Get orjson-serialized schema bytes for maximum performance."""
        if self._cached_schema is None:
            schema = self.to_json_schema()
            self._cached_schema = orjson.dumps(schema)
        return self._cached_schema

    def invalidate_cache(self) -> None:
        """Invalidate the cached schema."""
        self._cached_schema = None


# ============================================================================
# Schema Generation Utilities
# ============================================================================


def build_input_schema(parameters: list[ToolParameter]) -> dict[str, Any]:
    """Build JSON Schema input schema from parameters."""
    properties = {}
    required = []

    for param in parameters:
        properties[param.name] = param.to_json_schema()
        if param.required:
            required.append(param.name)

    return {"type": "object", "properties": properties, "required": required if required else None}


def build_input_schema_bytes(parameters: list[ToolParameter]) -> bytes:
    """Build orjson-serialized input schema for maximum performance."""
    schema = build_input_schema(parameters)
    return orjson.dumps(schema)


# ============================================================================
# Type Inference Utilities
# ============================================================================


def infer_type_from_annotation(annotation: Any) -> str:
    """Infer JSON Schema type from Python type annotation."""
    import typing

    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    # First check for direct basic types (most common case)
    if annotation in type_map:
        return type_map[annotation]

    # Handle modern typing features
    if hasattr(typing, "get_origin") and hasattr(typing, "get_args"):
        origin = typing.get_origin(annotation)

        # Handle both typing.Union and types.UnionType (Python 3.10+ X | Y syntax)
        if origin is Union or (UnionType is not None and origin is UnionType):
            args = typing.get_args(annotation)
            if len(args) == 2 and type(None) in args:
                # Optional[T] case (Union[T, None] or T | None)
                non_none_type = next(arg for arg in args if arg is not type(None))
                return type_map.get(non_none_type, "string")
            else:
                # Multiple union types - default to string
                return "string"

        # Handle generic containers
        elif origin in (list, list):
            return "array"
        elif origin in (dict, dict):
            return "object"
        else:
            return type_map.get(origin, "string")

    # Fallback for older typing or direct types (Python 3.7-3.8 compatibility)
    elif hasattr(annotation, "__origin__"):  # pragma: no cover - Python 3.7-3.8 compatibility
        origin = annotation.__origin__
        if origin is Union:
            args = annotation.__args__
            if len(args) == 2 and type(None) in args:
                non_none_type = next(arg for arg in args if arg is not type(None))
                return type_map.get(non_none_type, "string")
            else:
                return "string"
        elif origin in (list, list):
            return "array"
        elif origin in (dict, dict):
            return "object"
        else:
            return type_map.get(origin, "string")

    # Handle direct types (int, str, bool, etc.)
    return type_map.get(annotation, "string")


def extract_parameters_from_function(func: Any) -> list[ToolParameter]:
    """Extract parameters from a function signature."""
    sig = inspect.signature(func)
    parameters = []

    for param_name, param in sig.parameters.items():
        if param_name == "self":  # Skip self parameter for methods
            continue

        tool_param = ToolParameter.from_annotation(
            name=param_name,
            annotation=param.annotation if param.annotation != inspect.Parameter.empty else str,
            default=param.default,
        )
        parameters.append(tool_param)

    return parameters


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ToolParameter",
    "build_input_schema",
    "build_input_schema_bytes",
    "infer_type_from_annotation",
    "extract_parameters_from_function",
]
