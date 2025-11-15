"""Audit trail API endpoints for blockchain event logging and verification."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from models.database import get_db
from models.settlement import BlockchainEvent
from agents.escrow_agent_orchestrator import EscrowAgentOrchestrator
from services.blockchain_logger import BlockchainLogger, EventType
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class AuditTrailEntry(BaseModel):
    """Response model for audit trail entry."""
    transaction_hash: str
    block_number: Optional[str]
    event_type: str
    event_data: dict
    timestamp: str
    verified: bool


class AuditTrailResponse(BaseModel):
    """Response model for audit trail."""
    transaction_id: str
    entries: List[AuditTrailEntry]
    total: int
    limit: int
    offset: int


class BlockchainEventResponse(BaseModel):
    """Response model for blockchain event."""
    id: str
    transaction_id: str
    event_type: str
    event_data: dict
    blockchain_tx_hash: str
    block_number: Optional[str]
    timestamp: str
    created_at: str

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Response model for event list."""
    events: List[BlockchainEventResponse]
    total: int


class EventVerificationResponse(BaseModel):
    """Response model for event verification."""
    transaction_hash: str
    verified: bool
    message: str


@router.get("/transactions/{transaction_id}/audit-trail", response_model=AuditTrailResponse)
async def get_audit_trail(
    transaction_id: str,
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    start_time: Optional[datetime] = Query(None, description="Filter events after this time"),
    end_time: Optional[datetime] = Query(None, description="Filter events before this time"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of entries"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    include_verification: bool = Query(False, description="Verify each event's authenticity"),
    db: Session = Depends(get_db)
):
    """
    Get blockchain audit trail for a transaction.
    
    This endpoint retrieves the complete audit trail from the blockchain
    with optional filtering by event type and time range. Each entry
    includes the blockchain transaction hash, block number, event data,
    and verification status.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    logger.info(
        f"Retrieving audit trail for transaction {transaction_id}",
        extra={
            "event_type": event_type.value if event_type else None,
            "limit": limit,
            "offset": offset,
            "include_verification": include_verification
        }
    )
    
    try:
        # Verify transaction exists
        orchestrator = EscrowAgentOrchestrator(db)
        transaction = await orchestrator.get_transaction(transaction_id)
        await orchestrator.close()
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        # Get audit trail from blockchain
        blockchain_logger = BlockchainLogger()
        
        entries = await blockchain_logger.get_audit_trail(
            transaction_id=transaction_id,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
            include_verification=include_verification
        )
        
        await blockchain_logger.close()
        
        return AuditTrailResponse(
            transaction_id=transaction_id,
            entries=[
                AuditTrailEntry(
                    transaction_hash=entry["transaction_hash"],
                    block_number=entry.get("block_number"),
                    event_type=entry["event_type"],
                    event_data=entry["event_data"],
                    timestamp=entry["timestamp"],
                    verified=entry["verified"]
                )
                for entry in entries
            ],
            total=len(entries),
            limit=limit,
            offset=offset
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving audit trail: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/transactions/{transaction_id}/events", response_model=EventListResponse)
async def get_transaction_events(
    transaction_id: str,
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    db: Session = Depends(get_db)
):
    """
    Get transaction events from database.
    
    This endpoint retrieves blockchain events stored in the database
    for a specific transaction. Unlike the audit trail endpoint which
    queries the blockchain directly, this endpoint is faster but only
    returns events that have been logged to the database.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    logger.info(
        f"Retrieving events for transaction {transaction_id}",
        extra={"event_type": event_type.value if event_type else None}
    )
    
    try:
        # Verify transaction exists
        orchestrator = EscrowAgentOrchestrator(db)
        transaction = await orchestrator.get_transaction(transaction_id)
        await orchestrator.close()
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        # Get events from database
        blockchain_logger = BlockchainLogger()
        
        events = await blockchain_logger.get_transaction_events(
            transaction_id=transaction_id,
            db=db,
            event_type=event_type
        )
        
        await blockchain_logger.close()
        
        return EventListResponse(
            events=[
                BlockchainEventResponse(
                    id=event.id,
                    transaction_id=event.transaction_id,
                    event_type=event.event_type,
                    event_data=event.event_data or {},
                    blockchain_tx_hash=event.blockchain_tx_hash,
                    block_number=event.block_number,
                    timestamp=event.timestamp.isoformat(),
                    created_at=event.created_at.isoformat()
                )
                for event in events
            ],
            total=len(events)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving events: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/events/{transaction_hash}/verify", response_model=EventVerificationResponse)
async def verify_blockchain_event(
    transaction_hash: str,
    db: Session = Depends(get_db)
):
    """
    Verify the authenticity of a blockchain event.
    
    This endpoint verifies that a blockchain event with the given
    transaction hash exists on the blockchain and has not been tampered with.
    This is useful for dispute resolution and audit purposes.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    logger.info(f"Verifying blockchain event: {transaction_hash}")
    
    try:
        blockchain_logger = BlockchainLogger()
        
        verified = await blockchain_logger.verify_event(transaction_hash)
        
        await blockchain_logger.close()
        
        return EventVerificationResponse(
            transaction_hash=transaction_hash,
            verified=verified,
            message="Event verified successfully" if verified else "Event verification failed"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error verifying event: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
