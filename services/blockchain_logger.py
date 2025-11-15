"""Blockchain logger service for audit trail management."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from sqlalchemy.orm import Session

from services.blockchain_client import (
    BlockchainClient,
    BlockchainError,
    BlockchainEventLog,
    AuditTrailEntry
)
from models.settlement import BlockchainEvent
from models.database import get_db


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types for blockchain logging."""
    TRANSACTION_INITIATED = "transaction_initiated"
    EARNEST_MONEY_DEPOSITED = "earnest_money_deposited"
    VERIFICATION_TASK_ASSIGNED = "verification_task_assigned"
    VERIFICATION_COMPLETED = "verification_completed"
    PAYMENT_RELEASED = "payment_released"
    SETTLEMENT_EXECUTED = "settlement_executed"
    DISPUTE_RAISED = "dispute_raised"
    DISPUTE_RESOLVED = "dispute_resolved"
    TRANSACTION_CANCELLED = "transaction_cancelled"


class BlockchainLogger:
    """Logger service for blockchain audit trail management."""
    
    def __init__(
        self,
        blockchain_client: Optional[BlockchainClient] = None
    ):
        """Initialize blockchain logger.
        
        Args:
            blockchain_client: BlockchainClient instance (creates new if not provided)
        """
        self.blockchain_client = blockchain_client or BlockchainClient()
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self._is_processing = False
    
    async def start_processing(self):
        """Start async event processing."""
        if self._is_processing:
            logger.warning("Event processing already started")
            return
        
        self._is_processing = True
        self._processing_task = asyncio.create_task(self._process_event_queue())
        logger.info("Blockchain event processing started")
    
    async def stop_processing(self):
        """Stop async event processing."""
        if not self._is_processing:
            return
        
        self._is_processing = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Blockchain event processing stopped")
    
    async def _process_event_queue(self):
        """Process events from the queue asynchronously."""
        while self._is_processing:
            try:
                # Get event from queue with timeout
                try:
                    event_data = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the event
                transaction_id = event_data["transaction_id"]
                event_type = event_data["event_type"]
                event_payload = event_data["event_payload"]
                timestamp = event_data["timestamp"]
                db = event_data["db"]
                
                try:
                    # Log to blockchain
                    result = await self.blockchain_client.log_event(
                        transaction_id=transaction_id,
                        event_type=event_type,
                        event_data=event_payload,
                        timestamp=timestamp
                    )
                    
                    # Store in database
                    blockchain_event = BlockchainEvent(
                        transaction_id=transaction_id,
                        event_type=event_type,
                        event_data=event_payload,
                        blockchain_tx_hash=result.transaction_hash,
                        block_number=result.block_number,
                        timestamp=timestamp
                    )
                    
                    db.add(blockchain_event)
                    db.commit()
                    
                    logger.info(f"Event processed: {event_type} for transaction {transaction_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing event: {str(e)}")
                    db.rollback()
                
                finally:
                    self._event_queue.task_done()
                    
            except Exception as e:
                logger.error(f"Error in event processing loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def log_transaction_event(
        self,
        transaction_id: str,
        event_type: EventType,
        event_data: Dict[str, Any],
        db: Session,
        async_processing: bool = True,
        timestamp: Optional[datetime] = None
    ) -> Optional[BlockchainEvent]:
        """Log a transaction event to the blockchain.
        
        Args:
            transaction_id: Transaction identifier
            event_type: Type of event
            event_data: Event data to log
            db: Database session
            async_processing: If True, queue for async processing; if False, process immediately
            timestamp: Event timestamp (defaults to current time)
        
        Returns:
            BlockchainEvent if processed immediately, None if queued for async processing
        
        Raises:
            BlockchainError: If immediate processing fails
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        logger.info(f"Logging event: {event_type.value} for transaction {transaction_id}")
        
        if async_processing and self._is_processing:
            # Queue for async processing
            await self._event_queue.put({
                "transaction_id": transaction_id,
                "event_type": event_type.value,
                "event_payload": event_data,
                "timestamp": timestamp,
                "db": db
            })
            logger.debug(f"Event queued for async processing: {event_type.value}")
            return None
        else:
            # Process immediately
            try:
                result = await self.blockchain_client.log_event(
                    transaction_id=transaction_id,
                    event_type=event_type.value,
                    event_data=event_data,
                    timestamp=timestamp
                )
                
                # Store in database
                blockchain_event = BlockchainEvent(
                    transaction_id=transaction_id,
                    event_type=event_type.value,
                    event_data=event_data,
                    blockchain_tx_hash=result.transaction_hash,
                    block_number=result.block_number,
                    timestamp=timestamp
                )
                
                db.add(blockchain_event)
                db.commit()
                db.refresh(blockchain_event)
                
                logger.info(f"Event logged immediately: {event_type.value} - {result.transaction_hash}")
                return blockchain_event
                
            except Exception as e:
                logger.error(f"Error logging event immediately: {str(e)}")
                db.rollback()
                raise
    
    async def get_audit_trail(
        self,
        transaction_id: str,
        event_type: Optional[EventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        include_verification: bool = False
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a transaction with filtering and pagination.
        
        Args:
            transaction_id: Transaction identifier
            event_type: Filter by event type (optional)
            start_time: Filter events after this time (optional)
            end_time: Filter events before this time (optional)
            limit: Maximum number of entries to return
            offset: Offset for pagination
            include_verification: If True, verify each event's authenticity
        
        Returns:
            List of audit trail entries with event details
        
        Raises:
            BlockchainError: If audit trail retrieval fails
        """
        logger.info(f"Retrieving audit trail for transaction {transaction_id}")
        
        try:
            # Get audit trail from blockchain
            entries = await self.blockchain_client.get_audit_trail(
                transaction_id=transaction_id,
                event_type=event_type.value if event_type else None,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                offset=offset
            )
            
            # Format entries
            audit_trail = []
            for entry in entries:
                trail_entry = {
                    "transaction_hash": entry.transaction_hash,
                    "block_number": entry.block_number,
                    "event_type": entry.event_type,
                    "event_data": entry.event_data,
                    "timestamp": entry.timestamp.isoformat(),
                    "verified": entry.verified
                }
                
                # Optionally verify each event
                if include_verification and not entry.verified:
                    try:
                        verified = await self.blockchain_client.verify_event(
                            entry.transaction_hash
                        )
                        trail_entry["verified"] = verified
                    except Exception as e:
                        logger.warning(f"Failed to verify event {entry.transaction_hash}: {str(e)}")
                        trail_entry["verified"] = False
                
                audit_trail.append(trail_entry)
            
            logger.info(f"Retrieved {len(audit_trail)} audit trail entries")
            return audit_trail
            
        except Exception as e:
            logger.error(f"Error retrieving audit trail: {str(e)}")
            raise
    
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
            BlockchainError: If verification fails
        """
        logger.info(f"Verifying event: {transaction_hash}")
        
        try:
            verified = await self.blockchain_client.verify_event(transaction_hash)
            logger.info(f"Event {transaction_hash} verification: {verified}")
            return verified
        except Exception as e:
            logger.error(f"Error verifying event: {str(e)}")
            raise
    
    async def get_transaction_events(
        self,
        transaction_id: str,
        db: Session,
        event_type: Optional[EventType] = None
    ) -> List[BlockchainEvent]:
        """Get blockchain events for a transaction from database.
        
        Args:
            transaction_id: Transaction identifier
            db: Database session
            event_type: Filter by event type (optional)
        
        Returns:
            List of BlockchainEvent records
        """
        logger.info(f"Retrieving database events for transaction {transaction_id}")
        
        query = db.query(BlockchainEvent).filter(
            BlockchainEvent.transaction_id == transaction_id
        )
        
        if event_type:
            query = query.filter(BlockchainEvent.event_type == event_type.value)
        
        events = query.order_by(BlockchainEvent.timestamp.asc()).all()
        
        logger.info(f"Retrieved {len(events)} events from database")
        return events
    
    async def close(self):
        """Close the blockchain logger and cleanup resources."""
        await self.stop_processing()
        await self.blockchain_client.close()
        logger.info("Blockchain logger closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_processing()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
