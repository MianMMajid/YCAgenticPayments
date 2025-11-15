"""Verification models for escrow verification tasks and reports."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, String, Numeric, DateTime, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship

from models.database import BaseModel


class VerificationType(str, Enum):
    """Verification type enum."""
    TITLE_SEARCH = "title_search"
    INSPECTION = "inspection"
    APPRAISAL = "appraisal"
    LENDING = "lending"


class TaskStatus(str, Enum):
    """Task status enum."""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportStatus(str, Enum):
    """Report status enum."""
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class VerificationTask(BaseModel):
    """Verification task assigned to an agent."""
    
    __tablename__ = "verification_tasks"
    
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    verification_type = Column(SQLEnum(VerificationType), nullable=False)
    assigned_agent_id = Column(String(255), nullable=False)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.ASSIGNED)
    deadline = Column(DateTime, nullable=False)
    payment_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    report_id = Column(String, ForeignKey("verification_reports.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="verification_tasks")
    report = relationship("VerificationReport", back_populates="task", uselist=False)


class VerificationReport(BaseModel):
    """Report submitted by verification agent."""
    
    __tablename__ = "verification_reports"
    
    task_id = Column(String, ForeignKey("verification_tasks.id"), nullable=True)
    agent_id = Column(String(255), nullable=False)
    report_type = Column(SQLEnum(VerificationType), nullable=False)
    status = Column(SQLEnum(ReportStatus), nullable=False, default=ReportStatus.NEEDS_REVIEW)
    findings = Column(JSON, nullable=True)
    documents = Column(JSON, nullable=True)  # List of URLs to supporting documents
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_notes = Column(String(2000), nullable=True)
    
    # Relationships
    task = relationship("VerificationTask", back_populates="report")
