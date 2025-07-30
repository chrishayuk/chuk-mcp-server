#!/usr/bin/env python3
# src/chuk_mcp_server/types/content.py
"""
Content - Content formatting with orjson optimization

This module provides content formatting functions using chuk_mcp types
with orjson optimization for maximum performance.
"""

import orjson
from typing import List, Dict, Any

from .base import (
    TextContent, ImageContent, AudioContent, EmbeddedResource,
    create_text_content, content_to_dict
)

def format_content(content) -> List[Dict[str, Any]]:
    """Format content using chuk_mcp types with orjson optimization."""
    if isinstance(content, str):
        text_content = create_text_content(content)
        return [content_to_dict(text_content)]
    elif isinstance(content, dict):
        # 🚀 Use orjson for 2-3x faster JSON serialization
        json_str = orjson.dumps(content, option=orjson.OPT_INDENT_2).decode()
        text_content = create_text_content(json_str)
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

def format_content_as_text(content: Any) -> str:
    """Format any content as plain text."""
    if isinstance(content, str):
        return content
    elif isinstance(content, (dict, list)):
        return orjson.dumps(content, option=orjson.OPT_INDENT_2).decode()
    else:
        return str(content)

def format_content_as_json(content: Any) -> str:
    """Format any content as JSON string with orjson."""
    if isinstance(content, str):
        # Try to parse and re-format for consistency
        try:
            parsed = orjson.loads(content)
            return orjson.dumps(parsed, option=orjson.OPT_INDENT_2).decode()
        except orjson.JSONDecodeError:
            # If not valid JSON, wrap in quotes
            return orjson.dumps(content).decode()
    else:
        return orjson.dumps(content, option=orjson.OPT_INDENT_2).decode()

__all__ = ["format_content", "format_content_as_text", "format_content_as_json"]