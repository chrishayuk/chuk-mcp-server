#!/usr/bin/env python3
"""
Ultra-Minimal MCP Protocol Performance Test

Tests actual MCP JSON-RPC performance with zero client overhead.
Uses raw sockets and pre-built MCP requests.

Target: Measure true MCP protocol performance without client bottlenecks.
Expected: 10,000-20,000+ RPS for MCP operations on your optimized server.

Updated to work with the actual tools from zero_config_examples.py
"""

import asyncio
import gc
import json
import statistics
import sys
import time
from dataclasses import dataclass


@dataclass
class MCPResult:
    """MCP-specific performance result"""

    name: str
    rps: float
    avg_ms: float
    min_ms: float
    max_ms: float
    success_rate: float
    total_requests: int
    mcp_errors: int
    available: bool = True  # Whether resource/tool exists


class UltraMinimalMCPTest:
    """Ultra-minimal MCP protocol performance test"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        duration: float = 5.0,
        max_concurrency: int = 200,
        verbose: bool = False,
    ):
        self.host = host
        self.port = port
        self.session_id = None
        self.duration = duration
        self.max_concurrency = max_concurrency
        self.verbose = verbose

        # Pre-built MCP requests (no encoding overhead)
        self.mcp_initialize = self._build_http_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "ultra-minimal-test", "version": "1.0.0"},
                },
            }
        )

        self.mcp_ping = self._build_http_request({"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}})

        self.mcp_tools_list = self._build_http_request(
            {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}
        )

        self.mcp_resources_list = self._build_http_request(
            {"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}}
        )

        # Tool calls for actual tools from zero_config_examples.py
        self.hello_call = self._build_http_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "hello", "arguments": {"name": "PerfTest"}},
            }
        )

        self.calculate_call = self._build_http_request(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {"name": "calculate", "arguments": {"expression": "2 + 2"}},
            }
        )

        # Resource read for actual resources
        self.settings_resource_read = self._build_http_request(
            {"jsonrpc": "2.0", "id": 7, "method": "resources/read", "params": {"uri": "config://settings"}}
        )

        self.readme_resource_read = self._build_http_request(
            {"jsonrpc": "2.0", "id": 8, "method": "resources/read", "params": {"uri": "docs://readme"}}
        )

    def _build_http_request(self, json_data: dict) -> bytes:
        """Build complete HTTP POST request with JSON body"""
        json_body = json.dumps(json_data)
        content_length = len(json_body.encode("utf-8"))

        http_request = (
            f"POST /mcp HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: keep-alive\r\n"
            f"User-Agent: UltraMinimalMCP/1.0\r\n"
            f"\r\n"
            f"{json_body}"
        )
        return http_request.encode("utf-8")

    def _build_http_request_with_session(self, json_data: dict) -> bytes:
        """Build HTTP request with session ID header"""
        json_body = json.dumps(json_data)
        content_length = len(json_body.encode("utf-8"))

        session_header = f"Mcp-Session-Id: {self.session_id}\r\n" if self.session_id else ""

        http_request = (
            f"POST /mcp HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: keep-alive\r\n"
            f"{session_header}"
            f"User-Agent: UltraMinimalMCP/1.0\r\n"
            f"\r\n"
            f"{json_body}"
        )
        return http_request.encode("utf-8")

    async def run_mcp_performance_tests(self):
        """Run comprehensive MCP protocol performance tests"""
        print("🚀 ChukMCPServer Ultra-Minimal MCP Protocol Test")
        print("=" * 60)
        print("ZERO client overhead - raw sockets + pre-built MCP requests")
        print("Target: Measure true MCP JSON-RPC performance")
        print("Testing actual tools from zero_config_examples.py")
        print()

        # Check MCP server availability
        if not await self._check_mcp_server():
            print("❌ MCP server not available")
            print("💡 Make sure your server is running on the correct port")
            print(f"   Expected: {self.host}:{self.port}")
            return False

        # Initialize MCP session
        if not await self._initialize_mcp_session():
            print("❌ MCP session initialization failed")
            return False

        print(f"✅ MCP session initialized: {self.session_id[:8] if self.session_id else 'No session'}...")
        print()

        # Rebuild requests with session ID
        self._rebuild_requests_with_session()

        results = []

        # Test 1: MCP Ping (basic JSON-RPC)
        print("🎯 Testing MCP Ping (JSON-RPC)...")
        ping_result = await self._test_mcp_operation(
            self.mcp_ping, "MCP Ping", concurrency=self.max_concurrency, duration=self.duration
        )
        results.append(ping_result)
        print(
            f"   {ping_result.rps:>8,.0f} RPS | {ping_result.avg_ms:>6.2f}ms avg | {ping_result.success_rate:>5.1f}% success"
        )

        # Test 2: MCP Tools List
        print("🔧 Testing MCP Tools List...")
        tools_result = await self._test_mcp_operation(
            self.mcp_tools_list, "MCP Tools List", concurrency=self.max_concurrency, duration=self.duration
        )
        results.append(tools_result)
        print(
            f"   {tools_result.rps:>8,.0f} RPS | {tools_result.avg_ms:>6.2f}ms avg | {tools_result.success_rate:>5.1f}% success"
        )

        # Test 3: MCP Resources List
        print("📂 Testing MCP Resources List...")
        resources_result = await self._test_mcp_operation(
            self.mcp_resources_list, "MCP Resources List", concurrency=self.max_concurrency, duration=self.duration
        )
        results.append(resources_result)
        print(
            f"   {resources_result.rps:>8,.0f} RPS | {resources_result.avg_ms:>6.2f}ms avg | {resources_result.success_rate:>5.1f}% success"
        )

        # Test 4: Hello Tool Call (simple sync tool)
        print("👋 Testing Hello Tool Call...")
        hello_result = await self._test_mcp_operation(
            self.hello_call, "Hello Tool Call", concurrency=min(100, self.max_concurrency), duration=self.duration
        )
        results.append(hello_result)
        print(
            f"   {hello_result.rps:>8,.0f} RPS | {hello_result.avg_ms:>6.2f}ms avg | {hello_result.success_rate:>5.1f}% success"
        )

        # Test 5: Calculate Tool Call (simple computation)
        print("🧮 Testing Calculate Tool Call...")
        calc_result = await self._test_mcp_operation(
            self.calculate_call,
            "Calculate Tool Call",
            concurrency=min(100, self.max_concurrency),
            duration=self.duration,
        )
        results.append(calc_result)
        print(
            f"   {calc_result.rps:>8,.0f} RPS | {calc_result.avg_ms:>6.2f}ms avg | {calc_result.success_rate:>5.1f}% success"
        )

        # Test 6: Settings Resource Read (check if available first)
        print("⚙️  Testing Settings Resource Read...", end=" ")
        if await self._check_resource_exists("config://settings"):
            settings_result = await self._test_mcp_operation(
                self.settings_resource_read,
                "Settings Resource Read",
                concurrency=min(100, self.max_concurrency),
                duration=self.duration,
            )
            results.append(settings_result)
            print(
                f"\n   {settings_result.rps:>8,.0f} RPS | {settings_result.avg_ms:>6.2f}ms avg | {settings_result.success_rate:>5.1f}% success"
            )
        else:
            print("N/A (resource not found)")

        # Test 7: README Resource Read (check if available first)
        print("📖 Testing README Resource Read...", end=" ")
        if await self._check_resource_exists("docs://readme"):
            readme_result = await self._test_mcp_operation(
                self.readme_resource_read,
                "README Resource Read",
                concurrency=min(100, self.max_concurrency),
                duration=self.duration,
            )
            results.append(readme_result)
            print(
                f"\n   {readme_result.rps:>8,.0f} RPS | {readme_result.avg_ms:>6.2f}ms avg | {readme_result.success_rate:>5.1f}% success"
            )
        else:
            print("N/A (resource not found)")

        # Test 8: Concurrency scaling for MCP Ping
        print("\n⚡ Testing MCP Ping Concurrency Scaling...")
        await self._test_mcp_concurrency_scaling()

        # Test 9: Maximum MCP throughput
        print("\n🚀 Finding Maximum MCP Throughput...")
        max_mcp_result = await self._find_maximum_mcp_throughput()
        results.append(max_mcp_result)
        print(f"   Max MCP throughput: {max_mcp_result.rps:>8,.0f} RPS")

        # Summary
        self._print_mcp_summary(results)

        return True

    async def _check_mcp_server(self) -> bool:
        """Check if MCP server is available"""
        try:
            # First check basic connectivity
            reader, writer = await asyncio.open_connection(self.host, self.port)

            # Try a simple HTTP GET to /mcp first
            get_request = (f"GET /mcp HTTP/1.1\r\nHost: {self.host}:{self.port}\r\nConnection: close\r\n\r\n").encode(
                "ascii"
            )

            writer.write(get_request)
            await writer.drain()

            response = await reader.read(4096)
            writer.close()
            await writer.wait_closed()

            print("📊 MCP endpoint check: HTTP response received")

            if self.verbose and response:
                print(f"📝 Response preview: {response[:200]}...")

            if b"HTTP/1.1 200" in response or b"ChukMCPServer" in response:
                return True
            else:
                print("❌ Unexpected MCP endpoint response")
                if self.verbose:
                    print(f"   Full response: {response.decode('utf-8', errors='ignore')[:500]}")
                return False

        except Exception as e:
            print(f"❌ Connection error: {e}")
            print(f"💡 Check if server is running on {self.host}:{self.port}")
            return False

    async def _initialize_mcp_session(self) -> bool:
        """Initialize MCP session and extract session ID"""
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
            writer.write(self.mcp_initialize)
            await writer.drain()

            # Read the full HTTP response
            response = await reader.read(8192)
            writer.close()
            await writer.wait_closed()

            response_str = response.decode("utf-8", errors="ignore")

            if "HTTP/1.1 200" not in response_str:
                print(f"❌ Initialize failed: {response_str[:200]}")
                return False

            # Extract session ID from headers
            for line in response_str.split("\r\n"):
                if line.lower().startswith("mcp-session-id:"):
                    self.session_id = line.split(":", 1)[1].strip()
                    break

            # Send initialized notification if we have a session
            if self.session_id:
                await self._send_initialized_notification()

            return True

        except Exception as e:
            print(f"Session init error: {e}")
            return False

    async def _send_initialized_notification(self):
        """Send MCP initialized notification"""
        try:
            notification = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}

            notification_request = self._build_http_request_with_session(notification)

            reader, writer = await asyncio.open_connection(self.host, self.port)
            writer.write(notification_request)
            await writer.drain()
            await reader.read(1024)  # Consume response
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass  # Notification failures are non-critical

    async def _check_resource_exists(self, uri: str) -> bool:
        """Check if a resource exists before benchmarking it"""
        try:
            check_request = self._build_http_request_with_session(
                {"jsonrpc": "2.0", "id": 999, "method": "resources/read", "params": {"uri": uri}}
            )

            reader, writer = await asyncio.open_connection(self.host, self.port)
            writer.write(check_request)
            await writer.drain()

            response = await reader.read(8192)
            writer.close()
            await writer.wait_closed()

            # Check if response contains an error (resource not found)
            if b'"error"' in response:
                return False
            elif b'"result"' in response:
                return True

            return False
        except Exception:
            return False

    def _rebuild_requests_with_session(self):
        """Rebuild requests with session ID"""
        if not self.session_id:
            return

        # Rebuild requests with session header
        self.mcp_ping = self._build_http_request_with_session(
            {"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}}
        )

        self.mcp_tools_list = self._build_http_request_with_session(
            {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}
        )

        self.mcp_resources_list = self._build_http_request_with_session(
            {"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}}
        )

        self.hello_call = self._build_http_request_with_session(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "hello", "arguments": {"name": "PerfTest"}},
            }
        )

        self.calculate_call = self._build_http_request_with_session(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {"name": "calculate", "arguments": {"expression": "2 + 2"}},
            }
        )

        self.settings_resource_read = self._build_http_request_with_session(
            {"jsonrpc": "2.0", "id": 7, "method": "resources/read", "params": {"uri": "config://settings"}}
        )

        self.readme_resource_read = self._build_http_request_with_session(
            {"jsonrpc": "2.0", "id": 8, "method": "resources/read", "params": {"uri": "docs://readme"}}
        )

    async def _test_mcp_operation(
        self, request_bytes: bytes, name: str, concurrency: int = 100, duration: float = 5.0
    ) -> MCPResult:
        """Test a specific MCP operation with raw sockets"""

        async def worker():
            worker_times = []
            worker_successes = 0
            worker_failures = 0
            worker_mcp_errors = 0

            try:
                reader, writer = await asyncio.open_connection(self.host, self.port)

                end_time = time.time() + duration

                while time.time() < end_time:
                    start = time.time()

                    try:
                        writer.write(request_bytes)
                        await writer.drain()

                        # Read HTTP response
                        response = await reader.read(8192)

                        if b"HTTP/1.1 200" in response:
                            # Check for MCP errors in JSON response
                            if b'"error"' in response:
                                worker_mcp_errors += 1
                                worker_failures += 1
                            elif b'"result"' in response or b'"jsonrpc"' in response:
                                worker_successes += 1
                            else:
                                worker_failures += 1
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

            return worker_times, worker_successes, worker_failures, worker_mcp_errors

        # Run workers concurrently
        start_time = time.time()
        worker_results = await asyncio.gather(*[worker() for _ in range(concurrency)])
        actual_duration = time.time() - start_time

        # Aggregate results
        all_times = []
        total_successes = 0
        total_failures = 0
        total_mcp_errors = 0

        for worker_times, worker_successes, worker_failures, worker_mcp_errors in worker_results:
            all_times.extend(worker_times)
            total_successes += worker_successes
            total_failures += worker_failures
            total_mcp_errors += worker_mcp_errors

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

        return MCPResult(
            name=name,
            rps=rps,
            avg_ms=avg_ms,
            min_ms=min_ms,
            max_ms=max_ms,
            success_rate=success_rate,
            total_requests=total_requests,
            mcp_errors=total_mcp_errors,
        )

    async def _test_mcp_concurrency_scaling(self):
        """Test MCP concurrency scaling"""
        print("   Concurrency |    RPS     | Avg(ms) | Success% | MCP Errors")
        print("   " + "-" * 60)

        for concurrency in [1, 5, 10, 25, 50, 100, 200, 500]:
            result = await self._test_mcp_operation(
                self.mcp_ping, f"MCP Scale {concurrency}", concurrency=concurrency, duration=3.0
            )

            print(
                f"   {concurrency:>10} | {result.rps:>8,.0f} | {result.avg_ms:>6.1f} | "
                f"{result.success_rate:>6.1f}% | {result.mcp_errors:>8}"
            )

            # Stop if performance degrades significantly
            if result.success_rate < 80:
                print("   (Stopping due to high failure rate)")
                break

    async def _find_maximum_mcp_throughput(self) -> MCPResult:
        """Find maximum MCP throughput"""
        best_result = None
        best_rps = 0

        for concurrency in [50, 100, 200, 500, 1000]:
            print(f"   Testing {concurrency:>4} MCP connections...", end=" ", flush=True)

            result = await self._test_mcp_operation(
                self.mcp_ping, f"MCP Max {concurrency}", concurrency=concurrency, duration=3.0
            )

            print(f"{result.rps:>8,.0f} RPS ({result.success_rate:>5.1f}% success)")

            if result.success_rate >= 95 and result.rps > best_rps:
                best_rps = result.rps
                best_result = result

            if result.success_rate < 80:
                break

        return best_result or MCPResult("MCP Max", 0, 0, 0, 0, 0, 0, 0)

    def _print_mcp_summary(self, results: list[MCPResult]):
        """Print MCP performance summary"""
        print("\n" + "=" * 60)
        print("📊 ULTRA-MINIMAL MCP PROTOCOL RESULTS")
        print("=" * 60)

        if not results:
            print("❌ No MCP results to show")
            return

        # Find best MCP result
        best_result = max(results, key=lambda r: r.rps)

        print("🚀 Maximum MCP Performance:")
        print(f"   Peak RPS: {best_result.rps:>12,.0f}")
        print(f"   Avg Latency: {best_result.avg_ms:>9.2f}ms")
        print(f"   Success Rate: {best_result.success_rate:>8.1f}%")
        print(f"   MCP Errors: {best_result.mcp_errors:>10}")
        print(f"   Operation: {best_result.name}")

        # Detailed MCP results
        print("\n📋 All MCP Test Results:")
        print("   Operation               |    RPS     | Avg(ms) | Success% | MCP Errors")
        print("   " + "-" * 75)

        for result in results:
            print(
                f"   {result.name:<23} | {result.rps:>8,.0f} | {result.avg_ms:>6.1f} | "
                f"{result.success_rate:>6.1f}% | {result.mcp_errors:>8}"
            )

        # MCP Performance Analysis
        print("\n🔍 MCP Performance Analysis:")
        if best_result.rps > 15000:
            print("   🏆 EXCEPTIONAL MCP performance!")
            print("   🚀 Your ChukMCPServer is world-class")
        elif best_result.rps > 10000:
            print("   ✅ EXCELLENT MCP performance!")
            print("   💪 Great JSON-RPC handling efficiency")
        elif best_result.rps > 5000:
            print("   👍 GOOD MCP performance")
            print("   🔧 Room for JSON/tool optimization")
        elif best_result.rps > 1000:
            print("   ⚠️  MODERATE MCP performance")
            print("   🛠️  Check async tool execution paths")
        else:
            print("   ❌ LOW MCP performance")
            print("   🔍 Significant MCP bottlenecks present")

        # ChukMCPServer specific insights
        tool_results = [r for r in results if "Tool" in r.name]
        resource_results = [r for r in results if "Resource" in r.name]

        if tool_results:
            avg_tool_rps = sum(r.rps for r in tool_results) / len(tool_results)
            print("\n🔧 Tool Performance:")
            print(f"   Average Tool RPS: {avg_tool_rps:>8,.0f}")
            for result in tool_results:
                print(f"   {result.name}: {result.rps:>8,.0f} RPS")

        if resource_results:
            avg_resource_rps = sum(r.rps for r in resource_results) / len(resource_results)
            print("\n📂 Resource Performance:")
            print(f"   Average Resource RPS: {avg_resource_rps:>8,.0f}")
            for result in resource_results:
                print(f"   {result.name}: {result.rps:>8,.0f} RPS")

        print("\n🧠 ChukMCPServer Zero Config Performance:")
        print("   ✨ These are your actual zero-config tools & resources!")
        print("   🚀 Performance achieved with ZERO configuration")
        print("   🧠 Smart inference and auto-optimization working")

        print("\n" + "=" * 60)


def parse_arguments():
    """Parse command line arguments for host, port, and other options"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ultra-Minimal MCP Protocol Performance Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ultra_minimal_mcp_performance_test.py                    # Default: localhost:8000
  python ultra_minimal_mcp_performance_test.py 8001              # Custom port
  python ultra_minimal_mcp_performance_test.py localhost:8001    # Custom host:port
  python ultra_minimal_mcp_performance_test.py 192.168.1.100:8000 # Remote server
  python ultra_minimal_mcp_performance_test.py --host 0.0.0.0 --port 8080
  python ultra_minimal_mcp_performance_test.py --duration 10 --concurrency 500
        """,
    )

    # Positional argument for quick host:port specification
    parser.add_argument(
        "target",
        nargs="?",
        help='Target in format [host][:port] or just port (e.g., "localhost:8001", "8001", "192.168.1.100:8000")',
    )

    # Explicit host and port options
    parser.add_argument("--host", default="localhost", help="Server hostname or IP address (default: localhost)")

    parser.add_argument("--port", "-p", type=int, default=8000, help="Server port number (default: 8000)")

    # Test configuration options
    parser.add_argument(
        "--duration", "-d", type=float, default=5.0, help="Test duration in seconds for each operation (default: 5.0)"
    )

    parser.add_argument(
        "--concurrency", "-c", type=int, default=200, help="Maximum concurrency level to test (default: 200)"
    )

    parser.add_argument(
        "--quick", "-q", action="store_true", help="Run quick tests with reduced duration and concurrency"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output with detailed connection info"
    )

    args = parser.parse_args()

    # Parse target if provided
    if args.target:
        target = args.target

        # Handle different target formats
        if target.isdigit():
            # Just a port number
            args.port = int(target)
        elif ":" in target:
            # host:port format
            if target.startswith("http://"):
                target = target[7:]
            elif target.startswith("https://"):
                target = target[8:]

            if "/" in target:
                target = target.split("/")[0]

            host_part, port_part = target.rsplit(":", 1)
            args.host = host_part
            args.port = int(port_part)
        else:
            # Just a hostname
            args.host = target

    # Quick mode adjustments
    if args.quick:
        args.duration = min(args.duration, 2.0)
        args.concurrency = min(args.concurrency, 50)

    return args


async def main():
    """Main entry point with argument parsing"""
    args = parse_arguments()

    print("⚡ ChukMCPServer Ultra-Minimal MCP Protocol Test")
    print(f"🎯 Target: {args.host}:{args.port}")
    print("📝 Zero client overhead - MCP JSON-RPC performance")
    print("🏆 Goal: Measure true ChukMCPServer performance")
    print("🧠 Testing actual zero-config tools and resources")

    if args.quick:
        print("⚡ Quick mode: Reduced duration and concurrency")

    if args.verbose:
        print("📊 Test Configuration:")
        print(f"   Duration: {args.duration}s per test")
        print(f"   Max Concurrency: {args.concurrency}")
        print(f"   Target: {args.host}:{args.port}")

    print()

    # Optimize for maximum performance
    gc.collect()
    gc.disable()  # Disable GC during testing

    test = UltraMinimalMCPTest(
        host=args.host, port=args.port, duration=args.duration, max_concurrency=args.concurrency, verbose=args.verbose
    )

    try:
        success = await test.run_mcp_performance_tests()

        if success:
            print("🎉 Ultra-minimal MCP performance testing completed!")
            print("🧠 Your zero-configuration server delivered the results above!")
        else:
            print("❌ MCP performance testing failed. Check server status.")
            print(f"💡 Make sure your zero_config_examples.py server is running on {args.host}:{args.port}")
            print("💡 Try: uv run examples/zero_config_examples.py")
            if args.port != 8000:
                print("💡 Or run server with custom port to match your test target")
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
