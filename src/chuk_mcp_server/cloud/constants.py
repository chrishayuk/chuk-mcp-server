#!/usr/bin/env python3
"""
Cloud provider constants — environment variables, config keys, service types, and defaults.
"""

# ---------------------------------------------------------------------------
# Config dictionary keys (shared across all providers)
# ---------------------------------------------------------------------------
CFG_CLOUD_PROVIDER = "cloud_provider"
CFG_SERVICE_TYPE = "service_type"
CFG_REGION = "region"
CFG_PROJECT_ID = "project_id"
CFG_SUBSCRIPTION_ID = "subscription_id"
CFG_HOST = "host"
CFG_PORT = "port"
CFG_WORKERS = "workers"
CFG_MAX_CONNECTIONS = "max_connections"
CFG_LOG_LEVEL = "log_level"
CFG_DEBUG = "debug"
CFG_PERFORMANCE_MODE = "performance_mode"
CFG_TIMEOUT_SEC = "timeout_sec"
CFG_MEMORY_MB = "memory_mb"
CFG_FUNCTION_NAME = "function_name"
CFG_FUNCTION_VERSION = "function_version"
CFG_RUNTIME = "runtime"


# ---------------------------------------------------------------------------
# Environment type strings
# ---------------------------------------------------------------------------
ENV_TYPE_SERVERLESS = "serverless"
ENV_TYPE_PRODUCTION = "production"


# ---------------------------------------------------------------------------
# Provider identifiers
# ---------------------------------------------------------------------------
PROVIDER_AWS = "aws"
PROVIDER_GCP = "gcp"
PROVIDER_AZURE = "azure"
PROVIDER_VERCEL = "vercel"
PROVIDER_NETLIFY = "netlify"
PROVIDER_CLOUDFLARE = "cloudflare"

DISPLAY_AWS = "Amazon Web Services"
DISPLAY_GCP = "Google Cloud Platform"
DISPLAY_AZURE = "Microsoft Azure"
DISPLAY_VERCEL = "Vercel"
DISPLAY_NETLIFY = "Netlify"
DISPLAY_CLOUDFLARE = "Cloudflare Workers"


# ---------------------------------------------------------------------------
# Logging level config values
# ---------------------------------------------------------------------------
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Network defaults
# ---------------------------------------------------------------------------
DEFAULT_HOST = "0.0.0.0"
ENV_PORT = "PORT"

# Default ports per provider/service
DEFAULT_PORT_GENERAL = 8000
DEFAULT_PORT_GCP = 8080
DEFAULT_PORT_AZURE_FUNCTIONS = 7071
DEFAULT_PORT_VERCEL = 3000
DEFAULT_PORT_NETLIFY = 8888
DEFAULT_PORT_CLOUDFLARE = 8787


# ---------------------------------------------------------------------------
# AWS environment variables
# ---------------------------------------------------------------------------
AWS_LAMBDA_FUNCTION_NAME = "AWS_LAMBDA_FUNCTION_NAME"
AWS_EXECUTION_ENV = "AWS_EXECUTION_ENV"
AWS_REGION = "AWS_REGION"
AWS_DEFAULT_REGION = "AWS_DEFAULT_REGION"
AWS_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"
AWS_SESSION_TOKEN = "AWS_SESSION_TOKEN"
AWS_LAMBDA_RUNTIME_API = "AWS_LAMBDA_RUNTIME_API"
AWS_LAMBDA_FUNCTION_MEMORY_SIZE = "AWS_LAMBDA_FUNCTION_MEMORY_SIZE"
AWS_LAMBDA_FUNCTION_TIMEOUT = "AWS_LAMBDA_FUNCTION_TIMEOUT"
AWS_LAMBDA_FUNCTION_VERSION = "AWS_LAMBDA_FUNCTION_VERSION"
ECS_CONTAINER_METADATA_URI = "ECS_CONTAINER_METADATA_URI"
ECS_CONTAINER_METADATA_URI_V4 = "ECS_CONTAINER_METADATA_URI_V4"
AWS_BEANSTALK_APPLICATION_NAME = "AWS_BEANSTALK_APPLICATION_NAME"
AWS_BEANSTALK_ENVIRONMENT_NAME = "AWS_BEANSTALK_ENVIRONMENT_NAME"
AWS_BEANSTALK_VERSION_LABEL = "AWS_BEANSTALK_VERSION_LABEL"
AWS_ECS_FARGATE = "AWS_ECS_FARGATE"
AWS_DEFAULT_REGION_VALUE = "us-east-1"


# ---------------------------------------------------------------------------
# GCP environment variables
# ---------------------------------------------------------------------------
GCP_CLOUD_FUNCTION_NAME = "GOOGLE_CLOUD_FUNCTION_NAME"
GCP_FUNCTION_NAME = "FUNCTION_NAME"
GCP_FUNCTION_TARGET = "FUNCTION_TARGET"
GCP_FUNCTION_MEMORY_MB = "FUNCTION_MEMORY_MB"
GCP_FUNCTION_TIMEOUT_SEC = "FUNCTION_TIMEOUT_SEC"
GCP_FUNCTION_REGION = "FUNCTION_REGION"
GCP_K_SERVICE = "K_SERVICE"
GCP_K_CONFIGURATION = "K_CONFIGURATION"
GCP_K_REVISION = "K_REVISION"
GCP_GAE_APPLICATION = "GAE_APPLICATION"
GCP_GAE_DEPLOYMENT_ID = "GAE_DEPLOYMENT_ID"
GCP_GAE_ENV = "GAE_ENV"
GCP_GAE_INSTANCE = "GAE_INSTANCE"
GCP_GAE_MEMORY_MB = "GAE_MEMORY_MB"
GCP_GAE_RUNTIME = "GAE_RUNTIME"
GCP_GAE_SERVICE = "GAE_SERVICE"
GCP_GAE_VERSION = "GAE_VERSION"
GCP_GCE_METADATA_TIMEOUT = "GCE_METADATA_TIMEOUT"
GCP_CLOUD_PROJECT = "GOOGLE_CLOUD_PROJECT"
GCP_GCLOUD_PROJECT = "GCLOUD_PROJECT"
GCP_PROJECT = "GCP_PROJECT"
GCP_CLOUD_RUN_CPU = "CLOUD_RUN_CPU"
GCP_CLOUD_RUN_CONCURRENCY = "CLOUD_RUN_CONCURRENCY"
GCP_GAE_ENV_STANDARD = "standard"


# ---------------------------------------------------------------------------
# Azure environment variables
# ---------------------------------------------------------------------------
AZURE_FUNCTIONS_ENVIRONMENT = "AZURE_FUNCTIONS_ENVIRONMENT"
AZURE_WEBSITE_SITE_NAME = "WEBSITE_SITE_NAME"
AZURE_ACI_RESOURCE_GROUP = "ACI_RESOURCE_GROUP"
AZURE_WEBJOBS_SCRIPT_ROOT = "AzureWebJobsScriptRoot"
AZURE_WEBJOBS_STORAGE = "AzureWebJobsStorage"
AZURE_FUNCTIONS_WORKER_RUNTIME = "FUNCTIONS_WORKER_RUNTIME"
AZURE_FUNCTIONS_EXTENSION_VERSION = "FUNCTIONS_EXTENSION_VERSION"
AZURE_CLIENT_ID = "AZURE_CLIENT_ID"
AZURE_SUBSCRIPTION_ID = "AZURE_SUBSCRIPTION_ID"
AZURE_WEBSITE_RESOURCE_GROUP = "WEBSITE_RESOURCE_GROUP"
AZURE_WEBSITE_SKU = "WEBSITE_SKU"
AZURE_WEBSITE_INSTANCE_ID = "WEBSITE_INSTANCE_ID"
AZURE_DEFAULT_RUNTIME = "python"


# ---------------------------------------------------------------------------
# Edge platform environment variables
# ---------------------------------------------------------------------------
VERCEL_ENV_FLAG = "VERCEL"
VERCEL_ENV = "VERCEL_ENV"
VERCEL_URL = "VERCEL_URL"
VERCEL_REGION = "VERCEL_REGION"
VERCEL_GIT_COMMIT_SHA = "VERCEL_GIT_COMMIT_SHA"

NETLIFY_ENV_FLAG = "NETLIFY"
NETLIFY_DEV = "NETLIFY_DEV"
NETLIFY_SITE_ID = "SITE_ID"
NETLIFY_DEPLOY_ID = "DEPLOY_ID"
NETLIFY_CONTEXT = "CONTEXT"
NETLIFY_BRANCH = "BRANCH"
NETLIFY_COMMIT_REF = "COMMIT_REF"

CF_PAGES = "CF_PAGES"
CF_PAGES_COMMIT_SHA = "CF_PAGES_COMMIT_SHA"
CF_PAGES_BRANCH = "CF_PAGES_BRANCH"
CF_ACCOUNT_ID = "CLOUDFLARE_ACCOUNT_ID"
CF_API_TOKEN = "CLOUDFLARE_API_TOKEN"


# ---------------------------------------------------------------------------
# AWS service types
# ---------------------------------------------------------------------------
SVC_LAMBDA_ARM64 = "lambda_arm64"
SVC_LAMBDA_X86 = "lambda_x86"
SVC_FARGATE = "fargate"
SVC_ELASTIC_BEANSTALK = "elastic_beanstalk"
SVC_EC2 = "ec2"
SVC_AWS_GENERIC = "aws_generic"

# AWS performance modes
PERF_LAMBDA_HIGH_MEMORY = "lambda_high_memory"
PERF_LAMBDA_STANDARD = "lambda_standard"
PERF_LAMBDA_MINIMAL = "lambda_minimal"
PERF_FARGATE_OPTIMIZED = "fargate_optimized"
PERF_BEANSTALK_OPTIMIZED = "beanstalk_optimized"
PERF_EC2_OPTIMIZED = "ec2_optimized"


# ---------------------------------------------------------------------------
# GCP service types
# ---------------------------------------------------------------------------
SVC_GCF_GEN1 = "gcf_gen1"
SVC_GCF_GEN2 = "gcf_gen2"
SVC_CLOUD_RUN = "cloud_run"
SVC_GAE_STANDARD = "gae_standard"
SVC_GAE_FLEXIBLE = "gae_flexible"
SVC_GCE = "gce"
SVC_GCP_GENERIC = "gcp_generic"

# GCP performance modes
PERF_GCF_HIGH_MEMORY = "gcf_high_memory"
PERF_GCF_STANDARD = "gcf_standard"
PERF_GCF_MINIMAL = "gcf_minimal"
PERF_CLOUD_RUN_OPTIMIZED = "cloud_run_optimized"
PERF_APP_ENGINE_OPTIMIZED = "app_engine_optimized"
PERF_GCE_OPTIMIZED = "gce_optimized"


# ---------------------------------------------------------------------------
# Azure service types
# ---------------------------------------------------------------------------
SVC_AZURE_FUNCTIONS = "azure_functions"
SVC_APP_SERVICE = "app_service"
SVC_CONTAINER_INSTANCES = "container_instances"
SVC_AZURE_GENERIC = "azure_generic"

# Azure performance modes
PERF_AZURE_FUNCTIONS_OPTIMIZED = "azure_functions_optimized"
PERF_APP_SERVICE_OPTIMIZED = "app_service_optimized"
PERF_ACI_OPTIMIZED = "aci_optimized"


# ---------------------------------------------------------------------------
# Edge service types
# ---------------------------------------------------------------------------
SVC_VERCEL_PRODUCTION = "vercel_production"
SVC_VERCEL_PREVIEW = "vercel_preview"
SVC_NETLIFY_PRODUCTION = "netlify_production"
SVC_NETLIFY_PREVIEW = "netlify_preview"
SVC_NETLIFY_DEV = "netlify_dev"
SVC_CLOUDFLARE_PAGES = "cloudflare_pages"
SVC_CLOUDFLARE_WORKERS = "cloudflare_workers"

# Edge performance modes
PERF_VERCEL_OPTIMIZED = "vercel_optimized"
PERF_NETLIFY_OPTIMIZED = "netlify_optimized"
PERF_CLOUDFLARE_OPTIMIZED = "cloudflare_optimized"

# Netlify context values
NETLIFY_CTX_PRODUCTION = "production"
NETLIFY_CTX_DEPLOY_PREVIEW = "deploy-preview"


# ---------------------------------------------------------------------------
# Memory thresholds (MB)
# ---------------------------------------------------------------------------
MEMORY_HIGH_THRESHOLD = 2048
MEMORY_MEDIUM_THRESHOLD = 1024
LAMBDA_MAX_MEMORY = 3008
DEFAULT_FUNCTION_MEMORY = 512
DEFAULT_FUNCTION_TIMEOUT = 60
