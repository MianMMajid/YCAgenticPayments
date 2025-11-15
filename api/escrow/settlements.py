"""Settlement API endpoints for escrow final settlements."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field

from models.database import get_db
from models.settlement import Settlement
from agents.escrow_agent_orchestrator import EscrowAgentOrchestrator, EscrowError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class SettlementExecuteRequest(BaseModel):
    """Request model for executing settlement."""
    buyer_agent_commission_rate: Decimal = Field(
        default=Decimal("0.03"),
        description="Buyer agent commission rate (default 3%)",
        ge=0,
        le=1
    )
    seller_agent_commission_rate: Decimal = Field(
        default=Decimal("0.03"),
        description="Seller agent commission rate (default 3%)",
        ge=0,
        le=1
    )
    closing_costs: Optional[Decimal] = Field(
        None,
        description="Total closing costs (calculated if not provided)",
        ge=0
    )
    additional_distributions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Additional distributions to make"
    )


class SettlementResponse(BaseModel):
    """Response model for settlement details."""
    id: str
    transaction_id: str
    total_amount: str
    seller_amount: str
    buyer_agent_commission: str
    seller_agent_commission: str
    closing_costs: str
    distributions: Optional[List[Dict[str, Any]]]
    blockchain_tx_hash: Optional[str]
    executed_at: str
    created_at: str

    class Config:
        from_attributes = True


class SettlementPreviewResponse(BaseModel):
    """Response model for settlement preview/calculation."""
    transaction_id: str
    total_purchase_price: str
    seller_amount: str
    buyer_agent_commission: str
    buyer_agent_commission_rate: str
    seller_agent_commission: str
    seller_agent_commission_rate: str
    closing_costs: str
    breakdown: Dict[str, str]


@router.post("/transactions/{transaction_id}/settlement", response_model=SettlementResponse, status_code=201)
async def execute_settlement(
    transaction_id: str,
    settlement_data: SettlementExecuteRequest,
    db: Session = Depends(get_db)
):
    """
    Execute final settlement for a transaction.
    
    This endpoint:
    - Validates all verifications are approved
    - Calculates final settlement amounts
    - Distributes funds to seller, agents, and service providers
    - Logs settlement on blockchain
    - Sends settlement completion notifications
    - Transitions transaction to SETTLED state
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    logger.info(
        f"Executing settlement for transaction {transaction_id}",
        extra={
            "buyer_commission_rate": str(settlement_data.buyer_agent_commission_rate),
            "seller_commission_rate": str(settlement_data.seller_agent_commission_rate)
        }
    )
    
    try:
        orchestrator = EscrowAgentOrchestrator(db)
        
        settlement = await orchestrator.execute_settlement(
            transaction_id=transaction_id,
            buyer_agent_commission_rate=settlement_data.buyer_agent_commission_rate,
            seller_agent_commission_rate=settlement_data.seller_agent_commission_rate,
            closing_costs=settlement_data.closing_costs,
            additional_distributions=settlement_data.additional_distributions
        )
        
        await orchestrator.close()
        
        return SettlementResponse(
            id=settlement.id,
            transaction_id=settlement.transaction_id,
            total_amount=str(settlement.total_amount),
            seller_amount=str(settlement.seller_amount),
            buyer_agent_commission=str(settlement.buyer_agent_commission),
            seller_agent_commission=str(settlement.seller_agent_commission),
            closing_costs=str(settlement.closing_costs),
            distributions=settlement.distributions,
            blockchain_tx_hash=settlement.blockchain_tx_hash,
            executed_at=settlement.executed_at.isoformat(),
            created_at=settlement.created_at.isoformat()
        )
        
    except EscrowError as e:
        logger.error(f"Failed to execute settlement: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error executing settlement: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/transactions/{transaction_id}/settlement", response_model=SettlementResponse)
async def get_settlement(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Get settlement details for a transaction.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    logger.info(f"Fetching settlement for transaction {transaction_id}")
    
    try:
        # Verify transaction exists
        orchestrator = EscrowAgentOrchestrator(db)
        transaction = await orchestrator.get_transaction(transaction_id)
        await orchestrator.close()
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        # Get settlement
        settlement = db.query(Settlement).filter(
            Settlement.transaction_id == transaction_id
        ).first()
        
        if not settlement:
            raise HTTPException(
                status_code=404,
                detail=f"Settlement not found for transaction {transaction_id}"
            )
        
        return SettlementResponse(
            id=settlement.id,
            transaction_id=settlement.transaction_id,
            total_amount=str(settlement.total_amount),
            seller_amount=str(settlement.seller_amount),
            buyer_agent_commission=str(settlement.buyer_agent_commission),
            seller_agent_commission=str(settlement.seller_agent_commission),
            closing_costs=str(settlement.closing_costs),
            distributions=settlement.distributions,
            blockchain_tx_hash=settlement.blockchain_tx_hash,
            executed_at=settlement.executed_at.isoformat(),
            created_at=settlement.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching settlement: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/transactions/{transaction_id}/settlement/preview", response_model=SettlementPreviewResponse)
async def preview_settlement(
    transaction_id: str,
    buyer_agent_commission_rate: Decimal = Query(
        default=Decimal("0.03"),
        description="Buyer agent commission rate (default 3%)",
        ge=0,
        le=1
    ),
    seller_agent_commission_rate: Decimal = Query(
        default=Decimal("0.03"),
        description="Seller agent commission rate (default 3%)",
        ge=0,
        le=1
    ),
    closing_costs: Optional[Decimal] = Query(
        None,
        description="Total closing costs (calculated if not provided)",
        ge=0
    ),
    db: Session = Depends(get_db)
):
    """
    Preview settlement calculation without executing it.
    
    This endpoint calculates settlement amounts based on provided parameters
    without actually executing the settlement. Useful for showing users
    what they will receive before finalizing.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    logger.info(
        f"Previewing settlement for transaction {transaction_id}",
        extra={
            "buyer_commission_rate": str(buyer_agent_commission_rate),
            "seller_commission_rate": str(seller_agent_commission_rate)
        }
    )
    
    try:
        orchestrator = EscrowAgentOrchestrator(db)
        
        preview = await orchestrator.calculate_settlement_preview(
            transaction_id=transaction_id,
            buyer_agent_commission_rate=buyer_agent_commission_rate,
            seller_agent_commission_rate=seller_agent_commission_rate,
            closing_costs=closing_costs
        )
        
        await orchestrator.close()
        
        return SettlementPreviewResponse(**preview)
        
    except EscrowError as e:
        logger.error(f"Failed to preview settlement: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error previewing settlement: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
