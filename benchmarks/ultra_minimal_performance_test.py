#!/usr/bin/env python3
"""
Ultra-Minimal ChukMCPServer Performance Test

Designed to eliminate ALL client-side bottlenecks and measure true server performance.
Uses raw socket connections, minimal Python overhead, and optimized patterns.

Target: Match AB performance - 20,000+ RPS for simple endpoints.
"""

import asyncio
import time
import socket
import statistics
import sys
from dataclasses import dataclass
from typing import List, Optional
import gc


@dataclass
class UltraResult:
    """Ultra-minimal performance result"""

    name: str
    rps: float
    avg_ms: float
    min_ms: float
    max_ms: float
    success_rate: float
    total_requests: int


class UltraMinimalPerfTest:
    """Ultra-minimal performance test - zero client overhead"""

    def __init__(self, host: str = "localhost", port: int = 8001):
        self.host = host
        self.port = port

        # Pre-built HTTP requests as bytes (no encoding overhead)
        self.ping_request = (
            f"GET /ping HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Connection: keep-alive\r\n"
            f"User-Agent: UltraMinimal/1.0\r\n"
            f"\r\n"
        ).encode("ascii")

        self.version_request = (
            f"GET /version HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Connection: keep-alive\r\n"
            f"User-Agent: UltraMinimal/1.0\r\n"
            f"\r\n"
        ).encode("ascii")

        self.health_request = (
            f"GET /health HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Connection: keep-alive\r\n"
            f"User-Agent: UltraMinimal/1.0\r\n"
            f"\r\n"
        ).encode("ascii")

    async def run_ultra_minimal_tests(self):
        """Run ultra-minimal performance tests"""
        print("🚀 ChukMCPServer Ultra-Minimal Performance Test")
        print("=" * 60)
        print("ZERO client overhead - raw sockets + pre-built requests")
        print("Target: Match AB performance levels (20,000+ RPS)")
        print()

        # Test server availability first
        if not await self._check_server():
            print("❌ Server not available")
            return False

        results = []

        # Test 1: Single connection performance baseline
        print("🎯 Single Connection Baseline Tests...")
        ping_single = await self._test_single_connection("/ping", self.ping_request, duration=3.0)
        print(f"   Ping (1 conn): {ping_single.rps:>8,.0f} RPS | {ping_single.avg_ms:>6.2f}ms avg")

        # Test 2: Multi-connection HTTP Ping (like AB)
        print("\n🏓 Multi-Connection HTTP Ping (AB-style)...")
        for concurrency in [10, 50, 100, 200, 500]:
            result = await self._test_raw_http_endpoint(
                self.ping_request, "HTTP Ping", concurrency=concurrency, duration=5.0
            )
            print(
                f"   {concurrency:>3} conn: {result.rps:>8,.0f} RPS | {result.avg_ms:>6.2f}ms avg | {result.success_rate:>5.1f}% success"
            )

            # Stop if we hit the sweet spot or performance degrades
            if result.rps > 15000 or result.success_rate < 95:
                results.append(result)
                break
            results.append(result)

        # Test 3: Version endpoint (cached)
        print("\n📋 Multi-Connection HTTP Version...")
        version_result = await self._test_raw_http_endpoint(
            self.version_request, "HTTP Version", concurrency=200, duration=5.0
        )
        results.append(version_result)
        print(
            f"   200 conn: {version_result.rps:>8,.0f} RPS | {version_result.avg_ms:>6.2f}ms avg | {version_result.success_rate:>5.1f}% success"
        )

        # Test 4: Health endpoint (dynamic)
        print("\n🏥 Multi-Connection HTTP Health...")
        health_result = await self._test_raw_http_endpoint(
            self.health_request, "HTTP Health", concurrency=200, duration=5.0
        )
        results.append(health_result)
        print(
            f"   200 conn: {health_result.rps:>8,.0f} RPS | {health_result.avg_ms:>6.2f}ms avg | {health_result.success_rate:>5.1f}% success"
        )

        # Test 5: Maximum throughput test
        print("\n🚀 Maximum Throughput Test...")
        max_result = await self._find_maximum_throughput()
        results.append(max_result)
        print(f"   Max throughput: {max_result.rps:>8,.0f} RPS with {max_result.total_requests // 5} connections")

        # Summary
        self._print_ultra_summary(results)

        return True

    async def _check_server(self) -> bool:
        """Quick server availability check with raw socket"""
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
            writer.write(self.ping_request)
            await writer.drain()

            response = await reader.read(1024)
            writer.close()
            await writer.wait_closed()

            return b"HTTP/1.1 200" in response
        except Exception:
            return False

    async def _test_single_connection(self, path: str, request_bytes: bytes, duration: float = 3.0) -> UltraResult:
        """Test with single persistent connection"""
        times = []
        successes = 0
        failures = 0

        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)

            end_time = time.time() + duration

            while time.time() < end_time:
                start = time.time()

                try:
                    writer.write(request_bytes)
                    await writer.drain()

                    # Read response
                    response = await reader.read(4096)

                    if b"HTTP/1.1 200" in response:
                        successes += 1
                    else:
                        failures += 1

                    times.append(time.time() - start)

                except Exception:
                    failures += 1
                    times.append(time.time() - start)

            writer.close()
            await writer.wait_closed()

        except Exception:
            failures += 1

        # Calculate metrics
        total_requests = successes + failures
        actual_duration = max(times) if times else duration
        rps = total_requests / duration if duration > 0 else 0
        success_rate = (successes / total_requests * 100) if total_requests > 0 else 0

        if times:
            avg_ms = statistics.mean(times) * 1000
            min_ms = min(times) * 1000
            max_ms = max(times) * 1000
        else:
            avg_ms = min_ms = max_ms = 0

        return UltraResult(
            name=f"Single {path}",
            rps=rps,
            avg_ms=avg_ms,
            min_ms=min_ms,
            max_ms=max_ms,
            success_rate=success_rate,
            total_requests=total_requests,
        )

    async def _test_raw_http_endpoint(
        self, request_bytes: bytes, name: str, concurrency: int = 100, duration: float = 5.0
    ) -> UltraResult:
        """Test with multiple raw socket connections (AB-style)"""

        async def worker():
            worker_times = []
            worker_successes = 0
            worker_failures = 0

            try:
                reader, writer = await asyncio.open_connection(self.host, self.port)

                end_time = time.time() + duration

                while time.time() < end_time:
                    start = time.time()

                    try:
                        writer.write(request_bytes)
                        await writer.drain()

                        # Read response efficiently
                        response = await reader.read(4096)

                        if b"HTTP/1.1 200" in response:
                            worker_successes += 1
                        else:
                            worker_failures += 1

                        worker_times.append(time.time() - start)

                    except Exception:
                        worker_failures += 1
                        worker_times.append(time.time() - start)

                writer.close()
                await writer.wait_closed()

            except Exception:
                worker_failures += 1

            return worker_times, worker_successes, worker_failures

        # Run workers concurrently
        start_time = time.time()
        worker_results = await asyncio.gather(*[worker() for _ in range(concurrency)])
        actual_duration = time.time() - start_time

        # Aggregate results
        all_times = []
        total_successes = 0
        total_failures = 0

        for worker_times, worker_successes, worker_failures in worker_results:
            all_times.extend(worker_times)
            total_successes += worker_successes
            total_failures += worker_failures

        # Calculate metrics
        total_requests = total_successes + total_failures
        rps = total_requests / actual_duration if actual_duration > 0 else 0
        success_rate = (total_successes / total_requests * 100) if total_requests > 0 else 0

        if all_times:
            avg_ms = statistics.mean(all_times) * 1000
            min_ms = min(all_times) * 1000
            max_ms = max(all_times) * 1000
        else:
            avg_ms = min_ms = max_ms = 0

        return UltraResult(
            name=name,
            rps=rps,
            avg_ms=avg_ms,
            min_ms=min_ms,
            max_ms=max_ms,
            success_rate=success_rate,
            total_requests=total_requests,
        )

    async def _find_maximum_throughput(self) -> UltraResult:
        """Find maximum sustainable throughput"""
        print("   Searching for maximum throughput...")

        best_rps = 0
        best_concurrency = 100
        best_result = None

        # Test different concurrency levels
        for concurrency in [50, 100, 200, 500, 1000, 1500, 2000]:
            print(f"     Testing {concurrency:>4} connections...", end=" ", flush=True)

            result = await self._test_raw_http_endpoint(
                self.ping_request, f"Max Test ({concurrency})", concurrency=concurrency, duration=3.0
            )

            print(f"{result.rps:>8,.0f} RPS ({result.success_rate:>5.1f}% success)")

            # Track best performance with good success rate
            if result.success_rate >= 95 and result.rps > best_rps:
                best_rps = result.rps
                best_concurrency = concurrency
                best_result = result

            # Stop if success rate drops too much
            if result.success_rate < 80:
                print(f"     Stopping at {concurrency} connections due to low success rate")
                break

        return best_result or UltraResult("Max Test", 0, 0, 0, 0, 0, 0)

    def _print_ultra_summary(self, results: List[UltraResult]):
        """Print ultra-minimal summary"""
        print("\n" + "=" * 60)
        print("📊 ULTRA-MINIMAL PERFORMANCE RESULTS")
        print("=" * 60)

        if not results:
            print("❌ No results to show")
            return

        # Find best result
        best_result = max(results, key=lambda r: r.rps)

        print(f"🚀 Maximum Performance Achieved:")
        print(f"   Peak RPS: {best_result.rps:>12,.0f}")
        print(f"   Avg Latency: {best_result.avg_ms:>9.2f}ms")
        print(f"   Success Rate: {best_result.success_rate:>8.1f}%")
        print(f"   Test: {best_result.name}")

        # Detailed results
        print(f"\n📋 All Test Results:")
        print("   Test Name               |    RPS     | Avg(ms) | Success%")
        print("   " + "-" * 60)

        for result in results:
            print(f"   {result.name:<23} | {result.rps:>8,.0f} | {result.avg_ms:>6.1f} | {result.success_rate:>6.1f}%")

        # Compare to AB baseline
        print(f"\n🔍 Performance Analysis:")
        if best_result.rps > 20000:
            print("   🏆 EXCELLENT! Matches high-performance expectations")
            print("   🚀 Your server optimizations are working perfectly")
        elif best_result.rps > 15000:
            print("   ✅ VERY GOOD! Strong performance achieved")
            print("   💪 Server optimizations showing good results")
        elif best_result.rps > 10000:
            print("   👍 GOOD performance, room for improvement")
            print("   🔧 Consider profiling request handling path")
        elif best_result.rps > 5000:
            print("   ⚠️  MODERATE performance")
            print("   🛠️  Check for bottlenecks in request processing")
        else:
            print("   ❌ LOW performance - investigation needed")
            print("   🔍 Significant bottlenecks present")

        # AB comparison
        print(f"\n📊 Comparison Notes:")
        print(f"   AB baseline: ~26,000 RPS (reported)")
        print(f"   Ultra test: {best_result.rps:>8,.0f} RPS (achieved)")

        if best_result.rps > 20000:
            ratio = best_result.rps / 26000 * 100
            print(f"   Efficiency: {ratio:>8.1f}% of AB performance")
            print("   🎯 Client overhead eliminated successfully!")
        else:
            print("   🔍 Gap suggests server-side optimization opportunities")

        print("\n" + "=" * 60)


async def main():
    """Main entry point"""
    host = "localhost"
    port = 8001

    if len(sys.argv) > 1:
        if ":" in sys.argv[1]:
            url = sys.argv[1].replace("http://", "").replace("https://", "")
            if ":" in url:
                host, port_str = url.split(":", 1)
                port = int(port_str.split("/")[0])
        else:
            port = int(sys.argv[1])

    print("⚡ ChukMCPServer Ultra-Minimal Performance Test")
    print(f"🎯 Target: {host}:{port}")
    print("📝 Zero client overhead - raw sockets + pre-built requests")
    print("🏆 Goal: Match AB performance levels")
    print()

    # Optimize for maximum performance
    gc.collect()
    gc.disable()  # Disable GC during testing

    test = UltraMinimalPerfTest(host, port)

    try:
        success = await test.run_ultra_minimal_tests()

        if success:
            print("🎉 Ultra-minimal performance testing completed!")
        else:
            print("❌ Performance testing failed. Check server status.")
            sys.exit(1)

    finally:
        gc.enable()  # Re-enable GC


if __name__ == "__main__":
    # Use the fastest possible event loop
    import platform

    if platform.system() != "Windows":
        try:
            import uvloop

            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            print("🚀 Using uvloop for maximum performance")
        except ImportError:
            print("⚠️  uvloop not available")

    asyncio.run(main())
