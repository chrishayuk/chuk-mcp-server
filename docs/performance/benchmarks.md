# Performance Benchmarks

ChukMCPServer achieves world-class performance across all protocol operations.

## In-Process Protocol Benchmarks

Core framework paths measured without HTTP transport overhead. These numbers represent the raw throughput of the protocol handler.

### Protocol Operations

| Operation | Throughput | Avg Latency | p95 Latency |
|-----------|-----------|-------------|-------------|
| ping | 1,027,771 ops/s | 0.9 us | 1.0 us |
| resources/list | 558,191 ops/s | 1.7 us | 2.1 us |
| resources/read | 483,749 ops/s | 2.0 us | 2.2 us |
| tools/list | 377,270 ops/s | 2.6 us | 2.7 us |
| tools/call (echo+meta) | 83,014 ops/s | 12.0 us | 15.7 us |
| tools/call (add) | 76,089 ops/s | 13.1 us | 16.4 us |

### Handler Creation and Serialization

| Operation | Throughput |
|-----------|-----------|
| to_mcp_bytes (cached) | 26,588,970 ops/s |
| to_mcp_format (cached dict) | 1,442,083 ops/s |
| ResourceHandler.from_function | 460,354 ops/s |
| PromptHandler.from_function | 152,989 ops/s |
| ToolHandler.from_function | 72,093 ops/s |

### Key Observations

- **Sub-microsecond ping**: Protocol dispatch overhead is under 1 us
- **Cached serialization**: orjson byte caching delivers 26M+ ops/s for repeated serialization
- **Tool call overhead**: ~13 us per call includes task auto-wiring, argument parsing, result formatting
- **List operations**: 377K-558K ops/s for schema listing with pre-cached responses

## HTTP Transport Benchmarks

End-to-end performance including HTTP transport (Starlette/Uvicorn).

| Metric | Value |
|--------|-------|
| Peak Throughput | 36,348 RPS |
| Average Latency | 2.74 ms |
| p50 Latency | 2-3 ms |
| p95 Latency | 5-6 ms |
| Success Rate | 100% |

## Test Setup

- **Hardware**: MacBook Pro M2 Pro
- **Python**: 3.11.10
- **In-process**: No transport, direct protocol handler calls
- **HTTP**: Starlette/Uvicorn, 100 concurrent connections, 60s duration with 10s warmup

## Run Benchmarks

```bash
# In-process benchmark (no server needed)
python benchmarks/in_process_benchmark.py

# HTTP benchmark (starts server automatically)
python benchmarks/quick_benchmark.py
```

## Next Steps

- [Optimization Guide](optimization.md) - Improve performance
- [Comparison](comparison.md) - vs other frameworks
- [HTTP Mode](../deployment/http-mode.md) - Configuration
