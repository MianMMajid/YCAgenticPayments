# Integration Guide

## Overview

This guide provides step-by-step instructions for integrating with the Intelligent Escrow Agents API. It covers authentication, webhook setup, error handling, and common integration patterns.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication Flow](#authentication-flow)
3. [Webhook Setup](#webhook-setup)
4. [Error Handling](#error-handling)
5. [Common Integration Patterns](#common-integration-patterns)
6. [Testing](#testing)
7. [Production Checklist](#production-checklist)

## Getting Started

### Prerequisites

- API credentials (contact support@counterai.com)
- HTTPS endpoint for receiving webhooks
- Agent license information
- Development environment with HTTP client library

### Base URLs

```
Development: http://localhost:8000
Staging: https://staging-api.counterai.com
Production: https://api.counterai.com
```

### Quick Start

1. Register your agent
2. Authenticate to get access token
3. Configure webhook endpoint
4. Create your first transaction
5. Monitor transaction progress

## Authentication Flow

### Step 1: Register Agent

First-time setup requires agent registration:

```python
import requests

def register_agent():
    response = requests.post(
        "https://api.counterai.com/auth/register",
        json={
            "agent_id": "your_unique_agent_id",
            "agent_type": "buyer_agent",  # or "seller_agent", "title_agent", etc.
            "name": "Your Name",
            "email": "your.email@example.com",
            "phone": "+1234567890",
            "license_number": "CA-DRE-12345678",
            "webhook_url": "https://your-domain.com/webhooks/escrow"
        }
    )
    response.raise_for_status()
    return response.json()

agent = register_agent()
print(f"Agent registered: {agent['agent_id']}")
```


### Step 2: Authenticate

Obtain a JWT access token:

```python
def login(agent_id: str, password: str):
    response = requests.post(
        "https://api.counterai.com/auth/login",
        json={
            "agent_id": agent_id,
            "password": password
        }
    )
    response.raise_for_status()
    data = response.json()
    return data["access_token"]

token = login("your_agent_id", "your_password")
```

### Step 3: Use Token in Requests

Include the token in the Authorization header:

```python
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.get(
    "https://api.counterai.com/api/escrow/transactions",
    headers=headers
)
```

### Token Refresh

Tokens expire after 1 hour. Implement automatic refresh:

```python
import time
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, agent_id: str, password: str):
        self.agent_id = agent_id
        self.password = password
        self.token = None
        self.expires_at = None
    
    def get_token(self) -> str:
        if self.token and self.expires_at > datetime.now():
            return self.token
        
        # Refresh token
        response = requests.post(
            "https://api.counterai.com/auth/login",
            json={
                "agent_id": self.agent_id,
                "password": self.password
            }
        )
        response.raise_for_status()
        data = response.json()
        
        self.token = data["access_token"]
        self.expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        
        return self.token

# Usage
token_manager = TokenManager("your_agent_id", "your_password")
headers = {"Authorization": f"Bearer {token_manager.get_token()}"}
```

## Webhook Setup

### Step 1: Create Webhook Endpoint

Create an HTTPS endpoint to receive webhook events:

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_secret"

@app.route("/webhooks/escrow", methods=["POST"])
def handle_webhook():
    # Verify signature
    signature = request.headers.get("X-Webhook-Signature")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Process event
    event = request.json
    event_type = event["event"]
    
    if event_type == "verification.assigned":
        handle_verification_assigned(event["data"])
    elif event_type == "payment.released":
        handle_payment_released(event["data"])
    elif event_type == "settlement.executed":
        handle_settlement_executed(event["data"])
    
    return jsonify({"status": "received"}), 200

def verify_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

def handle_verification_assigned(data):
    print(f"Verification assigned: {data['verification_type']}")
    # Your logic here

def handle_payment_released(data):
    print(f"Payment released: ${data['payment_amount']}")
    # Your logic here

def handle_settlement_executed(data):
    print(f"Settlement executed: {data['transaction_id']}")
    # Your logic here
```

### Step 2: Register Webhook URL

Update your agent profile with webhook URL:

```python
def update_webhook_url(token: str, webhook_url: str):
    response = requests.patch(
        "https://api.counterai.com/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"webhook_url": webhook_url}
    )
    response.raise_for_status()
    return response.json()

update_webhook_url(token, "https://your-domain.com/webhooks/escrow")
```

### Step 3: Handle Webhook Events

Implement handlers for each event type:

```python
class WebhookHandler:
    def __init__(self, secret: str):
        self.secret = secret
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        expected = hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    def handle_event(self, event: dict):
        event_type = event["event"]
        handlers = {
            "transaction.initiated": self.on_transaction_initiated,
            "transaction.funded": self.on_transaction_funded,
            "verification.assigned": self.on_verification_assigned,
            "verification.completed": self.on_verification_completed,
            "payment.released": self.on_payment_released,
            "settlement.executed": self.on_settlement_executed,
            "dispute.raised": self.on_dispute_raised,
            "transaction.cancelled": self.on_transaction_cancelled
        }
        
        handler = handlers.get(event_type)
        if handler:
            handler(event["data"])
        else:
            print(f"Unknown event type: {event_type}")
    
    def on_transaction_initiated(self, data):
        print(f"Transaction initiated: {data['transaction_id']}")
    
    def on_verification_assigned(self, data):
        print(f"Verification assigned: {data['verification_type']}")
        # Start verification process
    
    def on_payment_released(self, data):
        print(f"Payment released: ${data['payment_amount']}")
        # Update internal records
    
    def on_settlement_executed(self, data):
        print(f"Settlement executed: {data['transaction_id']}")
        # Close transaction in your system
```

### Webhook Retry Logic

The system retries failed webhooks with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: After 5 seconds
- Attempt 3: After 25 seconds
- Attempt 4: After 125 seconds

Return HTTP 200 to acknowledge receipt. Any other status triggers retry.

## Error Handling

### Error Response Structure

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid earnest money amount",
    "details": {
      "field": "earnest_money",
      "constraint": "must be greater than 0"
    },
    "request_id": "req_abc123"
  }
}
```

### Handling Different Error Types

```python
class EscrowAPIError(Exception):
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

def make_api_request(url: str, method: str = "GET", **kwargs):
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json().get("error", {})
        
        if e.response.status_code == 400:
            raise EscrowAPIError(
                error_data.get("code", "VALIDATION_ERROR"),
                error_data.get("message", "Validation failed"),
                error_data.get("details")
            )
        elif e.response.status_code == 401:
            raise EscrowAPIError("AUTHENTICATION_ERROR", "Invalid or expired token")
        elif e.response.status_code == 403:
            raise EscrowAPIError("AUTHORIZATION_ERROR", "Insufficient permissions")
        elif e.response.status_code == 404:
            raise EscrowAPIError("NOT_FOUND", "Resource not found")
        elif e.response.status_code == 429:
            raise EscrowAPIError("RATE_LIMIT_EXCEEDED", "Too many requests")
        elif e.response.status_code >= 500:
            raise EscrowAPIError("INTERNAL_ERROR", "Server error")
        else:
            raise EscrowAPIError("UNKNOWN_ERROR", str(e))
```

### Retry Strategy

Implement exponential backoff for transient errors:

```python
import time
from typing import Callable, Any

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_errors: tuple = (EscrowAPIError,)
):
    for attempt in range(max_retries):
        try:
            return func()
        except retryable_errors as e:
            if attempt == max_retries - 1:
                raise
            
            # Don't retry client errors (4xx)
            if hasattr(e, 'code') and e.code in [
                "VALIDATION_ERROR",
                "AUTHENTICATION_ERROR",
                "AUTHORIZATION_ERROR",
                "NOT_FOUND"
            ]:
                raise
            
            delay = initial_delay * (backoff_factor ** attempt)
            print(f"Retry attempt {attempt + 1} after {delay}s")
            time.sleep(delay)

# Usage
def create_transaction():
    return make_api_request(
        "https://api.counterai.com/api/escrow/transactions",
        method="POST",
        headers=headers,
        json=transaction_data
    )

transaction = retry_with_backoff(create_transaction)
```

### Circuit Breaker Pattern

Prevent cascading failures:

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable) -> Any:
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def api_call():
    return circuit_breaker.call(lambda: make_api_request(...))
```

## Common Integration Patterns

### Pattern 1: Create Transaction

Complete flow for initiating a transaction:

```python
class EscrowIntegration:
    def __init__(self, base_url: str, token_manager: TokenManager):
        self.base_url = base_url
        self.token_manager = token_manager
    
    def create_transaction(
        self,
        buyer_agent_id: str,
        seller_agent_id: str,
        property_id: str,
        earnest_money: float,
        total_purchase_price: float,
        target_closing_date: str,
        metadata: dict = None
    ):
        headers = {
            "Authorization": f"Bearer {self.token_manager.get_token()}",
            "Content-Type": "application/json"
        }
        
        data = {
            "buyer_agent_id": buyer_agent_id,
            "seller_agent_id": seller_agent_id,
            "property_id": property_id,
            "earnest_money": earnest_money,
            "total_purchase_price": total_purchase_price,
            "target_closing_date": target_closing_date,
            "metadata": metadata or {}
        }
        
        response = requests.post(
            f"{self.base_url}/api/escrow/transactions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        
        transaction = response.json()
        print(f"Transaction created: {transaction['id']}")
        print(f"Wallet ID: {transaction['wallet_id']}")
        print(f"State: {transaction['state']}")
        
        return transaction

# Usage
integration = EscrowIntegration(
    "https://api.counterai.com",
    token_manager
)

transaction = integration.create_transaction(
    buyer_agent_id="agent_buyer_001",
    seller_agent_id="agent_seller_001",
    property_id="prop_12345",
    earnest_money=10000.00,
    total_purchase_price=500000.00,
    target_closing_date="2025-12-01T00:00:00Z",
    metadata={
        "property_address": "123 Main St, San Francisco, CA 94102",
        "buyer_name": "Alice Johnson",
        "seller_name": "Bob Smith"
    }
)
```

### Pattern 2: Submit Verification Report

Verification agents submit reports:

```python
def submit_verification_report(
    self,
    transaction_id: str,
    verification_type: str,
    agent_id: str,
    status: str,
    findings: dict,
    documents: list
):
    headers = {
        "Authorization": f"Bearer {self.token_manager.get_token()}",
        "Content-Type": "application/json"
    }
    
    data = {
        "verification_type": verification_type,
        "agent_id": agent_id,
        "status": status,
        "findings": findings,
        "documents": documents
    }
    
    response = requests.post(
        f"{self.base_url}/api/escrow/transactions/{transaction_id}/verifications",
        headers=headers,
        json=data
    )
    response.raise_for_status()
    
    report = response.json()
    print(f"Report submitted: {report['id']}")
    
    if report.get("payment_released"):
        print(f"Payment released: ${report['payment_amount']}")
    
    return report

# Usage - Title Search Agent
report = integration.submit_verification_report(
    transaction_id="txn_abc123",
    verification_type="title_search",
    agent_id="agent_title_001",
    status="approved",
    findings={
        "title_status": "clear",
        "liens": [],
        "encumbrances": [],
        "ownership_verified": True
    },
    documents=[
        "https://storage.example.com/reports/title_search_123.pdf"
    ]
)
```

### Pattern 3: Monitor Transaction Progress

Poll for transaction updates:

```python
def monitor_transaction(self, transaction_id: str, poll_interval: int = 30):
    headers = {
        "Authorization": f"Bearer {self.token_manager.get_token()}"
    }
    
    while True:
        response = requests.get(
            f"{self.base_url}/api/escrow/transactions/{transaction_id}",
            headers=headers
        )
        response.raise_for_status()
        
        transaction = response.json()
        state = transaction["state"]
        
        print(f"Transaction {transaction_id} state: {state}")
        
        if state in ["settled", "cancelled", "disputed"]:
            print(f"Transaction reached terminal state: {state}")
            break
        
        time.sleep(poll_interval)
    
    return transaction

# Usage
final_transaction = integration.monitor_transaction("txn_abc123")
```

### Pattern 4: Execute Settlement

Escrow agent executes final settlement:

```python
def execute_settlement(
    self,
    transaction_id: str,
    buyer_agent_commission_rate: float = 0.025,
    seller_agent_commission_rate: float = 0.025,
    closing_costs: float = 5000.00
):
    headers = {
        "Authorization": f"Bearer {self.token_manager.get_token()}",
        "Content-Type": "application/json"
    }
    
    data = {
        "buyer_agent_commission_rate": buyer_agent_commission_rate,
        "seller_agent_commission_rate": seller_agent_commission_rate,
        "closing_costs": closing_costs
    }
    
    response = requests.post(
        f"{self.base_url}/api/escrow/transactions/{transaction_id}/settlement",
        headers=headers,
        json=data
    )
    response.raise_for_status()
    
    settlement = response.json()
    print(f"Settlement executed: {settlement['id']}")
    print(f"Seller amount: ${settlement['seller_amount']}")
    print(f"Blockchain TX: {settlement['blockchain_tx_hash']}")
    
    return settlement

# Usage
settlement = integration.execute_settlement("txn_abc123")
```

### Pattern 5: Handle Disputes

Raise and manage disputes:

```python
def raise_dispute(
    self,
    transaction_id: str,
    raised_by: str,
    dispute_type: str,
    description: str,
    evidence: list = None
):
    headers = {
        "Authorization": f"Bearer {self.token_manager.get_token()}",
        "Content-Type": "application/json"
    }
    
    data = {
        "raised_by": raised_by,
        "dispute_type": dispute_type,
        "description": description,
        "evidence": evidence or []
    }
    
    response = requests.post(
        f"{self.base_url}/api/escrow/transactions/{transaction_id}/disputes",
        headers=headers,
        json=data
    )
    response.raise_for_status()
    
    dispute = response.json()
    print(f"Dispute raised: {dispute['id']}")
    
    return dispute

# Usage
dispute = integration.raise_dispute(
    transaction_id="txn_abc123",
    raised_by="agent_buyer_001",
    dispute_type="verification_quality",
    description="Inspection report incomplete - missing roof assessment",
    evidence=["https://storage.example.com/evidence/photo1.jpg"]
)
```

## Testing

### Test Environment

Use the staging environment for testing:

```python
# Staging configuration
STAGING_BASE_URL = "https://staging-api.counterai.com"
STAGING_AGENT_ID = "test_agent_001"
STAGING_PASSWORD = "test_password"

# Create test client
test_token_manager = TokenManager(STAGING_AGENT_ID, STAGING_PASSWORD)
test_integration = EscrowIntegration(STAGING_BASE_URL, test_token_manager)
```

### Integration Test Example

```python
def test_complete_transaction_flow():
    # 1. Create transaction
    transaction = test_integration.create_transaction(
        buyer_agent_id="test_buyer_001",
        seller_agent_id="test_seller_001",
        property_id="test_prop_001",
        earnest_money=5000.00,
        total_purchase_price=250000.00,
        target_closing_date="2025-12-01T00:00:00Z"
    )
    
    assert transaction["state"] == "initiated"
    transaction_id = transaction["id"]
    
    # 2. Submit verification reports
    verifications = [
        ("title_search", "agent_title_001"),
        ("inspection", "agent_inspect_001"),
        ("appraisal", "agent_appraisal_001")
    ]
    
    for verification_type, agent_id in verifications:
        report = test_integration.submit_verification_report(
            transaction_id=transaction_id,
            verification_type=verification_type,
            agent_id=agent_id,
            status="approved",
            findings={"status": "approved"},
            documents=[]
        )
        assert report["payment_released"] == True
    
    # 3. Execute settlement
    settlement = test_integration.execute_settlement(transaction_id)
    assert settlement["executed_at"] is not None
    
    # 4. Verify final state
    final_transaction = test_integration.get_transaction(transaction_id)
    assert final_transaction["state"] == "settled"
    
    print("✓ Complete transaction flow test passed")

# Run test
test_complete_transaction_flow()
```

### Mock Webhook Testing

Test webhook handling locally:

```python
import json

def test_webhook_handler():
    handler = WebhookHandler("test_secret")
    
    # Mock webhook event
    event = {
        "event": "verification.completed",
        "timestamp": "2025-11-14T10:00:00Z",
        "data": {
            "transaction_id": "txn_test_001",
            "verification_type": "inspection",
            "agent_id": "agent_inspect_001",
            "status": "approved"
        }
    }
    
    # Test event handling
    handler.handle_event(event)
    
    print("✓ Webhook handler test passed")

test_webhook_handler()
```

## Production Checklist

### Security

- [ ] Store API credentials securely (environment variables, secrets manager)
- [ ] Use HTTPS for all API calls
- [ ] Implement webhook signature verification
- [ ] Rotate API tokens regularly
- [ ] Enable rate limiting on your webhook endpoint
- [ ] Implement IP whitelisting if possible

### Reliability

- [ ] Implement retry logic with exponential backoff
- [ ] Add circuit breaker for API calls
- [ ] Set appropriate timeouts (30s for API calls)
- [ ] Handle webhook retries idempotently
- [ ] Log all API interactions for debugging
- [ ] Monitor API error rates

### Monitoring

- [ ] Set up alerts for API errors
- [ ] Track transaction success rates
- [ ] Monitor webhook delivery failures
- [ ] Log correlation IDs for request tracing
- [ ] Set up health check monitoring
- [ ] Track API response times

### Data Management

- [ ] Store transaction IDs for reconciliation
- [ ] Backup webhook events
- [ ] Implement data retention policies
- [ ] Handle PII according to regulations
- [ ] Archive completed transactions

### Testing

- [ ] Test complete transaction flows in staging
- [ ] Test error scenarios (network failures, invalid data)
- [ ] Test webhook handling with retries
- [ ] Load test your webhook endpoint
- [ ] Test token refresh logic
- [ ] Verify audit trail access

### Documentation

- [ ] Document your integration architecture
- [ ] Create runbooks for common issues
- [ ] Document webhook event handlers
- [ ] Maintain API version compatibility matrix
- [ ] Document error handling procedures

## Support

For integration support:

- **Email**: support@counterai.com
- **Documentation**: https://docs.counterai.com
- **API Status**: https://status.counterai.com
- **Slack Community**: https://counterai.slack.com

## Appendix

### Complete Python Client Example

```python
# escrow_client.py
import requests
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

class TokenManager:
    """Manages JWT token lifecycle with automatic refresh."""
    
    def __init__(self, base_url: str, agent_id: str, password: str):
        self.base_url = base_url
        self.agent_id = agent_id
        self.password = password
        self.token: Optional[str] = None
        self.expires_at: Optional[datetime] = None
    
    def get_token(self) -> str:
        if self.token and self.expires_at and self.expires_at > datetime.now():
            return self.token
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"agent_id": self.agent_id, "password": self.password}
        )
        response.raise_for_status()
        data = response.json()
        
        self.token = data["access_token"]
        self.expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        
        return self.token


class EscrowClient:
    """Complete client for Intelligent Escrow Agents API."""
    
    def __init__(self, base_url: str, token_manager: TokenManager):
        self.base_url = base_url
        self.token_manager = token_manager
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token_manager.get_token()}",
            "Content-Type": "application/json"
        }
    
    def create_transaction(self, **kwargs) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/escrow/transactions",
            headers=self._headers(),
            json=kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/escrow/transactions/{transaction_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def list_transactions(self, **filters) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/escrow/transactions",
            headers=self._headers(),
            params=filters
        )
        response.raise_for_status()
        return response.json()
    
    def submit_verification(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/escrow/transactions/{transaction_id}/verifications",
            headers=self._headers(),
            json=kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def execute_settlement(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/escrow/transactions/{transaction_id}/settlement",
            headers=self._headers(),
            json=kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def raise_dispute(self, transaction_id: str, **kwargs) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/escrow/transactions/{transaction_id}/disputes",
            headers=self._headers(),
            json=kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def get_audit_trail(self, transaction_id: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/escrow/transactions/{transaction_id}/audit-trail",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()


# Usage example
if __name__ == "__main__":
    token_manager = TokenManager(
        base_url="https://api.counterai.com",
        agent_id="your_agent_id",
        password="your_password"
    )
    
    client = EscrowClient("https://api.counterai.com", token_manager)
    
    # Create transaction
    transaction = client.create_transaction(
        buyer_agent_id="agent_001",
        seller_agent_id="agent_002",
        property_id="prop_123",
        earnest_money=10000.00,
        total_purchase_price=500000.00,
        target_closing_date="2025-12-01T00:00:00Z"
    )
    
    print(f"Transaction created: {transaction['id']}")
```

### Environment Variables

```bash
# .env file
ESCROW_API_BASE_URL=https://api.counterai.com
ESCROW_AGENT_ID=your_agent_id
ESCROW_PASSWORD=your_password
ESCROW_WEBHOOK_SECRET=your_webhook_secret
ESCROW_WEBHOOK_URL=https://your-domain.com/webhooks/escrow
```

### Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('escrow_integration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('escrow_integration')
```
