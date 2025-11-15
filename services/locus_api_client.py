"""Locus API Client for real A2A payments.

Based on Locus MCP Spec: https://docs.paywithlocus.com/mcp-spec

The MCP server provides built-in payment tools:
- send_to_address: Send USDC to any wallet address
- send_to_contact: Send to whitelisted contacts
- send_to_email: Send via email escrow

This client calls the backend API that the MCP server uses.
"""
import logging
import httpx
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Locus API Base URL
# Based on MCP spec: https://docs.paywithlocus.com/mcp-spec
# The MCP server proxies to backend endpoints
# Found working endpoint: https://app.paywithlocus.com/api/mcp/send_to_address
LOCUS_API_BASE_URL = os.getenv("LOCUS_API_BASE_URL", "https://app.paywithlocus.com")


class LocusAPIClient:
    """
    Client for making real Locus API calls.
    
    Handles authentication and payment execution for agent-to-agent payments.
    """
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Initialize Locus API Client.
        
        Args:
            api_key: Agent API key for authentication
            base_url: Optional base URL (defaults to LOCUS_API_BASE_URL)
        """
        self.api_key = api_key
        self.base_url = base_url or LOCUS_API_BASE_URL
        # Authentication based on MCP spec: https://docs.paywithlocus.com/mcp-spec
        # API keys prefixed with 'locus_' are validated by backend
        # Backend returns associated OAuth client scopes
        # Try both Bearer token and X-API-Key formats
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": api_key  # Some APIs use header instead of Bearer
        }
        
        logger.info(f"Locus API Client initialized (base_url: {self.base_url})")
    
    async def execute_payment(
        self,
        agent_id: str,
        amount: float,
        recipient_wallet: str,
        currency: str = "USDC",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an agent-to-agent payment via Locus API.
        
        Args:
            agent_id: Agent ID making the payment
            amount: Payment amount in USDC
            recipient_wallet: Recipient wallet address
            currency: Currency (default: USDC)
            description: Optional payment description
            
        Returns:
            Dictionary with payment result:
            {
                "status": "SUCCESS",
                "transaction_hash": "0x...",
                "amount": 0.03,
                "recipient": "0x...",
                "timestamp": "2025-11-15T...",
                "locus_transaction_id": "..."
            }
        """
        logger.info(
            f"Executing A2A payment via Locus API",
            extra={
                "agent_id": agent_id,
                "amount": amount,
                "recipient": recipient_wallet[:20] + "..."
            }
        )
        
        # Payment request payload based on MCP spec send_to_address tool
        # According to MCP spec: send_to_address(address, amount, memo)
        payload = {
            "address": recipient_wallet,
            "amount": amount,
            "memo": description or f"Payment from agent {agent_id}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Based on MCP spec: https://docs.paywithlocus.com/mcp-spec
                # The MCP server proxies to backend API at /api/mcp/tools/send_to_address
                # Found via testing: api.paywithlocus.com/api/mcp/tools/send_to_address returns 401 JSON
                # This is the correct endpoint - need proper authentication
                endpoints = [
                    # Primary endpoint (from MCP spec - correct endpoint!)
                    "https://api.paywithlocus.com/api/mcp/tools/send_to_address",
                    # Alternative MCP endpoints
                    "https://api.paywithlocus.com/api/mcp/tools/execute",
                    "https://api.paywithlocus.com/api/mcp/send_to_address",
                    # Fallback endpoints
                    f"{self.base_url}/api/mcp/send_to_address",
                    f"{self.base_url}/api/mcp/payments/send_to_address",
                    f"{self.base_url}/mcp/send_to_address",
                    f"{self.base_url}/api/v1/payments/send_to_address",
                    f"{self.base_url}/api/v1/payments",
                ]
                
                last_error = None
                for endpoint in endpoints:
                    try:
                        logger.debug(f"Trying endpoint: {endpoint}")
                        response = await client.post(
                            endpoint,
                            json=payload,
                            headers=self.headers
                        )
                        
                        if response.status_code == 200 or response.status_code == 201:
                            # Try to parse JSON response
                            try:
                                result = response.json()
                            except Exception as json_error:
                                # If not JSON, check if it's HTML or text
                                response_text = response.text[:500]
                                logger.warning(f"Response is not JSON: {response_text[:100]}")
                                
                                # Check if it's HTML (might be a redirect or error page)
                                if response_text.strip().startswith("<"):
                                    return {
                                        "status": "ERROR",
                                        "error": "Received HTML response instead of JSON",
                                        "message": "Endpoint may require different authentication or format",
                                        "response_preview": response_text[:200]
                                    }
                                
                                # Try to extract transaction info from text
                                return {
                                    "status": "SUCCESS",
                                    "transaction_hash": "unknown",
                                    "amount": amount,
                                    "recipient": recipient_wallet,
                                    "currency": currency,
                                    "timestamp": datetime.utcnow().isoformat() + "Z",
                                    "description": description,
                                    "raw_response": response_text,
                                    "note": "Response was not JSON format"
                                }
                            
                            logger.info(
                                f"Payment executed successfully",
                                extra={
                                    "tx_hash": result.get("transaction_hash", "")[:20] + "..." if result.get("transaction_hash") else "N/A",
                                    "status_code": response.status_code
                                }
                            )
                            
                            return {
                                "status": "SUCCESS",
                                "transaction_hash": result.get("transaction_hash") or result.get("tx_hash") or result.get("id") or result.get("transaction_id"),
                                "locus_transaction_id": result.get("id") or result.get("transaction_id") or result.get("locus_transaction_id"),
                                "amount": amount,
                                "recipient": recipient_wallet,
                                "currency": currency,
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "description": description,
                                "raw_response": result
                            }
                        elif response.status_code == 401:
                            logger.error("Authentication failed - check API key")
                            return {
                                "status": "ERROR",
                                "error": "Authentication failed",
                                "message": "Invalid API key or agent ID"
                            }
                        elif response.status_code == 402:
                            logger.warning("Payment required or insufficient funds")
                            return {
                                "status": "ERROR",
                                "error": "Payment required",
                                "message": "Insufficient funds or payment required"
                            }
                        else:
                            last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                            logger.warning(f"Endpoint {endpoint} returned {response.status_code}")
                            continue
                            
                    except httpx.TimeoutException:
                        last_error = "Request timeout"
                        logger.warning(f"Timeout on endpoint: {endpoint}")
                        continue
                    except httpx.NetworkError as e:
                        last_error = f"Network error: {str(e)}"
                        logger.warning(f"Network error on endpoint: {endpoint}: {e}")
                        continue
                    except Exception as e:
                        last_error = f"Error: {str(e)}"
                        logger.warning(f"Error on endpoint: {endpoint}: {e}")
                        continue
                
                # If all endpoints failed, return error
                logger.error(f"All payment endpoints failed. Last error: {last_error}")
                return {
                    "status": "ERROR",
                    "error": "All API endpoints failed",
                    "message": last_error or "Unknown error",
                    "tried_endpoints": endpoints
                }
                
        except Exception as e:
            logger.error(f"Payment execution failed: {str(e)}", exc_info=True)
            return {
                "status": "ERROR",
                "error": str(e),
                "message": f"Payment execution failed: {str(e)}"
            }
    
    async def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent information from Locus API.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Dictionary with agent info
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                endpoints = [
                    f"{self.base_url}/v1/agents/{agent_id}",
                    f"{self.base_url}/api/v1/agents/{agent_id}",
                    f"{self.base_url}/agents/{agent_id}",
                ]
                
                for endpoint in endpoints:
                    try:
                        response = await client.get(endpoint, headers=self.headers)
                        if response.status_code == 200:
                            return response.json()
                    except Exception:
                        continue
                
                return {"error": "Could not fetch agent info"}
        except Exception as e:
            logger.error(f"Failed to get agent info: {e}")
            return {"error": str(e)}
    
    async def get_wallet_balance(self, wallet_address: str) -> Dict[str, Any]:
        """
        Get wallet balance from Locus API.
        
        Args:
            wallet_address: Wallet address
            
        Returns:
            Dictionary with balance info
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                endpoints = [
                    f"{self.base_url}/v1/wallets/{wallet_address}/balance",
                    f"{self.base_url}/api/v1/wallets/{wallet_address}",
                    f"{self.base_url}/wallets/{wallet_address}",
                ]
                
                for endpoint in endpoints:
                    try:
                        response = await client.get(endpoint, headers=self.headers)
                        if response.status_code == 200:
                            return response.json()
                    except Exception:
                        continue
                
                return {"error": "Could not fetch wallet balance"}
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {e}")
            return {"error": str(e)}

