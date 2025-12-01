# Prompts

Prompts are reusable templates that help Claude generate better responses.

## What is a Prompt?

A prompt template that Claude can use:

```python
from chuk_mcp_server import prompt

@prompt
def code_review(code: str, language: str) -> str:
    """Generate a code review prompt."""
    return f"""
    Review this {language} code:

    ```{language}
    {code}
    ```

    Focus on:
    - Code quality
    - Potential bugs
    - Best practices
    - Performance
    """
```

## When to Use Prompts

Use prompts for:
- **Code reviews** - Standardized review templates
- **Documentation** - Generate docs from code
- **Analysis** - Structured analysis tasks
- **Workflows** - Multi-step processes

## Next Steps

- [Tools](tools.md) - For actions
- [Resources](resources.md) - For data
- [Examples](../examples/calculator.md) - Real examples
