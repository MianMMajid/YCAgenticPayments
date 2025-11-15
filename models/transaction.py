"""Transaction model for escrow transactions."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, String, Numeric, DateTime, JSON, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship

from models.database import BaseModel, EncryptedString


class TransactionState(str, Enum):
    """Transaction state enum."""
    INITIATED = "initiated"
    FUNDED = "funded"
    VERIFICATION_IN_PROGRESS = "verification_in_progress"
    VERIFICATION_COMPLETE = "verification_complete"
    SETTLEMENT_PENDING = "settlement_pending"
    SETTLED = "settled"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class Transaction(BaseModel):
    """Transaction entity for escrow transactions."""
    
    __tablename__ = "transactions"
    
    buyer_agent_id = Column(String(255), nullable=False)
    seller_agent_id = Column(String(255), nullable=False)
    property_id = Column(String(255), nullable=False)
    earnest_money = Column(Numeric(precision=12, scale=2), nullable=False)
    total_purchase_price = Column(Numeric(precision=12, scale=2), nullable=False)
    state = Column(SQLEnum(TransactionState), nullable=False, default=TransactionState.INITIATED)
    wallet_id = Column(String(255), nullable=True)
    initiated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    target_closing_date = Column(DateTime, nullable=False)
    actual_closing_date = Column(DateTime, nullable=True)
    transaction_metadata = Column("metadata", JSON, nullable=True)
    
    # Encrypted sensitive data (PII, financial details)
    encrypted_metadata = Column(Text, nullable=True)  # Encrypted JSON for sensitive data
    
    # Relationships
    verification_tasks = relationship("VerificationTask", back_populates="transaction", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="transaction", cascade="all, delete-orphan")
    settlement = relationship("Settlement", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    blockchain_events = relationship("BlockchainEvent", back_populates="transaction", cascade="all, delete-orphan")
