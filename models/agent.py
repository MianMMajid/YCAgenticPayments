"""Agent model for authentication and authorization."""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func

from models.database import BaseModel, EncryptedString


class Agent(BaseModel):
    """Agent model for authentication."""
    
    __tablename__ = "agents"
    
    # Agent identification
    agent_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(EncryptedString(255), nullable=False)
    
    # Authentication
    api_key_hash = Column(String(255), nullable=False)  # Hashed API key
    
    # Role (stored as string, validated against AgentRole enum)
    role = Column(String(50), nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Agent(id={self.id}, agent_id={self.agent_id}, role={self.role})>"
