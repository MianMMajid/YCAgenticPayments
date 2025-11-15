"""Security features for smart contract wallet operations."""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, String, Numeric, DateTime, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import Session, relationship

from models.database import BaseModel
from api.structured_logging import get_logger

logger = get_logger(__name__)


class ApprovalStatus(str, Enum):
    """Multi-signature approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class WalletOperation(BaseModel):
    """Wallet operation requiring approval."""
    
    __tablename__ = "wallet_operations"
    
    transaction_id = Column(String(255), nullable=False, index=True)
    wallet_id = Column(String(255), nullable=False)
    operation_type = Column(String(50), nullable=False)  # PAYMENT, SETTLEMENT
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    recipient_id = Column(String(255), nullable=False)
    operation_data = Column(JSON, nullable=True)
    
    # Multi-signature fields
    required_approvals = Column(Numeric, nullable=False, default=1)
    current_approvals = Column(Numeric, nullable=False, default=0)
    approvers = Column(JSON, nullable=True, default=list)  # List of agent IDs who approved
    
    # Time lock fields
    time_lock_until = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default=ApprovalStatus.PENDING.value)
    executed_at = Column(DateTime, nullable=True)
    
    # Audit trail
    initiated_by = Column(String(255), nullable=False)
    initiated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class WalletSecurityConfig(BaseModel):
    """Security configuration for wallet operations."""
    
    __tablename__ = "wallet_security_configs"
    
    wallet_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Multi-signature configuration
    multi_sig_enabled = Column(Boolean, nullable=False, default=False)
    multi_sig_threshold_amount = Column(Numeric(precision=12, scale=2), nullable=False, default=Decimal("50000.00"))
    required_approvers = Column(Numeric, nullable=False, default=2)
    
    # Time lock configuration
    time_lock_enabled = Column(Boolean, nullable=False, default=False)
    time_lock_duration_hours = Column(Numeric, nullable=False, default=24)
    time_lock_threshold_amount = Column(Numeric(precision=12, scale=2), nullable=False, default=Decimal("100000.00"))
    
    # Emergency pause
    is_paused = Column(Boolean, nullable=False, default=False)
    paused_at = Column(DateTime, nullable=True)
    paused_by = Column(String(255), nullable=True)
    pause_reason = Column(String(500), nullable=True)


class WalletAuditLog(BaseModel):
    """Audit log for wallet operations."""
    
    __tablename__ = "wallet_audit_logs"
    
    wallet_id = Column(String(255), nullable=False, index=True)
    operation_id = Column(String(255), nullable=True)
    operation_type = Column(String(50), nullable=False)
    agent_id = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)  # INITIATED, APPROVED, REJECTED, EXECUTED, PAUSED, RESUMED
    amount = Column(Numeric(precision=12, scale=2), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)


class WalletSecurityService:
    """Service for managing wallet security features."""
    
    def __init__(self, db: Session):
        """Initialize wallet security service."""
        self.db = db
    
    def get_security_config(self, wallet_id: str) -> Optional[WalletSecurityConfig]:
        """Get security configuration for a wallet."""
        return self.db.query(WalletSecurityConfig).filter(
            WalletSecurityConfig.wallet_id == wallet_id
        ).first()
    
    def create_security_config(
        self,
        wallet_id: str,
        multi_sig_enabled: bool = False,
        multi_sig_threshold: Decimal = Decimal("50000.00"),
        required_approvers: int = 2,
        time_lock_enabled: bool = False,
        time_lock_duration_hours: int = 24,
        time_lock_threshold: Decimal = Decimal("100000.00")
    ) -> WalletSecurityConfig:
        """Create security configuration for a wallet."""
        config = WalletSecurityConfig(
            wallet_id=wallet_id,
            multi_sig_enabled=multi_sig_enabled,
            multi_sig_threshold_amount=multi_sig_threshold,
            required_approvers=required_approvers,
            time_lock_enabled=time_lock_enabled,
            time_lock_duration_hours=time_lock_duration_hours,
            time_lock_threshold_amount=time_lock_threshold
        )
        
        self.db.add(config)
        self.db.commit()
        
        logger.info(
            "wallet_security_config_created",
            wallet_id=wallet_id,
            multi_sig_enabled=multi_sig_enabled,
            time_lock_enabled=time_lock_enabled
        )
        
        return config
    
    def requires_multi_signature(
        self,
        wallet_id: str,
        amount: Decimal
    ) -> bool:
        """Check if operation requires multi-signature approval."""
        config = self.get_security_config(wallet_id)
        
        if not config or not config.multi_sig_enabled:
            return False
        
        return amount >= config.multi_sig_threshold_amount
    
    def requires_time_lock(
        self,
        wallet_id: str,
        amount: Decimal
    ) -> bool:
        """Check if operation requires time lock."""
        config = self.get_security_config(wallet_id)
        
        if not config or not config.time_lock_enabled:
            return False
        
        return amount >= config.time_lock_threshold_amount
    
    def create_wallet_operation(
        self,
        transaction_id: str,
        wallet_id: str,
        operation_type: str,
        amount: Decimal,
        recipient_id: str,
        initiated_by: str,
        operation_data: Optional[Dict[str, Any]] = None
    ) -> WalletOperation:
        """Create a wallet operation that may require approval."""
        config = self.get_security_config(wallet_id)
        
        # Determine required approvals
        required_approvals = 1  # Default: only initiator
        if config and config.multi_sig_enabled and amount >= config.multi_sig_threshold_amount:
            required_approvals = int(config.required_approvers)
        
        # Determine time lock
        time_lock_until = None
        if config and config.time_lock_enabled and amount >= config.time_lock_threshold_amount:
            time_lock_until = datetime.utcnow() + timedelta(hours=int(config.time_lock_duration_hours))
        
        operation = WalletOperation(
            transaction_id=transaction_id,
            wallet_id=wallet_id,
            operation_type=operation_type,
            amount=amount,
            recipient_id=recipient_id,
            operation_data=operation_data or {},
            required_approvals=required_approvals,
            current_approvals=0,
            approvers=[],
            time_lock_until=time_lock_until,
            status=ApprovalStatus.PENDING.value,
            initiated_by=initiated_by
        )
        
        self.db.add(operation)
        self.db.commit()
        
        # Log operation creation
        self._log_audit(
            wallet_id=wallet_id,
            operation_id=operation.id,
            operation_type=operation_type,
            agent_id=initiated_by,
            action="INITIATED",
            amount=amount,
            details={
                "recipient_id": recipient_id,
                "required_approvals": required_approvals,
                "time_lock_until": time_lock_until.isoformat() if time_lock_until else None
            }
        )
        
        logger.info(
            "wallet_operation_created",
            operation_id=operation.id,
            wallet_id=wallet_id,
            amount=str(amount),
            required_approvals=required_approvals,
            time_lock_until=time_lock_until.isoformat() if time_lock_until else None
        )
        
        return operation
    
    def approve_operation(
        self,
        operation_id: str,
        approver_id: str
    ) -> WalletOperation:
        """Approve a wallet operation."""
        operation = self.db.query(WalletOperation).filter(
            WalletOperation.id == operation_id
        ).first()
        
        if not operation:
            raise ValueError(f"Operation {operation_id} not found")
        
        if operation.status != ApprovalStatus.PENDING.value:
            raise ValueError(f"Operation is not pending approval: {operation.status}")
        
        # Check if already approved by this agent
        approvers = operation.approvers or []
        if approver_id in approvers:
            raise ValueError(f"Agent {approver_id} has already approved this operation")
        
        # Add approval
        approvers.append(approver_id)
        operation.approvers = approvers
        operation.current_approvals = len(approvers)
        
        # Check if enough approvals
        if operation.current_approvals >= operation.required_approvals:
            operation.status = ApprovalStatus.APPROVED.value
        
        self.db.commit()
        
        # Log approval
        self._log_audit(
            wallet_id=operation.wallet_id,
            operation_id=operation.id,
            operation_type=operation.operation_type,
            agent_id=approver_id,
            action="APPROVED",
            amount=operation.amount,
            details={
                "current_approvals": operation.current_approvals,
                "required_approvals": operation.required_approvals
            }
        )
        
        logger.info(
            "wallet_operation_approved",
            operation_id=operation.id,
            approver_id=approver_id,
            current_approvals=operation.current_approvals,
            required_approvals=operation.required_approvals
        )
        
        return operation
    
    def can_execute_operation(
        self,
        operation_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if operation can be executed.
        
        Returns:
            Tuple of (can_execute, reason_if_not)
        """
        operation = self.db.query(WalletOperation).filter(
            WalletOperation.id == operation_id
        ).first()
        
        if not operation:
            return False, "Operation not found"
        
        # Check if wallet is paused
        config = self.get_security_config(operation.wallet_id)
        if config and config.is_paused:
            return False, f"Wallet is paused: {config.pause_reason}"
        
        # Check approval status
        if operation.status != ApprovalStatus.APPROVED.value:
            if operation.current_approvals < operation.required_approvals:
                return False, f"Insufficient approvals: {operation.current_approvals}/{operation.required_approvals}"
            return False, f"Operation status: {operation.status}"
        
        # Check time lock
        if operation.time_lock_until and datetime.utcnow() < operation.time_lock_until:
            remaining = operation.time_lock_until - datetime.utcnow()
            return False, f"Time lock active for {remaining.total_seconds() / 3600:.1f} more hours"
        
        return True, None
    
    def mark_operation_executed(
        self,
        operation_id: str,
        executed_by: str
    ) -> WalletOperation:
        """Mark operation as executed."""
        operation = self.db.query(WalletOperation).filter(
            WalletOperation.id == operation_id
        ).first()
        
        if not operation:
            raise ValueError(f"Operation {operation_id} not found")
        
        operation.executed_at = datetime.utcnow()
        self.db.commit()
        
        # Log execution
        self._log_audit(
            wallet_id=operation.wallet_id,
            operation_id=operation.id,
            operation_type=operation.operation_type,
            agent_id=executed_by,
            action="EXECUTED",
            amount=operation.amount
        )
        
        logger.info(
            "wallet_operation_executed",
            operation_id=operation.id,
            executed_by=executed_by
        )
        
        return operation
    
    def pause_wallet(
        self,
        wallet_id: str,
        paused_by: str,
        reason: str
    ) -> WalletSecurityConfig:
        """Emergency pause all operations on a wallet."""
        config = self.get_security_config(wallet_id)
        
        if not config:
            raise ValueError(f"Security config not found for wallet {wallet_id}")
        
        config.is_paused = True
        config.paused_at = datetime.utcnow()
        config.paused_by = paused_by
        config.pause_reason = reason
        
        self.db.commit()
        
        # Log pause
        self._log_audit(
            wallet_id=wallet_id,
            operation_id=None,
            operation_type="EMERGENCY_PAUSE",
            agent_id=paused_by,
            action="PAUSED",
            details={"reason": reason}
        )
        
        logger.warning(
            "wallet_paused",
            wallet_id=wallet_id,
            paused_by=paused_by,
            reason=reason
        )
        
        return config
    
    def resume_wallet(
        self,
        wallet_id: str,
        resumed_by: str
    ) -> WalletSecurityConfig:
        """Resume operations on a paused wallet."""
        config = self.get_security_config(wallet_id)
        
        if not config:
            raise ValueError(f"Security config not found for wallet {wallet_id}")
        
        if not config.is_paused:
            raise ValueError(f"Wallet {wallet_id} is not paused")
        
        config.is_paused = False
        config.paused_at = None
        config.paused_by = None
        config.pause_reason = None
        
        self.db.commit()
        
        # Log resume
        self._log_audit(
            wallet_id=wallet_id,
            operation_id=None,
            operation_type="RESUME",
            agent_id=resumed_by,
            action="RESUMED"
        )
        
        logger.info(
            "wallet_resumed",
            wallet_id=wallet_id,
            resumed_by=resumed_by
        )
        
        return config
    
    def get_audit_trail(
        self,
        wallet_id: str,
        limit: int = 100
    ) -> List[WalletAuditLog]:
        """Get audit trail for a wallet."""
        return self.db.query(WalletAuditLog).filter(
            WalletAuditLog.wallet_id == wallet_id
        ).order_by(
            WalletAuditLog.timestamp.desc()
        ).limit(limit).all()
    
    def _log_audit(
        self,
        wallet_id: str,
        operation_id: Optional[str],
        operation_type: str,
        agent_id: str,
        action: str,
        amount: Optional[Decimal] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log wallet operation to audit trail."""
        log = WalletAuditLog(
            wallet_id=wallet_id,
            operation_id=operation_id,
            operation_type=operation_type,
            agent_id=agent_id,
            action=action,
            amount=amount,
            details=details or {}
        )
        
        self.db.add(log)
        self.db.commit()
