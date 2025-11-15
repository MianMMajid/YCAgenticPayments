"""Verification API endpoints for escrow verification tasks and reports."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from models.database import get_db
from models.verification import (
    VerificationTask,
    VerificationReport,
    VerificationType,
    TaskStatus,
    ReportStatus
)
from agents.escrow_agent_orchestrator import EscrowAgentOrchestrator, EscrowError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class VerificationReportCreate(BaseModel):
    """Request model for submitting a verification report."""
    agent_id: str = Field(..., description="ID of the agent submitting the report")
    report_type: VerificationType = Field(..., description="Type of verification")
    findings: dict = Field(..., description="Verification findings")
    documents: List[str] = Field(default_factory=list, description="URLs to supporting documents")
    status: ReportStatus = Field(default=ReportStatus.NEEDS_REVIEW, description="Report status")


class VerificationTaskUpdate(BaseModel):
    """Request model for updating verification task status."""
    status: TaskStatus = Field(..., description="New task status")


class VerificationReportResponse(BaseModel):
    """Response model for verification report."""
    id: str
    task_id: Optional[str]
    agent_id: str
    report_type: str
    status: str
    findings: dict
    documents: List[str]
    submitted_at: str
    reviewed_at: Optional[str]
    reviewer_notes: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class VerificationTaskResponse(BaseModel):
    """Response model for verification task."""
    id: str
    transaction_id: str
    verification_type: str
    assigned_agent_id: str
    status: str
    deadline: str
    payment_amount: str
    report_id: Optional[str]
    assigned_at: str
    completed_at: Optional[str]
    created_at: str
    updated_at: str
    report: Optional[VerificationReportResponse]

    class Config:
        from_attributes = True


class VerificationTaskListResponse(BaseModel):
    """Response model for verification task list."""
    tasks: List[VerificationTaskResponse]
    total: int


@router.post("/transactions/{transaction_id}/verifications", response_model=VerificationReportResponse, status_code=201)
async def submit_verification_report(
    transaction_id: str,
    report_data: VerificationReportCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a verification report for a transaction.
    
    This endpoint:
    - Creates a verification report
    - Updates the associated task status
    - Releases payment if report is approved
    - Logs verification completion on blockchain
    - Sends notifications to all parties
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4
    """
    logger.info(
        f"Submitting verification report for transaction {transaction_id}",
        extra={
            "agent_id": report_data.agent_id,
            "report_type": report_data.report_type.value
        }
    )
    
    try:
        orchestrator = EscrowAgentOrchestrator(db)
        
        # Verify transaction exists
        transaction = await orchestrator.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        # Find the verification task
        task = db.query(VerificationTask).filter(
            VerificationTask.transaction_id == transaction_id,
            VerificationTask.verification_type == report_data.report_type
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Verification task not found for type {report_data.report_type.value}"
            )
        
        # Create verification report
        report = VerificationReport(
            task_id=task.id,
            agent_id=report_data.agent_id,
            report_type=report_data.report_type,
            status=report_data.status,
            findings=report_data.findings,
            documents=report_data.documents,
            submitted_at=datetime.utcnow()
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        # Process verification completion
        await orchestrator.process_verification_completion(
            transaction_id=transaction_id,
            verification_type=report_data.report_type,
            report=report
        )
        
        await orchestrator.close()
        
        return VerificationReportResponse(
            id=report.id,
            task_id=report.task_id,
            agent_id=report.agent_id,
            report_type=report.report_type.value,
            status=report.status.value,
            findings=report.findings,
            documents=report.documents or [],
            submitted_at=report.submitted_at.isoformat(),
            reviewed_at=report.reviewed_at.isoformat() if report.reviewed_at else None,
            reviewer_notes=report.reviewer_notes,
            created_at=report.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except EscrowError as e:
        logger.error(f"Failed to submit verification report: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error submitting verification report: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/transactions/{transaction_id}/verifications", response_model=VerificationTaskListResponse)
async def list_verification_tasks(
    transaction_id: str,
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    verification_type: Optional[VerificationType] = Query(None, description="Filter by verification type"),
    db: Session = Depends(get_db)
):
    """
    List verification tasks for a transaction.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4
    """
    logger.info(
        f"Listing verification tasks for transaction {transaction_id}",
        extra={
            "status": status.value if status else None,
            "verification_type": verification_type.value if verification_type else None
        }
    )
    
    try:
        # Verify transaction exists
        orchestrator = EscrowAgentOrchestrator(db)
        transaction = await orchestrator.get_transaction(transaction_id)
        await orchestrator.close()
        
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
        
        # Build query with filters
        query = db.query(VerificationTask).filter(
            VerificationTask.transaction_id == transaction_id
        )
        
        if status:
            query = query.filter(VerificationTask.status == status)
        if verification_type:
            query = query.filter(VerificationTask.verification_type == verification_type)
        
        tasks = query.all()
        
        return VerificationTaskListResponse(
            tasks=[
                VerificationTaskResponse(
                    id=task.id,
                    transaction_id=task.transaction_id,
                    verification_type=task.verification_type.value,
                    assigned_agent_id=task.assigned_agent_id,
                    status=task.status.value,
                    deadline=task.deadline.isoformat(),
                    payment_amount=str(task.payment_amount),
                    report_id=task.report_id,
                    assigned_at=task.assigned_at.isoformat(),
                    completed_at=task.completed_at.isoformat() if task.completed_at else None,
                    created_at=task.created_at.isoformat(),
                    updated_at=task.updated_at.isoformat(),
                    report=VerificationReportResponse(
                        id=task.report.id,
                        task_id=task.report.task_id,
                        agent_id=task.report.agent_id,
                        report_type=task.report.report_type.value,
                        status=task.report.status.value,
                        findings=task.report.findings or {},
                        documents=task.report.documents or [],
                        submitted_at=task.report.submitted_at.isoformat(),
                        reviewed_at=task.report.reviewed_at.isoformat() if task.report.reviewed_at else None,
                        reviewer_notes=task.report.reviewer_notes,
                        created_at=task.report.created_at.isoformat()
                    ) if task.report else None
                )
                for task in tasks
            ],
            total=len(tasks)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing verification tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/verifications/{verification_id}", response_model=VerificationTaskResponse)
async def get_verification_task(
    verification_id: str,
    db: Session = Depends(get_db)
):
    """
    Get verification task details by ID.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4
    """
    logger.info(f"Fetching verification task {verification_id}")
    
    try:
        task = db.query(VerificationTask).filter(
            VerificationTask.id == verification_id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Verification task {verification_id} not found")
        
        return VerificationTaskResponse(
            id=task.id,
            transaction_id=task.transaction_id,
            verification_type=task.verification_type.value,
            assigned_agent_id=task.assigned_agent_id,
            status=task.status.value,
            deadline=task.deadline.isoformat(),
            payment_amount=str(task.payment_amount),
            report_id=task.report_id,
            assigned_at=task.assigned_at.isoformat(),
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            report=VerificationReportResponse(
                id=task.report.id,
                task_id=task.report.task_id,
                agent_id=task.report.agent_id,
                report_type=task.report.report_type.value,
                status=task.report.status.value,
                findings=task.report.findings or {},
                documents=task.report.documents or [],
                submitted_at=task.report.submitted_at.isoformat(),
                reviewed_at=task.report.reviewed_at.isoformat() if task.report.reviewed_at else None,
                reviewer_notes=task.report.reviewer_notes,
                created_at=task.report.created_at.isoformat()
            ) if task.report else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching verification task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/verifications/{verification_id}", response_model=VerificationTaskResponse)
async def update_verification_status(
    verification_id: str,
    update_data: VerificationTaskUpdate,
    db: Session = Depends(get_db)
):
    """
    Update verification task status.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4
    """
    logger.info(
        f"Updating verification task {verification_id}",
        extra={"new_status": update_data.status.value}
    )
    
    try:
        task = db.query(VerificationTask).filter(
            VerificationTask.id == verification_id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Verification task {verification_id} not found")
        
        # Update status
        task.status = update_data.status
        
        # Update completed_at if status is COMPLETED
        if update_data.status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.utcnow()
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return VerificationTaskResponse(
            id=task.id,
            transaction_id=task.transaction_id,
            verification_type=task.verification_type.value,
            assigned_agent_id=task.assigned_agent_id,
            status=task.status.value,
            deadline=task.deadline.isoformat(),
            payment_amount=str(task.payment_amount),
            report_id=task.report_id,
            assigned_at=task.assigned_at.isoformat(),
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
            report=VerificationReportResponse(
                id=task.report.id,
                task_id=task.report.task_id,
                agent_id=task.report.agent_id,
                report_type=task.report.report_type.value,
                status=task.report.status.value,
                findings=task.report.findings or {},
                documents=task.report.documents or [],
                submitted_at=task.report.submitted_at.isoformat(),
                reviewed_at=task.report.reviewed_at.isoformat() if task.report.reviewed_at else None,
                reviewer_notes=task.report.reviewer_notes,
                created_at=task.report.created_at.isoformat()
            ) if task.report else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating verification task: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
