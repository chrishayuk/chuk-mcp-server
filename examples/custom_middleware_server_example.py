#!/usr/bin/env python3
"""
HTTP Request Context Server Example

This example demonstrates:
1. How ContextMiddleware captures all request modifications
2. Creating a custom auth middleware that adds data to the request scope
3. Accessing the complete request data from MCP tools via context
"""

from chuk_mcp_server import run, tool
from chuk_mcp_server.context import get_http_request
from chuk_mcp_server.endpoint_registry import register_middleware


# Define custom auth middleware that adds data to the request
class CustomAuthMiddleware:
    """
    Middleware that authenticates based on Custom-Header-Auth header.

    This middleware runs before ContextMiddleware and modifies the scope.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            # Skip non-HTTP requests
            return await self.app(scope, receive, send)

        # Default auth state
        authenticated = False

        # Check for the Custom-Header-Auth header
        authenticated = dict(scope.get("headers", [])).get(b"custom-header-auth", "") == b"True"

        # Modify the scope to include auth info that will be captured by ContextMiddleware
        scope["authenticated"] = authenticated
        scope["auth_level"] = "admin" if authenticated else "guest"

        # Log authentication attempt
        client = scope.get("client", ("unknown", 0))
        print(f"Auth check: {'✓' if authenticated else '✗'} Client {client[0]}")

        # Continue to next middleware (which will eventually be ContextMiddleware)
        return await self.app(scope, receive, send)


# Register our custom auth middleware
print("Registering CustomAuthMiddleware...")
register_middleware(CustomAuthMiddleware, priority=50, name="custom_auth")


@tool
def get_auth_info():
    """
    Get authentication information from the HTTP request context.

    This tool demonstrates accessing authentication data that was
    added to the request by CustomAuthMiddleware and then captured
    by ContextMiddleware.
    """
    request = get_http_request()

    if not request:
        return {"error": "No HTTP request in context", "hint": "This tool is designed to be used with HTTP requests"}

    # Access the auth data added by our middleware
    return {
        "authenticated": request.get("authenticated", False),
        "auth_level": request.get("auth_level", "unknown"),
        "client": request.get("client", ("unknown", 0))[0],
        "path": request.get("path", "unknown"),
    }


@tool
def protected_operation():
    """
    A protected operation that requires authentication.

    This tool demonstrates checking for authentication before
    performing an operation.
    """
    request = get_http_request()

    if not request:
        return {"error": "No HTTP request in context", "hint": "This tool is designed to be used with HTTP requests"}

    # Check authentication that was added by our middleware
    # and captured by ContextMiddleware
    authenticated = request.get("authenticated", False)
    if not authenticated:
        return {"error": "Authentication required", "hint": "Send the Custom-Header-Auth: true header"}

    # If authenticated, perform the operation
    return {
        "success": True,
        "operation": "protected_operation",
        "result": "Secret data accessed successfully",
        "user_level": request.get("auth_level", "unknown"),
    }


def main():
    """Run the server with our custom authentication middleware."""
    print("=" * 60)
    print("HTTP REQUEST CONTEXT SERVER EXAMPLE")
    print("=" * 60)
    print("\nThis example demonstrates:")
    print("1. CustomAuthMiddleware adds auth data to the request scope")
    print("2. MCP tools can access the complete request data via context")
    print("\nAvailable tools:")
    print("- get_auth_info: Get authentication information from the request context")
    print("- protected_operation: A protected operation requiring authentication")
    print("\n" + "=" * 60)

    # Run the server
    run(
        transport="http",
        host="localhost",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
