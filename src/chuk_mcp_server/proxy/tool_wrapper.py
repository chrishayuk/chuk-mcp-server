"""
Tool wrapper for creating proxy tools that forward to remote MCP servers.
"""

import logging
from typing import Any

from ..types import ToolHandler

logger = logging.getLogger(__name__)


async def create_proxy_tool(
    namespace: str,
    tool_name: str,
    server_client: Any,
    metadata: dict[str, Any] | None = None,
) -> ToolHandler:
    """
    Create a proxy tool that forwards calls to a remote MCP server.

    Args:
        namespace: Tool namespace (e.g., "proxy.time")
        tool_name: Original tool name (e.g., "get_current_time")
        server_client: Client for communicating with the remote server
        metadata: Tool metadata from remote server

    Returns:
        ToolHandler that proxies calls to the remote server
    """
    metadata = metadata or {}
    fq_name = f"{namespace}.{tool_name}"
    description = metadata.get("description", f"Proxied tool: {fq_name}")
    server_name = namespace.split(".")[-1]

    # Extract parameter schema from metadata
    input_schema = metadata.get("inputSchema", {})
    properties = input_schema.get("properties", {})
    required_params = input_schema.get("required", [])

    # Build dynamic function signature based on remote tool's parameters
    params_code = []
    for param_name, param_info in properties.items():
        param_type = param_info.get("type", "string")
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
            # Get default value and properly quote strings
            default_val = param_info.get("default")
            if default_val is None:
                default_repr = "None"
            elif isinstance(default_val, str):
                # Properly escape and quote string defaults
                default_repr = repr(default_val)
            elif isinstance(default_val, int | float | bool):
                default_repr = str(default_val)
            elif isinstance(default_val, dict | list):
                default_repr = repr(default_val)
            else:
                default_repr = "None"

            params_code.append(f"{param_name}: {type_hint} = {default_repr}")

    # Create wrapper function dynamically
    func_params = ", ".join(params_code) if params_code else ""

    # Build kwargs collection code
    kwargs_collection = []
    for p in params_code:
        param_name = p.split(":")[0].strip()
        kwargs_collection.append(f"    if {param_name} is not None:")
        kwargs_collection.append(f"        kwargs['{param_name}'] = {param_name}")

    kwargs_code = "\n".join(kwargs_collection) if kwargs_collection else "    pass"

    # Build the function code with proper indentation
    func_code = f"""
async def _proxy_wrapper({func_params}):
    import logging
    logger = logging.getLogger(__name__)

    kwargs = {{}}
{kwargs_code}

    logger.debug(f"Proxying call to {server_name}.{tool_name} with args: {{kwargs}}")

    try:
        result = await server_client.call_tool(
            tool_name="{tool_name}",
            arguments=kwargs,
        )

        # Handle legacy StdioServerClient format (dict with isError/content)
        if isinstance(result, dict) and result.get("isError"):
            error_msg = result.get("error", "Unknown MCP error")
            raise RuntimeError(f"Remote tool error: {{error_msg}}")

        # Handle legacy format
        if isinstance(result, dict) and "content" in result:
            return result.get("content")

        # Handle new transport format (direct result)
        return result

    except Exception as e:
        logger.error(f"Proxy call failed for {server_name}.{tool_name}: {{e}}")
        raise
"""

    # Compile and execute the function
    # Using exec() here is safe because:
    # 1. The code is generated programmatically, not from user input
    # 2. All variable names come from validated tool metadata (MCP schema)
    # 3. The local_vars dict is controlled and sandboxed
    # 4. This is only executed during tool registration, not at runtime
    local_vars = {"server_client": server_client, "logger": logger}
    try:
        exec(func_code, local_vars)  # nosec B102
        _proxy_wrapper = local_vars["_proxy_wrapper"]
    except SyntaxError as e:
        logger.error(f"Syntax error in generated proxy function: {e}")
        logger.error(f"Generated code:\n{func_code}")
        raise

    # Create tool handler from the wrapper function
    tool_handler = ToolHandler.from_function(
        _proxy_wrapper,
        name=fq_name,
        description=description,
    )

    # Attach metadata for debugging (dynamic attributes)
    _proxy_wrapper._proxy_server = server_name
    _proxy_wrapper._proxy_metadata = metadata

    logger.debug(f"Created proxy tool: {fq_name}")
    return tool_handler
