#!/usr/bin/env python3
# src/chuk_mcp_server/config/system_detector.py
"""
System resource detection and optimization.
"""

from typing import Any

from .base import ConfigDetector
from .constants import (
    CONNECTIONS_PER_GB,
    CONTAINER_MAX_CONNECTIONS,
    CPU_UTILIZATION_FACTOR,
    DEVELOPMENT_MAX_CONNECTIONS,
    ENV_DEBUG,
    ENV_LOG_LEVEL,
    HIGH_CORE_THRESHOLD,
    MAX_WORKERS_CAP,
    MEDIUM_CORE_THRESHOLD,
    PRODUCTION_MAX_CONNECTIONS,
    SERVERLESS_MAX_CONNECTIONS,
)


class SystemDetector(ConfigDetector):
    """Detects system resources and calculates optimal settings."""

    def detect(self) -> dict[str, Any]:
        """Detect all system-related configuration."""
        return {
            "workers": self.detect_optimal_workers(),
            "max_connections": self.detect_max_connections(),
            "debug": self.detect_debug_mode(),
            "log_level": self.detect_log_level(),
            "performance_mode": self.detect_performance_mode(),
        }

    def detect_optimal_workers(self, environment: str | None = None, is_containerized: bool = False) -> int:
        """Calculate optimal worker count based on system resources."""
        try:
            import psutil

            cpu_cores = psutil.cpu_count(logical=True) or 1
            memory = psutil.virtual_memory()
            memory_gb = memory.available / (1024**3)

            # Environment-based adjustments
            if environment == "serverless":
                return 1  # Serverless: single worker for cold start performance
            elif environment == "development":
                return min(cpu_cores // 2, 4) or 1  # Moderate workers for debugging
            elif is_containerized:
                # Container: be conservative with resources
                return min(cpu_cores, MAX_WORKERS_CAP) if memory_gb >= 2 else min(cpu_cores // 2, 4) or 1
            else:
                # Production: optimize for throughput
                if cpu_cores <= MEDIUM_CORE_THRESHOLD:
                    return cpu_cores
                elif cpu_cores <= HIGH_CORE_THRESHOLD:
                    return min(cpu_cores, MAX_WORKERS_CAP)
                else:
                    # High-core systems: use 50-75% of cores
                    return int(cpu_cores * CPU_UTILIZATION_FACTOR)

        except Exception as e:
            self.logger.debug(f"Error detecting CPU/memory: {e}")
            return 1  # Fallback if psutil fails

    def detect_max_connections(self, environment: str | None = None, is_containerized: bool = False) -> int:
        """Calculate maximum connection limit based on available memory."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            memory_gb = memory.available / (1024**3)

            # Estimate ~1MB per connection (conservative)
            base_connections = int(memory_gb * CONNECTIONS_PER_GB)

            # Environment-based limits
            if environment == "serverless":
                return min(base_connections, SERVERLESS_MAX_CONNECTIONS)
            elif environment == "development":
                return min(base_connections, DEVELOPMENT_MAX_CONNECTIONS)
            elif is_containerized:
                return min(base_connections, CONTAINER_MAX_CONNECTIONS)
            else:
                return min(base_connections, PRODUCTION_MAX_CONNECTIONS)

        except Exception as e:
            self.logger.debug(f"Error detecting memory: {e}")
            return DEVELOPMENT_MAX_CONNECTIONS  # Fallback

    def detect_debug_mode(self, environment: str | None = None) -> bool:
        """Determine if debug mode should be enabled."""
        # Explicit debug flags
        debug_env = self.get_env_var(ENV_DEBUG, "").lower()
        if debug_env in ["true", "1", "yes", "on"]:
            return True
        elif debug_env in ["false", "0", "no", "off"]:
            return False

        # Environment-based defaults
        return environment in ["development", "testing"] if environment else True

    def detect_log_level(self, environment: str | None = None) -> str:
        """Determine appropriate log level."""
        # Explicit log level
        log_level = self.get_env_var(ENV_LOG_LEVEL, "").upper()
        if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            return log_level

        # Environment-based defaults
        if environment == "development":
            return "INFO"
        elif environment == "testing" or environment == "production":
            return "WARNING"
        else:
            return "INFO"

    def detect_performance_mode(self, environment: str | None = None) -> str:
        """Determine optimal performance mode."""
        try:
            import psutil

            cpu_cores = psutil.cpu_count(logical=True) or 1
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)

            if environment == "serverless":
                return "serverless_optimized"
            elif environment == "development":
                return "development"
            elif environment == "testing":
                return "testing"
            elif cpu_cores >= MAX_WORKERS_CAP and memory_gb >= MAX_WORKERS_CAP:
                return "ultra_high_performance"
            elif cpu_cores >= MEDIUM_CORE_THRESHOLD and memory_gb >= MEDIUM_CORE_THRESHOLD:
                return "high_performance"
            else:
                return "balanced"

        except Exception as e:
            self.logger.debug(f"Error detecting system specs: {e}")
            return "balanced"
