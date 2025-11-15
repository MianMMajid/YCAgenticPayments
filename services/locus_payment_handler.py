"""Locus Payment Handler for Counter AI."""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from services.locus_integration import LocusIntegration
from services.locus_api_client import LocusAPIClient

logger = logging.getLogger(__name__)


class LocusPaymentHandler:
    """
    Process autonomous agent payments through Locus.
    
    Handles payment execution, budget checking, and payment history
    tracking for agent-based transactions.
    """
    
    def __init__(self, locus_integration: LocusIntegration, use_real_api: bool = True):
        """
        Initialize Locus Payment Handler.
        
        Args:
            locus_integration: LocusIntegration instance
            use_real_api: Whether to use real Locus API (default: True)
        """
        self.locus = locus_integration
        self.payment_history: List[Dict[str, Any]] = []
        self.use_real_api = use_real_api
        
        # Initialize API client if using real API
        self.api_client: Optional[LocusAPIClient] = None
        if use_real_api:
            # Use the main API key for the client
            api_key = locus_integration.get_api_key()
            if api_key:
                self.api_client = LocusAPIClient(api_key=api_key)
                logger.info("Locus Payment Handler initialized with real API client")
            else:
                logger.warning("No API key available, falling back to mock payments")
                self.use_real_api = False
        else:
            logger.info("Locus Payment Handler initialized (mock mode)")
    
    async def execute_payment(
        self,
        agent_id: str,
        amount: float,
        recipient: str,
        service_url: str,
        description: str
    ) -> Dict[str, Any]:
        """
        Execute payment for an agent.
        
        Flow:
        a. Get policy from agent_id
        b. Call locus.check_budget(agent_type, amount)
        c. If approved: Create payment record, log, add to history
        d. If rejected: Log rejection reason
        
        Args:
            agent_id: Agent identifier (e.g., "title-agent")
            amount: Payment amount
            recipient: Recipient wallet address
            service_url: Service endpoint URL
            description: Payment description
            
        Returns:
            Dictionary with payment result:
            {
                "status": "SUCCESS" or "REJECTED",
                "agent": "title-agent",
                "amount": 0.03,
                "recipient": "0x7A8B9C0D...",
                "tx_hash": "0xSigned_...",
                "timestamp": "2025-11-15T12:38:00Z",
                "service": service_url
            }
        """
        # Extract agent type from agent_id
        agent_type = self._extract_agent_type(agent_id)
        
        logger.info(
            f"Executing payment: {agent_id}",
            extra={
                "agent_type": agent_type,
                "amount": amount,
                "recipient": recipient[:10] + "..."
            }
        )
        
        # Step 1: Check budget
        budget_check = self.locus.check_budget(agent_type, amount)
        
        if not budget_check["approved"]:
            logger.warning(
                f"Payment rejected: {agent_id}",
                extra={
                    "amount": amount,
                    "available": budget_check["available"],
                    "budget": budget_check["budget"]
                }
            )
            
            result = {
                "status": "REJECTED",
                "reason": budget_check["message"],
                "agent": agent_id,
                "agent_type": agent_type,
                "amount": amount,
                "budget": budget_check["budget"],
                "available": budget_check["available"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # Add to history even if rejected
            self.payment_history.append(result)
            
            return result
        
        # Step 2: Payment approved - execute payment
        result = None
        agent_api_key = None
        
        if self.use_real_api:
            # Get actual agent ID and API key from environment
            import os
            actual_agent_id = self.locus.get_agent_id(agent_type)
            if not actual_agent_id:
                logger.warning(f"No agent ID found for {agent_type}, using provided agent_id")
                actual_agent_id = agent_id
            
            # Get agent-specific API key
            agent_key_map = {
                "title": os.getenv("LOCUS_AGENT_TITLE_KEY", ""),
                "inspection": os.getenv("LOCUS_AGENT_INSPECTION_KEY", ""),
                "appraisal": os.getenv("LOCUS_AGENT_APPRAISAL_KEY", ""),
                "underwriting": os.getenv("LOCUS_AGENT_UNDERWRITING_KEY", "")
            }
            agent_api_key = agent_key_map.get(agent_type, self.locus.get_api_key())
            
            if agent_api_key:
                # Create API client with agent-specific key
                api_client = LocusAPIClient(api_key=agent_api_key)
                
                # Execute real payment via Locus API
                logger.info(f"Executing real A2A payment via Locus API")
                payment_result = await api_client.execute_payment(
                    agent_id=actual_agent_id,
                    amount=amount,
                    recipient_wallet=recipient,
                    currency="USDC",
                    description=description
                )
                
                if payment_result.get("status") == "SUCCESS":
                    tx_hash = payment_result.get("transaction_hash") or payment_result.get("locus_transaction_id", "")
                    logger.info(
                        f"Real payment executed successfully: {agent_id}",
                        extra={
                            "amount": amount,
                            "tx_hash": tx_hash[:20] + "..." if tx_hash else "N/A",
                            "locus_tx_id": payment_result.get("locus_transaction_id", "")
                        }
                    )
                    
                    result = {
                        "status": "SUCCESS",
                        "agent": agent_id,
                        "agent_type": agent_type,
                        "amount": amount,
                        "recipient": recipient,
                        "tx_hash": tx_hash,
                        "locus_transaction_id": payment_result.get("locus_transaction_id"),
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "service": service_url,
                        "description": description,
                        "payment_method": "Locus API",
                        "raw_api_response": payment_result
                    }
                else:
                    # API call failed
                    error_msg = payment_result.get("error") or payment_result.get("message", "Unknown error")
                    logger.error(f"Locus API payment failed: {error_msg}")
                    
                    result = {
                        "status": "ERROR",
                        "agent": agent_id,
                        "agent_type": agent_type,
                        "amount": amount,
                        "recipient": recipient,
                        "error": error_msg,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "service": service_url,
                        "description": description,
                        "payment_method": "Locus API (failed)",
                        "raw_api_response": payment_result
                    }
            else:
                logger.warning(f"No API key for {agent_type}, falling back to mock")
        
        # Fallback to mock payment if real API not used or failed
        if not result:
            logger.info(f"Using mock payment (real API not available)")
            tx_hash = self._generate_tx_hash(agent_id, amount, recipient)
            
            result = {
                "status": "SUCCESS",
                "agent": agent_id,
                "agent_type": agent_type,
                "amount": amount,
                "recipient": recipient,
                "tx_hash": tx_hash,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "service": service_url,
                "description": description,
                "payment_method": "Mock"
            }
        
        # Add to payment history
        self.payment_history.append(result)
        
        return result
    
    def get_payment_history(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get payment history.
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            List of payment records
        """
        if agent_id:
            return [
                payment for payment in self.payment_history
                if payment.get("agent") == agent_id
            ]
        
        return self.payment_history.copy()
    
    def get_payment_summary(self) -> Dict[str, Any]:
        """
        Get payment summary statistics.
        
        Returns:
            Dictionary with summary:
            {
                "total_payments": 0.091,
                "by_agent": {
                    "title": 0.03,
                    "inspection": 0.012,
                    "appraisal": 0.010,
                    "underwriting": 0.019
                },
                "total_budget": 0.091,
                "remaining": 0.0,
                "transactions": 4
            }
        """
        successful_payments = [
            p for p in self.payment_history
            if p.get("status") == "SUCCESS"
        ]
        
        total_payments = sum(p.get("amount", 0) for p in successful_payments)
        
        by_agent = {}
        for payment in successful_payments:
            agent_type = payment.get("agent_type", "unknown")
            by_agent[agent_type] = by_agent.get(agent_type, 0) + payment.get("amount", 0)
        
        # Get total budget
        total_budget = sum(self.locus.budgets.values())
        
        # Calculate remaining
        remaining = total_budget - total_payments
        
        return {
            "total_payments": total_payments,
            "by_agent": by_agent,
            "total_budget": total_budget,
            "remaining": remaining,
            "transactions": len(successful_payments)
        }
    
    def _extract_agent_type(self, agent_id: str) -> str:
        """
        Extract agent type from agent ID.
        
        Args:
            agent_id: Agent identifier (e.g., "title-agent", "inspection-agent")
            
        Returns:
            Agent type string
        """
        agent_id_lower = agent_id.lower()
        
        if "title" in agent_id_lower:
            return "title"
        elif "inspection" in agent_id_lower:
            return "inspection"
        elif "appraisal" in agent_id_lower:
            return "appraisal"
        elif "underwriting" in agent_id_lower or "lending" in agent_id_lower:
            return "underwriting"
        else:
            logger.warning(f"Unknown agent type for agent_id: {agent_id}, defaulting to 'title'")
            return "title"
    
    def _generate_tx_hash(self, agent_id: str, amount: float, recipient: str) -> str:
        """
        Generate transaction hash (mock for demo).
        
        In production, this would create an actual blockchain transaction
        and return the real transaction hash.
        
        Args:
            agent_id: Agent identifier
            amount: Payment amount
            recipient: Recipient address
            
        Returns:
            Mock transaction hash
        """
        import hashlib
        import time
        
        data = f"{agent_id}:{amount}:{recipient}:{time.time()}"
        hash_obj = hashlib.sha256(data.encode())
        return "0x" + hash_obj.hexdigest()[:40]

