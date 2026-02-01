#!/usr/bin/env python3
"""
Configuration detection constants — CI indicators, container detection,
port numbers, worker/connection limits.
"""

# ---------------------------------------------------------------------------
# CI/CD environment indicator variables
# ---------------------------------------------------------------------------
CI_INDICATORS = (
    "CI",
    "CONTINUOUS_INTEGRATION",
    "GITHUB_ACTIONS",
    "GITLAB_CI",
    "JENKINS_HOME",
    "TRAVIS",
    "CIRCLECI",
    "BUILDKITE",
    "DRONE",
    "BAMBOO_BUILD_KEY",
)


# ---------------------------------------------------------------------------
# Transport detection environment variables
# ---------------------------------------------------------------------------
ENV_MCP_TRANSPORT = "MCP_TRANSPORT"
ENV_MCP_STDIO = "MCP_STDIO"
ENV_USE_STDIO = "USE_STDIO"


# ---------------------------------------------------------------------------
# Serverless environment detection variables
# ---------------------------------------------------------------------------
ENV_AWS_LAMBDA = "AWS_LAMBDA_FUNCTION_NAME"
ENV_GCP_FUNCTION = "GOOGLE_CLOUD_FUNCTION_NAME"
ENV_AZURE_FUNCTIONS = "AZURE_FUNCTIONS_ENVIRONMENT"
ENV_VERCEL = "VERCEL"
ENV_NETLIFY = "NETLIFY"


# ---------------------------------------------------------------------------
# Container detection
# ---------------------------------------------------------------------------
DOCKERENV_PATH = "/.dockerenv"
CGROUP_PATH = "/proc/1/cgroup"
MOUNTINFO_PATH = "/proc/self/mountinfo"

CONTAINER_INDICATORS = ("docker", "containerd", "lxc", "kubepods")

ENV_KUBERNETES_HOST = "KUBERNETES_SERVICE_HOST"
ENV_CONTAINER = "CONTAINER"


# ---------------------------------------------------------------------------
# Environment type detection variables
# ---------------------------------------------------------------------------
ENV_NODE_ENV = "NODE_ENV"
ENV_ENV = "ENV"
ENV_ENVIRONMENT = "ENVIRONMENT"
ENV_DEBUG = "DEBUG"
ENV_LOG_LEVEL = "LOG_LEVEL"
ENV_PORT = "PORT"


# ---------------------------------------------------------------------------
# Platform-specific environment variables (for port detection)
# ---------------------------------------------------------------------------
PLATFORM_PORT_MAP: dict[str, int] = {
    "VERCEL": 3000,
    "RAILWAY_ENVIRONMENT": 8000,
    "RENDER": 8000,
    "FLY_APP_NAME": 8080,
    "HEROKU_APP_NAME": 8000,
}


# ---------------------------------------------------------------------------
# Port scanning defaults
# ---------------------------------------------------------------------------
PREFERRED_PORTS = (8000, 8001, 8080, 3000, 5000, 4000)
PORT_MIN = 1
PORT_MAX = 65535


# ---------------------------------------------------------------------------
# Worker/connection limit defaults
# ---------------------------------------------------------------------------
CONNECTIONS_PER_GB = 800
SERVERLESS_MAX_CONNECTIONS = 100
DEVELOPMENT_MAX_CONNECTIONS = 1000
CONTAINER_MAX_CONNECTIONS = 5000
PRODUCTION_MAX_CONNECTIONS = 10000

# CPU-based worker thresholds
LOW_CORE_THRESHOLD = 2
MEDIUM_CORE_THRESHOLD = 4
HIGH_CORE_THRESHOLD = 16
CPU_UTILIZATION_FACTOR = 0.6
MAX_WORKERS_CAP = 8


# ---------------------------------------------------------------------------
# Project detection file names
# ---------------------------------------------------------------------------
PYTHON_PROJECT_FILES = ("pyproject.toml", "setup.py", "requirements.txt", "Pipfile")
NODE_PROJECT_FILES = ("package.json",)
RUST_PROJECT_FILES = ("Cargo.toml",)

# Composition config
DEFAULT_CONFIG_FILE = "config.yaml"
