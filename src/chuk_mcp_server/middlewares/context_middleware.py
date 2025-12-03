"""
Middleware for storing HTTP Request into Context
"""

from starlette.types import ASGIApp, Receive, Scope, Send

from ..context import set_http_request


class ContextMiddleware:
    """Middleware that captures the HTTP request in the context."""

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize the middleware.

        Args:
            app: The ASGI application
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process the ASGI request.

        Args:
            scope: The ASGI connection scope
            receive: The ASGI receive function
            send: The ASGI send function
        """
        # Store the request scope in the context
        set_http_request(scope)

        # Continue processing the request
        await self.app(scope, receive, send)
