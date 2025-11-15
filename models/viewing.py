"""Viewing model for tracking property viewing appointments."""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from models.database import BaseModel


class Viewing(BaseModel):
    """Model for storing property viewing appointments."""
    
    __tablename__ = "viewings"
    
    # Foreign Key
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Property Information
    property_id = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    listing_url = Column(String(1000), nullable=True)
    
    # Appointment Details
    requested_time = Column(String(50), nullable=False)  # ISO timestamp
    confirmed_time = Column(String(50), nullable=True)  # ISO timestamp
    
    # Listing Agent Information
    agent_name = Column(String(255), nullable=True)
    agent_email = Column(String(255), nullable=True)
    agent_phone = Column(String(50), nullable=True)
    
    # Status Tracking
    status = Column(String(50), nullable=False, default="requested", index=True)
    # Status values: "requested", "confirmed", "cancelled", "completed"
    
    # Calendar Integration
    calendar_event_id = Column(String(255), nullable=True)
    
    # Notes
    notes = Column(String(2000), nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="viewings")
    
    def __repr__(self):
        return f"<Viewing(id={self.id}, address={self.address}, status={self.status})>"
