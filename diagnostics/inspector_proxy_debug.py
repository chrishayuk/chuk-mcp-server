#!/usr/bin/env python3
"""
Inspector Proxy Debug Tool - ULTRA DETAILED VERSION

This acts as a proxy between MCP Inspector and your real MCP server,
capturing and logging EVERY detail of the communication for debugging.
"""

import asyncio
import aiohttp
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import orjson
import time
import argparse


# Target server configuration
TARGET_SERVER = "http://localhost:8000"  # Your real MCP server base URL
TARGET_PATH = "/mcp"  # The MCP endpoint path on your server

# Session management
SESSION_ID = None


async def proxy_request(request: Request) -> Response:
    """Proxy requests between Inspector and your MCP server while logging everything"""

    try:
        # Log incoming request from Inspector with FULL details
        print("=" * 120)
        print(f"🔍 INSPECTOR → PROXY REQUEST #{int(time.time() * 1000) % 100000}")
        print("=" * 120)
        print(f"📋 Request Details:")
        print(f"  Method: {request.method}")
        print(f"  URL: {request.url}")
        print(f"  Path: {request.url.path}")
        print(f"  Query: {request.url.query}")
        print(f"  Scheme: {request.url.scheme}")
        print(f"  Host: {request.url.hostname}")
        print(f"  Port: {request.url.port}")
        print(f"  Client: {request.client}")

        print(f"\n📋 ALL Inspector Headers ({len(request.headers)} total):")
        inspector_headers = {}
        for name, value in request.headers.items():
            print(f"  {name}: {value}")
            # Filter headers to forward (exclude host, content-length, etc.)
            if name.lower() not in ["host", "content-length", "connection"]:
                inspector_headers[name] = value

        print(f"\n📋 Headers to Forward ({len(inspector_headers)} total):")
        for name, value in inspector_headers.items():
            print(f"  {name}: {value}")

        # Log body from Inspector with detailed analysis
        body = await request.body()
        print(f"\n📄 Inspector Body Analysis:")
        print(f"  Size: {len(body)} bytes")
        print(f"  Type: {type(body)}")
        print(f"  Raw bytes (first 100): {body[:100]}")

        if body:
            try:
                parsed = orjson.loads(body)
                print(f"  ✅ Valid JSON")
                print(f"  JSON Keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
                print(f"  Pretty JSON:\n{orjson.dumps(parsed, option=orjson.OPT_INDENT_2).decode()}")

                # Analyze specific fields
                if isinstance(parsed, dict):
                    print(f"  🔍 Field Analysis:")
                    for key, value in parsed.items():
                        print(f"    {key}: {type(value).__name__} = {str(value)[:100]}")

            except Exception as e:
                print(f"  ❌ JSON Parse Error: {e}")
                print(f"  Raw String: {body.decode('utf-8', errors='ignore')[:200]}")
        else:
            print("  (empty body)")

        print(f"\n⏰ Timestamp: {time.strftime('%H:%M:%S.%f')[:-3]} ({time.time()})")
        print(f"🧵 Thread ID: {id(asyncio.current_task())}")

        # Handle CORS preflight with detailed logging
        if request.method == "OPTIONS":
            print("\n✅ CORS PREFLIGHT DETECTED")
            print("  Sending CORS response...")
            cors_headers = {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400",
            }
            print(f"  CORS Headers: {cors_headers}")
            return Response("", headers=cors_headers)

        # Map Inspector paths to server paths
        server_path = map_inspector_path_to_server(request.url.path)
        print(f"\n🗺️  Path Mapping:")
        print(f"  Original: {request.url.path}")
        print(f"  Mapped: {server_path}")

        # Session ID analysis
        current_session = SESSION_ID
        print(f"\n🔑 Session Analysis:")
        print(f"  Current Global Session ID: {current_session}")
        print(f"  Session in Request Headers: {request.headers.get('mcp-session-id', 'None')}")

        # Forward request to real MCP server
        print(f"\n🚀 PROXY → SERVER REQUEST")
        print("-" * 60)

        # Construct target URL
        target_url = f"{TARGET_SERVER}{server_path}"
        if request.url.query:
            target_url += f"?{request.url.query}"

        print(f"🎯 Target Details:")
        print(f"  Server: {TARGET_SERVER}")
        print(f"  Path: {server_path}")
        print(f"  Full URL: {target_url}")

        # Add session ID to headers if we have one and this isn't the initialize request
        body_json = None
        if body:
            try:
                body_json = orjson.loads(body)
            except Exception:
                pass

        is_initialize = body_json and body_json.get("method") == "initialize"

        print(f"\n🔍 Request Analysis:")
        print(f"  Is Initialize: {is_initialize}")
        print(f"  Has Body: {bool(body)}")
        print(f"  Body Method: {body_json.get('method') if body_json else 'None'}")

        if SESSION_ID and not is_initialize:
            inspector_headers["mcp-session-id"] = SESSION_ID
            print(f"🔑 ADDED session ID to headers: {SESSION_ID}")
        elif is_initialize:
            print("🆕 Initialize request - no session ID needed yet")
        else:
            print("❓ No session ID to add")

        print(f"\n📤 Final Headers to Send ({len(inspector_headers)} total):")
        for name, value in inspector_headers.items():
            print(f"  {name}: {value}")

        # Check Accept header to determine response type
        accept_header = request.headers.get("accept", "")
        expects_sse = "text/event-stream" in accept_header

        print(f"\n🎭 Response Type Analysis:")
        print(f"  Accept Header: '{accept_header}'")
        print(f"  Expects SSE: {expects_sse}")
        print(f"  Will use: {'SSE Stream' if expects_sse else 'JSON Response'}")

        if expects_sse:
            print("📡 Using SSE proxy...")
            response = await proxy_sse_request(target_url, request.method, body, inspector_headers)
            if response is None:
                print("❌ SSE proxy returned None, creating error response")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": "SSE proxy returned None"},
                }
                return Response(
                    orjson.dumps(error_response),
                    status_code=500,
                    media_type="application/json",
                    headers={"Access-Control-Allow-Origin": "*"},
                )
            return response
        else:
            print("📄 Using JSON proxy...")
            async with aiohttp.ClientSession() as session:
                response = await proxy_json_request(session, target_url, request.method, body, inspector_headers)
                if response is None:
                    print("❌ JSON proxy returned None, creating error response")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32603, "message": "JSON proxy returned None"},
                    }
                    return Response(
                        orjson.dumps(error_response),
                        status_code=500,
                        media_type="application/json",
                        headers={"Access-Control-Allow-Origin": "*"},
                    )
                return response

    except Exception as e:
        print(f"❌ CRITICAL PROXY ERROR in proxy_request: {e}")
        import traceback

        traceback.print_exc()
        error_response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": f"Proxy error: {str(e)}"}}
        return Response(
            orjson.dumps(error_response),
            status_code=500,
            media_type="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )


def map_inspector_path_to_server(inspector_path: str) -> str:
    """Map Inspector paths to the actual server endpoints"""

    # Inspector typically sends requests to /mcp/inspector
    # but the actual MCP server expects the TARGET_PATH (usually /mcp)
    if inspector_path.startswith("/mcp/inspector"):
        return TARGET_PATH
    elif inspector_path.startswith("/mcp"):
        return TARGET_PATH
    else:
        # For any other paths, forward as-is
        return inspector_path


async def proxy_json_request(session, target_url, method, body, headers):
    """Proxy a JSON request and response with detailed logging"""

    try:
        print(f"\n🌐 JSON REQUEST DETAILS:")
        print(f"  Target URL: {target_url}")
        print(f"  Method: {method}")
        print(f"  Body size: {len(body) if body else 0} bytes")
        print(f"  Headers count: {len(headers)}")

        # Test connection first
        try:
            async with session.get(
                f"{TARGET_SERVER}{TARGET_PATH}", timeout=aiohttp.ClientTimeout(total=5)
            ) as test_response:
                print(f"✅ JSON Connection test successful (status: {test_response.status})")
        except Exception as e:
            print(f"❌ JSON Connection test failed: {e}")
            raise aiohttp.ClientError(f"Cannot connect to target server {TARGET_SERVER}{TARGET_PATH}: {e}")

        async with session.request(
            method, target_url, data=body if body else None, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            # Log server response
            print(f"\n📥 SERVER → PROXY JSON RESPONSE")
            print("-" * 50)
            print(f"Status: {response.status}")
            print(f"Reason: {response.reason}")
            print(f"Headers ({len(response.headers)} total):")

            response_headers = {"Access-Control-Allow-Origin": "*"}
            for name, value in response.headers.items():
                print(f"  {name}: {value}")
                # Forward important headers
                if name.lower() in ["content-type", "mcp-session-id", "mcp-protocol-version"]:
                    response_headers[name] = value

                # Capture session ID from server response
                if name.lower() == "mcp-session-id":
                    global SESSION_ID
                    SESSION_ID = value
                    print(f"🔑 Captured session ID from JSON response: {SESSION_ID}")

            response_body = await response.read()
            print(f"\nServer Body ({len(response_body)} bytes):")

            if response_body:
                try:
                    parsed = orjson.loads(response_body)
                    print(f"  JSON: {orjson.dumps(parsed, option=orjson.OPT_INDENT_2).decode()}")

                    # Also check for session ID in response body (some servers put it there)
                    if "result" in parsed and isinstance(parsed["result"], dict):
                        if "sessionId" in parsed["result"] or "session_id" in parsed["result"]:
                            session_from_body = parsed["result"].get("sessionId") or parsed["result"].get("session_id")
                            if session_from_body and not SESSION_ID:
                                SESSION_ID = session_from_body
                                print(f"🔑 Captured session ID from JSON response body: {SESSION_ID}")

                except Exception as e:
                    print(f"  Raw: {response_body.decode('utf-8', errors='ignore')}")
                    print(f"  Parse error: {e}")

            print(f"\n🔄 PROXY → INSPECTOR JSON RESPONSE")
            print("-" * 50)
            print(f"Forwarding status: {response.status}")
            print(f"Forwarding headers: {response_headers}")

            return Response(response_body, status_code=response.status, headers=response_headers)

    except Exception as e:
        print(f"❌ Error in proxy_json_request: {e}")
        import traceback

        traceback.print_exc()
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": f"JSON proxy error: {str(e)}"},
        }
        return Response(
            orjson.dumps(error_response),
            status_code=500,
            media_type="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )


async def proxy_sse_request(target_url, method, body, headers):
    """Proxy an SSE request and stream response with ultra-detailed logging"""

    try:

        async def sse_proxy_generator():
            try:
                print(f"\n🌐 SSE CONNECTION DETAILS:")
                print(f"  Target URL: {target_url}")
                print(f"  Method: {method}")
                print(f"  Body size: {len(body) if body else 0} bytes")
                print(f"  Headers count: {len(headers)}")

                print(f"\n📋 SSE Request Headers:")
                for name, value in headers.items():
                    print(f"    {name}: {value}")

                if body:
                    print(f"\n📦 SSE Request Body:")
                    print(f"  Raw bytes: {body[:200]}...")
                    try:
                        body_json = orjson.loads(body)
                        print(f"  Parsed JSON: {orjson.dumps(body_json, option=orjson.OPT_INDENT_2).decode()}")
                    except:
                        print(f"  Not valid JSON")

                # Test connection first
                timeout = aiohttp.ClientTimeout(total=30, connect=10)
                async with aiohttp.ClientSession(timeout=timeout) as sse_session:
                    # Test basic connectivity first
                    print(f"\n🔍 SSE CONNECTION TEST:")
                    try:
                        async with sse_session.get(
                            f"{TARGET_SERVER}{TARGET_PATH}", timeout=aiohttp.ClientTimeout(total=5)
                        ) as test_response:
                            print(f"  ✅ Connection test successful")
                            print(f"  Test status: {test_response.status}")
                            print(f"  Test headers: {dict(test_response.headers)}")
                    except Exception as e:
                        print(f"  ❌ Connection test failed: {e}")
                        error_event = {
                            "type": "connection_error",
                            "error": f"Cannot connect to target server {TARGET_SERVER}{TARGET_PATH}: {str(e)}",
                            "timestamp": time.time(),
                        }
                        yield f"data: {orjson.dumps(error_event).decode()}\n\n"
                        return

                    print(f"\n🚀 MAKING ACTUAL SSE REQUEST:")
                    print(f"  URL: {target_url}")
                    print(f"  Method: {method}")
                    print(f"  Timeout: {timeout}")

                    async with sse_session.request(
                        method, target_url, data=body if body else None, headers=headers
                    ) as response:
                        print(f"\n📥 SERVER SSE RESPONSE RECEIVED:")
                        print(f"  Status: {response.status}")
                        print(f"  Reason: {response.reason}")
                        print(f"  Version: {response.version}")
                        print(f"  Content-Type: {response.headers.get('content-type')}")
                        print(f"  Content-Length: {response.headers.get('content-length', 'Not specified')}")
                        print(f"  Transfer-Encoding: {response.headers.get('transfer-encoding', 'Not specified')}")

                        print(f"\n📋 ALL SERVER RESPONSE HEADERS ({len(response.headers)} total):")
                        for name, value in response.headers.items():
                            print(f"    {name}: {value}")

                        # Capture session ID from response headers
                        session_header_names = ["mcp-session-id", "Mcp-Session-Id", "MCP-Session-Id"]
                        captured_session = None
                        for header_name in session_header_names:
                            if header_name in response.headers:
                                captured_session = response.headers[header_name]
                                print(f"  🔑 Found session ID in header '{header_name}': {captured_session}")
                                break

                        if captured_session:
                            global SESSION_ID
                            SESSION_ID = captured_session
                            print(f"🔑 UPDATED global session ID: {SESSION_ID}")
                        else:
                            print(f"⚠️  No session ID found in response headers")

                        if response.status != 200:
                            error_data = await response.read()
                            print(f"❌ Server returned non-200 status")
                            print(f"  Status: {response.status}")
                            print(f"  Error body: {error_data.decode()}")
                            error_event = {
                                "type": "error",
                                "error": f"Server returned {response.status}",
                                "body": error_data.decode(),
                            }
                            yield f"data: {orjson.dumps(error_event).decode()}\n\n"
                            return

                        print(f"\n🌊 STREAMING SERVER RESPONSE TO INSPECTOR:")
                        print(f"  Starting to read chunks...")

                        # Read the response line by line for SSE
                        event_count = 0
                        empty_line_count = 0
                        buffer = ""
                        total_bytes = 0

                        async for chunk in response.content.iter_chunked(1024):
                            if chunk:
                                chunk_str = chunk.decode("utf-8", errors="ignore")
                                total_bytes += len(chunk)
                                buffer += chunk_str

                                print(f"📦 Received chunk: {len(chunk)} bytes (total: {total_bytes})")
                                print(f"  Chunk content: {repr(chunk_str[:200])}")
                                print(f"  Buffer size: {len(buffer)}")

                                # Process complete lines
                                while "\n" in buffer:
                                    line, buffer = buffer.split("\n", 1)

                                    print(f"📡 Processing line: {repr(line)}")

                                    if line.strip():  # Non-empty lines
                                        event_count += 1
                                        print(f"📡 SSE Event #{event_count}: {repr(line)}")

                                        # Check for session ID in SSE data
                                        if line.startswith("data: "):
                                            try:
                                                data_json = orjson.loads(line[6:])  # Remove 'data: ' prefix
                                                print(
                                                    f"  📊 SSE Data JSON: {orjson.dumps(data_json, option=orjson.OPT_INDENT_2).decode()}"
                                                )

                                                if "result" in data_json and isinstance(data_json["result"], dict):
                                                    if (
                                                        "sessionId" in data_json["result"]
                                                        or "session_id" in data_json["result"]
                                                    ):
                                                        session_from_data = data_json["result"].get(
                                                            "sessionId"
                                                        ) or data_json["result"].get("session_id")
                                                        if session_from_data and not SESSION_ID:
                                                            SESSION_ID = session_from_data
                                                            print(f"🔑 Captured session ID from SSE data: {SESSION_ID}")
                                            except Exception as parse_error:
                                                print(f"  ⚠️  Could not parse SSE data as JSON: {parse_error}")

                                        yield f"{line}\n"
                                    else:
                                        # Empty line - part of SSE format
                                        empty_line_count += 1
                                        print(f"📡 SSE Empty line #{empty_line_count} (event separator)")
                                        yield "\n"

                        # Send any remaining buffer
                        if buffer.strip():
                            print(f"📡 SSE Final buffer: {repr(buffer)}")
                            yield buffer

                        print(f"\n✅ SSE STREAMING COMPLETE:")
                        print(f"  Total non-empty events: {event_count}")
                        print(f"  Total empty lines: {empty_line_count}")
                        print(f"  Total events: {event_count + empty_line_count}")
                        print(f"  Total bytes: {total_bytes}")
                        print(f"  Final session ID: {SESSION_ID}")

            except aiohttp.ClientError as e:
                print(f"❌ SSE Client connection error: {e}")
                error_event = {"type": "connection_error", "error": str(e), "timestamp": time.time()}
                yield f"data: {orjson.dumps(error_event).decode()}\n\n"
            except Exception as e:
                print(f"❌ SSE proxy error: {e}")
                import traceback

                traceback.print_exc()
                error_event = {"type": "error", "error": str(e), "timestamp": time.time()}
                yield f"data: {orjson.dumps(error_event).decode()}\n\n"

        # Build response headers with detailed logging
        response_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }

        # Forward session ID if we captured one
        if SESSION_ID:
            response_headers["Mcp-Session-Id"] = SESSION_ID
            print(f"🔑 Adding session ID to response headers: {SESSION_ID}")

        print(f"\n📤 CREATING SSE RESPONSE TO INSPECTOR:")
        print(f"  Response headers: {response_headers}")

        return StreamingResponse(sse_proxy_generator(), media_type="text/event-stream", headers=response_headers)

    except Exception as e:
        print(f"❌ Critical error in proxy_sse_request: {e}")
        import traceback

        traceback.print_exc()
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": f"SSE proxy error: {str(e)}"},
        }
        return Response(
            orjson.dumps(error_response),
            status_code=500,
            media_type="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )


def create_proxy_app():
    """Create proxy app with CORS middleware"""

    middleware = [
        Middleware(
            CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
        )
    ]

    routes = [
        # Catch all routes and proxy them
        Route("/{path:path}", proxy_request, methods=["GET", "POST", "OPTIONS", "PUT", "DELETE", "PATCH"])
    ]

    return Starlette(routes=routes, middleware=middleware)


async def test_target_server(target_server: str, target_path: str):
    """Test if the target server is reachable"""
    full_url = f"{target_server}{target_path}"
    print(f"🔍 Testing connection to target server: {full_url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"✅ Target server is reachable (status: {response.status})")
                return True
    except Exception as e:
        print(f"❌ Cannot reach target server: {e}")
        print(f"💡 Make sure your MCP server is running on {full_url}")
        return False


def main():
    parser = argparse.ArgumentParser(description="MCP Inspector Proxy Debug Tool - ULTRA DETAILED")
    parser.add_argument("--proxy-port", type=int, default=8011, help="Port for the proxy server (default: 8011)")
    parser.add_argument(
        "--server-port", type=int, default=8000, help="Port where your MCP server is running (default: 8000)"
    )
    parser.add_argument(
        "--server-host", default="localhost", help="Host where your MCP server is running (default: localhost)"
    )
    parser.add_argument("--server-path", default="/mcp", help="Path to MCP endpoint on your server (default: /mcp)")

    args = parser.parse_args()

    global TARGET_SERVER, TARGET_PATH
    TARGET_SERVER = f"http://{args.server_host}:{args.server_port}"
    TARGET_PATH = args.server_path

    print("🔬 MCP Inspector Proxy Debug Tool - ULTRA DETAILED")
    print("=" * 80)
    print("This proxy captures EVERY detail of Inspector ↔ Server communication")
    print()
    print("Configuration:")
    print(f"  • Your MCP server: {TARGET_SERVER}{TARGET_PATH}")
    print(f"  • Proxy server: http://localhost:{args.proxy_port}")
    print(f"  • Inspector URL: http://localhost:{args.proxy_port}/mcp/inspector")
    print()
    print("Enhanced Features:")
    print("  • Full request/response analysis")
    print("  • Detailed SSE event tracking")
    print("  • Session ID flow monitoring")
    print("  • Chunk-level stream analysis")
    print("  • Complete header inspection")
    print()
    print("Setup Steps:")
    print(f"1. Make sure your MCP server is running on: {TARGET_SERVER}{TARGET_PATH}")
    print(f"2. This proxy will run on: http://localhost:{args.proxy_port}")
    print(f"3. In MCP Inspector, connect to: http://localhost:{args.proxy_port}/mcp/inspector")
    print("4. Watch the ultra-detailed logs below")
    print()

    # Test target server connectivity
    async def test_and_start():
        server_reachable = await test_target_server(TARGET_SERVER, TARGET_PATH)
        if not server_reachable:
            print()
            print("⚠️  WARNING: Target server is not reachable!")
            print("   The proxy will still start, but connections will fail.")
            print(f"   Make sure to start your MCP server on {TARGET_SERVER}{TARGET_PATH} first.")

        print()
        print("Starting ultra-detailed proxy server...")
        print("=" * 80)

    # Run the test
    asyncio.run(test_and_start())

    app = create_proxy_app()

    try:
        import uvicorn

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=args.proxy_port,
            log_level="warning",  # Reduce uvicorn noise
        )
    except KeyboardInterrupt:
        print("\n👋 Proxy server stopped")


if __name__ == "__main__":
    main()
