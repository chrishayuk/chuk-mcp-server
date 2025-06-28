# quick_benchmark.py - Fast, simple MCP server benchmark
import asyncio
import aiohttp
import json
import time
import statistics
from typing import Dict, List, Optional

class QuickBenchmark:
    """Simple, fast MCP server benchmark"""
    
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
        
        # Initialize session
        await self._setup_session()
        
        # Run tests
        results = {}
        results['connection'] = await self._test_connection()
        results['initialization'] = await self._test_initialization()
        results['tools_list'] = await self._test_tools_list()
        results['resources_list'] = await self._test_resources_list()
        results['tool_calls'] = await self._test_tool_calls()
        results['resource_reads'] = await self._test_resource_reads()
        results['sequential_load'] = await self._test_sequential_load()
        
        # Print results
        self._print_results(results)
        
        return results
    
    async def _setup_session(self):
        """Setup MCP session"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
                
                init_message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize", 
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "quick-benchmark", "version": "1.0.0"}
                    }
                }
                
                async with session.post(self.server_url, json=init_message, headers=headers) as resp:
                    if resp.status == 200:
                        self.session_id = resp.headers.get('Mcp-Session-Id')
                        if self.session_id:
                            headers['Mcp-Session-Id'] = self.session_id
                        
                        # Send initialized notification
                        init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
                        async with session.post(self.server_url, json=init_notif, headers=headers):
                            pass
                        
                        # Discover capabilities
                        await self._discover_capabilities(session, headers)
                        
        except Exception as e:
            print(f"❌ Session setup failed: {e}")
    
    async def _discover_capabilities(self, session: aiohttp.ClientSession, headers: Dict):
        """Discover available tools and resources"""
        try:
            # Get tools
            tools_msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            async with session.post(self.server_url, json=tools_msg, headers=headers) as resp:
                if resp.status == 200:
                    data = await self._parse_response(resp)
                    if data and 'result' in data and 'tools' in data['result']:
                        self.tools = data['result']['tools']
            
            # Get resources
            resources_msg = {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}}
            async with session.post(self.server_url, json=resources_msg, headers=headers) as resp:
                if resp.status == 200:
                    data = await self._parse_response(resp)
                    if data and 'result' in data and 'resources' in data['result']:
                        self.resources = data['result']['resources']
                        
        except Exception as e:
            print(f"⚠️  Discovery failed: {e}")
    
    async def _test_connection(self):
        """Test basic connection"""
        print("🔌 Testing connection...")
        times = []
        
        for _ in range(10):  # Small number of tests
            start = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.server_url) as resp:
                        await resp.read()
                        times.append(time.time() - start)
            except:
                times.append(time.time() - start)
        
        return self._calc_stats("Connection", times)
    
    async def _test_initialization(self):
        """Test MCP initialization"""
        print("🚀 Testing initialization...")
        times = []
        
        for _ in range(5):  # Even fewer for complex operations
            start = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    }
                    
                    init_message = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0.0"}
                        }
                    }
                    
                    async with session.post(self.server_url, json=init_message, headers=headers) as resp:
                        if resp.status == 200:
                            await self._parse_response(resp)
                        times.append(time.time() - start)
            except:
                times.append(time.time() - start)
        
        return self._calc_stats("Initialization", times)
    
    async def _test_tools_list(self):
        """Test tools/list performance"""
        print("🔧 Testing tools/list...")
        return await self._test_method("tools/list", "Tools List", 10)
    
    async def _test_resources_list(self):
        """Test resources/list performance"""
        print("📄 Testing resources/list...")
        return await self._test_method("resources/list", "Resources List", 10)
    
    async def _test_tool_calls(self):
        """Test tool execution"""
        print("🧪 Testing tool calls...")
        
        if not self.tools:
            return {"name": "Tool Calls", "avg_ms": 0, "min_ms": 0, "max_ms": 0, "rps": 0, "count": 0}
        
        # Test first available tool
        tool = self.tools[0]
        tool_name = tool['name']
        
        # Use appropriate arguments based on tool name
        if tool_name == "add":
            args = {"a": 5, "b": 3}
        elif tool_name == "hello":
            args = {"name": "test"}
        else:
            args = {}
        
        times = []
        
        for _ in range(5):
            start = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    headers = self._get_headers()
                    
                    call_message = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": args}
                    }
                    
                    async with session.post(self.server_url, json=call_message, headers=headers) as resp:
                        if resp.status == 200:
                            await self._parse_response(resp)
                        times.append(time.time() - start)
            except:
                times.append(time.time() - start)
        
        return self._calc_stats(f"Tool Call ({tool_name})", times)
    
    async def _test_resource_reads(self):
        """Test resource reading"""
        print("📖 Testing resource reads...")
        
        if not self.resources:
            return {"name": "Resource Reads", "avg_ms": 0, "min_ms": 0, "max_ms": 0, "rps": 0, "count": 0}
        
        # Test first available resource
        resource = self.resources[0]
        uri = resource['uri']
        
        times = []
        
        for _ in range(5):
            start = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    headers = self._get_headers()
                    
                    read_message = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "resources/read",
                        "params": {"uri": uri}
                    }
                    
                    async with session.post(self.server_url, json=read_message, headers=headers) as resp:
                        if resp.status == 200:
                            await self._parse_response(resp)
                        times.append(time.time() - start)
            except:
                times.append(time.time() - start)
        
        return self._calc_stats(f"Resource Read ({uri})", times)
    
    async def _test_sequential_load(self):
        """Test sequential load (no concurrency to avoid hanging)"""
        print("📈 Testing sequential load...")
        
        times = []
        total_start = time.time()
        
        # Run 20 sequential requests
        for i in range(20):
            start = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    headers = self._get_headers()
                    
                    # Alternate between tools/list and resources/list
                    method = "tools/list" if i % 2 == 0 else "resources/list"
                    message = {"jsonrpc": "2.0", "id": i, "method": method, "params": {}}
                    
                    async with session.post(self.server_url, json=message, headers=headers) as resp:
                        if resp.status == 200:
                            await self._parse_response(resp)
                        times.append(time.time() - start)
            except:
                times.append(time.time() - start)
        
        total_time = time.time() - total_start
        return self._calc_stats("Sequential Load", times, total_time)
    
    async def _test_method(self, method: str, name: str, iterations: int):
        """Test a specific MCP method"""
        times = []
        
        for _ in range(iterations):
            start = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    headers = self._get_headers()
                    message = {"jsonrpc": "2.0", "id": 1, "method": method, "params": {}}
                    
                    async with session.post(self.server_url, json=message, headers=headers) as resp:
                        if resp.status == 200:
                            await self._parse_response(resp)
                        times.append(time.time() - start)
            except:
                times.append(time.time() - start)
        
        return self._calc_stats(name, times)
    
    def _get_headers(self):
        """Get HTTP headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if self.session_id:
            headers['Mcp-Session-Id'] = self.session_id
        return headers
    
    async def _parse_response(self, response: aiohttp.ClientResponse):
        """Parse response (SSE or JSON)"""
        try:
            content_type = response.headers.get('Content-Type', '')
            
            if 'text/event-stream' in content_type:
                async for line in response.content:
                    line = line.decode('utf-8').rstrip('\r\n')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data:
                            return json.loads(data)
            elif 'application/json' in content_type:
                return await response.json()
        except:
            pass
        return None
    
    def _calc_stats(self, name: str, times: List[float], total_time: float = None):
        """Calculate statistics from timing data"""
        if not times:
            return {"name": name, "avg_ms": 0, "min_ms": 0, "max_ms": 0, "rps": 0, "count": 0}
        
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        
        if total_time:
            rps = len(times) / total_time
        else:
            rps = 1 / avg_time if avg_time > 0 else 0
        
        return {
            "name": name,
            "avg_ms": avg_time * 1000,
            "min_ms": min_time * 1000,
            "max_ms": max_time * 1000,
            "rps": rps,
            "count": len(times)
        }
    
    def _print_results(self, results: Dict):
        """Print benchmark results"""
        print("\n" + "=" * 50)
        print("📊 QUICK BENCHMARK RESULTS")
        print("=" * 50)
        print(f"Server: {self.server_name}")
        print(f"Tools Found: {len(self.tools)}")
        print(f"Resources Found: {len(self.resources)}")
        print()
        print(f"{'Test':<20} {'Avg(ms)':<8} {'Min(ms)':<8} {'Max(ms)':<8} {'RPS':<6}")
        print("-" * 50)
        
        for test_name, result in results.items():
            if isinstance(result, dict) and 'avg_ms' in result:
                print(f"{result['name'][:19]:<20} {result['avg_ms']:>6.1f} {result['min_ms']:>6.1f} {result['max_ms']:>6.1f} {result['rps']:>4.1f}")
        
        # Calculate overall performance score
        total_rps = sum(r['rps'] for r in results.values() if isinstance(r, dict) and 'rps' in r)
        avg_response_time = statistics.mean([r['avg_ms'] for r in results.values() if isinstance(r, dict) and 'avg_ms' in r and r['avg_ms'] > 0])
        
        print("\n📈 SUMMARY")
        print(f"Total RPS: {total_rps:.1f}")
        print(f"Avg Response Time: {avg_response_time:.1f}ms")
        
        # Performance rating
        if avg_response_time < 50:
            rating = "🚀 Excellent"
        elif avg_response_time < 100:
            rating = "✅ Good"
        elif avg_response_time < 200:
            rating = "⚠️  Fair"
        else:
            rating = "❌ Poor"
        
        print(f"Performance Rating: {rating}")

async def main():
    """Run quick benchmark"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python quick_benchmark.py <server_url> [server_name]")
        print("Example: python quick_benchmark.py http://localhost:8000/mcp 'My FastMCP Server'")
        return
    
    server_url = sys.argv[1]
    server_name = sys.argv[2] if len(sys.argv) > 2 else "MCP Server"
    
    benchmark = QuickBenchmark(server_url, server_name)
    await benchmark.run_benchmark()

if __name__ == "__main__":
    asyncio.run(main())