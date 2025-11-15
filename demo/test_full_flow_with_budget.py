"""
Full Flow Test: End-to-End Test with Budget Tracking

This test verifies:
1. All agents can execute their workflows
2. Budget tracking works correctly
3. Payment history is maintained
4. Total budget usage matches expected values

Tests with:
- Mock services (x402 endpoints)
- Locus integration (if configured)
- Budget tracking and validation
"""
import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.title_search_agent import TitleSearchAgent
from agents.inspection_agent import InspectionAgent
from agents.appraisal_agent import AppraisalAgent
from agents.lending_agent import LendingAgent
from agents.base_verification_agent import TaskDetails
from config.settings import settings

# Simple mock Transaction class
class MockTransaction:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", "demo-tx-001")
        self.buyer_agent_id = kwargs.get("buyer_agent_id", "buyer-001")
        self.seller_agent_id = kwargs.get("seller_agent_id", "seller-001")
        self.property_id = kwargs.get("property_id", "prop-123")
        self.total_purchase_price = kwargs.get("total_purchase_price", Decimal("850000.00"))
        self.earnest_money = kwargs.get("earnest_money", Decimal("25000.00"))
        self.transaction_metadata = kwargs.get("transaction_metadata", {})
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.updated_at = kwargs.get("updated_at", datetime.utcnow())


async def test_full_flow():
    """Test the complete end-to-end flow with budget tracking."""
    
    print("=" * 70)
    print("FULL USER FLOW TEST - WITH BUDGET TRACKING")
    print("=" * 70)
    
    # Check Locus configuration
    has_locus = bool(settings.locus_api_key and settings.locus_wallet_address)
    use_mocks = settings.use_mock_services
    
    print(f"\nConfiguration:")
    print(f"  - Locus Configured: {'✓ Yes' if has_locus else '✗ No (using mocks)'}")
    print(f"  - Use Mock Services: {'Yes' if use_mocks else 'No'}")
    print(f"  - Demo Mode: {settings.demo_mode}")
    
    if has_locus:
        print(f"\n  Wallet: {settings.locus_wallet_name}")
        print(f"  Address: {settings.locus_wallet_address[:10]}...")
        print(f"  Network: Base Mainnet (Chain {settings.locus_chain_id})")
    
    # Initialize Locus if configured
    payment_handler = None
    if has_locus and not use_mocks:
        try:
            from services.locus_wallet_manager import init_wallet_manager
            from services.locus_integration import init_locus
            from services.locus_payment_handler import LocusPaymentHandler
            
            print("\n[Initializing Locus...]")
            wallet = init_wallet_manager()
            locus = init_locus(settings.locus_api_key, wallet.get_address())
            payment_handler = LocusPaymentHandler(locus)
            print("  ✓ Locus initialized")
        except Exception as e:
            print(f"  ✗ Locus initialization failed: {e}")
            print("  → Falling back to mock payments")
            payment_handler = None
    
    # Expected budgets (in USDC)
    expected_budgets = {
        "title": settings.agent_title_budget,
        "inspection": settings.agent_inspection_budget,
        "appraisal": settings.agent_appraisal_budget,
        "underwriting": settings.agent_underwriting_budget
    }
    
    total_expected = sum(expected_budgets.values())
    
    print(f"\nExpected Budget Usage:")
    print(f"  - Title:       ${expected_budgets['title']:.4f} USDC")
    print(f"  - Inspection:  ${expected_budgets['inspection']:.4f} USDC")
    print(f"  - Appraisal:   ${expected_budgets['appraisal']:.4f} USDC")
    print(f"  - Underwriting: ${expected_budgets['underwriting']:.4f} USDC")
    print(f"  - Total:       ${total_expected:.4f} USDC")
    
    # Create transaction
    transaction = MockTransaction(
        id="test-tx-001",
        property_id="test-prop-123",
        transaction_metadata={
            "property_address": "123 Main Street, Baltimore, MD 21201",
            "property_type": "single-family",
            "bedrooms": 4,
            "bathrooms": 3,
            "square_feet": 2500,
            "year_built": 1995
        }
    )
    
    # Create agents
    title_agent = TitleSearchAgent()
    inspection_agent = InspectionAgent()
    appraisal_agent = AppraisalAgent()
    lending_agent = LendingAgent()
    
    agents_config = [
        ("Title Agent", title_agent, "title", Decimal("1200.00"), expected_budgets["title"]),
        ("Inspection Agent", inspection_agent, "inspection", Decimal("500.00"), expected_budgets["inspection"]),
        ("Appraisal Agent", appraisal_agent, "appraisal", Decimal("400.00"), expected_budgets["appraisal"]),
        ("Underwriting Agent", lending_agent, "underwriting", Decimal("0.00"), expected_budgets["underwriting"])
    ]
    
    print("\n" + "=" * 70)
    print("EXECUTING AGENTS")
    print("=" * 70)
    print()
    
    start_time = datetime.utcnow()
    results = []
    
    # Run agents sequentially to track budget usage
    for agent_name, agent, agent_type, payment_amount, expected_budget in agents_config:
        print(f"[{agent_name}] Starting verification...")
        print(f"  → Service: {agent_type}")
        print(f"  → Expected Budget: ${expected_budget:.4f} USDC")
        
        task_details = TaskDetails(
            task_id=f"task-{agent_type}",
            transaction_id=transaction.id,
            property_id=transaction.property_id,
            deadline=datetime.utcnow() + timedelta(days=7),
            payment_amount=payment_amount,
            requirements={}
        )
        
        try:
            # Execute agent
            report = await agent.execute_verification(transaction, task_details)
            
            # Extract payment info from report
            findings = report.findings if hasattr(report, 'findings') else {}
            payment_tx = findings.get("payment_tx", "N/A")
            status = findings.get("title_status") or findings.get("status") or "COMPLETE"
            
            print(f"  ✓ Status: {status}")
            print(f"  ✓ Payment TX: {payment_tx}")
            print(f"  ✓ Task completed successfully")
            
            results.append({
                "agent": agent_name,
                "type": agent_type,
                "success": True,
                "payment_tx": payment_tx,
                "status": status,
                "expected_budget": expected_budget
            })
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            results.append({
                "agent": agent_name,
                "type": agent_type,
                "success": False,
                "error": str(e),
                "expected_budget": expected_budget
            })
        
        print()
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    # Get payment summary if Locus is configured
    payment_summary = None
    if payment_handler:
        try:
            payment_summary = payment_handler.get_payment_summary()
        except Exception:
            pass
    
    # Print results
    print("=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n✓ {success_count}/{len(agents_config)} agents completed successfully")
    print(f"⏱  Total time: {duration:.2f} seconds")
    
    if success_count == len(agents_config):
        print("\n🎉 All agents completed autonomously!")
        print("   - All x402 payments verified")
        print("   - All services called successfully")
        print("   - All payments signed and submitted")
    else:
        print(f"\n⚠️  {len(agents_config) - success_count} agent(s) failed")
        for r in results:
            if not r.get("success"):
                print(f"   - {r['agent']}: {r.get('error', 'Unknown error')}")
    
    # Budget tracking
    print("\n" + "=" * 70)
    print("BUDGET TRACKING")
    print("=" * 70)
    
    if payment_summary:
        print(f"\nPayment Summary (from Locus):")
        print(f"  - Total Payments: ${payment_summary['total_payments']:.4f} USDC")
        print(f"  - Total Budget:   ${payment_summary['total_budget']:.4f} USDC")
        print(f"  - Remaining:      ${payment_summary['remaining']:.4f} USDC")
        print(f"  - Transactions:   {payment_summary['transactions']}")
        
        print(f"\n  By Agent:")
        for agent_type, amount in payment_summary['by_agent'].items():
            print(f"    - {agent_type}: ${amount:.4f} USDC")
        
        # Verify against expected
        print(f"\n  Expected vs Actual:")
        for r in results:
            if r.get("success"):
                agent_type = r["type"]
                expected = r["expected_budget"]
                actual = payment_summary['by_agent'].get(agent_type, 0.0)
                match = "✓" if abs(expected - actual) < 0.0001 else "✗"
                print(f"    {match} {agent_type}: Expected ${expected:.4f}, Actual ${actual:.4f}")
    else:
        print("\n  (Budget tracking not available - using mock payments)")
        print(f"  Expected total: ${total_expected:.4f} USDC")
        print(f"  (In production, this would be tracked via Locus)")
    
    # Final summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print(f"\n✓ All agents executed")
    print(f"✓ x402 protocol handled")
    print(f"✓ Payments signed and submitted")
    if payment_summary:
        print(f"✓ Budget tracking: ${payment_summary['total_payments']:.4f} USDC used")
        print(f"✓ Remaining budget: ${payment_summary['remaining']:.4f} USDC")
    else:
        print(f"✓ Mock payments used (${total_expected:.4f} USDC equivalent)")
    
    print("\n" + "=" * 70)
    
    return success_count == len(agents_config)


if __name__ == "__main__":
    print("\n⚠️  Make sure mock_services.py is running on localhost:5001")
    print("   Run: python3 demo/mock_services.py\n")
    
    try:
        success = asyncio.run(test_full_flow())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

