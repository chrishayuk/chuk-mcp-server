#!/usr/bin/env python3
# src/chuk_mcp_server/config/project_detector.py
"""
Project name detection from various sources.
"""

import re
from pathlib import Path
from typing import Optional
from .base import ConfigDetector


class ProjectDetector(ConfigDetector):
    """Detects project name from directory structure and config files."""
    
    GENERIC_DIRS = {"src", "lib", "app", "server", "api"}
    
    def detect(self) -> str:
        """Detect project name from various sources."""
        try:
            # Try current directory name first
            name = self._detect_from_directory()
            if name:
                return name
            
            # Try various config files
            name = self._detect_from_package_json()
            if name:
                return name
                
            name = self._detect_from_pyproject_toml()
            if name:
                return name
                
            name = self._detect_from_setup_py()
            if name:
                return name
                
            name = self._detect_from_cargo_toml()
            if name:
                return name
            
            # Try parent directory fallback
            name = self._detect_from_parent_directory()
            if name:
                return name
                
        except Exception as e:
            self.logger.debug(f"Error detecting project name: {e}")
        
        # Final fallback
        return "Smart MCP Server"
    
    def _detect_from_directory(self) -> Optional[str]:
        """Detect from current directory name."""
        try:
            current_dir = Path.cwd().name
            if current_dir and current_dir not in self.GENERIC_DIRS:
                # Check if it's a generic name that should fall back
                if current_dir.lower() in ['tmp', 'temp', 'test', 'random-dir']:
                    return None
                return self._format_project_name(current_dir)
        except Exception as e:
            self.logger.debug(f"Could not get current directory: {e}")
        return None
    
    def _detect_from_package_json(self) -> Optional[str]:
        """Detect from package.json."""
        package_json = Path.cwd() / "package.json"
        content = self.safe_file_read(package_json)
        if content:
            data = self.safe_json_parse(content)
            if data and 'name' in data:
                name = data['name']
                if name:
                    return self._format_project_name(name)
        return None
    
    def _detect_from_pyproject_toml(self) -> Optional[str]:
        """Detect from pyproject.toml."""
        pyproject = Path.cwd() / "pyproject.toml"
        content = self.safe_file_read(pyproject)
        if content:
            # Simple parser for name field
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('name = '):
                    # Extract name from 'name = "package-name"' or 'name = 'package-name''
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', line)
                    if match:
                        name = match.group(1)
                        if name:
                            return self._format_project_name(name)
        return None
    
    def _detect_from_setup_py(self) -> Optional[str]:
        """Detect from setup.py."""
        setup_py = Path.cwd() / "setup.py"
        content = self.safe_file_read(setup_py)
        if content:
            # Look for name= in setup() call
            for line in content.split('\n'):
                if 'name' in line and '=' in line:
                    # Extract name from various formats
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', line)
                    if match:
                        name = match.group(1)
                        if name and not name.startswith('__'):
                            return self._format_project_name(name)
        return None
    
    def _detect_from_cargo_toml(self) -> Optional[str]:
        """Detect from Cargo.toml (Rust)."""
        cargo_toml = Path.cwd() / "Cargo.toml"
        content = self.safe_file_read(cargo_toml)
        if content:
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('name = '):
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', line)
                    if match:
                        name = match.group(1)
                        if name:
                            return self._format_project_name(name)
        return None
    
    def _detect_from_parent_directory(self) -> Optional[str]:
        """Fallback to parent directory if we're in a common subdirectory."""
        try:
            current_dir = Path.cwd().name
            if current_dir in self.GENERIC_DIRS:
                parent_dir = Path.cwd().parent.name
                if parent_dir not in self.GENERIC_DIRS:
                    return self._format_project_name(parent_dir)
        except Exception as e:
            self.logger.debug(f"Could not check parent directory: {e}")
        return None
    
    def _format_project_name(self, name: str) -> str:
        """Format a project name into a nice server name."""
        # Replace underscores and hyphens with spaces, then title case
        formatted = name.replace('_', ' ').replace('-', ' ').title()
        return f"{formatted} MCP Server"