# Finding the Locus Backend API Endpoint

**Reference**: [Locus MCP Spec](https://docs.paywithlocus.com/mcp-spec)

---

## Understanding the Architecture

Based on the MCP spec:

```
AI Agent → MCP Client → MCP Server → Backend API → Smart Wallet → Base Network
```

The **MCP Server** provides tools (like `send_to_address`), but the **Backend API** actually executes the payments.

---

## Method 1: Browser DevTools (Recommended)

### Step-by-Step

1. **Log into Locus Dashboard**
   - Go to: https://app.paywithlocus.com
   - Log in with your credentials

2. **Open Browser DevTools**
   - Press `F12` or `Cmd+Option+I` (Mac)
   - Go to **Network** tab
   - Check "Preserve log"

3. **Make a Test Payment**
   - In the dashboard, try to send a payment
   - Or view an existing transaction
   - Watch the Network tab for API calls

4. **Find the Payment Endpoint**
   - Look for POST requests
   - Check the URL - it should be something like:
     - `/api/mcp/...`
     - `/api/v1/payments/...`
     - `/api/payments/...`
   - Copy the **full URL** (including base URL)

5. **Check Request Format**
   - Click on the request
   - Go to **Payload** or **Request** tab
   - See the JSON structure
   - Copy the format

6. **Check Headers**
   - Go to **Headers** tab
   - See how authentication is done
   - Check `Authorization` header format

---

## Method 2: Check MCP Client Library

If you have access to the official MCP client:

1. **Install MCP Client**
   ```bash
   npm install @locus/mcp-client-credentials
   ```

2. **Check Source Code**
   - Look at how `send_to_address` is implemented
   - Find the backend API endpoint it calls
   - Replicate in our Python code

---

## Method 3: Contact Locus Support

Email or contact Locus and ask for:
- Backend API base URL
- Payment endpoint path (`/api/...`)
- Request/response format
- Authentication method

---

## Method 4: Try Common Patterns

Based on the MCP spec mentioning `/api/mcp/x402-proxy`, try:

```bash
# MCP proxy endpoints
https://api.paywithlocus.com/api/mcp/send_to_address
https://api.paywithlocus.com/api/mcp/payments/send_to_address

# Direct backend endpoints
https://api.paywithlocus.com/api/v1/payments
https://api.paywithlocus.com/api/v1/payments/send_to_address

# Alternative base URLs
https://backend.paywithlocus.com/api/payments
https://app.paywithlocus.com/api/payments
```

---

## Expected Request Format

Based on MCP spec `send_to_address` tool:

```http
POST /api/mcp/send_to_address
Authorization: Bearer locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG
Content-Type: application/json

{
  "address": "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d",
  "amount": 0.001,
  "memo": "Test A2A Payment"
}
```

---

## Once You Find It

1. **Update `.env`**:
   ```bash
   LOCUS_API_BASE_URL=https://actual-backend-url.com
   ```

2. **Or update code**:
   - Edit `services/locus_api_client.py`
   - Add endpoint to `endpoints` list
   - Or change `LOCUS_API_BASE_URL`

3. **Test**:
   ```bash
   python3 scripts/test_locus_a2a_payment.py
   ```

---

## Alternative: Use MCP Client Directly

If the backend API is not accessible, you could:

1. **Use the official MCP client** (`@locus/mcp-client-credentials`)
2. **Call MCP tools** from Python via subprocess or HTTP
3. **Let MCP handle** the backend communication

This would require:
- Installing Node.js
- Using the MCP client library
- Calling MCP tools from Python

---

**Next Step**: Use Browser DevTools to find the actual endpoint when making a payment in the Locus dashboard.

