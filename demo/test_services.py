"""
Quick test script to verify mock services work.
"""
import sys
import os
import asyncio
import httpx

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_mock_service():
    """Test a mock service endpoint."""
    print("Testing mock service endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test health endpoint
            print("\n1. Testing /health endpoint...")
            response = await client.get("http://localhost:5001/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
            else:
                print(f"   Error: {response.text}")
            
            # Test title search without payment (should get 402)
            print("\n2. Testing /landamerica/title-search without payment...")
            response = await client.post(
                "http://localhost:5001/landamerica/title-search",
                json={"property_id": "test-123"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 402:
                print("   ✓ Got 402 Payment Required (expected)")
                error_data = response.json()
                print(f"   Amount required: ${error_data.get('amount', 0)}")
            else:
                print(f"   Unexpected status: {response.text[:200]}")
            
            # Test title search with payment
            print("\n3. Testing /landamerica/title-search with payment...")
            response = await client.post(
                "http://localhost:5001/landamerica/title-search",
                json={
                    "property_id": "test-123",
                    "payment_signature": "test-signature-123",
                    "payment_tx_hash": "0xtest456"
                }
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ Payment accepted, service completed")
                result = response.json()
                print(f"   Title status: {result.get('result', {}).get('title_status', 'N/A')}")
                print(f"   Payment TX: {result.get('payment_tx', 'N/A')}")
            else:
                print(f"   Error: {response.text[:200]}")
                
    except httpx.ConnectError:
        print("\n❌ ERROR: Could not connect to http://localhost:5001")
        print("   Make sure mock_services.py is running!")
        print("   Run: python3 demo/mock_services.py")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("MOCK SERVICES TEST")
    print("=" * 60)
    result = asyncio.run(test_mock_service())
    sys.exit(0 if result else 1)

