# API Documentation

## Overview

The Counter AI Real Estate Broker & Intelligent Escrow Agents API provides a comprehensive platform for automating real estate transactions with AI-powered agents and smart contract-based escrow management.

## Base URLs

- **Production**: `https://api.counterai.com`
- **Staging**: `https://staging-api.counterai.com`
- **Development**: `http://localhost:8000`

## Interactive Documentation

Once the API server is running, you can access interactive documentation at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Authentication

All escrow API endpoints require JWT-based authentication. Agents must authenticate before accessing protected resources.

### Authentication Flow

1. **Register Agent** (if not already registered)
2. **Login** to obtain JWT access token
3. **Include token** in `Authorization` header for all requests

### Endpoints

#### Register Agent

```http
POST /auth/register
Content-Type: application/json

{
  "agent_id": "agent_12345",
  "agent_type": "buyer_agent",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "license_number": "CA-DRE-12345678"
}
```

**Response:**
```json
{
  "agent_id": "agent_12345",
  "agent_type": "buyer_agent",
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2025-11-14T10:00:00Z"
}
```

#### Login

```http
POST /auth/login
Content-Type: application/json

{
  "agent_id": "agent_12345",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Using the Token

Include the token in the `Authorization` header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Core API Endpoints

### Transaction Management

#### Initiate Transaction

Create a new escrow transaction with earnest money deposit.

```http
POST /api/escrow/transactions
Authorization: Bearer {token}
Content-Type: application/json

{
  "buyer_agent_id": "agent_buyer_001",
  "seller_agent_id": "agent_seller_001",
  "property_id": "prop_12345",
  "earnest_money": 10000.00,
  "total_purchase_price": 500000.00,
  "target_closing_date": "2025-12-01T00:00:00Z",
  "metadata": {
    "property_address": "123 Main St, San Francisco, CA 94102",
    "buyer_name": "Alice Johnson",
    "seller_name": "Bob Smith"
  }
}
```

**Response:**
```json
{
  "id": "txn_abc123",
  "buyer_agent_id": "agent_buyer_001",
  "seller_agent_id": "agent_seller_001",
  "property_id": "prop_12345",
  "earnest_money": 10000.00,
  "total_purchase_price": 500000.00,
  "state": "initiated",
  "wallet_id": "wallet_xyz789",
  "initiated_at": "2025-11-14T10:00:00Z",
  "target_closing_date": "2025-12-01T00:00:00Z",
  "created_at": "2025-11-14T10:00:00Z"
}
```

#### Get Transaction Details

```http
GET /api/escrow/transactions/{transaction_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "txn_abc123",
  "buyer_agent_id": "agent_buyer_001",
  "seller_agent_id": "agent_seller_001",
  "property_id": "prop_12345",
  "earnest_money": 10000.00,
  "total_purchase_price": 500000.00,
  "state": "verification_in_progress",
  "wallet_id": "wallet_xyz789",
  "initiated_at": "2025-11-14T10:00:00Z",
  "target_closing_date": "2025-12-01T00:00:00Z",
  "actual_closing_date": null,
  "metadata": {
    "property_address": "123 Main St, San Francisco, CA 94102"
  },
  "created_at": "2025-11-14T10:00:00Z",
  "updated_at": "2025-11-14T10:05:00Z"
}
```

#### List Transactions

```http
GET /api/escrow/transactions?state=verification_in_progress&limit=10&offset=0
Authorization: Bearer {token}
```

**Query Parameters:**
- `state` (optional): Filter by transaction state
- `buyer_agent_id` (optional): Filter by buyer agent
- `seller_agent_id` (optional): Filter by seller agent
- `limit` (optional): Number of results (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "transactions": [
    {
      "id": "txn_abc123",
      "state": "verification_in_progress",
      "earnest_money": 10000.00,
      "total_purchase_price": 500000.00,
      "initiated_at": "2025-11-14T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### Cancel Transaction

```http
DELETE /api/escrow/transactions/{transaction_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "txn_abc123",
  "state": "cancelled",
  "cancelled_at": "2025-11-14T11:00:00Z"
}
```

### Verification Management

#### List Verification Tasks

```http
GET /api/escrow/transactions/{transaction_id}/verifications
Authorization: Bearer {token}
```

**Response:**
```json
{
  "verifications": [
    {
      "id": "ver_title_001",
      "transaction_id": "txn_abc123",
      "verification_type": "title_search",
      "assigned_agent_id": "agent_title_001",
      "status": "in_progress",
      "deadline": "2025-11-19T10:00:00Z",
      "payment_amount": 1200.00,
      "assigned_at": "2025-11-14T10:00:00Z"
    },
    {
      "id": "ver_inspect_001",
      "transaction_id": "txn_abc123",
      "verification_type": "inspection",
      "assigned_agent_id": "agent_inspect_001",
      "status": "completed",
      "deadline": "2025-11-21T10:00:00Z",
      "payment_amount": 500.00,
      "assigned_at": "2025-11-14T10:00:00Z",
      "completed_at": "2025-11-16T14:30:00Z"
    }
  ],
  "total": 4
}
```

#### Submit Verification Report

```http
POST /api/escrow/transactions/{transaction_id}/verifications
Authorization: Bearer {token}
Content-Type: application/json

{
  "verification_type": "inspection",
  "agent_id": "agent_inspect_001",
  "status": "approved",
  "findings": {
    "overall_condition": "good",
    "issues_found": [
      "Minor roof repair needed",
      "HVAC filter replacement recommended"
    ],
    "estimated_repair_cost": 2500.00
  },
  "documents": [
    "https://storage.example.com/reports/inspection_123.pdf"
  ]
}
```

**Response:**
```json
{
  "id": "report_inspect_001",
  "task_id": "ver_inspect_001",
  "agent_id": "agent_inspect_001",
  "report_type": "inspection",
  "status": "approved",
  "findings": {
    "overall_condition": "good",
    "issues_found": ["Minor roof repair needed"]
  },
  "submitted_at": "2025-11-16T14:30:00Z",
  "payment_released": true,
  "payment_amount": 500.00
}
```

#### Get Verification Details

```http
GET /api/escrow/verifications/{verification_id}
Authorization: Bearer {token}
```

### Payment Management

#### List Payments

```http
GET /api/escrow/transactions/{transaction_id}/payments
Authorization: Bearer {token}
```

**Response:**
```json
{
  "payments": [
    {
      "id": "pay_001",
      "transaction_id": "txn_abc123",
      "payment_type": "earnest_money",
      "recipient_id": "wallet_xyz789",
      "amount": 10000.00,
      "status": "completed",
      "blockchain_tx_hash": "0x1234...abcd",
      "initiated_at": "2025-11-14T10:00:00Z",
      "completed_at": "2025-11-14T10:01:00Z"
    },
    {
      "id": "pay_002",
      "transaction_id": "txn_abc123",
      "payment_type": "verification",
      "recipient_id": "agent_inspect_001",
      "amount": 500.00,
      "status": "completed",
      "blockchain_tx_hash": "0x5678...efgh",
      "initiated_at": "2025-11-16T14:30:00Z",
      "completed_at": "2025-11-16T14:31:00Z"
    }
  ],
  "total": 2
}
```

#### Get Payment Details

```http
GET /api/escrow/payments/{payment_id}
Authorization: Bearer {token}
```

#### Retry Failed Payment

```http
POST /api/escrow/payments/{payment_id}/retry
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "pay_003",
  "status": "pending",
  "retry_attempt": 1,
  "initiated_at": "2025-11-14T11:00:00Z"
}
```

### Settlement Management

#### Execute Settlement

```http
POST /api/escrow/transactions/{transaction_id}/settlement
Authorization: Bearer {token}
Content-Type: application/json

{
  "buyer_agent_commission_rate": 0.025,
  "seller_agent_commission_rate": 0.025,
  "closing_costs": 5000.00
}
```

**Response:**
```json
{
  "id": "settle_001",
  "transaction_id": "txn_abc123",
  "total_amount": 500000.00,
  "seller_amount": 462400.00,
  "buyer_agent_commission": 12500.00,
  "seller_agent_commission": 12500.00,
  "closing_costs": 5000.00,
  "verification_payments": 2100.00,
  "distributions": [
    {
      "recipient_id": "agent_seller_001",
      "amount": 462400.00,
      "type": "seller_proceeds"
    },
    {
      "recipient_id": "agent_buyer_001",
      "amount": 12500.00,
      "type": "commission"
    },
    {
      "recipient_id": "agent_seller_001",
      "amount": 12500.00,
      "type": "commission"
    }
  ],
  "blockchain_tx_hash": "0x9abc...def0",
  "executed_at": "2025-11-28T15:00:00Z"
}
```

#### Get Settlement Details

```http
GET /api/escrow/transactions/{transaction_id}/settlement
Authorization: Bearer {token}
```

### Audit Trail

#### Get Transaction Audit Trail

```http
GET /api/escrow/transactions/{transaction_id}/audit-trail
Authorization: Bearer {token}
```

**Response:**
```json
{
  "transaction_id": "txn_abc123",
  "events": [
    {
      "id": "evt_001",
      "event_type": "transaction_initiated",
      "event_data": {
        "earnest_money": 10000.00,
        "buyer_agent_id": "agent_buyer_001"
      },
      "blockchain_tx_hash": "0x1111...2222",
      "block_number": 12345678,
      "timestamp": "2025-11-14T10:00:00Z"
    },
    {
      "id": "evt_002",
      "event_type": "verification_completed",
      "event_data": {
        "verification_type": "inspection",
        "agent_id": "agent_inspect_001"
      },
      "blockchain_tx_hash": "0x3333...4444",
      "block_number": 12345890,
      "timestamp": "2025-11-16T14:30:00Z"
    }
  ],
  "total": 15
}
```

#### Verify Blockchain Event

```http
POST /api/escrow/events/{transaction_hash}/verify
Authorization: Bearer {token}
```

**Response:**
```json
{
  "transaction_hash": "0x1111...2222",
  "verified": true,
  "block_number": 12345678,
  "confirmations": 1000,
  "timestamp": "2025-11-14T10:00:00Z"
}
```

### Dispute Management

#### Raise Dispute

```http
POST /api/escrow/transactions/{transaction_id}/disputes
Authorization: Bearer {token}
Content-Type: application/json

{
  "raised_by": "agent_buyer_001",
  "dispute_type": "verification_quality",
  "description": "Inspection report incomplete - missing roof assessment",
  "evidence": [
    "https://storage.example.com/evidence/photo1.jpg"
  ]
}
```

**Response:**
```json
{
  "id": "dispute_001",
  "transaction_id": "txn_abc123",
  "raised_by": "agent_buyer_001",
  "dispute_type": "verification_quality",
  "status": "open",
  "description": "Inspection report incomplete",
  "raised_at": "2025-11-17T09:00:00Z"
}
```

#### List Disputes

```http
GET /api/escrow/transactions/{transaction_id}/disputes
Authorization: Bearer {token}
```

#### Update Dispute Status

```http
PATCH /api/escrow/disputes/{dispute_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "resolved",
  "resolution": "Re-inspection completed with full roof assessment",
  "resolved_by": "escrow_agent_001"
}
```

### Wallet Security

#### Configure Multi-Signature

```http
POST /api/escrow/transactions/{transaction_id}/wallet/multisig
Authorization: Bearer {token}
Content-Type: application/json

{
  "required_signatures": 2,
  "signers": [
    "agent_buyer_001",
    "agent_seller_001",
    "escrow_agent_001"
  ]
}
```

#### Set Time Lock

```http
POST /api/escrow/transactions/{transaction_id}/wallet/timelock
Authorization: Bearer {token}
Content-Type: application/json

{
  "unlock_time": "2025-11-28T00:00:00Z",
  "reason": "Cooling-off period"
}
```

#### Emergency Pause

```http
POST /api/escrow/transactions/{transaction_id}/wallet/pause
Authorization: Bearer {token}
Content-Type: application/json

{
  "reason": "Security concern - investigating unauthorized access attempt"
}
```

## Webhooks

The system sends webhooks to notify agents of important events. Configure webhook URLs during agent registration or via the settings endpoint.

### Webhook Events

- `transaction.initiated` - New transaction created
- `transaction.funded` - Earnest money received
- `verification.assigned` - Task assigned to agent
- `verification.completed` - Verification report submitted
- `payment.released` - Milestone payment processed
- `settlement.executed` - Final settlement completed
- `dispute.raised` - Dispute opened
- `transaction.cancelled` - Transaction cancelled

### Webhook Payload

```json
{
  "event": "verification.completed",
  "timestamp": "2025-11-16T14:30:00Z",
  "data": {
    "transaction_id": "txn_abc123",
    "verification_id": "ver_inspect_001",
    "verification_type": "inspection",
    "agent_id": "agent_inspect_001",
    "status": "approved",
    "payment_amount": 500.00
  },
  "signature": "sha256=abc123..."
}
```

### Webhook Signature Verification

Verify webhook authenticity using HMAC-SHA256:

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Error Handling

### Error Response Format

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

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `AUTHENTICATION_ERROR` | 401 | Missing or invalid token |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource state conflict |
| `PAYMENT_ERROR` | 422 | Payment processing failed |
| `WORKFLOW_ERROR` | 422 | Workflow execution failed |
| `INTEGRATION_ERROR` | 502 | External service failure |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

### Retry Logic

For transient errors (5xx, network timeouts), implement exponential backoff:

```python
import time
import requests

def api_call_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait_time)
```

## Rate Limiting

- **Default**: 100 requests per minute per agent
- **Burst**: Up to 20 requests in 1 second
- **Headers**: 
  - `X-RateLimit-Limit`: Total requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

## Pagination

List endpoints support pagination:

```http
GET /api/escrow/transactions?limit=50&offset=0
```

**Response includes pagination metadata:**
```json
{
  "transactions": [...],
  "total": 150,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

## Filtering and Sorting

Most list endpoints support filtering and sorting:

```http
GET /api/escrow/transactions?state=verification_in_progress&sort=-created_at
```

**Common filters:**
- `state`: Transaction state
- `buyer_agent_id`: Buyer agent ID
- `seller_agent_id`: Seller agent ID
- `created_after`: ISO 8601 timestamp
- `created_before`: ISO 8601 timestamp

**Sorting:**
- Prefix with `-` for descending order
- Examples: `created_at`, `-updated_at`, `earnest_money`

## Health Checks

### Liveness Probe

```http
GET /health/live
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-14T10:00:00Z"
}
```

### Readiness Probe

```http
GET /health/ready
```

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "agentic_stripe": "healthy",
    "blockchain": "healthy"
  },
  "timestamp": "2025-11-14T10:00:00Z"
}
```

## Metrics

### Prometheus Metrics

```http
GET /metrics
```

**Key metrics:**
- `escrow_transactions_total`: Total transactions created
- `escrow_transactions_by_state`: Transactions grouped by state
- `escrow_closing_cycle_time_seconds`: Time from initiation to settlement
- `escrow_verification_completion_rate`: Percentage of verifications completed on time
- `escrow_payment_success_rate`: Percentage of successful payments
- `api_request_duration_seconds`: API response time histogram

## SDKs and Client Libraries

### Python Example

```python
import requests

class EscrowClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def create_transaction(self, data: dict):
        response = requests.post(
            f"{self.base_url}/api/escrow/transactions",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_transaction(self, transaction_id: str):
        response = requests.get(
            f"{self.base_url}/api/escrow/transactions/{transaction_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = EscrowClient("http://localhost:8000", "your_token_here")
transaction = client.create_transaction({
    "buyer_agent_id": "agent_001",
    "seller_agent_id": "agent_002",
    "property_id": "prop_123",
    "earnest_money": 10000.00,
    "total_purchase_price": 500000.00,
    "target_closing_date": "2025-12-01T00:00:00Z"
})
print(f"Transaction created: {transaction['id']}")
```

### JavaScript Example

```javascript
class EscrowClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async createTransaction(data) {
    const response = await fetch(`${this.baseUrl}/api/escrow/transactions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  }

  async getTransaction(transactionId) {
    const response = await fetch(
      `${this.baseUrl}/api/escrow/transactions/${transactionId}`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    );
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  }
}

// Usage
const client = new EscrowClient('http://localhost:8000', 'your_token_here');
const transaction = await client.createTransaction({
  buyer_agent_id: 'agent_001',
  seller_agent_id: 'agent_002',
  property_id: 'prop_123',
  earnest_money: 10000.00,
  total_purchase_price: 500000.00,
  target_closing_date: '2025-12-01T00:00:00Z'
});
console.log(`Transaction created: ${transaction.id}`);
```

## Support

For API support and questions:
- Email: support@counterai.com
- Documentation: https://docs.counterai.com
- Status Page: https://status.counterai.com
