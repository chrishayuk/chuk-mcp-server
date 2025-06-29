#!/usr/bin/env python3
# chuk_mcp_server/types.py
"""
Types - Type definitions and data structures
"""
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import inspect
import json

# ============================================================================
# Core Types
# ============================================================================

class TransportType(Enum):
    """Supported transport types."""
    HTTP = "http"
    STDIO = "stdio"
    SSE = "sse"


@dataclass
class ServerInfo:
    """MCP Server information."""
    name: str
    version: str
    title: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"name": self.name, "version": self.version}
        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class Capabilities:
    """MCP Server capabilities."""
    tools: bool = True
    resources: bool = True
    prompts: bool = False
    logging: bool = False
    experimental: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP capabilities format."""
        caps = {}
        
        if self.tools:
            caps["tools"] = {"listChanged": True}
        if self.resources:
            caps["resources"] = {"subscribe": False, "listChanged": True}
        if self.prompts:
            caps["prompts"] = {"listChanged": True}
        if self.logging:
            caps["logging"] = {}
        if self.experimental:
            caps["experimental"] = self.experimental
        else:
            caps["experimental"] = {}
            
        return caps


# ============================================================================
# Tool Types
# ============================================================================

@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None
    
    @classmethod
    def from_annotation(cls, name: str, annotation: Any, default: Any = inspect.Parameter.empty) -> 'ToolParameter':
        """Create parameter from function annotation."""
        # Handle common Python types
        type_map = {
            str: "string",
            int: "integer", 
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }
        
        param_type = "string"  # default
        description = None
        enum_values = None
        
        # Get base type
        if hasattr(annotation, '__origin__'):
            # Handle generic types like Optional, Union, List, etc.
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
            description=description,
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


@dataclass 
class Tool:
    """MCP Tool definition."""
    name: str
    description: str
    handler: Callable
    parameters: List[ToolParameter]
    
    @classmethod
    def from_function(cls, func: Callable, name: Optional[str] = None, description: Optional[str] = None) -> 'Tool':
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
            
            # Type conversion if needed
            if value is not None:
                if param.type == "integer" and not isinstance(value, int):
                    value = int(value)
                elif param.type == "number" and not isinstance(value, (int, float)):
                    value = float(value)
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
# Resource Types
# ============================================================================

@dataclass
class Resource:
    """MCP Resource definition."""
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
        if isinstance(result, dict) or isinstance(result, list):
            return json.dumps(result, indent=2)
        else:
            return str(result)


# ============================================================================
# Content Types
# ============================================================================

@dataclass
class TextContent:
    """Text content for MCP responses."""
    text: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {"type": "text", "text": self.text}


@dataclass
class ImageContent:
    """Image content for MCP responses."""
    data: str
    mime_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "image", 
            "data": self.data,
            "mimeType": self.mime_type
        }


# Union type for all content types
Content = Union[TextContent, ImageContent, str, dict]


def format_content(content: Content) -> List[Dict[str, Any]]:
    """Format content for MCP response."""
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    elif isinstance(content, dict):
        return [{"type": "text", "text": json.dumps(content, indent=2)}]
    elif isinstance(content, (TextContent, ImageContent)):
        return [content.to_dict()]
    elif isinstance(content, list):
        result = []
        for item in content:
            result.extend(format_content(item))
        return result
    else:
        return [{"type": "text", "text": str(content)}]