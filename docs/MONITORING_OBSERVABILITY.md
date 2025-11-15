# Monitoring and Observability

This document describes the monitoring and observability features implemented for the Intelligent Escrow Agents system.

## Overview

The system includes comprehensive monitoring and observability features:

1. **Metrics Collection** - Prometheus-compatible metrics for transaction throughput, closing cycle times, verification completion rates, payment success rates, and API response times
2. **Structured Logging** - JSON-formatted logs with correlation IDs for request tracing
3. **Health Checks** - Liveness, readiness, and dependency health check endpoints

## Metrics Collection

### Prometheus Metrics

The system exposes Prometheus-compatible metrics at `/metrics` endpoint.

#### Transaction Metrics

- `escrow_transactions_initiated_total` - Total number of transactions initiated
- `escrow_transactions_settled_total` - Total number of transactions settled
- `escrow_transactions_disputed_total` - Total number of transactions disputed
- `escrow_transactions_cancelled_total` - Total number of transactions cancelled
- `escrow_closing_cycle_time_seconds` - Histogram of closing cycle times (from initiation to settlement)

#### Verification Metrics

- `escrow_verification_tasks_assigned_total{verification_type}` - Total verification tasks assigned by type
- `escrow_verification_tasks_completed_total{verification_type}` - Total verification tasks completed by type
- `escrow_verification_tasks_failed_total{verification_type}` - Total verification tasks failed by type
- `escrow_verification_completion_time_seconds{verification_type}` - Histogram of verification completion times

#### Payment Metrics

- `escrow_payments_initiated_total{payment_type}` - Total payments initiated by type
- `escrow_payments_completed_total{payment_type}` - Total payments completed by type
- `escrow_payments_failed_total{payment_type}` - Total payments failed by type
- `escrow_payment_amount_total_cents{payment_type}` - Total payment amount in cents by type

#### API Metrics

- `escrow_api_request_duration_seconds{method,endpoint,status_code}` - Histogram of API request durations with p50, p95, p99 percentiles

#### Workflow Metrics

- `escrow_workflow_execution_time_seconds{workflow_type}` - Histogram of workflow execution times

#### Blockchain Metrics

- `escrow_blockchain_events_logged_total{event_type}` - Total blockchain events logged by type
- `escrow_blockchain_logging_errors_total` - Total blockchain logging errors

#### Active Transactions Gauge

- `escrow_active_transactions{state}` - Number of active transactions by state

### Custom Metrics Endpoints

#### Verification Completion Rate

```
GET /metrics/verification-completion-rate?verification_type={type}
```

Returns the verification completion rate as a percentage.

**Parameters:**
- `verification_type` (optional) - Specific verification type (title_search, inspection, appraisal, lending)

**Response:**
```json
{
  "verification_type": "title_search",
  "completion_rate": 95.5,
  "unit": "percentage"
}
```

#### Payment Success Rate

```
GET /metrics/payment-success-rate?payment_type={type}
```

Returns the payment success rate as a percentage.

**Parameters:**
- `payment_type` (optional) - Specific payment type

**Response:**
```json
{
  "payment_type": "verification",
  "success_rate": 98.2,
  "unit": "percentage"
}
```

### Using Metrics in Code

```python
from api.escrow_metrics import escrow_metrics

# Track transaction initiation
escrow_metrics.track_transaction_initiated(
    transaction_id="txn_123",
    initiated_at=datetime.utcnow()
)

# Track transaction settlement
escrow_metrics.track_transaction_settled(
    transaction_id="txn_123",
    settled_at=datetime.utcnow()
)

# Track verification assignment
escrow_metrics.track_verification_assigned(
    verification_id="ver_456",
    verification_type="title_search",
    assigned_at=datetime.utcnow()
)

# Track verification completion
escrow_metrics.track_verification_completed(
    verification_id="ver_456",
    verification_type="title_search",
    completed_at=datetime.utcnow()
)

# Track payment
escrow_metrics.track_payment_initiated(
    payment_id="pay_789",
    payment_type="verification",
    amount=1200.00,
    initiated_at=datetime.utcnow()
)

escrow_metrics.track_payment_completed(
    payment_id="pay_789",
    payment_type="verification"
)
```

## Structured Logging

### Features

- **JSON Format** - Logs are output in JSON format in production for easy parsing
- **Correlation IDs** - Each request gets a unique correlation ID for tracing
- **Contextual Data** - Logs include structured data fields for filtering and analysis
- **Log Levels** - Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Correlation IDs

Correlation IDs are automatically generated for each request and included in all logs during request processing.

**Request Header:**
```
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
```

**Response Header:**
```
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
```

### Log Format

```json
{
  "timestamp": "2025-11-14T10:30:45.123456Z",
  "level": "INFO",
  "logger": "api.escrow.transactions",
  "message": "Transaction initiated",
  "module": "transactions",
  "function": "create_transaction",
  "line": 42,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "transaction_id": "txn_123",
  "buyer_agent_id": "agent_456",
  "seller_agent_id": "agent_789"
}
```

### Using Structured Logging

```python
from api.structured_logging import get_logger

logger = get_logger(__name__)

# Log with structured data
logger.info(
    "Transaction initiated",
    transaction_id="txn_123",
    buyer_agent_id="agent_456",
    seller_agent_id="agent_789",
    earnest_money=50000.00
)

# Log with context manager
from api.structured_logging import LogContext

with LogContext(transaction_id="txn_123", user_id="user_456"):
    logger.info("Processing transaction")
    # All logs within this context will include transaction_id and user_id
```

### Getting Correlation ID

```python
from api.structured_logging import get_correlation_id

correlation_id = get_correlation_id()
```

## Health Checks

### Endpoints

#### Liveness Probe

```
GET /health/live
```

Returns 200 OK if the application is running. Used by orchestrators to determine if the application should be restarted.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-14T10:30:45.123456Z",
  "service": "Counter AI Real Estate Broker - Escrow System",
  "version": "1.0.0"
}
```

#### Readiness Probe

```
GET /health/ready
```

Returns 200 if ready to serve traffic, 503 if not ready. Checks all critical dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-14T10:30:45.123456Z",
  "service": "Counter AI Real Estate Broker - Escrow System",
  "version": "1.0.0",
  "environment": "production",
  "dependencies": {
    "database": {
      "status": "healthy",
      "response_time_seconds": 0.012,
      "message": "Database connection successful"
    },
    "redis": {
      "status": "healthy",
      "response_time_seconds": 0.005,
      "connected_clients": 3,
      "used_memory_human": "2.5M",
      "message": "Redis connection successful"
    },
    "agentic_stripe": {
      "status": "healthy",
      "response_time_seconds": 0.008,
      "message": "Agentic Stripe client initialized"
    },
    "blockchain": {
      "status": "healthy",
      "response_time_seconds": 0.015,
      "network": "mainnet",
      "message": "Blockchain client initialized"
    },
    "circuit_breakers": {
      "status": "healthy",
      "circuit_breakers": {
        "agentic_stripe": {
          "state": "closed",
          "failure_count": 0
        },
        "blockchain": {
          "state": "closed",
          "failure_count": 0
        }
      },
      "message": "All circuit breakers closed"
    }
  }
}
```

#### Startup Probe

```
GET /health/startup
```

Checks if the application has completed initialization. Similar to readiness probe.

#### Dependencies Check

```
GET /health/dependencies
```

Provides detailed information about each dependency's health.

#### General Health Check

```
GET /health
```

Alias for readiness check for backward compatibility.

### Health Status Values

- `healthy` - All systems operational
- `degraded` - Some non-critical systems have issues
- `unhealthy` - Critical systems are down

### Kubernetes Configuration Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: escrow-api
spec:
  containers:
  - name: api
    image: escrow-api:latest
    ports:
    - containerPort: 8000
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
    startupProbe:
      httpGet:
        path: /health/startup
        port: 8000
      initialDelaySeconds: 0
      periodSeconds: 10
      timeoutSeconds: 3
      failureThreshold: 30
```

## Prometheus Configuration

### Scrape Configuration

```yaml
scrape_configs:
  - job_name: 'escrow-api'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Key metrics to monitor:

1. **Transaction Throughput**
   - Rate of transactions initiated per hour
   - Rate of transactions settled per hour

2. **Closing Cycle Time**
   - p50, p95, p99 percentiles of closing cycle time
   - Target: 7-14 days (604800-1209600 seconds)

3. **Verification Completion Rate**
   - Percentage of verification tasks completed
   - Target: >95%

4. **Payment Success Rate**
   - Percentage of payments completed successfully
   - Target: >98%

5. **API Response Time**
   - p50, p95, p99 percentiles of API response time
   - Target: p95 < 1s, p99 < 2.5s

6. **Active Transactions**
   - Number of transactions in each state
   - Monitor for stuck transactions

## Alerting

### Recommended Alerts

1. **High Closing Cycle Time**
   - Alert if p95 closing cycle time > 21 days
   - Severity: Warning

2. **Low Verification Completion Rate**
   - Alert if completion rate < 90%
   - Severity: Warning

3. **Low Payment Success Rate**
   - Alert if success rate < 95%
   - Severity: Critical

4. **High API Error Rate**
   - Alert if 5xx error rate > 5%
   - Severity: Critical

5. **Dependency Unhealthy**
   - Alert if any critical dependency is unhealthy
   - Severity: Critical

6. **Circuit Breaker Open**
   - Alert if any circuit breaker is open
   - Severity: Warning

## Log Aggregation

### ELK Stack Configuration

Logs can be aggregated using the ELK (Elasticsearch, Logstash, Kibana) stack.

**Logstash Configuration:**
```
input {
  file {
    path => "/var/log/escrow-api/*.log"
    codec => json
  }
}

filter {
  json {
    source => "message"
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "escrow-api-%{+YYYY.MM.dd}"
  }
}
```

### Useful Queries

**Find all logs for a specific transaction:**
```
transaction_id:"txn_123"
```

**Find all logs for a specific correlation ID:**
```
correlation_id:"550e8400-e29b-41d4-a716-446655440000"
```

**Find all errors:**
```
level:"ERROR"
```

**Find all payment failures:**
```
metric_type:"payment_failed"
```

## Performance Considerations

- Metrics collection has minimal overhead (<1ms per operation)
- Structured logging adds ~2-5ms per log entry
- Health checks are cached for 5 seconds to reduce load
- Prometheus scraping should be configured for 15-30 second intervals

## Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Metrics
ENABLE_METRICS=true

# Health Checks
HEALTH_CHECK_CACHE_TTL=5  # seconds
```

## Troubleshooting

### Metrics Not Appearing

1. Check that `/metrics` endpoint is accessible
2. Verify Prometheus scrape configuration
3. Check application logs for errors

### Correlation IDs Not Working

1. Verify `CorrelationIdMiddleware` is registered
2. Check that middleware is first in the chain
3. Verify `X-Correlation-ID` header is being sent

### Health Checks Failing

1. Check dependency connectivity (database, Redis, etc.)
2. Review health check logs for specific errors
3. Verify configuration settings for external services
