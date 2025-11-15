"""Database connection and base configuration."""
import uuid
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import create_engine, Column, String, DateTime, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from cryptography.fernet import Fernet

from config.settings import settings

logger = logging.getLogger(__name__)

# Initialize encryption cipher
if not settings.encryption_key:
    if settings.environment == "production":
        raise ValueError(
            "ENCRYPTION_KEY is required in production. "
            "Generate one with: python scripts/generate_encryption_key.py"
        )
    else:
        # In development, generate a key but warn the user
        logger.warning(
            "ENCRYPTION_KEY not set. Generated a temporary key. "
            "This key will change on restart, making encrypted data unreadable. "
            "Set ENCRYPTION_KEY in your .env file for persistent encryption."
        )
        cipher = Fernet(Fernet.generate_key())
else:
    cipher = Fernet(settings.encryption_key.encode())


class EncryptedString(TypeDecorator):
    """Custom SQLAlchemy type for encrypted string fields."""
    
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        """Encrypt value before storing in database."""
        if value is not None:
            return cipher.encrypt(value.encode()).decode()
        return value
    
    def process_result_value(self, value: Any, dialect: Any) -> Optional[str]:
        """Decrypt value when retrieving from database."""
        if value is not None:
            return cipher.decrypt(value.encode()).decode()
        return value


# Create database engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.environment == "development"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


class BaseModel(Base):
    """Base model class with common fields."""
    
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
