#!/usr/bin/env python3
# src/chuk_mcp_server/config/network_detector.py
"""
Network configuration detection (host and port).
"""

import socket
from typing import Any

from .base import ConfigDetector


class NetworkDetector(ConfigDetector):
    """Detects optimal network configuration (host and port)."""

    PLATFORM_HOSTS = {
        "VERCEL": "0.0.0.0",
        "RAILWAY_ENVIRONMENT": "0.0.0.0",
        "RENDER": "0.0.0.0",
        "FLY_APP_NAME": "0.0.0.0",
        "HEROKU_APP_NAME": "0.0.0.0",
    }

    PLATFORM_PORTS = {
        "VERCEL": 3000,
        "NETLIFY": 8888,
        "RAILWAY_ENVIRONMENT": 8000,
    }

    PREFERRED_PORTS = [8000, 8001, 8080, 3000, 5000, 4000]

    def detect(self) -> dict[str, Any]:
        """Detect network configuration (implements abstract method)."""
        return {"host": self.detect_host(), "port": self.detect_port()}

    def detect_host(self, environment: str = None, is_containerized: bool = False) -> str:
        """Detect optimal host binding based on environment and platform."""
        # Check for specific platform requirements first
        for env_var, host in self.PLATFORM_HOSTS.items():
            if self.get_env_var(env_var):
                return host

        # Environment-based detection
        if environment in ["production", "serverless"] or is_containerized:
            return "0.0.0.0"

        # Development and testing: localhost for security
        return "localhost"

    def detect_port(self) -> int:
        """Detect optimal port with platform-specific logic."""
        # Check platform-specific defaults FIRST (before PORT env var)
        for env_var, port in self.PLATFORM_PORTS.items():
            env_value = self.get_env_var(env_var)
            if env_value:
                self.logger.debug(f"Using platform-specific port {port} for {env_var}")
                return port

        # Then check environment variable (most common in production)
        env_port = self.get_env_var("PORT")
        if env_port:
            try:
                port = int(env_port)
                if 1 <= port <= 65535:  # Valid port range
                    self.logger.debug(f"Using PORT environment variable: {port}")
                    return port
            except (ValueError, TypeError):
                self.logger.debug(f"Invalid PORT value: {env_port}")

        # Find available port starting from preferred ranges
        self.logger.debug("Scanning for available port")
        return self._find_available_port()

    def _find_available_port(self) -> int:
        """Find an available port by scanning preferred ports."""
        # Try preferred ports first
        for port in self.PREFERRED_PORTS:
            if self._is_port_available(port):
                return port

        # Scan range 8000-8100
        for port in range(8000, 8100):
            if self._is_port_available(port):
                return port

        # Scan range 3000-3100 (common for web servers)
        for port in range(3000, 3100):
            if self._is_port_available(port):
                return port

        # Fallback to 8000 (might conflict, but better than crashing)
        self.logger.warning("No available ports found, falling back to 8000")
        return 8000

    def _is_port_available(self, port: int) -> bool:
        """Check if port is available for binding."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("localhost", port))
                return True
        except (OSError, Exception) as e:
            self.logger.debug(f"Port {port} not available: {e}")
            return False

    def detect_network_config(self, environment: str = None, is_containerized: bool = False) -> tuple[str, int]:
        """Detect both host and port configuration."""
        host = self.detect_host(environment, is_containerized)
        port = self.detect_port()
        return host, port
