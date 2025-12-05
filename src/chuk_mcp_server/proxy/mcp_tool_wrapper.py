"""
MCP Tool Wrapper - Create ToolHandlers from chuk-tool-processor MCPTool instances.

This dynamically generates function signatures matching the MCP tool's inputSchema.
"""

import logging
from typing import Any

from chuk_tool_processor.mcp import MCPTool

from ..types import ToolHandler

logger = logging.getLogger(__name__)


def create_mcp_tool_handler(
    mcp_tool: MCPTool,
    tool_def: dict[str, Any],
    full_name: str,
) -> ToolHandler:
    """
    Create a ToolHandler that wraps an MCPTool with proper signature.

    Args:
        mcp_tool: The MCPTool instance to wrap
        tool_def: Tool definition dict with inputSchema
        full_name: Full namespaced tool name

    Returns:
        ToolHandler with dynamically generated signature
    """
    description = tool_def.get("description", f"MCP proxied tool: {full_name}")
    input_schema = tool_def.get("inputSchema", {})
    properties = input_schema.get("properties", {})
    required_params = input_schema.get("required", [])

    # Build dynamic function parameters
    params_code = []
    for param_name, param_info in properties.items():
        param_type = param_info.get("type", "str")

        # Map JSON Schema types to Python type hints
        type_hint = {
            "string": "str",
            "number": "float",
            "integer": "int",
            "boolean": "bool",
            "object": "dict",
            "array": "list",
        }.get(param_type, "Any")

        # Add default if not required
        if param_name in required_params:
            params_code.append(f"{param_name}: {type_hint}")
        else:
            default_val = param_info.get("default")
            if default_val is None:
                default_repr = "None"
            elif isinstance(default_val, str):
                default_repr = repr(default_val)
            elif isinstance(default_val, int | float | bool):
                default_repr = str(default_val)
            elif isinstance(default_val, dict | list):
                default_repr = repr(default_val)
            else:
                default_repr = "None"

            params_code.append(f"{param_name}: {type_hint} = {default_repr}")

    func_params = ", ".join(params_code) if params_code else ""

    # Build kwargs collection
    kwargs_collection = []
    for p in params_code:
        param_name = p.split(":")[0].strip()
        kwargs_collection.append(f"    if {param_name} is not None:")
        kwargs_collection.append(f"        kwargs['{param_name}'] = {param_name}")

    kwargs_code = "\n".join(kwargs_collection) if kwargs_collection else "    pass"

    # Generate wrapper function
    func_code = f"""
async def _mcp_tool_wrapper({func_params}):
    import logging
    logger = logging.getLogger(__name__)

    kwargs = {{}}
{kwargs_code}

    logger.debug(f"Calling MCP tool {full_name} with args: {{kwargs}}")

    try:
        result = await mcp_tool.execute(**kwargs)
        return result
    except Exception as e:
        logger.error(f"MCP tool call failed for {full_name}: {{e}}")
        raise
"""

    # Compile and execute
    local_vars = {"mcp_tool": mcp_tool, "logger": logger}
    try:
        exec(func_code, local_vars)  # nosec B102
        _mcp_tool_wrapper = local_vars["_mcp_tool_wrapper"]
    except SyntaxError as e:
        logger.error(f"Syntax error in generated MCP wrapper: {e}")
        logger.error(f"Generated code:\n{func_code}")
        raise

    # Create ToolHandler
    tool_handler = ToolHandler.from_function(
        _mcp_tool_wrapper,
        name=full_name,
        description=description,
    )

    logger.debug(f"Created MCP tool handler: {full_name}")
    return tool_handler
