#!/usr/bin/env python3
"""
Standalone Async Native ChukMCPServer Demo

This demo creates and tests a full async native server showcasing
advanced concurrent, streaming, and monitoring capabilities.
"""

import asyncio
import json
import os
import subprocess
import sys
import time

import httpx


class StandaloneAsyncDemo:
    """Self-contained async native demo showcasing advanced capabilities"""

    def __init__(self):
        self.server_process: subprocess.Popen | None = None
        self.server_url = "http://localhost:8001"
        self.mcp_url = f"{self.server_url}/mcp"
        self.temp_file = "standalone_async_server.py"

    async def run_demo(self):
        """Run the complete standalone demo"""
        print("🚀 Standalone Async Native ChukMCPServer Demo")
        print("=" * 60)
        print("This demo creates and tests a full async native server")
        print("with advanced concurrent, streaming, and monitoring capabilities")
        print("=" * 60)

        try:
            # Create the server file
            self._create_server_file()

            # Start the server
            await self._start_server()

            # Wait for server to be ready
            await self._wait_for_server()

            # Discover capabilities
            await self._discover_capabilities()

            # Test basic tools
            await self._test_basic_tools()

            # Test async features
            await self._test_async_features()

            # Test resources
            await self._test_resources()

            # Performance test
            await self._performance_test()

            # Final comparison
            self._show_comparison()

        except KeyboardInterrupt:
            print("\n⚠️ Demo interrupted")
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            import traceback

            traceback.print_exc()
        finally:
            await self._cleanup()

    def _create_server_file(self):
        """Create the async native server file"""
        print("📝 Creating async native server...")

        server_code = '''#!/usr/bin/env python3
"""Standalone Async Native ChukMCPServer with advanced capabilities"""
import asyncio
import time
import random
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Union

from chuk_mcp_server import ChukMCPServer

# Configure logging to reduce noise
logging.getLogger().setLevel(logging.WARNING)

# Create async native server
mcp = ChukMCPServer(
    name="Standalone Async Native Server",
    version="2.0.0",
    description="Full async native server with advanced async capabilities"
)

def ensure_int(value: Union[str, int, float]) -> int:
    """Ensure a value is converted to int safely"""
    if isinstance(value, int):
        return value
    elif isinstance(value, float):
        return int(value)
    elif isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            try:
                return int(float(value))
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to integer")
    else:
        return int(value)

def ensure_float(value: Union[str, int, float]) -> float:
    """Ensure a value is converted to float safely"""
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Cannot convert '{value}' to float")
    else:
        return float(value)

@mcp.tool
async def async_hello(name: str, delay: Union[str, int, float] = 0.1) -> str:
    """Async hello with configurable delay"""
    try:
        delay_float = ensure_float(delay)

        # Ensure reasonable bounds
        if delay_float < 0:
            delay_float = 0.0
        elif delay_float > 10.0:
            delay_float = 10.0

        await asyncio.sleep(delay_float)
        return f"Hello, {name}! (async processed after {delay_float}s)"
    except Exception as e:
        return f"Hello, {name}! (processed with error: {str(e)})"

@mcp.tool
async def concurrent_api_calls(endpoints: List[str]) -> Dict[str, Any]:
    """Make multiple concurrent API calls"""
    try:
        async def simulate_api_call(endpoint: str):
            # Simulate realistic API call timing
            await asyncio.sleep(0.05 + random.random() * 0.1)
            return {
                'endpoint': endpoint,
                'status': 'success',
                'response_time_ms': round((0.05 + random.random() * 0.1) * 1000, 1),
                'data': f'data_from_{endpoint}',
                'timestamp': datetime.now().isoformat()
            }

        start_time = time.time()
        # Execute all API calls concurrently
        results = await asyncio.gather(*[simulate_api_call(ep) for ep in endpoints])
        total_time = time.time() - start_time

        return {
            'operation': 'concurrent_api_calls',
            'total_endpoints': len(endpoints),
            'successful_calls': len(results),
            'failed_calls': 0,
            'total_time_seconds': round(total_time, 3),
            'concurrent_execution': True,
            'performance': {
                'avg_response_time_ms': round(sum(r['response_time_ms'] for r in results) / len(results), 1),
                'total_wait_time_if_sequential': round(sum(r['response_time_ms'] for r in results) / 1000, 3),
                'time_saved_by_concurrency': round((sum(r['response_time_ms'] for r in results) / 1000) - total_time, 3)
            },
            'results': results
        }
    except Exception as e:
        return {
            'operation': 'concurrent_api_calls',
            'error': f"Error in concurrent_api_calls: {str(e)}",
            'total_endpoints': len(endpoints) if endpoints else 0,
            'successful_calls': 0,
            'failed_calls': len(endpoints) if endpoints else 0
        }

@mcp.tool
async def stream_processing(item_count: Union[str, int] = 5, process_delay: Union[str, float] = 0.1) -> Dict[str, Any]:
    """Process items using async streaming patterns"""
    try:
        item_count_int = ensure_int(item_count)
        process_delay_float = ensure_float(process_delay)

        # Ensure reasonable bounds
        if item_count_int <= 0:
            item_count_int = 1
        elif item_count_int > 100:
            item_count_int = 100

        if process_delay_float < 0:
            process_delay_float = 0.001
        elif process_delay_float > 5.0:
            process_delay_float = 5.0

        async def data_stream(count: int):
            """Async generator for streaming data"""
            for i in range(count):
                await asyncio.sleep(0.03)  # Simulate data generation delay
                yield {
                    'id': i,
                    'timestamp': datetime.now().isoformat(),
                    'value': random.randint(1, 100),
                    'source': f'stream_item_{i}'
                }

        processed_items = []
        start_time = time.time()

        # Process streaming data
        async for data_item in data_stream(item_count_int):
            # Simulate processing each item
            await asyncio.sleep(process_delay_float)

            processed_item = {
                **data_item,
                'processed': True,
                'processed_at': datetime.now().isoformat(),
                'processing_time_ms': process_delay_float * 1000
            }
            processed_items.append(processed_item)

        total_time = time.time() - start_time

        return {
            'operation': 'stream_processing',
            'stream_complete': True,
            'items_processed': len(processed_items),
            'total_time_seconds': round(total_time, 3),
            'avg_time_per_item_ms': round((total_time / len(processed_items)) * 1000, 1) if processed_items else 0,
            'streaming_efficiency': {
                'items_per_second': round(len(processed_items) / total_time, 1) if total_time > 0 else 0,
                'memory_efficient': True,
                'async_streaming': True
            },
            'processed_items': processed_items
        }
    except Exception as e:
        return {
            'operation': 'stream_processing',
            'error': f"Error in stream_processing: {str(e)}",
            'items_processed': 0,
            'stream_complete': False
        }

@mcp.tool
async def batch_processing(items: List[str], batch_size: Union[str, int] = 3) -> Dict[str, Any]:
    """Process data in concurrent batches"""
    try:
        batch_size_int = ensure_int(batch_size)

        # Ensure reasonable bounds
        if batch_size_int <= 0:
            batch_size_int = 1
        elif batch_size_int > len(items):
            batch_size_int = len(items)

        async def process_single_item(item: str, batch_id: int):
            # Simulate item processing
            processing_time = 0.02 + random.random() * 0.03
            await asyncio.sleep(processing_time)

            return {
                'item': item,
                'batch_id': batch_id,
                'processed_at': datetime.now().isoformat(),
                'processing_time_ms': round(processing_time * 1000, 1),
                'result': f'processed_{item}',
                'status': 'success'
            }

        all_results = []
        start_time = time.time()
        batch_count = 0

        # Process items in batches
        for i in range(0, len(items), batch_size_int):
            batch = items[i:i + batch_size_int]
            batch_count += 1

            # Process entire batch concurrently
            batch_results = await asyncio.gather(*[
                process_single_item(item, batch_count) for item in batch
            ])

            all_results.extend(batch_results)

            # Small delay between batches
            if i + batch_size_int < len(items):
                await asyncio.sleep(0.01)

        total_time = time.time() - start_time

        return {
            'operation': 'batch_processing',
            'batch_complete': True,
            'total_items': len(items),
            'batch_size': batch_size_int,
            'total_batches': batch_count,
            'total_time_seconds': round(total_time, 3),
            'efficiency': {
                'items_per_second': round(len(items) / total_time, 1) if total_time > 0 else 0,
                'avg_batch_time_ms': round((total_time / batch_count) * 1000, 1) if batch_count > 0 else 0,
                'concurrent_within_batches': True
            },
            'results': all_results
        }
    except Exception as e:
        return {
            'operation': 'batch_processing',
            'error': f"Error in batch_processing: {str(e)}",
            'total_items': len(items) if items else 0,
            'batch_complete': False
        }

@mcp.tool
async def real_time_monitoring(duration: Union[str, int] = 3, interval: Union[str, float] = 0.5) -> Dict[str, Any]:
    """Real-time system monitoring with async data collection"""
    try:
        duration_int = ensure_int(duration)
        interval_float = ensure_float(interval)

        # Ensure reasonable bounds
        if duration_int <= 0:
            duration_int = 1
        elif duration_int > 60:
            duration_int = 60

        if interval_float <= 0:
            interval_float = 0.1
        elif interval_float > 10.0:
            interval_float = 10.0

        monitoring_data = []
        start_time = time.time()
        end_time = start_time + duration_int

        while time.time() < end_time:
            await asyncio.sleep(interval_float)

            # Simulate collecting various metrics
            current_time = time.time()
            data_point = {
                'timestamp': datetime.now().isoformat(),
                'elapsed_seconds': round(current_time - start_time, 2),
                'metrics': {
                    'cpu_usage_percent': random.randint(15, 85),
                    'memory_usage_percent': random.randint(30, 90),
                    'active_connections': random.randint(5, 50),
                    'requests_per_second': random.randint(100, 1500),
                    'response_time_ms': round(random.uniform(0.5, 5.0), 2)
                },
                'status': 'healthy' if random.random() > 0.1 else 'warning'
            }
            monitoring_data.append(data_point)

        total_time = time.time() - start_time

        # Calculate averages
        if monitoring_data:
            avg_cpu = round(sum(d['metrics']['cpu_usage_percent'] for d in monitoring_data) / len(monitoring_data), 1)
            avg_memory = round(sum(d['metrics']['memory_usage_percent'] for d in monitoring_data) / len(monitoring_data), 1)
            avg_rps = round(sum(d['metrics']['requests_per_second'] for d in monitoring_data) / len(monitoring_data), 1)
        else:
            avg_cpu = avg_memory = avg_rps = 0

        return {
            'operation': 'real_time_monitoring',
            'monitoring_complete': True,
            'requested_duration': duration_int,
            'actual_duration': round(total_time, 2),
            'data_points_collected': len(monitoring_data),
            'collection_interval': interval_float,
            'summary': {
                'avg_cpu_percent': avg_cpu,
                'avg_memory_percent': avg_memory,
                'avg_requests_per_second': avg_rps,
                'healthy_samples': len([d for d in monitoring_data if d['status'] == 'healthy']),
                'warning_samples': len([d for d in monitoring_data if d['status'] == 'warning'])
            },
            'real_time_data': monitoring_data
        }
    except Exception as e:
        return {
            'operation': 'real_time_monitoring',
            'error': f"Error in real_time_monitoring: {str(e)}",
            'monitoring_complete': False,
            'data_points_collected': 0
        }

# Async resources
@mcp.resource("async://live-dashboard", mime_type="application/json")
async def get_live_dashboard() -> Dict[str, Any]:
    """Get live dashboard data"""
    try:
        await asyncio.sleep(0.02)  # Simulate async data collection

        return {
            'dashboard_type': 'live_metrics',
            'timestamp': datetime.now().isoformat(),
            'data_freshness': 'real_time',
            'metrics': {
                'current_load': random.randint(20, 80),
                'active_users': random.randint(50, 500),
                'requests_per_minute': random.randint(1000, 5000),
                'avg_response_time_ms': round(random.uniform(0.5, 3.0), 2),
                'error_rate_percent': round(random.uniform(0.1, 2.0), 2)
            },
            'system_health': {
                'database': 'healthy',
                'cache': 'healthy',
                'api_gateway': 'healthy',
                'message_queue': 'healthy'
            },
            'async_collected': True
        }
    except Exception as e:
        return {
            'error': f"Error in get_live_dashboard: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }

@mcp.resource("async://performance-report", mime_type="text/markdown")
async def get_performance_report() -> str:
    """Get async performance report"""
    try:
        await asyncio.sleep(0.05)  # Simulate report generation

        return f"""# Async Native Performance Report

**Generated**: {datetime.now().isoformat()}
**Server**: Standalone Async Native ChukMCPServer
**Framework**: ChukMCPServer with chuk_mcp

## 🚀 Async Capabilities Demonstrated

### Concurrent Operations
- Multiple API calls executed simultaneously
- Significant time savings through concurrency
- Non-blocking I/O operations

### Stream Processing
- Async generators for data streaming
- Memory-efficient processing
- Real-time data handling

### Batch Processing
- Concurrent processing within batches
- Optimized throughput
- Scalable batch sizes

### Real-time Monitoring
- Live data collection
- Configurable monitoring intervals
- Async metric aggregation

## 📊 Performance Benefits

- **Concurrency**: Execute multiple operations simultaneously
- **Efficiency**: Non-blocking async operations
- **Scalability**: Handle thousands of concurrent requests
- **Responsiveness**: Real-time data processing
- **Resource Usage**: Efficient memory and CPU utilization
- **Type Safety**: Robust parameter conversion

---
**Powered by ChukMCPServer Async Native Architecture** 🌊
"""
    except Exception as e:
        return f"Error generating performance report: {str(e)}"

if __name__ == "__main__":
    print("🌟 Starting Standalone Async Native ChukMCPServer...")
    mcp.run(host="localhost", port=8001, debug=False)
'''

        with open(self.temp_file, "w") as f:
            f.write(server_code)

        print("   ✅ Server file created")

    async def _start_server(self):
        """Start the async native server"""
        print("🚀 Starting async native server on port 8001...")

        self.server_process = subprocess.Popen(
            [sys.executable, self.temp_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        print("   Server starting...")

    async def _wait_for_server(self, max_wait: int = 15):
        """Wait for server to be ready"""
        print("⏳ Waiting for server to be ready...")

        async with httpx.AsyncClient() as client:
            for _attempt in range(max_wait):
                try:
                    response = await client.get(f"{self.server_url}/health", timeout=2.0)
                    if response.status_code == 200:
                        print("   ✅ Server ready!")
                        return
                except Exception:
                    await asyncio.sleep(1)

            raise Exception("Server failed to start")

    async def _discover_capabilities(self):
        """Discover server capabilities"""
        print("\n🔍 Discovering Server Capabilities...")

        async with httpx.AsyncClient() as client:
            # Initialize session
            session_id = await self._init_session(client)
            headers = self._get_headers(session_id)

            # Get tools
            tools_response = await client.post(
                f"{self.mcp_url}",
                json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                headers=headers,
            )

            tools = []
            if tools_response.status_code == 200:
                data = tools_response.json()
                if "result" in data and "tools" in data["result"]:
                    tools = data["result"]["tools"]

            # Get resources
            resources_response = await client.post(
                f"{self.mcp_url}",
                json={"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}},
                headers=headers,
            )

            resources = []
            if resources_response.status_code == 200:
                data = resources_response.json()
                if "result" in data and "resources" in data["result"]:
                    resources = data["result"]["resources"]

            print(f"   📋 Tools found: {len(tools)}")
            for tool in tools:
                print(f"      - {tool['name']}: {tool.get('description', 'No description')[:50]}...")

            print(f"   📄 Resources found: {len(resources)}")
            for resource in resources:
                print(f"      - {resource['uri']}: {resource.get('name', 'No name')}")

    async def _test_basic_tools(self):
        """Test basic async tools"""
        print("\n🔧 Testing Basic Async Tools...")

        async with httpx.AsyncClient() as client:
            session_id = await self._init_session(client)
            headers = self._get_headers(session_id)

            # Test async_hello
            print("   Testing async_hello...")
            start_time = time.time()

            response = await client.post(
                f"{self.mcp_url}",
                json={
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": "async_hello", "arguments": {"name": "Demo User", "delay": 0.1}},
                },
                headers=headers,
            )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                content = self._extract_content(result)
                print(f"      ✅ Success in {elapsed:.3f}s: {content}")
            else:
                print(f"      ❌ Failed: {response.status_code}")

    async def _test_async_features(self):
        """Test advanced async features"""
        print("\n⚡ Testing Advanced Async Features...")

        async with httpx.AsyncClient() as client:
            session_id = await self._init_session(client)
            headers = self._get_headers(session_id)

            # Test concurrent API calls
            print("   🌐 Testing concurrent_api_calls...")
            start_time = time.time()

            response = await client.post(
                f"{self.mcp_url}",
                json={
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "concurrent_api_calls",
                        "arguments": {"endpoints": ["users", "orders", "inventory", "analytics", "reports"]},
                    },
                },
                headers=headers,
            )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                content = self._extract_content(result)
                if "error" in content:
                    print(f"      ❌ Error: {content['error']}")
                else:
                    print(f"      ✅ Success in {elapsed:.3f}s")
                    print(f"         Endpoints: {content.get('total_endpoints', 0)}")
                    print(f"         Concurrent: {content.get('concurrent_execution', False)}")
                    print(f"         Server time: {content.get('total_time_seconds', 0)}s")
                    print(f"         Time saved: {content.get('performance', {}).get('time_saved_by_concurrency', 0)}s")
            else:
                print(f"      ❌ Failed: {response.status_code}")

            # Test stream processing
            print("   🌊 Testing stream_processing...")
            start_time = time.time()

            response = await client.post(
                f"{self.mcp_url}",
                json={
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {"name": "stream_processing", "arguments": {"item_count": 5, "process_delay": 0.05}},
                },
                headers=headers,
            )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                content = self._extract_content(result)
                if "error" in content:
                    print(f"      ❌ Error: {content['error']}")
                else:
                    print(f"      ✅ Success in {elapsed:.3f}s")
                    print(f"         Items processed: {content.get('items_processed', 0)}")
                    print(f"         Stream time: {content.get('total_time_seconds', 0)}s")
                    print(f"         Items/sec: {content.get('streaming_efficiency', {}).get('items_per_second', 0)}")
            else:
                print(f"      ❌ Failed: {response.status_code}")

            # Test batch processing
            print("   📦 Testing batch_processing...")
            start_time = time.time()

            response = await client.post(
                f"{self.mcp_url}",
                json={
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "batch_processing",
                        "arguments": {"items": ["item1", "item2", "item3", "item4", "item5", "item6"], "batch_size": 3},
                    },
                },
                headers=headers,
            )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                content = self._extract_content(result)
                if "error" in content:
                    print(f"      ❌ Error: {content['error']}")
                else:
                    print(f"      ✅ Success in {elapsed:.3f}s")
                    print(f"         Items: {content.get('total_items', 0)}")
                    print(f"         Batches: {content.get('total_batches', 0)}")
                    print(f"         Items/sec: {content.get('efficiency', {}).get('items_per_second', 0)}")
            else:
                print(f"      ❌ Failed: {response.status_code}")

            # Test real-time monitoring
            print("   📊 Testing real_time_monitoring...")
            start_time = time.time()

            response = await client.post(
                f"{self.mcp_url}",
                json={
                    "jsonrpc": "2.0",
                    "id": 8,
                    "method": "tools/call",
                    "params": {"name": "real_time_monitoring", "arguments": {"duration": 2, "interval": 0.4}},
                },
                headers=headers,
            )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                content = self._extract_content(result)
                if "error" in content:
                    print(f"      ❌ Error: {content['error']}")
                else:
                    print(f"      ✅ Success in {elapsed:.3f}s")
                    print(f"         Data points: {content.get('data_points_collected', 0)}")
                    print(f"         Avg CPU: {content.get('summary', {}).get('avg_cpu_percent', 0)}%")
                    print(f"         Avg Memory: {content.get('summary', {}).get('avg_memory_percent', 0)}%")
            else:
                print(f"      ❌ Failed: {response.status_code}")

    async def _test_resources(self):
        """Test async resources"""
        print("\n📄 Testing Async Resources...")

        async with httpx.AsyncClient() as client:
            session_id = await self._init_session(client)
            headers = self._get_headers(session_id)

            resources = ["async://live-dashboard", "async://performance-report"]

            for uri in resources:
                print(f"   Reading {uri}...")
                start_time = time.time()

                response = await client.post(
                    f"{self.mcp_url}",
                    json={"jsonrpc": "2.0", "id": 9, "method": "resources/read", "params": {"uri": uri}},
                    headers=headers,
                )

                elapsed = time.time() - start_time

                if response.status_code == 200:
                    result = response.json()
                    if "result" in result and "contents" in result["result"]:
                        contents = result["result"]["contents"]
                        if contents:
                            content_size = len(str(contents[0]))
                            mime_type = contents[0].get("mimeType", "unknown")
                            print(f"      ✅ Success in {elapsed:.3f}s - {content_size} chars ({mime_type})")
                        else:
                            print(f"      ✅ Success in {elapsed:.3f}s - Empty content")
                    else:
                        print("      ❌ Unexpected response format")
                else:
                    print(f"      ❌ Failed: {response.status_code}")

    async def _performance_test(self):
        """Quick performance test"""
        print("\n🚀 Performance Test...")

        async with httpx.AsyncClient() as client:
            session_id = await self._init_session(client)
            headers = self._get_headers(session_id)

            # Test rapid calls
            print("   Testing rapid sequential calls...")
            iterations = 10
            times = []

            for i in range(iterations):
                start_time = time.time()

                response = await client.post(
                    f"{self.mcp_url}",
                    json={
                        "jsonrpc": "2.0",
                        "id": 10 + i,
                        "method": "tools/call",
                        "params": {"name": "async_hello", "arguments": {"name": f"User{i}", "delay": 0.01}},
                    },
                    headers=headers,
                )

                elapsed = time.time() - start_time
                times.append(elapsed)

                if response.status_code != 200:
                    print(f"      Request {i} failed")

            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                rps = 1 / avg_time if avg_time > 0 else 0

                print("   📊 Performance Results:")
                print(f"      Iterations: {iterations}")
                print(f"      Avg time: {avg_time * 1000:.1f}ms")
                print(f"      Min time: {min_time * 1000:.1f}ms")
                print(f"      Max time: {max_time * 1000:.1f}ms")
                print(f"      RPS: {rps:.1f}")

                if avg_time < 0.05:
                    rating = "🚀 Excellent"
                elif avg_time < 0.1:
                    rating = "✅ Good"
                else:
                    rating = "⚡ Fair"

                print(f"      Rating: {rating}")

    def _show_comparison(self):
        """Show comparison with traditional server"""
        print("\n📊 Async Native vs Traditional Comparison")
        print("=" * 60)
        print("🔧 Traditional Server (Port 8000):")
        print("   ✅ 7 traditional tools (hello, add, calculate, etc.)")
        print("   ✅ High RPS for simple operations")
        print("   ✅ Excellent performance for standard use cases")
        print("   ✅ Production-ready and stable")
        print()
        print("🚀 Async Native Server (Port 8001):")
        print("   ✅ 5 async-first tools with advanced capabilities")
        print("   ✅ Concurrent API calls (multiple simultaneous requests)")
        print("   ✅ Stream processing (async generators)")
        print("   ✅ Batch processing (concurrent batches)")
        print("   ✅ Real-time monitoring (live data collection)")
        print("   ✅ Async resources with live data")
        print("   ✅ Type-safe parameter handling")
        print()
        print("🎯 Key Differences:")
        print("   Traditional: Async-compatible tools (work well with async)")
        print("   Async Native: Async-first tools (designed for concurrency)")
        print("   Use Case: Choose based on your specific requirements")
        print()
        print("🏆 Both demonstrate excellent ChukMCPServer capabilities!")
        print("   The async server showcases advanced concurrent programming patterns")
        print("=" * 60)

    async def _init_session(self, client: httpx.AsyncClient) -> str:
        """Initialize MCP session and return session ID"""
        init_response = await client.post(
            f"{self.mcp_url}",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "standalone-demo", "version": "1.0.0"},
                },
            },
        )

        session_id = init_response.headers.get("Mcp-Session-Id")

        # Send initialized notification
        headers = {"Content-Type": "application/json"}
        if session_id:
            headers["Mcp-Session-Id"] = session_id

        await client.post(
            f"{self.mcp_url}",
            json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            headers=headers,
        )

        return session_id

    def _get_headers(self, session_id: str) -> dict:
        """Get headers with session ID"""
        headers = {"Content-Type": "application/json"}
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        return headers

    def _extract_content(self, result: dict) -> any:
        """Extract content from MCP result"""
        if "result" in result and "content" in result["result"]:
            content = result["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                content_item = content[0]
                if isinstance(content_item, dict) and "text" in content_item:
                    try:
                        return json.loads(content_item["text"])
                    except json.JSONDecodeError:
                        return content_item["text"]
                return content_item
            return content
        return result

    async def _cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up...")

        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("   ✅ Server stopped")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                print("   🔪 Server force killed")
            except Exception as e:
                print(f"   ⚠️ Error stopping server: {e}")

        # Clean up temp file
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
            print("   ✅ Temp files cleaned")


async def main():
    """Main entry point"""
    demo = StandaloneAsyncDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
