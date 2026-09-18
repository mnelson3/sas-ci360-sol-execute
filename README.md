# SAS CI360 Sol Execute

## Python client for SAS Customer Intelligence 360 Marketing Execution APIs

This repository provides Python interfaces for SAS Customer Intelligence 360 Marketing Execution APIs.

> This is an independent client library and is not an official SAS product. "SAS" and "Customer Intelligence 360" are trademarks of SAS Institute Inc.; this project is not affiliated with or endorsed by SAS Institute.

### Overview

The Execute module enables programmatic campaign execution, message sending, and marketing automation within the CI360 platform.

### Features

- Campaign execution and management
- Batch job submission and monitoring
- Job scheduling
- Execution monitoring and reporting
- Sync and async APIs for every operation

### Prerequisites

- Python 3.8+
- Access to a SAS Customer Intelligence 360 environment
- `sasci360apicore` and `sasci360apimarketingexecution` — SAS-internal packages required at runtime for authentication and API access. These are not published on public PyPI; obtain them from your SAS CI360 environment/administrator. See [requirements.txt](requirements.txt) for the full dependency list.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mnelson3/sas-ci360-sol-execute.git
   cd sas-ci360-sol-execute
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Getting Started

```python
from sasci360solexecute.base import CI360ExecuteBase, CI360ExecuteConfig

config = CI360ExecuteConfig(
    host="https://your-ci360-host.sas.com",
    secret_key="your-secret-key",
    tenant_id="your-tenant-id"
)

client = CI360ExecuteBase(config)

# Execute campaigns programmatically
result = client.execute_campaign("campaign-id")
```

### Solutions Code

The execute module provides:

1. **Campaign Execution**: Launch, monitor, and cancel campaign executions
2. **Batch Processing**: Submit, monitor, and cancel batch jobs
3. **Job Scheduling**: Create, list, update, and delete scheduled jobs
4. **Execution Monitoring**: Track campaign performance metrics

### Troubleshooting

- Verify campaign configurations
- Check execution permissions
- Monitor API rate limits
- Review execution logs

## 🛠️ Developer/Implementation Guide

This section provides comprehensive guidance for developers implementing campaign execution solutions with SAS CI360.

### Architecture Overview

The SAS CI360 Execute module follows a workflow-driven architecture designed for scalable marketing execution:

```
┌─────────────────────────────────────────────────────────────┐
│                   Execute Module                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Campaign    │ │ Batch       │ │ Job         │           │
│  │ Execution   │ │ Processing  │ │ Scheduling  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ REST API    │ │ JWT Auth    │ │ Async I/O   │           │
│  │ Client      │ │ & Security  │ │ Operations  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

#### Core Components

1. **Campaign Execution Layer**
   - `CI360ExecuteBase`: Core client class for all operations below
   - Campaign lifecycle management (execute, monitor status, cancel)
   - Execution metrics and reporting

2. **Batch Processing Layer**
   - Batch job submission and status tracking
   - Job listing with pagination and status filtering
   - Batch job cancellation

3. **Job Scheduling Layer**
   - Create and manage scheduled jobs
   - Update or delete existing schedules
   - List active/inactive schedules

### Configuration Management

#### Environment Variables
```bash
export SAS_CI360_SECRET_KEY="your-secret-key"
export SAS_CI360_TENANT_ID="your-tenant-id"
```

#### Configuration Class
```python
from sasci360solexecute.base import CI360ExecuteConfig

config = CI360ExecuteConfig(
    algorithm="HS256",
    encoding="utf-8",
    host="your-ci360-host.sas.com",
    secret_key="your-secret-key",
    tenant_id="your-tenant-id"
)
```

### API Integration Patterns

#### Campaign Execution
```python
from sasci360solexecute.base import CI360ExecuteBase, CI360ExecuteConfig

client = CI360ExecuteBase(CI360ExecuteConfig(
    host="https://your-ci360-host.sas.com",
    secret_key="your-secret-key",
    tenant_id="your-tenant-id"
))

result = client.execute_campaign(
    campaign_id="summer-promo-2024",
    execution_params={"priority": "high"}
)
print(f"Execution started: {result['executionId']}")
```

#### Asynchronous Operations
```python
import asyncio
from sasci360solexecute.base import CI360ExecuteBase, CI360ExecuteConfig

async def execute_marketing_workflow():
    client = CI360ExecuteBase(CI360ExecuteConfig(
        host="https://your-ci360-host.sas.com",
        secret_key="your-secret-key",
        tenant_id="your-tenant-id"
    ))

    # Execute campaign asynchronously
    campaign_result = await client.execute_campaign_async("summer-promo-2024")
    execution_id = campaign_result["executionId"]

    # Monitor execution in real-time
    while True:
        status = await client.get_execution_status_async(execution_id)
        print(f"Campaign status: {status['status']}")

        if status["status"] in ["completed", "failed", "cancelled"]:
            break

        await asyncio.sleep(30)  # Check every 30 seconds

# Run async workflow
asyncio.run(execute_marketing_workflow())
```

#### Batch Job Operations
```python
# Submit a batch job
job_data = {
    "name": "Customer Update Batch",
    "operations": [{"type": "update", "data": {"customerId": "123"}}]
}

result = client.submit_batch_job(job_data)
print(f"Batch job queued: {result['jobId']}")
```

### Error Handling

#### Exception Types
```python
from sasci360solexecute.base import (
    CI360ExecuteBase,
    CI360ExecuteError,
    CI360ExecuteAuthError,
    CI360ExecuteValidationError
)

try:
    client = CI360ExecuteBase(config)
    result = client.execute_campaign("summer-promo-2024")
except CI360ExecuteAuthError as e:
    print(f"Authentication failed: {e}")
    # Handle auth issues (token refresh, credentials)
except CI360ExecuteValidationError as e:
    print(f"Validation error: {e}")
    # Handle campaign configuration issues
except CI360ExecuteError as e:
    print(f"Execution error: {e}")
    # Handle general execution errors
```

#### Campaign Failure Recovery
```python
import time

def execute_campaign_with_recovery(client, campaign_id, max_retries=3):
    for attempt in range(max_retries + 1):
        try:
            return client.execute_campaign(campaign_id)
        except CI360ExecuteError as e:
            if attempt < max_retries:
                print(f"Campaign execution failed (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)  # exponential backoff
                continue
            raise
```

### Testing Approaches

See [tests/test_base.py](tests/test_base.py) for the full suite. The pattern used throughout:

```python
import asyncio
import unittest
from unittest.mock import patch
from sasci360solexecute.base import CI360ExecuteBase, CI360ExecuteConfig

class TestCampaignExecution(unittest.TestCase):
    def setUp(self):
        self.config = CI360ExecuteConfig(
            host="https://api.example.com",
            secret_key="test-secret-key",
            tenant_id="test-tenant-id"
        )

    @patch('sasci360solexecute.base.requests.Session')
    @patch('sasci360solexecute.base.Encryption')
    @patch('sasci360solexecute.base.CI360ExecuteBase._make_request_async')
    def test_execute_campaign(self, mock_request, mock_encryption_class, mock_session_class):
        mock_request.return_value = {"executionId": "exec-123", "status": "running"}

        client = CI360ExecuteBase(self.config)
        result = client.execute_campaign("camp-123")

        self.assertEqual(result["executionId"], "exec-123")
```

### Performance Considerations

#### Concurrent Campaign Execution
```python
# Execute multiple campaigns concurrently
async def execute_multiple_campaigns(client, campaign_ids):
    tasks = [client.execute_campaign_async(cid) for cid in campaign_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = []
    failed = []

    for campaign_id, result in zip(campaign_ids, results):
        if isinstance(result, Exception):
            failed.append({"campaign_id": campaign_id, "error": str(result)})
        else:
            successful.append(result)

    return successful, failed
```

#### Rate Limiting and Throttling
```python
import asyncio
from sasci360solexecute.base import CI360ExecuteBase

class RateLimitedExecuteClient(CI360ExecuteBase):
    def __init__(self, *args, requests_per_minute=60, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests_per_minute = requests_per_minute
        self.request_times = []

    async def _make_request_async(self, *args, **kwargs):
        now = asyncio.get_event_loop().time()

        # Remove old requests outside the time window
        self.request_times = [t for t in self.request_times if now - t < 60]

        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            await asyncio.sleep(sleep_time)

        self.request_times.append(now)
        return await super()._make_request_async(*args, **kwargs)
```

#### Monitoring and Alerting
```python
# Campaign performance monitoring
def monitor_campaign_performance(client, campaign_id, alert_thresholds):
    metrics = client.get_execution_metrics(campaign_id=campaign_id)

    alerts = []

    if metrics.get("failedExecutions", 0) > alert_thresholds["max_failures"]:
        alerts.append(f"High failure count: {metrics['failedExecutions']}")

    return alerts
```

### Campaign Optimization

1. **A/B Testing**: Implement multivariate campaign testing
2. **Dynamic Content**: Real-time content optimization based on performance
3. **Audience Segmentation**: Automated audience splitting and targeting
4. **Performance Analytics**: Real-time campaign metrics and insights
5. **Automated Adjustments**: AI-driven campaign parameter optimization

### Contributing

We welcome your contributions! Please read [CONTRIBUTING](CONTRIBUTING.md) for details on how to submit contributions to this project.

### License

This project is licensed under the [Nelson Grey LLC Community License 1.0](LICENSE).

- **Free for individuals, education, and research**: use, modify, and distribute this software for non-commercial purposes
- **Commercial evaluation**: evaluate the software for a possible commercial use, free of charge
- **Commercial production use**: requires a commercial license from Nelson Grey LLC
- **Automatic conversion**: on December 13, 2029, this automatically converts to the Apache License 2.0

For commercial licensing inquiries, contact support@nelsongrey.com.

### Additional Resources

For more information, see [Marketing Execution API](https://go.documentation.sas.com/doc/en/cintcdc/production.a/cintapis/rest-mkt-exec-api.htm).
