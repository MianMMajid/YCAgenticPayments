#!/usr/bin/env python3
"""
Instructions: Find Locus API Endpoint via Browser DevTools

This script provides step-by-step instructions for finding the correct
Locus API endpoint by monitoring network traffic in the browser.
"""
print("=" * 70)
print("HOW TO FIND LOCUS API ENDPOINT VIA BROWSER DEVTOOLS")
print("=" * 70)
print("""
Since Locus uses MCP (Model Context Protocol) and we're getting HTML
responses from direct API calls, we need to find the actual endpoint
by monitoring the browser when making a payment in the dashboard.

STEP-BY-STEP INSTRUCTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. OPEN LOCUS DASHBOARD
   • Go to: https://app.paywithlocus.com
   • Log in with your account

2. OPEN BROWSER DEVTOOLS
   • Press F12 (Windows/Linux) or Cmd+Option+I (Mac)
   • Or: Right-click → Inspect → Network tab

3. PREPARE NETWORK TAB
   • Go to the "Network" tab in DevTools
   • Check "Preserve log" checkbox
   • Filter by "Fetch/XHR" or "All"

4. MAKE A TEST PAYMENT
   • Navigate to payments section
   • Click "Send Payment" or similar
   • Send a small test payment (e.g., 0.001 USDC)
   • To one of your recipient wallets:
     - LandAmerica: 0x86752df5821648a76c3f9e15766cca3d5226903a
     - AmeriSpec: 0x0c8115aac3551a4d5282b9dc0aa8721b80f341bc
     - CoreLogic: 0xbf951bed631ddd22f2461c67539708861050c060
     - Fannie Mae: 0x5a9a151475b9e7fe2a74b4f8b5277de4e8030953

5. FIND THE API CALL
   • Look for POST requests in the Network tab
   • The request should have:
     - Method: POST
     - Status: 200 or 201
     - Type: fetch or xhr
   • Look for URLs containing:
     - "api"
     - "payment"
     - "send"
     - "locus"

6. EXAMINE THE REQUEST
   Click on the request to see details:
   
   HEADERS TAB:
   • Request URL: Copy this full URL
   • Request Method: Should be POST
   • Authorization: Check the format
     - Bearer token?
     - API key in header?
     - Other format?
   • Content-Type: Should be application/json
   
   PAYLOAD TAB:
   • Request Payload: Copy the JSON structure
   • Note the exact field names:
     - "address" or "recipient_wallet"?
     - "amount" format (number or string)?
     - "memo" or "description"?
     - Any other required fields?
   
   RESPONSE TAB:
   • Response format: JSON or other?
   • Response structure: What fields are returned?
   • Transaction hash location: Where is it in the response?

7. COPY THE INFORMATION
   Copy these details:
   • Full endpoint URL
   • Request headers (especially Authorization format)
   • Request payload structure
   • Response structure

8. UPDATE OUR CODE
   Once you have the endpoint:
   • Update LOCUS_API_BASE_URL in .env
   • Or update services/locus_api_client.py
   • Update request format if needed
   • Test with scripts/run_all_payments.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALTERNATIVE: CHECK LOCUS DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The Locus documentation mentions MCP (Model Context Protocol). You might need:

1. Install Locus MCP client:
   npm install @locus-technologies/mcp-client

2. Use MCP tools instead of direct API calls

3. Or check if there's a Python MCP client available

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT TO LOOK FOR IN THE NETWORK TAB:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example of what you might see:

Request URL: https://api.paywithlocus.com/v1/payments
Method: POST
Headers:
  Authorization: Bearer locus_dev_...
  Content-Type: application/json
Payload:
  {
    "to": "0x...",
    "amount": 0.001,
    "currency": "USDC",
    "memo": "Test payment"
  }

OR it might be:

Request URL: https://app.paywithlocus.com/api/mcp/tools/send_to_address
Method: POST
Headers:
  X-API-Key: locus_dev_...
Payload:
  {
    "address": "0x...",
    "amount": 0.001,
    "memo": "Test"
  }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Once you find the endpoint, update:
• scripts/run_all_payments.py
• services/locus_api_client.py
• .env (LOCUS_API_BASE_URL)

Then test again with: python3 scripts/run_all_payments.py

""")
print("=" * 70)

