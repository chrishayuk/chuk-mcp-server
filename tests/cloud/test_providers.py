#!/usr/bin/env python3
"""Tests for cloud providers."""

import os
from unittest.mock import patch

from chuk_mcp_server.cloud.providers.aws import AWSProvider
from chuk_mcp_server.cloud.providers.azure import AzureProvider
from chuk_mcp_server.cloud.providers.edge import CloudflareProvider, NetlifyProvider, VercelProvider
from chuk_mcp_server.cloud.providers.gcp import GCPProvider


class TestAWSProvider:
    """Test AWS Provider."""

    def test_aws_provider_attributes(self):
        """Test AWS provider attributes."""
        provider = AWSProvider()
        assert provider.name == "aws"
        assert provider.display_name == "Amazon Web Services"

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test-function"})
    def test_detect_lambda_function_name(self):
        """Test detection via AWS_LAMBDA_FUNCTION_NAME."""
        provider = AWSProvider()
        assert provider.detect() is True

    @patch.dict(os.environ, {"AWS_EXECUTION_ENV": "AWS_Lambda_python3.8"})
    def test_detect_execution_env(self):
        """Test detection via AWS_EXECUTION_ENV."""
        provider = AWSProvider()
        assert provider.detect() is True

    @patch.dict(os.environ, {"AWS_REGION": "us-east-1", "AWS_DEFAULT_REGION": "us-east-1"})
    def test_detect_weak_indicators(self):
        """Test detection via multiple weak indicators."""
        provider = AWSProvider()
        assert provider.detect() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_no_aws_env(self):
        """Test no detection when AWS env vars are missing."""
        provider = AWSProvider()
        assert provider.detect() is False

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test-func", "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "512"})
    def test_get_config_overrides_lambda(self):
        """Test config overrides for Lambda."""
        provider = AWSProvider()
        config = provider.get_config_overrides()

        assert config["host"] == "0.0.0.0"
        assert config["port"] == 8000
        assert config["workers"] == 1
        assert config["cloud_provider"] == "aws"

    @patch.dict(os.environ, {"ECS_CONTAINER_METADATA_URI": "http://169.254.170.2/v3"})
    def test_get_config_overrides_fargate(self):
        """Test config overrides for Fargate."""
        provider = AWSProvider()
        config = provider.get_config_overrides()

        assert config["host"] == "0.0.0.0"
        assert config["port"] == 8000
        assert config["workers"] == 4

    @patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test"})
    def test_get_service_type_lambda(self):
        """Test service type for Lambda."""
        provider = AWSProvider()
        assert provider.get_service_type() == "lambda_x86"

    @patch.dict(os.environ, {"ECS_CONTAINER_METADATA_URI": "http://test"})
    def test_get_service_type_fargate(self):
        """Test service type for Fargate."""
        provider = AWSProvider()
        assert provider.get_service_type() == "fargate"

    def test_get_environment_type(self):
        """Test environment type."""
        provider = AWSProvider()
        # Without any indicators, it defaults to production
        assert provider.get_environment_type() == "production"

        # Test with Lambda indicator
        with patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test"}):
            assert provider.get_environment_type() == "serverless"

    def test_is_lambda(self):
        """Test Lambda environment detection."""
        provider = AWSProvider()

        with patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "test"}):
            assert provider._is_lambda() is True

        with patch.dict(os.environ, {}, clear=True):
            assert provider._is_lambda() is False

    def test_is_fargate(self):
        """Test Fargate environment detection."""
        provider = AWSProvider()

        with patch.dict(os.environ, {"ECS_CONTAINER_METADATA_URI": "http://test"}):
            assert provider._is_fargate() is True

        with patch.dict(os.environ, {"AWS_EXECUTION_ENV": "AWS_ECS_FARGATE"}):
            assert provider._is_fargate() is True

        with patch.dict(os.environ, {}, clear=True):
            assert provider._is_fargate() is False

    @patch.dict(os.environ, {"AWS_BEANSTALK_APPLICATION_NAME": "test-app"})
    def test_is_elastic_beanstalk(self):
        """Test Elastic Beanstalk detection."""
        provider = AWSProvider()
        assert provider._is_elastic_beanstalk() is True


class TestGCPProvider:
    """Test GCP Provider."""

    def test_gcp_provider_attributes(self):
        """Test GCP provider attributes."""
        provider = GCPProvider()
        assert provider.name == "gcp"
        assert provider.display_name == "Google Cloud Platform"

    @patch.dict(os.environ, {"K_SERVICE": "test-service"})
    def test_detect_cloud_run(self):
        """Test detection via K_SERVICE (Cloud Run)."""
        provider = GCPProvider()
        assert provider.detect() is True

    @patch.dict(os.environ, {"FUNCTION_NAME": "test-function"})
    def test_detect_cloud_functions(self):
        """Test detection via FUNCTION_NAME."""
        provider = GCPProvider()
        assert provider.detect() is True

    @patch.dict(os.environ, {"GAE_SERVICE": "default"})
    def test_detect_app_engine(self):
        """Test detection via GAE_SERVICE."""
        provider = GCPProvider()
        assert provider.detect() is True

    @patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"})
    def test_detect_google_cloud_project(self):
        """Test detection via GOOGLE_CLOUD_PROJECT."""
        provider = GCPProvider()
        assert provider.detect() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_no_gcp_env(self):
        """Test no detection when GCP env vars are missing."""
        provider = GCPProvider()
        assert provider.detect() is False

    @patch.dict(os.environ, {"FUNCTION_NAME": "test-func"})
    def test_get_config_overrides(self):
        """Test config overrides."""
        provider = GCPProvider()
        config = provider.get_config_overrides()

        assert config["cloud_provider"] == "gcp"
        assert "project_id" in config
        assert "host" in config

    @patch.dict(os.environ, {"FUNCTION_NAME": "test"})
    def test_get_service_type_functions(self):
        """Test service type for Cloud Functions."""
        provider = GCPProvider()
        assert provider.get_service_type() == "gcf_gen2"

    @patch.dict(os.environ, {"K_SERVICE": "test"})
    def test_get_service_type_cloud_run(self):
        """Test service type for Cloud Run."""
        provider = GCPProvider()
        assert provider.get_service_type() == "cloud_run"

    @patch.dict(os.environ, {"GAE_APPLICATION": "test", "GAE_ENV": "standard"})
    def test_get_service_type_app_engine(self):
        """Test service type for App Engine."""
        provider = GCPProvider()
        assert provider.get_service_type() == "gae_standard"

    def test_get_environment_type(self):
        """Test environment type."""
        provider = GCPProvider()

        with patch.dict(os.environ, {"FUNCTION_NAME": "test"}):
            assert provider.get_environment_type() == "serverless"

        with patch.dict(os.environ, {"GCE_METADATA_TIMEOUT": "1"}, clear=True):
            assert provider.get_environment_type() == "production"

    def test_is_cloud_functions(self):
        """Test Cloud Functions detection."""
        provider = GCPProvider()

        with patch.dict(os.environ, {"FUNCTION_NAME": "test"}):
            assert provider._is_cloud_functions() is True

        with patch.dict(os.environ, {"GOOGLE_CLOUD_FUNCTION_NAME": "test"}):
            assert provider._is_cloud_functions() is True

        with patch.dict(os.environ, {}, clear=True):
            assert provider._is_cloud_functions() is False

    def test_is_cloud_run(self):
        """Test Cloud Run detection."""
        provider = GCPProvider()

        with patch.dict(os.environ, {"K_SERVICE": "test"}):
            assert provider._is_cloud_run() is True

        with patch.dict(os.environ, {}, clear=True):
            assert provider._is_cloud_run() is False


class TestAzureProvider:
    """Test Azure Provider."""

    def test_azure_provider_attributes(self):
        """Test Azure provider attributes."""
        provider = AzureProvider()
        assert provider.name == "azure"
        assert provider.display_name == "Microsoft Azure"

    @patch.dict(os.environ, {"AZURE_FUNCTIONS_ENVIRONMENT": "Development"})
    def test_detect_functions_environment(self):
        """Test detection via AZURE_FUNCTIONS_ENVIRONMENT."""
        provider = AzureProvider()
        assert provider.detect() is True

    @patch.dict(os.environ, {"WEBSITE_SITE_NAME": "test-site"})
    def test_detect_website_name(self):
        """Test detection via WEBSITE_SITE_NAME."""
        provider = AzureProvider()
        assert provider.detect() is True

    @patch.dict(
        os.environ,
        {"AzureWebJobsScriptRoot": "/home/site/wwwroot", "AzureWebJobsStorage": "UseDevelopmentStorage=true"},
    )
    def test_detect_weak_indicators(self):
        """Test detection via multiple weak indicators."""
        provider = AzureProvider()
        assert provider.detect() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_no_azure_env(self):
        """Test no detection when Azure env vars are missing."""
        provider = AzureProvider()
        assert provider.detect() is False

    @patch.dict(os.environ, {"AZURE_FUNCTIONS_ENVIRONMENT": "Development"})
    def test_get_config_overrides(self):
        """Test config overrides."""
        provider = AzureProvider()
        config = provider.get_config_overrides()

        assert config["cloud_provider"] == "azure"
        assert "service_type" in config
        assert "subscription_id" in config

    @patch.dict(os.environ, {"AZURE_FUNCTIONS_ENVIRONMENT": "Development", "FUNCTIONS_WORKER_RUNTIME": "python"})
    def test_get_service_type_functions(self):
        """Test service type for Functions."""
        provider = AzureProvider()
        assert provider.get_service_type() == "azure_functions_python"

    @patch.dict(os.environ, {"ACI_RESOURCE_GROUP": "test-group"})
    def test_get_service_type_container(self):
        """Test service type for Container Instances."""
        provider = AzureProvider()
        assert provider.get_service_type() == "container_instances"

    def test_get_environment_type(self):
        """Test environment type."""
        provider = AzureProvider()

        with patch.dict(os.environ, {"AZURE_FUNCTIONS_ENVIRONMENT": "Development"}):
            assert provider.get_environment_type() == "serverless"

        with patch.dict(os.environ, {"WEBSITE_SITE_NAME": "test"}, clear=True):
            assert provider.get_environment_type() == "production"


class TestEdgeProviders:
    """Test Edge providers (Vercel, Netlify, Cloudflare)."""

    def test_vercel_provider(self):
        """Test Vercel provider."""
        provider = VercelProvider()
        assert provider.name == "vercel"
        assert provider.display_name == "Vercel"

        with patch.dict(os.environ, {"VERCEL": "1"}):
            assert provider.detect() is True

        with patch.dict(os.environ, {}, clear=True):
            assert provider.detect() is False

        config = provider.get_config_overrides()
        assert config["port"] == 3000
        assert provider.get_service_type() == "vercel_preview"
        assert provider.get_environment_type() == "serverless"

    def test_netlify_provider(self):
        """Test Netlify provider."""
        provider = NetlifyProvider()
        assert provider.name == "netlify"
        assert provider.display_name == "Netlify"

        with patch.dict(os.environ, {"NETLIFY": "true"}):
            assert provider.detect() is True

        with patch.dict(os.environ, {}, clear=True):
            assert provider.detect() is False

        config = provider.get_config_overrides()
        assert config["port"] == 8888
        assert provider.get_service_type() == "netlify_dev"
        assert provider.get_environment_type() == "serverless"

    def test_cloudflare_provider(self):
        """Test Cloudflare provider."""
        provider = CloudflareProvider()
        assert provider.name == "cloudflare"
        assert provider.display_name == "Cloudflare Workers"

        with patch.dict(os.environ, {"CF_PAGES": "1"}):
            assert provider.detect() is True

        with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "test-id"}):
            assert provider.detect() is True

        with patch.dict(os.environ, {}, clear=True):
            assert provider.detect() is False

        config = provider.get_config_overrides()
        assert config["port"] == 8787
        assert provider.get_service_type() == "cloudflare_workers"
        assert provider.get_environment_type() == "serverless"

    def test_vercel_service_types(self):
        """Test Vercel service type detection."""
        provider = VercelProvider()

        with patch.dict(os.environ, {"VERCEL_ENV": "production"}):
            assert provider.get_service_type() == "vercel_production"

        with patch.dict(os.environ, {"VERCEL_ENV": "preview"}):
            assert provider.get_service_type() == "vercel_preview"

    def test_netlify_service_types(self):
        """Test Netlify service type detection."""
        provider = NetlifyProvider()

        with patch.dict(os.environ, {"CONTEXT": "production"}):
            assert provider.get_service_type() == "netlify_production"

        with patch.dict(os.environ, {"CONTEXT": "deploy-preview"}):
            assert provider.get_service_type() == "netlify_preview"
