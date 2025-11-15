"""
Demo Script: Autonomous Agents with x402 Payment Handling

This script demonstrates how the escrow agents autonomously:
1. Call third-party services
2. Handle 402 Payment Required responses
3. Sign and submit payments
4. Complete verification tasks

Run this after starting mock_services.py in another terminal.
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
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any

# Simple mock Transaction class to avoid database initialization
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


async def run_demo():
    """Run the autonomous agent demo."""
    
    print("=" * 60)
    print("AUTONOMOUS ESCROW AGENTS DEMO")
    print("=" * 60)
    print("\nThis demo shows agents autonomously:")
    print("  1. Calling third-party services")
    print("  2. Handling 402 Payment Required responses")
    print("  3. Signing and submitting payments")
    print("  4. Completing verification tasks")
    print("\n" + "=" * 60 + "\n")
    
    # Create a mock transaction (avoiding database initialization)
    transaction = MockTransaction(
        id="demo-tx-001",
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
    title_agent = TitleSearchAgent()
    inspection_agent = InspectionAgent()
    appraisal_agent = AppraisalAgent()
    lending_agent = LendingAgent()
    
    agents = [
        ("Title Agent", title_agent, "/landamerica/title-search", Decimal("1200.00")),
        ("Inspection Agent", inspection_agent, "/amerispec/inspection", Decimal("500.00")),
        ("Appraisal Agent", appraisal_agent, "/corelogic/valuation", Decimal("400.00")),
        ("Underwriting Agent", lending_agent, "/fanniemae/verify", Decimal("0.00"))
    ]
    
    print("Starting autonomous agent execution...\n")
    start_time = datetime.utcnow()
    
    # Run all agents in parallel
    tasks = []
    for agent_name, agent, endpoint, amount in agents:
        task_details = TaskDetails(
            task_id=f"task-{agent_name.lower().replace(' ', '-')}",
            transaction_id=transaction.id,
            property_id=transaction.property_id,
            deadline=datetime.utcnow() + timedelta(days=7),
            payment_amount=amount,
            requirements={}
        )
        
        async def run_agent(agent_name, agent, endpoint, amount, task_details):
            print(f"[{agent_name}] Calling http://localhost:5001{endpoint}")
            try:
                report = await agent.execute_verification(transaction, task_details)
                print(f"[{agent_name}] ✓ Task completed successfully")
                if hasattr(report, 'findings') and report.findings:
                    findings = report.findings
                    if "payment_tx" in findings:
                        print(f"[{agent_name}] ✓ Payment TX: {findings['payment_tx']}")
                return True
            except Exception as e:
                print(f"[{agent_name}] ✗ Error: {str(e)}")
                return False
        
        tasks.append(run_agent(agent_name, agent, endpoint, amount, task_details))
    
    # Wait for all agents to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("DEMO RESULTS")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r is True)
    print(f"\n✓ {success_count}/{len(agents)} agents completed successfully")
    print(f"⏱  Total time: {duration:.2f} seconds")
    
    if success_count == len(agents):
        print("\n🎉 All agents completed autonomously!")
        print("   - All x402 payments verified")
        print("   - All services called successfully")
        print("   - All tasks completed")
    else:
        print(f"\n⚠️  {len(agents) - success_count} agent(s) failed")
        for i, (agent_name, _, _, _) in enumerate(agents):
            if results[i] is not True:
                print(f"   - {agent_name} failed")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n⚠️  Make sure mock_services.py is running on localhost:5001")
    print("   Run: python demo/mock_services.py\n")
    
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nDemo failed: {str(e)}")
        import traceback
        traceback.print_exc()

