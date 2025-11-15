"""Payment API endpoints for escrow payment transactions."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from models.database import get_db
from models.payment import Payment, PaymentType, PaymentStatus
from agents.escrow_agent_orchestrator import EscrowAgentOrchestrator, EscrowError
from services.smart_contract_wallet_manager import SmartContractWalletManager, WalletManagerError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class PaymentResponse(BaseModel):
    """Response model for payment details."""
    id: str
    transaction_id: str
    wallet_id: str
    payment_type: str
    recipient_id: str
    amount: str
    status: str
    blockchain_tx_hash: Optional[str]
    initiated_at: str
    completed_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """Response model for payment list."""
    payments: List[PaymentResponse]
    total: int


class PaymentRetryResponse(BaseModel):
    """Response model for payment retry."""
    payment_id: str
    status: str
    message: str
    transaction_hash: Optional[str]


@router.get("/transactions/{transaction_id}/payments", response_model=PaymentListResponse)
async def list_payments(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    List all payments for a transaction.
    
    Requirements: 3.1, 3.2, 3.3, 3.5, 4.2, 4.3, 4.4
    """
    logger.info(f"Listing payments for transaction {transaction_id}")
    
    try:
        # Verify transaction exists
        orchestrator = EscrowAgentOrchestrator(db)
        transaction = await orchestrator.get_transaction(transaction_id)
        await orchestrator.close()
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        # Get all payments for the transaction
        payments = db.query(Payment).filter(
            Payment.transaction_id == transaction_id
        ).order_by(Payment.initiated_at.desc()).all()
        
        return PaymentListResponse(
            payments=[
                PaymentResponse(
                    id=p.id,
                    transaction_id=p.transaction_id,
                    wallet_id=p.wallet_id,
                    payment_type=p.payment_type.value,
                    recipient_id=p.recipient_id,
                    amount=str(p.amount),
                    status=p.status.value,
                    blockchain_tx_hash=p.blockchain_tx_hash,
                    initiated_at=p.initiated_at.isoformat(),
                    completed_at=p.completed_at.isoformat() if p.completed_at else None,
                    created_at=p.created_at.isoformat()
                )
                for p in payments
            ],
            total=len(payments)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get payment details by ID.
    
    Requirements: 3.1, 3.2, 3.3, 3.5, 4.2, 4.3, 4.4
    """
    logger.info(f"Fetching payment {payment_id}")
    
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail=f"Payment {payment_id} not found")
        
        return PaymentResponse(
            id=payment.id,
            transaction_id=payment.transaction_id,
            wallet_id=payment.wallet_id,
            payment_type=payment.payment_type.value,
            recipient_id=payment.recipient_id,
            amount=str(payment.amount),
            status=payment.status.value,
            blockchain_tx_hash=payment.blockchain_tx_hash,
            initiated_at=payment.initiated_at.isoformat(),
            completed_at=payment.completed_at.isoformat() if payment.completed_at else None,
            created_at=payment.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/payments/{payment_id}/retry", response_model=PaymentRetryResponse)
async def retry_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """
    Retry a failed payment.
    
    This endpoint:
    - Validates the payment is in FAILED status
    - Attempts to reprocess the payment through the smart contract wallet
    - Updates payment status based on retry result
    - Logs retry attempt on blockchain
    
    Requirements: 3.1, 3.2, 3.3, 3.5, 4.2, 4.3, 4.4
    """
    logger.info(f"Retrying payment {payment_id}")
    
    try:
        # Get payment
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail=f"Payment {payment_id} not found")
        
        # Validate payment status
        if payment.status != PaymentStatus.FAILED:
            raise HTTPException(
                status_code=400,
                detail=f"Payment {payment_id} is not in FAILED status. Current status: {payment.status.value}"
            )
        
        # Get transaction
        orchestrator = EscrowAgentOrchestrator(db)
        transaction = await orchestrator.get_transaction(payment.transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {payment.transaction_id} not found"
            )
        
        # Retry payment through wallet manager
        wallet_manager = SmartContractWalletManager(db)
        
        try:
            # Update payment status to PROCESSING
            payment.status = PaymentStatus.PROCESSING
            db.add(payment)
            db.commit()
            
            # Attempt payment retry based on payment type
            if payment.payment_type == PaymentType.VERIFICATION:
                # Find the verification task to get milestone ID
                from models.verification import VerificationTask
                
                # Get verification tasks to find the one with matching payment amount
                tasks = db.query(VerificationTask).filter(
                    VerificationTask.transaction_id == payment.transaction_id
                ).all()
                
                matching_task = None
                for task in tasks:
                    if task.payment_amount == payment.amount and task.assigned_agent_id == payment.recipient_id:
                        matching_task = task
                        break
                
                if not matching_task:
                    raise WalletManagerError("Could not find matching verification task for payment retry")
                
                milestone_id = f"verification_{matching_task.verification_type.value}_{matching_task.id}"
                
                result = await wallet_manager.release_milestone_payment(
                    transaction=transaction,
                    milestone_id=milestone_id,
                    recipient_id=payment.recipient_id,
                    amount=payment.amount,
                    payment_type=payment.payment_type
                )
                
                # Update payment with success
                payment.status = PaymentStatus.COMPLETED
                payment.blockchain_tx_hash = result.transaction_hash
                payment.completed_at = datetime.utcnow()
                db.add(payment)
                db.commit()
                
                await wallet_manager.close()
                await orchestrator.close()
                
                return PaymentRetryResponse(
                    payment_id=payment.id,
                    status="success",
                    message="Payment retry successful",
                    transaction_hash=result.transaction_hash
                )
                
            else:
                # For other payment types, would need specific retry logic
                raise HTTPException(
                    status_code=400,
                    detail=f"Payment retry not supported for payment type {payment.payment_type.value}"
                )
                
        except WalletManagerError as e:
            # Payment retry failed
            payment.status = PaymentStatus.FAILED
            db.add(payment)
            db.commit()
            
            await wallet_manager.close()
            await orchestrator.close()
            
            logger.error(f"Payment retry failed: {str(e)}")
            
            return PaymentRetryResponse(
                payment_id=payment.id,
                status="failed",
                message=f"Payment retry failed: {str(e)}",
                transaction_hash=None
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrying payment: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
