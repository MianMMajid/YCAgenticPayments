"""Base verification agent abstract class."""
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
import logging
from enum import Enum

from models.transaction import Transaction
from models.verification import (
    VerificationTask,
    VerificationReport,
    VerificationType,
    TaskStatus,
    ReportStatus
)


logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of report validation."""
    
    def __init__(
        self,
        is_valid: bool,
        status: ReportStatus,
        errors: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None
    ):
        self.is_valid = is_valid
        self.status = status
        self.errors = errors or []
        self.warnings = warnings or []
    
    def __repr__(self) -> str:
        return f"ValidationResult(is_valid={self.is_valid}, status={self.status}, errors={len(self.errors)})"


class TaskDetails:
    """Details for a verification task."""
    
    def __init__(
        self,
        task_id: str,
        transaction_id: str,
        property_id: str,
        deadline: datetime,
        payment_amount: Decimal,
        requirements: Dict[str, Any]
    ):
        self.task_id = task_id
        self.transaction_id = transaction_id
        self.property_id = property_id
        self.deadline = deadline
        self.payment_amount = payment_amount
        self.requirements = requirements


class VerificationAgent(ABC):
    """
    Abstract base class for verification agents.
    
    All verification agents must implement execute_verification and validate_report methods.
    This class provides common functionality for authentication, logging, and status tracking.
    """
    
    def __init__(self, agent_id: str, agent_name: str):
        """
        Initialize the verification agent.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_name: Human-readable name for the agent
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
    
    @abstractmethod
    async def execute_verification(
        self,
        transaction: Transaction,
        task_details: TaskDetails
    ) -> VerificationReport:
        """
        Execute the verification task.
        
        Args:
            transaction: The transaction being verified
            task_details: Details about the verification task
        
        Returns:
            VerificationReport: The completed verification report
        
        Raises:
            Exception: If verification fails
        """
        pass
    
    @abstractmethod
    async def validate_report(
        self,
        report: VerificationReport
    ) -> ValidationResult:
        """
        Validate a verification report.
        
        Args:
            report: The report to validate
        
        Returns:
            ValidationResult: The validation result with status and any errors
        """
        pass
    
    async def submit_report(
        self,
        task: VerificationTask,
        report: VerificationReport
    ) -> None:
        """
        Submit a verification report and update task status.
        
        Args:
            task: The verification task
            report: The completed report
        """
        self.logger.info(
            f"Agent {self.agent_name} submitting report for task {task.id}",
            extra={
                "agent_id": self.agent_id,
                "task_id": task.id,
                "transaction_id": task.transaction_id,
                "report_id": report.id
            }
        )
        
        # Validate the report
        validation_result = await self.validate_report(report)
        
        if not validation_result.is_valid:
            self.logger.error(
                f"Report validation failed for task {task.id}: {validation_result.errors}",
                extra={
                    "agent_id": self.agent_id,
                    "task_id": task.id,
                    "errors": validation_result.errors
                }
            )
            report.status = ReportStatus.REJECTED
            report.reviewer_notes = "; ".join(validation_result.errors)
        else:
            report.status = validation_result.status
            if validation_result.warnings:
                report.reviewer_notes = "Warnings: " + "; ".join(validation_result.warnings)
        
        report.reviewed_at = datetime.utcnow()
        
        self.logger.info(
            f"Report submitted successfully for task {task.id} with status {report.status}",
            extra={
                "agent_id": self.agent_id,
                "task_id": task.id,
                "report_status": report.status.value
            }
        )
    
    async def update_task_status(
        self,
        task: VerificationTask,
        status: TaskStatus,
        completed_at: Optional[datetime] = None
    ) -> None:
        """
        Update the status of a verification task.
        
        Args:
            task: The verification task to update
            status: The new status
            completed_at: Optional completion timestamp
        """
        old_status = task.status
        task.status = status
        
        if completed_at:
            task.completed_at = completed_at
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
        
        self.logger.info(
            f"Task {task.id} status updated from {old_status} to {status}",
            extra={
                "agent_id": self.agent_id,
                "task_id": task.id,
                "old_status": old_status.value,
                "new_status": status.value
            }
        )
    
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate the agent with provided credentials.
        
        Args:
            credentials: Authentication credentials
        
        Returns:
            bool: True if authentication successful
        """
        # Basic authentication implementation
        # In production, this would validate against a secure credential store
        self.logger.info(
            f"Agent {self.agent_name} authenticated",
            extra={"agent_id": self.agent_id}
        )
        return True
    
    def log_activity(
        self,
        activity: str,
        level: str = "INFO",
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log agent activity with structured logging.
        
        Args:
            activity: Description of the activity
            level: Log level (INFO, WARNING, ERROR)
            extra_data: Additional data to include in the log
        """
        log_data = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "activity": activity
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(activity, extra=log_data)
