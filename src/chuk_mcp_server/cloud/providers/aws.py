#!/usr/bin/env python3
# src/chuk_mcp_server/cloud/providers/aws.py
"""
Amazon Web Services Provider

Detects and configures for AWS services including:
- AWS Lambda
- AWS Fargate
- AWS EC2
- AWS Elastic Beanstalk
"""

import os
from typing import Any

from ..base import CloudProvider
from ..constants import (
    AWS_ACCESS_KEY_ID,
    AWS_BEANSTALK_APPLICATION_NAME,
    AWS_BEANSTALK_ENVIRONMENT_NAME,
    AWS_BEANSTALK_VERSION_LABEL,
    AWS_DEFAULT_REGION,
    AWS_DEFAULT_REGION_VALUE,
    AWS_ECS_FARGATE,
    AWS_EXECUTION_ENV,
    AWS_LAMBDA_FUNCTION_MEMORY_SIZE,
    AWS_LAMBDA_FUNCTION_NAME,
    AWS_LAMBDA_FUNCTION_TIMEOUT,
    AWS_LAMBDA_FUNCTION_VERSION,
    AWS_LAMBDA_RUNTIME_API,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    AWS_SESSION_TOKEN,
    CFG_CLOUD_PROVIDER,
    CFG_DEBUG,
    CFG_FUNCTION_NAME,
    CFG_FUNCTION_VERSION,
    CFG_HOST,
    CFG_LOG_LEVEL,
    CFG_MAX_CONNECTIONS,
    CFG_MEMORY_MB,
    CFG_PERFORMANCE_MODE,
    CFG_PORT,
    CFG_REGION,
    CFG_RUNTIME,
    CFG_SERVICE_TYPE,
    CFG_TIMEOUT_SEC,
    CFG_WORKERS,
    DEFAULT_HOST,
    DEFAULT_PORT_GENERAL,
    DISPLAY_AWS,
    ECS_CONTAINER_METADATA_URI,
    ECS_CONTAINER_METADATA_URI_V4,
    ENV_PORT,
    ENV_TYPE_PRODUCTION,
    ENV_TYPE_SERVERLESS,
    LAMBDA_MAX_MEMORY,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    MEMORY_MEDIUM_THRESHOLD,
    PERF_BEANSTALK_OPTIMIZED,
    PERF_EC2_OPTIMIZED,
    PERF_FARGATE_OPTIMIZED,
    PERF_LAMBDA_HIGH_MEMORY,
    PERF_LAMBDA_MINIMAL,
    PERF_LAMBDA_STANDARD,
    PROVIDER_AWS,
    SVC_AWS_GENERIC,
    SVC_EC2,
    SVC_ELASTIC_BEANSTALK,
    SVC_FARGATE,
    SVC_LAMBDA_ARM64,
    SVC_LAMBDA_X86,
)


class AWSProvider(CloudProvider):
    """Amazon Web Services detection and configuration."""

    @property
    def name(self) -> str:
        return PROVIDER_AWS

    @property
    def display_name(self) -> str:
        return DISPLAY_AWS

    def get_priority(self) -> int:
        return 20

    def detect(self) -> bool:
        """Detect if running on Amazon Web Services."""
        # Strong indicators (definitive AWS)
        strong_indicators = [
            AWS_LAMBDA_FUNCTION_NAME,
            AWS_EXECUTION_ENV,
            ECS_CONTAINER_METADATA_URI,
            AWS_BEANSTALK_APPLICATION_NAME,
        ]

        # Check strong indicators first
        if any(os.environ.get(var) for var in strong_indicators):
            return True

        # Weaker indicators (need multiple matches)
        weak_indicators = [
            AWS_REGION,
            AWS_DEFAULT_REGION,
            AWS_ACCESS_KEY_ID,
            AWS_SECRET_ACCESS_KEY,
            AWS_SESSION_TOKEN,
        ]
        weak_matches = sum(1 for var in weak_indicators if os.environ.get(var))
        return weak_matches >= 2

    def get_environment_type(self) -> str:
        """Determine specific AWS service type."""
        if self._is_lambda() or self._is_fargate():
            return ENV_TYPE_SERVERLESS
        elif self._is_elastic_beanstalk() or self._is_ec2():
            return ENV_TYPE_PRODUCTION
        else:
            return ENV_TYPE_PRODUCTION  # Generic AWS

    def get_service_type(self) -> str:
        """Get specific AWS service type."""
        if self._is_lambda():
            runtime = os.environ.get(AWS_LAMBDA_RUNTIME_API, "")
            if "arm64" in runtime:
                return SVC_LAMBDA_ARM64
            else:
                return SVC_LAMBDA_X86
        elif self._is_fargate():
            return SVC_FARGATE
        elif self._is_elastic_beanstalk():
            return SVC_ELASTIC_BEANSTALK
        elif self._is_ec2():
            return SVC_EC2
        else:
            return SVC_AWS_GENERIC

    def get_config_overrides(self) -> dict[str, Any]:
        """Get AWS-specific configuration overrides."""
        service_type = self.get_service_type()

        base_config = {
            CFG_CLOUD_PROVIDER: PROVIDER_AWS,
            CFG_SERVICE_TYPE: service_type,
            CFG_REGION: self._get_region(),
        }

        if service_type.startswith("lambda_"):
            return {**base_config, **self._get_lambda_config()}
        elif service_type == SVC_FARGATE:
            return {**base_config, **self._get_fargate_config()}
        elif service_type == SVC_ELASTIC_BEANSTALK:
            return {**base_config, **self._get_beanstalk_config()}
        elif service_type == SVC_EC2:
            return {**base_config, **self._get_ec2_config()}
        else:
            return base_config

    def _is_lambda(self) -> bool:
        """Check if running in AWS Lambda."""
        return bool(os.environ.get(AWS_LAMBDA_FUNCTION_NAME))

    def _is_fargate(self) -> bool:
        """Check if running in AWS Fargate."""
        execution_env = os.environ.get(AWS_EXECUTION_ENV, "")
        return AWS_ECS_FARGATE in execution_env or bool(os.environ.get(ECS_CONTAINER_METADATA_URI))

    def _is_elastic_beanstalk(self) -> bool:
        """Check if running in Elastic Beanstalk."""
        return bool(os.environ.get(AWS_BEANSTALK_APPLICATION_NAME))

    def _is_ec2(self) -> bool:
        """Check if running in EC2."""
        # This is harder to detect definitively
        return bool(
            os.environ.get(AWS_REGION)
            and not self._is_lambda()
            and not self._is_fargate()
            and not self._is_elastic_beanstalk()
        )

    def _get_region(self) -> str:
        """Get AWS region."""
        return os.environ.get(AWS_REGION) or os.environ.get(AWS_DEFAULT_REGION) or AWS_DEFAULT_REGION_VALUE

    def _get_lambda_config(self) -> dict[str, Any]:
        """Get Lambda specific configuration."""
        memory_mb = int(os.environ.get(AWS_LAMBDA_FUNCTION_MEMORY_SIZE, 128))

        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for AWS Lambda runtime
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_GENERAL)),
            CFG_WORKERS: 1,  # Lambda is single-threaded per instance
            CFG_MAX_CONNECTIONS: min(memory_mb // 10, 1000),  # ~1 connection per 10MB
            CFG_LOG_LEVEL: LOG_LEVEL_WARNING,  # Optimized for cold start
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: self._get_lambda_performance_mode(),
            CFG_TIMEOUT_SEC: int(os.environ.get(AWS_LAMBDA_FUNCTION_TIMEOUT, 900)),
            CFG_MEMORY_MB: memory_mb,
            CFG_FUNCTION_NAME: os.environ.get(AWS_LAMBDA_FUNCTION_NAME, "unknown"),
            CFG_FUNCTION_VERSION: os.environ.get(AWS_LAMBDA_FUNCTION_VERSION, "$LATEST"),
            CFG_RUNTIME: os.environ.get(AWS_LAMBDA_RUNTIME_API, "unknown"),
        }

    def _get_fargate_config(self) -> dict[str, Any]:
        """Get Fargate specific configuration."""
        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for AWS Fargate load balancer
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_GENERAL)),
            CFG_WORKERS: 4,  # Will be optimized by system detector
            CFG_MAX_CONNECTIONS: 2000,
            CFG_LOG_LEVEL: LOG_LEVEL_INFO,
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_FARGATE_OPTIMIZED,
            "task_arn": os.environ.get(ECS_CONTAINER_METADATA_URI_V4, ""),
        }

    def _get_beanstalk_config(self) -> dict[str, Any]:
        """Get Elastic Beanstalk specific configuration."""
        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for AWS Elastic Beanstalk load balancer
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_GENERAL)),
            CFG_WORKERS: 4,  # Will be optimized by system detector
            CFG_MAX_CONNECTIONS: 3000,
            CFG_LOG_LEVEL: LOG_LEVEL_INFO,
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_BEANSTALK_OPTIMIZED,
            "application_name": os.environ.get(AWS_BEANSTALK_APPLICATION_NAME, "unknown"),
            "environment_name": os.environ.get(AWS_BEANSTALK_ENVIRONMENT_NAME, "unknown"),
            "version_label": os.environ.get(AWS_BEANSTALK_VERSION_LABEL, "unknown"),
        }

    def _get_ec2_config(self) -> dict[str, Any]:
        """Get EC2 specific configuration."""
        return {
            CFG_HOST: DEFAULT_HOST,  # nosec B104 - Required for AWS EC2 load balancer
            CFG_PORT: int(os.environ.get(ENV_PORT, DEFAULT_PORT_GENERAL)),
            CFG_WORKERS: 4,  # Will be optimized by system detector
            CFG_MAX_CONNECTIONS: 5000,
            CFG_LOG_LEVEL: LOG_LEVEL_INFO,
            CFG_DEBUG: False,
            CFG_PERFORMANCE_MODE: PERF_EC2_OPTIMIZED,
        }

    def _get_lambda_performance_mode(self) -> str:
        """Get Lambda performance mode based on memory."""
        memory_mb = int(os.environ.get(AWS_LAMBDA_FUNCTION_MEMORY_SIZE, 128))

        if memory_mb >= LAMBDA_MAX_MEMORY:  # Max Lambda memory
            return PERF_LAMBDA_HIGH_MEMORY
        elif memory_mb >= MEMORY_MEDIUM_THRESHOLD:  # 1GB+
            return PERF_LAMBDA_STANDARD
        else:  # < 1GB
            return PERF_LAMBDA_MINIMAL


# Manual registration function (called by providers/__init__.py)
def register_aws_provider(registry: Any) -> None:
    """Register AWS provider with the registry."""
    aws_provider = AWSProvider()
    registry.register_provider(aws_provider)
