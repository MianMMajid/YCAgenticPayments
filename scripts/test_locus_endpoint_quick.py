#!/usr/bin/env python3
"""
Quick Locus Endpoint Test

Tests the most likely endpoint combinations quickly.
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
TEST_MEMO = "Quick endpoint test"

# Most likely endpoint combinations (based on common API patterns)
LIKELY_ENDPOINTS = [
    # User's example format
    ("https://api.paywithlocus.com", "/send_to_address"),
    ("https://api.paywithlocus.com", "/api/send_to_address"),
    ("https://api.paywithlocus.com", "/api/v1/send_to_address"),
    ("https://api.paywithlocus.com", "/v1/send_to_address"),
    
    # App domain (we got 200 here before)
    ("https://app.paywithlocus.com", "/api/send_to_address"),
    ("https://app.paywithlocus.com", "/send_to_address"),
    ("https://app.paywithlocus.com", "/api/v1/send_to_address"),
    
    # MCP format
    ("https://api.paywithlocus.com", "/api/mcp/send_to_address"),
    ("https://app.paywithlocus.com", "/api/mcp/send_to_address"),
    
    # Alternative formats
    ("https://api.paywithlocus.com", "/api/payments"),
    ("https://api.paywithlocus.com", "/api/payments/send"),
    ("https://api.paywithlocus.com", "/api/payments/send_to_address"),
]


async def test_endpoint(base_url, path):
    """Test a single endpoint."""
    if not TEST_AGENT_KEY:
        return None
    
    endpoint = f"{base_url}{path}"
    
    # Try different payload formats
    payloads = [
        {"address": TEST_RECIPIENT, "amount": TEST_AMOUNT, "memo": TEST_MEMO},
        {"address": TEST_RECIPIENT, "amount": TEST_AMOUNT, "currency": "USDC", "memo": TEST_MEMO},
        {"recipient_wallet": TEST_RECIPIENT, "amount": TEST_AMOUNT, "memo": TEST_MEMO},
    ]
    
    headers = {
        "Authorization": f"Bearer {TEST_AGENT_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    for payload in payloads:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                
                # Check if JSON
                is_json = False
                json_data = None
                try:
                    json_data = response.json()
                    is_json = True
                except:
                    pass
                
                # Return first promising result
                if response.status_code in [200, 201] or is_json:
                    return {
                        "endpoint": endpoint,
                        "status": response.status_code,
                        "is_json": is_json,
                        "json_data": json_data if is_json else None,
                        "response_preview": response.text[:300] if not is_json else None,
                        "payload": payload
                    }
        except Exception as e:
            continue
    
    return None


async def quick_test():
    """Quick test of likely endpoints."""
    print("=" * 70)
    print("QUICK LOCUS ENDPOINT TEST")
    print("=" * 70)
    print(f"\nTesting {len(LIKELY_ENDPOINTS)} most likely endpoint combinations...")
    print(f"API Key: {TEST_AGENT_KEY[:20]}...")
    print()
    
    if not TEST_AGENT_KEY:
        print("❌ No API key found")
        return
    
    results = []
    for base_url, path in LIKELY_ENDPOINTS:
        print(f"Testing: {base_url}{path}...", end=" ")
        result = await test_endpoint(base_url, path)
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
            print(f"  Payload: {result['payload']}")
            print()
    else:
        print("❌ No promising endpoints found")
        print("\n💡 The API endpoint may not be publicly accessible.")
        print("   Try using Browser DevTools when making a payment in the Locus dashboard.")
        print()
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(quick_test())

