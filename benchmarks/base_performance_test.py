#!/usr/bin/env python3
"""
base_performance_test.py - Comprehensive Base Performance Test

Tests raw performance of the Fast MCP Server from the ground up,
starting with basic HTTP endpoints before testing MCP protocol specifics.

This script progressively tests:
1. Basic HTTP endpoints (ping, health, info)
2. Concurrency scaling 
3. Load testing with various patterns
4. Maximum sustainable throughput
5. Error handling under stress
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
    error_details: Dict[str, int]


class FastServerPerformanceTest:
    """Comprehensive performance testing for Fast MCP Server"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.results: List[PerformanceResult] = []
    
    async def run_full_test_suite(self):
        """Run comprehensive performance test suite"""
        print("🚀 Fast MCP Server - Comprehensive Performance Test")
        print(f"🔗 Base URL: {self.base_url}")
        print("=" * 80)
        
        # Test server availability first
        if not await self._check_server_availability():
            print("❌ Server not available. Please start the server first:")
            print("   python -m fast_mcp_server --port 8000")
            return False
        
        # Progressive testing
        await self._test_basic_endpoints()
        await self._test_concurrency_scaling()
        await self._test_sustained_load()
        await self._test_maximum_throughput()
        await self._test_error_handling()
        
        # Generate final report
        self._generate_performance_report()
        
        return True
    
    async def _check_server_availability(self) -> bool:
        """Check if server is available and responsive"""
        print("🔍 Checking server availability...")
        
        try:
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"   ✅ Server available: {data.get('status', 'unknown')}")
                        
                        # Get server info
                        async with session.get(f"{self.base_url}/") as info_resp:
                            if info_resp.status == 200:
                                info_data = await info_resp.json()
                                print(f"   📋 Server: {info_data.get('server', 'unknown')} v{info_data.get('version', 'unknown')}")
                                print(f"   📊 Current RPS: {info_data.get('performance', {}).get('current_rps', 0):.1f}")
                        
                        return True
                    else:
                        print(f"   ❌ Server returned status {resp.status}")
                        return False
        except Exception as e:
            print(f"   ❌ Server not available: {e}")
            return False
    
    async def _test_basic_endpoints(self):
        """Test basic HTTP endpoints for baseline performance"""
        print("\n📊 Testing Basic HTTP Endpoints")
        print("-" * 60)
        
        # Define test endpoints
        endpoints = [
            {"path": "/ping", "method": "GET", "name": "Ultra-Fast Ping", "expected_rps": 15000},
            {"path": "/health", "method": "GET", "name": "Health Check", "expected_rps": 12000},
            {"path": "/version", "method": "GET", "name": "Version Info", "expected_rps": 10000},
            {"path": "/", "method": "GET", "name": "Server Info", "expected_rps": 8000},
            {"path": "/metrics", "method": "GET", "name": "Metrics", "expected_rps": 6000},
        ]
        
        for endpoint in endpoints:
            print(f"\n🎯 Testing {endpoint['name']} ({endpoint['method']} {endpoint['path']})")
            
            # Test with low concurrency first
            result = await self._test_single_endpoint(endpoint, concurrency=10, duration=3.0)
            self.results.append(result)
            
            # Check if meets expectations
            expected = endpoint.get('expected_rps', 1000)
            status = "✅" if result.rps >= expected * 0.8 else "⚠️" if result.rps >= expected * 0.5 else "❌"
            
            print(f"   {status} {result.rps:>8.1f} RPS | {result.avg_response_ms:>6.2f}ms avg | {result.success_rate:>5.1f}% success")
            
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
        
        # Use the fastest endpoint for concurrency testing
        endpoint = {"path": "/ping", "method": "GET", "name": "Ping"}
        concurrency_levels = [1, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]
        
        print("Concurrency |    RPS     | Avg(ms) | Success% | Notes")
        print("-" * 60)
        
        peak_rps = 0
        optimal_concurrency = 1
        
        for concurrency in concurrency_levels:
            result = await self._test_single_endpoint(endpoint, concurrency, duration=5.0)
            self.results.append(result)
            
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
            
            print(f"{concurrency:>10} | {result.rps:>8.1f} | {result.avg_response_ms:>6.1f} | "
                  f"{result.success_rate:>6.1f}% | {notes}")
            
            # Stop if performance severely degrades
            if result.success_rate < 50:
                print("      ⚠️  High failure rate, stopping concurrency test")
                break
            
            # Add delay between tests
            await asyncio.sleep(1.0)
        
        print(f"\n🏆 Optimal Concurrency: {optimal_concurrency} connections")
        print(f"🚀 Peak Performance: {peak_rps:,.1f} RPS")
    
    async def _test_sustained_load(self):
        """Test sustained load performance"""
        print("\n🔥 Testing Sustained Load Performance")
        print("-" * 60)
        
        endpoint = {"path": "/health", "method": "GET", "name": "Health"}
        concurrency = 100
        durations = [10, 30, 60]  # Test for different durations
        
        print("Duration |    RPS     | Avg(ms) | Success% | Stability")
        print("-" * 60)
        
        baseline_rps = None
        
        for duration in durations:
            print(f"Testing {duration}s load...", end=" ", flush=True)
            
            result = await self._test_single_endpoint(endpoint, concurrency, duration)
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
    
    async def _test_maximum_throughput(self):
        """Find maximum sustainable throughput"""
        print("\n🚀 Finding Maximum Sustainable Throughput")
        print("-" * 60)
        
        endpoint = {"path": "/ping", "method": "GET", "name": "Ping"}
        
        # Binary search for maximum concurrency
        low = 100
        high = 10000
        best_rps = 0
        best_concurrency = 100
        
        print("Searching for maximum throughput...")
        
        while low <= high and high - low > 50:
            mid = (low + high) // 2
            print(f"  Testing {mid:,} connections...", end=" ", flush=True)
            
            result = await self._test_single_endpoint(endpoint, mid, duration=10.0)
            
            print(f"{result.rps:>8.1f} RPS, {result.success_rate:>5.1f}% success")
            
            if result.success_rate >= 95:
                if result.rps > best_rps:
                    best_rps = result.rps
                    best_concurrency = mid
                low = mid + 50
            else:
                high = mid - 50
        
        print(f"\n🏆 Maximum Sustainable Throughput:")
        print(f"   Concurrency: {best_concurrency:,} connections")
        print(f"   Throughput: {best_rps:,.1f} RPS")
    
    async def _test_error_handling(self):
        """Test error handling and recovery"""
        print("\n🛡️  Testing Error Handling and Recovery")
        print("-" * 60)
        
        # Test invalid endpoints
        error_endpoints = [
            {"path": "/nonexistent", "method": "GET", "name": "404 Errors"},
            {"path": "/mcp", "method": "POST", "name": "Invalid JSON-RPC", "data": {"invalid": "data"}},
            {"path": "/mcp", "method": "GET", "name": "Wrong Method"},
        ]
        
        for endpoint in error_endpoints:
            print(f"Testing {endpoint['name']}...", end=" ")
            
            result = await self._test_single_endpoint(endpoint, concurrency=50, duration=3.0)
            
            # For error endpoints, we expect failures
            if endpoint['name'] == "404 Errors":
                expected_status = result.failed_requests > result.successful_requests
                status = "✅" if expected_status else "❌"
                print(f"{status} {result.failed_requests} errors handled properly")
            else:
                # Check that server handles errors gracefully without crashing
                status = "✅" if result.total_requests > 0 else "❌"
                print(f"{status} Server remained responsive")
    
    async def _test_single_endpoint(
        self, 
        endpoint: Dict[str, Any], 
        concurrency: int, 
        duration: float
    ) -> PerformanceResult:
        """Test a single endpoint with given concurrency"""
        
        async def worker(worker_id: int):
            """Worker function for load testing"""
            times = []
            successes = 0
            failures = 0
            error_details = {}
            
            timeout = aiohttp.ClientTimeout(total=30.0)
            
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    end_time = time.time() + duration
                    
                    while time.time() < end_time:
                        start = time.time()
                        
                        try:
                            url = f"{self.base_url}{endpoint['path']}"
                            
                            if endpoint['method'] == 'GET':
                                async with session.get(url) as resp:
                                    await resp.text()  # Read response
                                    if 200 <= resp.status < 300:
                                        successes += 1
                                    else:
                                        failures += 1
                                        error_key = f"HTTP_{resp.status}"
                                        error_details[error_key] = error_details.get(error_key, 0) + 1
                            
                            elif endpoint['method'] == 'POST':
                                data = endpoint.get('data', {})
                                async with session.post(url, json=data) as resp:
                                    await resp.text()  # Read response
                                    if 200 <= resp.status < 300:
                                        successes += 1
                                    else:
                                        failures += 1
                                        error_key = f"HTTP_{resp.status}"
                                        error_details[error_key] = error_details.get(error_key, 0) + 1
                        
                        except asyncio.TimeoutError:
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
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=duration + 30.0
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
                error_details=all_error_details
            )
        
        except asyncio.TimeoutError:
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
                error_details={"timeout": 1}
            )
    
    def _generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE PERFORMANCE REPORT")
        print("=" * 80)
        
        if not self.results:
            print("No results to report")
            return
        
        # Find best performing endpoints
        best_rps = max(self.results, key=lambda r: r.rps)
        best_latency = min(self.results, key=lambda r: r.avg_response_ms)
        
        print(f"🚀 Peak Performance:")
        print(f"   Best RPS: {best_rps.rps:,.1f} ({best_rps.endpoint})")
        print(f"   Best Latency: {best_latency.avg_response_ms:.2f}ms ({best_latency.endpoint})")
        
        # Calculate overall statistics
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Requests: {total_requests:,}")
        print(f"   Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"   Endpoints Tested: {len(set(r.endpoint for r in self.results))}")
        
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
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if best_rps.rps > 10000:
            print("   ✅ Excellent performance! Server is production-ready.")
            print("   🚀 Consider scaling horizontally with multiple workers.")
        elif best_rps.rps > 5000:
            print("   ✅ Good performance. Consider optimizations for higher load.")
            print("   🔧 Profile hotspots and optimize critical paths.")
        else:
            print("   ⚠️  Performance could be improved.")
            print("   🔍 Check for bottlenecks in request handling.")
        
        print("\n" + "=" * 80)


async def main():
    """Main entry point"""
    base_url = "http://localhost:8000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print("🧪 Fast MCP Server - Base Performance Testing")
    print(f"📝 This test will comprehensively evaluate server performance")
    print(f"🎯 Target: 10,000+ RPS with sub-millisecond latency")
    print()
    
    test = FastServerPerformanceTest(base_url)
    success = await test.run_full_test_suite()
    
    if success:
        print("🎉 Performance testing completed successfully!")
    else:
        print("❌ Performance testing failed. Check server status.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())