# Framework Comparison

How ChukMCPServer compares to alternatives.

## Performance

ChukMCPServer achieves:
- **36,000+ RPS** peak throughput
- **<3ms** average latency
- **100%** success rate under load

## vs Official MCP SDK

- **Performance**: ChukMCPServer optimized for throughput
- **Features**: Built-in OAuth 2.1, cloud detection
- **Developer UX**: Decorator-based API

## vs FastMCP

- **Performance**: Further optimized JSON-RPC path
- **OAuth**: Built-in OAuth 2.1 support
- **Cloud**: Auto-detection and adapters

## vs Typical Frameworks

Most add 5-50ms overhead per tool call.
ChukMCPServer delivers <3ms through:
- Async I/O
- Pre-serialization
- uvloop optimization

## Next Steps

- [Benchmarks](benchmarks.md) - Detailed results
- [Optimization](optimization.md) - Tuning guide
- [Getting Started](../getting-started/installation.md) - Try it
