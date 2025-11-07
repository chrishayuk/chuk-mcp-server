"""Text processing tools module."""


def uppercase(text: str) -> str:
    """
    Convert text to uppercase.

    Args:
        text: Input text

    Returns:
        Uppercase version of the text
    """
    return text.upper()


uppercase._mcp_tool_metadata = {"name": "uppercase", "description": "Convert text to uppercase"}


def lowercase(text: str) -> str:
    """
    Convert text to lowercase.

    Args:
        text: Input text

    Returns:
        Lowercase version of the text
    """
    return text.lower()


lowercase._mcp_tool_metadata = {"name": "lowercase", "description": "Convert text to lowercase"}


def reverse(text: str) -> str:
    """
    Reverse text.

    Args:
        text: Input text

    Returns:
        Reversed text
    """
    return text[::-1]


reverse._mcp_tool_metadata = {"name": "reverse", "description": "Reverse text"}


def word_count(text: str) -> int:
    """
    Count words in text.

    Args:
        text: Input text

    Returns:
        Number of words
    """
    return len(text.split())


word_count._mcp_tool_metadata = {"name": "word_count", "description": "Count words in text"}
