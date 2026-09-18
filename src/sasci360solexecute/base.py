#!/usr/bin/env python3
#
# Copyright (c) 2025 Nelson Grey LLC
# Author: Nelson Grey LLC
#
# Licensed under the Nelson Grey LLC Community License 1.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# https://github.com/mnelson3/sas-ci360-sol-execute/blob/main/LICENSE
#
# -*- coding: utf-8 -*-
"""
SAS CI360 Execute Module Base Class

Provides foundational functionality for SAS Customer Intelligence 360
campaign execution operations, including connection management, authentication,
and campaign execution capabilities.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from sasci360apicore.encryption import Encryption
except ImportError:
    Encryption = None


@dataclass
class CI360ExecuteConfig:
    """Configuration for CI360 Execute operations."""

    algorithm: str = "HS256"
    api_base: str = "/marketingExecution"
    encoding: str = "utf-8"
    host: Optional[str] = None
    secret_key: Optional[str] = None
    tenant_id: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_backoff: float = 0.5
    enable_compression: bool = True
    batch_size: int = 1000
    max_concurrent_jobs: int = 10
    job_timeout: int = 3600


class CI360ExecuteError(Exception):
    """Base exception for CI360 Execute operations."""
    pass


class CI360ExecuteAuthError(CI360ExecuteError):
    """Authentication-related errors."""
    pass


class CI360ExecuteConnectionError(CI360ExecuteError):
    """Connection and network-related errors."""
    pass


class CI360ExecuteValidationError(CI360ExecuteError):
    """Data validation errors."""
    pass


class CI360ExecuteBase:
    """
    Base class for SAS CI360 Execute operations.

    Provides authentication, connection management, and common functionality
    for campaign execution, messaging, and batch operations with async support.
    """

    def __init__(self, config: Optional[CI360ExecuteConfig] = None) -> None:
        """
        Initialize the CI360 Execute base client.

        Args:
            config: Configuration object for CI360 Execute operations

        Raises:
            CI360ExecuteValidationError: If required configuration is missing
        """
        self.config = config or CI360ExecuteConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Validate configuration
        self._validate_config()

        # Initialize HTTP session with retry strategy
        self.session = self._create_session()

        # Generate authentication token
        self.token = self._generate_token()

        # Connection state
        self._connected = False

        self.logger.info("CI360 Execute Base initialized successfully")

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        required_fields = ['host', 'secret_key', 'tenant_id']
        missing = [field for field in required_fields if not getattr(self.config, field)]

        if missing:
            raise CI360ExecuteValidationError(f"Missing required configuration: {', '.join(missing)}")

        # Validate algorithm
        supported_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        if self.config.algorithm not in supported_algorithms:
            raise CI360ExecuteValidationError(f"Unsupported algorithm: {self.config.algorithm}")

        # Validate batch size
        if self.config.batch_size <= 0:
            raise CI360ExecuteValidationError("batch_size must be positive")

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _generate_token(self) -> str:
        """Generate JWT authentication token."""
        if Encryption is None:
            raise CI360ExecuteAuthError(
                "sasci360apicore is not installed; it is required to generate "
                "authentication tokens. See README.md for how to obtain it."
            )
        try:
            encryption = Encryption(
                algorithm=self.config.algorithm,
                encoding=self.config.encoding
            )

            return encryption.generate_jwt(
                tenant_id=self.config.tenant_id,
                secret_key=self.config.secret_key
            )
        except Exception as e:
            raise CI360ExecuteAuthError(f"Failed to generate authentication token: {e}")

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            Dict[str, str]: Headers dictionary with authorization token
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Tenant-ID": str(self.config.tenant_id)
        }

    async def validate_connection_async(self) -> bool:
        """
        Asynchronously validate connection to CI360 service.

        Returns:
            bool: True if connection is valid
        """
        try:
            # Basic health check endpoint
            host = self.config.host or ""
            health_url = urljoin(host, "/health")
            headers = self.get_auth_headers()

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(
                    health_url,
                    headers=headers,
                    timeout=self.config.timeout
                )
            )

            self._connected = response.status_code == 200
            return self._connected

        except Exception as e:
            self.logger.error(f"Connection validation failed: {e}")
            self._connected = False
            return False

    def validate_connection(self) -> bool:
        """
        Validate connection to CI360 service.

        Returns:
            bool: True if connection is valid
        """
        try:
            # Run async validation in sync context
            return asyncio.run(self.validate_connection_async())
        except Exception as e:
            self.logger.error(f"Sync connection validation failed: {e}")
            return False

    async def _make_request_async(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make asynchronous HTTP request to CI360 API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Dict[str, Any]: Response data

        Raises:
            CI360ExecuteConnectionError: For network/connection errors
            CI360ExecuteAuthError: For authentication errors
        """
        if not self._connected:
            await self.validate_connection_async()
            if not self._connected:
                raise CI360ExecuteConnectionError("No active connection to CI360 service")

        host = self.config.host or ""
        url = urljoin(host + self.config.api_base, endpoint.lstrip('/'))
        headers = self.get_auth_headers()

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=self.config.timeout
                )
            )

            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise CI360ExecuteAuthError(f"Authentication failed: {e}")
            elif response.status_code >= 500:
                raise CI360ExecuteConnectionError(f"Server error: {e}")
            else:
                raise CI360ExecuteError(f"API request failed: {e}")
        except requests.exceptions.RequestException as e:
            raise CI360ExecuteConnectionError(f"Network error: {e}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make synchronous HTTP request to CI360 API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Dict[str, Any]: Response data
        """
        try:
            return asyncio.run(self._make_request_async(method, endpoint, data, params))
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            raise

    # Campaign Execution APIs

    async def execute_campaign_async(self, campaign_id: str, execution_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a campaign asynchronously.

        Args:
            campaign_id: Unique campaign identifier
            execution_params: Optional execution parameters

        Returns:
            Dict containing execution results and job ID
        """
        payload = {
            "campaignId": campaign_id,
            "executionParams": execution_params or {}
        }
        return await self._make_request_async("POST", "/campaigns/execute", data=payload)

    def execute_campaign(self, campaign_id: str, execution_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a campaign synchronously."""
        payload = {
            "campaignId": campaign_id,
            "executionParams": execution_params or {}
        }
        return self._make_request("POST", "/campaigns/execute", data=payload)

    async def get_execution_status_async(self, execution_id: str) -> Dict[str, Any]:
        """
        Get campaign execution status asynchronously.

        Args:
            execution_id: Unique execution identifier

        Returns:
            Dict containing execution status and details
        """
        return await self._make_request_async("GET", f"/executions/{execution_id}")

    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get campaign execution status synchronously."""
        return self._make_request("GET", f"/executions/{execution_id}")

    async def cancel_execution_async(self, execution_id: str) -> bool:
        """
        Cancel a running campaign execution asynchronously.

        Args:
            execution_id: Unique execution identifier

        Returns:
            True if cancellation successful
        """
        await self._make_request_async("POST", f"/executions/{execution_id}/cancel")
        return True

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running campaign execution synchronously."""
        self._make_request("POST", f"/executions/{execution_id}/cancel")
        return True

    # Batch Processing APIs

    async def submit_batch_job_async(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a batch job for processing asynchronously.

        Args:
            job_data: Batch job configuration and data

        Returns:
            Dict containing job submission results and job ID
        """
        return await self._make_request_async("POST", "/batch/jobs", data=job_data)

    def submit_batch_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a batch job for processing synchronously."""
        return self._make_request("POST", "/batch/jobs", data=job_data)

    async def get_batch_job_status_async(self, job_id: str) -> Dict[str, Any]:
        """
        Get batch job status asynchronously.

        Args:
            job_id: Unique batch job identifier

        Returns:
            Dict containing job status and progress
        """
        return await self._make_request_async("GET", f"/batch/jobs/{job_id}")

    def get_batch_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get batch job status synchronously."""
        return self._make_request("GET", f"/batch/jobs/{job_id}")

    async def cancel_batch_job_async(self, job_id: str) -> bool:
        """
        Cancel a batch job asynchronously.

        Args:
            job_id: Unique batch job identifier

        Returns:
            True if cancellation successful
        """
        await self._make_request_async("POST", f"/batch/jobs/{job_id}/cancel")
        return True

    def cancel_batch_job(self, job_id: str) -> bool:
        """Cancel a batch job synchronously."""
        self._make_request("POST", f"/batch/jobs/{job_id}/cancel")
        return True

    async def get_batch_jobs_async(
        self,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List batch jobs asynchronously.

        Args:
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            status_filter: Optional status filter (pending, running, completed, failed)

        Returns:
            Dict containing list of batch jobs
        """
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset
        }
        if status_filter:
            params["status"] = status_filter

        return await self._make_request_async("GET", "/batch/jobs", params=params)

    def get_batch_jobs(
        self,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """List batch jobs synchronously."""
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset
        }
        if status_filter:
            params["status"] = status_filter

        return self._make_request("GET", "/batch/jobs", params=params)

    # Job Scheduling APIs

    async def schedule_job_async(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule a job for future execution asynchronously.

        Args:
            schedule_data: Job schedule configuration

        Returns:
            Dict containing schedule creation results
        """
        return await self._make_request_async("POST", "/schedules", data=schedule_data)

    def schedule_job(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a job for future execution synchronously."""
        return self._make_request("POST", "/schedules", data=schedule_data)

    async def get_scheduled_jobs_async(
        self,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        List scheduled jobs asynchronously.

        Args:
            limit: Maximum number of schedules to return
            offset: Number of schedules to skip
            active_only: Whether to return only active schedules

        Returns:
            Dict containing list of scheduled jobs
        """
        params = {
            "limit": limit,
            "offset": offset,
            "activeOnly": active_only
        }
        return await self._make_request_async("GET", "/schedules", params=params)

    def get_scheduled_jobs(
        self,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """List scheduled jobs synchronously."""
        params = {
            "limit": limit,
            "offset": offset,
            "activeOnly": active_only
        }
        return self._make_request("GET", "/schedules", params=params)

    async def update_schedule_async(self, schedule_id: str, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a job schedule asynchronously.

        Args:
            schedule_id: Unique schedule identifier
            schedule_data: Updated schedule configuration

        Returns:
            Dict containing updated schedule
        """
        return await self._make_request_async("PUT", f"/schedules/{schedule_id}", data=schedule_data)

    def update_schedule(self, schedule_id: str, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a job schedule synchronously."""
        return self._make_request("PUT", f"/schedules/{schedule_id}", data=schedule_data)

    async def delete_schedule_async(self, schedule_id: str) -> bool:
        """
        Delete a job schedule asynchronously.

        Args:
            schedule_id: Unique schedule identifier

        Returns:
            True if deletion successful
        """
        await self._make_request_async("DELETE", f"/schedules/{schedule_id}")
        return True

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a job schedule synchronously."""
        self._make_request("DELETE", f"/schedules/{schedule_id}")
        return True

    # Execution Monitoring APIs

    async def get_execution_metrics_async(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get execution metrics asynchronously.

        Args:
            start_date: Start date for metrics (ISO format)
            end_date: End date for metrics (ISO format)
            campaign_id: Optional campaign filter

        Returns:
            Dict containing execution metrics
        """
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if campaign_id:
            params["campaignId"] = campaign_id

        return await self._make_request_async("GET", "/metrics/executions", params=params)

    def get_execution_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get execution metrics synchronously."""
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if campaign_id:
            params["campaignId"] = campaign_id

        return self._make_request("GET", "/metrics/executions", params=params)

    def __enter__(self):
        """Context manager entry."""
        if not self.validate_connection():
            raise CI360ExecuteConnectionError("Failed to establish connection")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        if not await self.validate_connection_async():
            raise CI360ExecuteConnectionError("Failed to establish connection")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.session.close()
