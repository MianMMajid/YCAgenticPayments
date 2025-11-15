"""Blockchain client for immutable audit trail logging."""
import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config.settings import settings
from services.circuit_breaker import blockchain_circuit_breaker


logger = logging.getLogger(__name__)


@dataclass
class BlockchainEventLog:
    """Blockchain event log result."""
    transaction_hash: str
    block_number: Optional[str]
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime
    status: str


@dataclass
class AuditTrailEntry:
    """Audit trail entry."""
    transaction_hash: str
    block_number: Optional[str]
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime
    verified: bool


class BlockchainError(Exception):
    """Base exception for blockchain errors."""
    pass


class BlockchainConnectionError(BlockchainError):
    """Blockchain connection error."""
    pass


class BlockchainTransactionError(BlockchainError):
    """Blockchain transaction error."""
    pass


class BlockchainVerificationError(BlockchainError):
    """Blockchain verification error."""
    pass


class BlockchainClient:
    """Client for interacting with blockchain for audit trail logging."""
    
    def __init__(
        self,
        rpc_url: Optional[str] = None,
        network: Optional[str] = None,
        contract_address: Optional[str] = None,
        private_key: Optional[str] = None
    ):
        """Initialize blockchain client.
        
        Args:
            rpc_url: Blockchain RPC endpoint URL (defaults to settings)
            network: Network name (mainnet/testnet, defaults to settings)
            contract_address: Smart contract address for logging (defaults to settings)
            private_key: Private key for transaction signing (defaults to settings)
        """
        self.rpc_url = rpc_url or settings.blockchain_rpc_url
        self.network = network or settings.blockchain_network
        self.contract_address = contract_address or settings.blockchain_contract_address
        self.private_key = private_key or settings.blockchain_private_key
        
        if not self.rpc_url:
            raise BlockchainConnectionError("Blockchain RPC URL not configured")
        
        if not self.contract_address:
            raise BlockchainConnectionError("Blockchain contract address not configured")
        
        if not self.private_key:
            raise BlockchainConnectionError("Blockchain private key not configured")
        
        self.client = httpx.AsyncClient(
            base_url=self.rpc_url,
            headers={
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def _sign_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Sign transaction data with private key.
        
        Args:
            transaction_data: Transaction data to sign
        
        Returns:
            Signature string
        """
        # Create deterministic hash of transaction data
        data_string = json.dumps(transaction_data, sort_keys=True)
        data_hash = hashlib.sha256(data_string.encode()).hexdigest()
        
        # In production, use proper cryptographic signing (e.g., ECDSA)
        # For now, create a simple signature combining hash with private key hash
        key_hash = hashlib.sha256(self.private_key.encode()).hexdigest()
        signature = hashlib.sha256(f"{data_hash}{key_hash}".encode()).hexdigest()
        
        return signature
    
    @blockchain_circuit_breaker
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=32),
        retry=retry_if_exception_type((httpx.HTTPError, BlockchainError)),
        reraise=True
    )
    async def log_event(
        self,
        transaction_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> BlockchainEventLog:
        """Log an event to the blockchain.
        
        Args:
            transaction_id: Transaction identifier
            event_type: Type of event being logged
            event_data: Event data to log
            timestamp: Event timestamp (defaults to current time)
        
        Returns:
            BlockchainEventLog with transaction details
        
        Raises:
            BlockchainTransactionError: If event logging fails
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            logger.info(f"Logging blockchain event: {event_type} for transaction {transaction_id}")
            
            # Prepare transaction payload
            payload = {
                "transaction_id": transaction_id,
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": timestamp.isoformat(),
                "contract_address": self.contract_address,
                "network": self.network
            }
            
            # Sign the transaction
            signature = self._sign_transaction(payload)
            payload["signature"] = signature
            
            # Send to blockchain RPC
            response = await self.client.post(
                "/log_event",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            result = BlockchainEventLog(
                transaction_hash=data["transaction_hash"],
                block_number=data.get("block_number"),
                event_type=event_type,
                event_data=event_data,
                timestamp=timestamp,
                status=data.get("status", "pending")
            )
            
            logger.info(f"Event logged to blockchain: {result.transaction_hash}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error logging event: {e.response.status_code} - {e.response.text}")
            raise BlockchainTransactionError(f"Failed to log event: {e.response.text}")
        except httpx.HTTPError as e:
            logger.error(f"Network error logging event: {str(e)}")
            raise BlockchainTransactionError(f"Network error logging event: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error logging event: {str(e)}")
            raise BlockchainTransactionError(f"Unexpected error: {str(e)}")
    
    @blockchain_circuit_breaker
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=32),
        retry=retry_if_exception_type((httpx.HTTPError, BlockchainError)),
        reraise=True
    )
    async def get_audit_trail(
        self,
        transaction_id: str,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditTrailEntry]:
        """Retrieve audit trail for a transaction.
        
        Args:
            transaction_id: Transaction identifier
            event_type: Filter by event type (optional)
            start_time: Filter events after this time (optional)
            end_time: Filter events before this time (optional)
            limit: Maximum number of entries to return
            offset: Offset for pagination
        
        Returns:
            List of audit trail entries
        
        Raises:
            BlockchainError: If audit trail retrieval fails
        """
        try:
            logger.info(f"Retrieving audit trail for transaction {transaction_id}")
            
            params = {
                "transaction_id": transaction_id,
                "contract_address": self.contract_address,
                "limit": limit,
                "offset": offset
            }
            
            if event_type:
                params["event_type"] = event_type
            if start_time:
                params["start_time"] = start_time.isoformat()
            if end_time:
                params["end_time"] = end_time.isoformat()
            
            response = await self.client.get(
                "/audit_trail",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            entries = [
                AuditTrailEntry(
                    transaction_hash=entry["transaction_hash"],
                    block_number=entry.get("block_number"),
                    event_type=entry["event_type"],
                    event_data=entry["event_data"],
                    timestamp=datetime.fromisoformat(entry["timestamp"]),
                    verified=entry.get("verified", False)
                )
                for entry in data["entries"]
            ]
            
            logger.info(f"Retrieved {len(entries)} audit trail entries for transaction {transaction_id}")
            return entries
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error retrieving audit trail: {e.response.status_code} - {e.response.text}")
            raise BlockchainError(f"Failed to retrieve audit trail: {e.response.text}")
        except httpx.HTTPError as e:
            logger.error(f"Network error retrieving audit trail: {str(e)}")
            raise BlockchainError(f"Network error retrieving audit trail: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving audit trail: {str(e)}")
            raise BlockchainError(f"Unexpected error: {str(e)}")
    
    @blockchain_circuit_breaker
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=32),
        retry=retry_if_exception_type((httpx.HTTPError, BlockchainError)),
        reraise=True
    )
    async def verify_event(
        self,
        transaction_hash: str
    ) -> bool:
        """Verify the authenticity of a blockchain event.
        
        Args:
            transaction_hash: Transaction hash to verify
        
        Returns:
            True if event is verified, False otherwise
        
        Raises:
            BlockchainVerificationError: If verification fails
        """
        try:
            logger.info(f"Verifying blockchain event: {transaction_hash}")
            
            params = {
                "transaction_hash": transaction_hash,
                "contract_address": self.contract_address
            }
            
            response = await self.client.get(
                "/verify_event",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            verified = data.get("verified", False)
            
            logger.info(f"Event {transaction_hash} verification result: {verified}")
            return verified
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error verifying event: {e.response.status_code} - {e.response.text}")
            raise BlockchainVerificationError(f"Failed to verify event: {e.response.text}")
        except httpx.HTTPError as e:
            logger.error(f"Network error verifying event: {str(e)}")
            raise BlockchainVerificationError(f"Network error verifying event: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error verifying event: {str(e)}")
            raise BlockchainVerificationError(f"Unexpected error: {str(e)}")
    
    @blockchain_circuit_breaker
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.HTTPError, BlockchainError)),
        reraise=True
    )
    async def get_block_number(self) -> Optional[str]:
        """Get the current block number.
        
        Returns:
            Current block number or None if unavailable
        
        Raises:
            BlockchainError: If block number retrieval fails
        """
        try:
            logger.info("Retrieving current block number")
            
            response = await self.client.get("/block_number")
            response.raise_for_status()
            
            data = response.json()
            block_number = data.get("block_number")
            
            logger.info(f"Current block number: {block_number}")
            return block_number
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error retrieving block number: {e.response.status_code} - {e.response.text}")
            raise BlockchainError(f"Failed to retrieve block number: {e.response.text}")
        except httpx.HTTPError as e:
            logger.error(f"Network error retrieving block number: {str(e)}")
            raise BlockchainError(f"Network error retrieving block number: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving block number: {str(e)}")
            raise BlockchainError(f"Unexpected error: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if blockchain connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            response = await self.client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Blockchain health check failed: {str(e)}")
            return False
