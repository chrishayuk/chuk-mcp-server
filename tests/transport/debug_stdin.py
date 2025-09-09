#!/usr/bin/env python3
"""Debug stdin reading."""

import json
import sys

print("Debug: Starting stdin test", file=sys.stderr)
print("Debug: Waiting for input...", file=sys.stderr)

try:
    line = sys.stdin.readline()
    print(f"Debug: Got line: {repr(line)}", file=sys.stderr)

    if line.strip():
        try:
            data = json.loads(line.strip())
            print(f"Debug: Parsed JSON: {data}", file=sys.stderr)

            response = {"jsonrpc": "2.0", "id": data.get("id"), "result": {"status": "ok"}}
            response_line = json.dumps(response)
            print(response_line, flush=True)
        except Exception as e:
            print(f"Debug: JSON error: {e}", file=sys.stderr)

except Exception as e:
    print(f"Debug: Error: {e}", file=sys.stderr)
