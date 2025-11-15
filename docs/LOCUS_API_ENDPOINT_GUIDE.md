# Finding the Correct Locus API Endpoint

## Current Status

The Locus API client is trying to make payments, but we need to find the **correct API endpoint** from Locus documentation.

## What We've Tried

The following endpoints returned 404:
- `https://api.paywithlocus.com/v1/payments`
- `https://api.paywithlocus.com/api/v1/payments`
- `https://api.paywithlocus.com/payments`
- `https://api.paywithlocus.com/v1/agents/{agent_id}/payments`

## How to Find the Correct Endpoint

### Method 1: Check Locus Dashboard
1. Log into [Locus Dashboard](https://app.paywithlocus.com)
2. Look for **API Documentation** or **Developer** section
3. Check for **API Base URL** and **Payment Endpoints**

### Method 2: Check Browser Network Tab
1. Log into Locus Dashboard
2. Open browser DevTools (F12)
3. Go to **Network** tab
4. Make a test payment or view transactions
5. Look for API calls - the endpoint URL will be visible

### Method 3: Contact Locus Support
- Email: support@paywithlocus.com (or check their website)
- Ask for: API documentation, payment endpoint, authentication method

### Method 4: Check Locus Documentation
- Visit: https://docs.paywithlocus.com
- Look for: API reference, payment endpoints, agent-to-agent payments

## Expected API Structure

Based on common API patterns, the endpoint might be:

```bash
# Option 1: Direct payment endpoint
POST https://api.paywithlocus.com/v1/payments
Authorization: Bearer {agent_api_key}
Content-Type: application/json

{
  "agent_id": "ooeju0aot520uv7dd77nr7d5r",
  "amount": 0.001,
  "currency": "USDC",
  "recipient_wallet": "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d",
  "description": "Test payment"
}

# Option 2: Agent-specific endpoint
POST https://api.paywithlocus.com/v1/agents/{agent_id}/payments
Authorization: Bearer {agent_api_key}

# Option 3: Transaction-based
POST https://api.paywithlocus.com/v1/transactions
Authorization: Bearer {agent_api_key}
```

## Once You Find the Endpoint

1. **Update `LOCUS_API_BASE_URL`** in `.env`:
   ```bash
   LOCUS_API_BASE_URL=https://api.paywithlocus.com  # or actual URL
   ```

2. **Update `services/locus_api_client.py`**:
   - Change `LOCUS_API_BASE_URL` constant
   - Or add the endpoint to the `endpoints` list in `execute_payment()`

3. **Test the payment**:
   ```bash
   python3 scripts/test_locus_a2a_payment.py
   ```

## Alternative: Direct Blockchain Payment

If Locus doesn't have a REST API, payments might be made directly on-chain:

1. **Sign transaction** with wallet private key
2. **Broadcast to Base network** (Chain ID 8453)
3. **Locus tracks** the transaction on-chain

In this case, we'd need to:
- Use web3.py or similar library
- Sign USDC transfer transaction
- Send to Base network
- Locus dashboard reads from blockchain

## Current Implementation

The code is ready to make API calls once we have the correct endpoint. The `LocusAPIClient` class:
- ✅ Handles authentication (Bearer token with API key)
- ✅ Tries multiple endpoint variations
- ✅ Provides detailed error messages
- ✅ Returns structured payment results

**Next Step**: Find the actual Locus API endpoint and update the code.

