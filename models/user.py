"""User model for storing buyer profiles and preferences."""
from sqlalchemy import Column, String, Integer, Boolean, JSON
from sqlalchemy.orm import relationship

from models.database import BaseModel, EncryptedString


class User(BaseModel):
    """User model representing a home buyer."""
    
    __tablename__ = "users"
    
    # Personal Information (encrypted)
    phone_number = Column(EncryptedString(255), unique=True, nullable=False, index=True)
    email = Column(EncryptedString(255), nullable=True)
    name = Column(String(255), nullable=True)
    
    # Preferences
    preferred_locations = Column(JSON, default=list)  # List of cities/states
    max_budget = Column(Integer, nullable=True)
    min_beds = Column(Integer, nullable=True)
    min_baths = Column(Integer, nullable=True)
    property_types = Column(JSON, default=list)  # ["single-family", "condo", etc.]
    
    # Pre-approval Status
    pre_approved = Column(Boolean, default=False)
    pre_approval_amount = Column(Integer, nullable=True)
    
    # Google Calendar Integration
    google_calendar_token = Column(EncryptedString(1000), nullable=True)
    google_calendar_refresh_token = Column(EncryptedString(1000), nullable=True)
    
    # Session Management
    last_active = Column(String(50), nullable=True)  # ISO timestamp
    
    # Relationships
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    risk_analyses = relationship("RiskAnalysis", back_populates="user", cascade="all, delete-orphan")
    viewings = relationship("Viewing", back_populates="user", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name})>"
