#!/usr/bin/env python3
# src/chuk_mcp_server/types.py
"""
Types - Direct integration with chuk_mcp types

This module uses chuk_mcp types directly, eliminating unnecessary conversion layers
and providing a cleaner, more maintainable API.
"""

import inspect
import json
import time
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# Direct chuk_mcp imports - No Conversion Layer
# ============================================================================

# Use chuk_mcp types directly
from chuk_mcp.protocol.types import (
    # Server/Client info (use directly)
    ServerInfo,
    ClientInfo,
    
    # Capabilities (use directly)
    ServerCapabilities,
    ClientCapabilities,
    ToolsCapability,
    ResourcesCapability,
    PromptsCapability,
    LoggingCapability,
    
    # Content types (use directly)
    TextContent,
    ImageContent,
    AudioContent,
    EmbeddedResource,
    Content,
    Annotations,
    create_text_content,
    create_image_content,
    create_audio_content,
    create_embedded_resource,
    content_to_dict,
    parse_content,
    
    # Error handling
    MCPError,
    ProtocolError,
    ValidationError,
    
    # Versioning
    CURRENT_VERSION,
    SUPPORTED_VERSIONS,
    ProtocolVersion,
)

# Import chuk_mcp's Resource, Tool, and ToolInputSchema types separately to avoid naming conflicts
from chuk_mcp.protocol.messages.resources.resource import Resource as MCPResource
from chuk_mcp.protocol.messages.tools.tool import Tool as MCPTool
from chuk_mcp.protocol.messages.tools.tool_input_schema import ToolInputSchema as MCPToolInputSchema

# ============================================================================
# Framework-Specific Enums (Keep Simple)
# ============================================================================

class TransportType(Enum):
    """Supported transport types for ChukMCPServer."""
    HTTP = "http"
    STDIO = "stdio"
    SSE = "sse"


# ============================================================================
# Enhanced Tool Parameter with Modern Typing
# ============================================================================

@dataclass
class ToolParameter:
    """Tool parameter definition with enhanced type support."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None
    
    @classmethod
    def from_annotation(cls, name: str, annotation: Any, 
                       default: Any = inspect.Parameter.empty) -> 'ToolParameter':
        """Create parameter from function annotation with modern typing support."""
        import typing
        from typing import Union, List, Dict  # Add explicit imports
        
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
        
        # Handle modern typing features
        if hasattr(typing, 'get_origin') and hasattr(typing, 'get_args'):
            origin = typing.get_origin(annotation)
            args = typing.get_args(annotation)
            
            if origin is Union:
                # Handle Optional[T] and Union types
                if len(args) == 2 and type(None) in args:
                    # Optional[T] case
                    non_none_type = next(arg for arg in args if arg is not type(None))
                    param_type = type_map.get(non_none_type, "string")
                else:
                    # Multiple union types - default to string
                    param_type = "string"
            
            # Handle Literal types for enums
            elif hasattr(typing, 'Literal') and origin is typing.Literal:
                param_type = "string"
                enum_values = list(args)
            
            # Handle generic containers
            elif origin in (list, typing.List):
                param_type = "array"
            elif origin in (dict, typing.Dict):
                param_type = "object"
            else:
                param_type = type_map.get(origin, "string")
        
        # Fallback for older typing or direct types
        elif hasattr(annotation, '__origin__'):
            origin = annotation.__origin__
            if origin is Union:
                args = annotation.__args__
                if len(args) == 2 and type(None) in args:
                    non_none_type = next(arg for arg in args if arg is not type(None))
                    param_type = type_map.get(non_none_type, "string")
                else:
                    param_type = "string"
            elif origin in (list, List):
                param_type = "array"
            elif origin in (dict, Dict):
                param_type = "object"
            else:
                param_type = type_map.get(origin, "string")
        else:
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
            enum=enum_values
        )
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = {"type": self.type}
        
        if self.description:
            schema["description"] = self.description
        if self.enum:
            schema["enum"] = self.enum
        if self.default is not None:
            schema["default"] = self.default
            
        return schema


# ============================================================================
# Enhanced Framework Tool Handler with Better Error Handling
# ============================================================================

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


@dataclass 
class ToolHandler:
    """Framework tool handler with enhanced error handling - wraps chuk_mcp Tool."""
    mcp_tool: MCPTool  # The actual MCP tool
    handler: Callable
    parameters: List[ToolParameter]
    
    @classmethod
    def from_function(cls, func: Callable, name: Optional[str] = None, 
                     description: Optional[str] = None) -> 'ToolHandler':
        """Create ToolHandler from a function."""
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Execute {tool_name}"
        
        # Extract parameters from function signature
        sig = inspect.signature(func)
        parameters = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':  # Skip self parameter for methods
                continue
                
            tool_param = ToolParameter.from_annotation(
                name=param_name,
                annotation=param.annotation if param.annotation != inspect.Parameter.empty else str,
                default=param.default
            )
            parameters.append(tool_param)
        
        # Build JSON schema for the MCP tool using the proper schema type
        properties = {}
        required = []
        
        for param in parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)
        
        # Create the proper MCP ToolInputSchema
        input_schema = MCPToolInputSchema(
            type="object",
            properties=properties,
            required=required if required else None
        )
        
        # Create the MCP tool with the proper schema
        mcp_tool = MCPTool(
            name=tool_name,
            description=tool_description,
            inputSchema=input_schema.model_dump(exclude_none=True)
        )
        
        return cls(
            mcp_tool=mcp_tool,
            handler=func,
            parameters=parameters
        )
    
    @property
    def name(self) -> str:
        """Get the tool name."""
        return self.mcp_tool.name
    
    @property
    def description(self) -> Optional[str]:
        """Get the tool description."""
        return self.mcp_tool.description
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP tool format."""
        return self.mcp_tool.model_dump(exclude_none=True)
    
    def _validate_and_convert_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and convert arguments with specific error types."""
        validated_args = {}
        
        for param in self.parameters:
            value = arguments.get(param.name)
            
            if value is None:
                if param.required:
                    raise ParameterValidationError(param.name, param.type, None)
                value = param.default
            
            # Type validation and conversion
            if value is not None:
                try:
                    validated_value = self._convert_type(value, param)
                    validated_args[param.name] = validated_value
                except (ValueError, TypeError) as e:
                    raise ParameterValidationError(param.name, param.type, value)
        
        return validated_args
    
    def _convert_type(self, value: Any, param: ToolParameter) -> Any:
        """Convert value to the expected parameter type with robust handling."""
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
                    except ValueError:
                        raise ValueError(f"Cannot convert string '{value}' to integer")
            else:
                # Try direct int conversion for other types
                return int(value)
        
        elif param.type == "number":
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    raise ValueError(f"Cannot convert string '{value}' to number")
            else:
                return float(value)
        
        elif param.type == "boolean":
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                # Handle string boolean conversion
                lower_val = value.lower()
                if lower_val in ('true', '1', 'yes', 'on', 't', 'y'):
                    return True
                elif lower_val in ('false', '0', 'no', 'off', 'f', 'n'):
                    return False
                else:
                    raise ValueError(f"Cannot convert string '{value}' to boolean")
            elif isinstance(value, (int, float)):
                # Handle numeric boolean conversion
                return bool(value)
            else:
                return bool(value)
        
        elif param.type == "string":
            if isinstance(value, str):
                return value
            else:
                # Convert other types to string
                return str(value)
        
        elif param.type == "array":
            if isinstance(value, list):
                return value
            elif isinstance(value, (tuple, set)):
                return list(value)
            elif isinstance(value, str):
                # Try to parse JSON array
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                    else:
                        raise ValueError(f"String '{value}' does not represent an array")
                except json.JSONDecodeError:
                    raise ValueError(f"Cannot convert string '{value}' to array")
            else:
                raise ValueError(f"Cannot convert {type(value).__name__} to array")
        
        elif param.type == "object":
            if isinstance(value, dict):
                return value
            elif isinstance(value, str):
                # Try to parse JSON object
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict):
                        return parsed
                    else:
                        raise ValueError(f"String '{value}' does not represent an object")
                except json.JSONDecodeError:
                    raise ValueError(f"Cannot convert string '{value}' to object")
            else:
                raise ValueError(f"Cannot convert {type(value).__name__} to object")
        
        # Check enum values if specified
        if param.enum and value not in param.enum:
            raise ValueError(f"Value '{value}' must be one of {param.enum}")
        
        return value
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
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
            raise ToolExecutionError(self.name, e)


# ============================================================================
# Enhanced Framework Resource Handler with Caching
# ============================================================================

@dataclass
class ResourceHandler:
    """Framework resource handler with optional caching - wraps chuk_mcp Resource."""
    mcp_resource: MCPResource  # The actual MCP resource
    handler: Callable
    cache_ttl: Optional[int] = None  # Cache TTL in seconds
    
    def __post_init__(self):
        self._cached_content: Optional[str] = None
        self._cache_timestamp: Optional[float] = None
    
    @classmethod
    def from_function(cls, uri: str, func: Callable, name: Optional[str] = None, 
                     description: Optional[str] = None, mime_type: str = "text/plain",
                     cache_ttl: Optional[int] = None) -> 'ResourceHandler':
        """Create ResourceHandler from a function."""
        resource_name = name or func.__name__.replace('_', ' ').title()
        resource_description = description or func.__doc__ or f"Resource: {uri}"
        
        # Create the MCP resource
        mcp_resource = MCPResource(
            uri=uri,
            name=resource_name,
            description=resource_description,
            mimeType=mime_type
        )
        
        return cls(
            mcp_resource=mcp_resource,
            handler=func,
            cache_ttl=cache_ttl
        )
    
    @property
    def uri(self) -> str:
        """Get the resource URI."""
        return self.mcp_resource.uri
    
    @property
    def name(self) -> str:
        """Get the resource name."""
        return self.mcp_resource.name
    
    @property
    def description(self) -> Optional[str]:
        """Get the resource description."""
        return self.mcp_resource.description
    
    @property
    def mime_type(self) -> Optional[str]:
        """Get the resource MIME type."""
        return self.mcp_resource.mimeType
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP resource format."""
        return self.mcp_resource.model_dump(exclude_none=True)
    
    async def read(self) -> str:
        """Read the resource content with optional caching."""
        now = time.time()
        
        # Check cache validity
        if (self.cache_ttl and 
            self._cached_content and 
            self._cache_timestamp and
            now - self._cache_timestamp < self.cache_ttl):
            return self._cached_content
        
        # Read fresh content
        try:
            if inspect.iscoroutinefunction(self.handler):
                result = await self.handler()
            else:
                result = self.handler()
            
            # Format content based on MIME type
            content = self._format_content(result)
            
            # Cache if TTL is set
            if self.cache_ttl:
                self._cached_content = content
                self._cache_timestamp = now
            
            return content
            
        except Exception as e:
            raise MCPError(f"Failed to read resource '{self.uri}': {str(e)}")
    
    def _format_content(self, result: Any) -> str:
        """Format content based on MIME type."""
        mime_type = self.mime_type or "text/plain"
        
        if mime_type == "application/json":
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2, ensure_ascii=False)
            else:
                return json.dumps(result, ensure_ascii=False)
        elif mime_type == "text/markdown":
            return str(result)
        elif mime_type == "text/plain":
            return str(result)
        else:
            # For unknown MIME types, convert to string
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2)
            else:
                return str(result)
    
    def invalidate_cache(self):
        """Manually invalidate the cached content."""
        self._cached_content = None
        self._cache_timestamp = None


# ============================================================================
# Simplified Capabilities Helper
# ============================================================================

def create_server_capabilities(
    tools: bool = True,
    resources: bool = True,
    prompts: bool = False,
    logging: bool = False,
    experimental: Optional[Dict[str, Any]] = None
) -> ServerCapabilities:
    """Create server capabilities using chuk_mcp types directly."""
    capabilities = {}
    
    if tools:
        capabilities["tools"] = ToolsCapability(listChanged=True)
    if resources:
        capabilities["resources"] = ResourcesCapability(
            listChanged=True, 
            subscribe=False
        )
    if prompts:
        capabilities["prompts"] = PromptsCapability(listChanged=True)
    if logging:
        capabilities["logging"] = LoggingCapability()
    if experimental:
        capabilities["experimental"] = experimental
    
    return ServerCapabilities(**capabilities)


# ============================================================================
# Content Formatting using chuk_mcp directly
# ============================================================================

def format_content(content) -> List[Dict[str, Any]]:
    """Format content using chuk_mcp types directly."""
    if isinstance(content, str):
        text_content = create_text_content(content)
        return [content_to_dict(text_content)]
    elif isinstance(content, dict):
        text_content = create_text_content(json.dumps(content, indent=2))
        return [content_to_dict(text_content)]
    elif isinstance(content, (TextContent, ImageContent, AudioContent, EmbeddedResource)):
        return [content_to_dict(content)]
    elif isinstance(content, list):
        result = []
        for item in content:
            result.extend(format_content(item))
        return result
    else:
        text_content = create_text_content(str(content))
        return [content_to_dict(text_content)]


# ============================================================================
# Legacy Compatibility (for existing code)
# ============================================================================

# Create simple wrappers that use chuk_mcp types directly
def Capabilities(**kwargs) -> ServerCapabilities:
    """Legacy compatibility wrapper for create_server_capabilities."""
    return create_server_capabilities(**kwargs)

# Aliases for backward compatibility
Resource = ResourceHandler
Tool = ToolHandler


# ============================================================================
# Clean Exports - Direct chuk_mcp types
# ============================================================================

__all__ = [
    # Framework-specific types
    "TransportType",
    "ToolParameter", 
    "Tool",
    "Resource",        # Alias for ResourceHandler
    "ResourceHandler", # Explicit name
    
    # Framework helpers
    "create_server_capabilities",
    "format_content",
    "Capabilities",  # Legacy compatibility
    
    # Exception types
    "ParameterValidationError",
    "ToolExecutionError",
    
    # Direct chuk_mcp types (no conversion needed)
    "ServerInfo",
    "ClientInfo", 
    "ServerCapabilities",
    "ClientCapabilities",
    "ToolsCapability",
    "ResourcesCapability",
    "PromptsCapability",
    "LoggingCapability",
    "MCPResource",  # chuk_mcp's Resource type
    
    # Content types (direct from chuk_mcp)
    "TextContent",
    "ImageContent",
    "AudioContent", 
    "EmbeddedResource",
    "Content",
    "Annotations",
    
    # Content helpers (direct from chuk_mcp)
    "create_text_content",
    "create_image_content",
    "create_audio_content",
    "create_embedded_resource",
    "content_to_dict",
    "parse_content",
    
    # Error types (direct from chuk_mcp)
    "MCPError",
    "ProtocolError",
    "ValidationError",
    
    # Versioning (direct from chuk_mcp)
    "CURRENT_VERSION",
    "SUPPORTED_VERSIONS",
    "ProtocolVersion",
]