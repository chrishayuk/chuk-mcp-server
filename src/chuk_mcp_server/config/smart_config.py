#!/usr/bin/env python3
# src/chuk_mcp_server/config/smart_config.py
"""
Main smart configuration class that orchestrates all detectors.
"""

from typing import Dict, Any
from .project_detector import ProjectDetector
from .environment_detector import EnvironmentDetector
from .network_detector import NetworkDetector
from .system_detector import SystemDetector
from .container_detector import ContainerDetector


class SmartConfig:
    """Main smart configuration class that orchestrates all detection."""
    
    def __init__(self):
        self.project_detector = ProjectDetector()
        self.environment_detector = EnvironmentDetector()
        self.network_detector = NetworkDetector()
        self.system_detector = SystemDetector()
        self.container_detector = ContainerDetector()
        
        # Cache detection results
        self._cache: Dict[str, Any] = {}
    
    def get_all_defaults(self) -> Dict[str, Any]:
        """Get all smart defaults in one call for efficiency."""
        if not self._cache:
            self._detect_all()
        return self._cache.copy()
    
    def _detect_all(self):
        """Detect all configuration values and cache them."""
        # Core detections
        project_name = self.project_detector.detect()
        environment = self.environment_detector.detect()
        is_containerized = self.container_detector.detect()
        
        # Network configuration (depends on environment and containerization)
        host, port = self.network_detector.detect_network_config(environment, is_containerized)
        
        # System configuration (depends on environment and containerization)
        system_config = self.system_detector.detect()
        workers = self.system_detector.detect_optimal_workers(environment, is_containerized)
        max_connections = self.system_detector.detect_max_connections(environment, is_containerized)
        debug = self.system_detector.detect_debug_mode(environment)
        log_level = self.system_detector.detect_log_level(environment)
        performance_mode = self.system_detector.detect_performance_mode(environment)
        
        # Cache all results
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
    
    def get_project_name(self) -> str:
        """Get detected project name."""
        if 'project_name' not in self._cache:
            self._cache['project_name'] = self.project_detector.detect()
        return self._cache['project_name']
    
    def get_environment(self) -> str:
        """Get detected environment."""
        if 'environment' not in self._cache:
            self._cache['environment'] = self.environment_detector.detect()
        return self._cache['environment']
    
    def get_host(self) -> str:
        """Get detected optimal host."""
        if 'host' not in self._cache:
            environment = self.get_environment()
            is_containerized = self.is_containerized()
            self._cache['host'] = self.network_detector.detect_host(environment, is_containerized)
        return self._cache['host']
    
    def get_port(self) -> int:
        """Get detected optimal port."""
        if 'port' not in self._cache:
            self._cache['port'] = self.network_detector.detect_port()
        return self._cache['port']
    
    def is_containerized(self) -> bool:
        """Check if running in a container."""
        if 'containerized' not in self._cache:
            self._cache['containerized'] = self.container_detector.detect()
        return self._cache['containerized']
    
    def get_workers(self) -> int:
        """Get optimal worker count."""
        if 'workers' not in self._cache:
            environment = self.get_environment()
            is_containerized = self.is_containerized()
            self._cache['workers'] = self.system_detector.detect_optimal_workers(environment, is_containerized)
        return self._cache['workers']
    
    def get_max_connections(self) -> int:
        """Get maximum connection limit."""
        if 'max_connections' not in self._cache:
            environment = self.get_environment()
            is_containerized = self.is_containerized()
            self._cache['max_connections'] = self.system_detector.detect_max_connections(environment, is_containerized)
        return self._cache['max_connections']
    
    def should_enable_debug(self) -> bool:
        """Check if debug mode should be enabled."""
        if 'debug' not in self._cache:
            environment = self.get_environment()
            self._cache['debug'] = self.system_detector.detect_debug_mode(environment)
        return self._cache['debug']
    
    def get_log_level(self) -> str:
        """Get appropriate log level."""
        if 'log_level' not in self._cache:
            environment = self.get_environment()
            self._cache['log_level'] = self.system_detector.detect_log_level(environment)
        return self._cache['log_level']
    
    def get_performance_mode(self) -> str:
        """Get optimal performance mode."""
        if 'performance_mode' not in self._cache:
            environment = self.get_environment()
            self._cache['performance_mode'] = self.system_detector.detect_performance_mode(environment)
        return self._cache['performance_mode']
    
    def clear_cache(self):
        """Clear the detection cache to force re-detection."""
        self._cache.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all detected configuration."""
        config = self.get_all_defaults()
        return {
            "detection_summary": {
                "project": config["project_name"],
                "environment": config["environment"],
                "network": f"{config['host']}:{config['port']}",
                "containerized": config["containerized"],
                "performance": config["performance_mode"],
                "resources": f"{config['workers']} workers, {config['max_connections']} max connections",
                "logging": f"{config['log_level']} level, debug={config['debug']}"
            },
            "full_config": config
        }