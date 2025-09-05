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


class AWSProvider(CloudProvider):
    """Amazon Web Services detection and configuration."""

    @property
    def name(self) -> str:
        return "aws"

    @property
    def display_name(self) -> str:
        return "Amazon Web Services"

    def get_priority(self) -> int:
        return 20

    def detect(self) -> bool:
        """Detect if running on Amazon Web Services."""
        # Strong indicators (definitive AWS)
        strong_indicators = [
            "AWS_LAMBDA_FUNCTION_NAME",
            "AWS_EXECUTION_ENV",
            "ECS_CONTAINER_METADATA_URI",
            "AWS_BEANSTALK_APPLICATION_NAME",
        ]

        # Check strong indicators first
        if any(os.environ.get(var) for var in strong_indicators):
            return True

        # Weaker indicators (need multiple matches)
        weak_indicators = [
            "AWS_REGION",
            "AWS_DEFAULT_REGION",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
        ]
        weak_matches = sum(1 for var in weak_indicators if os.environ.get(var))
        return weak_matches >= 2

    def get_environment_type(self) -> str:
        """Determine specific AWS service type."""
        if self._is_lambda() or self._is_fargate():
            return "serverless"
        elif self._is_elastic_beanstalk() or self._is_ec2():
            return "production"
        else:
            return "production"  # Generic AWS

    def get_service_type(self) -> str:
        """Get specific AWS service type."""
        if self._is_lambda():
            runtime = os.environ.get("AWS_LAMBDA_RUNTIME_API", "")
            if "arm64" in runtime:
                return "lambda_arm64"
            else:
                return "lambda_x86"
        elif self._is_fargate():
            return "fargate"
        elif self._is_elastic_beanstalk():
            return "elastic_beanstalk"
        elif self._is_ec2():
            return "ec2"
        else:
            return "aws_generic"

    def get_config_overrides(self) -> dict[str, Any]:
        """Get AWS-specific configuration overrides."""
        service_type = self.get_service_type()

        base_config = {
            "cloud_provider": "aws",
            "service_type": service_type,
            "region": self._get_region(),
        }

        if service_type.startswith("lambda_"):
            return {**base_config, **self._get_lambda_config()}
        elif service_type == "fargate":
            return {**base_config, **self._get_fargate_config()}
        elif service_type == "elastic_beanstalk":
            return {**base_config, **self._get_beanstalk_config()}
        elif service_type == "ec2":
            return {**base_config, **self._get_ec2_config()}
        else:
            return base_config

    def _is_lambda(self) -> bool:
        """Check if running in AWS Lambda."""
        return bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

    def _is_fargate(self) -> bool:
        """Check if running in AWS Fargate."""
        execution_env = os.environ.get("AWS_EXECUTION_ENV", "")
        return "AWS_ECS_FARGATE" in execution_env or bool(os.environ.get("ECS_CONTAINER_METADATA_URI"))

    def _is_elastic_beanstalk(self) -> bool:
        """Check if running in Elastic Beanstalk."""
        return bool(os.environ.get("AWS_BEANSTALK_APPLICATION_NAME"))

    def _is_ec2(self) -> bool:
        """Check if running in EC2."""
        # This is harder to detect definitively
        return bool(
            os.environ.get("AWS_REGION")
            and not self._is_lambda()
            and not self._is_fargate()
            and not self._is_elastic_beanstalk()
        )

    def _get_region(self) -> str:
        """Get AWS region."""
        return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"

    def _get_lambda_config(self) -> dict[str, Any]:
        """Get Lambda specific configuration."""
        memory_mb = int(os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", 128))

        return {
            "host": "0.0.0.0",
            "port": int(os.environ.get("PORT", 8000)),
            "workers": 1,  # Lambda is single-threaded per instance
            "max_connections": min(memory_mb // 10, 1000),  # ~1 connection per 10MB
            "log_level": "WARNING",  # Optimized for cold start
            "debug": False,
            "performance_mode": self._get_lambda_performance_mode(),
            "timeout_sec": int(os.environ.get("AWS_LAMBDA_FUNCTION_TIMEOUT", 900)),
            "memory_mb": memory_mb,
            "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
            "function_version": os.environ.get("AWS_LAMBDA_FUNCTION_VERSION", "$LATEST"),
            "runtime": os.environ.get("AWS_LAMBDA_RUNTIME_API", "unknown"),
        }

    def _get_fargate_config(self) -> dict[str, Any]:
        """Get Fargate specific configuration."""
        return {
            "host": "0.0.0.0",
            "port": int(os.environ.get("PORT", 8000)),
            "workers": 4,  # Will be optimized by system detector
            "max_connections": 2000,
            "log_level": "INFO",
            "debug": False,
            "performance_mode": "fargate_optimized",
            "task_arn": os.environ.get("ECS_CONTAINER_METADATA_URI_V4", ""),
        }

    def _get_beanstalk_config(self) -> dict[str, Any]:
        """Get Elastic Beanstalk specific configuration."""
        return {
            "host": "0.0.0.0",
            "port": int(os.environ.get("PORT", 8000)),
            "workers": 4,  # Will be optimized by system detector
            "max_connections": 3000,
            "log_level": "INFO",
            "debug": False,
            "performance_mode": "beanstalk_optimized",
            "application_name": os.environ.get("AWS_BEANSTALK_APPLICATION_NAME", "unknown"),
            "environment_name": os.environ.get("AWS_BEANSTALK_ENVIRONMENT_NAME", "unknown"),
            "version_label": os.environ.get("AWS_BEANSTALK_VERSION_LABEL", "unknown"),
        }

    def _get_ec2_config(self) -> dict[str, Any]:
        """Get EC2 specific configuration."""
        return {
            "host": "0.0.0.0",
            "port": int(os.environ.get("PORT", 8000)),
            "workers": 4,  # Will be optimized by system detector
            "max_connections": 5000,
            "log_level": "INFO",
            "debug": False,
            "performance_mode": "ec2_optimized",
        }

    def _get_lambda_performance_mode(self) -> str:
        """Get Lambda performance mode based on memory."""
        memory_mb = int(os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", 128))

        if memory_mb >= 3008:  # Max Lambda memory
            return "lambda_high_memory"
        elif memory_mb >= 1024:  # 1GB+
            return "lambda_standard"
        else:  # < 1GB
            return "lambda_minimal"
