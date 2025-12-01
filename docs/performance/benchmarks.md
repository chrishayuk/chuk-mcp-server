# Performance Benchmarks

ChukMCPServer achieves world-class performance.

## Results

| Metric | Value |
|--------|-------|
| Peak Throughput | 36,348 RPS |
| Average Latency | 2.74ms |
| p50 Latency | 2-3ms |
| p95 Latency | 5-6ms |
| Success Rate | 100% |

## Test Setup

- **Transport**: HTTP + SSE
- **Hardware**: MacBook Pro M2 Pro
- **Python**: 3.11.10
- **Concurrency**: 100 connections
- **Duration**: 60s with 10s warmup

## Run Benchmarks

```bash
python benchmarks/ultra_minimal_mcp_performance_test.py
```

## Next Steps

- [Optimization Guide](optimization.md) - Improve performance
- [Comparison](comparison.md) - vs other frameworks
- [HTTP Mode](../deployment/http-mode.md) - Configuration
