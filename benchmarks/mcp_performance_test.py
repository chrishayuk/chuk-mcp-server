#!/usr/bin/env python3
"""
mcp_performance_test.py - Comprehensive MCP Protocol Performance Test using httpx

Modern async performance testing with httpx for clean, reliable HTTP operations.
Progressive testing approach optimized for both traditional and async-native MCP servers.

Test Categories:
1. MCP Protocol handshake and capability discovery
2. Individual MCP operation performance baselines
3. Concurrency scaling analysis
4. Sustained load performance
5. Maximum throughput discovery
6. Error handling and recovery
"""

import asyncio
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class MCPPerformanceResult:
    """MCP-specific performance test result with detailed metrics"""

    operation: str
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
    p99_response_ms: float
    success_rate: float
    mcp_errors: dict[str, int]
    throughput_mb_per_sec: float
    session_info: dict[str, Any]


class MCPPerformanceTest:
    """Comprehensive MCP protocol performance testing with httpx"""

    def __init__(self, mcp_url: str = "http://localhost:8000/mcp"):
        self.mcp_url = mcp_url
        self.base_url = mcp_url.replace("/mcp", "")
        self.session_id: str | None = None
        self.server_info: dict[str, Any] = {}
        self.available_tools: list[dict[str, Any]] = []
        self.available_resources: list[dict[str, Any]] = []
        self.results: list[MCPPerformanceResult] = []

        # HTTP client configuration optimized for performance testing
        self.limits = httpx.Limits(max_keepalive_connections=200, max_connections=1000, keepalive_expiry=30.0)

        # Performance test configuration
        self.test_config = {
            "warm_up_requests": 50,
            "baseline_duration": 5.0,
            "scaling_duration": 8.0,
            "sustained_duration": 30.0,
            "max_concurrency": 2000,
            "timeout_seconds": 30.0,
        }

    async def run_full_mcp_test_suite(self):
        """Run comprehensive MCP performance test suite"""
        print("🚀 MCP Protocol Performance Test Suite (httpx + async)")
        print(f"🔗 MCP URL: {self.mcp_url}")
        print("=" * 80)

        # Test MCP protocol availability and warm up
        if not await self._check_mcp_availability():
            print("❌ MCP server not available. Please start the server first.")
            return False

        # Warm up the server
        await self._warm_up_server()

        # Progressive MCP testing
        await self._test_mcp_handshake_performance()
        await self._test_individual_mcp_operations()
        await self._test_mcp_concurrency_scaling()
        await self._test_sustained_mcp_load()
        await self._test_maximum_mcp_throughput()
        await self._test_mcp_error_handling()

        # Generate comprehensive report
        self._generate_mcp_performance_report()

        return True

    async def _check_mcp_availability(self) -> bool:
        """Check MCP server availability and initialize session"""
        print("🔍 Checking MCP protocol availability...")

        try:
            async with httpx.AsyncClient(limits=self.limits, timeout=10.0) as client:
                # Check base server health
                try:
                    health_response = await client.get(f"{self.base_url}/health")
                    if health_response.status_code != 200:
                        print(f"   ❌ Base server not healthy: {health_response.status_code}")
                        return False
                except Exception:
                    print("   ⚠️  Health endpoint not available, proceeding with MCP test")

                # Test MCP initialize
                if not await self._perform_mcp_initialize(client):
                    return False

                # Discover MCP capabilities
                await self._discover_mcp_capabilities(client)

                print("   ✅ MCP protocol available")
                print(
                    f"   📋 Server: {self.server_info.get('name', 'unknown')} v{self.server_info.get('version', 'unknown')}"
                )
                print(f"   🔧 Tools available: {len(self.available_tools)}")
                print(f"   📄 Resources available: {len(self.available_resources)}")

                # Detect server type
                server_type = (
                    "async-native"
                    if any("async" in tool.get("name", "").lower() for tool in self.available_tools)
                    else "traditional"
                )
                print(f"   🏷️  Server type: {server_type}")

                return True

        except Exception as e:
            print(f"   ❌ MCP protocol not available: {e}")
            return False

    async def _perform_mcp_initialize(self, client: httpx.AsyncClient) -> bool:
        """Perform MCP initialize handshake"""
        try:
            headers = {"Content-Type": "application/json"}

            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-perf-test", "version": "2.0.0"},
                },
            }

            response = await client.post(self.mcp_url, json=init_message, headers=headers)

            if response.status_code == 200:
                self.session_id = response.headers.get("Mcp-Session-Id")
                data = response.json()

                if "result" in data and "serverInfo" in data["result"]:
                    self.server_info = data["result"]["serverInfo"]

                    # Send initialized notification
                    if self.session_id:
                        headers["Mcp-Session-Id"] = self.session_id

                    init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}

                    notif_response = await client.post(self.mcp_url, json=init_notif, headers=headers)
                    return notif_response.status_code in [200, 202, 204]

            return False

        except Exception as e:
            print(f"   ❌ MCP initialize failed: {e}")
            return False

    async def _discover_mcp_capabilities(self, client: httpx.AsyncClient):
        """Discover available MCP tools and resources"""
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        try:
            # Get tools
            tools_msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            response = await client.post(self.mcp_url, json=tools_msg, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "tools" in data["result"]:
                    self.available_tools = data["result"]["tools"]

            # Get resources
            resources_msg = {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}}
            response = await client.post(self.mcp_url, json=resources_msg, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "resources" in data["result"]:
                    self.available_resources = data["result"]["resources"]

        except Exception as e:
            print(f"   ⚠️  Capability discovery error: {e}")

    async def _warm_up_server(self):
        """Warm up the server with initial requests"""
        print("🔥 Warming up server...")

        warm_up_message = {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}

        async with httpx.AsyncClient(limits=self.limits, timeout=5.0) as client:
            headers = self._get_headers()

            # Send warm-up requests
            tasks = []
            for _i in range(self.test_config["warm_up_requests"]):
                task = client.post(self.mcp_url, json=warm_up_message, headers=headers)
                tasks.append(task)

            try:
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                successful_warmups = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
                print(f"   ✅ Warm-up complete: {successful_warmups}/{len(responses)} successful requests")
            except Exception as e:
                print(f"   ⚠️  Warm-up issues: {e}")

    def _get_headers(self) -> dict[str, str]:
        """Get standard MCP request headers"""
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        return headers

    def _get_smart_tool_arguments(self, tool: dict[str, Any]) -> dict[str, Any]:
        """Get appropriate arguments for different tool types"""
        tool_name = tool["name"].lower()

        # Performance-optimized arguments for different tool types
        if "hello" in tool_name or "greet" in tool_name:
            return {"name": "PerfTest"}
        elif "add" in tool_name or "sum" in tool_name:
            return {"a": 5, "b": 3}
        elif "calculate" in tool_name or "calc" in tool_name:
            return {"expression": "2 + 2"}
        elif "async_hello" in tool_name:
            return {"name": "PerfTest", "delay": 0.01}  # Minimal delay for performance testing
        elif "concurrent" in tool_name:
            return {"urls": ["test1", "test2"]}  # Minimal test data
        elif "stream" in tool_name:
            return {"item_count": 3, "process_delay": 0.01}  # Small dataset for perf testing
        elif "batch" in tool_name:
            return {"items": ["test1", "test2"], "batch_size": 2}
        elif "monitor" in tool_name or "dashboard" in tool_name:
            return {"duration": 1, "update_interval": 0.2}  # Short duration for perf testing
        elif "file" in tool_name:
            return {"file_count": 3, "processing_complexity": "simple"}
        elif "task" in tool_name or "distributed" in tool_name:
            return {"task_count": 4, "worker_count": 2}
        else:
            # Fallback to schema-based argument generation
            return self._generate_args_from_schema(tool)

    def _generate_args_from_schema(self, tool: dict[str, Any]) -> dict[str, Any]:
        """Generate arguments from tool schema for unknown tools"""
        schema = tool.get("inputSchema", {})
        properties = schema.get("properties", {})

        args = {}
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "string")

            if prop_type == "string":
                args[prop_name] = "test"
            elif prop_type == "integer":
                args[prop_name] = 1
            elif prop_type == "number":
                args[prop_name] = 1.0
            elif prop_type == "boolean":
                args[prop_name] = True
            elif prop_type == "array":
                args[prop_name] = ["test"]
            elif prop_type == "object":
                args[prop_name] = {}

        return args

    async def _test_mcp_handshake_performance(self):
        """Test MCP handshake performance"""
        print("\n🤝 Testing MCP Handshake Performance")
        print("-" * 60)

        handshake_times = []
        success_count = 0

        async with httpx.AsyncClient(limits=self.limits, timeout=15.0) as client:
            for _i in range(10):
                start_time = time.time()
                try:
                    if await self._perform_mcp_initialize(client):
                        success_count += 1
                    handshake_times.append(time.time() - start_time)
                except Exception:
                    handshake_times.append(time.time() - start_time)

        if handshake_times:
            avg_time = statistics.mean(handshake_times) * 1000
            min_time = min(handshake_times) * 1000
            max_time = max(handshake_times) * 1000
            success_rate = (success_count / len(handshake_times)) * 100

            status = "✅" if success_rate >= 95 else "⚠️" if success_rate >= 80 else "❌"
            print(f"   {status} Handshake: {avg_time:.1f}ms avg | {min_time:.1f}ms min | {max_time:.1f}ms max")
            print(f"      Success rate: {success_rate:.1f}% | Target: >95% success")

    async def _test_individual_mcp_operations(self):
        """Test individual MCP operations for baseline performance"""
        print("\n📊 Testing Individual MCP Operations")
        print("-" * 60)

        # Core MCP operations
        operations = [
            {
                "name": "MCP Ping",
                "message": {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}},
                "expected_rps": 8000,
            },
            {
                "name": "Tools List",
                "message": {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                "expected_rps": 6000,
            },
            {
                "name": "Resources List",
                "message": {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}},
                "expected_rps": 6000,
            },
        ]

        # Add tool call if available
        if self.available_tools:
            tool = self.available_tools[0]
            tool_args = self._get_smart_tool_arguments(tool)

            operations.append(
                {
                    "name": f"Tool Call ({tool['name']})",
                    "message": {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {"name": tool["name"], "arguments": tool_args},
                    },
                    "expected_rps": 3000,  # Lower expectation for complex tools
                }
            )

        # Add resource read if available
        if self.available_resources:
            resource = self.available_resources[0]
            operations.append(
                {
                    "name": "Resource Read",
                    "message": {
                        "jsonrpc": "2.0",
                        "id": 5,
                        "method": "resources/read",
                        "params": {"uri": resource["uri"]},
                    },
                    "expected_rps": 4000,
                }
            )

        for operation in operations:
            print(f"\n🎯 Testing {operation['name']}")

            result = await self._test_single_mcp_operation(
                operation, concurrency=20, duration=self.test_config["baseline_duration"]
            )
            self.results.append(result)

            # Performance evaluation
            expected = operation.get("expected_rps", 1000)

            if result.rps >= expected:
                status = "🎉"
                performance = f"Exceeds target ({expected:,} RPS)"
            elif result.rps >= expected * 0.8:
                status = "✅"
                performance = f"Meets target ({expected:,} RPS)"
            elif result.rps >= expected * 0.5:
                status = "⚠️"
                performance = f"Below target ({expected:,} RPS)"
            else:
                status = "❌"
                performance = f"Poor performance ({expected:,} RPS)"

            print(
                f"   {status} {result.rps:>8.1f} RPS | {result.avg_response_ms:>6.2f}ms avg | {result.success_rate:>5.1f}% success"
            )
            print(f"      {performance}")

    async def _test_mcp_concurrency_scaling(self):
        """Test MCP concurrency scaling characteristics"""
        print("\n⚡ Testing MCP Concurrency Scaling")
        print("-" * 60)

        # Use fastest operation for concurrency testing
        operation = {"name": "MCP Ping", "message": {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}}

        concurrency_levels = [1, 5, 10, 20, 50, 100, 200, 500, 1000]

        print("Concurrency |    RPS     | Avg(ms) | P95(ms) | Success% | Notes")
        print("-" * 70)

        peak_rps = 0
        optimal_concurrency = 1

        for concurrency in concurrency_levels:
            result = await self._test_single_mcp_operation(
                operation, concurrency, duration=self.test_config["scaling_duration"]
            )
            self.results.append(result)

            # Track peak performance
            if result.rps > peak_rps and result.success_rate > 95:
                peak_rps = result.rps
                optimal_concurrency = concurrency

            # Generate notes
            notes = ""
            if result.success_rate < 90:
                notes = "High failures"
            elif result.avg_response_ms > 100:
                notes = "High latency"
            elif len(result.mcp_errors) > 0:
                notes = f"Errors: {sum(result.mcp_errors.values())}"
            elif result.rps > peak_rps * 0.95:
                notes = "Peak performance"
            else:
                notes = "Good"

            print(
                f"{concurrency:>10} | {result.rps:>8.1f} | {result.avg_response_ms:>6.1f} | "
                f"{result.p95_response_ms:>6.1f} | {result.success_rate:>6.1f}% | {notes}"
            )

            # Stop if performance degrades significantly
            if result.success_rate < 50:
                print("      ⚠️  Severe performance degradation, stopping concurrency test")
                break

            # Brief cooldown between tests
            await asyncio.sleep(1.0)

        print(f"\n🏆 Optimal Concurrency: {optimal_concurrency} connections")
        print(f"🚀 Peak Performance: {peak_rps:,.1f} RPS")

    async def _test_sustained_mcp_load(self):
        """Test sustained MCP load performance"""
        print("\n🔥 Testing Sustained MCP Load Performance")
        print("-" * 60)

        operation = {
            "name": "MCP Tools List",
            "message": {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        }

        concurrency = 100
        durations = [10, 30, 60]

        print("Duration |    RPS     | Avg(ms) | P95(ms) | Success% | Stability")
        print("-" * 65)

        baseline_rps = None

        for duration in durations:
            print(f"Testing {duration}s load...", end=" ", flush=True)

            result = await self._test_single_mcp_operation(operation, concurrency, duration)
            self.results.append(result)

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
                f"{result.p95_response_ms:>6.1f} | {result.success_rate:>6.1f}% | {stability}"
            )

            # Brief cooldown
            await asyncio.sleep(2.0)

    async def _test_maximum_mcp_throughput(self):
        """Find maximum sustainable MCP throughput"""
        print("\n🚀 Finding Maximum Sustainable MCP Throughput")
        print("-" * 60)

        operation = {"name": "MCP Ping", "message": {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}}

        # Binary search for maximum concurrency
        low = 100
        high = self.test_config["max_concurrency"]
        best_rps = 0
        best_concurrency = 100

        print("Searching for maximum MCP throughput...")

        while low <= high and high - low > 50:
            mid = (low + high) // 2
            print(f"  Testing {mid:,} connections...", end=" ", flush=True)

            result = await self._test_single_mcp_operation(operation, mid, duration=8.0)

            print(f"{result.rps:>8.1f} RPS, {result.success_rate:>5.1f}% success")

            if result.success_rate >= 95:
                if result.rps > best_rps:
                    best_rps = result.rps
                    best_concurrency = mid
                low = mid + 50
            else:
                high = mid - 50

        print("\n🏆 Maximum Sustainable MCP Throughput:")
        print(f"   Concurrency: {best_concurrency:,} connections")
        print(f"   Throughput: {best_rps:,.1f} RPS")

    async def _test_mcp_error_handling(self):
        """Test MCP error handling and recovery"""
        print("\n🛡️  Testing MCP Error Handling")
        print("-" * 60)

        error_operations = [
            {"name": "Invalid JSON-RPC", "message": {"invalid": "not_jsonrpc"}, "expected_error": "parse_error"},
            {
                "name": "Unknown Method",
                "message": {"jsonrpc": "2.0", "id": 1, "method": "unknown/method", "params": {}},
                "expected_error": "method_not_found",
            },
            {
                "name": "Invalid Tool Call",
                "message": {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "nonexistent"}},
                "expected_error": "invalid_params",
            },
        ]

        for error_op in error_operations:
            print(f"Testing {error_op['name']}...", end=" ")

            result = await self._test_single_mcp_operation(error_op, concurrency=10, duration=3.0)

            total_errors = sum(result.mcp_errors.values())
            error_handled = total_errors > 0 and result.total_requests > 0

            status = "✅" if error_handled else "❌"
            print(f"{status} {total_errors} errors handled properly")

    async def _test_single_mcp_operation(
        self, operation: dict[str, Any], concurrency: int, duration: float
    ) -> MCPPerformanceResult:
        """Test a single MCP operation with specified concurrency and duration"""

        async def mcp_worker(worker_id: int, client: httpx.AsyncClient):
            """Worker function for MCP performance testing"""
            times = []
            successes = 0
            failures = 0
            mcp_errors = {}
            total_bytes = 0

            headers = self._get_headers()
            end_time = time.time() + duration

            while time.time() < end_time:
                start = time.time()

                try:
                    # Create unique message ID
                    message = operation["message"].copy()
                    if "id" in message:
                        message["id"] = f"{worker_id}_{int(time.time() * 1000000) % 1000000}"

                    response = await client.post(self.mcp_url, json=message, headers=headers)
                    response_text = await response.aread()
                    total_bytes += len(response_text)

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if "error" in data:
                                # MCP protocol error
                                error_code = data["error"].get("code", "unknown")
                                mcp_errors[f"mcp_{error_code}"] = mcp_errors.get(f"mcp_{error_code}", 0) + 1
                                failures += 1
                            else:
                                successes += 1
                        except Exception:
                            failures += 1
                            mcp_errors["json_decode"] = mcp_errors.get("json_decode", 0) + 1
                    else:
                        failures += 1
                        mcp_errors[f"http_{response.status_code}"] = (
                            mcp_errors.get(f"http_{response.status_code}", 0) + 1
                        )

                except httpx.TimeoutException:
                    failures += 1
                    mcp_errors["timeout"] = mcp_errors.get("timeout", 0) + 1
                except Exception as e:
                    failures += 1
                    error_key = type(e).__name__
                    mcp_errors[error_key] = mcp_errors.get(error_key, 0) + 1

                elapsed = time.time() - start
                times.append(elapsed)

                # Brief delay to prevent overwhelming
                await asyncio.sleep(0.001)

            return times, successes, failures, mcp_errors, total_bytes

        # Execute test with workers
        start_time = time.time()

        try:
            # Use persistent connections for performance
            async with httpx.AsyncClient(limits=self.limits, timeout=self.test_config["timeout_seconds"]) as client:
                # Create worker tasks
                tasks = [mcp_worker(i, client) for i in range(concurrency)]

                # Run with timeout
                worker_results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True), timeout=duration + 10.0
                )

            actual_duration = time.time() - start_time

            # Aggregate results
            all_times = []
            total_successes = 0
            total_failures = 0
            all_mcp_errors = {}
            total_bytes = 0

            for result in worker_results:
                if isinstance(result, Exception):
                    total_failures += 1
                    error_key = type(result).__name__
                    all_mcp_errors[error_key] = all_mcp_errors.get(error_key, 0) + 1
                else:
                    times, successes, failures, mcp_errors, bytes_transferred = result
                    all_times.extend(times)
                    total_successes += successes
                    total_failures += failures
                    total_bytes += bytes_transferred

                    # Merge MCP errors
                    for key, count in mcp_errors.items():
                        all_mcp_errors[key] = all_mcp_errors.get(key, 0) + count

            # Calculate statistics
            total_requests = total_successes + total_failures
            rps = total_requests / actual_duration if actual_duration > 0 else 0
            success_rate = (total_successes / total_requests * 100) if total_requests > 0 else 0
            throughput_mb_per_sec = (total_bytes / (1024 * 1024)) / actual_duration if actual_duration > 0 else 0

            if all_times:
                avg_time = statistics.mean(all_times)
                min_time = min(all_times)
                max_time = max(all_times)
                sorted_times = sorted(all_times)
                p95_time = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
                p99_time = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
            else:
                avg_time = min_time = max_time = p95_time = p99_time = 0

            return MCPPerformanceResult(
                operation=operation["name"],
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
                p99_response_ms=p99_time * 1000,
                success_rate=success_rate,
                mcp_errors=all_mcp_errors,
                throughput_mb_per_sec=throughput_mb_per_sec,
                session_info={"session_id": self.session_id, "server_info": self.server_info},
            )

        except TimeoutError:
            return MCPPerformanceResult(
                operation=operation["name"],
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
                p99_response_ms=0,
                success_rate=0,
                mcp_errors={"timeout": 1},
                throughput_mb_per_sec=0,
                session_info={"session_id": self.session_id, "server_info": self.server_info},
            )

    def _generate_mcp_performance_report(self):
        """Generate comprehensive MCP performance report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE MCP PROTOCOL PERFORMANCE REPORT")
        print("=" * 80)

        if not self.results:
            print("❌ No results to report")
            return

        # Find best performing operations
        best_rps = max(self.results, key=lambda r: r.rps)
        best_latency = min(self.results, key=lambda r: r.avg_response_ms)
        best_throughput = max(self.results, key=lambda r: r.throughput_mb_per_sec)

        print("🚀 Peak MCP Performance:")
        print(f"   Best RPS: {best_rps.rps:,.1f} ({best_rps.operation})")
        print(f"   Best Latency: {best_latency.avg_response_ms:.2f}ms ({best_latency.operation})")
        print(f"   Best Throughput: {best_throughput.throughput_mb_per_sec:.1f} MB/s")

        # Overall statistics
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        total_mcp_errors = sum(sum(r.mcp_errors.values()) for r in self.results)
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0

        print("\n📈 Overall MCP Statistics:")
        print(f"   Total Requests: {total_requests:,}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")
        print(f"   Protocol Errors: {total_mcp_errors:,}")
        print(f"   Operations Tested: {len({r.operation for r in self.results})}")
        print(f"   Tools Available: {len(self.available_tools)}")
        print(f"   Resources Available: {len(self.available_resources)}")

        # Performance grading
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

        print(f"\n🏆 MCP Performance Grade: {grade}")

        # Latency analysis
        latency_results = [r for r in self.results if r.avg_response_ms > 0]
        if latency_results:
            avg_latency = statistics.mean([r.avg_response_ms for r in latency_results])
            p95_latency = statistics.mean([r.p95_response_ms for r in latency_results])

            print("\n⚡ Latency Analysis:")
            print(f"   Average Latency: {avg_latency:.2f}ms")
            print(f"   P95 Latency: {p95_latency:.2f}ms")
            print(f"   Best Latency: {best_latency.avg_response_ms:.2f}ms")

        # Recommendations
        print("\n💡 Performance Recommendations:")
        if best_rps.rps > 10000:
            print("   ✅ Excellent MCP performance! Production ready.")
            print("   🚀 Consider implementing caching for even better performance.")
        elif best_rps.rps > 5000:
            print("   ✅ Good MCP performance. Consider optimizations for higher load.")
            print("   🔧 Profile JSON-RPC parsing and tool execution paths.")
        else:
            print("   ⚠️  MCP performance could be improved.")
            print("   🔍 Check for bottlenecks in request handling and tool execution.")

        if overall_success_rate > 99:
            print("   ✅ Excellent protocol reliability.")
        elif overall_success_rate > 95:
            print("   ✅ Good protocol reliability.")
        else:
            print("   ⚠️  Protocol reliability needs attention.")

        print("\n" + "=" * 80)


async def main():
    """Main entry point for MCP performance testing"""
    mcp_url = "http://localhost:8000/mcp"

    if len(sys.argv) > 1:
        mcp_url = sys.argv[1]

    print("🧪 MCP Protocol Performance Test Suite")
    print("📝 Comprehensive evaluation of MCP protocol performance using httpx")
    print("🎯 Target: High RPS with low latency and excellent reliability")
    print()

    test = MCPPerformanceTest(mcp_url)
    success = await test.run_full_mcp_test_suite()

    if success:
        print("🎉 MCP performance testing completed successfully!")
    else:
        print("❌ MCP performance testing failed. Check server status.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
