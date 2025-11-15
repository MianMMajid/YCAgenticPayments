"""
Mock Service Client for Demo

Handles HTTP calls to mock x402 payment services with automatic payment handling.
"""
import httpx
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from demo.payment_helper import generate_payment_signature

logger = logging.getLogger(__name__)


class MockServiceError(Exception):
    """Exception raised for mock service errors."""
    pass


class MockServiceClient:
    """Client for interacting with mock x402 payment services."""
    
    BASE_URL = "http://localhost:5001"
    
    async def call_service_with_payment(
        self,
        endpoint: str,
        property_id: str,
        transaction_id: str,
        amount: Decimal,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call a mock service endpoint, handling 402 Payment Required automatically.
        
        Args:
            endpoint: Service endpoint (e.g., "/landamerica/title-search")
            property_id: Property identifier
            transaction_id: Transaction identifier
            amount: Payment amount required
            additional_data: Additional data to include in request
            
        Returns:
            Service response data
            
        Raises:
            MockServiceError: If service call fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        # Prepare request data
        request_data = {
            "property_id": property_id,
            "transaction_id": transaction_id,
            **(additional_data or {})
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First attempt - will likely get 402
                logger.info(f"[{endpoint}] Calling {url}")
                response = await client.post(url, json=request_data)
                
                # Handle 402 Payment Required
                if response.status_code == 402:
                    logger.info(f"[{endpoint}] Got 402 Payment Required")
                    error_data = response.json()
                    
                    # Generate payment signature
                    payment_info = generate_payment_signature(
                        service_endpoint=endpoint,
                        amount=amount,
                        property_id=property_id,
                        transaction_id=transaction_id
                    )
                    
                    logger.info(f"[{endpoint}] Signed payment: {payment_info['payment_tx_hash']}")
                    
                    # Add payment to request
                    request_data.update({
                        "payment_signature": payment_info["payment_signature"],
                        "payment_tx_hash": payment_info["payment_tx_hash"]
                    })
                    
                    # Retry with payment
                    logger.info(f"[{endpoint}] Retrying with payment...")
                    response = await client.post(url, json=request_data)
                
                # Check for success
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"[{endpoint}] SUCCESS - {result.get('result', {}).get('status', 'Complete')}")
                    logger.info(f"[{endpoint}] TX: {result.get('payment_tx', 'N/A')}")
                    return result
                else:
                    error_msg = f"Service error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('message', '')}"
                    except:
                        error_msg += f" - {response.text[:100]}"
                    raise MockServiceError(error_msg)
                    
        except httpx.TimeoutException:
            raise MockServiceError(f"Request timeout for {endpoint}")
        except httpx.NetworkError as e:
            raise MockServiceError(f"Network error for {endpoint}: {str(e)}")
        except Exception as e:
            if isinstance(e, MockServiceError):
                raise
            raise MockServiceError(f"Unexpected error calling {endpoint}: {str(e)}")

