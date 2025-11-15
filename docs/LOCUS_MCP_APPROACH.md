# Locus MCP Approach - Correct Integration Method

## Key Finding from Locus Documentation

Based on the [Locus Getting Started Guide](https://docs.paywithlocus.com/getting-started), Locus uses **MCP (Model Context Protocol)** for agent payments, not direct REST API calls.

## Architecture

```
Your Application → MCP Client → MCP Server → Locus Backend → Blockchain
```

The `send_to_address` tool is provided by the MCP server, not a direct HTTP endpoint.

## Two Integration Methods

### Method 1: LangChain with OAuth (Recommended for Production)

- Uses OAuth Client Credentials (Client ID + Secret)
- Full MCP integration
- LangChain ReAct agent
- More secure

### Method 2: Claude SDK with API Key (Simpler)

- Uses single API Key
- Claude SDK
- Streaming support
- Good for prototypes

## Current Issue

We've been trying to call REST endpoints like:
- `https://api.paywithlocus.com/send_to_address`
- `https://app.paywithlocus.com/api/send_to_address`

But these return HTML (frontend app) instead of JSON because:
- **Locus doesn't expose a direct REST API for payments**
- Payments must go through the MCP server
- The MCP server provides the `send_to_address` tool

## Solution Options

### Option 1: Use Locus MCP Client (Recommended)

Install the Locus MCP client and use it from Python:

```bash
npm install @locus-technologies/mcp-client
```

Then call MCP tools from Python via subprocess or HTTP bridge.

### Option 2: Find the MCP Server Endpoint

The MCP server might be accessible at:
- A local server (runs on your machine)
- A remote endpoint (provided by Locus)
- Through the Locus dashboard

### Option 3: Use Browser DevTools

1. Make a payment in the Locus dashboard
2. Open Browser DevTools → Network tab
3. Find the actual API call that processes the payment
4. Replicate that exact request format

## Next Steps

1. **Check if Locus provides a Python MCP client**
2. **Use Browser DevTools to find the actual payment endpoint**
3. **Contact Locus support for the correct API endpoint format**

## Current Status

- ✅ All agent credentials configured
- ✅ All wallet addresses configured
- ✅ Payment handler code ready
- ❌ Need correct API endpoint or MCP client

