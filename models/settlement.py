"""Settlement model for final transaction settlement."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, String, Numeric, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from models.database import BaseModel


class Settlement(BaseModel):
    """Final settlement record."""
    
    __tablename__ = "settlements"
    
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False, unique=True)
    total_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    seller_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    buyer_agent_commission = Column(Numeric(precision=12, scale=2), nullable=False)
    seller_agent_commission = Column(Numeric(precision=12, scale=2), nullable=False)
    closing_costs = Column(Numeric(precision=12, scale=2), nullable=False)
    distributions = Column(JSON, nullable=True)  # List of distribution details
    blockchain_tx_hash = Column(String(255), nullable=True)
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="settlement")


class BlockchainEvent(BaseModel):
    """On-chain event log for audit trail."""
    
    __tablename__ = "blockchain_events"
    
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=True)
    blockchain_tx_hash = Column(String(255), nullable=False)
    block_number = Column(String(100), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="blockchain_events")
