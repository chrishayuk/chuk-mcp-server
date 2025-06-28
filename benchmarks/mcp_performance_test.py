#!/usr/bin/env python3
"""
mcp_performance_test.py - Comprehensive MCP Protocol Performance Test

Tests MCP protocol performance from the ground up, mirroring the base performance
test structure but focusing specifically on MCP JSON-RPC operations.

Progressive testing approach:
1. MCP Protocol availability and handshake
2. Individual MCP operation performance
3. Concurrency scaling for MCP operations
4. Sustained MCP load testing
5. Maximum MCP throughput discovery
6. MCP error handling and recovery
"""

import asyncio
import aiohttp
import json
import time
import statistics
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class MCPPerformanceResult:
    """MCP-specific performance test result"""
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
    success_rate: float
    mcp_errors: Dict[str, int]
    session_info: Dict[str, Any]


class MCPPerformanceTest:
    """Comprehensive MCP protocol performance testing"""
    
    def __init__(self, mcp_url: str = "http://localhost:8000/mcp"):
        self.mcp_url = mcp_url
        self.base_url = mcp_url.replace('/mcp', '')
        self.session_id: Optional[str] = None
        self.server_info: Dict[str, Any] = {}
        self.available_tools: List[Dict[str, Any]] = []
        self.available_resources: List[Dict[str, Any]] = []
        self.results: List[MCPPerformanceResult] = []
    
    async def run_full_mcp_test_suite(self):
        """Run comprehensive MCP performance test suite"""
        print("🚀 Fast MCP Server - Comprehensive MCP Protocol Performance Test")
        print(f"🔗 MCP URL: {self.mcp_url}")
        print("=" * 80)
        
        # Test MCP protocol availability
        if not await self._check_mcp_availability():
            print("❌ MCP server not available. Please start the server first:")
            print("   python -m fast_mcp_server --port 8000")
            return False
        
        # Progressive MCP testing
        await self._test_mcp_handshake_performance()
        await self._test_individual_mcp_operations()
        await self._test_mcp_concurrency_scaling()
        await self._test_sustained_mcp_load()
        await self._test_maximum_mcp_throughput()
        await self._test_mcp_error_handling()
        
        # Generate MCP-specific report
        self._generate_mcp_performance_report()
        
        return True
    
    async def _check_mcp_availability(self) -> bool:
        """Check if MCP server is available and get capabilities"""
        print("🔍 Checking MCP protocol availability...")
        
        try:
            # First check if base server is up
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/health") as resp:
                    if resp.status != 200:
                        print(f"   ❌ Base server not healthy: {resp.status}")
                        return False
                
                # Test MCP initialize
                init_success = await self._perform_mcp_initialize(session)
                if not init_success:
                    return False
                
                # Discover MCP capabilities
                await self._discover_mcp_capabilities(session)
                
                print(f"   ✅ MCP protocol available")
                print(f"   📋 Server: {self.server_info.get('name', 'unknown')} v{self.server_info.get('version', 'unknown')}")
                print(f"   🔧 Tools available: {len(self.available_tools)}")
                print(f"   📄 Resources available: {len(self.available_resources)}")
                
                return True
                
        except Exception as e:
            print(f"   ❌ MCP protocol not available: {e}")
            return False
    
    async def _perform_mcp_initialize(self, session: aiohttp.ClientSession) -> bool:
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
                    "clientInfo": {"name": "mcp-perf-test", "version": "1.0.0"}
                }
            }
            
            async with session.post(self.mcp_url, json=init_message, headers=headers) as resp:
                if resp.status == 200:
                    self.session_id = resp.headers.get('Mcp-Session-Id')
                    data = await resp.json()
                    
                    if 'result' in data and 'serverInfo' in data['result']:
                        self.server_info = data['result']['serverInfo']
                        
                        # Send initialized notification
                        if self.session_id:
                            headers['Mcp-Session-Id'] = self.session_id
                        
                        init_notif = {
                            "jsonrpc": "2.0",
                            "method": "notifications/initialized",
                            "params": {}
                        }
                        
                        async with session.post(self.mcp_url, json=init_notif, headers=headers) as notif_resp:
                            return notif_resp.status == 204
                    
                return False
                
        except Exception:
            return False
    
    async def _discover_mcp_capabilities(self, session: aiohttp.ClientSession):
        """Discover available MCP tools and resources"""
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers['Mcp-Session-Id'] = self.session_id
        
        try:
            # Get tools
            tools_msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            async with session.post(self.mcp_url, json=tools_msg, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'result' in data and 'tools' in data['result']:
                        self.available_tools = data['result']['tools']
            
            # Get resources
            resources_msg = {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}}
            async with session.post(self.mcp_url, json=resources_msg, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'result' in data and 'resources' in data['result']:
                        self.available_resources = data['result']['resources']
                        
        except Exception:
            pass
    
    async def _test_mcp_handshake_performance(self):
        """Test MCP handshake performance"""
        print("\n🤝 Testing MCP Handshake Performance")
        print("-" * 60)
        
        # Test multiple initialize sequences
        handshake_times = []
        success_count = 0
        
        for i in range(10):
            start_time = time.time()
            try:
                timeout = aiohttp.ClientTimeout(total=10.0)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    if await self._perform_mcp_initialize(session):
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
            print(f"      Success rate: {success_rate:.1f}% | Target: Sub-second handshake")
    
    async def _test_individual_mcp_operations(self):
        """Test individual MCP operations for baseline performance"""
        print("\n📊 Testing Individual MCP Operations")
        print("-" * 60)
        
        # Define MCP operations to test
        operations = [
            {
                "name": "Ping", 
                "message": {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}},
                "expected_rps": 12000
            },
            {
                "name": "Tools List",
                "message": {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                "expected_rps": 8000
            },
            {
                "name": "Resources List", 
                "message": {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}},
                "expected_rps": 8000
            }
        ]
        
        # Add tool call if tools are available
        if self.available_tools:
            tool = self.available_tools[0]
            tool_args = {}
            
            # Provide appropriate arguments based on tool name
            if tool['name'] == 'add':
                tool_args = {"a": 5, "b": 3}
            elif tool['name'] == 'hello':
                tool_args = {"name": "test"}
            
            operations.append({
                "name": f"Tool Call ({tool['name']})",
                "message": {
                    "jsonrpc": "2.0", "id": 4, "method": "tools/call",
                    "params": {"name": tool['name'], "arguments": tool_args}
                },
                "expected_rps": 5000
            })
        
        # Add resource read if resources are available
        if self.available_resources:
            resource = self.available_resources[0]
            operations.append({
                "name": f"Resource Read",
                "message": {
                    "jsonrpc": "2.0", "id": 5, "method": "resources/read",
                    "params": {"uri": resource['uri']}
                },
                "expected_rps": 6000
            })
        
        for operation in operations:
            print(f"\n🎯 Testing {operation['name']}")
            
            result = await self._test_single_mcp_operation(operation, concurrency=10, duration=3.0)
            self.results.append(result)
            
            # Check performance against expectations
            expected = operation.get('expected_rps', 1000)
            status = "✅" if result.rps >= expected * 0.8 else "⚠️" if result.rps >= expected * 0.5 else "❌"
            
            print(f"   {status} {result.rps:>8.1f} RPS | {result.avg_response_ms:>6.2f}ms avg | {result.success_rate:>5.1f}% success")
            
            if result.rps >= expected:
                print(f"      🎉 Exceeds target ({expected:,} RPS)")
            elif result.rps >= expected * 0.8:
                print(f"      ✅ Meets target ({expected:,} RPS)")
            else:
                print(f"      ⚠️  Below target ({expected:,} RPS)")
    
    async def _test_mcp_concurrency_scaling(self):
        """Test MCP concurrency scaling"""
        print("\n⚡ Testing MCP Concurrency Scaling")
        print("-" * 60)
        
        # Use ping for concurrency testing (fastest operation)
        operation = {
            "name": "MCP Ping",
            "message": {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}
        }
        
        concurrency_levels = [1, 5, 10, 20, 50, 100, 200, 500, 1000]
        
        print("Concurrency |    RPS     | Avg(ms) | Success% | MCP Notes")
        print("-" * 65)
        
        peak_rps = 0
        optimal_concurrency = 1
        
        for concurrency in concurrency_levels:
            result = await self._test_single_mcp_operation(operation, concurrency, duration=5.0)
            self.results.append(result)
            
            # Track peak performance
            if result.rps > peak_rps and result.success_rate > 95:
                peak_rps = result.rps
                optimal_concurrency = concurrency
            
            # Format output with MCP-specific notes
            notes = ""
            if result.success_rate < 90:
                notes = "High MCP failures"
            elif result.avg_response_ms > 100:
                notes = "High JSON-RPC latency"
            elif len(result.mcp_errors) > 0:
                notes = f"MCP errors: {sum(result.mcp_errors.values())}"
            elif result.rps > peak_rps * 0.95:
                notes = "Peak MCP performance"
            
            print(f"{concurrency:>10} | {result.rps:>8.1f} | {result.avg_response_ms:>6.1f} | "
                  f"{result.success_rate:>6.1f}% | {notes}")
            
            # Stop if MCP protocol breaks down
            if result.success_rate < 50:
                print("      ⚠️  MCP protocol breakdown, stopping test")
                break
            
            await asyncio.sleep(1.0)
        
        print(f"\n🏆 Optimal MCP Concurrency: {optimal_concurrency} connections")
        print(f"🚀 Peak MCP Performance: {peak_rps:,.1f} RPS")
    
    async def _test_sustained_mcp_load(self):
        """Test sustained MCP load performance"""
        print("\n🔥 Testing Sustained MCP Load Performance")
        print("-" * 60)
        
        operation = {
            "name": "MCP Tools List",
            "message": {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        }
        
        concurrency = 100
        durations = [10, 30, 60]
        
        print("Duration |    RPS     | Avg(ms) | Success% | MCP Stability")
        print("-" * 60)
        
        baseline_rps = None
        
        for duration in durations:
            print(f"Testing {duration}s MCP load...", end=" ", flush=True)
            
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
            
            print(f"\r{duration:>6}s | {result.rps:>8.1f} | {result.avg_response_ms:>6.1f} | "
                  f"{result.success_rate:>6.1f}% | {stability}")
    
    async def _test_maximum_mcp_throughput(self):
        """Find maximum sustainable MCP throughput"""
        print("\n🚀 Finding Maximum Sustainable MCP Throughput")
        print("-" * 60)
        
        operation = {
            "name": "MCP Ping",
            "message": {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}
        }
        
        # Binary search for maximum MCP concurrency
        low = 100
        high = 10000
        best_rps = 0
        best_concurrency = 100
        
        print("Searching for maximum MCP throughput...")
        
        while low <= high and high - low > 50:
            mid = (low + high) // 2
            print(f"  Testing {mid:,} MCP connections...", end=" ", flush=True)
            
            result = await self._test_single_mcp_operation(operation, mid, duration=10.0)
            
            print(f"{result.rps:>8.1f} RPS, {result.success_rate:>5.1f}% success")
            
            if result.success_rate >= 95:
                if result.rps > best_rps:
                    best_rps = result.rps
                    best_concurrency = mid
                low = mid + 50
            else:
                high = mid - 50
        
        print(f"\n🏆 Maximum Sustainable MCP Throughput:")
        print(f"   Concurrency: {best_concurrency:,} MCP connections")
        print(f"   Throughput: {best_rps:,.1f} MCP RPS")
    
    async def _test_mcp_error_handling(self):
        """Test MCP error handling and recovery"""
        print("\n🛡️  Testing MCP Error Handling and Recovery")
        print("-" * 60)
        
        # Test various MCP error scenarios
        error_operations = [
            {
                "name": "Invalid JSON-RPC",
                "message": {"invalid": "not_jsonrpc"},
                "expected": "parse_error"
            },
            {
                "name": "Unknown Method",
                "message": {"jsonrpc": "2.0", "id": 1, "method": "unknown/method", "params": {}},
                "expected": "method_not_found"
            },
            {
                "name": "Invalid Params",
                "message": {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"invalid": "params"}},
                "expected": "invalid_params"
            }
        ]
        
        for error_op in error_operations:
            print(f"Testing {error_op['name']}...", end=" ")
            
            result = await self._test_single_mcp_operation(error_op, concurrency=20, duration=3.0)
            
            # For error operations, we expect controlled failures
            total_errors = sum(result.mcp_errors.values())
            error_handled = total_errors > 0 and result.total_requests > 0
            
            status = "✅" if error_handled else "❌"
            print(f"{status} {total_errors} MCP errors handled properly")
    
    async def _test_single_mcp_operation(
        self, 
        operation: Dict[str, Any], 
        concurrency: int, 
        duration: float
    ) -> MCPPerformanceResult:
        """Test a single MCP operation with given concurrency"""
        
        async def mcp_worker(worker_id: int):
            """Worker function for MCP testing"""
            times = []
            successes = 0
            failures = 0
            mcp_errors = {}
            
            headers = {"Content-Type": "application/json"}
            if self.session_id:
                headers['Mcp-Session-Id'] = self.session_id
            
            timeout = aiohttp.ClientTimeout(total=30.0)
            
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    end_time = time.time() + duration
                    
                    while time.time() < end_time:
                        start = time.time()
                        
                        try:
                            # Create unique message for each request
                            message = operation['message'].copy()
                            if 'id' in message:
                                message['id'] = f"{worker_id}_{int(time.time() * 1000000) % 1000000}"
                            
                            async with session.post(self.mcp_url, json=message, headers=headers) as resp:
                                response_text = await resp.text()
                                
                                if resp.status == 200:
                                    try:
                                        data = json.loads(response_text)
                                        if 'error' in data:
                                            # MCP protocol error
                                            error_code = data['error'].get('code', 'unknown')
                                            mcp_errors[f"mcp_{error_code}"] = mcp_errors.get(f"mcp_{error_code}", 0) + 1
                                            failures += 1
                                        else:
                                            successes += 1
                                    except json.JSONDecodeError:
                                        failures += 1
                                        mcp_errors["json_decode"] = mcp_errors.get("json_decode", 0) + 1
                                else:
                                    failures += 1
                                    mcp_errors[f"http_{resp.status}"] = mcp_errors.get(f"http_{resp.status}", 0) + 1
                        
                        except asyncio.TimeoutError:
                            failures += 1
                            mcp_errors["timeout"] = mcp_errors.get("timeout", 0) + 1
                        except Exception as e:
                            failures += 1
                            error_key = type(e).__name__
                            mcp_errors[error_key] = mcp_errors.get(error_key, 0) + 1
                        
                        elapsed = time.time() - start
                        times.append(elapsed)
                        
                        # Small delay to prevent overwhelming
                        await asyncio.sleep(0.001)
            
            except Exception:
                if not times:
                    times = [duration]
                failures += 1
            
            return times, successes, failures, mcp_errors
        
        # Run MCP workers
        start_time = time.time()
        
        try:
            tasks = [mcp_worker(i) for i in range(concurrency)]
            worker_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=duration + 30.0
            )
            
            actual_duration = time.time() - start_time
            
            # Aggregate results
            all_times = []
            total_successes = 0
            total_failures = 0
            all_mcp_errors = {}
            
            for result in worker_results:
                if isinstance(result, Exception):
                    total_failures += 1
                    error_key = type(result).__name__
                    all_mcp_errors[error_key] = all_mcp_errors.get(error_key, 0) + 1
                else:
                    times, successes, failures, mcp_errors = result
                    all_times.extend(times)
                    total_successes += successes
                    total_failures += failures
                    
                    # Merge MCP errors
                    for key, count in mcp_errors.items():
                        all_mcp_errors[key] = all_mcp_errors.get(key, 0) + count
            
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
            
            return MCPPerformanceResult(
                operation=operation['name'],
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
                mcp_errors=all_mcp_errors,
                session_info={"session_id": self.session_id, "server_info": self.server_info}
            )
        
        except asyncio.TimeoutError:
            return MCPPerformanceResult(
                operation=operation['name'],
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
                mcp_errors={"timeout": 1},
                session_info={"session_id": self.session_id, "server_info": self.server_info}
            )
    
    def _generate_mcp_performance_report(self):
        """Generate comprehensive MCP performance report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE MCP PROTOCOL PERFORMANCE REPORT")
        print("=" * 80)
        
        if not self.results:
            print("No MCP results to report")
            return
        
        # Find best performing MCP operations
        best_rps = max(self.results, key=lambda r: r.rps)
        best_latency = min(self.results, key=lambda r: r.avg_response_ms)
        
        print(f"🚀 Peak MCP Performance:")
        print(f"   Best RPS: {best_rps.rps:,.1f} ({best_rps.operation})")
        print(f"   Best Latency: {best_latency.avg_response_ms:.2f}ms ({best_latency.operation})")
        
        # MCP-specific statistics
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        total_mcp_errors = sum(sum(r.mcp_errors.values()) for r in self.results)
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        
        print(f"\n📈 MCP Protocol Statistics:")
        print(f"   Total MCP Requests: {total_requests:,}")
        print(f"   MCP Success Rate: {overall_success_rate:.1f}%")
        print(f"   MCP Protocol Errors: {total_mcp_errors:,}")
        print(f"   MCP Operations Tested: {len(set(r.operation for r in self.results))}")
        print(f"   Available Tools: {len(self.available_tools)}")
        print(f"   Available Resources: {len(self.available_resources)}")
        
        # MCP Performance grade
        if best_rps.rps > 15000:
            grade = "S+ (Exceptional MCP)"
        elif best_rps.rps > 10000:
            grade = "S (Excellent MCP)"
        elif best_rps.rps > 5000:
            grade = "A (Very Good MCP)"
        elif best_rps.rps > 1000:
            grade = "B (Good MCP)"
        else:
            grade = "C (MCP Needs Improvement)"
        
        print(f"\n🏆 MCP Performance Grade: {grade}")
        
        # MCP-specific recommendations
        print(f"\n💡 MCP Protocol Recommendations:")
        if best_rps.rps > 10000:
            print("   ✅ Excellent MCP performance! Protocol is production-ready.")
            print("   🚀 Consider implementing tool/resource caching for even better performance.")
            print("   📡 Ready for high-frequency MCP client integration.")
        elif best_rps.rps > 5000:
            print("   ✅ Good MCP performance. Consider optimizations for higher tool load.")
            print("   🔧 Profile MCP message parsing and tool execution paths.")
        else:
            print("   ⚠️  MCP performance could be improved.")
            print("   🔍 Check for bottlenecks in JSON-RPC handling and tool execution.")
        
        # Protocol compliance
        if overall_success_rate > 99:
            print("   ✅ Excellent MCP protocol compliance.")
        elif overall_success_rate > 95:
            print("   ✅ Good MCP protocol compliance.")
        else:
            print("   ⚠️  MCP protocol compliance issues detected.")
        
        print("\n" + "=" * 80)


async def main():
    """Main entry point"""
    mcp_url = "http://localhost:8000/mcp"
    
    if len(sys.argv) > 1:
        mcp_url = sys.argv[1]
    
    print("🧪 Fast MCP Server - MCP Protocol Performance Testing")
    print(f"📝 This test comprehensively evaluates MCP protocol performance")
    print(f"🎯 Target: 10,000+ MCP RPS with sub-millisecond JSON-RPC latency")
    print()
    
    test = MCPPerformanceTest(mcp_url)
    success = await test.run_full_mcp_test_suite()
    
    if success:
        print("🎉 MCP performance testing completed successfully!")
    else:
        print("❌ MCP performance testing failed. Check MCP server status.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())