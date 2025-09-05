#!/usr/bin/env python3
"""
base_performance_test.py - Working Base Performance Test for ChukMCPServer

This test works with the actual ChukMCPServer endpoints and structure.
Tests both HTTP endpoints and MCP protocol performance using httpx.
"""

import asyncio
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class PerformanceResult:
    """Performance test result"""

    endpoint: str
    concurrency: int
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    rps: float
    avg_response_ms: float
    min_response_ms: float
    max_response_ms: float
    p95_response_ms: float
    success_rate: float
    error_details: dict[str, int]


class ChukMCPPerformanceTest:
    """Performance testing for ChukMCPServer"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")
        self.mcp_url = f"{self.base_url}/mcp"
        self.results: list[PerformanceResult] = []
        self.session_id: str | None = None

    async def run_full_test_suite(self):
        """Run comprehensive performance test suite"""
        print("🚀 ChukMCPServer - Base Performance Test")
        print(f"🔗 Base URL: {self.base_url}")
        print(f"🔗 MCP URL: {self.mcp_url}")
        print("=" * 80)

        # Test server availability first
        if not await self._check_server_availability():
            print("❌ Server not available. Please start the ChukMCPServer first")
            return False

        # Initialize MCP session
        await self._initialize_mcp_session()

        # Progressive testing
        await self._test_http_endpoints()
        await self._test_mcp_operations()
        await self._test_concurrency_scaling()
        await self._test_sustained_load()
        await self._test_error_handling()

        # Generate final report
        self._generate_performance_report()

        return True

    async def _check_server_availability(self) -> bool:
        """Check if ChukMCPServer is available and responsive"""
        print("🔍 Checking ChukMCPServer availability...")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try the main endpoints that should exist
                test_endpoints = [
                    ("/", "Server Info"),
                    ("/health", "Health Check"),
                    ("/mcp", "MCP Endpoint (GET)"),
                ]

                server_available = False
                for path, name in test_endpoints:
                    try:
                        response = await client.get(f"{self.base_url}{path}")
                        if response.status_code == 200:
                            data = response.json()
                            print(f"   ✅ {name} available: {response.status_code}")
                            if path == "/":
                                server_name = data.get("server", {}).get("name", "Unknown")
                                version = data.get("server", {}).get("version", "Unknown")
                                print(f"   📋 Server: {server_name} v{version}")
                            server_available = True
                            break
                        else:
                            print(f"   ⚠️  {name}: {response.status_code}")
                    except Exception as e:
                        print(f"   ⚠️  {name}: {e}")

                if server_available:
                    return True
                else:
                    print("   ❌ No working endpoints found")
                    return False

        except Exception as e:
            print(f"   ❌ Server not available: {e}")
            return False

    async def _initialize_mcp_session(self):
        """Initialize MCP session for protocol testing"""
        print("🔗 Initializing MCP session...")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Content-Type": "application/json"}

                init_message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "performance-test", "version": "1.0.0"},
                    },
                }

                response = await client.post(self.mcp_url, json=init_message, headers=headers)
                if response.status_code == 200:
                    self.session_id = response.headers.get("Mcp-Session-Id")
                    print(f"   ✅ MCP session initialized: {self.session_id[:8] if self.session_id else 'None'}...")

                    # Send initialized notification
                    if self.session_id:
                        headers["Mcp-Session-Id"] = self.session_id

                    init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}

                    notif_response = await client.post(self.mcp_url, json=init_notif, headers=headers)
                    if notif_response.status_code in [200, 202, 204]:
                        print("   ✅ MCP initialization complete")
                    else:
                        print(f"   ⚠️  MCP notification failed: {notif_response.status_code}")
                else:
                    print(f"   ❌ MCP initialization failed: {response.status_code}")

        except Exception as e:
            print(f"   ❌ MCP session initialization failed: {e}")

    async def _test_http_endpoints(self):
        """Test basic HTTP endpoints for baseline performance"""
        print("\n📊 Testing HTTP Endpoints")
        print("-" * 60)

        # Define test endpoints that should exist on ChukMCPServer
        endpoints = [
            {"path": "/", "method": "GET", "name": "Server Info", "expected_rps": 5000},
            {"path": "/health", "method": "GET", "name": "Health Check", "expected_rps": 8000},
            {"path": "/ping", "method": "GET", "name": "Ping", "expected_rps": 10000},
            {"path": "/mcp", "method": "GET", "name": "MCP Info", "expected_rps": 6000},
        ]

        for endpoint in endpoints:
            print(f"\n🎯 Testing {endpoint['name']} ({endpoint['method']} {endpoint['path']})")

            # Test with low concurrency first
            result = await self._test_single_endpoint(endpoint, concurrency=10, duration=3.0)
            if result.total_requests > 0:  # Only add if we got results
                self.results.append(result)

                # Check if meets expectations
                expected = endpoint.get("expected_rps", 1000)
                status = "✅" if result.rps >= expected * 0.8 else "⚠️" if result.rps >= expected * 0.5 else "❌"

                print(
                    f"   {status} {result.rps:>8.1f} RPS | {result.avg_response_ms:>6.2f}ms avg | {result.success_rate:>5.1f}% success"
                )

                if result.rps >= expected:
                    print(f"      🎉 Exceeds target ({expected:,} RPS)")
                elif result.rps >= expected * 0.8:
                    print(f"      ✅ Meets target ({expected:,} RPS)")
                else:
                    print(f"      ⚠️  Below target ({expected:,} RPS)")
            else:
                print("   ❌ Endpoint not available or failed")

    async def _test_mcp_operations(self):
        """Test MCP protocol operations"""
        print("\n🔧 Testing MCP Protocol Operations")
        print("-" * 60)

        if not self.session_id:
            print("   ❌ No MCP session, skipping MCP tests")
            return

        # Define MCP operations to test
        mcp_operations = [
            {
                "name": "MCP Ping",
                "message": {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}},
                "expected_rps": 6000,
            },
            {
                "name": "Tools List",
                "message": {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                "expected_rps": 4000,
            },
            {
                "name": "Resources List",
                "message": {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}},
                "expected_rps": 4000,
            },
        ]

        for operation in mcp_operations:
            print(f"\n🎯 Testing {operation['name']}")

            result = await self._test_mcp_operation(operation, concurrency=10, duration=3.0)
            if result.total_requests > 0:
                self.results.append(result)

                expected = operation.get("expected_rps", 1000)
                status = "✅" if result.rps >= expected * 0.8 else "⚠️" if result.rps >= expected * 0.5 else "❌"

                print(
                    f"   {status} {result.rps:>8.1f} RPS | {result.avg_response_ms:>6.2f}ms avg | {result.success_rate:>5.1f}% success"
                )

                if result.rps >= expected:
                    print(f"      🎉 Exceeds target ({expected:,} RPS)")
                elif result.rps >= expected * 0.8:
                    print(f"      ✅ Meets target ({expected:,} RPS)")
                else:
                    print(f"      ⚠️  Below target ({expected:,} RPS)")

    async def _test_concurrency_scaling(self):
        """Test how performance scales with concurrency"""
        print("\n⚡ Testing Concurrency Scaling")
        print("-" * 60)

        # Use the fastest available endpoint
        if not self.results:
            print("   ❌ No successful endpoints to test concurrency")
            return

        # Find the best performing endpoint
        best_result = max(self.results, key=lambda r: r.rps)
        print(f"Using best endpoint for concurrency test: {best_result.endpoint}")

        # Use MCP ping if available, otherwise HTTP endpoint
        if self.session_id:
            test_operation = {
                "name": "MCP Ping",
                "message": {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}},
                "type": "mcp",
            }
        else:
            test_operation = {"path": "/", "method": "GET", "name": "Server Info", "type": "http"}

        concurrency_levels = [1, 5, 10, 20, 50, 100, 200]

        print("Concurrency |    RPS     | Avg(ms) | Success% | Notes")
        print("-" * 60)

        peak_rps = 0
        optimal_concurrency = 1

        for concurrency in concurrency_levels:
            if test_operation["type"] == "mcp":
                result = await self._test_mcp_operation(test_operation, concurrency, duration=5.0)
            else:
                result = await self._test_single_endpoint(test_operation, concurrency, duration=5.0)

            if result.total_requests > 0:
                # Track peak performance
                if result.rps > peak_rps and result.success_rate > 95:
                    peak_rps = result.rps
                    optimal_concurrency = concurrency

                # Format output
                notes = ""
                if result.success_rate < 90:
                    notes = "High failures"
                elif result.avg_response_ms > 100:
                    notes = "High latency"
                elif result.rps > peak_rps * 0.95:
                    notes = "Peak performance"

                print(
                    f"{concurrency:>10} | {result.rps:>8.1f} | {result.avg_response_ms:>6.1f} | "
                    f"{result.success_rate:>6.1f}% | {notes}"
                )

                # Stop if performance severely degrades
                if result.success_rate < 50:
                    print("      ⚠️  High failure rate, stopping concurrency test")
                    break
            else:
                print(f"{concurrency:>10} | {'0.0':>8} | {'N/A':>6} | {'0.0':>6}% | Failed")

            # Add delay between tests
            await asyncio.sleep(1.0)

        print(f"\n🏆 Optimal Concurrency: {optimal_concurrency} connections")
        print(f"🚀 Peak Performance: {peak_rps:,.1f} RPS")

    async def _test_sustained_load(self):
        """Test sustained load performance"""
        print("\n🔥 Testing Sustained Load Performance")
        print("-" * 60)

        # Use MCP tools list or HTTP health check
        if self.session_id:
            test_operation = {
                "name": "Tools List",
                "message": {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                "type": "mcp",
            }
        else:
            test_operation = {"path": "/", "method": "GET", "name": "Server Info", "type": "http"}

        concurrency = 50
        durations = [10, 30]  # Shorter durations for testing

        print("Duration |    RPS     | Avg(ms) | Success% | Stability")
        print("-" * 60)

        baseline_rps = None

        for duration in durations:
            print(f"Testing {duration}s load...", end=" ", flush=True)

            if test_operation["type"] == "mcp":
                result = await self._test_mcp_operation(test_operation, concurrency, duration)
            else:
                result = await self._test_single_endpoint(test_operation, concurrency, duration)

            if result.total_requests > 0:
                if baseline_rps is None:
                    baseline_rps = result.rps
                    stability = "Baseline"
                else:
                    degradation = (baseline_rps - result.rps) / baseline_rps * 100
                    if degradation < 5:
                        stability = "Excellent"
                    elif degradation < 15:
                        stability = "Good"
                    elif degradation < 30:
                        stability = "Fair"
                    else:
                        stability = "Poor"

                print(
                    f"\r{duration:>6}s | {result.rps:>8.1f} | {result.avg_response_ms:>6.1f} | "
                    f"{result.success_rate:>6.1f}% | {stability}"
                )
            else:
                print(f"\r{duration:>6}s | {'0.0':>8} | {'N/A':>6} | {'0.0':>6}% | Failed")

    async def _test_error_handling(self):
        """Test error handling and recovery"""
        print("\n🛡️  Testing Error Handling and Recovery")
        print("-" * 60)

        # Test invalid HTTP endpoints
        error_endpoints = [
            {"path": "/nonexistent", "method": "GET", "name": "404 Errors"},
            {"path": "/mcp", "method": "POST", "name": "Invalid JSON", "data": {"invalid": "data"}},
        ]

        for endpoint in error_endpoints:
            print(f"Testing {endpoint['name']}...", end=" ")

            result = await self._test_single_endpoint(endpoint, concurrency=20, duration=2.0)

            if result.total_requests > 0:
                # For error endpoints, we expect failures
                if endpoint["name"] == "404 Errors":
                    expected_status = result.failed_requests > result.successful_requests
                    status = "✅" if expected_status else "❌"
                    print(f"{status} {result.failed_requests} errors handled properly")
                else:
                    # Check that server handles errors gracefully without crashing
                    status = "✅" if result.total_requests > 0 else "❌"
                    print(f"{status} Server remained responsive")
            else:
                print("❌ No requests processed")

        # Test invalid MCP requests if session available
        if self.session_id:
            print("Testing Invalid MCP Request...", end=" ")

            invalid_mcp = {
                "name": "Invalid MCP",
                "message": {"jsonrpc": "2.0", "id": 1, "method": "nonexistent/method", "params": {}},
            }

            result = await self._test_mcp_operation(invalid_mcp, concurrency=20, duration=2.0)
            if result.total_requests > 0:
                print(f"✅ {result.total_requests} invalid requests handled")
            else:
                print("❌ No requests processed")

    async def _test_single_endpoint(
        self, endpoint: dict[str, Any], concurrency: int, duration: float
    ) -> PerformanceResult:
        """Test a single HTTP endpoint with given concurrency"""

        async def worker(worker_id: int):
            """Worker function for load testing"""
            times = []
            successes = 0
            failures = 0
            error_details = {}

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    end_time = time.time() + duration

                    while time.time() < end_time:
                        start = time.time()

                        try:
                            url = f"{self.base_url}{endpoint['path']}"

                            if endpoint["method"] == "GET":
                                response = await client.get(url)
                                await response.aread()  # Read response body
                                if 200 <= response.status_code < 300:
                                    successes += 1
                                else:
                                    failures += 1
                                    error_key = f"HTTP_{response.status_code}"
                                    error_details[error_key] = error_details.get(error_key, 0) + 1

                            elif endpoint["method"] == "POST":
                                data = endpoint.get("data", {})
                                response = await client.post(url, json=data)
                                await response.aread()  # Read response body
                                if 200 <= response.status_code < 300:
                                    successes += 1
                                else:
                                    failures += 1
                                    error_key = f"HTTP_{response.status_code}"
                                    error_details[error_key] = error_details.get(error_key, 0) + 1

                        except httpx.TimeoutException:
                            failures += 1
                            error_details["timeout"] = error_details.get("timeout", 0) + 1
                        except Exception as e:
                            failures += 1
                            error_key = type(e).__name__
                            error_details[error_key] = error_details.get(error_key, 0) + 1

                        elapsed = time.time() - start
                        times.append(elapsed)

                        # Small delay to prevent overwhelming
                        await asyncio.sleep(0.001)

            except Exception:
                # Worker failed completely
                if not times:
                    times = [duration]  # Add dummy time
                failures += 1

            return times, successes, failures, error_details

        # Run workers
        start_time = time.time()

        try:
            tasks = [worker(i) for i in range(concurrency)]
            worker_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=duration + 30.0
            )

            actual_duration = time.time() - start_time

            # Aggregate results
            all_times = []
            total_successes = 0
            total_failures = 0
            all_error_details = {}

            for result in worker_results:
                if isinstance(result, Exception):
                    total_failures += 1
                    error_key = type(result).__name__
                    all_error_details[error_key] = all_error_details.get(error_key, 0) + 1
                else:
                    times, successes, failures, error_details = result
                    all_times.extend(times)
                    total_successes += successes
                    total_failures += failures

                    # Merge error details
                    for key, count in error_details.items():
                        all_error_details[key] = all_error_details.get(key, 0) + count

            # Calculate statistics
            total_requests = total_successes + total_failures
            rps = total_requests / actual_duration if actual_duration > 0 else 0
            success_rate = (total_successes / total_requests * 100) if total_requests > 0 else 0

            if all_times:
                avg_time = statistics.mean(all_times)
                min_time = min(all_times)
                max_time = max(all_times)
                sorted_times = sorted(all_times)
                p95_time = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
            else:
                avg_time = min_time = max_time = p95_time = 0

            return PerformanceResult(
                endpoint=f"{endpoint['method']} {endpoint['path']}",
                concurrency=concurrency,
                duration=actual_duration,
                total_requests=total_requests,
                successful_requests=total_successes,
                failed_requests=total_failures,
                rps=rps,
                avg_response_ms=avg_time * 1000,
                min_response_ms=min_time * 1000,
                max_response_ms=max_time * 1000,
                p95_response_ms=p95_time * 1000,
                success_rate=success_rate,
                error_details=all_error_details,
            )

        except TimeoutError:
            return PerformanceResult(
                endpoint=f"{endpoint['method']} {endpoint['path']}",
                concurrency=concurrency,
                duration=duration,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                rps=0,
                avg_response_ms=0,
                min_response_ms=0,
                max_response_ms=0,
                p95_response_ms=0,
                success_rate=0,
                error_details={"timeout": 1},
            )

    async def _test_mcp_operation(
        self, operation: dict[str, Any], concurrency: int, duration: float
    ) -> PerformanceResult:
        """Test a single MCP operation with given concurrency"""

        async def mcp_worker(worker_id: int):
            """Worker function for MCP testing"""
            times = []
            successes = 0
            failures = 0
            error_details = {}

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    headers = {"Content-Type": "application/json"}
                    if self.session_id:
                        headers["Mcp-Session-Id"] = self.session_id

                    end_time = time.time() + duration

                    while time.time() < end_time:
                        start = time.time()

                        try:
                            # Create unique message ID
                            message = operation["message"].copy()
                            message["id"] = f"{worker_id}_{int(time.time() * 1000000) % 1000000}"

                            response = await client.post(self.mcp_url, json=message, headers=headers)
                            await response.aread()  # Read response body
                            if response.status_code == 200:
                                successes += 1
                            else:
                                failures += 1
                                error_key = f"HTTP_{response.status_code}"
                                error_details[error_key] = error_details.get(error_key, 0) + 1

                        except httpx.TimeoutException:
                            failures += 1
                            error_details["timeout"] = error_details.get("timeout", 0) + 1
                        except Exception as e:
                            failures += 1
                            error_key = type(e).__name__
                            error_details[error_key] = error_details.get(error_key, 0) + 1

                        elapsed = time.time() - start
                        times.append(elapsed)

                        # Small delay to prevent overwhelming
                        await asyncio.sleep(0.001)

            except Exception:
                if not times:
                    times = [duration]
                failures += 1

            return times, successes, failures, error_details

        # Run workers (same logic as HTTP endpoint test)
        start_time = time.time()

        try:
            tasks = [mcp_worker(i) for i in range(concurrency)]
            worker_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=duration + 30.0
            )

            actual_duration = time.time() - start_time

            # Aggregate results (same as HTTP test)
            all_times = []
            total_successes = 0
            total_failures = 0
            all_error_details = {}

            for result in worker_results:
                if isinstance(result, Exception):
                    total_failures += 1
                    error_key = type(result).__name__
                    all_error_details[error_key] = all_error_details.get(error_key, 0) + 1
                else:
                    times, successes, failures, error_details = result
                    all_times.extend(times)
                    total_successes += successes
                    total_failures += failures

                    for key, count in error_details.items():
                        all_error_details[key] = all_error_details.get(key, 0) + count

            # Calculate statistics
            total_requests = total_successes + total_failures
            rps = total_requests / actual_duration if actual_duration > 0 else 0
            success_rate = (total_successes / total_requests * 100) if total_requests > 0 else 0

            if all_times:
                avg_time = statistics.mean(all_times)
                min_time = min(all_times)
                max_time = max(all_times)
                sorted_times = sorted(all_times)
                p95_time = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
            else:
                avg_time = min_time = max_time = p95_time = 0

            return PerformanceResult(
                endpoint=f"MCP {operation['name']}",
                concurrency=concurrency,
                duration=actual_duration,
                total_requests=total_requests,
                successful_requests=total_successes,
                failed_requests=total_failures,
                rps=rps,
                avg_response_ms=avg_time * 1000,
                min_response_ms=min_time * 1000,
                max_response_ms=max_time * 1000,
                p95_response_ms=p95_time * 1000,
                success_rate=success_rate,
                error_details=all_error_details,
            )

        except TimeoutError:
            return PerformanceResult(
                endpoint=f"MCP {operation['name']}",
                concurrency=concurrency,
                duration=duration,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                rps=0,
                avg_response_ms=0,
                min_response_ms=0,
                max_response_ms=0,
                p95_response_ms=0,
                success_rate=0,
                error_details={"timeout": 1},
            )

    def _generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE PERFORMANCE REPORT")
        print("=" * 80)

        if not self.results:
            print("❌ No results to report")
            return

        # Find best performing endpoints
        best_rps = max(self.results, key=lambda r: r.rps)
        best_latency = min(self.results, key=lambda r: r.avg_response_ms)

        print("🚀 Peak Performance:")
        print(f"   Best RPS: {best_rps.rps:,.1f} ({best_rps.endpoint})")
        print(f"   Best Latency: {best_latency.avg_response_ms:.2f}ms ({best_latency.endpoint})")

        # Calculate overall statistics
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0

        print("\n📈 Overall Statistics:")
        print(f"   Total Requests: {total_requests:,}")
        print(f"   Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"   Endpoints Tested: {len(set(r.endpoint for r in self.results))}")
        print(f"   MCP Session: {'✅ Active' if self.session_id else '❌ Not Available'}")

        # Performance grade
        if best_rps.rps > 15000:
            grade = "S+ (Exceptional)"
        elif best_rps.rps > 10000:
            grade = "S (Excellent)"
        elif best_rps.rps > 5000:
            grade = "A (Very Good)"
        elif best_rps.rps > 1000:
            grade = "B (Good)"
        else:
            grade = "C (Needs Improvement)"

        print(f"\n🏆 Performance Grade: {grade}")

        # Detailed results table
        print("\n📋 Detailed Results:")
        print(f"{'Endpoint':<25} {'RPS':<10} {'Avg(ms)':<10} {'Success%':<10}")
        print("-" * 60)
        for result in self.results:
            endpoint_name = result.endpoint[:24]
            print(
                f"{endpoint_name:<25} {result.rps:<10.1f} {result.avg_response_ms:<10.1f} {result.success_rate:<10.1f}"
            )

        # Recommendations
        print("\n💡 Recommendations:")
        if best_rps.rps > 5000:
            print("   ✅ Good baseline performance detected")
            print("   🚀 Ready for optimization phase")
        elif best_rps.rps > 1000:
            print("   ⚠️  Moderate performance. Optimization recommended.")
            print("   🔧 Focus on response caching and connection pooling")
        else:
            print("   ❌ Performance needs significant improvement")
            print("   🔍 Check for major bottlenecks in request handling")

        if overall_success_rate > 95:
            print("   ✅ Excellent reliability")
        elif overall_success_rate > 90:
            print("   ✅ Good reliability")
        else:
            print("   ⚠️  Reliability needs attention")

        print("\n" + "=" * 80)


async def main():
    """Main entry point"""
    base_url = "http://localhost:8001"

    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    print("🧪 ChukMCPServer - Base Performance Testing")
    print("📝 This test works with actual ChukMCPServer endpoints")
    print("🎯 Target: Establish baseline and identify optimization opportunities")
    print()

    test = ChukMCPPerformanceTest(base_url)
    success = await test.run_full_test_suite()

    if success:
        print("🎉 Performance testing completed successfully!")
        print("🚀 Ready for optimization phase!")
    else:
        print("❌ Performance testing failed. Check server status.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
