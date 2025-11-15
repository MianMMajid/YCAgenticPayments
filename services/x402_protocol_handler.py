"""x402 Protocol Handler for Counter AI."""
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class X402ProtocolHandler:
    """
    Handle x402 payment protocol (HTTP 402).
    
    Implements the x402 payment flow:
    1. Agent calls service (GET)
    2. Service returns 402 Payment Required
    3. Agent extracts: amount, challenge
    4. Agent signs payment with wallet
    5. Agent retries (POST) with X-PAYMENT header
    6. Service verifies and returns data
    """
    
    def __init__(self, payment_handler=None):
        """
        Initialize x402 Protocol Handler.
        
        Args:
            payment_handler: Optional payment handler for signing payments
        """
        self.payment_handler = payment_handler
        logger.info("x402 Protocol Handler initialized")
    
    def parse_402_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Parse HTTP 402 Payment Required response.
        
        Args:
            response: HTTP 402 response object
            
        Returns:
            Dictionary with parsed response:
            {
                "status": 402,
                "amount": 0.03,
                "challenge": "landamerica_title_...",
                "service": "LandAmerica"
            }
        """
        try:
            data = response.json()
        except Exception:
            data = {}
        
        result = {
            "status": response.status_code,
            "amount": data.get("amount", 0.0),
            "challenge": data.get("challenge") or data.get("payment_endpoint", ""),
            "service": data.get("service") or self._extract_service_name(response.url.path),
            "message": data.get("message", "Payment Required"),
            "currency": data.get("currency", "USD")
        }
        
        logger.info(
            "Parsed 402 response",
            extra={
                "amount": result["amount"],
                "service": result["service"]
            }
        )
        
        return result
    
    def sign_payment(self, challenge: str, amount: float) -> str:
        """
        Sign payment challenge.
        
        In production, this would sign with the wallet's private key.
        For now, generates a deterministic signature.
        
        Args:
            challenge: Payment challenge string
            amount: Payment amount
            
        Returns:
            Payment signature string (e.g., "0xSigned_[challenge]_[timestamp]")
        """
        import hashlib
        import time
        
        timestamp = int(time.time())
        data = f"{challenge}:{amount}:{timestamp}"
        hash_obj = hashlib.sha256(data.encode())
        signature = "0xSigned_" + hash_obj.hexdigest()[:32]
        
        logger.debug(
            "Payment signed",
            extra={
                "challenge": challenge[:20] + "...",
                "amount": amount
            }
        )
        
        return signature
    
    async def execute_x402_flow(
        self,
        service_url: str,
        amount: float,
        agent_id: Optional[str] = None,
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute complete x402 payment flow.
        
        Flow:
        a. GET to service_url
        b. If 402: parse response
        c. Sign payment challenge
        d. POST to service_url with X-PAYMENT header
        e. Parse response
        f. Return result
        
        Args:
            service_url: Service endpoint URL
            amount: Expected payment amount
            agent_id: Optional agent ID for payment handler
            recipient: Optional recipient address for payment handler
            
        Returns:
            Dictionary with result:
            {
                "status": "success" or "failed",
                "data": {...},
                "payment_signed": "0xSigned_...",
                "tx_hash": "0x..."
            }
        """
        logger.info(
            f"Executing x402 flow: {service_url}",
            extra={"amount": amount}
        )
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Initial GET request
                logger.debug(f"Step 1: GET {service_url}")
                response1 = await client.get(service_url)
                
                if response1.status_code != 402:
                    logger.warning(
                        f"Expected 402, got {response1.status_code}",
                        extra={"url": service_url}
                    )
                    return {
                        "status": "failed",
                        "error": f"Expected 402 Payment Required, got {response1.status_code}",
                        "response_status": response1.status_code
                    }
                
                # Step 2: Parse 402 response
                logger.debug("Step 2: Parsing 402 response")
                payment_info = self.parse_402_response(response1)
                
                # Step 3: Sign payment
                logger.debug("Step 3: Signing payment")
                challenge = payment_info.get("challenge", service_url)
                
                # If payment handler available, use it
                if self.payment_handler and agent_id and recipient:
                    payment_result = await self.payment_handler.execute_payment(
                        agent_id=agent_id,
                        amount=amount,
                        recipient=recipient,
                        service_url=service_url,
                        description=f"x402 payment for {service_url}"
                    )
                    
                    if payment_result.get("status") != "SUCCESS":
                        return {
                            "status": "failed",
                            "error": "Payment rejected",
                            "payment_result": payment_result
                        }
                    
                    signature = payment_result.get("tx_hash", "")
                    tx_hash = payment_result.get("tx_hash", "")
                else:
                    # Fallback to simple signing
                    signature = self.sign_payment(challenge, amount)
                    tx_hash = signature
                
                # Step 4: Retry with payment header
                logger.debug("Step 4: Retrying with payment header")
                response2 = await self.retry_with_payment_header(
                    client=client,
                    url=service_url,
                    signature=signature
                )
                
                # Step 5: Parse final response
                if response2.status_code == 200:
                    try:
                        data = response2.json()
                    except Exception:
                        data = {"raw_response": response2.text}
                    
                    logger.info(
                        "x402 flow completed successfully",
                        extra={"service": service_url}
                    )
                    
                    return {
                        "status": "success",
                        "data": data,
                        "payment_signed": signature,
                        "tx_hash": tx_hash,
                        "service": payment_info.get("service")
                    }
                else:
                    logger.error(
                        f"Payment retry failed: {response2.status_code}",
                        extra={"url": service_url}
                    )
                    
                    return {
                        "status": "failed",
                        "error": f"Payment retry failed with status {response2.status_code}",
                        "response_status": response2.status_code,
                        "payment_signed": signature
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"x402 flow timeout: {service_url}")
            return {
                "status": "failed",
                "error": "Request timeout"
            }
        except httpx.NetworkError as e:
            logger.error(f"x402 flow network error: {service_url}", exc_info=True)
            return {
                "status": "failed",
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"x402 flow error: {service_url}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def retry_with_payment_header(
        self,
        client: httpx.AsyncClient,
        url: str,
        signature: str
    ) -> httpx.Response:
        """
        Retry request with X-PAYMENT header.
        
        Args:
            client: httpx AsyncClient instance
            url: Service URL
            signature: Payment signature
            
        Returns:
            HTTP response
        """
        headers = {
            "X-PAYMENT": signature,
            "Content-Type": "application/json"
        }
        
        logger.debug(
            "Retrying with payment header",
            extra={"url": url, "signature": signature[:20] + "..."}
        )
        
        # Try POST first, fallback to GET
        try:
            response = await client.post(url, headers=headers, json={})
        except Exception:
            response = await client.get(url, headers=headers)
        
        return response
    
    def _extract_service_name(self, path: str) -> str:
        """
        Extract service name from URL path.
        
        Args:
            path: URL path
            
        Returns:
            Service name
        """
        service_map = {
            "landamerica": "LandAmerica",
            "amerispec": "AmeriSpec",
            "corelogic": "CoreLogic",
            "fanniemae": "Fannie Mae"
        }
        
        path_lower = path.lower()
        for key, name in service_map.items():
            if key in path_lower:
                return name
        
        return "Unknown Service"

