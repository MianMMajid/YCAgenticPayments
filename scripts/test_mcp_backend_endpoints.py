#!/usr/bin/env python3
"""
Test MCP Backend API Endpoints

Based on MCP Spec architecture, the MCP Lambda server proxies to a backend API.
This script tests likely backend API endpoints that the MCP server would call.
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

TEST_AGENT_KEY = os.getenv("LOCUS_AGENT_TITLE_KEY", "")
TEST_RECIPIENT = "0x86752df5821648a76c3f9e15766cca3d5226903a"
TEST_AMOUNT = 0.001
TEST_MEMO = "MCP backend endpoint test"

# Based on MCP Spec architecture, the backend API likely has these endpoints:
# The MCP server proxies tool calls to the backend
MCP_BACKEND_ENDPOINTS = [
    # MCP tool execution endpoints (most likely)
    ("https://api.paywithlocus.com", "/api/mcp/tools/send_to_address"),
    ("https://api.paywithlocus.com", "/api/mcp/tools/execute"),
    ("https://api.paywithlocus.com", "/api/mcp/send_to_address"),
    
    # Backend payment endpoints
    ("https://api.paywithlocus.com", "/api/v1/payments"),
    ("https://api.paywithlocus.com", "/api/v1/payments/send"),
    ("https://api.paywithlocus.com", "/api/v1/payments/send_to_address"),
    
    # Alternative backend paths
    ("https://api.paywithlocus.com", "/api/payments"),
    ("https://api.paywithlocus.com", "/api/payments/send"),
    ("https://api.paywithlocus.com", "/api/payments/send_to_address"),
    
    # MCP proxy endpoints
    ("https://api.paywithlocus.com", "/mcp/tools/send_to_address"),
    ("https://api.paywithlocus.com", "/mcp/send_to_address"),
    
    # App domain (sometimes backend is on app domain)
    ("https://app.paywithlocus.com", "/api/mcp/tools/send_to_address"),
    ("https://app.paywithlocus.com", "/api/v1/payments"),
    ("https://app.paywithlocus.com", "/api/payments"),
]


async def test_mcp_backend_endpoint(base_url, path):
    """Test a single MCP backend endpoint."""
    if not TEST_AGENT_KEY:
        return None
    
    endpoint = f"{base_url}{path}"
    
    # Try different payload formats based on MCP spec
    payloads = [
        # Format 1: Direct tool parameters (from MCP spec)
        {
            "address": TEST_RECIPIENT,
            "amount": TEST_AMOUNT,
            "memo": TEST_MEMO
        },
        # Format 2: MCP tool call format
        {
            "tool": "send_to_address",
            "arguments": {
                "address": TEST_RECIPIENT,
                "amount": TEST_AMOUNT,
                "memo": TEST_MEMO
            }
        },
        # Format 3: Backend API format
        {
            "to": TEST_RECIPIENT,
            "amount": TEST_AMOUNT,
            "currency": "USDC",
            "memo": TEST_MEMO
        },
    ]
    
    # Try different header formats
    header_formats = [
        # Format 1: Bearer token (OAuth)
        {
            "Authorization": f"Bearer {TEST_AGENT_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        # Format 2: API Key header
        {
            "X-API-Key": TEST_AGENT_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        # Format 3: Both
        {
            "Authorization": f"Bearer {TEST_AGENT_KEY}",
            "X-API-Key": TEST_AGENT_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
    ]
    
    for headers in header_formats:
        for payload in payloads:
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                    response = await client.post(endpoint, json=payload, headers=headers)
                    
                    # Check if JSON response
                    is_json = False
                    json_data = None
                    try:
                        json_data = response.json()
                        is_json = True
                    except:
                        pass
                    
                    # Return if we get a promising response
                    if response.status_code in [200, 201] or is_json:
                        return {
                            "endpoint": endpoint,
                            "status": response.status_code,
                            "is_json": is_json,
                            "json_data": json_data if is_json else None,
                            "response_preview": response.text[:300] if not is_json else None,
                            "payload": payload,
                            "headers": list(headers.keys())
                        }
            except Exception:
                continue
    
    return None


async def test_all_mcp_backend_endpoints():
    """Test all likely MCP backend endpoints."""
    print("=" * 70)
    print("MCP BACKEND API ENDPOINT TEST")
    print("=" * 70)
    print("\nBased on MCP Spec architecture:")
    print("  • MCP Lambda server proxies tool calls to backend API")
    print("  • Backend API executes payments via smart wallet")
    print("  • We're testing backend endpoints directly (bypassing MCP server)")
    print()
    print(f"Testing {len(MCP_BACKEND_ENDPOINTS)} likely backend endpoints...")
    print(f"API Key: {TEST_AGENT_KEY[:20]}...")
    print()
    
    if not TEST_AGENT_KEY:
        print("❌ No API key found")
        return
    
    results = []
    for base_url, path in MCP_BACKEND_ENDPOINTS:
        endpoint = f"{base_url}{path}"
        print(f"Testing: {endpoint}...", end=" ")
        result = await test_mcp_backend_endpoint(base_url, path)
        if result:
            print(f"✅ Status {result['status']}, JSON: {result['is_json']}")
            results.append(result)
        else:
            print("❌")
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    
    if results:
        print(f"✅ Found {len(results)} promising endpoints:\n")
        for result in results:
            print(f"Endpoint: {result['endpoint']}")
            print(f"  Status: {result['status']}")
            print(f"  Is JSON: {result['is_json']}")
            if result['is_json']:
                print(f"  Response: {result['json_data']}")
            else:
                print(f"  Response preview: {result['response_preview'][:100]}...")
            print(f"  Payload format: {list(result['payload'].keys())}")
            print(f"  Headers: {result['headers']}")
            print()
    else:
        print("❌ No promising endpoints found")
        print("\n💡 The backend API may:")
        print("   • Require MCP server authentication (not direct API key)")
        print("   • Only be accessible through MCP client")
        print("   • Use different endpoint structure")
        print("\n💡 Next steps:")
        print("   1. Use Browser DevTools to find actual endpoint")
        print("   2. Check if Locus provides Python MCP client")
        print("   3. Contact Locus support for backend API documentation")
        print()
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_all_mcp_backend_endpoints())

