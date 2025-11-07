"""Unified composition layer for server composition and proxying."""

from .config_loader import CompositionConfigLoader, load_from_config
from .manager import CompositionManager

__all__ = [
    "CompositionManager",
    "CompositionConfigLoader",
    "load_from_config",
]
