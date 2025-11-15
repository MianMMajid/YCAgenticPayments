# Locus MCP Integration Guide

**Reference**: [Locus MCP Spec](https://docs.paywithlocus.com/mcp-spec)

---

## Overview

Based on the Locus MCP Spec, Locus uses a **Model Context Protocol (MCP) server** architecture. The MCP server provides tools that AI agents can use to make payments.

### Architecture

```
AI Agent → MCP Client → MCP Server → Backend API → Smart Wallet → Base Network
```

---

## Built-in Payment Tools

According to the MCP spec, there are built-in payment tools:

### 1. `send_to_address`
**Purpose**: Send USDC to any wallet address  
**Required Scope**: `address_payments:write`  
**Parameters**:
- `address` (string, required) - Recipient wallet address (0x...)
- `amount` (number, required) - Amount in USDC (must be positive)
- `memo` (string, required) - Payment memo/description

**Returns**:
- Transaction ID
- Amount sent
- Recipient address
- Payment status

### 2. `send_to_contact`
**Purpose**: Send USDC to a whitelisted contact  
**Required Scope**: `contact_payments:write`  
**Parameters**:
- `contact_number` (number, required)
- `amount` (number, required)
- `memo` (string, required)

### 3. `send_to_email`
**Purpose**: Send USDC via escrow to an email address  
**Required Scope**: `email_payments:write`  
**Parameters**:
- `email` (string, required)
- `amount` (number, required)
- `memo` (string, optional)

---

## Authentication

### API Key Authentication
- API keys prefixed with `locus_` (e.g., `locus_dev_exC56yN_...`)
- Backend validates key and returns associated OAuth client scopes
- Used in `Authorization: Bearer {api_key}` header

### OAuth 2.0 Client Credentials (Alternative)
- Standard machine-to-machine authentication
- JWT tokens issued by AWS Cognito
- Scopes determine tool access

---

## Backend API Endpoints

Based on the MCP spec architecture, the backend API likely has these endpoints:

### Payment Endpoints
- `/api/mcp/send_to_address` - MCP proxy endpoint
- `/api/mcp/payments/send_to_address` - Alternative path
- `/api/v1/payments` - Direct backend endpoint

### Authentication
- Uses `Authorization: Bearer {api_key}` header
- API key must be prefixed with `locus_`

---

## Implementation

### Current Implementation

Our `LocusAPIClient` class:
1. ✅ Uses API key authentication (Bearer token)
2. ✅ Sends `send_to_address` payload format:
   ```json
   {
     "address": "0x...",
     "amount": 0.001,
     "memo": "Payment description"
   }
   ```
3. ✅ Tries multiple endpoint variations
4. ✅ Handles errors appropriately

### What We Need

The **actual backend API endpoint** that the MCP server calls. The MCP spec shows the tool interface but not the exact HTTP endpoint.

---

## Finding the Backend API Endpoint

### Method 1: Check MCP Server Code
If you have access to the MCP server implementation, check:
- How `send_to_address` tool calls the backend
- What HTTP endpoint it uses
- What the request format is

### Method 2: Browser DevTools
1. Log into Locus Dashboard
2. Open DevTools (F12) → Network tab
3. Make a test payment
4. Look for API calls to backend endpoints
5. Check the request format

### Method 3: MCP Client Library
If using the official MCP client (`@locus/mcp-client-credentials`):
- Check the source code
- See what endpoints it calls
- Replicate the same calls

### Method 4: Contact Locus
Ask for:
- Backend API base URL
- Payment endpoint path
- Request/response format
- Authentication method

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

## Current Status

✅ **Code Ready**: Implementation matches MCP spec structure  
❌ **Endpoint Unknown**: Need actual backend API endpoint

### What's Working
- ✅ API key authentication (Bearer token)
- ✅ Correct payload format (`address`, `amount`, `memo`)
- ✅ Error handling
- ✅ Multiple endpoint attempts

### What's Missing
- ❌ Actual backend API endpoint URL
- ❌ Confirmed request/response format
- ❌ Scope validation (if needed)

---

## Next Steps

1. **Find Backend Endpoint**:
   - Check browser DevTools when making payments in dashboard
   - Or contact Locus for API documentation
   - Or check MCP server source code

2. **Update Code**:
   - Add correct endpoint to `locus_api_client.py`
   - Test with real API call
   - Verify payment appears in Locus Live

3. **Test Payment**:
   ```bash
   python3 scripts/test_locus_a2a_payment.py
   ```

---

## References

- [Locus MCP Spec](https://docs.paywithlocus.com/mcp-spec)
- MCP Built-in Payment Tools: `send_to_address`, `send_to_contact`, `send_to_email`
- Authentication: API Key (prefixed `locus_`) or OAuth 2.0
- Backend: Handles payments via smart wallet on Base network

---

**Status**: ✅ Code structure matches MCP spec. Need actual backend API endpoint.

