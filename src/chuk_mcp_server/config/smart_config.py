#!/usr/bin/env python3
# src/chuk_mcp_server/config/smart_config.py
"""
Clean smart configuration class with integrated cloud detection.
"""

from typing import Any

from .cloud_detector import CloudDetector
from .container_detector import ContainerDetector
from .environment_detector import EnvironmentDetector
from .network_detector import NetworkDetector
from .project_detector import ProjectDetector
from .system_detector import SystemDetector


class SmartConfig:
    """Smart configuration with integrated cloud detection."""

    def __init__(self):
        self.project_detector = ProjectDetector()
        self.environment_detector = EnvironmentDetector()
        self.network_detector = NetworkDetector()
        self.system_detector = SystemDetector()
        self.container_detector = ContainerDetector()
        self.cloud_detector = CloudDetector()
        self._cache: dict[str, Any] = {}

    def get_all_defaults(self) -> dict[str, Any]:
        """Return a copy of the cached config, populating if empty."""
        if not self._cache:
            self._detect_all()
        return self._cache.copy()

    def _detect_all(self):
        """Run every detector, apply cloud overrides, fill _cache with core keys."""
        # Core values
        project_name = self.project_detector.detect()
        environment = self.environment_detector.detect()
        is_containerized = self.container_detector.detect()

        # Cloud overrides
        cloud_cfg = self.cloud_detector.get_config_overrides()

        # Network
        base_host, base_port = self.network_detector.detect_network_config(environment, is_containerized)
        host = cloud_cfg.get("host", base_host)
        port = cloud_cfg.get("port", base_port)

        # System defaults
        base_workers = self.system_detector.detect_optimal_workers(environment, is_containerized)
        base_max_conn = self.system_detector.detect_max_connections(environment, is_containerized)
        base_debug = self.system_detector.detect_debug_mode(environment)
        base_log = self.system_detector.detect_log_level(environment)
        base_perf = self.system_detector.detect_performance_mode(environment)

        # Override logic; serverless forces 1 worker, 100 connections,
        # and uses 'serverless_optimized' performance mode
        if environment == "serverless":
            workers = 1
            max_connections = 100
            performance_mode = "serverless_optimized"
        else:
            workers = cloud_cfg.get("workers", base_workers)
            max_connections = cloud_cfg.get("max_connections", base_max_conn)
            performance_mode = cloud_cfg.get("performance_mode", base_perf)

        debug = cloud_cfg.get("debug", base_debug)
        log_level = cloud_cfg.get("log_level", base_log)

        # Cache only the core set of keys expected by tests
        self._cache = {
            "project_name": project_name,
            "environment": environment,
            "host": host,
            "port": port,
            "debug": debug,
            "workers": workers,
            "max_connections": max_connections,
            "log_level": log_level,
            "performance_mode": performance_mode,
            "containerized": is_containerized,
        }

    # ------------------------------------------------------------------------
    # Individual getters with lazy caching and cloud integration
    # ------------------------------------------------------------------------

    def get_project_name(self) -> str:
        if "project_name" not in self._cache:
            self._cache["project_name"] = self.project_detector.detect()
        return self._cache["project_name"]

    def get_environment(self) -> str:
        if "environment" not in self._cache:
            self._cache["environment"] = self.environment_detector.detect()
        return self._cache["environment"]

    def get_host(self) -> str:
        if "host" not in self._cache:
            env = self.get_environment()
            cont = self.is_containerized()
            base_host, _ = self.network_detector.detect_network_config(env, cont)
            cfg = self.cloud_detector.get_config_overrides()
            self._cache["host"] = cfg.get("host", base_host)
        return self._cache["host"]

    def get_port(self) -> int:
        if "port" not in self._cache:
            env = self.get_environment()
            cont = self.is_containerized()
            _, base_port = self.network_detector.detect_network_config(env, cont)
            cfg = self.cloud_detector.get_config_overrides()
            self._cache["port"] = cfg.get("port", base_port)
        return self._cache["port"]

    def is_containerized(self) -> bool:
        if "containerized" not in self._cache:
            self._cache["containerized"] = self.container_detector.detect()
        return self._cache["containerized"]

    def get_workers(self) -> int:
        if "workers" not in self._cache:
            env = self.get_environment()
            cont = self.is_containerized()
            base = self.system_detector.detect_optimal_workers(env, cont)
            cfg = self.cloud_detector.get_config_overrides()
            self._cache["workers"] = 1 if env == "serverless" else cfg.get("workers", base)
        return self._cache["workers"]

    def get_max_connections(self) -> int:
        if "max_connections" not in self._cache:
            env = self.get_environment()
            cont = self.is_containerized()
            base = self.system_detector.detect_max_connections(env, cont)
            cfg = self.cloud_detector.get_config_overrides()
            self._cache["max_connections"] = 100 if env == "serverless" else cfg.get("max_connections", base)
        return self._cache["max_connections"]

    def should_enable_debug(self) -> bool:
        if "debug" not in self._cache:
            env = self.get_environment()
            base = self.system_detector.detect_debug_mode(env)
            cfg = self.cloud_detector.get_config_overrides()
            self._cache["debug"] = cfg.get("debug", base)
        return self._cache["debug"]

    def get_log_level(self) -> str:
        if "log_level" not in self._cache:
            env = self.get_environment()
            base = self.system_detector.detect_log_level(env)
            cfg = self.cloud_detector.get_config_overrides()
            self._cache["log_level"] = cfg.get("log_level", base)
        return self._cache["log_level"]

    def get_performance_mode(self) -> str:
        if "performance_mode" not in self._cache:
            env = self.get_environment()
            base = self.system_detector.detect_performance_mode(env)
            cfg = self.cloud_detector.get_config_overrides()
            # ensure fallback for non-serverless
            self._cache["performance_mode"] = cfg.get("performance_mode", base)
        return self._cache["performance_mode"]

    # ------------------------------------------------------------------------
    # Cloud-specific methods
    # ------------------------------------------------------------------------

    def get_cloud_provider(self):
        return self.cloud_detector.detect()

    def get_cloud_config(self) -> dict[str, Any]:
        return self.cloud_detector.get_config_overrides()

    def is_cloud_environment(self) -> bool:
        return self.cloud_detector.is_cloud_environment()

    def get_cloud_summary(self) -> dict[str, Any]:
        provider = self.get_cloud_provider()
        if not provider:
            return {"detected": False}
        return {
            "detected": True,
            "provider": provider.name,
            "display_name": provider.display_name,
            "service_type": provider.get_service_type(),
            "environment_type": provider.get_environment_type(),
        }

    # ------------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------------

    def clear_cache(self):
        self._cache.clear()
        self.cloud_detector.clear_cache()

    def refresh_cloud_detection(self):
        self.cloud_detector.clear_cache()
        for key in ("cloud_provider", "cloud_config", "service_type", "cloud_display_name"):
            self._cache.pop(key, None)

    # ------------------------------------------------------------------------
    # Summary outputs
    # ------------------------------------------------------------------------

    def get_summary(self) -> dict[str, Any]:
        cfg = self.get_all_defaults()
        cloud = self.get_cloud_summary()
        detection_summary = {
            "project": cfg["project_name"],
            "environment": cfg["environment"],
            "network": f"{cfg['host']}:{cfg['port']}",
            "containerized": cfg["containerized"],
            "performance": cfg["performance_mode"],
            "resources": f"{cfg['workers']} workers, {cfg['max_connections']} max connections",
            "logging": f"{cfg['log_level']} level, debug={cfg['debug']}",
        }
        if cloud.get("detected"):
            detection_summary["cloud"] = cloud["display_name"]
            detection_summary["service"] = cloud.get("service_type", "N/A")
        else:
            detection_summary["cloud"] = "None detected"
            detection_summary["service"] = "N/A"
        return {"detection_summary": detection_summary, "cloud_summary": cloud, "full_config": cfg}

    def get_detailed_info(self) -> dict[str, Any]:
        summary = self.get_summary()
        return {
            **summary,
            "detectors": {
                "project_detector": type(self.project_detector).__name__,
                "environment_detector": type(self.environment_detector).__name__,
                "network_detector": type(self.network_detector).__name__,
                "system_detector": type(self.system_detector).__name__,
                "container_detector": type(self.container_detector).__name__,
                "cloud_detector": type(self.cloud_detector).__name__,
            },
            "detection_details": {
                "environment": self.environment_detector.get_detection_info(),
                "cloud": self.cloud_detector.get_detection_info(),
            },
            "cache_status": {
                "cached_keys": list(self._cache.keys()),
                "total_cached": len(self._cache),
            },
        }
