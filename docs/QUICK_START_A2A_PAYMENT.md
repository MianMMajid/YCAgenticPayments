# Quick Start: Make A2A Payment on Locus Live

## Step 1: Find the API Endpoint

1. Open https://app.paywithlocus.com
2. Press F12 → Network tab
3. Make a test payment in the dashboard
4. Find the POST request
5. Copy the endpoint URL

## Step 2: Update Code

Add to `.env`:
```bash
LOCUS_API_BASE_URL=https://actual-backend-url.com
```

Or edit `services/locus_api_client.py` and add the endpoint to the `endpoints` list.

## Step 3: Test

```bash
python3 scripts/test_locus_a2a_payment.py
```

## What You'll See

If successful:
```
✅ PAYMENT SUCCESSFUL!
  Transaction Hash: 0x...
  Amount: 0.001 USDC
  Recipient: 0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d

🎉 Check your Locus Live dashboard to see this transaction!
```

The payment will appear in your Locus Live dashboard!

---

**Current Status**: Code ready, need endpoint URL from dashboard.

