"""SearchHistory model for tracking property searches."""
from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship

from models.database import BaseModel


class SearchHistory(BaseModel):
    """Model for storing user property search history."""
    
    __tablename__ = "search_history"
    
    # Foreign Key
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Search Parameters
    query = Column(String(500), nullable=True)  # Original voice query
    location = Column(String(255), nullable=False)
    max_price = Column(Integer, nullable=True)
    min_price = Column(Integer, nullable=True)
    min_beds = Column(Integer, nullable=True)
    min_baths = Column(Integer, nullable=True)
    property_type = Column(String(100), nullable=True)
    
    # Search Results (cached)
    results = Column(JSON, default=list)  # List of property dictionaries
    total_found = Column(Integer, default=0)
    
    # Relationship
    user = relationship("User", back_populates="search_history")
    
    def __repr__(self):
        return f"<SearchHistory(id={self.id}, location={self.location}, user_id={self.user_id})>"
