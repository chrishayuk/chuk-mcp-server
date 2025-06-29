#!/usr/bin/env python3
"""
examples/streaming_mcp_example.py - Streaming MCP Server Example

Demonstrates the StreamableMCP server with HTTP streaming capabilities
using chuk-mcp protocol + our streaming extensions.
"""

import asyncio
import time
import random
from typing import AsyncGenerator

from fast_mcp_server.endpoints.mcp import tool, resource


# ============================================================================
# Streaming Tools Examples
# ============================================================================

@tool("count_stream", "Stream counting numbers", streaming=True)
async def stream_counter(count: int = 10, delay: float = 0.5) -> AsyncGenerator[dict, None]:
    """
    Stream a sequence of counting numbers with metadata
    
    Args:
        count: Number of items to stream
        delay: Delay between items in seconds
    """
    for i in range(count):
        yield {
            "number": i + 1,
            "total": count,
            "progress": round((i + 1) / count * 100, 1),
            "timestamp": time.time()
        }
        await asyncio.sleep(delay)


@tool("live_data", "Stream live sensor data", streaming=True)
async def stream_live_data(duration: int = 30, interval: float = 1.0) -> AsyncGenerator[dict, None]:
    """
    Stream simulated live sensor data
    
    Args:
        duration: How long to stream data (seconds)
        interval: Time between readings (seconds)
    """
    start_time = time.time()
    reading_count = 0
    
    while time.time() - start_time < duration:
        reading_count += 1
        
        # Simulate sensor readings
        yield {
            "reading_id": reading_count,
            "temperature": round(random.uniform(20.0, 25.0), 2),
            "humidity": round(random.uniform(40.0, 60.0), 2),
            "pressure": round(random.uniform(1010.0, 1020.0), 2),
            "timestamp": time.time(),
            "elapsed": round(time.time() - start_time, 2)
        }
        
        await asyncio.sleep(interval)


@tool("process_stream", "Process data with streaming output", streaming=True)
async def stream_processing(items: list, process_delay: float = 0.2) -> AsyncGenerator[dict, None]:
    """
    Process a list of items with streaming progress updates
    
    Args:
        items: List of items to process
        process_delay: Processing delay per item
    """
    total_items = len(items)
    
    for i, item in enumerate(items):
        # Simulate processing
        await asyncio.sleep(process_delay)
        
        # Simulate some processing result
        processed_result = {
            "original": item,
            "processed": str(item).upper() if isinstance(item, str) else item * 2,
            "length": len(str(item))
        }
        
        yield {
            "item_index": i,
            "total_items": total_items,
            "progress_percent": round((i + 1) / total_items * 100, 1),
            "result": processed_result,
            "processing_time": process_delay,
            "timestamp": time.time()
        }


@tool("log_tail", "Stream log entries", streaming=True)
async def stream_logs(lines: int = 50, interval: float = 0.1) -> AsyncGenerator[str, None]:
    """
    Stream simulated log entries
    
    Args:
        lines: Number of log lines to generate
        interval: Time between log entries
    """
    log_levels = ["INFO", "DEBUG", "WARNING", "ERROR"]
    services = ["api", "database", "auth", "worker", "cache"]
    messages = [
        "Request processed successfully",
        "Connection established",
        "Cache hit",
        "Cache miss",
        "Rate limit applied",
        "Authentication successful",
        "Validation completed",
        "Database query executed",
        "Background task started",
        "Cleanup completed"
    ]
    
    for i in range(lines):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        level = random.choice(log_levels)
        service = random.choice(services)
        message = random.choice(messages)
        
        log_entry = f"[{timestamp}] {level:7} {service:8} | {message} (entry {i+1}/{lines})"
        
        yield log_entry
        await asyncio.sleep(interval)


# ============================================================================
# Streaming Resources Examples
# ============================================================================

@resource("stream://live-stats", "Live Server Statistics", streaming=True)
async def stream_server_stats() -> AsyncGenerator[dict, None]:
    """Stream live server statistics every second"""
    from ..models import get_state
    
    while True:
        state = get_state()
        
        yield {
            "server": {
                "uptime": round(state.metrics.uptime(), 2),
                "total_requests": state.metrics.total_requests,
                "requests_per_second": round(state.metrics.rps(), 2),
                "active_sessions": len(state.sessions)
            },
            "mcp": {
                "tool_calls": state.metrics.tool_calls,
                "resource_reads": state.metrics.resource_reads,
                "errors": state.metrics.errors
            },
            "timestamp": time.time()
        }
        
        await asyncio.sleep(1.0)


@resource("stream://system-monitor", "System Resource Monitor", streaming=True)
async def stream_system_monitor() -> AsyncGenerator[dict, None]:
    """Stream system resource usage"""
    try:
        import psutil
        
        while True:
            yield {
                "cpu": {
                    "percent": psutil.cpu_percent(interval=0.1),
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                    "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                    "percent_used": psutil.virtual_memory().percent
                },
                "disk": {
                    "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                    "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                    "percent_used": round((psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100, 1)
                },
                "timestamp": time.time()
            }
            
            await asyncio.sleep(2.0)
            
    except ImportError:
        # Fallback if psutil not available
        while True:
            yield {
                "message": "psutil not available for system monitoring",
                "simulated_cpu": round(random.uniform(10, 80), 1),
                "timestamp": time.time()
            }
            await asyncio.sleep(2.0)


@resource("stream://events", "Event Stream", streaming=True)
async def stream_events() -> AsyncGenerator[dict, None]:
    """Stream simulated events"""
    event_types = ["user_login", "api_call", "file_upload", "data_sync", "error_occurred"]
    
    event_id = 1
    
    while True:
        yield {
            "event_id": event_id,
            "event_type": random.choice(event_types),
            "user_id": f"user_{random.randint(1, 100)}",
            "metadata": {
                "ip": f"192.168.1.{random.randint(1, 254)}",
                "success": random.choice([True, True, True, False])  # 75% success rate
            },
            "timestamp": time.time()
        }
        
        event_id += 1
        await asyncio.sleep(random.uniform(0.5, 2.0))


# ============================================================================
# Non-Streaming Tools for Comparison
# ============================================================================

@tool("quick_calc", "Quick calculation")
def quick_calculation(expression: str) -> dict:
    """
    Perform a quick calculation
    
    Args:
        expression: Mathematical expression to evaluate
    """
    try:
        # Safe evaluation of simple math expressions
        allowed_chars = set('0123456789+-*/.() ')
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return {
                "expression": expression,
                "result": result,
                "type": type(result).__name__,
                "timestamp": time.time()
            }
        else:
            return {
                "error": "Invalid characters in expression",
                "expression": expression,
                "allowed_chars": "0-9, +, -, *, /, ., (, ), space"
            }
    except Exception as e:
        return {
            "error": str(e),
            "expression": expression,
            "timestamp": time.time()
        }


@tool("text_analysis", "Analyze text content")
def analyze_text(text: str) -> dict:
    """
    Analyze text and return statistics
    
    Args:
        text: Text to analyze
    """
    import re
    
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    
    return {
        "text_length": len(text),
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "average_word_length": round(sum(len(word) for word in words) / len(words), 2) if words else 0,
        "unique_words": len(set(word.lower() for word in words)),
        "character_distribution": {
            "letters": sum(1 for c in text if c.isalpha()),
            "digits": sum(1 for c in text if c.isdigit()),
            "spaces": sum(1 for c in text if c.isspace()),
            "punctuation": sum(1 for c in text if not c.isalnum() and not c.isspace())
        },
        "timestamp": time.time()
    }


# ============================================================================
# Usage Examples and Documentation
# ============================================================================

def print_streaming_examples():
    """Print examples of how to use the streaming capabilities"""
    
    print("""
🌊 StreamableMCP Server - Streaming Examples

📡 MCP PROTOCOL WITH STREAMING:

    # Regular MCP request (JSON-RPC)
    POST /mcp
    Content-Type: application/json
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "count_stream", "arguments": {"count": 5, "delay": 1.0}}
    }

    # Streaming MCP request (Server-Sent Events)
    POST /mcp
    Content-Type: application/json
    Accept: text/event-stream
    {
        "jsonrpc": "2.0", 
        "id": 1,
        "method": "tools/call",
        "params": {"name": "count_stream", "arguments": {"count": 5, "delay": 1.0}}
    }

🧪 TESTING STREAMING TOOLS:

    # Stream counting numbers
    curl -X POST http://localhost:8000/mcp \\
      -H "Content-Type: application/json" \\
      -H "Accept: text/event-stream" \\
      -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"count_stream","arguments":{"count":5}}}'

    # Stream live data
    curl -X POST http://localhost:8000/mcp \\
      -H "Content-Type: application/json" \\
      -H "Accept: text/event-stream" \\
      -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"live_data","arguments":{"duration":10}}}'

📄 TESTING STREAMING RESOURCES:

    # Stream live server stats
    curl -X POST http://localhost:8000/mcp \\
      -H "Content-Type: application/json" \\
      -H "Accept: text/event-stream" \\
      -d '{"jsonrpc":"2.0","id":1,"method":"resources/read","params":{"uri":"stream://live-stats"}}'

🎯 STREAMING FEATURES:

    ✅ Real-time data streaming
    ✅ Progress updates for long-running operations
    ✅ Live system monitoring
    ✅ Event streams
    ✅ Log tailing
    ✅ HTTP Server-Sent Events (SSE) transport
    ✅ Backward compatible with regular MCP protocol
    ✅ chuk-mcp protocol compliance + streaming extensions

⚡ PERFORMANCE:

    • Maintains 20,000+ RPS for regular requests
    • Efficient streaming with minimal overhead
    • Async generators for memory efficiency
    • HTTP/2 compatible Server-Sent Events
    """)


if __name__ == "__main__":
    print_streaming_examples()