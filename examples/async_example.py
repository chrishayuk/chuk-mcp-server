#!/usr/bin/env python3
"""
ChukMCPServer - Async Production Ready Example

This is the async-native version that demonstrates advanced concurrent,
streaming, and real-time capabilities using ChukMCPServer framework.
"""

import asyncio
import json
import time
import random
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

# Import our modular ChukMCPServer framework
from chuk_mcp_server import ChukMCPServer, Capabilities

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create Async-Native ChukMCP Server
mcp = ChukMCPServer(
    name="ChukMCPServer Async Example",
    version="2.0.0", 
    title="ChukMCPServer Async Production Server",
    description="An async-native MCP server demonstrating advanced concurrent capabilities",
    capabilities=Capabilities(
        tools=True,
        resources=True,
        prompts=False,
        logging=False
    )
)

# ============================================================================
# Type-Safe Helper Functions
# ============================================================================

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

# ============================================================================
# Async-Native Tools with Advanced Capabilities
# ============================================================================

@mcp.tool
async def async_hello(name: str, delay: Union[str, int, float] = 0.1) -> str:
    """
    Async hello with configurable delay.
    
    Args:
        name: Name to greet
        delay: Delay in seconds (demonstrates async behavior)
    """
    try:
        delay_float = ensure_float(delay)
        
        # Ensure reasonable bounds
        if delay_float < 0:
            delay_float = 0.0
        elif delay_float > 5.0:
            delay_float = 5.0
            
        await asyncio.sleep(delay_float)
        return f"Hello, {name}! (processed async after {delay_float}s delay)"
    except Exception as e:
        return f"Hello, {name}! (error: {str(e)})"

@mcp.tool
async def concurrent_web_requests(urls: List[str], timeout: Union[str, float] = 5.0) -> Dict[str, Any]:
    """
    Make multiple concurrent web requests (simulated).
    
    Args:
        urls: List of URLs to request
        timeout: Request timeout in seconds
    """
    try:
        timeout_float = ensure_float(timeout)
        
        async def simulate_web_request(url: str):
            # Simulate realistic web request timing
            request_time = 0.1 + random.random() * 0.5
            await asyncio.sleep(request_time)
            
            # Simulate occasional failures
            success = random.random() > 0.1
            
            return {
                'url': url,
                'status': 200 if success else 500,
                'response_time_ms': round(request_time * 1000, 1),
                'content_length': random.randint(1000, 50000) if success else 0,
                'timestamp': datetime.now().isoformat(),
                'success': success
            }
        
        start_time = time.time()
        
        # Execute all requests concurrently
        tasks = [simulate_web_request(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Process results
        successful_results = []
        failed_results = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_results.append({"error": str(result)})
            elif result['success']:
                successful_results.append(result)
            else:
                failed_results.append(result)
        
        return {
            'operation': 'concurrent_web_requests',
            'total_urls': len(urls),
            'successful_requests': len(successful_results),
            'failed_requests': len(failed_results),
            'total_time_seconds': round(total_time, 3),
            'concurrent_execution': True,
            'performance': {
                'avg_response_time_ms': round(
                    sum(r['response_time_ms'] for r in successful_results) / len(successful_results), 1
                ) if successful_results else 0,
                'requests_per_second': round(len(urls) / total_time, 1),
                'time_saved_vs_sequential': round(
                    sum(r['response_time_ms'] for r in successful_results) / 1000 - total_time, 3
                ) if successful_results else 0
            },
            'results': {
                'successful': successful_results,
                'failed': failed_results
            }
        }
    except Exception as e:
        return {
            'operation': 'concurrent_web_requests',
            'error': f"Error in concurrent requests: {str(e)}",
            'total_urls': len(urls) if urls else 0,
            'successful_requests': 0,
            'failed_requests': len(urls) if urls else 0
        }

@mcp.tool
async def data_stream_processor(
    item_count: Union[str, int] = 10, 
    process_delay: Union[str, float] = 0.1,
    batch_size: Union[str, int] = 3
) -> Dict[str, Any]:
    """
    Process data using async streaming patterns with batching.
    
    Args:
        item_count: Number of items to process
        process_delay: Processing delay per item in seconds
        batch_size: Size of processing batches
    """
    try:
        item_count_int = ensure_int(item_count)
        process_delay_float = ensure_float(process_delay)
        batch_size_int = ensure_int(batch_size)
        
        # Ensure reasonable bounds
        item_count_int = max(1, min(item_count_int, 50))
        process_delay_float = max(0.001, min(process_delay_float, 2.0))
        batch_size_int = max(1, min(batch_size_int, item_count_int))
        
        async def data_stream_generator(count: int):
            """Async generator for streaming data"""
            for i in range(count):
                await asyncio.sleep(0.01)  # Simulate data arrival
                yield {
                    'id': i,
                    'timestamp': datetime.now().isoformat(),
                    'data': f'item_{i}',
                    'value': random.randint(1, 1000),
                    'category': random.choice(['A', 'B', 'C'])
                }
        
        async def process_batch(batch_items: List[Dict]):
            """Process a batch of items concurrently"""
            async def process_single_item(item: Dict):
                await asyncio.sleep(process_delay_float)
                return {
                    **item,
                    'processed': True,
                    'processed_at': datetime.now().isoformat(),
                    'processing_time_ms': process_delay_float * 1000,
                    'processed_value': item['value'] * 2
                }
            
            # Process all items in batch concurrently
            return await asyncio.gather(*[process_single_item(item) for item in batch_items])
        
        processed_items = []
        current_batch = []
        start_time = time.time()
        
        # Stream and batch process data
        async for data_item in data_stream_generator(item_count_int):
            current_batch.append(data_item)
            
            # Process when batch is full
            if len(current_batch) >= batch_size_int:
                batch_results = await process_batch(current_batch)
                processed_items.extend(batch_results)
                current_batch = []
        
        # Process remaining items
        if current_batch:
            batch_results = await process_batch(current_batch)
            processed_items.extend(batch_results)
        
        total_time = time.time() - start_time
        
        return {
            'operation': 'data_stream_processor',
            'stream_complete': True,
            'total_items': item_count_int,
            'items_processed': len(processed_items),
            'batch_size': batch_size_int,
            'total_batches': (item_count_int + batch_size_int - 1) // batch_size_int,
            'total_time_seconds': round(total_time, 3),
            'streaming_efficiency': {
                'items_per_second': round(len(processed_items) / total_time, 1) if total_time > 0 else 0,
                'avg_processing_time_ms': round((total_time / len(processed_items)) * 1000, 1) if processed_items else 0,
                'memory_efficient': True,
                'concurrent_batching': True
            },
            'processed_items': processed_items
        }
    except Exception as e:
        return {
            'operation': 'data_stream_processor',
            'error': f"Error in stream processing: {str(e)}",
            'items_processed': 0,
            'stream_complete': False
        }

@mcp.tool
async def real_time_dashboard(
    duration: Union[str, int] = 5, 
    update_interval: Union[str, float] = 0.5
) -> Dict[str, Any]:
    """
    Generate real-time dashboard data with live metrics.
    
    Args:
        duration: Monitoring duration in seconds
        update_interval: Update interval in seconds
    """
    try:
        duration_int = ensure_int(duration)
        interval_float = ensure_float(update_interval)
        
        # Ensure reasonable bounds
        duration_int = max(1, min(duration_int, 30))
        interval_float = max(0.1, min(interval_float, 5.0))
        
        metrics_data = []
        start_time = time.time()
        end_time = start_time + duration_int
        
        while time.time() < end_time:
            await asyncio.sleep(interval_float)
            
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Simulate realistic system metrics
            cpu_base = 30 + 20 * random.random()
            memory_base = 40 + 30 * random.random()
            
            data_point = {
                'timestamp': datetime.now().isoformat(),
                'elapsed_seconds': round(elapsed, 2),
                'system_metrics': {
                    'cpu_usage_percent': round(cpu_base + 10 * random.random(), 1),
                    'memory_usage_percent': round(memory_base + 15 * random.random(), 1),
                    'disk_io_mbps': round(50 + 100 * random.random(), 1),
                    'network_io_mbps': round(10 + 40 * random.random(), 1)
                },
                'application_metrics': {
                    'active_connections': random.randint(50, 200),
                    'requests_per_second': random.randint(100, 500),
                    'avg_response_time_ms': round(50 + 200 * random.random(), 1),
                    'error_rate_percent': round(random.random() * 2, 2)
                },
                'business_metrics': {
                    'active_users': random.randint(1000, 5000),
                    'transactions_per_minute': random.randint(50, 300),
                    'revenue_per_hour': round(1000 + 500 * random.random(), 2)
                },
                'health_status': 'healthy' if random.random() > 0.15 else 'warning'
            }
            metrics_data.append(data_point)
        
        total_time = time.time() - start_time
        
        # Calculate aggregated metrics
        if metrics_data:
            avg_cpu = round(sum(d['system_metrics']['cpu_usage_percent'] for d in metrics_data) / len(metrics_data), 1)
            avg_memory = round(sum(d['system_metrics']['memory_usage_percent'] for d in metrics_data) / len(metrics_data), 1)
            avg_response_time = round(sum(d['application_metrics']['avg_response_time_ms'] for d in metrics_data) / len(metrics_data), 1)
            total_transactions = sum(d['business_metrics']['transactions_per_minute'] for d in metrics_data)
        else:
            avg_cpu = avg_memory = avg_response_time = total_transactions = 0
        
        return {
            'operation': 'real_time_dashboard',
            'monitoring_complete': True,
            'requested_duration': duration_int,
            'actual_duration': round(total_time, 2),
            'update_interval': interval_float,
            'data_points_collected': len(metrics_data),
            'summary_metrics': {
                'avg_cpu_percent': avg_cpu,
                'avg_memory_percent': avg_memory,
                'avg_response_time_ms': avg_response_time,
                'total_transactions': total_transactions,
                'healthy_samples': len([d for d in metrics_data if d['health_status'] == 'healthy']),
                'warning_samples': len([d for d in metrics_data if d['health_status'] == 'warning'])
            },
            'real_time_data': metrics_data,
            'dashboard_features': {
                'real_time_updates': True,
                'multi_metric_tracking': True,
                'health_monitoring': True,
                'business_intelligence': True
            }
        }
    except Exception as e:
        return {
            'operation': 'real_time_dashboard',
            'error': f"Error in real-time monitoring: {str(e)}",
            'monitoring_complete': False,
            'data_points_collected': 0
        }

@mcp.tool
async def async_file_processor(
    file_count: Union[str, int] = 5,
    processing_complexity: str = "medium"
) -> Dict[str, Any]:
    """
    Simulate async file processing with different complexity levels.
    
    Args:
        file_count: Number of files to process
        processing_complexity: Processing complexity ("simple", "medium", "complex")
    """
    try:
        file_count_int = ensure_int(file_count)
        file_count_int = max(1, min(file_count_int, 20))
        
        # Define processing complexity
        complexity_settings = {
            "simple": {"base_time": 0.1, "variance": 0.05, "operations": ["parse", "validate"]},
            "medium": {"base_time": 0.3, "variance": 0.1, "operations": ["parse", "validate", "transform", "index"]},
            "complex": {"base_time": 0.8, "variance": 0.2, "operations": ["parse", "validate", "transform", "analyze", "optimize", "compress"]}
        }
        
        if processing_complexity not in complexity_settings:
            processing_complexity = "medium"
        
        settings = complexity_settings[processing_complexity]
        
        async def process_single_file(file_id: int):
            """Process a single file with realistic operations"""
            file_name = f"file_{file_id:03d}.dat"
            file_size = random.randint(1024, 1024*1024)  # 1KB to 1MB
            
            processing_time = settings["base_time"] + random.uniform(-settings["variance"], settings["variance"])
            processing_time = max(0.05, processing_time)  # Minimum processing time
            
            # Simulate processing steps
            operations_completed = []
            step_time = processing_time / len(settings["operations"])
            
            for operation in settings["operations"]:
                await asyncio.sleep(step_time)
                operations_completed.append({
                    "operation": operation,
                    "completed_at": datetime.now().isoformat(),
                    "duration_ms": round(step_time * 1000, 1)
                })
            
            return {
                'file_id': file_id,
                'file_name': file_name,
                'file_size_bytes': file_size,
                'processing_time_ms': round(processing_time * 1000, 1),
                'complexity': processing_complexity,
                'operations_completed': operations_completed,
                'processed_at': datetime.now().isoformat(),
                'success': True,
                'throughput_mbps': round((file_size / (1024 * 1024)) / processing_time, 2)
            }
        
        start_time = time.time()
        
        # Process all files concurrently
        tasks = [process_single_file(i) for i in range(file_count_int)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Calculate aggregated statistics
        total_size = sum(r['file_size_bytes'] for r in results)
        avg_processing_time = sum(r['processing_time_ms'] for r in results) / len(results)
        total_throughput = (total_size / (1024 * 1024)) / total_time  # MB/s
        
        return {
            'operation': 'async_file_processor',
            'processing_complete': True,
            'files_processed': len(results),
            'processing_complexity': processing_complexity,
            'total_time_seconds': round(total_time, 3),
            'performance_metrics': {
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'avg_processing_time_ms': round(avg_processing_time, 1),
                'total_throughput_mbps': round(total_throughput, 2),
                'files_per_second': round(len(results) / total_time, 1),
                'concurrent_processing': True
            },
            'complexity_info': {
                'level': processing_complexity,
                'operations_per_file': len(settings["operations"]),
                'avg_operations_time_ms': round(avg_processing_time / len(settings["operations"]), 1)
            },
            'processed_files': results
        }
    except Exception as e:
        return {
            'operation': 'async_file_processor',
            'error': f"Error in file processing: {str(e)}",
            'files_processed': 0,
            'processing_complete': False
        }

@mcp.tool
async def distributed_task_coordinator(
    task_count: Union[str, int] = 8,
    worker_count: Union[str, int] = 3
) -> Dict[str, Any]:
    """
    Simulate distributed task coordination with multiple workers.
    
    Args:
        task_count: Number of tasks to distribute
        worker_count: Number of worker processes
    """
    try:
        task_count_int = ensure_int(task_count)
        worker_count_int = ensure_int(worker_count)
        
        task_count_int = max(1, min(task_count_int, 50))
        worker_count_int = max(1, min(worker_count_int, 10))
        
        # Create task queue
        task_queue = asyncio.Queue()
        results_queue = asyncio.Queue()
        
        # Generate tasks
        tasks = []
        for i in range(task_count_int):
            task = {
                'task_id': i,
                'task_type': random.choice(['compute', 'network', 'database', 'analysis']),
                'priority': random.choice(['low', 'medium', 'high']),
                'estimated_duration': random.uniform(0.1, 1.0),
                'created_at': datetime.now().isoformat()
            }
            tasks.append(task)
            await task_queue.put(task)
        
        async def worker(worker_id: int):
            """Simulate a distributed worker"""
            worker_results = []
            
            while True:
                try:
                    task = await asyncio.wait_for(task_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    break
                
                # Simulate task processing
                start_time = time.time()
                processing_time = task['estimated_duration'] * (0.8 + 0.4 * random.random())
                await asyncio.sleep(processing_time)
                
                result = {
                    'task_id': task['task_id'],
                    'worker_id': worker_id,
                    'task_type': task['task_type'],
                    'priority': task['priority'],
                    'estimated_duration': task['estimated_duration'],
                    'actual_duration': round(processing_time, 3),
                    'started_at': start_time,
                    'completed_at': time.time(),
                    'success': random.random() > 0.05,  # 95% success rate
                    'result_size_kb': random.randint(1, 100)
                }
                
                worker_results.append(result)
                await results_queue.put(result)
                task_queue.task_done()
            
            return worker_results
        
        start_time = time.time()
        
        # Start all workers concurrently
        worker_tasks = [worker(i) for i in range(worker_count_int)]
        worker_results = await asyncio.gather(*worker_tasks)
        
        # Collect all results
        all_results = []
        for worker_result_list in worker_results:
            all_results.extend(worker_result_list)
        
        total_time = time.time() - start_time
        
        # Calculate performance metrics
        successful_tasks = [r for r in all_results if r['success']]
        failed_tasks = [r for r in all_results if not r['success']]
        
        if successful_tasks:
            avg_processing_time = sum(r['actual_duration'] for r in successful_tasks) / len(successful_tasks)
            total_result_size = sum(r['result_size_kb'] for r in successful_tasks)
        else:
            avg_processing_time = 0
            total_result_size = 0
        
        # Worker performance analysis
        worker_performance = {}
        for worker_result_list in worker_results:
            if worker_result_list:
                worker_id = worker_result_list[0]['worker_id']
                worker_performance[f'worker_{worker_id}'] = {
                    'tasks_completed': len(worker_result_list),
                    'success_rate': round(sum(1 for r in worker_result_list if r['success']) / len(worker_result_list) * 100, 1),
                    'avg_processing_time': round(sum(r['actual_duration'] for r in worker_result_list) / len(worker_result_list), 3)
                }
        
        return {
            'operation': 'distributed_task_coordinator',
            'coordination_complete': True,
            'total_tasks': task_count_int,
            'worker_count': worker_count_int,
            'tasks_completed': len(all_results),
            'successful_tasks': len(successful_tasks),
            'failed_tasks': len(failed_tasks),
            'total_time_seconds': round(total_time, 3),
            'performance_metrics': {
                'tasks_per_second': round(len(all_results) / total_time, 1),
                'avg_processing_time': round(avg_processing_time, 3),
                'success_rate_percent': round(len(successful_tasks) / len(all_results) * 100, 1) if all_results else 0,
                'total_result_size_kb': total_result_size,
                'concurrent_workers': worker_count_int
            },
            'worker_performance': worker_performance,
            'task_results': all_results
        }
    except Exception as e:
        return {
            'operation': 'distributed_task_coordinator',
            'error': f"Error in task coordination: {str(e)}",
            'tasks_completed': 0,
            'coordination_complete': False
        }

# ============================================================================
# Async Resources with Live Data
# ============================================================================

@mcp.resource("async://server-metrics", mime_type="application/json")
async def get_server_metrics() -> Dict[str, Any]:
    """Get live server metrics (async collection)."""
    await asyncio.sleep(0.05)  # Simulate async metric collection
    
    return {
        'server_type': 'async_native',
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': time.time(),
        'metrics': {
            'active_coroutines': len(asyncio.all_tasks()),
            'event_loop_time': round(time.time() % 1, 6),
            'memory_usage_mb': random.randint(50, 200),
            'cpu_usage_percent': random.randint(10, 80),
            'async_operations_per_second': random.randint(100, 1000)
        },
        'capabilities': {
            'concurrent_requests': True,
            'streaming_data': True,
            'real_time_monitoring': True,
            'distributed_processing': True,
            'auto_scaling': True
        },
        'performance': {
            'avg_response_time_ms': round(random.uniform(5, 50), 1),
            'throughput_ops_per_sec': random.randint(500, 2000),
            'concurrent_connections': random.randint(10, 100)
        }
    }

@mcp.resource("async://performance-report", mime_type="text/markdown")
async def get_async_performance_report() -> str:
    """Get comprehensive async performance report."""
    await asyncio.sleep(0.1)  # Simulate report generation
    
    return f"""# Async Native Performance Report

**Generated**: {datetime.now().isoformat()}  
**Server**: ChukMCPServer Async Production Server  
**Framework**: ChukMCPServer with chuk_mcp  

## 🚀 Async-Native Capabilities

### Advanced Concurrent Operations
- **Concurrent Web Requests**: Multiple HTTP requests executed simultaneously
- **Data Stream Processing**: Async generators with concurrent batch processing
- **Real-time Dashboard**: Live metrics collection and aggregation
- **Async File Processing**: Concurrent file operations with complexity scaling
- **Distributed Task Coordination**: Multi-worker task distribution

### Performance Characteristics
- **Non-blocking I/O**: All operations use async/await patterns
- **Concurrent Execution**: Multiple operations run simultaneously
- **Memory Efficiency**: Streaming data processing without full buffering
- **Scalable Architecture**: Worker pools and task distribution
- **Real-time Capabilities**: Live data collection and monitoring

## 📊 Performance Benefits

### Concurrency Advantages
- **Simultaneous Operations**: Execute multiple tasks at once
- **Efficient Resource Usage**: Non-blocking I/O operations
- **Scalable Throughput**: Handle thousands of concurrent requests
- **Real-time Processing**: Live data streaming and processing
- **Distributed Computing**: Coordinate multiple workers

### Use Cases
- **API Aggregation**: Concurrent calls to multiple services
- **Data Pipeline Processing**: Stream large datasets efficiently
- **Real-time Analytics**: Live dashboard and monitoring
- **File Processing**: Batch processing with concurrency
- **Microservices Coordination**: Distribute tasks across workers

## 🔧 Technical Implementation

### Async Patterns Used
- **Async/Await**: Native Python async syntax
- **Asyncio.gather()**: Concurrent task execution
- **Async Generators**: Memory-efficient data streaming
- **Queue-based Processing**: Producer-consumer patterns
- **Worker Pools**: Distributed task processing

### Type Safety
- **Union Types**: Accept multiple parameter formats
- **Type Conversion**: Robust string→number conversion
- **Bounds Checking**: Validate parameter ranges
- **Error Handling**: Graceful failure recovery

## 🎯 Comparison with Traditional Servers

| Aspect | Traditional Server | Async Native Server |
|--------|-------------------|-------------------|
| **Throughput** | High for simple ops | Optimized for concurrent ops |
| **Latency** | Sub-millisecond | Low with concurrency benefits |
| **Concurrency** | Thread-based | Native async/await |
| **Memory Usage** | Higher per request | Efficient streaming |
| **Scalability** | Process-based | Event loop based |
| **Use Case** | High-frequency simple ops | Complex concurrent workflows |

---
**Powered by ChukMCPServer Async-Native Architecture** 🌊⚡
"""

@mcp.resource("async://examples", mime_type="application/json")
async def get_async_examples() -> Dict[str, Any]:
    """Get comprehensive async tool usage examples."""
    await asyncio.sleep(0.03)
    
    return {
        "description": "Async-native tool examples for ChukMCPServer",
        "server_info": {
            "name": "ChukMCPServer Async Example",
            "version": "2.0.0",
            "type": "async_native",
            "tools_count": len(mcp.get_tools()),
            "framework": "ChukMCPServer with chuk_mcp"
        },
        "async_examples": [
            {
                "category": "Concurrent Operations",
                "description": "Demonstrate concurrent execution patterns",
                "examples": [
                    {
                        "tool": "concurrent_web_requests",
                        "arguments": {
                            "urls": ["https://api.example.com/users", "https://api.example.com/orders"],
                            "timeout": 5.0
                        },
                        "description": "Make multiple web requests concurrently"
                    },
                    {
                        "tool": "distributed_task_coordinator", 
                        "arguments": {"task_count": 10, "worker_count": 3},
                        "description": "Distribute tasks across multiple workers"
                    }
                ]
            },
            {
                "category": "Streaming & Real-time",
                "description": "Stream processing and live data",
                "examples": [
                    {
                        "tool": "data_stream_processor",
                        "arguments": {"item_count": 15, "process_delay": 0.1, "batch_size": 5},
                        "description": "Process streaming data with concurrent batching"
                    },
                    {
                        "tool": "real_time_dashboard",
                        "arguments": {"duration": 10, "update_interval": 0.5},
                        "description": "Generate live dashboard metrics"
                    }
                ]
            },
            {
                "category": "File & Batch Processing",
                "description": "Concurrent file and batch operations",
                "examples": [
                    {
                        "tool": "async_file_processor",
                        "arguments": {"file_count": 8, "processing_complexity": "medium"},
                        "description": "Process multiple files concurrently"
                    }
                ]
            },
            {
                "category": "Basic Async Operations",
                "description": "Simple async operations with timing",
                "examples": [
                    {
                        "tool": "async_hello",
                        "arguments": {"name": "AsyncUser", "delay": 0.5},
                        "description": "Async greeting with configurable delay"
                    }
                ]
            }
        ],
        "performance_tips": [
            "Use concurrent operations for I/O-bound tasks",
            "Stream large datasets to maintain memory efficiency",
            "Batch processing improves throughput for many small operations",
            "Real-time monitoring provides insights into system behavior",
            "Distributed coordination scales processing across workers"
        ],
        "async_patterns": {
            "concurrency": "asyncio.gather() for parallel execution",
            "streaming": "async generators for memory-efficient processing", 
            "batching": "Process multiple items simultaneously",
            "coordination": "Queue-based worker distribution",
            "monitoring": "Live metric collection and aggregation"
        }
    }

# ============================================================================
# Production Server Setup
# ============================================================================

def main():
    """Main entry point for async production server."""
    print("🚀 ChukMCPServer Async Production Server")
    print("=" * 50)
    
    # Show server information
    info = mcp.info()
    print(f"Server: {info['server']['name']}")
    print(f"Version: {info['server']['version']}")
    print(f"Type: Async-Native")
    print(f"Framework: ChukMCPServer with chuk_mcp")
    print()
    
    # Handle both old and new info structure
    mcp_info = info.get('mcp_components', info)
    print(f"🔧 Async Tools: {mcp_info['tools']['count']}")
    for tool_name in mcp_info['tools']['names']:
        print(f"   - {tool_name}")
    print()
    print(f"📂 Async Resources: {mcp_info['resources']['count']}")
    for resource_uri in mcp_info['resources']['uris']:
        print(f"   - {resource_uri}")
    print()
    print("🌊 Async Capabilities:")
    print("   - Concurrent operations")
    print("   - Stream processing")
    print("   - Real-time monitoring")
    print("   - Distributed coordination")
    print("   - Batch processing")
    print()
    print("🔍 MCP Inspector Instructions:")
    print("   1. This server: http://localhost:8001/mcp")
    print("   2. Use proxy: http://localhost:8011/mcp/inspector")
    print("   3. Transport: Streamable HTTP")
    print("   4. All async tools and resources available!")
    print("=" * 50)
    
    # Run server in production mode
    try:
        mcp.run(
            host="localhost", 
            port=8001,  # Different port for async server
            debug=False
        )
    except KeyboardInterrupt:
        print("\n👋 Async server shutting down gracefully...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        logging.error(f"Server error: {e}", exc_info=True)

if __name__ == "__main__":
    main()