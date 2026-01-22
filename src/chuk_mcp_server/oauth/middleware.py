"""
Generic OAuth middleware for ChukMCPServer.

Adds OAuth endpoints to any MCP server:
- OAuth Authorization Server discovery (/.well-known/oauth-authorization-server) - RFC 8414
- OAuth Protected Resource metadata (/.well-known/oauth-protected-resource) - RFC 9728
- Authorization endpoint (/oauth/authorize)
- Token endpoint (/oauth/token)
- External provider callback (/oauth/callback)
- Client registration (/oauth/register)

Works with any OAuth provider that implements BaseOAuthProvider.
"""

import logging
from typing import Any, Literal, cast
from urllib.parse import urlencode

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from .base_provider import BaseOAuthProvider
from .models import AuthorizationParams

logger = logging.getLogger(__name__)


class OAuthMiddleware:
    """
    Generic OAuth middleware for ChukMCPServer.

    Implements the MCP OAuth specification with pluggable provider support.
    """

    def __init__(
        self,
        mcp_server: Any,  # ChukMCPServer instance
        provider: BaseOAuthProvider,
        oauth_server_url: str = "http://localhost:8000",
        callback_path: str = "/oauth/callback",
        scopes_supported: list[str] | None = None,
        service_documentation: str | None = None,
        provider_name: str = "OAuth Provider",
    ):
        """
        Initialize generic OAuth middleware.

        Args:
            mcp_server: ChukMCPServer instance
            provider: OAuth provider instance (must implement BaseOAuthProvider)
            oauth_server_url: This OAuth server's base URL
            callback_path: Path for external provider callback (default: /oauth/callback)
            scopes_supported: List of supported scopes for metadata
            service_documentation: URL to service documentation
            provider_name: Human-readable name of the OAuth provider (e.g., "LinkedIn", "GitHub")
        """
        self.mcp = mcp_server
        self.provider = provider
        self.oauth_server_url = oauth_server_url
        self.callback_path = callback_path
        self.scopes_supported = scopes_supported or []
        self.service_documentation = service_documentation
        self.provider_name = provider_name

        # Register OAuth endpoints
        self._register_endpoints()

    def _register_endpoints(self) -> None:
        """Register OAuth endpoints with the MCP server."""

        # OAuth server metadata (RFC 8414)
        @self.mcp.endpoint("/.well-known/oauth-authorization-server", methods=["GET"])  # type: ignore[untyped-decorator]
        async def oauth_metadata(request: Request) -> JSONResponse:
            """OAuth Authorization Server Metadata endpoint."""
            return await self._metadata_endpoint(request)

        # Protected Resource Metadata (RFC 9728)
        @self.mcp.endpoint("/.well-known/oauth-protected-resource", methods=["GET"])  # type: ignore[untyped-decorator]
        async def protected_resource_metadata(request: Request) -> JSONResponse:
            """OAuth Protected Resource Metadata endpoint."""
            return await self._protected_resource_endpoint(request)

        # OAuth authorize endpoint
        @self.mcp.endpoint("/oauth/authorize", methods=["GET"])  # type: ignore[untyped-decorator]
        async def oauth_authorize(request: Request) -> Any:
            """OAuth authorization endpoint."""
            return await self._authorize_endpoint(request)

        # OAuth token endpoint
        @self.mcp.endpoint("/oauth/token", methods=["POST"])  # type: ignore[untyped-decorator]
        async def oauth_token(request: Request) -> JSONResponse:
            """OAuth token endpoint."""
            return await self._token_endpoint(request)

        # Client registration endpoint (RFC 7591)
        @self.mcp.endpoint("/oauth/register", methods=["POST"])  # type: ignore[untyped-decorator]
        async def oauth_register(request: Request) -> JSONResponse:
            """Dynamic client registration endpoint."""
            return await self._register_endpoint(request)

        # External OAuth provider callback
        @self.mcp.endpoint(self.callback_path, methods=["GET"])  # type: ignore[untyped-decorator]
        async def external_callback(request: Request) -> Any:
            """External OAuth provider callback endpoint."""
            return await self._external_callback_endpoint(request)

    # ============================================================================
    # OAuth Endpoints
    # ============================================================================

    async def _metadata_endpoint(self, request: Request) -> JSONResponse:
        """
        OAuth Authorization Server Metadata endpoint (RFC 8414).

        Returns server metadata for OAuth discovery.
        """
        metadata = {
            "issuer": self.oauth_server_url,
            "authorization_endpoint": f"{self.oauth_server_url}/oauth/authorize",
            "token_endpoint": f"{self.oauth_server_url}/oauth/token",
            "registration_endpoint": f"{self.oauth_server_url}/oauth/register",
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "response_types_supported": ["code"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_post",
                "client_secret_basic",
                "none",
            ],
            "code_challenge_methods_supported": ["S256", "plain"],
        }

        # Add optional metadata
        if self.scopes_supported:
            metadata["scopes_supported"] = self.scopes_supported

        if self.service_documentation:
            metadata["service_documentation"] = self.service_documentation

        return JSONResponse(metadata)

    async def _protected_resource_endpoint(self, request: Request) -> JSONResponse:
        """
        OAuth Protected Resource Metadata endpoint (RFC 9728).

        Returns information about this protected resource, including
        which authorization servers can issue tokens for it.
        """
        metadata = {
            "resource": self.oauth_server_url,
            "authorization_servers": [self.oauth_server_url],
            "bearer_methods_supported": ["header"],
            "resource_signing_alg_values_supported": ["RS256"],
        }

        # Add optional metadata
        if self.scopes_supported:
            metadata["scopes_supported"] = self.scopes_supported

        if self.service_documentation:
            metadata["resource_documentation"] = self.service_documentation

        return JSONResponse(metadata, headers={"Access-Control-Allow-Origin": "*"})

    async def _authorize_endpoint(self, request: Request) -> Any:
        """
        OAuth authorization endpoint.

        Handles authorization requests from MCP clients.
        May redirect to external provider for authentication.
        """
        try:
            # Parse authorization parameters
            params = dict(request.query_params)

            # Create AuthorizationParams object
            code_challenge_method_value = params.get("code_challenge_method")
            code_challenge_method: Literal["S256", "plain"] | None = None
            if code_challenge_method_value in ("S256", "plain"):
                code_challenge_method = cast(Literal["S256", "plain"], code_challenge_method_value)

            auth_params = AuthorizationParams(
                response_type=params.get("response_type", "code"),
                client_id=params["client_id"],
                redirect_uri=params["redirect_uri"],
                scope=params.get("scope"),
                state=params.get("state"),
                code_challenge=params.get("code_challenge"),
                code_challenge_method=code_challenge_method,
            )

            # Process authorization request
            result = await self.provider.authorize(auth_params)

            # Check if we need external provider authorization
            if result.get("requires_external_authorization"):
                # Redirect to external provider
                return RedirectResponse(result["authorization_url"])

            # We have authorization code, redirect back to client
            redirect_params = {
                "code": result["code"],
            }
            if result.get("state"):
                redirect_params["state"] = result["state"]

            redirect_url = f"{auth_params.redirect_uri}?{urlencode(redirect_params)}"
            return RedirectResponse(redirect_url)

        except Exception as e:
            # Return error response
            error_params = {
                "error": "server_error",
                "error_description": str(e),
            }
            if params.get("state"):
                error_params["state"] = params["state"]

            error_url = f"{params['redirect_uri']}?{urlencode(error_params)}"
            return RedirectResponse(error_url)

    async def _token_endpoint(self, request: Request) -> JSONResponse:
        """
        OAuth token endpoint.

        Exchanges authorization code for access token.
        Also handles refresh token requests.
        """
        try:
            # Parse form data
            form_data = await request.form()

            # Helper to extract string values from form
            def get_form_str(key: str) -> str | None:
                val = form_data.get(key)
                return str(val) if val is not None else None

            grant_type = get_form_str("grant_type")

            logger.debug(f"🔐 Token exchange request - grant_type: {grant_type}")
            logger.debug(f"🔐 Token exchange - client_id: {get_form_str('client_id')}")
            code_val = get_form_str("code")
            logger.debug(f"🔐 Token exchange - code: {code_val[:20]}..." if code_val else "no code")
            logger.debug(f"🔐 Token exchange - redirect_uri: {get_form_str('redirect_uri')}")
            logger.debug(f"🔐 Token exchange - code_verifier present: {bool(get_form_str('code_verifier'))}")

            if grant_type == "authorization_code":
                # Exchange authorization code for token
                code = get_form_str("code")
                client_id = get_form_str("client_id")
                redirect_uri = get_form_str("redirect_uri")
                code_verifier = get_form_str("code_verifier")

                if not code or not client_id or not redirect_uri:
                    return JSONResponse(
                        {"error": "invalid_request", "error_description": "Missing required parameters"},
                        status_code=400,
                    )

                token = await self.provider.exchange_authorization_code(
                    code=code,
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    code_verifier=code_verifier,
                )
            elif grant_type == "refresh_token":
                # Refresh access token
                refresh_token = get_form_str("refresh_token")
                client_id = get_form_str("client_id")
                scope = get_form_str("scope")

                if not refresh_token or not client_id:
                    return JSONResponse(
                        {"error": "invalid_request", "error_description": "Missing required parameters"},
                        status_code=400,
                    )

                token = await self.provider.exchange_refresh_token(
                    refresh_token=refresh_token,
                    client_id=client_id,
                    scope=scope,
                )
            else:
                return JSONResponse(
                    {
                        "error": "unsupported_grant_type",
                        "error_description": f"Grant type {grant_type} not supported",
                    },
                    status_code=400,
                )

            # Return token response
            return JSONResponse(
                {
                    "access_token": str(token.access_token),
                    "token_type": token.token_type,
                    "expires_in": token.expires_in,
                    "refresh_token": str(token.refresh_token) if token.refresh_token else None,
                    "scope": token.scope,
                }
            )

        except Exception as e:
            logger.error(f"❌ Token exchange failed: {type(e).__name__}: {str(e)}")
            import traceback

            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return JSONResponse(
                {
                    "error": "invalid_request",
                    "error_description": str(e),
                },
                status_code=400,
            )

    async def _register_endpoint(self, request: Request) -> JSONResponse:
        """
        Dynamic client registration endpoint (RFC 7591).

        Allows MCP clients to register dynamically.
        """
        try:
            # Parse registration request
            body = await request.json()

            # Register client
            client_info = await self.provider.register_client(body)

            return JSONResponse(
                {
                    "client_id": client_info.client_id,
                    "client_secret": client_info.client_secret,
                    "client_name": client_info.client_name,
                    "redirect_uris": client_info.redirect_uris,
                },
                status_code=201,
            )

        except Exception as e:
            return JSONResponse(
                {
                    "error": "invalid_client_metadata",
                    "error_description": str(e),
                },
                status_code=400,
            )

    async def _external_callback_endpoint(self, request: Request) -> Any:
        """
        External OAuth provider callback endpoint.

        Handles the callback from external provider after user authorization.
        Completes the external OAuth flow and redirects back to MCP client.
        """
        try:
            # Get authorization code and state
            code = request.query_params.get("code")
            state = request.query_params.get("state")
            error = request.query_params.get("error")

            if error:
                # External authorization failed
                return HTMLResponse(
                    f"""
                    <html>
                        <head><title>Authorization Failed</title></head>
                        <body>
                            <h1>{self.provider_name} Authorization Failed</h1>
                            <p>Error: {error}</p>
                            <p>Description: {request.query_params.get("error_description", "Unknown error")}</p>
                        </body>
                    </html>
                    """,
                    status_code=400,
                )

            if not code or not state:
                return HTMLResponse(
                    """
                    <html>
                        <head><title>Invalid Request</title></head>
                        <body>
                            <h1>Invalid OAuth Callback</h1>
                            <p>Missing required parameters</p>
                        </body>
                    </html>
                    """,
                    status_code=400,
                )

            # Handle external provider callback
            # Provider should implement handle_external_callback method
            if not hasattr(self.provider, "handle_external_callback"):
                raise NotImplementedError(
                    f"Provider {type(self.provider).__name__} must implement handle_external_callback method"
                )

            result = await self.provider.handle_external_callback(code, state)

            # Redirect back to MCP client with authorization code
            redirect_params = {
                "code": result["code"],
            }
            if result.get("state"):
                redirect_params["state"] = result["state"]

            redirect_url = f"{result['redirect_uri']}?{urlencode(redirect_params)}"

            # Return success page with auto-redirect
            return HTMLResponse(
                f"""
                <html>
                    <head>
                        <title>Authorization Successful</title>
                        <meta http-equiv="refresh" content="3;url={redirect_url}">
                    </head>
                    <body>
                        <h1>{self.provider_name} Authorization Successful!</h1>
                        <p>Your {self.provider_name} account has been linked.</p>
                        <p>Redirecting back to the application...</p>
                        <p>If not redirected, <a href="{redirect_url}">click here</a>.</p>
                    </body>
                </html>
                """
            )

        except Exception as e:
            return HTMLResponse(
                f"""
                <html>
                    <head><title>Error</title></head>
                    <body>
                        <h1>Authorization Error</h1>
                        <p>{str(e)}</p>
                    </body>
                </html>
                """,
                status_code=500,
            )
