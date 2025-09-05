#!/usr/bin/env python3
"""
Debug script to test network detection behavior.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add source path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chuk_mcp_server.config.network_detector import NetworkDetector


def test_platform_ports():
    """Test platform port detection."""
    print("Testing NetworkDetector platform port priority...")

    detector = NetworkDetector()

    # Print platform ports configuration
    print(f"Platform ports config: {detector.PLATFORM_PORTS}")

    # Test 1: Only VERCEL set
    print("\n1. Testing only VERCEL set:")
    with patch.dict(os.environ, {"VERCEL": "1"}, clear=True):
        print(f"   Environment: VERCEL={os.environ.get('VERCEL')}")
        result = detector.detect_port()
        print(f"   Result: {result} (expected: 3000)")

    # Test 2: Only PORT set
    print("\n2. Testing only PORT set:")
    with patch.dict(os.environ, {"PORT": "9000"}, clear=True):
        print(f"   Environment: PORT={os.environ.get('PORT')}")
        result = detector.detect_port()
        print(f"   Result: {result} (expected: 9000)")

    # Test 3: Both VERCEL and PORT set
    print("\n3. Testing both VERCEL and PORT set:")
    with patch.dict(os.environ, {"VERCEL": "1", "PORT": "9000"}, clear=True):
        print(f"   Environment: VERCEL={os.environ.get('VERCEL')}, PORT={os.environ.get('PORT')}")

        # Check get_env_var behavior
        vercel_val = detector.get_env_var("VERCEL")
        port_val = detector.get_env_var("PORT")
        print(f"   get_env_var('VERCEL'): {vercel_val}")
        print(f"   get_env_var('PORT'): {port_val}")

        # Step through the logic
        print("   Checking platform ports:")
        for env_var, port in detector.PLATFORM_PORTS.items():
            env_val = detector.get_env_var(env_var)
            print(f"     {env_var}: {env_val} -> port {port}")
            if env_val:
                print(f"     FOUND: {env_var} is set, should return {port}")
                break

        result = detector.detect_port()
        print(f"   Final result: {result} (expected: 3000)")

    # Test 4: Mock get_env_var directly
    print("\n4. Testing with mocked get_env_var:")

    def mock_get_env_var(key, default=None):
        values = {"VERCEL": "1", "PORT": "9000"}
        result = values.get(key, default)
        print(f"     mock_get_env_var('{key}') -> {result}")
        return result

    original_method = detector.get_env_var
    detector.get_env_var = mock_get_env_var

    try:
        result = detector.detect_port()
        print(f"   Result with mocked method: {result} (expected: 3000)")
    finally:
        detector.get_env_var = original_method


if __name__ == "__main__":
    test_platform_ports()
