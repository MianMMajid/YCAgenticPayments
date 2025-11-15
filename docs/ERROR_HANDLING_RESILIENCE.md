# Error Handling and Resilience Implementation

This document describes the error handling and resilience features implemented for the Intelligent Escrow Agents system.

## Overview

The system implements comprehensive error handling and resilience patterns to ensure reliable operation even when external services fail or experience issues.

## Components

### 1. Custom Exception Classes (`api/exceptions.py`)

#### Escrow-Specific Exceptions

- **EscrowError**: Base exception for all escrow system errors
- **ValidationError**: Raised when validation fails (HTTP 400)
- **PaymentError**: Raised when payment operations fail (HTTP 402)
- **WorkflowError**: Raised when workflow execution fails (HTTP 500)
- **IntegrationError**: Raised when external integrations fail (HTTP 503)

#### Exception Handlers

Each exception type has a dedicated handler that:
- Logs errors with full context
- Returns user-friendly error responses
- Includes error type and details in response
- Provides retry hints where applicable

### 2. Retry Logic (`services/retry_utils.py`)

#### Retry Decorators

**Generic Decorators:**
- `retry_with_exponential_backoff`: Configurable exponential backoff
- `retry_with_fixed_delay`: Fixed delay between retries

**Pre-configured Decorators:**
- `@retry_payment_operation`: 3 retries, exponential backoff (1s, 2s, 4s)
- `@retry_blockchain_operation`: 5 retries, exponential backoff (2s, 4s, 8s, 16s, 32s)
- `@retry_notification_operation`: 3 retries, fixed 5-second intervals

#### Usage Example

```python
from services.retry_utils import retry_payment_operation

@retry_payment_operation
async def release_payment(wallet_id: str, amount: Decimal):
    # Payment logic here
    pass
```

### 3. Circuit Breakers (`services/circuit_breaker.py`)

#### Circuit Breaker Pattern

Implements the circuit breaker pattern with three states:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Too many failures, requests fail fast
- **HALF_OPEN**: Testing recovery, limited requests allowed

#### Pre-configured Circuit Breakers

- **Agentic Stripe**: 5 failures, 60s recovery timeout
- **Blockchain**: 10 failures, 30s recovery timeout
- **Notifications**: 3 failures, 120s recovery timeout

#### Usage Example

```python
from services.circuit_breaker import agentic_stripe_circuit_breaker

@agentic_stripe_circuit_breaker
async def create_wallet(transaction_id: str):
    # Wallet creation logic here
    pass
```

#### Circuit Breaker Registry

Global registry for managing all circuit breakers:
- Track state of all circuits
- Monitor failure counts
- Reset circuits manually or automatically

### 4. Service Integration

#### Agentic Stripe Client

All payment operations protected with:
- Circuit breaker (5 failures, 60s timeout)
- Retry logic (3 attempts, exponential backoff)

Protected methods:
- `create_wallet`
- `configure_milestones`
- `release_milestone_payment`
- `execute_final_settlement`
- `get_wallet_balance`
- `get_transaction_history`

#### Blockchain Client

All blockchain operations protected with:
- Circuit breaker (10 failures, 30s timeout)
- Retry logic (5 attempts, exponential backoff)

Protected methods:
- `log_event`
- `get_audit_trail`
- `verify_event`
- `get_block_number`

#### Notification Engine

All notification operations protected with:
- Circuit breaker (3 failures, 120s timeout)
- Retry logic (3 attempts, 5s fixed delay)

Protected methods:
- `notify_transaction_parties`
- `send_escalation_alert`

## Monitoring

### Circuit Breaker Status Endpoint

**GET /health/circuit-breakers**

Returns the status of all circuit breakers:

```json
{
  "status": "healthy",
  "circuit_breakers": {
    "agentic_stripe": {
      "name": "agentic_stripe",
      "state": "closed",
      "failure_count": 0,
      "success_count": 0,
      "failure_threshold": 5,
      "recovery_timeout": 60.0,
      "last_failure_time": null,
      "opened_at": null
    },
    "blockchain": {
      "name": "blockchain",
      "state": "closed",
      "failure_count": 0,
      "success_count": 0,
      "failure_threshold": 10,
      "recovery_timeout": 30.0,
      "last_failure_time": null,
      "opened_at": null
    },
    "notification": {
      "name": "notification",
      "state": "closed",
      "failure_count": 0,
      "success_count": 0,
      "failure_threshold": 3,
      "recovery_timeout": 120.0,
      "last_failure_time": null,
      "opened_at": null
    }
  }
}
```

### Reset Circuit Breakers

**POST /admin/circuit-breakers/reset**

Manually reset all circuit breakers to closed state.

## Error Response Format

All errors follow a consistent format:

```json
{
  "error": "Payment failed: Insufficient funds",
  "error_type": "PaymentError",
  "status_code": 402,
  "details": {
    "payment_id": "pay_123",
    "amount": "1000.00",
    "service": "agentic_stripe"
  },
  "retry_allowed": true
}
```

## Best Practices

### 1. Use Appropriate Exception Types

```python
# For validation errors
raise ValidationError("Invalid transaction amount", field="amount")

# For payment errors
raise PaymentError("Insufficient funds", payment_id="pay_123", amount="1000.00")

# For workflow errors
raise WorkflowError("Task deadline exceeded", transaction_id="tx_123", workflow_state="verification")

# For integration errors
raise IntegrationError("agentic_stripe", "Connection timeout", operation="create_wallet")
```

### 2. Combine Retry and Circuit Breaker

```python
@agentic_stripe_circuit_breaker
@retry_payment_operation
async def process_payment():
    # Circuit breaker prevents cascading failures
    # Retry logic handles transient errors
    pass
```

### 3. Log with Context

```python
logger.error(
    "Payment failed",
    extra={
        "transaction_id": transaction_id,
        "payment_id": payment_id,
        "amount": amount,
        "error": str(e)
    }
)
```

## Configuration

Circuit breaker and retry parameters can be customized:

```python
from services.circuit_breaker import with_circuit_breaker
from services.retry_utils import retry_with_exponential_backoff

@with_circuit_breaker(
    name="custom_service",
    failure_threshold=3,
    recovery_timeout=30.0
)
@retry_with_exponential_backoff(
    max_attempts=5,
    initial_delay=1.0,
    max_delay=10.0
)
async def call_custom_service():
    pass
```

## Testing

### Test Circuit Breaker Behavior

```python
from services.circuit_breaker import CircuitBreaker, CircuitBreakerError

async def test_circuit_breaker():
    breaker = CircuitBreaker("test", failure_threshold=3, recovery_timeout=1.0)
    
    # Simulate failures
    for i in range(3):
        try:
            await breaker.call(failing_function)
        except Exception:
            pass
    
    # Circuit should be open
    assert breaker.state == CircuitState.OPEN
    
    # Should fail fast
    with pytest.raises(CircuitBreakerError):
        await breaker.call(failing_function)
```

### Test Retry Logic

```python
from services.retry_utils import retry_with_exponential_backoff

@retry_with_exponential_backoff(max_attempts=3, initial_delay=0.1)
async def flaky_function():
    # Function that may fail
    pass

async def test_retry():
    # Should retry up to 3 times
    result = await flaky_function()
    assert result is not None
```

## Metrics

The system tracks the following metrics:
- Circuit breaker state changes
- Failure counts per service
- Retry attempts per operation
- Recovery success rates
- Error rates by type

These metrics are logged and can be exported to monitoring systems like Prometheus.
