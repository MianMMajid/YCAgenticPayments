"""Transaction management API endpoints for escrow transactions."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from models.database import get_db
from models.transaction import Transaction, TransactionState
from agents.escrow_agent_orchestrator import EscrowAgentOrchestrator, EscrowError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class TransactionCreate(BaseModel):
    """Request model for creating a transaction."""
    buyer_agent_id: str = Field(..., description="ID of the buyer's agent")
    seller_agent_id: str = Field(..., description="ID of the seller's agent")
    property_id: str = Field(..., description="ID of the property")
    earnest_money: Decimal = Field(..., description="Earnest money deposit amount", gt=0)
    total_purchase_price: Decimal = Field(..., description="Total purchase price", gt=0)
    target_closing_date: datetime = Field(..., description="Target closing date")
    metadata: Optional[dict] = Field(None, description="Additional transaction metadata")


class TransactionUpdate(BaseModel):
    """Request model for updating a transaction."""
    target_closing_date: Optional[datetime] = None
    metadata: Optional[dict] = None


class TransactionResponse(BaseModel):
    """Response model for transaction details."""
    id: str
    buyer_agent_id: str
    seller_agent_id: str
    property_id: str
    earnest_money: str
    total_purchase_price: str
    state: str
    wallet_id: Optional[str]
    initiated_at: str
    target_closing_date: str
    actual_closing_date: Optional[str]
    metadata: Optional[dict]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Response model for transaction list."""
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Initiate a new escrow transaction.
    
    This endpoint:
    - Creates a new transaction record
    - Creates a smart contract wallet
    - Deposits earnest money into the wallet
    - Logs transaction initiation on blockchain
    - Transitions transaction to FUNDED state
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    logger.info(
        f"Creating transaction for property {transaction_data.property_id}",
        extra={
            "buyer_agent_id": transaction_data.buyer_agent_id,
            "seller_agent_id": transaction_data.seller_agent_id
        }
    )
    
    try:
        orchestrator = EscrowAgentOrchestrator(db)
        
        transaction = await orchestrator.initiate_transaction(
            buyer_agent_id=transaction_data.buyer_agent_id,
            seller_agent_id=transaction_data.seller_agent_id,
            property_id=transaction_data.property_id,
            earnest_money=transaction_data.earnest_money,
            total_purchase_price=transaction_data.total_purchase_price,
            target_closing_date=transaction_data.target_closing_date,
            transaction_metadata=transaction_data.metadata
        )
        
        await orchestrator.close()
        
        return TransactionResponse(
            id=transaction.id,
            buyer_agent_id=transaction.buyer_agent_id,
            seller_agent_id=transaction.seller_agent_id,
            property_id=transaction.property_id,
            earnest_money=str(transaction.earnest_money),
            total_purchase_price=str(transaction.total_purchase_price),
            state=transaction.state.value,
            wallet_id=transaction.wallet_id,
            initiated_at=transaction.initiated_at.isoformat(),
            target_closing_date=transaction.target_closing_date.isoformat(),
            actual_closing_date=transaction.actual_closing_date.isoformat() if transaction.actual_closing_date else None,
            metadata=transaction.transaction_metadata,
            created_at=transaction.created_at.isoformat(),
            updated_at=transaction.updated_at.isoformat()
        )
        
    except EscrowError as e:
        logger.error(f"Failed to create transaction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Get transaction details by ID.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    logger.info(f"Fetching transaction {transaction_id}")
    
    try:
        orchestrator = EscrowAgentOrchestrator(db)
        transaction = await orchestrator.get_transaction(transaction_id)
        await orchestrator.close()
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        return TransactionResponse(
            id=transaction.id,
            buyer_agent_id=transaction.buyer_agent_id,
            seller_agent_id=transaction.seller_agent_id,
            property_id=transaction.property_id,
            earnest_money=str(transaction.earnest_money),
            total_purchase_price=str(transaction.total_purchase_price),
            state=transaction.state.value,
            wallet_id=transaction.wallet_id,
            initiated_at=transaction.initiated_at.isoformat(),
            target_closing_date=transaction.target_closing_date.isoformat(),
            actual_closing_date=transaction.actual_closing_date.isoformat() if transaction.actual_closing_date else None,
            metadata=transaction.transaction_metadata,
            created_at=transaction.created_at.isoformat(),
            updated_at=transaction.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    buyer_agent_id: Optional[str] = Query(None, description="Filter by buyer agent ID"),
    seller_agent_id: Optional[str] = Query(None, description="Filter by seller agent ID"),
    property_id: Optional[str] = Query(None, description="Filter by property ID"),
    state: Optional[TransactionState] = Query(None, description="Filter by transaction state"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    List transactions with optional filtering and pagination.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    logger.info(
        f"Listing transactions",
        extra={
            "buyer_agent_id": buyer_agent_id,
            "seller_agent_id": seller_agent_id,
            "property_id": property_id,
            "state": state.value if state else None,
            "page": page,
            "page_size": page_size
        }
    )
    
    try:
        # Build query with filters
        query = db.query(Transaction)
        
        if buyer_agent_id:
            query = query.filter(Transaction.buyer_agent_id == buyer_agent_id)
        if seller_agent_id:
            query = query.filter(Transaction.seller_agent_id == seller_agent_id)
        if property_id:
            query = query.filter(Transaction.property_id == property_id)
        if state:
            query = query.filter(Transaction.state == state)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(page_size).all()
        
        return TransactionListResponse(
            transactions=[
                TransactionResponse(
                    id=t.id,
                    buyer_agent_id=t.buyer_agent_id,
                    seller_agent_id=t.seller_agent_id,
                    property_id=t.property_id,
                    earnest_money=str(t.earnest_money),
                    total_purchase_price=str(t.total_purchase_price),
                    state=t.state.value,
                    wallet_id=t.wallet_id,
                    initiated_at=t.initiated_at.isoformat(),
                    target_closing_date=t.target_closing_date.isoformat(),
                    actual_closing_date=t.actual_closing_date.isoformat() if t.actual_closing_date else None,
                    metadata=t.transaction_metadata,
                    created_at=t.created_at.isoformat(),
                    updated_at=t.updated_at.isoformat()
                )
                for t in transactions
            ],
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Unexpected error listing transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    update_data: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update transaction details.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    logger.info(f"Updating transaction {transaction_id}")
    
    try:
        orchestrator = EscrowAgentOrchestrator(db)
        transaction = await orchestrator.get_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        # Update fields
        if update_data.target_closing_date is not None:
            transaction.target_closing_date = update_data.target_closing_date
        
        if update_data.metadata is not None:
            if transaction.transaction_metadata is None:
                transaction.transaction_metadata = {}
            transaction.transaction_metadata.update(update_data.metadata)
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        await orchestrator.close()
        
        return TransactionResponse(
            id=transaction.id,
            buyer_agent_id=transaction.buyer_agent_id,
            seller_agent_id=transaction.seller_agent_id,
            property_id=transaction.property_id,
            earnest_money=str(transaction.earnest_money),
            total_purchase_price=str(transaction.total_purchase_price),
            state=transaction.state.value,
            wallet_id=transaction.wallet_id,
            initiated_at=transaction.initiated_at.isoformat(),
            target_closing_date=transaction.target_closing_date.isoformat(),
            actual_closing_date=transaction.actual_closing_date.isoformat() if transaction.actual_closing_date else None,
            metadata=transaction.transaction_metadata,
            created_at=transaction.created_at.isoformat(),
            updated_at=transaction.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating transaction: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/transactions/{transaction_id}", status_code=204)
async def cancel_transaction(
    transaction_id: str,
    reason: str = Query(..., description="Reason for cancellation"),
    refund_earnest_money: bool = Query(True, description="Whether to refund earnest money"),
    db: Session = Depends(get_db)
):
    """
    Cancel a transaction.
    
    This endpoint:
    - Transitions transaction to CANCELLED state
    - Cancels all pending verification tasks
    - Optionally refunds earnest money to buyer
    - Logs cancellation on blockchain
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    logger.info(
        f"Cancelling transaction {transaction_id}",
        extra={"reason": reason, "refund": refund_earnest_money}
    )
    
    try:
        orchestrator = EscrowAgentOrchestrator(db)
        
        await orchestrator.cancel_transaction(
            transaction_id=transaction_id,
            reason=reason,
            refund_earnest_money=refund_earnest_money
        )
        
        await orchestrator.close()
        
        return None
        
    except EscrowError as e:
        logger.error(f"Failed to cancel transaction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error cancelling transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
