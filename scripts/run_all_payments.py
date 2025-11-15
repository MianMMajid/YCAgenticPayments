#!/usr/bin/env python3
"""
Direct Locus Payment Script - All Agents

This script makes real payments directly via Locus API using each agent's credentials.
It uses the Locus "send_to_address" endpoint to send payments from the main wallet
to recipient wallets, with proper agent attribution.

This works independently of x402 protocol or service endpoints.
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Agent configuration with correct recipient wallet addresses
AGENTS = [
    {
        "name": "Title Agent",
        "env_agent_key": "LOCUS_AGENT_TITLE_KEY",
        "recipient": "0x86752df5821648a76c3f9e15766cca3d5226903a",  # LandAmerica (updated)
        "amount": 0.03,
        "memo": "Hackathon test payment - Title Search"
    },
    {
        "name": "Inspection Agent",
        "env_agent_key": "LOCUS_AGENT_INSPECTION_KEY",
        "recipient": "0x0c8115aac3551a4d5282b9dc0aa8721b80f341bc",  # AmeriSpec (updated)
        "amount": 0.012,
        "memo": "Hackathon test payment - Inspection"
    },
    {
        "name": "Appraisal Agent",
        "env_agent_key": "LOCUS_AGENT_APPRAISAL_KEY",
        "recipient": "0xbf951bed631ddd22f2461c67539708861050c060",  # CoreLogic (updated)
        "amount": 0.01,
        "memo": "Hackathon test payment - Appraisal"
    },
    {
        "name": "Underwriting Agent",
        "env_agent_key": "LOCUS_AGENT_UNDERWRITING_KEY",
        "recipient": "0x5a9a151475b9e7fe2a74b4f8b5277de4e8030953",  # Fannie Mae (updated)
        "amount": 0.019,
        "memo": "Hackathon test payment - Underwriting"
    },
]

# Try multiple potential Locus API endpoints
# Based on user's example: https://api.paywithlocus.com/send_to_address
LOCUS_API_ENDPOINTS = [
    "https://api.paywithlocus.com/send_to_address",  # User's example endpoint
    "https://api.paywithlocus.com/api/send_to_address",
    "https://api.paywithlocus.com/v1/send_to_address",
    "https://api.paywithlocus.com/api/v1/send_to_address",
    "https://app.paywithlocus.com/api/send_to_address",
    "https://app.paywithlocus.com/send_to_address",
    "https://api.paywithlocus.com/api/mcp/send_to_address",
    "https://app.paywithlocus.com/api/mcp/send_to_address",
]


async def send_payment(agent, endpoint):
    """Send a payment for a single agent."""
    api_key = os.getenv(agent["env_agent_key"])
    
    if not api_key:
        print(f"❌ {agent['name']}: API key not found in environment")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "address": agent["recipient"],
        "amount": agent["amount"],
        "memo": agent["memo"]
    }
    
    print(f"\n[{agent['name']}]")
    print("-" * 70)
    print(f"  Sending {agent['amount']} USDC to {agent['recipient']}")
    print(f"  Memo: {agent['memo']}")
    print(f"  Endpoint: {endpoint}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            
            print(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 201:
                try:
                    result = response.json()
                    print(f"  ✅ SUCCESS")
                    print(f"  Status: {result.get('status', 'n/a')}")
                    print(f"  TX Hash: {result.get('tx_hash', result.get('transaction_hash', 'n/a'))}")
                    if result.get('transaction_id'):
                        print(f"  Transaction ID: {result.get('transaction_id')}")
                    if result.get('locus_transaction_id'):
                        print(f"  Locus TX ID: {result.get('locus_transaction_id')}")
                    print(f"  Raw response: {result}")
                    return result
                except Exception as e:
                    print(f"  ⚠️  Response is not JSON: {response.text[:200]}")
                    return {"status": "success", "raw_response": response.text[:200]}
            elif response.status_code == 401:
                print(f"  ❌ Authentication failed - check API key")
                return None
            elif response.status_code == 402:
                print(f"  ⚠️  Payment required or insufficient funds")
                return None
            else:
                print(f"  ❌ Failed with status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                return None
                
    except httpx.TimeoutException:
        print(f"  ❌ Request timeout")
        return None
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return None


async def send_all_payments():
    """Send payments for all agents."""
    print("=" * 70)
    print("LOCUS DIRECT PAYMENT TEST - ALL AGENTS")
    print("=" * 70)
    print("\n⚠️  WARNING: This will make REAL payments on Locus!")
    print("   These transactions will appear in your Locus Live dashboard.\n")
    
    # Check if we have all API keys
    missing_keys = []
    for agent in AGENTS:
        key = os.getenv(agent["env_agent_key"])
        if not key:
            missing_keys.append(agent["name"])
    
    if missing_keys:
        print("❌ Missing API keys for:")
        for name in missing_keys:
            print(f"   • {name}")
        print("\nPlease set all agent API keys in .env file")
        return False
    
    print("✅ All API keys found")
    print(f"✅ Testing {len(AGENTS)} agents")
    print()
    
    # Try to find a working endpoint
    print("Testing endpoints to find working one...")
    working_endpoint = None
    
    # Test with first agent
    test_agent = AGENTS[0]
    for endpoint in LOCUS_API_ENDPOINTS:
        print(f"  Trying: {endpoint}")
        result = await send_payment(test_agent, endpoint)
        if result and result.get("status") in ["success", "SUCCESS"]:
            working_endpoint = endpoint
            print(f"\n✅ Found working endpoint: {endpoint}\n")
            break
        elif result:
            # If we got a response but not success, this might still be the right endpoint
            working_endpoint = endpoint
            print(f"\n⚠️  Endpoint responded but payment may have failed")
            print(f"   Using: {endpoint}\n")
            break
    
    if not working_endpoint:
        print("\n❌ Could not find working endpoint")
        print("   Tried all endpoints, none returned success")
        print("\n💡 Next steps:")
        print("   1. Check Locus documentation for correct endpoint")
        print("   2. Use Browser DevTools to find endpoint when making payment in dashboard")
        print("   3. Contact Locus support for API endpoint")
        return False
    
    # Send payments for all agents using working endpoint
    print("=" * 70)
    print("SENDING PAYMENTS FOR ALL AGENTS")
    print("=" * 70)
    print(f"\nUsing endpoint: {working_endpoint}\n")
    
    results = []
    for agent in AGENTS:
        result = await send_payment(agent, working_endpoint)
        results.append({
            "agent": agent["name"],
            "success": result is not None and result.get("status") in ["success", "SUCCESS"],
            "result": result
        })
        print("=" * 70)
    
    # Summary
    print("\n" + "=" * 70)
    print("PAYMENT SUMMARY")
    print("=" * 70)
    print()
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"Total Payments: {len(results)}")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print()
    
    if successful > 0:
        print("✅ Successful Payments:")
        for r in results:
            if r["success"]:
                tx_hash = r["result"].get("tx_hash") or r["result"].get("transaction_hash", "N/A")
                print(f"  • {r['agent']}: {tx_hash[:30]}...")
        print()
        print("🎉 Check your Locus Live dashboard to see these transactions!")
        print()
    
    if failed > 0:
        print("❌ Failed Payments:")
        for r in results:
            if not r["success"]:
                print(f"  • {r['agent']}")
        print()
    
    print("=" * 70)
    
    return successful == len(results)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("LOCUS DIRECT PAYMENT SCRIPT")
    print("=" * 70)
    print("\nThis script makes real A2A payments via Locus API.")
    print("Each payment is attributed to its respective agent.")
    print("All transactions will appear in your Locus Live dashboard.\n")
    
    try:
        success = asyncio.run(send_all_payments())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

