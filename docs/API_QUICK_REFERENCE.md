# API Quick Reference

Quick reference for the Intelligent Escrow Agents API.

## Base URL

```
Production: https://api.counterai.com
Staging: https://staging-api.counterai.com
Local: http://localhost:8000
```

## Authentication

```bash
# Login
curl -X POST https://api.counterai.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "your_agent_id", "password": "your_password"}'

# Use token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.counterai.com/api/escrow/transactions
```

## Common Endpoints

### Create Transaction
```bash
POST /api/escrow/transactions
{
  "buyer_agent_id": "agent_001",
  "seller_agent_id": "agent_002",
  "property_id": "prop_123",
  "earnest_money": 10000.00,
  "total_purchase_price": 500000.00,
  "target_closing_date": "2025-12-01T00:00:00Z"
}
```

### Get Transaction
```bash
GET /api/escrow/transactions/{transaction_id}
```

### Submit Verification
```bash
POST /api/escrow/transactions/{transaction_id}/verifications
{
  "verification_type": "inspection",
  "agent_id": "agent_inspect_001",
  "status": "approved",
  "findings": {...},
  "documents": [...]
}
```

### Execute Settlement
```bash
POST /api/escrow/transactions/{transaction_id}/settlement
{
  "buyer_agent_commission_rate": 0.025,
  "seller_agent_commission_rate": 0.025,
  "closing_costs": 5000.00
}
```

### Get Audit Trail
```bash
GET /api/escrow/transactions/{transaction_id}/audit-trail
```

## Transaction States

- `initiated` → `funded` → `verification_in_progress` → `verification_complete` → `settlement_pending` → `settled`
- Alternative: `disputed`, `cancelled`

## Verification Types

- `title_search` - $1,200
- `inspection` - $500
- `appraisal` - $400
- `lending` - No direct payment

## Webhook Events

- `transaction.initiated`
- `transaction.funded`
- `verification.assigned`
- `verification.completed`
- `payment.released`
- `settlement.executed`
- `dispute.raised`
- `transaction.cancelled`

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request |
| `AUTHENTICATION_ERROR` | 401 | Invalid token |
| `AUTHORIZATION_ERROR` | 403 | No permission |
| `NOT_FOUND` | 404 | Not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## Rate Limits

- 100 requests/minute per agent
- Burst: 20 requests/second

## Python Quick Start

```python
import requests

# Login
response = requests.post(
    "https://api.counterai.com/auth/login",
    json={"agent_id": "your_id", "password": "your_pass"}
)
token = response.json()["access_token"]

# Create transaction
headers = {"Authorization": f"Bearer {token}"}
transaction = requests.post(
    "https://api.counterai.com/api/escrow/transactions",
    headers=headers,
    json={
        "buyer_agent_id": "agent_001",
        "seller_agent_id": "agent_002",
        "property_id": "prop_123",
        "earnest_money": 10000.00,
        "total_purchase_price": 500000.00,
        "target_closing_date": "2025-12-01T00:00:00Z"
    }
).json()

print(f"Transaction ID: {transaction['id']}")
```

## JavaScript Quick Start

```javascript
// Login
const response = await fetch('https://api.counterai.com/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    agent_id: 'your_id',
    password: 'your_pass'
  })
});
const {access_token} = await response.json();

// Create transaction
const transaction = await fetch(
  'https://api.counterai.com/api/escrow/transactions',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      buyer_agent_id: 'agent_001',
      seller_agent_id: 'agent_002',
      property_id: 'prop_123',
      earnest_money: 10000.00,
      total_purchase_price: 500000.00,
      target_closing_date: '2025-12-01T00:00:00Z'
    })
  }
).then(r => r.json());

console.log(`Transaction ID: ${transaction.id}`);
```

## Documentation Links

- **Full API Docs**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Integration Guide**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Support

- Email: support@counterai.com
- Docs: https://docs.counterai.com
- Status: https://status.counterai.com
