# A2A Payment Setup Guide

## Current Status

✅ **Code Ready**: Payment handler and API client are implemented  
❌ **API Endpoint Unknown**: Need to find the correct Locus API endpoint

## What's Implemented

1. ✅ **Locus API Client** (`services/locus_api_client.py`)
   - Handles authentication with agent API keys
   - Tries multiple endpoint variations
   - Provides detailed error messages

2. ✅ **Payment Handler** (`services/locus_payment_handler.py`)
   - Uses agent-specific API keys
   - Falls back to mock if API unavailable
   - Tracks payment history

3. ✅ **Test Script** (`scripts/test_locus_a2a_payment.py`)
   - Makes real A2A payments
   - Shows detailed results

## Finding the Correct API Endpoint

### Option 1: Check Locus Dashboard

1. **Log into Dashboard**: https://app.paywithlocus.com
2. **Look for**:
   - "API" or "Developer" section
   - "Documentation" link
   - Network requests in browser DevTools

### Option 2: Check Browser Network Tab

1. Open Locus Dashboard
2. Press F12 → Network tab
3. Make a test payment or view transactions
4. Look for API calls - the endpoint will be visible

### Option 3: Check Locus Documentation

- Visit: https://docs.paywithlocus.com
- Look for: API reference, payment endpoints

### Option 4: Contact Locus Support

Ask for:
- API base URL
- Payment endpoint
- Authentication method
- Request/response format

## Once You Have the Endpoint

### Update Environment Variable

Add to `.env`:
```bash
LOCUS_API_BASE_URL=https://api.paywithlocus.com  # or actual URL
```

### Or Update Code Directly

Edit `services/locus_api_client.py`:
```python
LOCUS_API_BASE_URL = "https://actual-api-url.com"  # Replace with real URL
```

### Add Endpoint to List

In `services/locus_api_client.py`, add the endpoint to the `endpoints` list:
```python
endpoints = [
    "https://actual-endpoint.com/v1/payments",  # Add here
    # ... existing endpoints
]
```

## Testing

Once the endpoint is configured:

```bash
python3 scripts/test_locus_a2a_payment.py
```

This will:
1. Initialize Locus
2. Make a real A2A payment (0.001 USDC)
3. Show the transaction result
4. Payment should appear in Locus Live dashboard

## Expected Result

When successful, you should see:
```
✅ PAYMENT SUCCESSFUL!
  Transaction Hash: 0x...
  Locus TX ID: ...
  Amount: 0.001 USDC
  Recipient: 0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d

🎉 Check your Locus Live dashboard to see this transaction!
```

## Current Error

All endpoints return 404, which means:
- The API base URL might be wrong
- The endpoint path might be different
- Locus might use a different API structure

**Next Step**: Find the correct endpoint from Locus documentation or dashboard.

