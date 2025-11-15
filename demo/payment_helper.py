"""
Payment Helper for Demo

Generates payment signatures and transaction hashes for x402 payment services.
In production, this would use actual blockchain signing.
"""
import hashlib
import time
from decimal import Decimal
from typing import Dict, Any


def generate_payment_signature(
    service_endpoint: str,
    amount: Decimal,
    property_id: str,
    transaction_id: str
) -> Dict[str, Any]:
    """
    Generate a payment signature and transaction hash for demo purposes.
    
    In production, this would:
    1. Create a blockchain transaction
    2. Sign it with the wallet's private key
    3. Return the signed transaction hash
    
    Args:
        service_endpoint: The service endpoint being paid for
        amount: Payment amount
        property_id: Property identifier
        transaction_id: Transaction identifier
        
    Returns:
        Dict with payment_signature and payment_tx_hash
    """
    # Create a deterministic hash for demo purposes
    # In production, this would be a real blockchain transaction
    timestamp = int(time.time())
    data = f"{service_endpoint}:{amount}:{property_id}:{transaction_id}:{timestamp}"
    
    # Generate a mock transaction hash
    tx_hash = hashlib.sha256(data.encode()).hexdigest()
    
    # Generate a mock signature
    signature_data = f"{tx_hash}:{timestamp}:signed"
    signature = hashlib.sha256(signature_data.encode()).hexdigest()
    
    return {
        "payment_signature": signature,
        "payment_tx_hash": f"0x{tx_hash[:40]}",  # Ethereum-style hash
        "amount": str(amount),
        "timestamp": timestamp
    }


def verify_payment_signature(
    signature: str,
    tx_hash: str,
    service_endpoint: str,
    amount: Decimal
) -> bool:
    """
    Verify a payment signature (for demo purposes).
    
    In production, this would verify a blockchain transaction.
    
    Args:
        signature: Payment signature
        tx_hash: Transaction hash
        service_endpoint: Service endpoint
        amount: Payment amount
        
    Returns:
        True if signature is valid
    """
    # For demo, accept any non-empty signature
    return bool(signature and tx_hash and len(signature) > 0 and len(tx_hash) > 0)

