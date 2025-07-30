#!/usr/bin/env python3
"""
Ultra-Minimal MCP Protocol Performance Test

Tests actual MCP JSON-RPC performance with zero client overhead.
Uses raw sockets and pre-built MCP requests.

Target: Measure true MCP protocol performance without client bottlenecks.
Expected: 10,000-20,000+ RPS for MCP operations on your optimized server.
"""

import asyncio
import time
import json
import statistics
import sys
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import gc


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


class UltraMinimalMCPTest:
    """Ultra-minimal MCP protocol performance test"""
    
    def __init__(self, host: str = "localhost", port: int = 8001):
        self.host = host
        self.port = port
        self.session_id = None
        
        # Pre-built MCP requests (no encoding overhead)
        self.mcp_initialize = self._build_http_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "ultra-minimal-test", "version": "1.0.0"}
            }
        })
        
        self.mcp_ping = self._build_http_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "ping",
            "params": {}
        })
        
        self.mcp_tools_list = self._build_http_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {}
        })
        
        self.mcp_resources_list = self._build_http_request({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/list",
            "params": {}
        })
        
        # Async tool call (minimal parameters for performance)
        self.async_hello_call = self._build_http_request({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "async_hello",
                "arguments": {"name": "PerfTest", "delay": 0.001}  # Minimal delay
            }
        })
        
        # Resource read
        self.resource_read = self._build_http_request({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "resources/read",
            "params": {"uri": "async://server-metrics"}
        })
    
    def _build_http_request(self, json_data: dict) -> bytes:
        """Build complete HTTP POST request with JSON body"""
        json_body = json.dumps(json_data)
        content_length = len(json_body.encode('utf-8'))
        
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
        return http_request.encode('utf-8')
    
    def _build_http_request_with_session(self, json_data: dict) -> bytes:
        """Build HTTP request with session ID header"""
        json_body = json.dumps(json_data)
        content_length = len(json_body.encode('utf-8'))
        
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
        return http_request.encode('utf-8')
    
    async def run_mcp_performance_tests(self):
        """Run comprehensive MCP protocol performance tests"""
        print("🚀 ChukMCPServer Ultra-Minimal MCP Protocol Test")
        print("=" * 60)
        print("ZERO client overhead - raw sockets + pre-built MCP requests")
        print("Target: Measure true MCP JSON-RPC performance")
        print()
        
        # Check MCP server availability
        if not await self._check_mcp_server():
            print("❌ MCP server not available")
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
            self.mcp_ping, "MCP Ping", concurrency=200, duration=5.0
        )
        results.append(ping_result)
        print(f"   {ping_result.rps:>8,.0f} RPS | {ping_result.avg_ms:>6.2f}ms avg | {ping_result.success_rate:>5.1f}% success")
        
        # Test 2: MCP Tools List
        print("🔧 Testing MCP Tools List...")
        tools_result = await self._test_mcp_operation(
            self.mcp_tools_list, "MCP Tools List", concurrency=200, duration=5.0
        )
        results.append(tools_result)
        print(f"   {tools_result.rps:>8,.0f} RPS | {tools_result.avg_ms:>6.2f}ms avg | {tools_result.success_rate:>5.1f}% success")
        
        # Test 3: MCP Resources List
        print("📂 Testing MCP Resources List...")
        resources_result = await self._test_mcp_operation(
            self.mcp_resources_list, "MCP Resources List", concurrency=200, duration=5.0
        )
        results.append(resources_result)
        print(f"   {resources_result.rps:>8,.0f} RPS | {resources_result.avg_ms:>6.2f}ms avg | {resources_result.success_rate:>5.1f}% success")
        
        # Test 4: Async Tool Call (minimal delay)
        print("🌊 Testing Async Tool Call (async_hello)...")
        async_tool_result = await self._test_mcp_operation(
            self.async_hello_call, "Async Tool Call", concurrency=100, duration=5.0
        )
        results.append(async_tool_result)
        print(f"   {async_tool_result.rps:>8,.0f} RPS | {async_tool_result.avg_ms:>6.2f}ms avg | {async_tool_result.success_rate:>5.1f}% success")
        
        # Test 5: Resource Read
        print("📖 Testing Resource Read...")
        resource_result = await self._test_mcp_operation(
            self.resource_read, "Resource Read", concurrency=100, duration=5.0
        )
        results.append(resource_result)
        print(f"   {resource_result.rps:>8,.0f} RPS | {resource_result.avg_ms:>6.2f}ms avg | {resource_result.success_rate:>5.1f}% success")
        
        # Test 6: Concurrency scaling for MCP Ping
        print("\n⚡ Testing MCP Ping Concurrency Scaling...")
        await self._test_mcp_concurrency_scaling()
        
        # Test 7: Maximum MCP throughput
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
            get_request = (
                f"GET /mcp HTTP/1.1\r\n"
                f"Host: {self.host}:{self.port}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            ).encode('ascii')
            
            writer.write(get_request)
            await writer.drain()
            
            response = await reader.read(4096)
            writer.close()
            await writer.wait_closed()
            
            print(f"📊 MCP endpoint response: {response[:200]}...")
            
            if b"HTTP/1.1 200" in response:
                return True
            else:
                print(f"❌ MCP endpoint returned: {response.decode('utf-8', errors='ignore')[:300]}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
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
            
            if b"HTTP/1.1 200" not in response:
                return False
            
            # Extract session ID from headers
            response_str = response.decode('utf-8', errors='ignore')
            for line in response_str.split('\r\n'):
                if line.lower().startswith('mcp-session-id:'):
                    self.session_id = line.split(':', 1)[1].strip()
                    break
            
            # Send initialized notification
            if self.session_id:
                await self._send_initialized_notification()
            
            return True
            
        except Exception as e:
            print(f"Session init error: {e}")
            return False
    
    async def _send_initialized_notification(self):
        """Send MCP initialized notification"""
        try:
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            
            notification_request = self._build_http_request_with_session(notification)
            
            reader, writer = await asyncio.open_connection(self.host, self.port)
            writer.write(notification_request)
            await writer.drain()
            await reader.read(1024)  # Consume response
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass  # Notification failures are non-critical
    
    def _rebuild_requests_with_session(self):
        """Rebuild requests with session ID"""
        if not self.session_id:
            return
        
        # Rebuild requests with session header
        self.mcp_ping = self._build_http_request_with_session({
            "jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}
        })
        
        self.mcp_tools_list = self._build_http_request_with_session({
            "jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}
        })
        
        self.mcp_resources_list = self._build_http_request_with_session({
            "jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}
        })
        
        self.async_hello_call = self._build_http_request_with_session({
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "async_hello", "arguments": {"name": "PerfTest", "delay": 0.001}}
        })
        
        self.resource_read = self._build_http_request_with_session({
            "jsonrpc": "2.0", "id": 6, "method": "resources/read",
            "params": {"uri": "async://server-metrics"}
        })
    
    async def _test_mcp_operation(
        self, 
        request_bytes: bytes, 
        name: str, 
        concurrency: int = 100, 
        duration: float = 5.0
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
            mcp_errors=total_mcp_errors
        )
    
    async def _test_mcp_concurrency_scaling(self):
        """Test MCP concurrency scaling"""
        print("   Concurrency |    RPS     | Avg(ms) | Success% | MCP Errors")
        print("   " + "-" * 60)
        
        for concurrency in [1, 5, 10, 25, 50, 100, 200, 500]:
            result = await self._test_mcp_operation(
                self.mcp_ping, f"MCP Scale {concurrency}", 
                concurrency=concurrency, duration=3.0
            )
            
            print(f"   {concurrency:>10} | {result.rps:>8,.0f} | {result.avg_ms:>6.1f} | "
                  f"{result.success_rate:>6.1f}% | {result.mcp_errors:>8}")
            
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
                self.mcp_ping, f"MCP Max {concurrency}",
                concurrency=concurrency, duration=3.0
            )
            
            print(f"{result.rps:>8,.0f} RPS ({result.success_rate:>5.1f}% success)")
            
            if result.success_rate >= 95 and result.rps > best_rps:
                best_rps = result.rps
                best_result = result
            
            if result.success_rate < 80:
                break
        
        return best_result or MCPResult("MCP Max", 0, 0, 0, 0, 0, 0, 0)
    
    def _print_mcp_summary(self, results: List[MCPResult]):
        """Print MCP performance summary"""
        print("\n" + "=" * 60)
        print("📊 ULTRA-MINIMAL MCP PROTOCOL RESULTS")
        print("=" * 60)
        
        if not results:
            print("❌ No MCP results to show")
            return
        
        # Find best MCP result
        best_result = max(results, key=lambda r: r.rps)
        
        print(f"🚀 Maximum MCP Performance:")
        print(f"   Peak RPS: {best_result.rps:>12,.0f}")
        print(f"   Avg Latency: {best_result.avg_ms:>9.2f}ms")
        print(f"   Success Rate: {best_result.success_rate:>8.1f}%")
        print(f"   MCP Errors: {best_result.mcp_errors:>10}")
        print(f"   Operation: {best_result.name}")
        
        # Detailed MCP results
        print(f"\n📋 All MCP Test Results:")
        print("   Operation               |    RPS     | Avg(ms) | Success% | MCP Errors")
        print("   " + "-" * 75)
        
        for result in results:
            print(f"   {result.name:<23} | {result.rps:>8,.0f} | {result.avg_ms:>6.1f} | "
                  f"{result.success_rate:>6.1f}% | {result.mcp_errors:>8}")
        
        # MCP Performance Analysis
        print(f"\n🔍 MCP Performance Analysis:")
        if best_result.rps > 15000:
            print("   🏆 EXCEPTIONAL MCP performance!")
            print("   🚀 Your async MCP server is world-class")
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
        
        # Protocol overhead analysis
        http_baseline = 49239  # From previous HTTP test
        mcp_best = best_result.rps
        protocol_overhead = ((http_baseline - mcp_best) / http_baseline) * 100
        
        print(f"\n📊 Protocol Overhead Analysis:")
        print(f"   HTTP Baseline: {http_baseline:>8,} RPS (simple GET)")
        print(f"   MCP Best: {mcp_best:>12,.0f} RPS (JSON-RPC)")
        print(f"   Protocol Overhead: {protocol_overhead:>6.1f}%")
        
        if protocol_overhead < 30:
            print("   🎯 Excellent protocol efficiency!")
        elif protocol_overhead < 50:
            print("   ✅ Good protocol efficiency")
        else:
            print("   ⚠️  High protocol overhead - optimization opportunity")
        
        # Async-specific insights
        async_results = [r for r in results if 'async' in r.name.lower() or 'tool' in r.name.lower()]
        if async_results:
            print(f"\n🌊 Async Tool Performance:")
            for result in async_results:
                print(f"   {result.name}: {result.rps:>8,.0f} RPS")
            print("   💡 These show your async architecture benefits")
        
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
    
    print("⚡ ChukMCPServer Ultra-Minimal MCP Protocol Test")
    print(f"🎯 Target: {host}:{port}")
    print("📝 Zero client overhead - MCP JSON-RPC performance")
    print("🏆 Goal: Measure true async MCP server performance")
    print()
    
    # Optimize for maximum performance
    gc.collect()
    gc.disable()  # Disable GC during testing
    
    test = UltraMinimalMCPTest(host, port)
    
    try:
        success = await test.run_mcp_performance_tests()
        
        if success:
            print("🎉 Ultra-minimal MCP performance testing completed!")
        else:
            print("❌ MCP performance testing failed. Check server status.")
            sys.exit(1)
    
    finally:
        gc.enable()  # Re-enable GC


if __name__ == "__main__":
    # Use the fastest possible event loop
    import platform
    if platform.system() != 'Windows':
        try:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            print("🚀 Using uvloop for maximum performance")
        except ImportError:
            print("⚠️  uvloop not available")
    
    asyncio.run(main())