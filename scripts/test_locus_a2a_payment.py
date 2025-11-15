#!/usr/bin/env python3
"""
Test Script: Execute Real A2A Payment via Locus API

This script makes an actual agent-to-agent payment that will appear in Locus Live dashboard.
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
from services.locus_api_client import LocusAPIClient

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


async def test_a2a_payment():
    """Test making a real A2A payment via Locus API."""
    
    print("=" * 70)
    print("LOCUS A2A PAYMENT TEST")
    print("=" * 70)
    print("\nThis will make a REAL payment that appears in Locus Live dashboard.\n")
    
    # Initialize Locus
    try:
        print("[1/4] Initializing wallet...")
        wallet = init_wallet_manager()
        wallet_info = wallet.get_wallet_info()
        print(f"  ✓ Wallet: {wallet_info['name']}")
        print(f"  ✓ Address: {wallet_info['address']}")
        
        print("\n[2/4] Initializing Locus...")
        locus = init_locus(os.getenv("LOCUS_API_KEY"), wallet.get_address())
        print(f"  ✓ Locus initialized")
        
        print("\n[3/4] Initializing payment handler...")
        payment_handler = LocusPaymentHandler(locus, use_real_api=True)
        print(f"  ✓ Payment handler ready (using real API)")
        
        # Get test parameters
        print("\n[4/4] Payment details:")
        
        # Use Title Agent for test
        agent_id = os.getenv("LOCUS_AGENT_TITLE_ID", "ooeju0aot520uv7dd77nr7d5r")
        agent_key = os.getenv("LOCUS_AGENT_TITLE_KEY", "")
        recipient = os.getenv("SERVICE_RECIPIENT_LANDAMERICA", "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d")
        amount = 0.001  # Small test amount (0.001 USDC)
        
        print(f"  Agent ID: {agent_id}")
        print(f"  Recipient: {recipient}")
        print(f"  Amount: {amount} USDC")
        print(f"  Description: Test A2A Payment")
        
        print("\n" + "=" * 70)
        print("EXECUTING PAYMENT")
        print("=" * 70)
        print("\n⚠️  This will make a REAL payment on Locus!")
        print("   Press Ctrl+C to cancel (5 second delay)...\n")
        
        await asyncio.sleep(5)
        
        # Execute payment
        print("Executing payment...\n")
        result = await payment_handler.execute_payment(
            agent_id="title-agent",  # Internal agent ID
            amount=amount,
            recipient=recipient,
            service_url="test",
            description="Test A2A Payment - Should appear in Locus Live"
        )
        
        print("=" * 70)
        print("PAYMENT RESULT")
        print("=" * 70)
        print()
        
        if result.get("status") == "SUCCESS":
            print("✅ PAYMENT SUCCESSFUL!")
            print(f"  Transaction Hash: {result.get('tx_hash', 'N/A')}")
            if result.get("locus_transaction_id"):
                print(f"  Locus TX ID: {result.get('locus_transaction_id')}")
            print(f"  Amount: {result.get('amount')} USDC")
            print(f"  Recipient: {result.get('recipient')}")
            print(f"  Method: {result.get('payment_method', 'Unknown')}")
            print()
            print("🎉 Check your Locus Live dashboard to see this transaction!")
        elif result.get("status") == "ERROR":
            print("❌ PAYMENT FAILED")
            print(f"  Error: {result.get('error', 'Unknown error')}")
            print(f"  Message: {result.get('message', 'No details')}")
            if result.get("tried_endpoints"):
                print(f"\n  Tried endpoints:")
                for endpoint in result.get("tried_endpoints", []):
                    print(f"    - {endpoint}")
        else:
            print(f"⚠️  Payment status: {result.get('status')}")
            print(f"  Result: {result}")
        
        print("\n" + "=" * 70)
        
        return result.get("status") == "SUCCESS"
        
    except KeyboardInterrupt:
        print("\n\n❌ Payment cancelled by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will make a REAL payment on Locus!")
    print("   Make sure you have sufficient funds in your wallet.\n")
    
    try:
        success = asyncio.run(test_a2a_payment())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)

