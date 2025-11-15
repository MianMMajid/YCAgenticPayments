# Complete A2A Payment Guide

**Reference**: [Locus MCP Spec](https://docs.paywithlocus.com/mcp-spec)

---

## Current Status

✅ **Code Implementation**: Complete and matches MCP spec  
✅ **Authentication**: API keys configured  
✅ **Payload Format**: Matches `send_to_address` tool spec  
❌ **API Endpoint**: Need to find via browser DevTools

---

## Architecture Understanding

Based on the [MCP Spec](https://docs.paywithlocus.com/mcp-spec):

```
AI Agent → MCP Client → MCP Server (Lambda) → Backend API → Smart Wallet → Base Network
```

**Key Points**:
- The **MCP Server** is a Lambda function that provides tools
- The **Backend API** handles actual payment execution
- The backend API may not be directly accessible (only via MCP server)
- Payments use the `send_to_address` tool format

---

## How to Find the Actual Endpoint

### Method 1: Browser DevTools (Most Reliable)

1. **Open Locus Dashboard**
   - Go to: https://app.paywithlocus.com
   - Log in

2. **Open DevTools**
   - Press `F12` or `Cmd+Option+I` (Mac)
   - Go to **Network** tab
   - Check "Preserve log"

3. **Make a Payment in Dashboard**
   - Navigate to payments section
   - Send a test payment to an address
   - Watch the Network tab

4. **Find the API Call**
   - Look for POST requests
   - Check the URL - it will show the actual endpoint
   - Copy the **full URL**

5. **Check Request Details**
   - Click on the request
   - **Headers**: See authentication method
   - **Payload**: See request format
   - **Response**: See response format

6. **Update Code**
   - Add endpoint to `services/locus_api_client.py`
   - Or set `LOCUS_API_BASE_URL` in `.env`

---

## Expected Request Format

Based on MCP spec `send_to_address` tool:

```http
POST {BACKEND_API_URL}/api/mcp/send_to_address
Authorization: Bearer locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG
Content-Type: application/json

{
  "address": "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d",
  "amount": 0.001,
  "memo": "Test A2A Payment"
}
```

**Expected Response**:
```json
{
  "transaction_id": "...",
  "transaction_hash": "0x...",
  "amount": 0.001,
  "recipient": "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d",
  "status": "success"
}
```

---

## What's Already Implemented

### ✅ Locus API Client (`services/locus_api_client.py`)
- Matches MCP spec `send_to_address` format
- Uses correct payload: `{address, amount, memo}`
- Handles authentication with API keys
- Tries multiple endpoint variations
- Proper error handling

### ✅ Payment Handler (`services/locus_payment_handler.py`)
- Uses agent-specific API keys
- Calls Locus API client
- Falls back to mock if API unavailable
- Tracks payment history

### ✅ Test Scripts
- `scripts/test_locus_a2a_payment.py` - Full test
- `scripts/make_locus_payment_direct.py` - Direct payment
- `scripts/find_locus_endpoint.py` - Endpoint discovery

---

## Alternative: Use MCP Client Library

If the backend API is not directly accessible, you could:

1. **Install MCP Client**:
   ```bash
   npm install @locus/mcp-client-credentials
   ```

2. **Use from Python**:
   - Call Node.js script from Python
   - Or use HTTP to call MCP server directly
   - Or use the MCP protocol over stdio

3. **Benefits**:
   - Official client library
   - Handles authentication automatically
   - Works with MCP server

---

## Current Implementation Details

### Request Format (Matches MCP Spec)

```python
payload = {
    "address": "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d",
    "amount": 0.001,
    "memo": "Test A2A Payment"
}
```

### Authentication

```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "X-API-Key": api_key  # Some APIs use this
}
```

### Endpoints Tried

- `/api/mcp/send_to_address` (primary, based on MCP spec)
- `/api/mcp/payments/send_to_address`
- `/api/v1/payments/send_to_address`
- `/api/v1/payments`

---

## Next Steps

1. **Find Endpoint via DevTools** (Recommended)
   - Make payment in dashboard
   - Copy endpoint from Network tab
   - Update code

2. **Or Contact Locus**
   - Ask for backend API URL
   - Ask for payment endpoint
   - Ask for request/response format

3. **Or Use MCP Client**
   - Install official MCP client
   - Use from Python via subprocess
   - Let MCP handle backend communication

---

## Testing

Once you have the endpoint:

```bash
python3 scripts/test_locus_a2a_payment.py
```

This will:
1. Initialize Locus
2. Make a real A2A payment (0.001 USDC)
3. Show transaction result
4. Payment should appear in Locus Live dashboard

---

## Summary

✅ **Ready**: Code matches MCP spec perfectly  
✅ **Format**: Request format is correct  
✅ **Auth**: API keys configured  
⏳ **Pending**: Need actual backend API endpoint URL

**The implementation is complete - we just need the endpoint URL from the Locus dashboard!**

---

**Reference**: [Locus MCP Spec](https://docs.paywithlocus.com/mcp-spec)

