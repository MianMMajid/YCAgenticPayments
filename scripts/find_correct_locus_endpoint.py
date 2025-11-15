#!/usr/bin/env python3
"""
Diagnostic Script: Find Correct Locus API Endpoint

This script tests various endpoint combinations and request formats
to find the working Locus API endpoint for payments.
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import httpx
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Test configuration
TEST_AGENT_KEY = os.getenv("LOCUS_AGENT_TITLE_KEY", "")
TEST_RECIPIENT = "0x86752df5821648a76c3f9e15766cca3d5226903a"  # LandAmerica
TEST_AMOUNT = 0.001  # Small test amount
TEST_MEMO = "Endpoint test payment"

# Base URLs to test
BASE_URLS = [
    "https://api.paywithlocus.com",
    "https://app.paywithlocus.com",
    "https://backend.paywithlocus.com",
    "https://paywithlocus.com",
]

# Endpoint paths to test
ENDPOINT_PATHS = [
    "/send_to_address",
    "/api/send_to_address",
    "/api/v1/send_to_address",
    "/api/v1/payments/send_to_address",
    "/api/mcp/send_to_address",
    "/api/mcp/payments/send_to_address",
    "/mcp/send_to_address",
    "/v1/send_to_address",
    "/v1/payments/send_to_address",
    "/payments/send_to_address",
    "/send",
    "/api/send",
    "/api/payments",
    "/api/payments/send",
]

# Request payload formats to test
PAYLOAD_FORMATS = [
    # Format 1: Simple format
    {
        "address": TEST_RECIPIENT,
        "amount": TEST_AMOUNT,
        "memo": TEST_MEMO
    },
    # Format 2: With currency
    {
        "address": TEST_RECIPIENT,
        "amount": TEST_AMOUNT,
        "currency": "USDC",
        "memo": TEST_MEMO
    },
    # Format 3: With recipient_wallet
    {
        "recipient_wallet": TEST_RECIPIENT,
        "amount": TEST_AMOUNT,
        "memo": TEST_MEMO
    },
    # Format 4: With to/from
    {
        "to": TEST_RECIPIENT,
        "amount": TEST_AMOUNT,
        "memo": TEST_MEMO
    },
    # Format 5: MCP tool format
    {
        "tool": "send_to_address",
        "arguments": {
            "address": TEST_RECIPIENT,
            "amount": TEST_AMOUNT,
            "memo": TEST_MEMO
        }
    },
]

# Header formats to test
HEADER_FORMATS = [
    # Format 1: Bearer token
    lambda key: {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    },
    # Format 2: X-API-Key header
    lambda key: {
        "X-API-Key": key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    },
    # Format 3: Both
    lambda key: {
        "Authorization": f"Bearer {key}",
        "X-API-Key": key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    },
    # Format 4: With User-Agent
    lambda key: {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "CounterAI/1.0"
    },
]


async def test_endpoint(base_url, path, payload_format, header_func):
    """Test a single endpoint combination."""
    if not TEST_AGENT_KEY:
        return None
    
    endpoint = f"{base_url}{path}"
    headers = header_func(TEST_AGENT_KEY)
    payload = payload_format
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            
            # Check if response is JSON
            is_json = False
            response_data = None
            try:
                response_data = response.json()
                is_json = True
            except:
                pass
            
            return {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "is_json": is_json,
                "response_preview": response.text[:200] if not is_json else str(response_data)[:200],
                "headers": dict(response.headers),
                "payload_format": list(payload.keys()),
                "header_format": list(headers.keys())
            }
    except httpx.TimeoutException:
        return {
            "endpoint": endpoint,
            "status_code": None,
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "status_code": None,
            "error": str(e)
        }


async def find_working_endpoint():
    """Test all endpoint combinations to find a working one."""
    print("=" * 70)
    print("LOCUS API ENDPOINT FINDER")
    print("=" * 70)
    print("\nTesting various endpoint combinations and request formats...")
    print(f"Using Title Agent API key: {TEST_AGENT_KEY[:20]}...")
    print(f"Test recipient: {TEST_RECIPIENT}")
    print(f"Test amount: {TEST_AMOUNT} USDC")
    print()
    
    if not TEST_AGENT_KEY:
        print("❌ No API key found. Please set LOCUS_AGENT_TITLE_KEY in .env")
        return
    
    print("Testing combinations (this may take a while)...")
    print()
    
    results = []
    total_tests = len(BASE_URLS) * len(ENDPOINT_PATHS) * len(PAYLOAD_FORMATS) * len(HEADER_FORMATS)
    current_test = 0
    
    # Test all combinations
    for base_url in BASE_URLS:
        for path in ENDPOINT_PATHS:
            for payload_format in PAYLOAD_FORMATS:
                for header_func in HEADER_FORMATS:
                    current_test += 1
                    if current_test % 50 == 0:
                        print(f"  Progress: {current_test}/{total_tests}...")
                    
                    result = await test_endpoint(base_url, path, payload_format, header_func)
                    if result:
                        results.append(result)
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
    
    print(f"\n✅ Completed {total_tests} tests\n")
    
    # Analyze results
    print("=" * 70)
    print("RESULTS ANALYSIS")
    print("=" * 70)
    print()
    
    # Group by status code
    by_status = {}
    json_responses = []
    errors = []
    
    for result in results:
        status = result.get("status_code")
        if status:
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(result)
            
            if result.get("is_json"):
                json_responses.append(result)
        else:
            errors.append(result)
    
    # Print summary
    print("Status Code Summary:")
    for status in sorted(by_status.keys()):
        count = len(by_status[status])
        print(f"  {status}: {count} responses")
    print()
    
    if json_responses:
        print(f"✅ Found {len(json_responses)} JSON responses:")
        for result in json_responses[:5]:  # Show first 5
            print(f"\n  Endpoint: {result['endpoint']}")
            print(f"  Status: {result['status_code']}")
            print(f"  Response: {result['response_preview']}")
            print(f"  Payload format: {result['payload_format']}")
            print(f"  Headers: {result['header_format']}")
        if len(json_responses) > 5:
            print(f"\n  ... and {len(json_responses) - 5} more")
        print()
    
    # Show promising results (200/201 with any response)
    promising = [r for r in results if r.get("status_code") in [200, 201]]
    if promising:
        print(f"⚠️  Found {len(promising)} responses with status 200/201:")
        for result in promising[:10]:  # Show first 10
            print(f"\n  Endpoint: {result['endpoint']}")
            print(f"  Status: {result['status_code']}")
            print(f"  Is JSON: {result.get('is_json', False)}")
            print(f"  Response preview: {result['response_preview'][:100]}...")
        if len(promising) > 10:
            print(f"\n  ... and {len(promising) - 10} more")
        print()
    
    # Show errors
    if errors:
        print(f"❌ Found {len(errors)} errors:")
        for result in errors[:5]:
            print(f"  {result['endpoint']}: {result.get('error', 'Unknown')}")
        print()
    
    # Recommendations
    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print()
    
    if json_responses:
        print("✅ Try these endpoints (returned JSON):")
        for result in json_responses[:3]:
            print(f"  • {result['endpoint']}")
            print(f"    Payload: {result['payload_format']}")
            print(f"    Headers: {result['header_format']}")
        print()
    elif promising:
        print("⚠️  These endpoints returned 200/201 but not JSON:")
        print("   They might still work - check Locus dashboard for payments")
        for result in promising[:3]:
            print(f"  • {result['endpoint']}")
        print()
    else:
        print("❌ No promising endpoints found.")
        print("\n💡 Next steps:")
        print("  1. Check Locus documentation for API endpoint")
        print("  2. Use Browser DevTools when making payment in dashboard")
        print("  3. Contact Locus support for API endpoint")
        print()
    
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(find_working_endpoint())
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

