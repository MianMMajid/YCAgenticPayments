
# Webhook URLs Configuration

This document tracks all webhook and callback URLs for development (ngrok) and production.

## Development URLs (ngrok)

### 1. DocuSign Webhook
**URL**: `https://ycnov15.ngrok.app/webhooks/docusign`

**Purpose**: Receive DocuSign envelope events (sent, completed, etc.)

**Configuration**:
- Configure in DocuSign Developer Console → Your App → Webhooks
- Enable events: "Envelope Sent", "Envelope Completed"
- Webhook secret: `yGAcVEZJYE4sP8CENvMa/s4XJJF5e6+cR6EyAWV2HxE=`
- Base URI: `https://demo.docusign.net` (demo environment)

**Endpoint**: `POST /webhooks/docusign`

**Note**: If you configured it as `/api/auth/callback/docusign` in DocuSign, you may need to update it to `/webhooks/docusign` to match the actual endpoint.

---

### 2. Google OAuth Callback
**URL**: `https://ycnov15googleoauth.ngrok.app/api/auth/callback/google`

**Purpose**: Handle Google OAuth callback for Calendar API authentication

**Configuration**:
- Configure in Google Cloud Console → APIs & Services → Credentials
- OAuth 2.0 Client ID → Authorized redirect URIs
- Add: `https://ycnov15googleoauth.ngrok.app/api/auth/callback/google`

**Endpoint**: `GET /api/auth/callback/google`

---

### 3. Agentic Stripe Webhook
**URL**: `https://your-ngrok-url.ngrok.app/webhooks/agentic-stripe`

**Purpose**: Receive Agentic Stripe smart contract wallet events

**Configuration**:
- Configure in Agentic Stripe Dashboard → Webhooks
- Enable events: "payment.success", "payment.failure", "wallet.balance_updated"
- Webhook secret: Set in `.env` as `AGENTIC_STRIPE_WEBHOOK_SECRET`

**Endpoint**: `POST /webhooks/agentic-stripe`

**Headers**:
- `X-Agentic-Stripe-Signature`: HMAC-SHA256 signature for verification

**Event Types**:
- `payment.success`: Payment successfully processed
- `payment.failure`: Payment processing failed
- `wallet.balance_updated`: Wallet balance changed

---

### 4. Verification Agent Webhooks
**URL**: `https://your-ngrok-url.ngrok.app/webhooks/verification/{verification_type}`

**Purpose**: Receive verification completion/failure notifications from verification agents

**Configuration**:
- Configure in each verification agent's settings
- Webhook authentication uses agent-specific signatures

**Endpoints**:
- `POST /webhooks/verification/title_search` - Title Search Agent
- `POST /webhooks/verification/inspection` - Inspection Agent
- `POST /webhooks/verification/appraisal` - Appraisal Agent
- `POST /webhooks/verification/lending` - Lending Agent

**Headers**:
- `X-Agent-Signature`: HMAC-SHA256 signature for verification
- `X-Agent-Id`: Agent identifier

**Event Types**:
- `verification.completed`: Verification successfully completed
- `verification.failed`: Verification failed

---

## Production URLs

When deploying to production, update these URLs:

### DocuSign Webhook
- Production: `https://your-domain.vercel.app/webhooks/docusign`
- Update in: DocuSign Developer Console

### Google OAuth Callback
- Production: `https://your-domain.vercel.app/api/auth/callback/google`
- Update in: Google Cloud Console → Credentials

---

## Testing Webhooks

### Test DocuSign Webhook
```bash
curl -X POST https://ycnov15.ngrok.app/webhooks/docusign \
  -H "Content-Type: application/json" \
  -H "X-DocuSign-Signature: test" \
  -d '{
    "event": "envelope-completed",
    "data": {
      "envelopeId": "test-123"
    }
  }'
```

### Test Google OAuth Flow
1. Navigate to: `https://ycnov15googleoauth.ngrok.app/api/auth/google`
2. Complete OAuth flow
3. Callback will be received at: `https://ycnov15googleoauth.ngrok.app/api/auth/callback/google`

### Test Agentic Stripe Webhook
```bash
curl -X POST https://your-ngrok-url.ngrok.app/webhooks/agentic-stripe \
  -H "Content-Type: application/json" \
  -H "X-Agentic-Stripe-Signature: <computed-signature>" \
  -d '{
    "event_id": "evt_123",
    "event_type": "payment.success",
    "wallet_id": "wallet_123",
    "transaction_id": "txn_123",
    "payment_id": "pay_123",
    "amount": "1200.00",
    "recipient": "agent_123",
    "status": "completed",
    "blockchain_tx_hash": "0x123...",
    "timestamp": "2025-11-14T12:00:00Z",
    "data": {}
  }'
```

### Test Verification Agent Webhook
```bash
curl -X POST https://your-ngrok-url.ngrok.app/webhooks/verification/title_search \
  -H "Content-Type: application/json" \
  -H "X-Agent-Signature: <computed-signature>" \
  -H "X-Agent-Id: agent_123" \
  -d '{
    "event_id": "evt_456",
    "event_type": "verification.completed",
    "transaction_id": "txn_123",
    "verification_type": "title_search",
    "agent_id": "agent_123",
    "report_id": "report_123",
    "status": "approved",
    "findings": {
      "title_clear": true,
      "liens": []
    },
    "documents": ["https://example.com/report.pdf"],
    "timestamp": "2025-11-14T12:00:00Z"
  }'
```

---

## Notes

- **ngrok URLs change** when you restart ngrok (unless using a paid plan with static domains)
- **Update both services** when ngrok URLs change:
  1. DocuSign Developer Console
  2. Google Cloud Console
- For **production**, use your Vercel domain instead of ngrok URLs

---

**Last Updated**: $(date)

