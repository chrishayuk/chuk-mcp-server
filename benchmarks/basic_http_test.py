#!/usr/bin/env python3
"""
basic_http_test.py - Focus on basic HTTP endpoint performance

Tests just the fundamental HTTP endpoints to establish baseline performance
before moving to MCP protocol testing.
"""

import asyncio
import httpx
import time
import statistics
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class BasicResult:
    """Simple performance result"""
    endpoint: str
    rps: float
    avg_ms: float
    min_ms: float
    max_ms: float
    success_rate: float
    total_requests: int
    errors: Dict[str, int]


class BasicHTTPTest:
    """Focus on basic HTTP endpoint performance"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.results: List[BasicResult] = []
    
    async def run_basic_tests(self):
        """Run focused basic HTTP tests"""
        print("🔧 Basic HTTP Endpoint Performance Test")
        print(f"🔗 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test individual endpoints
        await self._test_individual_endpoints()
        
        # Test best endpoint with different concurrency levels
        await self._test_concurrency_levels()
        
        # Generate focused report
        self._generate_basic_report()
        
        return True
    
    async def _test_individual_endpoints(self):
        """Test each endpoint individually"""
        print("\n📊 Testing Individual HTTP Endpoints")
        print("-" * 50)
        
        endpoints = [
            {"path": "/health", "name": "Health Check", "target_rps": 8000},
            {"path": "/", "name": "Root/Info", "target_rps": 5000},
            {"path": "/ping", "name": "Ping", "target_rps": 10000},
            {"path": "/mcp", "name": "MCP GET", "target_rps": 6000},
            {"path": "/docs", "name": "Docs", "target_rps": 3000},
            {"path": "/version", "name": "Version", "target_rps": 8000},
        ]
        
        for endpoint in endpoints:
            print(f"\n🎯 Testing {endpoint['name']} ({endpoint['path']})")
            
            # Quick availability check first
            available = await self._check_endpoint_availability(endpoint['path'])
            if not available:
                print(f"   ❌ Endpoint not available")
                continue
            
            # Performance test
            result = await self._test_single_endpoint(
                endpoint['path'], 
                endpoint['name'],
                concurrency=10, 
                duration=3.0
            )
            
            if result:
                self.results.append(result)
                target = endpoint['target_rps']
                
                # Status determination
                if result.success_rate < 50:
                    status = "❌ FAIL"
                elif result.rps >= target * 0.9:
                    status = "✅ EXCELLENT"
                elif result.rps >= target * 0.7:
                    status = "⚠️  GOOD"
                elif result.rps >= target * 0.5:
                    status = "⚠️  FAIR"
                else:
                    status = "❌ POOR"
                
                print(f"   {status}")
                print(f"   📊 {result.rps:>8.1f} RPS | {result.avg_ms:>6.2f}ms avg | {result.success_rate:>5.1f}% success")
                print(f"   🎯 Target: {target:,} RPS ({result.rps/target*100:.1f}% of target)")
                
                if result.errors:
                    print(f"   ⚠️  Errors: {result.errors}")
            else:
                print(f"   ❌ Test failed completely")
    
    async def _check_endpoint_availability(self, path: str) -> bool:
        """Quick check if endpoint is available"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}{path}")
                return response.status_code < 500  # Allow 4xx but not 5xx
        except Exception:
            return False
    
    async def _test_single_endpoint(
        self, 
        path: str, 
        name: str,
        concurrency: int = 10, 
        duration: float = 3.0
    ) -> Optional[BasicResult]:
        """Test a single endpoint"""
        
        async def worker():
            """Single worker for testing"""
            times = []
            successes = 0
            failures = 0
            errors = {}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                end_time = time.time() + duration
                
                while time.time() < end_time:
                    start = time.time()
                    
                    try:
                        response = await client.get(f"{self.base_url}{path}")
                        
                        if response.status_code == 200:
                            successes += 1
                        else:
                            failures += 1
                            error_key = f"HTTP_{response.status_code}"
                            errors[error_key] = errors.get(error_key, 0) + 1
                        
                        # Read response to ensure full processing
                        await response.aread()
                        
                    except httpx.TimeoutException:
                        failures += 1
                        errors["timeout"] = errors.get("timeout", 0) + 1
                    except Exception as e:
                        failures += 1
                        error_key = type(e).__name__
                        errors[error_key] = errors.get(error_key, 0) + 1
                    
                    elapsed = time.time() - start
                    times.append(elapsed)
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.001)
            
            return times, successes, failures, errors
        
        try:
            # Run multiple workers
            start_time = time.time()
            tasks = [worker() for _ in range(concurrency)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            # Aggregate results
            all_times = []
            total_successes = 0
            total_failures = 0
            all_errors = {}
            
            for times, successes, failures, errors in results:
                all_times.extend(times)
                total_successes += successes
                total_failures += failures
                
                for error_type, count in errors.items():
                    all_errors[error_type] = all_errors.get(error_type, 0) + count
            
            if not all_times:
                return None
            
            # Calculate stats
            total_requests = total_successes + total_failures
            rps = total_requests / total_time
            success_rate = (total_successes / total_requests * 100) if total_requests > 0 else 0
            
            avg_time = statistics.mean(all_times) * 1000  # Convert to ms
            min_time = min(all_times) * 1000
            max_time = max(all_times) * 1000
            
            return BasicResult(
                endpoint=f"{name} ({path})",
                rps=rps,
                avg_ms=avg_time,
                min_ms=min_time,
                max_ms=max_time,
                success_rate=success_rate,
                total_requests=total_requests,
                errors=all_errors
            )
            
        except Exception as e:
            print(f"   ❌ Worker error: {e}")
            return None
    
    async def _test_concurrency_levels(self):
        """Test different concurrency levels on best endpoint"""
        if not self.results:
            print("\n❌ No successful endpoints to test concurrency")
            return
        
        # Find best performing endpoint
        best_result = max(self.results, key=lambda r: r.rps)
        endpoint_path = best_result.endpoint.split('(')[1].rstrip(')')
        
        print(f"\n⚡ Testing Concurrency Scaling on Best Endpoint: {endpoint_path}")
        print("-" * 50)
        print("Concurrency |    RPS     | Avg(ms) | Success% | Status")
        print("-" * 50)
        
        concurrency_levels = [1, 5, 10, 20, 50, 100]
        peak_rps = 0
        
        for concurrency in concurrency_levels:
            result = await self._test_single_endpoint(
                endpoint_path,
                f"Concurrency-{concurrency}",
                concurrency=concurrency,
                duration=2.0  # Shorter duration for concurrency test
            )
            
            if result:
                if result.rps > peak_rps:
                    peak_rps = result.rps
                    status = "🚀 PEAK"
                elif result.rps > peak_rps * 0.9:
                    status = "✅ GOOD"
                elif result.success_rate < 95:
                    status = "⚠️  DEGRADED"
                else:
                    status = "📉 DECLINING"
                
                print(f"{concurrency:>10} | {result.rps:>8.1f} | {result.avg_ms:>6.1f} | "
                      f"{result.success_rate:>6.1f}% | {status}")
                
                # Stop if performance severely degrades
                if result.success_rate < 80:
                    print("   ⚠️  Performance severely degraded, stopping test")
                    break
            else:
                print(f"{concurrency:>10} | {'FAILED':>8} | {'N/A':>6} | {'0.0':>6}% | ❌ FAILED")
                break
            
            await asyncio.sleep(0.5)  # Brief pause between tests
        
        print(f"\n🏆 Peak Performance: {peak_rps:.1f} RPS")
    
    def _generate_basic_report(self):
        """Generate focused performance report"""
        print("\n" + "=" * 60)
        print("📊 BASIC HTTP PERFORMANCE REPORT")
        print("=" * 60)
        
        if not self.results:
            print("❌ No successful results to report")
            return
        
        # Best and worst performers
        best = max(self.results, key=lambda r: r.rps)
        worst = min(self.results, key=lambda r: r.rps)
        
        print(f"🚀 Best Performer: {best.endpoint}")
        print(f"   RPS: {best.rps:.1f} | Latency: {best.avg_ms:.2f}ms | Success: {best.success_rate:.1f}%")
        
        print(f"\n📉 Worst Performer: {worst.endpoint}")
        print(f"   RPS: {worst.rps:.1f} | Latency: {worst.avg_ms:.2f}ms | Success: {worst.success_rate:.1f}%")
        
        # Overall assessment
        avg_rps = sum(r.rps for r in self.results) / len(self.results)
        avg_latency = sum(r.avg_ms for r in self.results) / len(self.results)
        avg_success = sum(r.success_rate for r in self.results) / len(self.results)
        
        print(f"\n📈 Overall Averages:")
        print(f"   RPS: {avg_rps:.1f}")
        print(f"   Latency: {avg_latency:.2f}ms")
        print(f"   Success Rate: {avg_success:.1f}%")
        
        # Grade the performance
        if best.rps > 8000 and avg_success > 95:
            grade = "A (Excellent)"
            recommendation = "✅ Ready for MCP protocol testing"
        elif best.rps > 5000 and avg_success > 90:
            grade = "B (Good)"
            recommendation = "⚠️  HTTP layer needs optimization before MCP testing"
        elif best.rps > 2000 and avg_success > 80:
            grade = "C (Fair)"
            recommendation = "🔧 Significant HTTP optimization needed"
        else:
            grade = "D (Poor)"
            recommendation = "❌ HTTP layer has serious performance issues"
        
        print(f"\n🏆 Performance Grade: {grade}")
        print(f"💡 Recommendation: {recommendation}")
        
        # Specific issues
        print(f"\n🔍 Specific Issues Found:")
        for result in self.results:
            if result.success_rate < 100:
                print(f"   ⚠️  {result.endpoint}: {100-result.success_rate:.1f}% failure rate")
            if result.avg_ms > 10:
                print(f"   ⚠️  {result.endpoint}: High latency ({result.avg_ms:.1f}ms)")
            if result.errors:
                print(f"   ⚠️  {result.endpoint}: Errors - {result.errors}")
        
        print("\n" + "=" * 60)


async def main():
    """Main entry point"""
    base_url = "http://localhost:8001"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print("🔧 ChukMCPServer - Basic HTTP Performance Test")
    print("📝 Focused test of fundamental HTTP endpoints")
    print("🎯 Goal: Establish if HTTP layer is ready for MCP protocol")
    print()
    
    test = BasicHTTPTest(base_url)
    await test.run_basic_tests()
    
    print("\n🎉 Basic HTTP testing completed!")
    print("📋 Use results to prioritize HTTP layer optimizations")


if __name__ == "__main__":
    asyncio.run(main())