#!/usr/bin/env python3
"""
In-process performance benchmark — no HTTP server needed.

Measures the core paths that were modified in the architecture audit:
  - ToolHandler.from_function (schema generation + caching)
  - to_mcp_format / to_mcp_bytes (cached serialization)
  - Protocol handler (initialize, tools/list, tools/call, resources/list)
  - ResourceHandler / PromptHandler creation

Run:  python benchmarks/in_process_benchmark.py
"""

import asyncio
import gc
import statistics
import time
from typing import Any


def _banner(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def _report(name: str, iterations: int, elapsed: float, latencies: list[float] | None = None) -> None:
    ops_per_sec = iterations / elapsed if elapsed > 0 else 0
    print(f"  {name:<40}  {iterations:>8,} ops  {elapsed:>7.3f}s  {ops_per_sec:>10,.0f} ops/s", end="")
    if latencies:
        avg_us = statistics.mean(latencies) * 1_000_000
        p95_us = sorted(latencies)[int(len(latencies) * 0.95)] * 1_000_000
        print(f"  avg={avg_us:.1f}us  p95={p95_us:.1f}us", end="")
    print()


# ============================================================================
# 1. ToolHandler creation benchmark
# ============================================================================
def bench_tool_creation(n: int = 5_000) -> None:
    _banner("ToolHandler.from_function (schema gen + cache)")
    from chuk_mcp_server.types.tools import ToolHandler

    def sample_tool(name: str, count: int = 10, verbose: bool = False) -> dict:
        """A sample tool with multiple parameter types."""
        return {"name": name, "count": count, "verbose": verbose}

    gc.disable()
    start = time.perf_counter()
    for _ in range(n):
        ToolHandler.from_function(sample_tool)
    elapsed = time.perf_counter() - start
    gc.enable()
    _report("ToolHandler.from_function", n, elapsed)


# ============================================================================
# 2. Cached serialization benchmark
# ============================================================================
def bench_serialization(n: int = 100_000) -> None:
    _banner("Cached serialization (to_mcp_format / to_mcp_bytes)")
    from chuk_mcp_server.types.tools import ToolHandler

    def sample_tool(name: str, count: int = 10, verbose: bool = False) -> dict:
        return {"name": name, "count": count, "verbose": verbose}

    handler = ToolHandler.from_function(
        sample_tool,
        read_only_hint=True,
        meta={"ui": {"resourceUri": "https://cdn.example.com/view.html"}},
    )

    # to_mcp_format (dict copy from cache)
    gc.disable()
    start = time.perf_counter()
    for _ in range(n):
        handler.to_mcp_format()
    elapsed_fmt = time.perf_counter() - start
    gc.enable()
    _report("to_mcp_format (cached dict)", n, elapsed_fmt)

    # to_mcp_bytes (orjson round-trip from cache)
    gc.disable()
    start = time.perf_counter()
    for _ in range(n):
        handler.to_mcp_bytes()
    elapsed_bytes = time.perf_counter() - start
    gc.enable()
    _report("to_mcp_bytes (cached bytes)", n, elapsed_bytes)


# ============================================================================
# 3. Resource + Prompt handler creation
# ============================================================================
def bench_resource_prompt_creation(n: int = 5_000) -> None:
    _banner("ResourceHandler / PromptHandler creation")
    from chuk_mcp_server.types.prompts import PromptHandler
    from chuk_mcp_server.types.resources import ResourceHandler

    def get_config() -> dict:
        """Return server configuration."""
        return {"version": "1.0", "debug": False}

    def code_review(code: str, language: str = "python") -> str:
        """Review code in the given language."""
        return f"Reviewing {language} code..."

    gc.disable()
    start = time.perf_counter()
    for i in range(n):
        ResourceHandler.from_function(f"config://item-{i}", get_config)
    elapsed_res = time.perf_counter() - start
    gc.enable()
    _report("ResourceHandler.from_function", n, elapsed_res)

    gc.disable()
    start = time.perf_counter()
    for _ in range(n):
        PromptHandler.from_function(code_review)
    elapsed_prompt = time.perf_counter() - start
    gc.enable()
    _report("PromptHandler.from_function", n, elapsed_prompt)


# ============================================================================
# 4. Protocol handler benchmark (in-process, no HTTP)
# ============================================================================
async def bench_protocol(n_ops: int = 2_000) -> None:
    _banner("Protocol handler (in-process, no transport)")
    from chuk_mcp_server.core import ChukMCPServer

    server = ChukMCPServer(name="bench-server", version="1.0.0")

    @server.tool(name="bench_add", read_only_hint=True)
    def bench_add(a: int, b: int) -> int:
        return a + b

    @server.tool(name="bench_echo", meta={"ui": {"resourceUri": "https://example.com"}})
    def bench_echo(message: str) -> str:
        return message

    @server.resource("config://bench")
    def bench_config() -> dict:
        return {"name": "bench", "version": "1.0"}

    protocol = server.protocol

    # Initialize a session
    init_msg: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": "init-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "benchmark", "version": "1.0"},
        },
    }
    _, session_id = await protocol.handle_request(init_msg)

    # --- tools/list ---
    tools_list_msg: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": "tl-1",
        "method": "tools/list",
        "params": {},
    }

    latencies: list[float] = []
    gc.disable()
    start = time.perf_counter()
    for i in range(n_ops):
        t0 = time.perf_counter()
        await protocol.handle_request({**tools_list_msg, "id": f"tl-{i}"}, session_id)
        latencies.append(time.perf_counter() - t0)
    elapsed = time.perf_counter() - start
    gc.enable()
    _report("tools/list", n_ops, elapsed, latencies)

    # --- tools/call ---
    call_msg: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": "tc-1",
        "method": "tools/call",
        "params": {"name": "bench_add", "arguments": {"a": 3, "b": 7}},
    }

    latencies = []
    gc.disable()
    start = time.perf_counter()
    for i in range(n_ops):
        t0 = time.perf_counter()
        await protocol.handle_request({**call_msg, "id": f"tc-{i}"}, session_id)
        latencies.append(time.perf_counter() - t0)
    elapsed = time.perf_counter() - start
    gc.enable()
    _report("tools/call (bench_add)", n_ops, elapsed, latencies)

    # --- tools/call with meta tool ---
    echo_msg: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": "ec-1",
        "method": "tools/call",
        "params": {"name": "bench_echo", "arguments": {"message": "hello"}},
    }

    latencies = []
    gc.disable()
    start = time.perf_counter()
    for i in range(n_ops):
        t0 = time.perf_counter()
        await protocol.handle_request({**echo_msg, "id": f"ec-{i}"}, session_id)
        latencies.append(time.perf_counter() - t0)
    elapsed = time.perf_counter() - start
    gc.enable()
    _report("tools/call (bench_echo+meta)", n_ops, elapsed, latencies)

    # --- resources/list ---
    res_list_msg: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": "rl-1",
        "method": "resources/list",
        "params": {},
    }

    latencies = []
    gc.disable()
    start = time.perf_counter()
    for i in range(n_ops):
        t0 = time.perf_counter()
        await protocol.handle_request({**res_list_msg, "id": f"rl-{i}"}, session_id)
        latencies.append(time.perf_counter() - t0)
    elapsed = time.perf_counter() - start
    gc.enable()
    _report("resources/list", n_ops, elapsed, latencies)

    # --- resources/read ---
    res_read_msg: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": "rr-1",
        "method": "resources/read",
        "params": {"uri": "config://bench"},
    }

    latencies = []
    gc.disable()
    start = time.perf_counter()
    for i in range(n_ops):
        t0 = time.perf_counter()
        await protocol.handle_request({**res_read_msg, "id": f"rr-{i}"}, session_id)
        latencies.append(time.perf_counter() - t0)
    elapsed = time.perf_counter() - start
    gc.enable()
    _report("resources/read", n_ops, elapsed, latencies)

    # --- ping ---
    ping_msg: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": "p-1",
        "method": "ping",
        "params": {},
    }

    latencies = []
    gc.disable()
    start = time.perf_counter()
    for i in range(n_ops):
        t0 = time.perf_counter()
        await protocol.handle_request({**ping_msg, "id": f"p-{i}"}, session_id)
        latencies.append(time.perf_counter() - t0)
    elapsed = time.perf_counter() - start
    gc.enable()
    _report("ping", n_ops, elapsed, latencies)


# ============================================================================
# Main
# ============================================================================
def main() -> None:
    print("=" * 60)
    print("  chuk-mcp-server In-Process Performance Benchmark")
    print("  No HTTP server needed — measures core framework paths")
    print("=" * 60)

    bench_tool_creation()
    bench_serialization()
    bench_resource_prompt_creation()
    asyncio.run(bench_protocol())

    print(f"\n{'=' * 60}")
    print("  Benchmark complete")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
