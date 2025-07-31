#!/usr/bin/env python3
# src/chuk_mcp_server/config/smart_config.py
"""
Clean smart configuration class with integrated cloud detection.
"""

from typing import Dict, Any, Optional
from .project_detector import ProjectDetector
from .environment_detector import EnvironmentDetector
from .network_detector import NetworkDetector
from .system_detector import SystemDetector
from .container_detector import ContainerDetector
from .cloud_detector import CloudDetector


class SmartConfig:
    """Smart configuration with integrated cloud detection."""
    
    def __init__(self):
        self.project_detector = ProjectDetector()
        self.environment_detector = EnvironmentDetector()
        self.network_detector = NetworkDetector()
        self.system_detector = SystemDetector()
        self.container_detector = ContainerDetector()
        self.cloud_detector = CloudDetector()
        
        # Cache detection results
        self._cache: Dict[str, Any] = {}
    
    def get_all_defaults(self) -> Dict[str, Any]:
        """Get all smart defaults with cloud integration."""
        if not self._cache:
            self._detect_all()
        return self._cache.copy()
    
    def _detect_all(self):
        """Detect all configuration values with cloud integration."""
        # Core detections
        project_name = self.project_detector.detect()
        environment = self.environment_detector.detect()
        is_containerized = self.container_detector.detect()
        
        # Cloud detection
        cloud_provider = self.cloud_detector.detect()
        cloud_config = self.cloud_detector.get_config_overrides()
        
        # Network configuration (with cloud overrides)
        base_host, base_port = self.network_detector.detect_network_config(environment, is_containerized)
        host = cloud_config.get('host', base_host)
        port = cloud_config.get('port', base_port)
        
        # System configuration (with cloud overrides)
        base_workers = self.system_detector.detect_optimal_workers(environment, is_containerized)
        base_max_connections = self.system_detector.detect_max_connections(environment, is_containerized)
        base_debug = self.system_detector.detect_debug_mode(environment)
        base_log_level = self.system_detector.detect_log_level(environment)
        base_performance_mode = self.system_detector.detect_performance_mode(environment)
        
        # Apply cloud overrides
        workers = cloud_config.get('workers', base_workers)
        max_connections = cloud_config.get('max_connections', base_max_connections)
        debug = cloud_config.get('debug', base_debug)
        log_level = cloud_config.get('log_level', base_log_level)
        performance_mode = cloud_config.get('performance_mode', base_performance_mode)
        
        # Cache all results
        self._cache = {
            # Core configuration
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
            
            # Cloud information
            "cloud_provider": cloud_provider.name if cloud_provider else None,
            "cloud_display_name": cloud_provider.display_name if cloud_provider else None,
            "service_type": cloud_provider.get_service_type() if cloud_provider else None,
            "cloud_config": cloud_config,
        }
    
    # ============================================================================
    # Individual Getters (with lazy loading and cloud integration)
    # ============================================================================
    
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
        """Get detected optimal host with cloud overrides."""
        if 'host' not in self._cache:
            environment = self.get_environment()
            is_containerized = self.is_containerized()
            base_host = self.network_detector.detect_host(environment, is_containerized)
            cloud_config = self.cloud_detector.get_config_overrides()
            self._cache['host'] = cloud_config.get('host', base_host)
        return self._cache['host']
    
    def get_port(self) -> int:
        """Get detected optimal port with cloud overrides."""
        if 'port' not in self._cache:
            base_port = self.network_detector.detect_port()
            cloud_config = self.cloud_detector.get_config_overrides()
            self._cache['port'] = cloud_config.get('port', base_port)
        return self._cache['port']
    
    def is_containerized(self) -> bool:
        """Check if running in a container."""
        if 'containerized' not in self._cache:
            self._cache['containerized'] = self.container_detector.detect()
        return self._cache['containerized']
    
    def get_workers(self) -> int:
        """Get optimal worker count with cloud overrides."""
        if 'workers' not in self._cache:
            environment = self.get_environment()
            is_containerized = self.is_containerized()
            base_workers = self.system_detector.detect_optimal_workers(environment, is_containerized)
            cloud_config = self.cloud_detector.get_config_overrides()
            self._cache['workers'] = cloud_config.get('workers', base_workers)
        return self._cache['workers']
    
    def get_max_connections(self) -> int:
        """Get maximum connection limit with cloud overrides."""
        if 'max_connections' not in self._cache:
            environment = self.get_environment()
            is_containerized = self.is_containerized()
            base_max = self.system_detector.detect_max_connections(environment, is_containerized)
            cloud_config = self.cloud_detector.get_config_overrides()
            self._cache['max_connections'] = cloud_config.get('max_connections', base_max)
        return self._cache['max_connections']
    
    def should_enable_debug(self) -> bool:
        """Check if debug mode should be enabled with cloud overrides."""
        if 'debug' not in self._cache:
            environment = self.get_environment()
            base_debug = self.system_detector.detect_debug_mode(environment)
            cloud_config = self.cloud_detector.get_config_overrides()
            self._cache['debug'] = cloud_config.get('debug', base_debug)
        return self._cache['debug']
    
    def get_log_level(self) -> str:
        """Get appropriate log level with cloud overrides."""
        if 'log_level' not in self._cache:
            environment = self.get_environment()
            base_log_level = self.system_detector.detect_log_level(environment)
            cloud_config = self.cloud_detector.get_config_overrides()
            self._cache['log_level'] = cloud_config.get('log_level', base_log_level)
        return self._cache['log_level']
    
    def get_performance_mode(self) -> str:
        """Get optimal performance mode with cloud overrides."""
        if 'performance_mode' not in self._cache:
            environment = self.get_environment()
            base_mode = self.system_detector.detect_performance_mode(environment)
            cloud_config = self.cloud_detector.get_config_overrides()
            self._cache['performance_mode'] = cloud_config.get('performance_mode', base_mode)
        return self._cache['performance_mode']
    
    # ============================================================================
    # Cloud Integration Methods
    # ============================================================================
    
    def get_cloud_provider(self):
        """Get detected cloud provider."""
        return self.cloud_detector.detect()
    
    def get_cloud_config(self) -> Dict[str, Any]:
        """Get cloud-specific configuration."""
        return self.cloud_detector.get_config_overrides()
    
    def is_cloud_environment(self) -> bool:
        """Check if running in a cloud environment."""
        return self.cloud_detector.is_cloud_environment()
    
    def get_cloud_summary(self) -> Dict[str, Any]:
        """Get cloud provider summary."""
        provider = self.cloud_detector.detect()
        if not provider:
            return {"detected": False}
        
        return {
            "detected": True,
            "provider": provider.name,
            "display_name": provider.display_name,
            "service_type": provider.get_service_type(),
            "environment_type": provider.get_environment_type(),
        }
    
    # ============================================================================
    # Cache Management
    # ============================================================================
    
    def clear_cache(self):
        """Clear all caches."""
        self._cache.clear()
        self.cloud_detector.clear_cache()
    
    def refresh_cloud_detection(self):
        """Refresh only cloud detection."""
        self.cloud_detector.clear_cache()
        # Remove cloud-related cache entries
        cloud_keys = ['cloud_provider', 'cloud_display_name', 'service_type', 'cloud_config']
        for key in cloud_keys:
            self._cache.pop(key, None)
    
    # ============================================================================
    # Summary Methods
    # ============================================================================
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary with cloud information."""
        config = self.get_all_defaults()
        cloud_summary = self.get_cloud_summary()
        
        detection_summary = {
            "project": config["project_name"],
            "environment": config["environment"],
            "network": f"{config['host']}:{config['port']}",
            "containerized": config["containerized"],
            "performance": config["performance_mode"],
            "resources": f"{config['workers']} workers, {config['max_connections']} max connections",
            "logging": f"{config['log_level']} level, debug={config['debug']}"
        }
        
        # Add cloud information
        if cloud_summary["detected"]:
            detection_summary["cloud"] = cloud_summary["display_name"]
            detection_summary["service"] = cloud_summary.get("service_type", "N/A")
        else:
            detection_summary["cloud"] = "None detected"
            detection_summary["service"] = "N/A"
        
        return {
            "detection_summary": detection_summary,
            "cloud_summary": cloud_summary,
            "full_config": config
        }
    
    def get_detailed_info(self) -> Dict[str, Any]:
        """Get detailed configuration information."""
        summary = self.get_summary()
        cloud_info = self.cloud_detector.get_detection_info()
        env_info = self.environment_detector.get_detection_info()
        
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
                "cloud": cloud_info,
                "environment": env_info,
            },
            "cache_status": {
                "cached_keys": list(self._cache.keys()),
                "total_cached": len(self._cache),
            }
        }