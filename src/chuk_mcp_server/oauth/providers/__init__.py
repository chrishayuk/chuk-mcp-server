"""Optional OAuth providers for chuk-mcp-server.

Providers can be imported individually based on installed dependencies.
"""

__all__ = []

# Try to import Google Drive provider if dependencies are available
try:
    from .google_drive import (  # noqa: F401
        GoogleDriveOAuthClient,
        GoogleDriveOAuthProvider,
    )

    __all__.extend(["GoogleDriveOAuthProvider", "GoogleDriveOAuthClient"])
except ImportError:
    pass  # Google Drive dependencies not installed
