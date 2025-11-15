# MCP Spec Analysis - Backend API Endpoint Discovery

Based on the [Locus MCP Spec](https://docs.paywithlocus.com/mcp-spec), here's what we learned:

## Architecture

```
AI Agent → MCP Client → MCP Lambda Server → Backend API → Smart Wallet → Blockchain
```

## Key Findings

### 1. MCP Server is a Lambda Function
- The MCP server is a Lambda function that validates OAuth tokens
- It registers built-in payment tools
- It proxies tool execution to the backend API

### 2. Built-in Payment Tools
The `send_to_address` tool is a **built-in payment tool** that:
- Requires scope: `address_payments:write`
- Parameters: `address`, `amount`, `memo`
- Returns: Transaction ID, amount sent, recipient address, payment status

### 3. Backend API Proxy
The MCP server proxies tool calls to a **backend API**. The backend:
- Manages policy groups & approvals
- Executes payments (smart wallet)
- Returns transaction details

### 4. Authentication
Two methods supported:
- **OAuth 2.0 Client Credentials** (Client ID + Secret)
- **API Key** (prefixed with `locus_`)

## What We Need

Since we're using Python (not Node.js MCP client), we need to find the **backend API endpoint** that the MCP server calls.

Based on the architecture, the backend API likely has endpoints like:
- `/api/mcp/tools/send_to_address` - Direct tool execution
- `/api/mcp/payments` - Payment execution
- `/api/v1/payments` - Alternative payment endpoint

## Next Steps

1. **Check if there's a Python MCP client** for Locus
2. **Find the backend API endpoint** by:
   - Using Browser DevTools when making payment in dashboard
   - Checking if Locus exposes backend API documentation
   - Testing common backend endpoint patterns

3. **Alternative: Use MCP Client via Bridge**
   - Install Node.js MCP client
   - Create a Python bridge to call MCP tools
   - More complex but would work with official client

## Testing Strategy

Since the MCP server proxies to backend, we should test:
1. Backend API endpoints directly (bypassing MCP server)
2. MCP server endpoints (if accessible)
3. Browser DevTools to find actual endpoint used by dashboard

