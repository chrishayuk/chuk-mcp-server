#!/usr/bin/env python3
# src/chuk_mcp_server/config/base.py
"""
Base classes and utilities for the smart configuration system.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigDetector(ABC):
    """Base class for configuration detectors."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def detect(self) -> Any:
        """Detect and return configuration value."""
        pass
    
    def safe_file_read(self, file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
        """Safely read a file with error handling."""
        try:
            if file_path.exists():
                return file_path.read_text(encoding=encoding)
        except (IOError, OSError, UnicodeDecodeError) as e:
            self.logger.debug(f"Could not read {file_path}: {e}")
        return None
    
    def safe_json_parse(self, content: str) -> Optional[Dict[str, Any]]:
        """Safely parse JSON content."""
        try:
            import json
            return json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.debug(f"Could not parse JSON: {e}")
        return None
    
    def get_env_var(self, key: str, default: Any = None) -> Any:
        """Get environment variable with logging."""
        value = os.environ.get(key, default)
        if value != default:
            self.logger.debug(f"Found environment variable {key}={value}")
        return value


class DetectionError(Exception):
    """Exception raised when detection fails."""
    pass