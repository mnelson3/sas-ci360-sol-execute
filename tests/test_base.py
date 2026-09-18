#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for SAS CI360 Execute Module

Comprehensive test suite for the CI360ExecuteBase class and its APIs.
"""

import asyncio
import unittest
from unittest.mock import Mock, patch
from typing import Dict, Any

from sasci360solexecute.base import CI360ExecuteBase, CI360ExecuteConfig, CI360ExecuteError


class TestCI360ExecuteConfig(unittest.TestCase):
    """Test cases for CI360ExecuteConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CI360ExecuteConfig()
        self.assertEqual(config.algorithm, "HS256")
        self.assertEqual(config.api_base, "/marketingExecution")
        self.assertEqual(config.encoding, "utf-8")
        self.assertIsNone(config.host)
        self.assertIsNone(config.secret_key)
        self.assertIsNone(config.tenant_id)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.retry_backoff, 0.5)
        self.assertTrue(config.enable_compression)
        self.assertEqual(config.max_concurrent_jobs, 10)
        self.assertEqual(config.job_timeout, 3600)

    def test_custom_config(self):
        """Test custom configuration values."""
        config = CI360ExecuteConfig(
            host="https://api.example.com",
            secret_key="test-secret",
            tenant_id="test-tenant",
            timeout=60,
            max_concurrent_jobs=5
        )
        self.assertEqual(config.host, "https://api.example.com")
        self.assertEqual(config.secret_key, "test-secret")
        self.assertEqual(config.tenant_id, "test-tenant")
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.max_concurrent_jobs, 5)


class TestCI360ExecuteBase(unittest.TestCase):
    """Test cases for CI360ExecuteBase class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = CI360ExecuteConfig(
            host="https://api.example.com",
            secret_key="test-secret-key",
            tenant_id="test-tenant-id"
        )

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    def test_initialization_success(self, mock_encryption_class, mock_session_class):
        """Test successful initialization."""
        mock_encryption = Mock()
        mock_encryption.generate_jwt.return_value = "test-token"
        mock_encryption_class.return_value = mock_encryption

        mock_session = Mock()
        mock_session_class.return_value = mock_session

        client = CI360ExecuteBase(self.config)

        self.assertEqual(client.config, self.config)
        self.assertEqual(client.token, "test-token")

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_execute_campaign_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async campaign execution."""
        mock_request.return_value = {"executionId": "exec-123", "status": "running"}

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.execute_campaign_async("camp-123", {"priority": "high"}))

        self.assertEqual(result["executionId"], "exec-123")
        expected_payload = {"campaignId": "camp-123", "executionParams": {"priority": "high"}}
        mock_request.assert_called_once_with("POST", "/campaigns/execute", data=expected_payload)

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_get_execution_status_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async execution status retrieval."""
        mock_request.return_value = {"executionId": "exec-123", "status": "completed", "progress": 100}

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.get_execution_status_async("exec-123"))

        self.assertEqual(result["status"], "completed")
        mock_request.assert_called_once_with("GET", "/executions/exec-123")

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_cancel_execution_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async execution cancellation."""
        mock_request.return_value = None

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.cancel_execution_async("exec-123"))

        self.assertTrue(result)
        mock_request.assert_called_once_with("POST", "/executions/exec-123/cancel")

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_submit_batch_job_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async batch job submission."""
        job_data = {
            "name": "Customer Update Batch",
            "operations": [{"type": "update", "data": {"customerId": "123"}}]
        }
        mock_request.return_value = {"jobId": "job-123", "status": "queued"}

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.submit_batch_job_async(job_data))

        self.assertEqual(result["jobId"], "job-123")
        mock_request.assert_called_once_with("POST", "/batch/jobs", data=job_data)

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_get_batch_job_status_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async batch job status retrieval."""
        mock_request.return_value = {"jobId": "job-123", "status": "running", "progress": 45}

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.get_batch_job_status_async("job-123"))

        self.assertEqual(result["status"], "running")
        mock_request.assert_called_once_with("GET", "/batch/jobs/job-123")

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_cancel_batch_job_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async batch job cancellation."""
        mock_request.return_value = None

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.cancel_batch_job_async("job-123"))

        self.assertTrue(result)
        mock_request.assert_called_once_with("POST", "/batch/jobs/job-123/cancel")

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_get_batch_jobs_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async batch jobs listing."""
        mock_request.return_value = {"jobs": [], "total": 0}

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.get_batch_jobs_async(limit=25, offset=50, status_filter="completed"))

        self.assertEqual(result, {"jobs": [], "total": 0})
        expected_params = {"limit": 25, "offset": 50, "status": "completed"}
        mock_request.assert_called_once_with("GET", "/batch/jobs", params=expected_params)

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_schedule_job_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async job scheduling."""
        schedule_data = {
            "name": "Daily Customer Sync",
            "schedule": "0 2 * * *",  # Daily at 2 AM
            "jobType": "batch",
            "jobData": {"type": "sync"}
        }
        mock_request.return_value = {"scheduleId": "sched-123", "nextRun": "2025-12-14T02:00:00Z"}

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.schedule_job_async(schedule_data))

        self.assertEqual(result["scheduleId"], "sched-123")
        mock_request.assert_called_once_with("POST", "/schedules", data=schedule_data)

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_get_scheduled_jobs_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async scheduled jobs listing."""
        mock_request.return_value = {"schedules": [], "total": 0}

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.get_scheduled_jobs_async(limit=10, offset=20, active_only=False))

        self.assertEqual(result, {"schedules": [], "total": 0})
        expected_params = {"limit": 10, "offset": 20, "activeOnly": False}
        mock_request.assert_called_once_with("GET", "/schedules", params=expected_params)

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_update_schedule_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async schedule update."""
        update_data = {"schedule": "0 4 * * *"}  # Change to 4 AM
        mock_request.return_value = {"scheduleId": "sched-123", "schedule": "0 4 * * *"}

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.update_schedule_async("sched-123", update_data))

        self.assertEqual(result["schedule"], "0 4 * * *")
        mock_request.assert_called_once_with("PUT", "/schedules/sched-123", data=update_data)

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_delete_schedule_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async schedule deletion."""
        mock_request.return_value = None

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.delete_schedule_async("sched-123"))

        self.assertTrue(result)
        mock_request.assert_called_once_with("DELETE", "/schedules/sched-123")

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_get_execution_metrics_async(self, mock_request, mock_encryption_class, mock_session_class):
        """Test async execution metrics retrieval."""
        mock_request.return_value = {
            "totalExecutions": 150,
            "successfulExecutions": 145,
            "failedExecutions": 5,
            "averageExecutionTime": 45.2
        }

        client = CI360ExecuteBase(self.config)
        result = asyncio.run(client.get_execution_metrics_async(
            start_date="2025-12-01",
            end_date="2025-12-13",
            campaign_id="camp-123"
        ))

        self.assertEqual(result["totalExecutions"], 150)
        expected_params = {
            "startDate": "2025-12-01",
            "endDate": "2025-12-13",
            "campaignId": "camp-123"
        }
        mock_request.assert_called_once_with("GET", "/metrics/executions", params=expected_params)

    # Synchronous method tests

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_execute_campaign_sync(self, mock_request, mock_encryption_class, mock_session_class):
        """Test synchronous campaign execution."""
        mock_request.return_value = {"executionId": "exec-123", "status": "running"}

        client = CI360ExecuteBase(self.config)
        result = client.execute_campaign("camp-123")

        self.assertEqual(result["executionId"], "exec-123")

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_get_execution_status_sync(self, mock_request, mock_encryption_class, mock_session_class):
        """Test synchronous execution status retrieval."""
        mock_request.return_value = {"executionId": "exec-123", "status": "completed"}

        client = CI360ExecuteBase(self.config)
        result = client.get_execution_status("exec-123")

        self.assertEqual(result["status"], "completed")

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_submit_batch_job_sync(self, mock_request, mock_encryption_class, mock_session_class):
        """Test synchronous batch job submission."""
        job_data = {"name": "Test Batch Job"}
        mock_request.return_value = {"jobId": "job-123"}

        client = CI360ExecuteBase(self.config)
        result = client.submit_batch_job(job_data)

        self.assertEqual(result["jobId"], "job-123")


class TestCI360ExecuteErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = CI360ExecuteConfig(
            host="https://api.example.com",
            secret_key="test-secret-key",
            tenant_id="test-tenant-id"
        )

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_execution_error_handling(self, mock_request, mock_encryption_class, mock_session_class):
        """Test execution error handling."""
        from sasci360solexecute.base import CI360ExecuteConnectionError
        mock_request.side_effect = CI360ExecuteConnectionError("Execution failed")

        client = CI360ExecuteBase(self.config)

        with self.assertRaises(CI360ExecuteConnectionError):
            asyncio.run(client.execute_campaign_async("camp-123"))


if __name__ == '__main__':
    unittest.main()