#!/usr/bin/env python3
"""
Test Script: Agents Make Payments Directly

This script directly calls each agent's payment method to test payments
without requiring database initialization.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from config.settings import settings

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


async def test_agent_payment(agent_name, perform_method, property_id, transaction_id):
    """Test a single agent's payment method."""
    print(f"[{agent_name}]")
    print("-" * 70)
    print(f"  Property ID: {property_id}")
    print(f"  Executing payment...")
    print()
    
    try:
        # Create a simple mock transaction object with all required attributes
        class MockTransaction:
            def __init__(self):
                self.id = transaction_id
                self.property_id = property_id
                self.total_purchase_price = 850000.00
                self.earnest_money = 25000.00
                self.transaction_metadata = {
                    "property_address": "123 Main Street, Baltimore, MD 21201",
                    "property_type": "single-family",
                    "bedrooms": 4,
                    "bathrooms": 3,
                    "square_feet": 2500,
                    "year_built": 1995
                }
        
        transaction = MockTransaction()
        
        # Call the agent's payment method directly
        result = await perform_method(property_id, transaction)
        
        # Extract payment info
        payment_tx = result.get("payment_tx") or result.get("tx_hash") or "N/A"
        
        print(f"  ✅ SUCCESS")
        print(f"  Payment TX: {payment_tx[:50]}...")
        if result.get("title_status"):
            print(f"  Title Status: {result.get('title_status')}")
        if result.get("inspection_date"):
            print(f"  Inspection Date: {result.get('inspection_date')}")
        if result.get("appraised_value"):
            print(f"  Appraised Value: ${result.get('appraised_value'):,.2f}")
        if result.get("loan_approved"):
            print(f"  Loan Approved: {result.get('loan_approved')}")
        print()
        
        return {
            "agent": agent_name,
            "status": "SUCCESS",
            "payment_tx": payment_tx,
            "result": result
        }
        
    except Exception as e:
        print(f"  ❌ FAILED: {str(e)}")
        print()
        return {
            "agent": agent_name,
            "status": "ERROR",
            "error": str(e)
        }


async def test_all_agents_payments():
    """Test all agents making payments."""
    
    print("=" * 70)
    print("AGENTS MAKE PAYMENTS - DIRECT TEST")
    print("=" * 70)
    print("\nThis test directly calls each agent's payment method.")
    print("Each agent will:")
    print("  1. Call service endpoint")
    print("  2. Handle 402 Payment Required")
    print("  3. Make payment via Locus")
    print("  4. Return results")
    print()
    
    # Check configuration
    use_mock = settings.use_mock_services
    demo_mode = settings.demo_mode
    
    print("Configuration:")
    print(f"  Use Mock Services: {use_mock}")
    print(f"  Demo Mode: {demo_mode}")
    if not use_mock and not demo_mode:
        print("  ⚠️  REAL PAYMENTS ENABLED - This will make actual payments!")
    print()
    
    # Import agents
    from agents.title_search_agent import TitleSearchAgent
    from agents.inspection_agent import InspectionAgent
    from agents.appraisal_agent import AppraisalAgent
    from agents.lending_agent import LendingAgent
    
    # Create agents
    title_agent = TitleSearchAgent()
    inspection_agent = InspectionAgent()
    appraisal_agent = AppraisalAgent()
    lending_agent = LendingAgent()
    
    # Test parameters
    property_id = "test-prop-123"
    transaction_id = "test-tx-001"
    
    # Define agent tests
    agent_tests = [
        ("Title Search Agent", title_agent._perform_title_search),
        ("Inspection Agent", inspection_agent._perform_inspection),
        ("Appraisal Agent", appraisal_agent._perform_appraisal),
        ("Underwriting Agent", lending_agent._perform_lending_verification),
    ]
    
    print("=" * 70)
    print("EXECUTING AGENT PAYMENTS")
    print("=" * 70)
    print()
    
    if not use_mock and not demo_mode:
        print("⚠️  REAL PAYMENTS - Starting in 3 seconds... Press Ctrl+C to cancel\n")
        await asyncio.sleep(3)
    
    # Execute all agents in parallel
    tasks = [
        test_agent_payment(name, method, property_id, transaction_id)
        for name, method in agent_tests
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    
    successful = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = len(results) - successful
    
    print(f"Total Agents: {len(results)}")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print()
    
    if successful > 0:
        print("✅ Successful Payments:")
        for r in results:
            if r["status"] == "SUCCESS":
                tx = r.get("payment_tx", "N/A")
                print(f"  • {r['agent']}: {tx[:30]}...")
        print()
        
        if not use_mock and not demo_mode:
            print("🎉 Check your Locus Live dashboard to see these payments!")
            print()
    
    if failed > 0:
        print("❌ Failed Payments:")
        for r in results:
            if r["status"] != "SUCCESS":
                error = r.get("error", "Unknown error")
                print(f"  • {r['agent']}: {error}")
        print()
    
    print("=" * 70)
    
    return successful == len(results)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AGENT PAYMENT DIRECT TEST")
    print("=" * 70)
    print("\nThis will test agents making payments directly through their")
    print("internal payment methods.\n")
    
    try:
        success = asyncio.run(test_all_agents_payments())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

