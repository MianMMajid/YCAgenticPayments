#!/usr/bin/env python3
"""
Live A2A Payment Test - All Agents

This script tests all 4 agents making real A2A payments that will appear in Locus Live dashboard.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

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


async def test_all_agents_live():
    """Test all 4 agents making real A2A payments."""
    
    print("=" * 70)
    print("LOCUS LIVE A2A PAYMENT TEST - ALL AGENTS")
    print("=" * 70)
    print("\n⚠️  WARNING: This will make REAL payments on Locus!")
    print("   These transactions will appear in your Locus Live dashboard.\n")
    
    # Initialize Locus
    try:
        print("[1/3] Initializing wallet and Locus...")
        wallet = init_wallet_manager()
        wallet_info = wallet.get_wallet_info()
        print(f"  ✓ Wallet: {wallet_info['name']}")
        print(f"  ✓ Address: {wallet_info['address']}")
        print(f"  ✓ Network: {wallet_info['network']}")
        
        locus = init_locus(os.getenv("LOCUS_API_KEY"), wallet.get_address())
        payment_handler = LocusPaymentHandler(locus, use_real_api=True)
        print(f"  ✓ Payment handler ready (REAL API mode)")
        
        # Define all agents to test
        agents = [
            {
                "name": "Title Search Agent",
                "internal_id": "title-agent",
                "agent_id_env": "LOCUS_AGENT_TITLE_ID",
                "recipient_env": "SERVICE_RECIPIENT_LANDAMERICA",
                "amount": 0.001,  # Small test amount
                "description": "Live Test - Title Search Payment"
            },
            {
                "name": "Inspection Agent",
                "internal_id": "inspection-agent",
                "agent_id_env": "LOCUS_AGENT_INSPECTION_ID",
                "recipient_env": "SERVICE_RECIPIENT_AMERISPEC",
                "amount": 0.001,
                "description": "Live Test - Inspection Payment"
            },
            {
                "name": "Appraisal Agent",
                "internal_id": "appraisal-agent",
                "agent_id_env": "LOCUS_AGENT_APPRAISAL_ID",
                "recipient_env": "SERVICE_RECIPIENT_CORELOGIC",
                "amount": 0.001,
                "description": "Live Test - Appraisal Payment"
            },
            {
                "name": "Underwriting Agent",
                "internal_id": "underwriting-agent",
                "agent_id_env": "LOCUS_AGENT_UNDERWRITING_ID",
                "recipient_env": "SERVICE_RECIPIENT_FANNIEMAE",
                "amount": 0.001,
                "description": "Live Test - Underwriting Payment"
            },
        ]
        
        print("\n[2/3] Payment Details:")
        print()
        for agent in agents:
            agent_id = os.getenv(agent["agent_id_env"], "")
            recipient = os.getenv(agent["recipient_env"], "")
            print(f"  {agent['name']}:")
            print(f"    Agent ID: {agent_id[:20]}...")
            print(f"    Recipient: {recipient}")
            print(f"    Amount: {agent['amount']} USDC")
            print()
        
        print("[3/3] Ready to execute payments")
        print("\n" + "=" * 70)
        print("EXECUTING LIVE PAYMENTS")
        print("=" * 70)
        print("\n⚠️  Starting in 3 seconds... Press Ctrl+C to cancel\n")
        await asyncio.sleep(3)
        
        results = []
        
        # Execute payments for each agent
        for i, agent in enumerate(agents, 1):
            print(f"\n[{i}/{len(agents)}] {agent['name']}")
            print("-" * 70)
            
            recipient = os.getenv(agent["recipient_env"], "")
            
            print(f"  Executing payment...")
            print(f"  Amount: {agent['amount']} USDC")
            print(f"  Recipient: {recipient}")
            print()
            
            try:
                result = await payment_handler.execute_payment(
                    agent_id=agent["internal_id"],
                    amount=agent["amount"],
                    recipient=recipient,
                    service_url=f"test-{agent['internal_id']}",
                    description=agent["description"]
                )
                
                results.append({
                    "agent": agent["name"],
                    "result": result
                })
                
                if result.get("status") == "SUCCESS":
                    print(f"  ✅ SUCCESS!")
                    print(f"    Transaction Hash: {result.get('tx_hash', 'N/A')}")
                    if result.get("locus_transaction_id"):
                        print(f"    Locus TX ID: {result.get('locus_transaction_id')}")
                    print(f"    Method: {result.get('payment_method', 'Unknown')}")
                elif result.get("status") == "ERROR":
                    print(f"  ❌ FAILED")
                    print(f"    Error: {result.get('error', 'Unknown error')}")
                    print(f"    Message: {result.get('message', 'No details')}")
                else:
                    print(f"  ⚠️  Status: {result.get('status')}")
                
                # Small delay between payments
                if i < len(agents):
                    await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"  ❌ EXCEPTION: {str(e)}")
                results.append({
                    "agent": agent["name"],
                    "result": {"status": "ERROR", "error": str(e)}
                })
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print()
        
        successful = sum(1 for r in results if r["result"].get("status") == "SUCCESS")
        failed = len(results) - successful
        
        print(f"Total Payments: {len(results)}")
        print(f"  ✅ Successful: {successful}")
        print(f"  ❌ Failed: {failed}")
        print()
        
        if successful > 0:
            print("✅ Successful Payments:")
            for r in results:
                if r["result"].get("status") == "SUCCESS":
                    tx_hash = r["result"].get("tx_hash", "N/A")
                    print(f"  • {r['agent']}: {tx_hash[:20]}...")
            print()
            print("🎉 Check your Locus Live dashboard to see these transactions!")
            print()
        
        if failed > 0:
            print("❌ Failed Payments:")
            for r in results:
                if r["result"].get("status") != "SUCCESS":
                    error = r["result"].get("error", "Unknown error")
                    print(f"  • {r['agent']}: {error}")
            print()
        
        print("=" * 70)
        
        return successful == len(results)
        
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("⚠️  LIVE PAYMENT TEST")
    print("=" * 70)
    print("\nThis script will make REAL A2A payments via Locus.")
    print("Each payment will be attributed to its respective agent.")
    print("All transactions will appear in your Locus Live dashboard.\n")
    
    try:
        success = asyncio.run(test_all_agents_live())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)

