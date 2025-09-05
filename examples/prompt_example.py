#!/usr/bin/env python3
# examples/prompt_example.py
"""
ChukMCPServer Prompt Decorator Examples

This example demonstrates the new @prompt decorator functionality
for creating custom prompts through the MCP protocol.
"""

from chuk_mcp_server import ChukMCPServer, prompt

# ============================================================================
# Example 1: Global Prompt Decorators (Zero Config)
# ============================================================================


@prompt
def code_review(code: str, language: str = "python") -> str:
    """
    Generate a code review prompt for the given code.

    This prompt will ask for a comprehensive code review including:
    - Code quality assessment
    - Potential bugs or issues
    - Best practices suggestions
    - Performance improvements
    """
    return f"""Please review this {language} code and provide feedback on:

1. **Code Quality**: Is the code readable and well-structured?
2. **Potential Issues**: Are there any bugs, edge cases, or problems?
3. **Best Practices**: Does it follow {language} best practices?
4. **Performance**: Any performance improvements you'd suggest?
5. **Security**: Any security concerns?

```{language}
{code}
```

Please provide specific, actionable feedback with examples where appropriate.
"""


@prompt
def documentation_writer(function_name: str, description: str, parameters: str = "", returns: str = "") -> str:
    """Generate documentation for a function."""
    return f"""Write comprehensive documentation for the following function:

**Function**: `{function_name}`
**Description**: {description}
**Parameters**: {parameters if parameters else "None"}
**Returns**: {returns if returns else "Not specified"}

Please generate:
1. A clear docstring following standard conventions
2. Usage examples with sample inputs and outputs
3. Any important notes about edge cases or limitations

Format the documentation in a clear, professional style suitable for API documentation.
"""


@prompt
def meeting_summarizer(transcript: str, meeting_type: str = "general", action_items: bool = True) -> str:
    """Generate a meeting summary from a transcript."""
    base_prompt = f"""Summarize this {meeting_type} meeting transcript:

{transcript}

Please provide:
1. **Key Discussion Points**: Main topics covered
2. **Decisions Made**: Any decisions reached during the meeting
3. **Important Information**: Key facts or insights shared
"""

    if action_items:
        base_prompt += "4. **Action Items**: Specific tasks assigned with owners and deadlines\n"

    base_prompt += "\nFormat the summary in clear sections with bullet points for easy reading."
    return base_prompt


@prompt
def creative_writing(genre: str, theme: str, word_count: int = 500) -> str:
    """Generate a creative writing prompt."""
    return f"""Create a {genre} story with the following requirements:

**Genre**: {genre.title()}
**Theme**: {theme}
**Target Length**: Approximately {word_count} words

**Story Requirements**:
1. Develop compelling characters with clear motivations
2. Include vivid descriptions that engage the senses
3. Build tension or conflict appropriate to the {genre} genre
4. Incorporate the theme of "{theme}" meaningfully into the narrative
5. Aim for a satisfying resolution or meaningful ending

**Additional Guidelines**:
- Use active voice and varied sentence structures
- Show rather than tell when developing character and plot
- Create a strong opening that hooks the reader
- Ensure the theme emerges naturally from the story rather than being forced

Begin writing your {genre} story now.
"""


# ============================================================================
# Example 2: Server-based Prompt Registration
# ============================================================================

# Create server instance
mcp = ChukMCPServer(
    name="Prompt Demo Server",
    description="Demonstration of ChukMCPServer prompt capabilities",
    prompts=True,  # Enable prompts capability
)


# Add some tools for comparison
@mcp.tool
def analyze_text(text: str, analysis_type: str = "sentiment") -> dict:
    """Analyze text for various properties."""
    return {
        "text": text,
        "analysis_type": analysis_type,
        "length": len(text),
        "word_count": len(text.split()),
        "mock_result": f"Mock {analysis_type} analysis complete",
    }


# Add some resources
@mcp.resource("config://prompts")
def get_prompt_config() -> dict:
    """Get configuration for the prompt system."""
    return {
        "prompt_system": "ChukMCPServer Prompt Framework",
        "version": "1.0.0",
        "supported_formats": ["string", "structured"],
        "capabilities": [
            "Dynamic argument parsing",
            "Type validation",
            "Caching and optimization",
            "Zero configuration",
        ],
    }


# Server-based prompt decorators
@mcp.prompt
def sql_generator(table: str, operation: str = "SELECT", conditions: str = "", fields: str = "*") -> str:
    """Generate SQL queries based on parameters."""
    if operation.upper() == "SELECT":
        query = f"SELECT {fields} FROM {table}"
        if conditions:
            query += f" WHERE {conditions}"
        query += ";"
    elif operation.upper() == "INSERT":
        query = f"-- INSERT template for {table}\nINSERT INTO {table} (column1, column2, column3)\nVALUES (value1, value2, value3);"
    elif operation.upper() == "UPDATE":
        query = f"-- UPDATE template for {table}\nUPDATE {table}\nSET column1 = value1, column2 = value2"
        if conditions:
            query += f"\nWHERE {conditions}"
        query += ";"
    elif operation.upper() == "DELETE":
        query = f"DELETE FROM {table}"
        if conditions:
            query += f" WHERE {conditions}"
        query += ";"
    else:
        query = f"-- Unknown operation: {operation}\n-- Available operations: SELECT, INSERT, UPDATE, DELETE"

    return f"""Here's the SQL query for your {operation.upper()} operation on the {table} table:

```sql
{query}
```

**Operation**: {operation.upper()}
**Table**: {table}
**Conditions**: {conditions if conditions else "None"}
**Fields**: {fields if operation.upper() == "SELECT" else "N/A"}

Please review and modify as needed for your specific use case.
"""


@mcp.prompt
def email_composer(recipient: str, subject: str, tone: str = "professional", purpose: str = "general") -> str:
    """Compose email templates based on context."""

    # Tone-based greeting
    if tone == "formal":
        greeting = "Dear"
        closing = "Sincerely"
    elif tone == "casual":
        greeting = "Hi"
        closing = "Best"
    else:  # professional
        greeting = "Hello"
        closing = "Best regards"

    return f"""Compose an email with the following specifications:

**To**: {recipient}
**Subject**: {subject}
**Tone**: {tone.title()}
**Purpose**: {purpose}

**Email Template**:
```
{greeting} {recipient},

[Opening paragraph - establish context and purpose]

[Body paragraphs - main content based on purpose: {purpose}]
- Key point 1
- Key point 2
- Key point 3

[Closing paragraph - call to action or next steps]

{closing},
[Your name]
```

**Writing Guidelines for {tone} tone**:
- Use appropriate formality level
- Be clear and concise
- Include specific details relevant to: {purpose}
- Maintain a {tone} but friendly approach
- End with clear next steps if applicable

Please draft the complete email following this structure.
"""


if __name__ == "__main__":
    print("🚀 ChukMCPServer - Prompt Decorator Demo")
    print("=" * 50)
    print("📝 This server demonstrates prompt decorator capabilities:")
    print()
    print("Global Prompts (@prompt decorator):")
    print("  • code_review - Generate code review prompts")
    print("  • documentation_writer - Create function documentation")
    print("  • meeting_summarizer - Summarize meeting transcripts")
    print("  • creative_writing - Generate creative writing prompts")
    print()
    print("Server Prompts (@mcp.prompt decorator):")
    print("  • sql_generator - Generate SQL queries")
    print("  • email_composer - Compose email templates")
    print()
    print("🔍 Test with MCP Inspector:")
    print("  URL: http://localhost:8000/mcp")
    print("  Transport: Streamable HTTP")
    print()
    print("💬 The prompts/ endpoints will be available:")
    print("  • prompts/list - List all available prompts")
    print("  • prompts/get - Get a specific prompt with arguments")
    print()

    # Run the server
    mcp.run(debug=True)
