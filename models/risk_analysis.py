"""RiskAnalysis model for storing property risk assessments."""
from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship

from models.database import BaseModel


class RiskAnalysis(BaseModel):
    """Model for storing property risk analysis results."""
    
    __tablename__ = "risk_analyses"
    
    # Foreign Key
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Property Information
    property_id = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=False)
    list_price = Column(Integer, nullable=False)
    
    # Risk Assessment Results
    flags = Column(JSON, default=list)  # List of risk flag dictionaries
    overall_risk = Column(String(50), nullable=True)  # "high", "medium", "low"
    
    # Source Data (for audit trail)
    estimated_value = Column(Integer, nullable=True)
    tax_assessment = Column(Integer, nullable=True)
    flood_zone = Column(String(50), nullable=True)
    crime_score = Column(Integer, nullable=True)
    
    # Additional metadata
    data_sources = Column(JSON, default=dict)  # Track which APIs were used
    
    # Relationship
    user = relationship("User", back_populates="risk_analyses")
    
    def __repr__(self):
        return f"<RiskAnalysis(id={self.id}, property_id={self.property_id}, overall_risk={self.overall_risk})>"
