"""Locus Integration service for Counter AI."""
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global singleton instance
_locus_instance: Optional['LocusIntegration'] = None


class LocusIntegration:
    """
    Main integration point with Locus payment infrastructure.
    
    Manages policies, budgets, and agent configurations for autonomous
    payment processing through Locus.
    """
    
    # Agent type mappings
    AGENT_TYPES = {
        "title": "title",
        "inspection": "inspection",
        "appraisal": "appraisal",
        "underwriting": "underwriting",
        "lending": "underwriting"  # Alias for lending agent
    }
    
    def __init__(self, api_key: str, wallet_address: str):
        """
        Initialize Locus Integration.
        
        Args:
            api_key: Locus API key (LOCUS_API_KEY from .env)
            wallet_address: Wallet address from wallet manager
        """
        self.api_key = api_key
        self.wallet_address = wallet_address
        
        # Note: No Policy Groups needed - just Agent IDs and wallets
        # Load budgets from environment (support both env var formats)
        self.budgets = {
            "title": float(os.getenv("AGENT_TITLE_BUDGET", os.getenv("agent_title_budget", "0.03"))),
            "inspection": float(os.getenv("AGENT_INSPECTION_BUDGET", os.getenv("agent_inspection_budget", "0.012"))),
            "appraisal": float(os.getenv("AGENT_APPRAISAL_BUDGET", os.getenv("agent_appraisal_budget", "0.010"))),
            "underwriting": float(os.getenv("AGENT_UNDERWRITING_BUDGET", os.getenv("agent_underwriting_budget", "0.019")))
        }
        
        # Track budget usage (in production, this would be persisted)
        self.budget_usage = {
            "title": 0.0,
            "inspection": 0.0,
            "appraisal": 0.0,
            "underwriting": 0.0
        }
        
        logger.info(
            "Initializing Locus Integration",
            extra={
                "wallet_address": wallet_address[:10] + "...",
                "agents_configured": len([k for k in self.budgets.keys()])
            }
        )
        
        # Print summary on init
        self._print_summary()
    
    def _print_summary(self) -> None:
        """Print initialization summary."""
        total_budget = sum(self.budgets.values())
        logger.info(
            "Locus Integration initialized",
            extra={
                "total_budget": total_budget,
                "agents_configured": len(self.budgets)
            }
        )
        print(f"  ✓ Locus API initialized")
        print(f"  ✓ Total budget: ${total_budget:.4f}/day")
    
    def get_agent_id(self, agent_type: str) -> str:
        """
        Get agent ID for agent type.
        
        Args:
            agent_type: Agent type ("title", "inspection", "appraisal", "underwriting")
            
        Returns:
            Agent ID string from environment
            
        Raises:
            ValueError: If agent type is invalid
        """
        # Normalize agent type
        normalized_type = self.AGENT_TYPES.get(agent_type.lower(), agent_type.lower())
        
        if normalized_type not in self.AGENT_TYPES.values():
            raise ValueError(
                f"Invalid agent type: {agent_type}. "
                f"Valid types: {list(self.AGENT_TYPES.keys())}"
            )
        
        # Map agent type to environment variable name
        env_var_map = {
            "title": "LOCUS_AGENT_TITLE_ID",
            "inspection": "LOCUS_AGENT_INSPECTION_ID",
            "appraisal": "LOCUS_AGENT_APPRAISAL_ID",
            "underwriting": "LOCUS_AGENT_UNDERWRITING_ID"
        }
        
        agent_id = os.getenv(env_var_map.get(normalized_type, ""), "")
        
        if not agent_id:
            logger.warning(f"No agent ID configured for agent type: {agent_type}")
        
        return agent_id
    
    def get_budget(self, agent_type: str) -> float:
        """
        Get budget for agent type.
        
        Args:
            agent_type: Agent type ("title", "inspection", "appraisal", "underwriting")
            
        Returns:
            Budget amount as float
        """
        normalized_type = self.AGENT_TYPES.get(agent_type.lower(), agent_type.lower())
        return self.budgets.get(normalized_type, 0.0)
    
    def check_budget(self, agent_type: str, amount: float) -> Dict[str, Any]:
        """
        Check if payment amount is within budget.
        
        Args:
            agent_type: Agent type
            amount: Payment amount to check
            
        Returns:
            Dictionary with budget check results:
            {
                "agent": "title",
                "amount": 0.03,
                "budget": 0.03,
                "available": 0.03,
                "approved": True,
                "message": "Payment approved"
            }
        """
        normalized_type = self.AGENT_TYPES.get(agent_type.lower(), agent_type.lower())
        budget = self.budgets.get(normalized_type, 0.0)
        used = self.budget_usage.get(normalized_type, 0.0)
        available = budget - used
        
        approved = amount <= available
        
        result = {
            "agent": normalized_type,
            "amount": amount,
            "budget": budget,
            "used": used,
            "available": available,
            "approved": approved,
            "message": "Payment approved" if approved else "Amount exceeds available budget"
        }
        
        if approved:
            # Update usage (in production, this would be persisted)
            self.budget_usage[normalized_type] = used + amount
            logger.info(
                f"Budget check approved: {normalized_type}",
                extra={"amount": amount, "available": available - amount}
            )
        else:
            logger.warning(
                f"Budget check rejected: {normalized_type}",
                extra={"amount": amount, "available": available, "budget": budget}
            )
        
        return result
    
    def get_all_agent_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all agent information including budgets.
        
        Returns:
            Dictionary mapping agent types to their info:
            {
                "title": {
                    "agent_id": "ooeju0aot520uv7dd77nr7d5r",
                    "budget": 0.03,
                    "used": 0.0,
                    "available": 0.03
                },
                ...
            }
        """
        agent_info = {}
        
        env_var_map = {
            "title": "LOCUS_AGENT_TITLE_ID",
            "inspection": "LOCUS_AGENT_INSPECTION_ID",
            "appraisal": "LOCUS_AGENT_APPRAISAL_ID",
            "underwriting": "LOCUS_AGENT_UNDERWRITING_ID"
        }
        
        for agent_type in self.budgets.keys():
            agent_id = os.getenv(env_var_map.get(agent_type, ""), "")
            budget = self.budgets.get(agent_type, 0.0)
            used = self.budget_usage.get(agent_type, 0.0)
            
            agent_info[agent_type] = {
                "agent_id": agent_id,
                "budget": budget,
                "used": used,
                "available": budget - used
            }
        
        return agent_info
    
    def get_api_key(self) -> str:
        """
        Get Locus API key.
        
        Returns:
            API key string
        """
        return self.api_key


def init_locus(api_key: Optional[str] = None, wallet_address: Optional[str] = None) -> LocusIntegration:
    """
    Initialize global Locus Integration instance.
    
    Args:
        api_key: Locus API key
        wallet_address: Wallet address from wallet manager
        
    Returns:
        Initialized LocusIntegration instance
        
    Raises:
        ValueError: If API key is missing
    """
    global _locus_instance
    
    if _locus_instance is not None:
        logger.warning("Locus integration already initialized, returning existing instance")
        return _locus_instance
    
    # Support loading from env if not provided
    if not api_key:
        api_key = os.getenv("LOCUS_API_KEY") or os.getenv("locus_api_key", "")
    
    if not api_key:
        raise ValueError("Locus API key is required (LOCUS_API_KEY or locus_api_key)")
    
    if not wallet_address:
        raise ValueError("Wallet address is required")
    
    _locus_instance = LocusIntegration(
        api_key=api_key,
        wallet_address=wallet_address
    )
    
    logger.info("Locus Integration initialized successfully")
    
    return _locus_instance


def get_locus() -> Optional[LocusIntegration]:
    """
    Get global Locus Integration instance.
    
    Returns:
        LocusIntegration instance if initialized, None otherwise
    """
    return _locus_instance

