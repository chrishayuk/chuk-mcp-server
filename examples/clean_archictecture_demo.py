#!/usr/bin/env python3
# examples/clean_architecture_demo.py
"""
Demo of the clean architecture where:
- Providers live in cloud/
- CloudDetector lives in config/ and uses the providers
- Clean separation of concerns
"""

import os
import sys
from pathlib import Path

# Add source path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def demonstrate_clean_separation():
    """Demonstrate the clean separation between config and cloud modules."""

    print("🏗️  Clean Architecture Demo")
    print("=" * 60)

    # 1. Show cloud providers (from cloud module)
    print("\n1️⃣ Cloud Providers (from cloud module):")
    try:
        from chuk_mcp_server.cloud import cloud_registry, list_cloud_providers

        providers = list_cloud_providers()
        for provider_info in providers:
            status = "✅ DETECTED" if provider_info["detected"] else "⚪ available"
            print(f"   {status} {provider_info['display_name']} ({provider_info['name']})")

        print(f"   📊 Total providers in cloud registry: {len(providers)}")

    except ImportError as e:
        print(f"   ❌ Cloud module not available: {e}")

    # 2. Show cloud detector (from config module)
    print("\n2️⃣ Cloud Detector (from config module):")
    try:
        from chuk_mcp_server.config import CloudDetector

        cloud_detector = CloudDetector()
        provider = cloud_detector.detect()

        if provider:
            print(f"   ✅ Detected: {provider.display_name}")
            print(f"   🏷️  Provider: {provider.name}")
            print(f"   🚀 Service: {provider.get_service_type()}")
            print(f"   🌍 Environment: {provider.get_environment_type()}")

            config_overrides = cloud_detector.get_config_overrides()
            print(f"   ⚙️  Config overrides: {len(config_overrides)} settings")
            for key, value in config_overrides.items():
                if key not in ["cloud_provider", "service_type"]:  # Skip metadata
                    print(f"      {key}: {value}")
        else:
            print("   🏠 No cloud provider detected (local environment)")

    except ImportError as e:
        print(f"   ❌ Config module not available: {e}")

    # 3. Show smart config integration
    print("\n3️⃣ Smart Config Integration:")
    try:
        from chuk_mcp_server.config import SmartConfig

        smart_config = SmartConfig()
        summary = smart_config.get_summary()

        print("   📊 Detection Summary:")
        for key, value in summary["detection_summary"].items():
            print(f"      {key.replace('_', ' ').title()}: {value}")

        cloud_summary = summary["cloud_summary"]
        if cloud_summary["detected"]:
            print(f"\n   ☁️  Cloud Integration:")
            print(f"      Provider: {cloud_summary['display_name']}")
            print(f"      Service: {cloud_summary['service_type']}")
            print(f"      Environment: {cloud_summary['environment_type']}")

    except ImportError as e:
        print(f"   ❌ Smart config not available: {e}")


def demonstrate_architecture_benefits():
    """Show the benefits of the clean architecture."""

    print("\n" + "=" * 60)
    print("🎯 Architecture Benefits")
    print("=" * 60)

    print("\n✅ Clean Separation:")
    print("   📁 cloud/ - Contains all cloud providers")
    print("   📁 config/ - Contains all configuration detectors")
    print("   🔗 CloudDetector imports from cloud module")
    print("   🎯 Single responsibility for each module")

    print("\n✅ Easy Extension:")
    print("   ➕ Add new providers to cloud/providers/")
    print("   🏷️  Use @cloud_provider decorator for auto-registration")
    print("   🔄 CloudDetector automatically uses new providers")
    print("   📦 No changes needed to config module")

    print("\n✅ Proper Dependencies:")
    print("   ⬇️  config depends on cloud (imports providers)")
    print("   ❌ cloud does NOT depend on config")
    print("   🏗️  Clean dependency hierarchy")
    print("   🧪 Easy to test each module independently")

    print("\n✅ Zero Configuration:")
    print("   🧠 CloudDetector automatically finds providers")
    print("   ⚙️  Applies cloud-specific configuration")
    print("   🔧 Works with existing SmartConfig system")
    print("   🚀 No manual setup required")


def demonstrate_adding_provider():
    """Show how easy it is to add a new provider."""

    print("\n" + "=" * 60)
    print("➕ Adding New Provider Example")
    print("=" * 60)

    example_code = """
# src/chuk_mcp_server/cloud/providers/digitalocean.py
from ..base import CloudProvider
from ..registry import cloud_provider

@cloud_provider("digitalocean", "DigitalOcean Functions", priority=25)
class DigitalOceanProvider(CloudProvider):
    @property
    def name(self) -> str:
        return "digitalocean"
    
    @property  
    def display_name(self) -> str:
        return "DigitalOcean Functions"
    
    def detect(self) -> bool:
        return bool(os.environ.get('DO_FUNCTION_NAME'))
    
    def get_environment_type(self) -> str:
        return "serverless"
    
    def get_config_overrides(self) -> Dict[str, Any]:
        return {
            "host": "0.0.0.0",
            "port": int(os.environ.get('PORT', 8080)),
            "workers": 1,
            "performance_mode": "digitalocean_optimized"
        }

# That's it! CloudDetector will automatically use it.
"""

    print("📝 Steps to add DigitalOcean Functions support:")
    print("   1️⃣ Create new file: cloud/providers/digitalocean.py")
    print("   2️⃣ Copy the code above")
    print("   3️⃣ Import in cloud/providers/__init__.py")
    print("   4️⃣ Done! Zero configuration works everywhere")

    print(f"\n💻 Example Code:")
    print(example_code)


def demonstrate_usage():
    """Show usage examples with the clean architecture."""

    print("\n" + "=" * 60)
    print("🚀 Usage Examples")
    print("=" * 60)

    usage_examples = """
# Zero configuration - works everywhere
from chuk_mcp_server import ChukMCPServer, tool

mcp = ChukMCPServer()  # Auto-detects cloud via config system

@mcp.tool
def hello(name: str) -> str:
    return f"Hello from {mcp.cloud_provider or 'local'}, {name}!"

# Deployment ready for any cloud platform!

# Manual cloud detection
from chuk_mcp_server.config import detect_cloud_provider

provider = detect_cloud_provider()
if provider:
    print(f"Running on {provider.display_name}")
    config = provider.get_config_overrides()
    print(f"Using {config['workers']} workers")

# Environment-aware tools
@mcp.tool
async def environment_info() -> dict:
    from chuk_mcp_server.config import CloudDetector
    
    cloud_detector = CloudDetector()
    provider = cloud_detector.detect()
    
    return {
        "platform": provider.display_name if provider else "Local",
        "service": provider.get_service_type() if provider else "development",
        "config": cloud_detector.get_config_overrides()
    }
"""

    print("📚 Usage Examples:")
    print(usage_examples)


def main():
    """Run the complete demonstration."""
    try:
        demonstrate_clean_separation()
        demonstrate_architecture_benefits()
        demonstrate_adding_provider()
        demonstrate_usage()

        print("\n" + "=" * 60)
        print("🎉 Clean Architecture Demo Complete!")
        print("=" * 60)

        print("\n🏗️  Architecture Summary:")
        print("   📁 cloud/ - Self-contained cloud providers")
        print("   📁 config/ - Configuration detectors (uses cloud/)")
        print("   🔗 Clean dependency: config → cloud")
        print("   🎯 Single responsibility per module")
        print("   ➕ Easy to extend with new providers")
        print("   🚀 Zero configuration for end users")

        print("\n✨ This architecture solves all the original issues:")
        print("   ✅ Providers belong in cloud/")
        print("   ✅ CloudDetector is just a detector")
        print("   ✅ No confusing names or artificial separation")
        print("   ✅ Clean, maintainable, extensible")

    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
