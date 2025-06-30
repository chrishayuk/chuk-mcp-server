#!/usr/bin/env python3
"""
Types - Clean integration with chuk_mcp types

This module imports and re-exports chuk_mcp types while adding framework-specific
conveniences and developer-friendly APIs on top.
"""

import inspect
import json
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# Import chuk_mcp Types (Primary Source of Truth)
# ============================================================================

# Core chuk_mcp protocol types
from chuk_mcp.protocol.types.content import (
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
    parse_content
)

from chuk_mcp.protocol.types.capabilities import (
    ServerCapabilities,
    ClientCapabilities,
    ToolsCapability,
    ResourcesCapability,
    PromptsCapability,
    LoggingCapability
)

from chuk_mcp.protocol.types.info import (
    ServerInfo as ChukServerInfo,
    ClientInfo as ChukClientInfo
)

# ============================================================================
# Framework-Specific Convenience Types
# ============================================================================

class TransportType(Enum):
    """Supported transport types for ChukMCPServer."""
    HTTP = "http"
    STDIO = "stdio"
    SSE = "sse"


@dataclass 
class ServerInfo:
    """Framework wrapper for chuk_mcp ServerInfo with conveniences."""
    name: str
    version: str
    title: Optional[str] = None
    description: Optional[str] = None
    
    def to_chuk_mcp(self) -> ChukServerInfo:
        """Convert to chuk_mcp ServerInfo."""
        return ChukServerInfo(
            name=self.name,
            version=self.version,
            title=self.title
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.to_chuk_mcp().model_dump(exclude_none=True)


@dataclass
class Capabilities:
    """Framework wrapper for chuk_mcp ServerCapabilities with conveniences."""
    tools: bool = True
    resources: bool = True
    prompts: bool = False
    logging: bool = False
    experimental: Optional[Dict[str, Any]] = None
    
    def to_chuk_mcp(self) -> ServerCapabilities:
        """Convert to chuk_mcp ServerCapabilities."""
        caps_dict = {}
        
        if self.tools:
            caps_dict["tools"] = ToolsCapability(listChanged=True)
        if self.resources:
            caps_dict["resources"] = ResourcesCapability(
                listChanged=True, 
                subscribe=False
            )
        if self.prompts:
            caps_dict["prompts"] = PromptsCapability(listChanged=True)
        if self.logging:
            caps_dict["logging"] = LoggingCapability()
        if self.experimental:
            caps_dict["experimental"] = self.experimental
        
        return ServerCapabilities(**caps_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP capabilities format."""
        return self.to_chuk_mcp().model_dump(exclude_none=True)


# ============================================================================
# Tool Parameter
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
        """Create parameter from function annotation."""
        # Enhanced type mapping
        type_map = {
            str: "string",
            int: "integer", 
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            List: "array",
            Dict: "object"
        }
        
        param_type = "string"  # default
        
        # Handle generic types like Optional, Union, List, etc.
        if hasattr(annotation, '__origin__'):
            origin = annotation.__origin__
            if origin is Union:
                # Handle Optional (Union[T, None])
                args = annotation.__args__
                if len(args) == 2 and type(None) in args:
                    # This is Optional[T]
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
            enum=None
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
# Framework Tool
# ============================================================================

@dataclass 
class Tool:
    """Framework tool wrapper."""
    name: str
    description: str
    handler: Callable
    parameters: List[ToolParameter]
    
    @classmethod
    def from_function(cls, func: Callable, name: Optional[str] = None, 
                     description: Optional[str] = None) -> 'Tool':
        """Create Tool from a function."""
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
        
        return cls(
            name=tool_name,
            description=tool_description,
            handler=func,
            parameters=parameters
        )
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP tool format."""
        # Build JSON schema for parameters
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)
        
        input_schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            input_schema["required"] = required
        
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": input_schema
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the tool with given arguments."""
        # Validate and convert arguments
        validated_args = {}
        
        for param in self.parameters:
            value = arguments.get(param.name)
            
            if value is None:
                if param.required:
                    raise ValueError(f"Missing required parameter: {param.name}")
                value = param.default
            
            # Enhanced type conversion
            if value is not None:
                if param.type == "integer" and not isinstance(value, int):
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"Cannot convert {value} to integer for parameter {param.name}")
                elif param.type == "number" and not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"Cannot convert {value} to number for parameter {param.name}")
                elif param.type == "boolean" and not isinstance(value, bool):
                    value = bool(value)
            
            if value is not None:
                validated_args[param.name] = value
        
        # Execute the function
        if inspect.iscoroutinefunction(self.handler):
            return await self.handler(**validated_args)
        else:
            return self.handler(**validated_args)


# ============================================================================
# Framework Resource
# ============================================================================

@dataclass
class Resource:
    """Framework resource wrapper."""
    uri: str
    name: str
    description: str
    mime_type: str
    handler: Callable
    
    @classmethod
    def from_function(cls, uri: str, func: Callable, name: Optional[str] = None, 
                     description: Optional[str] = None, mime_type: str = "text/plain") -> 'Resource':
        """Create Resource from a function."""
        resource_name = name or func.__name__.replace('_', ' ').title()
        resource_description = description or func.__doc__ or f"Resource: {uri}"
        
        return cls(
            uri=uri,
            name=resource_name,
            description=resource_description,
            mime_type=mime_type,
            handler=func
        )
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP resource format."""
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }
    
    async def read(self) -> str:
        """Read the resource content."""
        if inspect.iscoroutinefunction(self.handler):
            result = await self.handler()
        else:
            result = self.handler()
        
        # Convert result to string if needed
        if isinstance(result, (dict, list)):
            return json.dumps(result, indent=2)
        else:
            return str(result)


# ============================================================================
# Content Formatting using chuk_mcp
# ============================================================================

def format_content(content) -> List[Dict[str, Any]]:
    """Format content using chuk_mcp types for robust serialization."""
    if isinstance(content, str):
        # Use chuk_mcp's create_text_content function
        text_content = create_text_content(content)
        return [content_to_dict(text_content)]
    elif isinstance(content, dict):
        # Convert dict to JSON string using chuk_mcp
        text_content = create_text_content(json.dumps(content, indent=2))
        return [content_to_dict(text_content)]
    elif isinstance(content, (TextContent, ImageContent, AudioContent, EmbeddedResource)):
        # Use chuk_mcp's content_to_dict function
        return [content_to_dict(content)]
    elif isinstance(content, list):
        result = []
        for item in content:
            result.extend(format_content(item))
        return result
    else:
        # Convert anything else to string using chuk_mcp
        text_content = create_text_content(str(content))
        return [content_to_dict(text_content)]


# ============================================================================
# Re-exports and Aliases
# ============================================================================

# Direct re-exports of chuk_mcp types
ChukServerInfo = ChukServerInfo
ChukClientInfo = ChukClientInfo

# Framework aliases for backwards compatibility
ServerCapabilities = ServerCapabilities  # Direct chuk_mcp type
ClientCapabilities = ClientCapabilities   # Direct chuk_mcp type

__all__ = [
    # Framework types
    "TransportType",
    "ServerInfo", 
    "Capabilities",
    "ToolParameter",
    "Tool",
    "Resource",
    
    # chuk_mcp content types (direct)
    "TextContent",
    "ImageContent", 
    "AudioContent",
    "EmbeddedResource",
    "Content",
    "Annotations",
    
    # Content helper functions
    "create_text_content",
    "create_image_content", 
    "create_audio_content",
    "create_embedded_resource",
    "format_content",
    "content_to_dict",
    "parse_content",
    
    # chuk_mcp types (direct)
    "ServerCapabilities",
    "ClientCapabilities",
    "ChukServerInfo",
    "ChukClientInfo",
    
    # Capability types
    "ToolsCapability",
    "ResourcesCapability",
    "PromptsCapability",
    "LoggingCapability",
]