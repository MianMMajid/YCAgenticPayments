"""Locus Wallet Manager for Counter AI."""
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global singleton instance
_wallet_manager_instance: Optional['LocusWalletManager'] = None


class LocusWalletManager:
    """
    Manages blockchain wallet for Locus payments.
    
    Handles wallet initialization, validation, and information retrieval
    for the Locus payment infrastructure on Base Mainnet (Chain 8453).
    """
    
    def __init__(
        self,
        wallet_address: str,
        private_key: str,
        chain_id: int = 8453,
        wallet_name: str = "Yc-MakeEmPay"
    ):
        """
        Initialize Locus Wallet Manager.
        
        Args:
            wallet_address: Wallet address (0x format)
            private_key: Private key (0x format)
            chain_id: Blockchain chain ID (default: 8453 for Base Mainnet)
            wallet_name: Human-readable wallet name
        """
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.chain_id = chain_id
        self.wallet_name = wallet_name
        
        logger.info(
            f"Initializing Locus Wallet Manager: {wallet_name}",
            extra={
                "wallet_address": wallet_address[:10] + "...",
                "chain_id": chain_id
            }
        )
    
    def get_wallet_info(self) -> Dict[str, Any]:
        """
        Get wallet information.
        
        Returns:
            Dictionary containing wallet details:
            {
                "name": "Yc-MakeEmPay",
                "address": "0x45B876...",
                "chain_id": 8453,
                "network": "Base Mainnet",
                "status": "Active"
            }
        """
        network_map = {
            8453: "Base Mainnet",
            84531: "Base Sepolia Testnet",
            1: "Ethereum Mainnet"
        }
        
        network = network_map.get(self.chain_id, f"Chain {self.chain_id}")
        
        return {
            "name": self.wallet_name,
            "address": self.wallet_address,
            "chain_id": self.chain_id,
            "network": network,
            "status": "Active" if self.validate_wallet() else "Invalid"
        }
    
    def validate_wallet(self) -> bool:
        """
        Validate wallet address and private key format.
        
        Checks:
        - Address format: 0x + 40 hex characters
        - Private key format: 0x + 64 hex characters
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate address format
            if not self.wallet_address.startswith("0x"):
                logger.error("Wallet address must start with 0x")
                return False
            
            address_hex = self.wallet_address[2:]
            if len(address_hex) != 40:
                logger.error(f"Wallet address must be 42 characters (0x + 40 hex), got {len(self.wallet_address)}")
                return False
            
            try:
                int(address_hex, 16)
            except ValueError:
                logger.error("Wallet address contains invalid hex characters")
                return False
            
            # Validate private key format
            if not self.private_key.startswith("0x"):
                logger.error("Private key must start with 0x")
                return False
            
            key_hex = self.private_key[2:]
            if len(key_hex) != 64:
                logger.error(f"Private key must be 66 characters (0x + 64 hex), got {len(self.private_key)}")
                return False
            
            try:
                int(key_hex, 16)
            except ValueError:
                logger.error("Private key contains invalid hex characters")
                return False
            
            logger.debug("Wallet validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Wallet validation error: {str(e)}")
            return False
    
    def get_address(self) -> str:
        """
        Get wallet address.
        
        Returns:
            Wallet address string
        """
        return self.wallet_address
    
    def get_private_key(self) -> str:
        """
        Get private key (for signing transactions).
        
        Returns:
            Private key string
        """
        return self.private_key
    
    def get_chain_id(self) -> int:
        """
        Get chain ID.
        
        Returns:
            Chain ID integer
        """
        return self.chain_id


def init_wallet_manager() -> LocusWalletManager:
    """
    Initialize global Locus Wallet Manager instance.
    
    Loads configuration from environment variables:
    - LOCUS_WALLET_ADDRESS
    - LOCUS_WALLET_PRIVATE_KEY
    - LOCUS_CHAIN_ID (defaults to 8453)
    
    Returns:
        Initialized LocusWalletManager instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    global _wallet_manager_instance
    
    if _wallet_manager_instance is not None:
        logger.warning("Wallet manager already initialized, returning existing instance")
        return _wallet_manager_instance
    
    # Support both uppercase and lowercase env var formats
    wallet_address = os.getenv("LOCUS_WALLET_ADDRESS") or os.getenv("locus_wallet_address")
    private_key = os.getenv("LOCUS_WALLET_PRIVATE_KEY") or os.getenv("locus_wallet_private_key")
    chain_id = int(os.getenv("LOCUS_CHAIN_ID", os.getenv("locus_chain_id", "8453")))
    wallet_name = os.getenv("LOCUS_WALLET_NAME", os.getenv("locus_wallet_name", "Yc-MakeEmPay"))
    
    if not wallet_address:
        raise ValueError("LOCUS_WALLET_ADDRESS environment variable is required")
    
    if not private_key:
        raise ValueError("LOCUS_WALLET_PRIVATE_KEY environment variable is required")
    
    _wallet_manager_instance = LocusWalletManager(
        wallet_address=wallet_address,
        private_key=private_key,
        chain_id=chain_id,
        wallet_name=wallet_name
    )
    
    # Validate on initialization
    if not _wallet_manager_instance.validate_wallet():
        raise ValueError("Invalid wallet address or private key format")
    
    logger.info(f"Locus Wallet Manager initialized: {wallet_name}")
    
    return _wallet_manager_instance


def get_wallet_manager() -> Optional[LocusWalletManager]:
    """
    Get global Locus Wallet Manager instance.
    
    Returns:
        LocusWalletManager instance if initialized, None otherwise
    """
    return _wallet_manager_instance

