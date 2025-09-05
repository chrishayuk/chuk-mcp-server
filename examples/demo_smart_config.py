#!/usr/bin/env python3
# examples/demo_smart_config.py
"""
Smart Configuration Demo Script

A real demonstration of the modular smart configuration system detecting
actual system configuration and showing how all detectors work together.
"""

import os
import socket

# Add source path for demo
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chuk_mcp_server.config import (
    ContainerDetector,
    EnvironmentDetector,
    NetworkDetector,
    ProjectDetector,
    SmartConfig,
    SystemDetector,
)


def print_banner():
    """Print a welcome banner."""
    print("🧠 Smart Configuration System Demo")
    print("=" * 50)
    print("Real-time detection of your current system configuration")
    print()


def print_section(title: str, emoji: str = "🔍"):
    """Print a formatted section header."""
    print(f"\n{emoji} {title}")
    print("-" * (len(title) + 4))


def print_detection(label: str, value, details: str = ""):
    """Print a detection result."""
    print(f"   ✅ {label}: {value}")
    if details:
        print(f"      {details}")


def demo_individual_detectors():
    """Show each detector working on the real system."""
    print_section("Individual Detector Results", "🔧")

    # 1. Project Detector
    print("\n1️⃣ Project Name Detection")
    project_detector = ProjectDetector()
    project_name = project_detector.detect()
    print_detection("Detected Project", project_name)
    print(f"      Current directory: {Path.cwd()}")

    # Check what files exist
    config_files = []
    for file_name in ["package.json", "pyproject.toml", "setup.py", "Cargo.toml"]:
        if (Path.cwd() / file_name).exists():
            config_files.append(file_name)
    if config_files:
        print(f"      Found config files: {', '.join(config_files)}")
    else:
        print("      No project config files found")

    # 2. Environment Detector
    print("\n2️⃣ Environment Detection")
    env_detector = EnvironmentDetector()
    environment = env_detector.detect()
    print_detection("Detected Environment", environment)

    # Show relevant environment variables
    env_vars_to_check = ["NODE_ENV", "ENV", "ENVIRONMENT", "CI", "AWS_LAMBDA_FUNCTION_NAME", "VERCEL", "PORT"]
    found_env_vars = {}
    for var in env_vars_to_check:
        value = os.environ.get(var)
        if value:
            found_env_vars[var] = value

    if found_env_vars:
        print("      Relevant environment variables:")
        for var, value in found_env_vars.items():
            print(f"        {var}={value}")
    else:
        print("      No explicit environment variables set")

    # 3. Container Detector
    print("\n3️⃣ Container Detection")
    container_detector = ContainerDetector()
    is_containerized = container_detector.detect()
    print_detection("Running in Container", is_containerized)

    # Show what we checked
    print("      Container indicators checked:")
    print(f"        /.dockerenv exists: {Path('/.dockerenv').exists()}")
    print(f"        KUBERNETES_SERVICE_HOST: {bool(os.environ.get('KUBERNETES_SERVICE_HOST'))}")
    print(f"        CONTAINER env var: {bool(os.environ.get('CONTAINER'))}")
    print(f"        /proc/1/cgroup exists: {Path('/proc/1/cgroup').exists()}")

    # 4. Network Detector
    print("\n4️⃣ Network Configuration")
    network_detector = NetworkDetector()
    host = network_detector.detect_host(environment, is_containerized)
    port = network_detector.detect_port()
    print_detection("Optimal Host", host)
    print_detection("Optimal Port", port)

    # Check port availability
    def check_port(port_num):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("localhost", port_num))
                return True
        except OSError:
            return False

    print("      Port availability check:")
    test_ports = [8000, 8001, 3000, 5000]
    for test_port in test_ports:
        available = check_port(test_port)
        status = "✅ available" if available else "❌ in use"
        print(f"        Port {test_port}: {status}")

    # 5. System Detector
    print("\n5️⃣ System Resource Detection")
    system_detector = SystemDetector()

    try:
        import psutil

        # Get actual system info
        cpu_cores = psutil.cpu_count(logical=True)
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)

        print_detection("CPU Cores", f"{cpu_cores} cores")
        print_detection("Total Memory", f"{memory_gb:.1f} GB")
        print_detection("Available Memory", f"{memory.available / (1024**3):.1f} GB")

        # Show optimal settings
        workers = system_detector.detect_optimal_workers(environment, is_containerized)
        max_connections = system_detector.detect_max_connections(environment, is_containerized)
        debug_mode = system_detector.detect_debug_mode(environment)
        log_level = system_detector.detect_log_level(environment)
        performance_mode = system_detector.detect_performance_mode(environment)

        print_detection("Optimal Workers", workers)
        print_detection("Max Connections", max_connections)
        print_detection("Debug Mode", debug_mode)
        print_detection("Log Level", log_level)
        print_detection("Performance Mode", performance_mode)

    except ImportError:
        print("      ⚠️  psutil not available - using fallback detection")
        workers = 1
        print_detection("Optimal Workers", f"{workers} (fallback)")


def demo_smart_config():
    """Show the complete SmartConfig in action."""
    print_section("Complete Smart Configuration", "🧠")

    print("Creating SmartConfig instance...")
    config = SmartConfig()

    print("\n📊 All Configuration Detected:")
    all_config = config.get_all_defaults()

    # Display in a nice format
    config_display = {
        "Project & Environment": {
            "project_name": all_config["project_name"],
            "environment": all_config["environment"],
            "containerized": all_config["containerized"],
        },
        "Network Configuration": {"host": all_config["host"], "port": all_config["port"]},
        "System Optimization": {
            "workers": all_config["workers"],
            "max_connections": all_config["max_connections"],
            "performance_mode": all_config["performance_mode"],
        },
        "Development Settings": {"debug": all_config["debug"], "log_level": all_config["log_level"]},
    }

    for category, settings in config_display.items():
        print(f"\n   {category}:")
        for key, value in settings.items():
            print(f"      {key.replace('_', ' ').title()}: {value}")


def demo_configuration_summary():
    """Show the configuration summary feature."""
    print_section("Configuration Summary", "📋")

    config = SmartConfig()
    summary = config.get_summary()

    print("🎯 Detection Summary:")
    detection_summary = summary["detection_summary"]
    for key, value in detection_summary.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")


def demo_caching_behavior():
    """Demonstrate the caching behavior."""
    print_section("Caching Behavior Demo", "⚡")

    config = SmartConfig()

    print("First detection (cold cache):")
    start_time = time.time()
    project_name = config.get_project_name()
    first_time = time.time() - start_time
    print(f"   Project name: {project_name}")
    print(f"   Time: {first_time:.4f} seconds")

    print("\nSecond detection (cached):")
    start_time = time.time()
    project_name = config.get_project_name()
    second_time = time.time() - start_time
    print(f"   Project name: {project_name}")
    print(f"   Time: {second_time:.4f} seconds")

    if second_time < first_time:
        speedup = first_time / second_time if second_time > 0 else float("inf")
        print(f"   🚀 Caching speedup: {speedup:.1f}x faster")

    print("\nClearing cache...")
    config.clear_cache()

    print("After cache clear:")
    start_time = time.time()
    project_name = config.get_project_name()
    third_time = time.time() - start_time
    print(f"   Time: {third_time:.4f} seconds")


def demo_realistic_scenarios():
    """Show how configuration would differ in various scenarios."""
    print_section("Scenario Predictions", "🎭")

    print("Based on current detection, here's how configuration would change:")

    config = SmartConfig()
    current_env = config.get_environment()
    config.is_containerized()

    scenarios = [
        ("🏠 If running in development", "development", False),
        ("🏭 If running in production", "production", False),
        ("🐳 If running in Docker", current_env, True),
        ("☁️ If running in AWS Lambda", "serverless", False),
    ]

    for scenario_name, env, containerized in scenarios:
        print(f"\n{scenario_name}:")

        # Show what would change
        network_detector = NetworkDetector()
        system_detector = SystemDetector()

        host = network_detector.detect_host(env, containerized)
        workers = system_detector.detect_optimal_workers(env, containerized)
        debug = system_detector.detect_debug_mode(env)
        log_level = system_detector.detect_log_level(env)

        print(f"   Host: {host}")
        print(f"   Workers: {workers}")
        print(f"   Debug: {debug}")
        print(f"   Log Level: {log_level}")


def demo_environment_variables():
    """Show what environment variables would affect detection."""
    print_section("Environment Variable Guide", "🌍")

    print("Environment variables that affect smart detection:")

    categories = {
        "Environment Detection": [
            ("NODE_ENV", "production/development/staging/test"),
            ("ENV", "prod/dev/stage/test"),
            ("CI", "true (detects CI/CD environment)"),
            ("AWS_LAMBDA_FUNCTION_NAME", "any value (detects serverless)"),
            ("VERCEL", "any value (detects Vercel platform)"),
        ],
        "Network Configuration": [
            ("PORT", "port number (e.g., 8080)"),
            ("VERCEL", "true (uses port 3000)"),
            ("NETLIFY", "true (uses port 8888)"),
        ],
        "Container Detection": [
            ("CONTAINER", "any value (indicates containerized)"),
            ("KUBERNETES_SERVICE_HOST", "any value (detects K8s)"),
        ],
        "Debug & Logging": [
            ("DEBUG", "true/false (overrides debug mode)"),
            ("LOG_LEVEL", "DEBUG/INFO/WARNING/ERROR"),
        ],
    }

    for category, vars_list in categories.items():
        print(f"\n📂 {category}:")
        for var_name, description in vars_list:
            current_value = os.environ.get(var_name)
            if current_value:
                print(f"   ✅ {var_name}={current_value} - {description}")
            else:
                print(f"   ⚪ {var_name} - {description}")


def main():
    """Run the complete demo."""
    print_banner()

    try:
        demo_individual_detectors()
        demo_smart_config()
        demo_configuration_summary()
        demo_caching_behavior()
        demo_realistic_scenarios()
        demo_environment_variables()

        print_section("Demo Complete! 🎉", "✨")
        print("The smart configuration system has analyzed your current environment")
        print("and would automatically optimize settings for your deployment scenario.")
        print("\nTry setting different environment variables and running again!")
        print("Example: NODE_ENV=production python demo_smart_config.py")

    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("Make sure you're running from the project root directory")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
