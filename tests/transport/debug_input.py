#!/usr/bin/env python3
"""Debug the exact input being sent."""

input_text = """{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test","version":"1.0.0"},"protocolVersion":"2025-06-18"}}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"hello","arguments":{"name":"STDIO"}}}
"""

print("Input text:")
print(repr(input_text))
print()
print("Lines:")
for i, line in enumerate(input_text.split("\\n")):
    print(f"{i}: {repr(line)}")
    if line.strip():
        try:
            import json

            data = json.loads(line)
            print(f"    ✅ Valid JSON: {data.get('method', 'N/A')}")
        except Exception as e:
            print(f"    ❌ Invalid JSON: {e}")
