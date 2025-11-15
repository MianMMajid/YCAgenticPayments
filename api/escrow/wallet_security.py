"""API endpoints for wallet security management."""
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth import get_current_agent, require_role, require_wallet_access, TokenData, AgentRole
from models.database import get_db
from services.wallet_security import (
    WalletSecurityService,
    WalletSecurityConfig,
    WalletOperation,
    WalletAuditLog
)
from api.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class SecurityConfigRequest(BaseModel):
    """Request to create/update security configuration."""
    multi_sig_enabled: bool = False
    multi_sig_threshold: Decimal = Decimal("50000.00")
    required_approvers: int = 2
    time_lock_enabled: bool = False
    time_lock_duration_hours: int = 24
    time_lock_threshold: Decimal = Decimal("100000.00")


class SecurityConfigResponse(BaseModel):
    """Security configuration response."""
    wallet_id: str
    multi_sig_enabled: bool
    multi_sig_threshold_amount: Decimal
    required_approvers: int
    time_lock_enabled: bool
    time_lock_duration_hours: int
    time_lock_threshold_amount: Decimal
    is_paused: bool
    paused_at: Optional[str]
    paused_by: Optional[str]
    pause_reason: Optional[str]


class OperationResponse(BaseModel):
    """Wallet operation response."""
    id: str
    transaction_id: str
    wallet_id: str
    operation_type: str
    amount: Decimal
    recipient_id: str
    required_approvals: int
    current_approvals: int
    approvers: List[str]
    time_lock_until: Optional[str]
    status: str
    initiated_by: str
    initiated_at: str
    executed_at: Optional[str]


class ApproveOperationRequest(BaseModel):
    """Request to approve an operation."""
    operation_id: str


class PauseWalletRequest(BaseModel):
    """Request to pause a wallet."""
    reason: str


class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    id: str
    wallet_id: str
    operation_id: Optional[str]
    operation_type: str
    agent_id: str
    action: str
    amount: Optional[Decimal]
    details: dict
    timestamp: str


@router.post(
    "/transactions/{transaction_id}/wallet/security-config",
    response_model=SecurityConfigResponse,
    dependencies=[Depends(require_wallet_access())]
)
async def create_wallet_security_config(
    transaction_id: str,
    request: SecurityConfigRequest,
    current_agent: TokenData = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Create security configuration for a transaction's wallet.
    
    Only Escrow Agents can configure wallet security.
    """
    from models.transaction import Transaction
    
    # Get transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if not transaction.wallet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction does not have a wallet"
        )
    
    # Create security service
    security_service = WalletSecurityService(db)
    
    # Check if config already exists
    existing_config = security_service.get_security_config(transaction.wallet_id)
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security configuration already exists"
        )
    
    # Create config
    config = security_service.create_security_config(
        wallet_id=transaction.wallet_id,
        multi_sig_enabled=request.multi_sig_enabled,
        multi_sig_threshold=request.multi_sig_threshold,
        required_approvers=request.required_approvers,
        time_lock_enabled=request.time_lock_enabled,
        time_lock_duration_hours=request.time_lock_duration_hours,
        time_lock_threshold=request.time_lock_threshold
    )
    
    logger.info(
        "wallet_security_config_created",
        transaction_id=transaction_id,
        wallet_id=transaction.wallet_id,
        agent_id=current_agent.agent_id
    )
    
    return SecurityConfigResponse(
        wallet_id=config.wallet_id,
        multi_sig_enabled=config.multi_sig_enabled,
        multi_sig_threshold_amount=config.multi_sig_threshold_amount,
        required_approvers=int(config.required_approvers),
        time_lock_enabled=config.time_lock_enabled,
        time_lock_duration_hours=int(config.time_lock_duration_hours),
        time_lock_threshold_amount=config.time_lock_threshold_amount,
        is_paused=config.is_paused,
        paused_at=config.paused_at.isoformat() if config.paused_at else None,
        paused_by=config.paused_by,
        pause_reason=config.pause_reason
    )


@router.get(
    "/transactions/{transaction_id}/wallet/security-config",
    response_model=SecurityConfigResponse
)
async def get_wallet_security_config(
    transaction_id: str,
    current_agent: TokenData = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get security configuration for a transaction's wallet."""
    from models.transaction import Transaction
    from api.auth import check_transaction_access
    
    # Get transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Check access
    if not check_transaction_access(transaction_id, current_agent, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this transaction"
        )
    
    if not transaction.wallet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction does not have a wallet"
        )
    
    # Get config
    security_service = WalletSecurityService(db)
    config = security_service.get_security_config(transaction.wallet_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security configuration not found"
        )
    
    return SecurityConfigResponse(
        wallet_id=config.wallet_id,
        multi_sig_enabled=config.multi_sig_enabled,
        multi_sig_threshold_amount=config.multi_sig_threshold_amount,
        required_approvers=int(config.required_approvers),
        time_lock_enabled=config.time_lock_enabled,
        time_lock_duration_hours=int(config.time_lock_duration_hours),
        time_lock_threshold_amount=config.time_lock_threshold_amount,
        is_paused=config.is_paused,
        paused_at=config.paused_at.isoformat() if config.paused_at else None,
        paused_by=config.paused_by,
        pause_reason=config.pause_reason
    )


@router.post(
    "/wallet-operations/{operation_id}/approve",
    response_model=OperationResponse
)
async def approve_wallet_operation(
    operation_id: str,
    current_agent: TokenData = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Approve a wallet operation.
    
    Only Escrow Agents can approve operations.
    """
    if current_agent.role != AgentRole.ESCROW_AGENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Escrow Agents can approve operations"
        )
    
    security_service = WalletSecurityService(db)
    
    try:
        operation = security_service.approve_operation(operation_id, current_agent.agent_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    logger.info(
        "wallet_operation_approved",
        operation_id=operation_id,
        agent_id=current_agent.agent_id
    )
    
    return OperationResponse(
        id=operation.id,
        transaction_id=operation.transaction_id,
        wallet_id=operation.wallet_id,
        operation_type=operation.operation_type,
        amount=operation.amount,
        recipient_id=operation.recipient_id,
        required_approvals=int(operation.required_approvals),
        current_approvals=int(operation.current_approvals),
        approvers=operation.approvers or [],
        time_lock_until=operation.time_lock_until.isoformat() if operation.time_lock_until else None,
        status=operation.status,
        initiated_by=operation.initiated_by,
        initiated_at=operation.initiated_at.isoformat(),
        executed_at=operation.executed_at.isoformat() if operation.executed_at else None
    )


@router.post(
    "/transactions/{transaction_id}/wallet/pause",
    response_model=SecurityConfigResponse,
    dependencies=[Depends(require_wallet_access())]
)
async def pause_wallet(
    transaction_id: str,
    request: PauseWalletRequest,
    current_agent: TokenData = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Emergency pause all operations on a wallet.
    
    Only Escrow Agents can pause wallets.
    """
    from models.transaction import Transaction
    
    # Get transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if not transaction.wallet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction does not have a wallet"
        )
    
    security_service = WalletSecurityService(db)
    
    try:
        config = security_service.pause_wallet(
            wallet_id=transaction.wallet_id,
            paused_by=current_agent.agent_id,
            reason=request.reason
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    logger.warning(
        "wallet_paused",
        transaction_id=transaction_id,
        wallet_id=transaction.wallet_id,
        agent_id=current_agent.agent_id,
        reason=request.reason
    )
    
    return SecurityConfigResponse(
        wallet_id=config.wallet_id,
        multi_sig_enabled=config.multi_sig_enabled,
        multi_sig_threshold_amount=config.multi_sig_threshold_amount,
        required_approvers=int(config.required_approvers),
        time_lock_enabled=config.time_lock_enabled,
        time_lock_duration_hours=int(config.time_lock_duration_hours),
        time_lock_threshold_amount=config.time_lock_threshold_amount,
        is_paused=config.is_paused,
        paused_at=config.paused_at.isoformat() if config.paused_at else None,
        paused_by=config.paused_by,
        pause_reason=config.pause_reason
    )


@router.post(
    "/transactions/{transaction_id}/wallet/resume",
    response_model=SecurityConfigResponse,
    dependencies=[Depends(require_wallet_access())]
)
async def resume_wallet(
    transaction_id: str,
    current_agent: TokenData = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Resume operations on a paused wallet.
    
    Only Escrow Agents can resume wallets.
    """
    from models.transaction import Transaction
    
    # Get transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if not transaction.wallet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction does not have a wallet"
        )
    
    security_service = WalletSecurityService(db)
    
    try:
        config = security_service.resume_wallet(
            wallet_id=transaction.wallet_id,
            resumed_by=current_agent.agent_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    logger.info(
        "wallet_resumed",
        transaction_id=transaction_id,
        wallet_id=transaction.wallet_id,
        agent_id=current_agent.agent_id
    )
    
    return SecurityConfigResponse(
        wallet_id=config.wallet_id,
        multi_sig_enabled=config.multi_sig_enabled,
        multi_sig_threshold_amount=config.multi_sig_threshold_amount,
        required_approvers=int(config.required_approvers),
        time_lock_enabled=config.time_lock_enabled,
        time_lock_duration_hours=int(config.time_lock_duration_hours),
        time_lock_threshold_amount=config.time_lock_threshold_amount,
        is_paused=config.is_paused,
        paused_at=config.paused_at.isoformat() if config.paused_at else None,
        paused_by=config.paused_by,
        pause_reason=config.pause_reason
    )


@router.get(
    "/transactions/{transaction_id}/wallet/audit-trail",
    response_model=List[AuditLogResponse]
)
async def get_wallet_audit_trail(
    transaction_id: str,
    limit: int = 100,
    current_agent: TokenData = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get audit trail for a transaction's wallet."""
    from models.transaction import Transaction
    from api.auth import check_transaction_access
    
    # Get transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Check access
    if not check_transaction_access(transaction_id, current_agent, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this transaction"
        )
    
    if not transaction.wallet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction does not have a wallet"
        )
    
    security_service = WalletSecurityService(db)
    audit_logs = security_service.get_audit_trail(transaction.wallet_id, limit=limit)
    
    return [
        AuditLogResponse(
            id=log.id,
            wallet_id=log.wallet_id,
            operation_id=log.operation_id,
            operation_type=log.operation_type,
            agent_id=log.agent_id,
            action=log.action,
            amount=log.amount,
            details=log.details or {},
            timestamp=log.timestamp.isoformat()
        )
        for log in audit_logs
    ]
