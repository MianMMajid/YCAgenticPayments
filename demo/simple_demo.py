"""
Simple Demo: Test x402 Payment Handling Without Database

This demo directly tests the mock service client to show x402 payment handling
without requiring database initialization.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from demo.mock_service_client import MockServiceClient
from decimal import Decimal


async def test_all_services():
    """Test all mock services with x402 payment handling."""
    
    print("=" * 60)
    print("AUTONOMOUS x402 PAYMENT HANDLING DEMO")
    print("=" * 60)
    print("\nThis demo shows how agents handle x402 Payment Required:")
    print("  1. Call service → Get 402")
    print("  2. Sign payment automatically")
    print("  3. Retry with payment → Success")
    print("\n" + "=" * 60 + "\n")
    
    client = MockServiceClient()
    
    services = [
        ("Title Search", "/landamerica/title-search", Decimal("1200.00")),
        ("Inspection", "/amerispec/inspection", Decimal("500.00")),
        ("Appraisal", "/corelogic/valuation", Decimal("400.00")),
        ("Loan Verification", "/fanniemae/verify", Decimal("0.00"))
    ]
    
    print("Starting service calls...\n")
    start_time = asyncio.get_event_loop().time()
    
    results = []
    for service_name, endpoint, amount in services:
        print(f"[{service_name}] Calling {endpoint}")
        try:
            result = await client.call_service_with_payment(
                endpoint=endpoint,
                property_id="demo-prop-123",
                transaction_id="demo-tx-001",
                amount=amount,
                additional_data={"purchase_price": 850000} if "valuation" in endpoint else {}
            )
            
            # Extract key info from result
            result_data = result.get("result", {})
            status = result_data.get("status") or result_data.get("title_status") or "Complete"
            tx_hash = result.get("payment_tx", "N/A")
            
            print(f"[{service_name}] ✓ SUCCESS - {status}")
            print(f"[{service_name}] ✓ TX: {tx_hash}")
            print()
            
            results.append((service_name, True))
        except Exception as e:
            print(f"[{service_name}] ✗ Error: {str(e)}")
            print()
            results.append((service_name, False))
    
    end_time = asyncio.get_event_loop().time()
    duration = end_time - start_time
    
    print("=" * 60)
    print("DEMO RESULTS")
    print("=" * 60)
    
    success_count = sum(1 for _, success in results if success)
    print(f"\n✓ {success_count}/{len(services)} services completed successfully")
    print(f"⏱  Total time: {duration:.2f} seconds")
    
    if success_count == len(services):
        print("\n🎉 All services completed autonomously!")
        print("   - All x402 payments verified")
        print("   - All services called successfully")
        print("   - All payments signed and submitted")
    else:
        print(f"\n⚠️  {len(services) - success_count} service(s) failed")
        for service_name, success in results:
            if not success:
                print(f"   - {service_name} failed")
    
    print("\n" + "=" * 60)
    
    return success_count == len(services)


if __name__ == "__main__":
    print("\n⚠️  Make sure mock_services.py is running on localhost:5001")
    print("   Run: python3 demo/mock_services.py\n")
    
    try:
        success = asyncio.run(test_all_services())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nDemo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

