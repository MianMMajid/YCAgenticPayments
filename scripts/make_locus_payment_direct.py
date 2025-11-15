#!/usr/bin/env python3
"""
Direct Locus Payment Script

This script attempts to make a payment using the agent credentials.
If the API endpoint is unknown, it will show what we're trying and provide
instructions for finding the correct endpoint.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from services.locus_wallet_manager import init_wallet_manager
from services.locus_integration import init_locus
from services.locus_payment_handler import LocusPaymentHandler

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


async def make_direct_payment():
    """Make a direct A2A payment."""
    
    print("=" * 70)
    print("DIRECT LOCUS A2A PAYMENT")
    print("=" * 70)
    print()
    
    # Initialize
    wallet = init_wallet_manager()
    locus = init_locus(os.getenv("LOCUS_API_KEY"), wallet.get_address())
    payment_handler = LocusPaymentHandler(locus, use_real_api=True)
    
    # Payment details
    agent_id = "title-agent"
    amount = 0.001  # Small test amount
    recipient = os.getenv("SERVICE_RECIPIENT_LANDAMERICA", "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d")
    
    print(f"Making payment:")
    print(f"  Agent: {agent_id}")
    print(f"  Amount: {amount} USDC")
    print(f"  Recipient: {recipient}")
    print()
    
    result = await payment_handler.execute_payment(
        agent_id=agent_id,
        amount=amount,
        recipient=recipient,
        service_url="test",
        description="Direct A2A Payment Test"
    )
    
    print("=" * 70)
    print("RESULT")
    print("=" * 70)
    print()
    
    if result.get("status") == "SUCCESS":
        print("✅ Payment successful!")
        print(f"  TX Hash: {result.get('tx_hash', 'N/A')}")
        if result.get("locus_transaction_id"):
            print(f"  Locus TX ID: {result.get('locus_transaction_id')}")
        print(f"  Method: {result.get('payment_method', 'Unknown')}")
        print()
        print("🎉 Check Locus Live dashboard to see this transaction!")
    elif result.get("status") == "ERROR":
        print("❌ Payment failed")
        print(f"  Error: {result.get('error', 'Unknown')}")
        print()
        print("💡 To fix this:")
        print("  1. Check Locus documentation for API endpoint")
        print("  2. Update LOCUS_API_BASE_URL in .env")
        print("  3. Or update services/locus_api_client.py with correct endpoint")
        print()
        if result.get("tried_endpoints"):
            print("  Tried endpoints:")
            for endpoint in result.get("tried_endpoints", []):
                print(f"    - {endpoint}")
    else:
        print(f"Status: {result.get('status')}")
        print(f"Result: {result}")
    
    print("=" * 70)
    
    return result.get("status") == "SUCCESS"


if __name__ == "__main__":
    try:
        success = asyncio.run(make_direct_payment())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

