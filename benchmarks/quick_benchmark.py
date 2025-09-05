# quick_benchmark.py - Fast, simple MCP server benchmark using httpx
import asyncio
import httpx
import json
import time
import statistics
from typing import Dict, List, Optional, Any


class QuickBenchmark:
    """Simple, fast MCP server benchmark using httpx"""

    def __init__(self, server_url: str, server_name: str = "MCP Server"):
        self.server_url = server_url
        self.server_name = server_name
        self.session_id: Optional[str] = None
        self.tools: List[Dict] = []
        self.resources: List[Dict] = []

    async def run_benchmark(self):
        """Run quick benchmark suite"""
        print(f"⚡ Quick MCP Benchmark: {self.server_name}")
        print(f"🔗 URL: {self.server_url}")
        print("=" * 50)

        # Initialize session and discover capabilities
        await self._setup_session()

        # Run tests
        results = {}
        results["connection"] = await self._test_connection()
        results["initialization"] = await self._test_initialization()
        results["tools_list"] = await self._test_tools_list()
        results["resources_list"] = await self._test_resources_list()

        if self.tools:
            results["tool_calls"] = await self._test_tool_calls()
        if self.resources:
            results["resource_reads"] = await self._test_resource_reads()

        results["sequential_load"] = await self._test_sequential_load()

        # Print results
        self._print_results(results)

        return results

    async def _setup_session(self):
        """Setup MCP session"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Content-Type": "application/json", "Accept": "application/json"}

                init_message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "quick-benchmark", "version": "1.0.0"},
                    },
                }

                response = await client.post(self.server_url, json=init_message, headers=headers)

                if response.status_code == 200:
                    self.session_id = response.headers.get("Mcp-Session-Id")
                    print(f"✅ Session initialized: {self.session_id[:8] if self.session_id else 'None'}...")

                    if self.session_id:
                        headers["Mcp-Session-Id"] = self.session_id

                    # Send initialized notification
                    init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
                    await client.post(self.server_url, json=init_notif, headers=headers)

                    # Discover capabilities
                    await self._discover_capabilities(client, headers)
                else:
                    print(f"❌ Initialization failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Session setup failed: {e}")

    async def _discover_capabilities(self, client: httpx.AsyncClient, headers: Dict):
        """Discover available tools and resources"""
        try:
            # Get tools
            tools_msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            response = await client.post(self.server_url, json=tools_msg, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data and "result" in data and "tools" in data["result"]:
                    self.tools = data["result"]["tools"]
                    print(f"🔧 Tools discovered: {len(self.tools)}")
                    for tool in self.tools[:3]:  # Show first 3
                        print(f"   - {tool['name']}")

            # Get resources
            resources_msg = {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}}
            response = await client.post(self.server_url, json=resources_msg, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if data and "result" in data and "resources" in data["result"]:
                    self.resources = data["result"]["resources"]
                    print(f"📄 Resources discovered: {len(self.resources)}")
                    for resource in self.resources[:3]:  # Show first 3
                        print(f"   - {resource['uri']}")

        except Exception as e:
            print(f"⚠️  Discovery failed: {e}")

    async def _test_connection(self):
        """Test basic connection"""
        print("🔌 Testing connection...")
        times = []

        # Test health endpoint if available, fallback to main endpoint
        health_url = self.server_url.replace("/mcp", "/health")

        for _ in range(5):
            start = time.time()
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(health_url)
                    times.append(time.time() - start)
            except Exception:
                # Fallback to main endpoint
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(self.server_url)
                        times.append(time.time() - start)
                except Exception:
                    times.append(time.time() - start)

        return self._calc_stats("Connection", times)

    async def _test_initialization(self):
        """Test MCP initialization"""
        print("🚀 Testing initialization...")
        times = []

        for i in range(3):
            start = time.time()
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    headers = {"Content-Type": "application/json", "Accept": "application/json"}

                    init_message = {
                        "jsonrpc": "2.0",
                        "id": i + 100,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {},
                            "clientInfo": {"name": f"test-{i}", "version": "1.0.0"},
                        },
                    }

                    response = await client.post(self.server_url, json=init_message, headers=headers)
                    if response.status_code == 200:
                        response.json()  # Parse response
                    times.append(time.time() - start)
            except Exception as e:
                times.append(time.time() - start)

        return self._calc_stats("Initialization", times)

    async def _test_tools_list(self):
        """Test tools/list performance"""
        print("🔧 Testing tools/list...")
        return await self._test_method("tools/list", "Tools List", 8)

    async def _test_resources_list(self):
        """Test resources/list performance"""
        print("📄 Testing resources/list...")
        return await self._test_method("resources/list", "Resources List", 8)

    async def _test_tool_calls(self):
        """Test tool execution"""
        print("🧪 Testing tool calls...")

        if not self.tools:
            return {"name": "Tool Calls", "avg_ms": 0, "min_ms": 0, "max_ms": 0, "rps": 0, "count": 0}

        # Test first available tool with smart argument detection
        tool = self.tools[0]
        tool_name = tool["name"]
        args = self._get_tool_arguments(tool)

        times = []

        for i in range(3):
            start = time.time()
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:  # Longer timeout for tool execution
                    headers = self._get_headers()

                    call_message = {
                        "jsonrpc": "2.0",
                        "id": i + 200,
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": args},
                    }

                    response = await client.post(self.server_url, json=call_message, headers=headers)
                    if response.status_code == 200:
                        response.json()  # Parse response
                    times.append(time.time() - start)
            except Exception as e:
                print(f"   Tool call error: {e}")
                times.append(time.time() - start)

        return self._calc_stats(f"Tool Call ({tool_name})", times)

    async def _test_resource_reads(self):
        """Test resource reading"""
        print("📖 Testing resource reads...")

        if not self.resources:
            return {"name": "Resource Reads", "avg_ms": 0, "min_ms": 0, "max_ms": 0, "rps": 0, "count": 0}

        # Test first available resource
        resource = self.resources[0]
        uri = resource["uri"]

        times = []

        for i in range(3):
            start = time.time()
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    headers = self._get_headers()

                    read_message = {"jsonrpc": "2.0", "id": i + 300, "method": "resources/read", "params": {"uri": uri}}

                    response = await client.post(self.server_url, json=read_message, headers=headers)
                    if response.status_code == 200:
                        response.json()  # Parse response
                    times.append(time.time() - start)
            except Exception as e:
                print(f"   Resource read error: {e}")
                times.append(time.time() - start)

        return self._calc_stats(f"Resource Read ({uri[:30]}...)", times)

    async def _test_sequential_load(self):
        """Test sequential load"""
        print("📈 Testing sequential load...")

        times = []
        total_start = time.time()

        # Run 15 sequential requests (mix of operations)
        for i in range(15):
            start = time.time()
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    headers = self._get_headers()

                    # Cycle through different operations
                    if i % 3 == 0:
                        method = "tools/list"
                    elif i % 3 == 1:
                        method = "resources/list"
                    else:
                        # Health check
                        health_url = self.server_url.replace("/mcp", "/health")
                        response = await client.get(health_url)
                        times.append(time.time() - start)
                        continue

                    message = {"jsonrpc": "2.0", "id": i + 400, "method": method, "params": {}}
                    response = await client.post(self.server_url, json=message, headers=headers)
                    if response.status_code == 200:
                        response.json()  # Parse response
                    times.append(time.time() - start)
            except Exception as e:
                times.append(time.time() - start)

        total_time = time.time() - total_start
        return self._calc_stats("Sequential Load", times, total_time)

    async def _test_method(self, method: str, name: str, iterations: int):
        """Test a specific MCP method"""
        times = []

        for i in range(iterations):
            start = time.time()
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    headers = self._get_headers()
                    message = {"jsonrpc": "2.0", "id": i + 500, "method": method, "params": {}}

                    response = await client.post(self.server_url, json=message, headers=headers)
                    if response.status_code == 200:
                        response.json()  # Parse response
                    times.append(time.time() - start)
            except Exception as e:
                times.append(time.time() - start)

        return self._calc_stats(name, times)

    def _get_headers(self):
        """Get HTTP headers with session ID"""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        return headers

    def _get_tool_arguments(self, tool: Dict) -> Dict[str, Any]:
        """Smart argument detection for tool testing"""
        tool_name = tool["name"].lower()

        # Common tool argument patterns
        if "hello" in tool_name or "greet" in tool_name:
            return {"name": "BenchmarkUser"}
        elif "add" in tool_name or "sum" in tool_name:
            return {"a": 5, "b": 3}
        elif "multiply" in tool_name or "mult" in tool_name:
            return {"a": 4, "b": 6}
        elif "calculate" in tool_name or "calc" in tool_name:
            return {"expression": "2 + 2"}
        elif "async_hello" in tool_name:
            return {"name": "BenchmarkUser", "delay": 0.01}  # Quick delay for benchmarking
        elif "stream" in tool_name:
            return {"item_count": 2, "process_delay": 0.01}  # Quick processing
        elif "batch" in tool_name:
            return {"items": ["test1", "test2"], "batch_size": 2}
        elif "monitor" in tool_name:
            return {"duration": 1, "interval": 0.2}  # Short monitoring for benchmark
        elif "concurrent" in tool_name:
            return {"endpoints": ["test1", "test2"]}
        else:
            # Try to extract from schema if available
            schema = tool.get("inputSchema", {})
            properties = schema.get("properties", {})
            required = schema.get("required", [])

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

    def _calc_stats(self, name: str, times: List[float], total_time: float = None):
        """Calculate statistics from timing data"""
        if not times:
            return {"name": name, "avg_ms": 0, "min_ms": 0, "max_ms": 0, "rps": 0, "count": 0}

        # Filter out extreme outliers (> 10 seconds probably means timeout/error)
        filtered_times = [t for t in times if t < 10.0]
        if not filtered_times:
            filtered_times = times

        avg_time = statistics.mean(filtered_times)
        min_time = min(filtered_times)
        max_time = max(filtered_times)

        if total_time:
            rps = len(filtered_times) / total_time
        else:
            rps = 1 / avg_time if avg_time > 0 else 0

        return {
            "name": name,
            "avg_ms": avg_time * 1000,
            "min_ms": min_time * 1000,
            "max_ms": max_time * 1000,
            "rps": rps,
            "count": len(filtered_times),
        }

    def _print_results(self, results: Dict):
        """Print benchmark results"""
        print("\n" + "=" * 60)
        print("📊 QUICK BENCHMARK RESULTS")
        print("=" * 60)
        print(f"Server: {self.server_name}")
        print(f"Tools Found: {len(self.tools)}")
        print(f"Resources Found: {len(self.resources)}")
        print()
        print(f"{'Test':<25} {'Avg(ms)':<8} {'Min(ms)':<8} {'Max(ms)':<8} {'RPS':<6} {'Count':<5}")
        print("-" * 60)

        for test_name, result in results.items():
            if isinstance(result, dict) and "avg_ms" in result:
                name = result["name"][:24]
                print(
                    f"{name:<25} {result['avg_ms']:>6.1f} {result['min_ms']:>6.1f} {result['max_ms']:>6.1f} {result['rps']:>4.1f} {result['count']:>3}"
                )

        # Calculate overall performance metrics
        valid_results = [r for r in results.values() if isinstance(r, dict) and "avg_ms" in r and r["avg_ms"] > 0]

        if valid_results:
            total_rps = sum(r["rps"] for r in valid_results)
            avg_response_time = statistics.mean([r["avg_ms"] for r in valid_results])

            print("\n📈 SUMMARY")
            print(f"Total RPS (across all tests): {total_rps:.1f}")
            print(f"Average Response Time: {avg_response_time:.1f}ms")

            # Performance rating based on average response time
            if avg_response_time < 50:
                rating = "🚀 Excellent"
            elif avg_response_time < 100:
                rating = "✅ Good"
            elif avg_response_time < 200:
                rating = "⚠️  Fair"
            else:
                rating = "❌ Poor"

            print(f"Performance Rating: {rating}")

            # Server type detection
            if any("async" in tool["name"].lower() for tool in self.tools):
                print("📝 Server Type: Async-Native (optimized for concurrent operations)")
            else:
                print("📝 Server Type: Traditional (optimized for high-throughput)")
        else:
            print("\n⚠️  No valid results to summarize")


async def main():
    """Run quick benchmark"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python quick_benchmark.py <server_url> [server_name]")
        print("Examples:")
        print("  python quick_benchmark.py http://localhost:8000/mcp 'Traditional Server'")
        print("  python quick_benchmark.py http://localhost:8001/mcp 'Async Native Server'")
        return

    server_url = sys.argv[1]
    server_name = sys.argv[2] if len(sys.argv) > 2 else "MCP Server"

    benchmark = QuickBenchmark(server_url, server_name)
    await benchmark.run_benchmark()


if __name__ == "__main__":
    asyncio.run(main())
