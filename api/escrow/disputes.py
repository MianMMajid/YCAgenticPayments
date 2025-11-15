"""Dispute API endpoints for escrow dispute management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from models.database import get_db
from models.verification import VerificationType
from agents.escrow_agent_orchestrator import EscrowAgentOrchestrator, EscrowError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class DisputeCreate(BaseModel):
    """Request model for raising a dispute."""
    raised_by: str = Field(..., description="ID of party raising the dispute")
    dispute_type: str = Field(..., description="Type of dispute (verification, payment, settlement, etc.)")
    description: str = Field(..., description="Description of the dispute")
    related_verification_type: Optional[VerificationType] = Field(
        None,
        description="Related verification type if applicable"
    )
    evidence: Optional[Dict[str, Any]] = Field(None, description="Evidence supporting the dispute")


class DisputeUpdate(BaseModel):
    """Request model for updating dispute status."""
    resolution: str = Field(..., description="Resolution decision (continue, cancel, retry_verification, etc.)")
    resolution_details: Dict[str, Any] = Field(..., description="Details of the resolution")
    resolved_by: str = Field(..., description="ID of party resolving the dispute")


class DisputeResponse(BaseModel):
    """Response model for dispute details."""
    dispute_id: str
    transaction_id: str
    status: str
    raised_by: str
    dispute_type: str
    description: str
    raised_at: str
    previous_state: str
    current_state: str
    audit_trail: List[Dict[str, Any]]
    related_report: Optional[Dict[str, Any]]
    resolution_options: List[str]


class DisputeListItem(BaseModel):
    """Response model for dispute list item."""
    dispute_id: str
    status: str
    raised_by: str
    dispute_type: str
    description: str
    raised_at: str
    resolved_at: Optional[str]
    resolution: Optional[str]


class DisputeListResponse(BaseModel):
    """Response model for dispute list."""
    disputes: List[DisputeListItem]
    total: int


class DisputeAuditTrailResponse(BaseModel):
    """Response model for dispute audit trail."""
    dispute: Dict[str, Any]
    transaction_id: str
    audit_trail: List[Dict[str, Any]]
    verification_reports: List[Dict[str, Any]]
    payment_history: List[Dict[str, Any]]
    transaction_state: str


@router.post("/transactions/{transaction_id}/disputes", response_model=DisputeResponse, status_code=201)
async def raise_dispute(
    transaction_id: str,
    dispute_data: DisputeCreate,
    db: Session = Depends(get_db)
):
    """
    Raise a dispute for a transaction.
    
    This endpoint:
    - Transitions transaction to DISPUTED state
    - Freezes fund releases
    - Provides access to audit trail for dispute resolution
    - Logs dispute on blockchain
    - Initiates dispute resolution workflow
    
    Requirements: 5.2, 5.3
    """
    logger.info(
        f"Raising dispute for transaction {transaction_id}",
        extra={
            "raised_by": dispute_data.raised_by,
            "dispute_type": dispute_data.dispute_type
        }
    )
    
    try:
        orchestrator = EscrowAgentOrchestrator(db)
        
        dispute = await orchestrator.handle_dispute(
            transaction_id=transaction_id,
            raised_by=dispute_data.raised_by,
            dispute_type=dispute_data.dispute_type,
            description=dispute_data.description,
            related_verification_type=dispute_data.related_verification_type,
            evidence=dispute_data.evidence
        )
        
        await orchestrator.close()
        
        return DisputeResponse(**dispute)
        
    except EscrowError as e:
        logger.error(f"Failed to raise dispute: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error raising dispute: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/transactions/{transaction_id}/disputes", response_model=DisputeListResponse)
async def list_disputes(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    List all disputes for a transaction.
    
    Requirements: 5.2, 5.3
    """
    logger.info(f"Listing disputes for transaction {transaction_id}")
    
    try:
        # Verify transaction exists
        orchestrator = EscrowAgentOrchestrator(db)
        transaction = await orchestrator.get_transaction(transaction_id)
        await orchestrator.close()
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        # Get disputes from transaction metadata
        disputes = transaction.transaction_metadata.get("disputes", []) if transaction.transaction_metadata else []
        
        return DisputeListResponse(
            disputes=[
                DisputeListItem(
                    dispute_id=dispute["dispute_id"],
                    status=dispute["status"],
                    raised_by=dispute["raised_by"],
                    dispute_type=dispute["dispute_type"],
                    description=dispute["description"],
                    raised_at=dispute["raised_at"],
                    resolved_at=dispute.get("resolved_at"),
                    resolution=dispute.get("resolution")
                )
                for dispute in disputes
            ],
            total=len(disputes)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing disputes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/disputes/{dispute_id}", status_code=204)
async def update_dispute_status(
    dispute_id: str,
    update_data: DisputeUpdate,
    transaction_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Update dispute status and resolve the dispute.
    
    This endpoint:
    - Updates dispute status to resolved
    - Transitions transaction to appropriate state based on resolution
    - Logs dispute resolution on blockchain
    - Executes resolution actions (continue, cancel, retry verification, etc.)
    
    Requirements: 5.2, 5.3
    """
    logger.info(
        f"Updating dispute {dispute_id}",
        extra={
            "resolution": update_data.resolution,
            "resolved_by": update_data.resolved_by
        }
    )
    
    try:
        # Find transaction containing this dispute
        if not transaction_id:
            # Search for transaction with this dispute
            from models.transaction import Transaction
            transactions = db.query(Transaction).all()
            
            transaction = None
            for t in transactions:
                if t.transaction_metadata and "disputes" in t.transaction_metadata:
                    for dispute in t.transaction_metadata["disputes"]:
                        if dispute["dispute_id"] == dispute_id:
                            transaction = t
                            break
                if transaction:
                    break
            
            if not transaction:
                raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")
            
            transaction_id = transaction.id
        
        orchestrator = EscrowAgentOrchestrator(db)
        
        await orchestrator.resolve_dispute(
            transaction_id=transaction_id,
            dispute_id=dispute_id,
            resolution=update_data.resolution,
            resolution_details=update_data.resolution_details,
            resolved_by=update_data.resolved_by
        )
        
        await orchestrator.close()
        
        return None
        
    except HTTPException:
        raise
    except EscrowError as e:
        logger.error(f"Failed to update dispute: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating dispute: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/disputes/{dispute_id}/audit-trail", response_model=DisputeAuditTrailResponse)
async def get_dispute_audit_trail(
    dispute_id: str,
    transaction_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive audit trail for a specific dispute.
    
    This endpoint provides all information needed for dispute resolution:
    - Complete blockchain audit trail
    - All verification reports
    - Payment history
    - Transaction state
    
    Requirements: 5.2, 5.3
    """
    logger.info(f"Retrieving audit trail for dispute {dispute_id}")
    
    try:
        # Find transaction containing this dispute
        if not transaction_id:
            # Search for transaction with this dispute
            from models.transaction import Transaction
            transactions = db.query(Transaction).all()
            
            transaction = None
            for t in transactions:
                if t.transaction_metadata and "disputes" in t.transaction_metadata:
                    for dispute in t.transaction_metadata["disputes"]:
                        if dispute["dispute_id"] == dispute_id:
                            transaction = t
                            break
                if transaction:
                    break
            
            if not transaction:
                raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found")
            
            transaction_id = transaction.id
        
        orchestrator = EscrowAgentOrchestrator(db)
        
        audit_trail_data = await orchestrator.get_dispute_audit_trail(
            transaction_id=transaction_id,
            dispute_id=dispute_id
        )
        
        await orchestrator.close()
        
        return DisputeAuditTrailResponse(**audit_trail_data)
        
    except HTTPException:
        raise
    except EscrowError as e:
        logger.error(f"Failed to get dispute audit trail: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting dispute audit trail: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
