#!/usr/bin/env python3
"""
Script to help find the Locus API endpoint.

This script tries various endpoint patterns and provides instructions
for finding the correct endpoint via browser DevTools.
"""
import asyncio
import httpx
import os
from pathlib import Path

# Load environment
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

API_KEY = os.getenv("LOCUS_AGENT_TITLE_KEY", "locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG")
AGENT_ID = os.getenv("LOCUS_AGENT_TITLE_ID", "ooeju0aot520uv7dd77nr7d5r")
RECIPIENT = os.getenv("SERVICE_RECIPIENT_LANDAMERICA", "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d")

# Try different base URLs
BASE_URLS = [
    "https://api.paywithlocus.com",
    "https://backend.paywithlocus.com",
    "https://app.paywithlocus.com",
    "https://paywithlocus.com/api",
]

# Try different endpoint patterns
ENDPOINT_PATTERNS = [
    "/api/mcp/send_to_address",
    "/api/mcp/payments/send_to_address",
    "/mcp/send_to_address",
    "/api/v1/payments/send_to_address",
    "/api/v1/payments",
    "/v1/payments/send_to_address",
    "/v1/payments",
    "/api/payments",
    "/payments",
]


async def test_endpoint(base_url: str, endpoint: str):
    """Test a specific endpoint."""
    url = f"{base_url}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    payload = {
        "address": RECIPIENT,
        "amount": 0.001,
        "memo": "Test payment"
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            return {
                "url": url,
                "status": response.status_code,
                "success": response.status_code in [200, 201],
                "response": response.text[:200] if response.status_code != 200 else "SUCCESS"
            }
    except Exception as e:
        return {
            "url": url,
            "status": "ERROR",
            "success": False,
            "response": str(e)[:200]
        }


async def find_endpoint():
    """Try to find the correct endpoint."""
    print("=" * 70)
    print("FINDING LOCUS API ENDPOINT")
    print("=" * 70)
    print("\nTrying different endpoint combinations...\n")
    
    results = []
    for base_url in BASE_URLS:
        for endpoint in ENDPOINT_PATTERNS:
            result = await test_endpoint(base_url, endpoint)
            results.append(result)
            
            if result["success"]:
                print(f"✅ FOUND: {result['url']}")
                print(f"   Status: {result['status']}")
                return result["url"]
            else:
                status = result.get("status", "ERROR")
                if status != 404:
                    print(f"⚠️  {result['url']} → {status}")
    
    print("\n" + "=" * 70)
    print("NO WORKING ENDPOINT FOUND")
    print("=" * 70)
    print("\n💡 Next Steps:")
    print("1. Open Locus Dashboard: https://app.paywithlocus.com")
    print("2. Open Browser DevTools (F12)")
    print("3. Go to Network tab")
    print("4. Make a test payment in the dashboard")
    print("5. Look for POST requests - copy the endpoint URL")
    print("6. Update LOCUS_API_BASE_URL in .env or locus_api_client.py")
    print("\n" + "=" * 70)
    
    return None


if __name__ == "__main__":
    asyncio.run(find_endpoint())

