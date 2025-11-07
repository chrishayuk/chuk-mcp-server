"""Math tools module - example tools for ChukMCPServer."""


def add(a: float, b: float) -> float:
    """
    Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


# Add metadata that ModuleLoader looks for
add._mcp_tool_metadata = {"name": "add", "description": "Add two numbers"}


def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of a and b
    """
    return a * b


multiply._mcp_tool_metadata = {"name": "multiply", "description": "Multiply two numbers"}


def power(base: float, exponent: float = 2.0) -> float:
    """
    Raise base to the power of exponent.

    Args:
        base: Base number
        exponent: Exponent (default: 2.0)

    Returns:
        base raised to the power of exponent
    """
    return base**exponent


power._mcp_tool_metadata = {"name": "power", "description": "Raise a number to a power"}
