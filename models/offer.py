"""Offer model for tracking purchase offers."""
from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship

from models.database import BaseModel


class Offer(BaseModel):
    """Model for storing purchase offer details."""
    
    __tablename__ = "offers"
    
    # Foreign Key
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Property Information
    property_id = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    
    # Offer Terms
    offer_price = Column(Integer, nullable=False)
    list_price = Column(Integer, nullable=True)
    closing_days = Column(Integer, nullable=False)
    closing_date = Column(String(50), nullable=True)  # ISO date
    financing_type = Column(String(50), nullable=False)  # "cash", "conventional", "fha", "va"
    contingencies = Column(JSON, default=list)  # ["inspection", "appraisal", "financing"]
    
    # Additional Terms
    earnest_money = Column(Integer, nullable=True)
    special_terms = Column(String(2000), nullable=True)
    
    # Docusign Integration
    envelope_id = Column(String(255), nullable=True, unique=True)
    signing_url = Column(String(1000), nullable=True)
    template_id = Column(String(255), nullable=True)
    
    # Status Tracking
    status = Column(String(50), nullable=False, default="draft", index=True)
    # Status values: "draft", "sent", "signed", "rejected", "accepted", "expired"
    
    # Timestamps
    sent_at = Column(String(50), nullable=True)  # ISO timestamp
    signed_at = Column(String(50), nullable=True)  # ISO timestamp
    
    # Relationship
    user = relationship("User", back_populates="offers")
    
    def __repr__(self):
        return f"<Offer(id={self.id}, address={self.address}, offer_price={self.offer_price}, status={self.status})>"
