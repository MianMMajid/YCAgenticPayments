#!/usr/bin/env python3
"""
Test Script: Agents Make Payments Through Normal Workflow

This script tests the full agent workflow where each agent:
1. Executes its verification task
2. Calls the service endpoint
3. Handles 402 Payment Required
4. Makes payment via Locus (real or mock)
5. Completes the verification

This uses the actual agent classes and their normal payment flow.
"""
import asyncio
import sys
import os
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from agents.title_search_agent import TitleSearchAgent
from agents.inspection_agent import InspectionAgent
from agents.appraisal_agent import AppraisalAgent
from agents.lending_agent import LendingAgent
from agents.base_verification_agent import TaskDetails

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


# Simple mock Transaction class
class MockTransaction:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", "test-tx-001")
        self.buyer_agent_id = kwargs.get("buyer_agent_id", "buyer-001")
        self.seller_agent_id = kwargs.get("seller_agent_id", "seller-001")
        self.property_id = kwargs.get("property_id", "prop-123")
        self.total_purchase_price = kwargs.get("total_purchase_price", Decimal("850000.00"))
        self.earnest_money = kwargs.get("earnest_money", Decimal("25000.00"))
        self.transaction_metadata = kwargs.get("transaction_metadata", {})
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.updated_at = kwargs.get("updated_at", datetime.utcnow())


async def test_agents_make_payments():
    """Test all agents making payments through their normal workflow."""
    
    print("=" * 70)
    print("AGENTS MAKE PAYMENTS - FULL WORKFLOW TEST")
    print("=" * 70)
    print("\nThis test runs the full agent workflow:")
    print("  1. Each agent executes its verification task")
    print("  2. Agent calls service endpoint (gets 402 Payment Required)")
    print("  3. Agent handles payment via Locus")
    print("  4. Agent completes verification")
    print()
    
    # Check configuration
    from config.settings import settings
    
    use_mock = settings.use_mock_services
    demo_mode = settings.demo_mode
    
    print("Configuration:")
    print(f"  Use Mock Services: {use_mock}")
    print(f"  Demo Mode: {demo_mode}")
    if not use_mock and not demo_mode:
        print("  ⚠️  REAL PAYMENTS ENABLED - This will make actual payments!")
    print()
    
    # Create a mock transaction
    transaction = MockTransaction(
        id="test-tx-001",
        buyer_agent_id="buyer-001",
        seller_agent_id="seller-001",
        property_id="prop-123",
        total_purchase_price=Decimal("850000.00"),
        earnest_money=Decimal("25000.00"),
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
    print("Initializing agents...")
    title_agent = TitleSearchAgent()
    inspection_agent = InspectionAgent()
    appraisal_agent = AppraisalAgent()
    lending_agent = LendingAgent()
    
    # Define agent tasks
    agents = [
        {
            "name": "Title Search Agent",
            "agent": title_agent,
            "task_details": TaskDetails(
                task_id="task-title-search",
                transaction_id=transaction.id,
                property_id=transaction.property_id,
                deadline=datetime.utcnow() + timedelta(days=7),
                payment_amount=Decimal("1200.00"),
                requirements={}
            )
        },
        {
            "name": "Inspection Agent",
            "agent": inspection_agent,
            "task_details": TaskDetails(
                task_id="task-inspection",
                transaction_id=transaction.id,
                property_id=transaction.property_id,
                deadline=datetime.utcnow() + timedelta(days=7),
                payment_amount=Decimal("500.00"),
                requirements={}
            )
        },
        {
            "name": "Appraisal Agent",
            "agent": appraisal_agent,
            "task_details": TaskDetails(
                task_id="task-appraisal",
                transaction_id=transaction.id,
                property_id=transaction.property_id,
                deadline=datetime.utcnow() + timedelta(days=7),
                payment_amount=Decimal("400.00"),
                requirements={}
            )
        },
        {
            "name": "Underwriting Agent",
            "agent": lending_agent,
            "task_details": TaskDetails(
                task_id="task-underwriting",
                transaction_id=transaction.id,
                property_id=transaction.property_id,
                deadline=datetime.utcnow() + timedelta(days=7),
                payment_amount=Decimal("0.00"),
                requirements={}
            )
        },
    ]
    
    print(f"✓ {len(agents)} agents initialized\n")
    
    print("=" * 70)
    print("EXECUTING AGENT WORKFLOWS")
    print("=" * 70)
    print()
    
    if not use_mock and not demo_mode:
        print("⚠️  REAL PAYMENTS - Starting in 3 seconds... Press Ctrl+C to cancel\n")
        await asyncio.sleep(3)
    
    results = []
    start_time = datetime.utcnow()
    
    # Execute agents in parallel
    async def execute_agent(agent_info):
        """Execute a single agent's workflow."""
        name = agent_info["name"]
        agent = agent_info["agent"]
        task_details = agent_info["task_details"]
        
        print(f"[{name}]")
        print("-" * 70)
        print(f"  Task: {task_details.task_id}")
        print(f"  Property: {task_details.property_id}")
        print(f"  Payment Amount: ${task_details.payment_amount}")
        print(f"  Executing...")
        print()
        
        try:
            # Execute the agent's verification task
            # This will automatically:
            # 1. Call the service endpoint
            # 2. Handle 402 Payment Required
            # 3. Make payment via Locus
            # 4. Complete verification
            result = await agent.execute_verification(transaction, task_details)
            
            # Extract payment info from result
            payment_tx = None
            if isinstance(result, dict):
                payment_tx = result.get("payment_tx") or result.get("tx_hash")
            
            status = "SUCCESS" if result else "FAILED"
            
            results.append({
                "agent": name,
                "status": status,
                "result": result,
                "payment_tx": payment_tx
            })
            
            if result:
                print(f"  ✅ SUCCESS")
                if payment_tx:
                    print(f"  Payment TX: {payment_tx[:30]}...")
                print()
            else:
                print(f"  ❌ FAILED")
                print()
                
        except Exception as e:
            print(f"  ❌ EXCEPTION: {str(e)}")
            print()
            results.append({
                "agent": name,
                "status": "ERROR",
                "error": str(e),
                "result": None
            })
    
    # Run all agents in parallel
    tasks = [execute_agent(agent_info) for agent_info in agents]
    await asyncio.gather(*tasks)
    
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    
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
    print(f"  ⏱️  Time: {elapsed:.2f} seconds")
    print()
    
    if successful > 0:
        print("✅ Successful Agents:")
        for r in results:
            if r["status"] == "SUCCESS":
                payment_info = ""
                if r.get("payment_tx"):
                    payment_info = f" (TX: {r['payment_tx'][:20]}...)"
                print(f"  • {r['agent']}{payment_info}")
        print()
        
        if not use_mock and not demo_mode:
            print("🎉 Check your Locus Live dashboard to see these payments!")
            print()
    
    if failed > 0:
        print("❌ Failed Agents:")
        for r in results:
            if r["status"] != "SUCCESS":
                error = r.get("error", "Unknown error")
                print(f"  • {r['agent']}: {error}")
        print()
    
    print("=" * 70)
    
    return successful == len(results)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AGENT PAYMENT WORKFLOW TEST")
    print("=" * 70)
    print("\nThis will test the full agent workflow where agents make payments")
    print("through their normal verification process.\n")
    
    try:
        success = asyncio.run(test_agents_make_payments())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

