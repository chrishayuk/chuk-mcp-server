#!/usr/bin/env python3
"""
Lightweight ChukMCPServer Performance Test with httpx

Ultra-minimal performance test designed to NOT bottleneck the server.
Uses httpx for modern async HTTP, minimal allocations, and optimized request patterns.

Target: Measure true server performance without client-side limitations.
Expected: 20,000+ RPS for ping, 15,000+ RPS for version, 10,000+ RPS for MCP calls.
"""

import asyncio
import httpx
import time
import json
import statistics
import sys
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import gc


@dataclass
class PerfResult:
    """Minimal performance result"""

    name: str
    rps: float
    avg_ms: float
    min_ms: float
    max_ms: float
    p95_ms: float
    success_rate: float
    total_requests: int


class LightweightPerfTest:
    """Ultra-lightweight performance test with httpx - minimal overhead"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")
        self.mcp_url = f"{self.base_url}/mcp"
        self.session_id = None

        # Optimized httpx limits for high performance
        self.limits = httpx.Limits(max_keepalive_connections=1000, max_connections=2000, keepalive_expiry=300.0)

        # Pre-built requests to avoid JSON encoding overhead
        self.ping_request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}).encode("utf-8")

        self.tools_list_request = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}).encode(
            "utf-8"
        )

    async def run_lightweight_tests(self):
        """Run lightweight performance tests with httpx"""
        print("🚀 ChukMCPServer Lightweight Performance Test (httpx)")
        print("=" * 60)
        print("Designed for MINIMAL client overhead to measure true server performance")
        print()

        async with httpx.AsyncClient(
            limits=self.limits,
            timeout=30.0,
            http2=False,  # HTTP/1.1 for better connection reuse
            headers={"User-Agent": "LightweightPerfTest-httpx/1.0"},
        ) as client:
            # Verify server availability
            if not await self._check_server(client):
                print("❌ Server not available")
                return False

            # Initialize MCP session if possible
            await self._init_mcp_session(client)

            # Run core performance tests
            results = []

            # Test 1: HTTP Ping (should be fastest)
            print("🏓 Testing HTTP Ping endpoint...")
            ping_result = await self._test_http_endpoint(client, "/ping", "HTTP Ping", duration=5.0, concurrency=500)
            results.append(ping_result)
            print(
                f"   {ping_result.rps:>8,.0f} RPS | {ping_result.avg_ms:>6.2f}ms avg | {ping_result.success_rate:>5.1f}% success"
            )

            # Test 2: HTTP Version (cached response)
            print("📋 Testing HTTP Version endpoint...")
            version_result = await self._test_http_endpoint(
                client, "/version", "HTTP Version", duration=5.0, concurrency=500
            )
            results.append(version_result)
            print(
                f"   {version_result.rps:>8,.0f} RPS | {version_result.avg_ms:>6.2f}ms avg | {version_result.success_rate:>5.1f}% success"
            )

            # Test 3: HTTP Health
            print("🏥 Testing HTTP Health endpoint...")
            health_result = await self._test_http_endpoint(
                client, "/health", "HTTP Health", duration=5.0, concurrency=500
            )
            results.append(health_result)
            print(
                f"   {health_result.rps:>8,.0f} RPS | {health_result.avg_ms:>6.2f}ms avg | {health_result.success_rate:>5.1f}% success"
            )

            # Test 4: MCP Ping (JSON-RPC)
            if self.session_id:
                print("🎯 Testing MCP Ping (JSON-RPC)...")
                mcp_ping_result = await self._test_mcp_ping(client, duration=5.0, concurrency=200)
                results.append(mcp_ping_result)
                print(
                    f"   {mcp_ping_result.rps:>8,.0f} RPS | {mcp_ping_result.avg_ms:>6.2f}ms avg | {mcp_ping_result.success_rate:>5.1f}% success"
                )

                # Test 5: MCP Tools List
                print("🔧 Testing MCP Tools List...")
                tools_result = await self._test_mcp_tools_list(client, duration=5.0, concurrency=200)
                results.append(tools_result)
                print(
                    f"   {tools_result.rps:>8,.0f} RPS | {tools_result.avg_ms:>6.2f}ms avg | {tools_result.success_rate:>5.1f}% success"
                )

            # Test 6: Async-specific tool tests
            if self.session_id:
                print("\n🌊 Testing Async-Native Tools...")
                await self._test_async_tools(client)

            # Test 7: Concurrency scaling (ping only)
            print("\n⚡ Testing Concurrency Scaling (HTTP Ping)...")
            await self._test_concurrency_scaling(client)

            # Test 8: Burst performance
            print("\n💥 Testing Burst Performance (1000 requests in parallel)...")
            burst_result = await self._test_burst_performance(client)
            print(
                f"   {burst_result.rps:>8,.0f} RPS | {burst_result.avg_ms:>6.2f}ms avg | {burst_result.success_rate:>5.1f}% success"
            )

            # Generate summary
            self._print_performance_summary(results + [burst_result])

        return True

    async def _check_server(self, client: httpx.AsyncClient) -> bool:
        """Quick server availability check"""
        try:
            response = await client.get(f"{self.base_url}/ping", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def _init_mcp_session(self, client: httpx.AsyncClient):
        """Initialize MCP session for protocol tests"""
        try:
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "lightweight-test-httpx", "version": "1.0.0"},
                },
            }

            response = await client.post(self.mcp_url, json=init_message)
            if response.status_code == 200:
                self.session_id = response.headers.get("Mcp-Session-Id")

                # Send initialized notification
                if self.session_id:
                    headers = {"Mcp-Session-Id": self.session_id}
                    notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
                    await client.post(self.mcp_url, json=notif, headers=headers)
        except Exception:
            pass  # MCP not available, skip protocol tests

    async def _test_http_endpoint(
        self, client: httpx.AsyncClient, path: str, name: str, duration: float = 5.0, concurrency: int = 500
    ) -> PerfResult:
        """Test HTTP endpoint with minimal overhead using httpx"""

        url = f"{self.base_url}{path}"
        times = []
        successes = 0
        failures = 0

        async def worker():
            worker_times = []
            worker_successes = 0
            worker_failures = 0

            end_time = time.time() + duration

            while time.time() < end_time:
                start = time.time()
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        worker_successes += 1
                    else:
                        worker_failures += 1
                    # Response content is automatically consumed by httpx
                except Exception:
                    worker_failures += 1

                worker_times.append(time.time() - start)

            return worker_times, worker_successes, worker_failures

        # Run workers
        start_time = time.time()
        worker_results = await asyncio.gather(*[worker() for _ in range(concurrency)])
        actual_duration = time.time() - start_time

        # Aggregate results
        for worker_times, worker_successes, worker_failures in worker_results:
            times.extend(worker_times)
            successes += worker_successes
            failures += worker_failures

        # Calculate metrics
        total_requests = successes + failures
        rps = total_requests / actual_duration if actual_duration > 0 else 0
        success_rate = (successes / total_requests * 100) if total_requests > 0 else 0

        if times:
            avg_ms = statistics.mean(times) * 1000
            min_ms = min(times) * 1000
            max_ms = max(times) * 1000
            sorted_times = sorted(times)
            p95_ms = sorted_times[int(len(sorted_times) * 0.95)] * 1000
        else:
            avg_ms = min_ms = max_ms = p95_ms = 0

        return PerfResult(
            name=name,
            rps=rps,
            avg_ms=avg_ms,
            min_ms=min_ms,
            max_ms=max_ms,
            p95_ms=p95_ms,
            success_rate=success_rate,
            total_requests=total_requests,
        )

    async def _test_mcp_ping(
        self, client: httpx.AsyncClient, duration: float = 5.0, concurrency: int = 200
    ) -> PerfResult:
        """Test MCP ping with pre-built requests using httpx"""

        times = []
        successes = 0
        failures = 0

        headers = (
            {"Content-Type": "application/json", "Mcp-Session-Id": self.session_id}
            if self.session_id
            else {"Content-Type": "application/json"}
        )

        async def worker():
            worker_times = []
            worker_successes = 0
            worker_failures = 0

            end_time = time.time() + duration

            while time.time() < end_time:
                start = time.time()
                try:
                    response = await client.post(
                        self.mcp_url,
                        content=self.ping_request,  # Pre-encoded bytes
                        headers=headers,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if "result" in data or "error" not in data:
                            worker_successes += 1
                        else:
                            worker_failures += 1
                    else:
                        worker_failures += 1
                except Exception:
                    worker_failures += 1

                worker_times.append(time.time() - start)

            return worker_times, worker_successes, worker_failures

        # Run workers
        start_time = time.time()
        worker_results = await asyncio.gather(*[worker() for _ in range(concurrency)])
        actual_duration = time.time() - start_time

        # Aggregate results
        for worker_times, worker_successes, worker_failures in worker_results:
            times.extend(worker_times)
            successes += worker_successes
            failures += worker_failures

        # Calculate metrics
        total_requests = successes + failures
        rps = total_requests / actual_duration if actual_duration > 0 else 0
        success_rate = (successes / total_requests * 100) if total_requests > 0 else 0

        if times:
            avg_ms = statistics.mean(times) * 1000
            min_ms = min(times) * 1000
            max_ms = max(times) * 1000
            sorted_times = sorted(times)
            p95_ms = sorted_times[int(len(sorted_times) * 0.95)] * 1000
        else:
            avg_ms = min_ms = max_ms = p95_ms = 0

        return PerfResult(
            name="MCP Ping",
            rps=rps,
            avg_ms=avg_ms,
            min_ms=min_ms,
            max_ms=max_ms,
            p95_ms=p95_ms,
            success_rate=success_rate,
            total_requests=total_requests,
        )

    async def _test_mcp_tools_list(
        self, client: httpx.AsyncClient, duration: float = 5.0, concurrency: int = 200
    ) -> PerfResult:
        """Test MCP tools list with pre-built requests using httpx"""

        times = []
        successes = 0
        failures = 0

        headers = (
            {"Content-Type": "application/json", "Mcp-Session-Id": self.session_id}
            if self.session_id
            else {"Content-Type": "application/json"}
        )

        async def worker():
            worker_times = []
            worker_successes = 0
            worker_failures = 0

            end_time = time.time() + duration

            while time.time() < end_time:
                start = time.time()
                try:
                    response = await client.post(
                        self.mcp_url,
                        content=self.tools_list_request,  # Pre-encoded bytes
                        headers=headers,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if "result" in data and "tools" in data.get("result", {}):
                            worker_successes += 1
                        else:
                            worker_failures += 1
                    else:
                        worker_failures += 1
                except Exception:
                    worker_failures += 1

                worker_times.append(time.time() - start)

            return worker_times, worker_successes, worker_failures

        # Run workers
        start_time = time.time()
        worker_results = await asyncio.gather(*[worker() for _ in range(concurrency)])
        actual_duration = time.time() - start_time

        # Aggregate results
        for worker_times, worker_successes, worker_failures in worker_results:
            times.extend(worker_times)
            successes += worker_successes
            failures += worker_failures

        # Calculate metrics
        total_requests = successes + failures
        rps = total_requests / actual_duration if actual_duration > 0 else 0
        success_rate = (successes / total_requests * 100) if total_requests > 0 else 0

        if times:
            avg_ms = statistics.mean(times) * 1000
            min_ms = min(times) * 1000
            max_ms = max(times) * 1000
            sorted_times = sorted(times)
            p95_ms = sorted_times[int(len(sorted_times) * 0.95)] * 1000
        else:
            avg_ms = min_ms = max_ms = p95_ms = 0

        return PerfResult(
            name="MCP Tools List",
            rps=rps,
            avg_ms=avg_ms,
            min_ms=min_ms,
            max_ms=max_ms,
            p95_ms=p95_ms,
            success_rate=success_rate,
            total_requests=total_requests,
        )

    async def _test_async_tools(self, client: httpx.AsyncClient):
        """Test async-native tools for concurrency benefits"""

        # Test async_hello with minimal delay
        print("   🚀 Testing async_hello (minimal delay)...")
        async_hello_msg = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "async_hello", "arguments": {"name": "PerfTest", "delay": 0.01}},
            }
        ).encode("utf-8")

        result = await self._test_mcp_request(client, async_hello_msg, "Async Hello", concurrency=100, duration=3.0)
        print(f"      {result.rps:>8,.0f} RPS | {result.avg_ms:>6.2f}ms avg | {result.success_rate:>5.1f}% success")

        # Test concurrent_web_requests (should show async benefits)
        print("   🌐 Testing concurrent_web_requests...")
        concurrent_msg = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "concurrent_web_requests",
                    "arguments": {"urls": ["test1", "test2"], "timeout": 3.0},
                },
            }
        ).encode("utf-8")

        result = await self._test_mcp_request(
            client, concurrent_msg, "Concurrent Requests", concurrency=50, duration=3.0
        )
        print(f"      {result.rps:>8,.0f} RPS | {result.avg_ms:>6.2f}ms avg | {result.success_rate:>5.1f}% success")

        # Test stream processing
        print("   🌊 Testing data_stream_processor...")
        stream_msg = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "data_stream_processor",
                    "arguments": {"item_count": 3, "process_delay": 0.01, "batch_size": 2},
                },
            }
        ).encode("utf-8")

        result = await self._test_mcp_request(client, stream_msg, "Stream Processing", concurrency=30, duration=3.0)
        print(f"      {result.rps:>8,.0f} RPS | {result.avg_ms:>6.2f}ms avg | {result.success_rate:>5.1f}% success")

    async def _test_mcp_request(
        self, client: httpx.AsyncClient, request_bytes: bytes, name: str, concurrency: int = 100, duration: float = 3.0
    ) -> PerfResult:
        """Test a specific MCP request with pre-encoded bytes using httpx"""

        times = []
        successes = 0
        failures = 0

        headers = (
            {"Content-Type": "application/json", "Mcp-Session-Id": self.session_id}
            if self.session_id
            else {"Content-Type": "application/json"}
        )

        async def worker():
            worker_times = []
            worker_successes = 0
            worker_failures = 0

            end_time = time.time() + duration

            while time.time() < end_time:
                start = time.time()
                try:
                    response = await client.post(self.mcp_url, content=request_bytes, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if "result" in data and "error" not in data:
                            worker_successes += 1
                        else:
                            worker_failures += 1
                    else:
                        worker_failures += 1
                except Exception:
                    worker_failures += 1

                worker_times.append(time.time() - start)

            return worker_times, worker_successes, worker_failures

        # Run workers
        start_time = time.time()
        worker_results = await asyncio.gather(*[worker() for _ in range(concurrency)])
        actual_duration = time.time() - start_time

        # Aggregate results
        for worker_times, worker_successes, worker_failures in worker_results:
            times.extend(worker_times)
            successes += worker_successes
            failures += worker_failures

        # Calculate metrics
        total_requests = successes + failures
        rps = total_requests / actual_duration if actual_duration > 0 else 0
        success_rate = (successes / total_requests * 100) if total_requests > 0 else 0

        if times:
            avg_ms = statistics.mean(times) * 1000
            min_ms = min(times) * 1000
            max_ms = max(times) * 1000
            sorted_times = sorted(times)
            p95_ms = sorted_times[int(len(sorted_times) * 0.95)] * 1000
        else:
            avg_ms = min_ms = max_ms = p95_ms = 0

        return PerfResult(
            name=name,
            rps=rps,
            avg_ms=avg_ms,
            min_ms=min_ms,
            max_ms=max_ms,
            p95_ms=p95_ms,
            success_rate=success_rate,
            total_requests=total_requests,
        )

    async def _test_concurrency_scaling(self, client: httpx.AsyncClient):
        """Test how performance scales with concurrency using httpx"""
        print("   Concurrency |    RPS     | Avg(ms) | Success%")
        print("   " + "-" * 45)

        concurrency_levels = [1, 5, 10, 25, 50, 100, 200, 500, 1000]
        url = f"{self.base_url}/ping"

        for concurrency in concurrency_levels:
            times = []
            successes = 0
            failures = 0

            async def worker():
                worker_times = []
                worker_successes = 0
                worker_failures = 0

                end_time = time.time() + 3.0  # Short test

                while time.time() < end_time:
                    start = time.time()
                    try:
                        response = await client.get(url)
                        if response.status_code == 200:
                            worker_successes += 1
                        else:
                            worker_failures += 1
                    except Exception:
                        worker_failures += 1

                    worker_times.append(time.time() - start)

                return worker_times, worker_successes, worker_failures

            # Run test
            start_time = time.time()
            worker_results = await asyncio.gather(*[worker() for _ in range(concurrency)])
            actual_duration = time.time() - start_time

            # Aggregate
            for worker_times, worker_successes, worker_failures in worker_results:
                times.extend(worker_times)
                successes += worker_successes
                failures += worker_failures

            total_requests = successes + failures
            rps = total_requests / actual_duration if actual_duration > 0 else 0
            success_rate = (successes / total_requests * 100) if total_requests > 0 else 0
            avg_ms = statistics.mean(times) * 1000 if times else 0

            print(f"   {concurrency:>10} | {rps:>8,.0f} | {avg_ms:>6.1f} | {success_rate:>6.1f}%")

            # Stop if performance degrades badly
            if success_rate < 80:
                print("   (Stopping due to high failure rate)")
                break

            # Brief pause between tests
            await asyncio.sleep(0.5)

    async def _test_burst_performance(self, client: httpx.AsyncClient) -> PerfResult:
        """Test burst performance - fire all requests simultaneously using httpx"""

        url = f"{self.base_url}/ping"
        burst_size = 1000

        async def single_request():
            start = time.time()
            try:
                response = await client.get(url)
                success = response.status_code == 200
            except Exception:
                success = False

            return time.time() - start, success

        # Fire all requests simultaneously
        start_time = time.time()
        results = await asyncio.gather(*[single_request() for _ in range(burst_size)])
        actual_duration = time.time() - start_time

        # Process results
        times = [r[0] for r in results]
        successes = sum(1 for r in results if r[1])
        failures = burst_size - successes

        rps = burst_size / actual_duration if actual_duration > 0 else 0
        success_rate = successes / burst_size * 100

        if times:
            avg_ms = statistics.mean(times) * 1000
            min_ms = min(times) * 1000
            max_ms = max(times) * 1000
            sorted_times = sorted(times)
            p95_ms = sorted_times[int(len(sorted_times) * 0.95)] * 1000
        else:
            avg_ms = min_ms = max_ms = p95_ms = 0

        return PerfResult(
            name="Burst Test",
            rps=rps,
            avg_ms=avg_ms,
            min_ms=min_ms,
            max_ms=max_ms,
            p95_ms=p95_ms,
            success_rate=success_rate,
            total_requests=burst_size,
        )

    def _print_performance_summary(self, results: List[PerfResult]):
        """Print comprehensive performance summary"""
        print("\n" + "=" * 60)
        print("📊 LIGHTWEIGHT PERFORMANCE TEST RESULTS (httpx)")
        print("=" * 60)

        # Find best performers
        best_rps = max(results, key=lambda r: r.rps)
        best_latency = min(results, key=lambda r: r.avg_ms)

        print(f"🚀 Peak Performance:")
        print(f"   Best RPS: {best_rps.rps:>10,.0f} ({best_rps.name})")
        print(f"   Best Latency: {best_latency.avg_ms:>7.2f}ms ({best_latency.name})")

        # Performance analysis
        total_requests = sum(r.total_requests for r in results)
        avg_success_rate = statistics.mean([r.success_rate for r in results])

        print(f"\n📈 Overall Statistics:")
        print(f"   Total Requests: {total_requests:>10,}")
        print(f"   Avg Success Rate: {avg_success_rate:>8.1f}%")
        print(f"   Tests Completed: {len(results):>9}")
        print(f"   HTTP Client: httpx (modern async)")

        # Detailed results table
        print(f"\n📋 Detailed Results:")
        print("   Test Name          |    RPS     | Avg(ms) | P95(ms) | Success%")
        print("   " + "-" * 65)

        for result in results:
            print(
                f"   {result.name:<18} | {result.rps:>8,.0f} | {result.avg_ms:>6.1f} | "
                f"{result.p95_ms:>6.1f} | {result.success_rate:>6.1f}%"
            )

        # Performance grading
        if best_rps.rps > 20000:
            grade = "S++ (Outstanding)"
            emoji = "🏆"
        elif best_rps.rps > 15000:
            grade = "S+ (Exceptional)"
            emoji = "🌟"
        elif best_rps.rps > 10000:
            grade = "S (Excellent)"
            emoji = "🚀"
        elif best_rps.rps > 5000:
            grade = "A (Very Good)"
            emoji = "✅"
        elif best_rps.rps > 1000:
            grade = "B (Good)"
            emoji = "👍"
        else:
            grade = "C (Needs Work)"
            emoji = "⚠️"

        print(f"\n{emoji} Performance Grade: {grade}")

        # httpx specific benefits
        print(f"\n⚡ httpx Benefits:")
        print("   ✅ Modern async HTTP client")
        print("   ✅ Automatic connection pooling")
        print("   ✅ Built-in response streaming")
        print("   ✅ Lower memory overhead")

        # Recommendations
        print(f"\n💡 Analysis:")
        if best_rps.rps > 15000 and avg_success_rate > 99:
            print("   🎉 Exceptional performance! Your server + httpx combo is outstanding.")
            print("   🔥 This is reference-level high-performance MCP implementation.")
        elif best_rps.rps > 10000 and avg_success_rate > 95:
            print("   ✅ Excellent performance! Great async server + httpx synergy.")
            print("   🚀 You've achieved production-grade high-performance MCP.")
        elif best_rps.rps > 5000:
            print("   👍 Good performance. Consider async tool optimizations.")
            print("   🔍 Profile async tool execution paths for improvements.")
        else:
            print("   ⚠️  Performance could be improved.")
            print("   🛠️  Check for blocking operations in async tool handlers.")

        print("\n" + "=" * 60)


async def main():
    """Main entry point"""
    base_url = "http://localhost:8001"  # Default to async server port

    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    print("⚡ ChukMCPServer Lightweight Performance Test (httpx)")
    print(f"🎯 Target URL: {base_url}")
    print("📝 Minimal client overhead with modern httpx to measure true server performance")
    print()

    # Force garbage collection before testing
    gc.collect()

    test = LightweightPerfTest(base_url)

    try:
        success = await test.run_lightweight_tests()

        if success:
            print("🎉 Lightweight performance testing with httpx completed!")
        else:
            print("❌ Performance testing failed. Check server status.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Test error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Optimize event loop for performance testing
    import platform

    if platform.system() != "Windows":
        try:
            import uvloop

            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            print("🚀 Using uvloop for maximum performance")
        except ImportError:
            print("⚠️  uvloop not available, using default event loop")

    asyncio.run(main())
