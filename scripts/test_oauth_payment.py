#!/usr/bin/env python3
"""
Test OAuth 2.0 Client Credentials Payment

Tests making a payment using OAuth 2.0 authentication instead of API key.
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.locus_oauth_client import LocusOAuthClient, get_locus_oauth_token

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


async def test_oauth_payment():
    """Test making a payment with OAuth authentication."""
    print("=" * 70)
    print("LOCUS OAUTH PAYMENT TEST")
    print("=" * 70)
    print()
    
    # Get OAuth credentials
    client_id = os.getenv("LOCUS_CLIENT_ID") or os.getenv("locus_client_id")
    client_secret = os.getenv("LOCUS_CLIENT_SECRET") or os.getenv("locus_client_secret")
    
    if not client_id or not client_secret:
        print("❌ OAuth credentials not found in .env")
        print("   Need: LOCUS_CLIENT_ID and LOCUS_CLIENT_SECRET")
        return False
    
    print(f"✅ Client ID: {client_id[:20]}...")
    print(f"✅ Client Secret: {'*' * 20}...")
    print()
    
    # Try to get OAuth token
    print("Step 1: Acquiring OAuth access token...")
    try:
        oauth_client = LocusOAuthClient(client_id, client_secret)
        access_token = await oauth_client.get_access_token()
        print(f"✅ Access token acquired: {access_token[:30]}...")
        print()
    except Exception as e:
        print(f"❌ Failed to get OAuth token: {e}")
        print()
        print("💡 The OAuth endpoint might be different.")
        print("   Check Locus documentation for correct OAuth endpoint.")
        return False
    
    # Test payment with OAuth token
    print("Step 2: Making payment with OAuth token...")
    
    endpoint = "https://api.paywithlocus.com/api/mcp/tools/send_to_address"
    payload = {
        "address": "0x86752df5821648a76c3f9e15766cca3d5226903a",  # LandAmerica
        "amount": 0.001,
        "memo": "OAuth test payment"
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    print(f"  ✅ SUCCESS!")
                    print(f"  Response: {result}")
                    return True
                except:
                    print(f"  Response: {response.text[:200]}")
                    return True  # Still success if 200
            elif response.status_code == 401:
                result = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                print(f"  ❌ Authentication failed")
                print(f"  Response: {result}")
                return False
            else:
                print(f"  ❌ Failed with status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_oauth_payment())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

