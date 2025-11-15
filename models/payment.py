"""Payment model for escrow payment transactions."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from enum import Enum

from sqlalchemy import Column, String, Numeric, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship

from models.database import BaseModel


class PaymentType(str, Enum):
    """Payment type enum."""
    EARNEST_MONEY = "earnest_money"
    VERIFICATION = "verification"
    COMMISSION = "commission"
    CLOSING_COST = "closing_cost"
    SETTLEMENT = "settlement"


class PaymentStatus(str, Enum):
    """Payment status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Payment(BaseModel):
    """Payment transaction record."""
    
    __tablename__ = "payments"
    
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    wallet_id = Column(String(255), nullable=False)
    payment_type = Column(SQLEnum(PaymentType), nullable=False)
    recipient_id = Column(String(255), nullable=False)
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    blockchain_tx_hash = Column(String(255), nullable=True)
    initiated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="payments")
