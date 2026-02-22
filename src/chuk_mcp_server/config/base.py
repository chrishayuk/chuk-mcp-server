#!/usr/bin/env python3
# src/chuk_mcp_server/config/base.py
"""
Base classes and utilities for the smart configuration system.
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConfigDetector(ABC):
    """Base class for configuration detectors."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def detect(self) -> Any:
        """Detect and return configuration value."""
        pass

    def safe_file_read(self, file_path: Path, encoding: str = "utf-8") -> str | None:
        """Safely read a file with error handling."""
        try:
            if file_path.exists():
                return file_path.read_text(encoding=encoding)
        except (OSError, UnicodeDecodeError) as e:
            self.logger.debug(f"Could not read {file_path}: {e}")
        return None

    def safe_json_parse(self, content: str) -> dict[str, Any] | None:
        """Safely parse JSON content."""
        try:
            import orjson

            return orjson.loads(content)
        except (orjson.JSONDecodeError, TypeError) as e:
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
