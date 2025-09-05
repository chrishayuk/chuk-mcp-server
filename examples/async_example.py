#!/usr/bin/env python3
"""
ChukMCPServer - Async Production Ready Example (Resource Performance Optimized)

This version is optimized for maximum performance by:
- Disabling verbose logging during production
- Optimizing resource reads for 20,000+ RPS
- Removing performance bottlenecks from async resources
- Maintaining all async capabilities without overhead
"""

import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Any

# Import our modular ChukMCPServer framework
from chuk_mcp_server import Capabilities, ChukMCPServer

# ============================================================================
# Production Logging Configuration (MINIMAL)
# ============================================================================


def configure_production_logging():
    """Configure minimal logging for production performance"""

    # Set root logger to WARNING (eliminates most framework logs)
    logging.getLogger().setLevel(logging.WARNING)

    # Disable specific ChukMCPServer verbose loggers
    performance_affecting_loggers = [
        "chuk_mcp_server.protocol",  # The main culprit - logs every request
        "chuk_mcp_server.mcp_registry",  # Logs tool/resource operations
        "chuk_mcp_server.endpoint_registry",
        "uvicorn.access",  # HTTP access logs
    ]

    for logger_name in performance_affecting_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)  # Only show critical errors

    # Keep core server logs for startup/shutdown info only
    core_loggers = ["chuk_mcp_server.core", "chuk_mcp_server.http_server"]

    for logger_name in core_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)  # Only warnings and errors

    # Custom formatter for the few logs we do want
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Configure root logger with minimal output
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    print("🔇 Production logging configured - verbose logs disabled for performance")


# Configure production logging BEFORE creating the server
configure_production_logging()

# ============================================================================
# Resource Performance Optimization Cache
# ============================================================================

# Pre-computed static data for maximum performance
STATIC_METRICS_BASE = {
    "server_type": "async_native_optimized",
    "capabilities": {
        "concurrent_requests": True,
        "streaming_data": True,
        "real_time_monitoring": True,
        "distributed_processing": True,
        "auto_scaling": True,
        "production_optimized": True,
    },
}

# Pre-computed random values (refreshed occasionally, not every request)
_cached_metrics = {
    "memory_usage_mb": 150,
    "cpu_usage_percent": 45,
    "async_operations_per_second": 25000,
    "active_connections": 250,
    "concurrent_connections": 150,
    "last_refresh": time.time(),
}


def refresh_cached_metrics():
    """Refresh cached metrics occasionally (not on every request)"""
    global _cached_metrics
    now = time.time()

    # Only refresh every 5 seconds to avoid overhead
    if now - _cached_metrics["last_refresh"] > 5.0:
        _cached_metrics.update(
            {
                "memory_usage_mb": random.randint(100, 200),
                "cpu_usage_percent": random.randint(20, 70),
                "async_operations_per_second": random.randint(20000, 40000),
                "active_connections": random.randint(100, 500),
                "concurrent_connections": random.randint(50, 300),
                "last_refresh": now,
            }
        )


# Create Async-Native ChukMCP Server
mcp = ChukMCPServer(
    name="ChukMCPServer Async Production (Resource Optimized)",
    version="2.0.0",
    title="ChukMCPServer Async Production Server - Resource Performance Optimized",
    description="An async-native MCP server optimized for maximum resource performance",
    capabilities=Capabilities(tools=True, resources=True, prompts=False, logging=False),
)

# ============================================================================
# Type-Safe Helper Functions
# ============================================================================


def ensure_int(value: str | int | float) -> int:
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


def ensure_float(value: str | int | float) -> float:
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
async def async_hello(name: str, delay: str | int | float = 0.1) -> str:
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
async def concurrent_web_requests(urls: list[str], timeout: str | float = 5.0) -> dict[str, Any]:
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
                "url": url,
                "status": 200 if success else 500,
                "response_time_ms": round(request_time * 1000, 1),
                "content_length": random.randint(1000, 50000) if success else 0,
                "timestamp": datetime.now().isoformat(),
                "success": success,
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
            elif result["success"]:
                successful_results.append(result)
            else:
                failed_results.append(result)

        return {
            "operation": "concurrent_web_requests",
            "total_urls": len(urls),
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "total_time_seconds": round(total_time, 3),
            "concurrent_execution": True,
            "performance": {
                "avg_response_time_ms": round(
                    sum(r["response_time_ms"] for r in successful_results) / len(successful_results), 1
                )
                if successful_results
                else 0,
                "requests_per_second": round(len(urls) / total_time, 1),
                "time_saved_vs_sequential": round(
                    sum(r["response_time_ms"] for r in successful_results) / 1000 - total_time, 3
                )
                if successful_results
                else 0,
            },
            "results": {"successful": successful_results, "failed": failed_results},
        }
    except Exception as e:
        return {
            "operation": "concurrent_web_requests",
            "error": f"Error in concurrent requests: {str(e)}",
            "total_urls": len(urls) if urls else 0,
            "successful_requests": 0,
            "failed_requests": len(urls) if urls else 0,
        }


@mcp.tool
async def data_stream_processor(
    item_count: str | int = 10, process_delay: str | float = 0.1, batch_size: str | int = 3
) -> dict[str, Any]:
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
                    "id": i,
                    "timestamp": datetime.now().isoformat(),
                    "data": f"item_{i}",
                    "value": random.randint(1, 1000),
                    "category": random.choice(["A", "B", "C"]),
                }

        async def process_batch(batch_items: list[dict]):
            """Process a batch of items concurrently"""

            async def process_single_item(item: dict):
                await asyncio.sleep(process_delay_float)
                return {
                    **item,
                    "processed": True,
                    "processed_at": datetime.now().isoformat(),
                    "processing_time_ms": process_delay_float * 1000,
                    "processed_value": item["value"] * 2,
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
            "operation": "data_stream_processor",
            "stream_complete": True,
            "total_items": item_count_int,
            "items_processed": len(processed_items),
            "batch_size": batch_size_int,
            "total_batches": (item_count_int + batch_size_int - 1) // batch_size_int,
            "total_time_seconds": round(total_time, 3),
            "streaming_efficiency": {
                "items_per_second": round(len(processed_items) / total_time, 1) if total_time > 0 else 0,
                "avg_processing_time_ms": round((total_time / len(processed_items)) * 1000, 1)
                if processed_items
                else 0,
                "memory_efficient": True,
                "concurrent_batching": True,
            },
            "processed_items": processed_items,
        }
    except Exception as e:
        return {
            "operation": "data_stream_processor",
            "error": f"Error in stream processing: {str(e)}",
            "items_processed": 0,
            "stream_complete": False,
        }


@mcp.tool
async def real_time_dashboard(duration: str | int = 5, update_interval: str | float = 0.5) -> dict[str, Any]:
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
                "timestamp": datetime.now().isoformat(),
                "elapsed_seconds": round(elapsed, 2),
                "system_metrics": {
                    "cpu_usage_percent": round(cpu_base + 10 * random.random(), 1),
                    "memory_usage_percent": round(memory_base + 15 * random.random(), 1),
                    "disk_io_mbps": round(50 + 100 * random.random(), 1),
                    "network_io_mbps": round(10 + 40 * random.random(), 1),
                },
                "application_metrics": {
                    "active_connections": random.randint(50, 200),
                    "requests_per_second": random.randint(100, 500),
                    "avg_response_time_ms": round(50 + 200 * random.random(), 1),
                    "error_rate_percent": round(random.random() * 2, 2),
                },
                "business_metrics": {
                    "active_users": random.randint(1000, 5000),
                    "transactions_per_minute": random.randint(50, 300),
                    "revenue_per_hour": round(1000 + 500 * random.random(), 2),
                },
                "health_status": "healthy" if random.random() > 0.15 else "warning",
            }
            metrics_data.append(data_point)

        total_time = time.time() - start_time

        # Calculate aggregated metrics
        if metrics_data:
            avg_cpu = round(sum(d["system_metrics"]["cpu_usage_percent"] for d in metrics_data) / len(metrics_data), 1)
            avg_memory = round(
                sum(d["system_metrics"]["memory_usage_percent"] for d in metrics_data) / len(metrics_data), 1
            )
            avg_response_time = round(
                sum(d["application_metrics"]["avg_response_time_ms"] for d in metrics_data) / len(metrics_data), 1
            )
            total_transactions = sum(d["business_metrics"]["transactions_per_minute"] for d in metrics_data)
        else:
            avg_cpu = avg_memory = avg_response_time = total_transactions = 0

        return {
            "operation": "real_time_dashboard",
            "monitoring_complete": True,
            "requested_duration": duration_int,
            "actual_duration": round(total_time, 2),
            "update_interval": interval_float,
            "data_points_collected": len(metrics_data),
            "summary_metrics": {
                "avg_cpu_percent": avg_cpu,
                "avg_memory_percent": avg_memory,
                "avg_response_time_ms": avg_response_time,
                "total_transactions": total_transactions,
                "healthy_samples": len([d for d in metrics_data if d["health_status"] == "healthy"]),
                "warning_samples": len([d for d in metrics_data if d["health_status"] == "warning"]),
            },
            "real_time_data": metrics_data,
            "dashboard_features": {
                "real_time_updates": True,
                "multi_metric_tracking": True,
                "health_monitoring": True,
                "business_intelligence": True,
            },
        }
    except Exception as e:
        return {
            "operation": "real_time_dashboard",
            "error": f"Error in real-time monitoring: {str(e)}",
            "monitoring_complete": False,
            "data_points_collected": 0,
        }


@mcp.tool
async def async_file_processor(file_count: str | int = 5, processing_complexity: str = "medium") -> dict[str, Any]:
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
            "complex": {
                "base_time": 0.8,
                "variance": 0.2,
                "operations": ["parse", "validate", "transform", "analyze", "optimize", "compress"],
            },
        }

        if processing_complexity not in complexity_settings:
            processing_complexity = "medium"

        settings = complexity_settings[processing_complexity]

        async def process_single_file(file_id: int):
            """Process a single file with realistic operations"""
            file_name = f"file_{file_id:03d}.dat"
            file_size = random.randint(1024, 1024 * 1024)  # 1KB to 1MB

            processing_time = settings["base_time"] + random.uniform(-settings["variance"], settings["variance"])
            processing_time = max(0.05, processing_time)  # Minimum processing time

            # Simulate processing steps
            operations_completed = []
            step_time = processing_time / len(settings["operations"])

            for operation in settings["operations"]:
                await asyncio.sleep(step_time)
                operations_completed.append(
                    {
                        "operation": operation,
                        "completed_at": datetime.now().isoformat(),
                        "duration_ms": round(step_time * 1000, 1),
                    }
                )

            return {
                "file_id": file_id,
                "file_name": file_name,
                "file_size_bytes": file_size,
                "processing_time_ms": round(processing_time * 1000, 1),
                "complexity": processing_complexity,
                "operations_completed": operations_completed,
                "processed_at": datetime.now().isoformat(),
                "success": True,
                "throughput_mbps": round((file_size / (1024 * 1024)) / processing_time, 2),
            }

        start_time = time.time()

        # Process all files concurrently
        tasks = [process_single_file(i) for i in range(file_count_int)]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Calculate aggregated statistics
        total_size = sum(r["file_size_bytes"] for r in results)
        avg_processing_time = sum(r["processing_time_ms"] for r in results) / len(results)
        total_throughput = (total_size / (1024 * 1024)) / total_time  # MB/s

        return {
            "operation": "async_file_processor",
            "processing_complete": True,
            "files_processed": len(results),
            "processing_complexity": processing_complexity,
            "total_time_seconds": round(total_time, 3),
            "performance_metrics": {
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "avg_processing_time_ms": round(avg_processing_time, 1),
                "total_throughput_mbps": round(total_throughput, 2),
                "files_per_second": round(len(results) / total_time, 1),
                "concurrent_processing": True,
            },
            "complexity_info": {
                "level": processing_complexity,
                "operations_per_file": len(settings["operations"]),
                "avg_operations_time_ms": round(avg_processing_time / len(settings["operations"]), 1),
            },
            "processed_files": results,
        }
    except Exception as e:
        return {
            "operation": "async_file_processor",
            "error": f"Error in file processing: {str(e)}",
            "files_processed": 0,
            "processing_complete": False,
        }


@mcp.tool
async def distributed_task_coordinator(task_count: str | int = 8, worker_count: str | int = 3) -> dict[str, Any]:
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
                "task_id": i,
                "task_type": random.choice(["compute", "network", "database", "analysis"]),
                "priority": random.choice(["low", "medium", "high"]),
                "estimated_duration": random.uniform(0.1, 1.0),
                "created_at": datetime.now().isoformat(),
            }
            tasks.append(task)
            await task_queue.put(task)

        async def worker(worker_id: int):
            """Simulate a distributed worker"""
            worker_results = []

            while True:
                try:
                    task = await asyncio.wait_for(task_queue.get(), timeout=0.1)
                except TimeoutError:
                    break

                # Simulate task processing
                start_time = time.time()
                processing_time = task["estimated_duration"] * (0.8 + 0.4 * random.random())
                await asyncio.sleep(processing_time)

                result = {
                    "task_id": task["task_id"],
                    "worker_id": worker_id,
                    "task_type": task["task_type"],
                    "priority": task["priority"],
                    "estimated_duration": task["estimated_duration"],
                    "actual_duration": round(processing_time, 3),
                    "started_at": start_time,
                    "completed_at": time.time(),
                    "success": random.random() > 0.05,  # 95% success rate
                    "result_size_kb": random.randint(1, 100),
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
        successful_tasks = [r for r in all_results if r["success"]]
        failed_tasks = [r for r in all_results if not r["success"]]

        if successful_tasks:
            avg_processing_time = sum(r["actual_duration"] for r in successful_tasks) / len(successful_tasks)
            total_result_size = sum(r["result_size_kb"] for r in successful_tasks)
        else:
            avg_processing_time = 0
            total_result_size = 0

        # Worker performance analysis
        worker_performance = {}
        for worker_result_list in worker_results:
            if worker_result_list:
                worker_id = worker_result_list[0]["worker_id"]
                worker_performance[f"worker_{worker_id}"] = {
                    "tasks_completed": len(worker_result_list),
                    "success_rate": round(
                        sum(1 for r in worker_result_list if r["success"]) / len(worker_result_list) * 100, 1
                    ),
                    "avg_processing_time": round(
                        sum(r["actual_duration"] for r in worker_result_list) / len(worker_result_list), 3
                    ),
                }

        return {
            "operation": "distributed_task_coordinator",
            "coordination_complete": True,
            "total_tasks": task_count_int,
            "worker_count": worker_count_int,
            "tasks_completed": len(all_results),
            "successful_tasks": len(successful_tasks),
            "failed_tasks": len(failed_tasks),
            "total_time_seconds": round(total_time, 3),
            "performance_metrics": {
                "tasks_per_second": round(len(all_results) / total_time, 1),
                "avg_processing_time": round(avg_processing_time, 3),
                "success_rate_percent": round(len(successful_tasks) / len(all_results) * 100, 1) if all_results else 0,
                "total_result_size_kb": total_result_size,
                "concurrent_workers": worker_count_int,
            },
            "worker_performance": worker_performance,
            "task_results": all_results,
        }
    except Exception as e:
        return {
            "operation": "distributed_task_coordinator",
            "error": f"Error in task coordination: {str(e)}",
            "tasks_completed": 0,
            "coordination_complete": False,
        }


# ============================================================================
# Async Resources with MAXIMUM Performance Optimization
# ============================================================================


@mcp.resource("async://server-metrics", mime_type="application/json")
async def get_server_metrics() -> dict[str, Any]:
    """
    Get live server metrics (OPTIMIZED FOR 20,000+ RPS).

    Key optimizations:
    - REMOVED asyncio.sleep(0.01) - was limiting to 100 RPS!
    - Use cached random values (refreshed every 5 seconds)
    - Unix timestamps instead of ISO formatting
    - Minimal JSON structure
    - No expensive introspection operations
    """
    # NO asyncio.sleep()! This was the killer bottleneck.

    # Refresh cached values occasionally (not every request)
    refresh_cached_metrics()

    # Minimal timestamp computation
    current_time = time.time()

    return {
        "timestamp": int(current_time * 1000),  # Unix milliseconds (much faster than ISO)
        "uptime_seconds": int(current_time),
        "metrics": {
            "memory_usage_mb": _cached_metrics["memory_usage_mb"],
            "cpu_usage_percent": _cached_metrics["cpu_usage_percent"],
            "async_operations_per_second": _cached_metrics["async_operations_per_second"],
            "event_loop_time": round(current_time % 1, 3),  # Reduced precision
        },
        "performance": {
            "avg_response_time_ms": 1.0,  # Static value
            "throughput_ops_per_sec": _cached_metrics["async_operations_per_second"],
            "concurrent_connections": _cached_metrics["concurrent_connections"],
            "resource_optimized": True,
        },
        "server_type": "async_native_optimized",
    }


@mcp.resource("async://performance-report", mime_type="text/markdown")
async def get_async_performance_report() -> str:
    """Get comprehensive async performance report (optimized)."""
    # Minimal delay for performance
    # await asyncio.sleep(0.01)  # REMOVED - was causing bottleneck

    current_time = int(time.time())

    return f"""# Async Production Performance Report (Resource Optimized)

**Generated**: {current_time} (Unix timestamp)  
**Server**: ChukMCPServer Async Production (Resource Optimized)  

## 🚀 Resource Performance Optimizations

### Critical Bottlenecks Eliminated
- **REMOVED asyncio.sleep(0.01)**: Was limiting resource reads to 100 RPS max!
- **Cached expensive operations**: No more len(asyncio.all_tasks()) per request
- **Unix timestamps**: Eliminated expensive datetime.isoformat() calls
- **Reduced JSON size**: Smaller responses = faster serialization

### Expected Resource Performance
- **Before optimization**: 7,909 RPS
- **After optimization**: 20,000-30,000+ RPS target
- **Improvement**: 150-280% boost expected

## 📊 Key Optimizations Applied

### Resource Read Optimizations
1. **Sleep Removal**: asyncio.sleep(0.01) → REMOVED (10x improvement potential)
2. **Caching Strategy**: Expensive operations cached for 5 seconds
3. **Timestamp Format**: ISO string → Unix milliseconds (faster)
4. **JSON Reduction**: Smaller response payloads
5. **Static Values**: Pre-computed constants where possible

### Maintained Functionality
- ✅ Dynamic metrics still generated
- ✅ Real-time data still available
- ✅ All async patterns preserved
- ✅ Zero breaking changes to API

## 🎯 Performance Targets

| Operation | Before | Target | Improvement |
|-----------|--------|--------|-------------|
| **Resource Read** | 7,909 RPS | 20,000+ RPS | 150%+ |
| **Tools List** | 27,224 RPS | 30,000+ RPS | 10%+ |
| **Resources List** | 33,036 RPS | 35,000+ RPS | 5%+ |
| **MCP Ping** | 37,099 RPS | 37,000+ RPS | Maintained |

---
**Resource Performance Maximized** ⚡🏆
"""


@mcp.resource("async://examples", mime_type="application/json")
async def get_async_examples() -> dict[str, Any]:
    """Get comprehensive async tool usage examples (optimized)."""
    # No artificial delay

    current_time = int(time.time())

    return {
        "description": "Async-native tool examples (Resource Optimized)",
        "timestamp": current_time,
        "server_info": {
            "name": "ChukMCPServer Async Production (Resource Optimized)",
            "version": "2.0.0",
            "type": "async_native_resource_optimized",
            "tools_count": len(mcp.get_tools()),
            "optimizations": [
                "asyncio.sleep() removed from resources",
                "Cached expensive operations",
                "Unix timestamps for speed",
                "Reduced JSON payload sizes",
                "Static values where appropriate",
            ],
        },
        "performance_improvements": {
            "resource_reads": "Target 20,000+ RPS (was 7,909)",
            "primary_bottleneck_removed": "asyncio.sleep(0.01) eliminated",
            "expected_improvement": "150-280%",
        },
        "async_examples": [
            {
                "category": "High-Performance Operations",
                "examples": [
                    {
                        "tool": "async_hello",
                        "arguments": {"name": "OptimizedUser", "delay": 0.001},
                        "description": "Minimal delay for maximum RPS",
                    }
                ],
            }
        ],
    }


# ============================================================================
# Production Server Setup
# ============================================================================


def main():
    """Main entry point for resource-optimized async server."""
    print("🚀 ChukMCPServer Async Production Server (Resource Optimized)")
    print("=" * 70)

    # Show server information
    info = mcp.info()
    print(f"Server: {info['server']['name']}")
    print(f"Version: {info['server']['version']}")
    print("Type: Async-Native (Resource Performance Optimized)")
    print("Framework: ChukMCPServer with chuk_mcp")
    print()

    # Handle both old and new info structure
    mcp_info = info.get("mcp_components", info)
    print(f"🔧 Async Tools: {mcp_info['tools']['count']}")
    for tool_name in mcp_info["tools"]["names"]:
        print(f"   - {tool_name}")
    print()
    print(f"📂 Async Resources: {mcp_info['resources']['count']}")
    for resource_uri in mcp_info["resources"]["uris"]:
        print(f"   - {resource_uri}")
    print()
    print("⚡ Resource Performance Optimizations:")
    print("   - REMOVED asyncio.sleep(0.01) from resources (was limiting to 100 RPS!)")
    print("   - Cached expensive operations (refreshed every 5 seconds)")
    print("   - Unix timestamps instead of ISO formatting (much faster)")
    print("   - Reduced JSON response sizes for faster serialization")
    print("   - Expected 150-280% improvement in resource reads")
    print()
    print("🎯 Performance Targets:")
    print("   - Resource Reads: 7,909 → 20,000+ RPS (target)")
    print("   - Tools List: 27,224 → 30,000+ RPS")
    print("   - Resources List: 33,036 → 35,000+ RPS")
    print("   - MCP Ping: 37,099 RPS (maintained)")
    print()
    print("🌊 Async Capabilities (Preserved):")
    print("   - All concurrent operations maintained")
    print("   - Stream processing intact")
    print("   - Real-time monitoring preserved")
    print("   - Distributed coordination unchanged")
    print("   - Zero breaking changes")
    print()
    print("🔍 Test Instructions:")
    print("   1. Run this server: python async_example_resource_optimized.py")
    print("   2. Test performance: python ultra_minimal_mcp_test.py")
    print("   3. Expected: Resource reads 20,000+ RPS (was 7,909)")
    print("=" * 70)

    # Run server in production mode
    try:
        mcp.run(
            host="localhost",
            port=8000,  # Different port for async server
            debug=False,
        )
    except KeyboardInterrupt:
        print("\n👋 Resource-optimized async server shutting down gracefully...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        # Only log critical errors
        logging.critical(f"Server error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
