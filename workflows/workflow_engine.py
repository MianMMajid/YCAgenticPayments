"""Workflow execution engine for orchestrating verification workflows."""
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from decimal import Decimal
import logging
import json

from models.transaction import Transaction
from models.verification import (
    VerificationTask,
    VerificationType,
    TaskStatus,
    VerificationReport,
    ReportStatus
)
from models.database import get_db
from workflows.verification_workflow import VerificationWorkflow, TaskDefinition
from services.workflow_cache import workflow_cache

logger = logging.getLogger(__name__)


class WorkflowExecutionError(Exception):
    """Raised when workflow execution encounters an error."""
    pass


class WorkflowEngine:
    """
    Orchestrates verification workflows with task assignment, completion handling,
    and automatic retry logic.
    
    Manages workflow state caching in Redis for performance optimization.
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds
    
    def __init__(self):
        """Initialize workflow engine."""
        self._task_handlers: Dict[VerificationType, Callable] = {}
        self._completion_callbacks: List[Callable] = []
        self._cache = workflow_cache
    
    def register_task_handler(
        self,
        verification_type: VerificationType,
        handler: Callable
    ) -> None:
        """
        Register a handler for a specific verification type.
        
        Args:
            verification_type: Type of verification
            handler: Async function to handle task execution
        """
        self._task_handlers[verification_type] = handler
        logger.info(f"Registered handler for {verification_type.value}")
    
    def register_completion_callback(self, callback: Callable) -> None:
        """
        Register a callback to be invoked when workflow completes.
        
        Args:
            callback: Async function to call on workflow completion
        """
        self._completion_callbacks.append(callback)
    
    async def create_workflow(
        self,
        transaction: Transaction,
        task_definitions: Optional[Dict[VerificationType, TaskDefinition]] = None
    ) -> VerificationWorkflow:
        """
        Create a new verification workflow for a transaction.
        
        Args:
            transaction: Transaction to create workflow for
            task_definitions: Optional custom task definitions
            
        Returns:
            Created VerificationWorkflow instance
        """
        workflow = VerificationWorkflow(transaction, task_definitions)
        
        # Create tasks in database
        tasks = workflow.create_tasks()
        db = next(get_db())
        try:
            for task in tasks:
                db.add(task)
            db.commit()
            
            # Refresh to get IDs
            for task in tasks:
                db.refresh(task)
            
            logger.info(
                f"Created workflow with {len(tasks)} tasks for transaction {transaction.id}"
            )
            
            # Cache workflow state using workflow_cache service
            workflow_data = self._serialize_workflow(workflow)
            self._cache.cache_workflow_state(transaction.id, workflow_data)
            
            return workflow
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create workflow: {e}")
            raise WorkflowExecutionError(f"Failed to create workflow: {e}")
        finally:
            db.close()
    
    async def assign_task(
        self,
        task: VerificationTask,
        agent_id: str
    ) -> None:
        """
        Assign a verification task to an agent.
        
        Args:
            task: Task to assign
            agent_id: ID of agent to assign to
        """
        db = next(get_db())
        try:
            task.assigned_agent_id = agent_id
            task.status = TaskStatus.ASSIGNED
            task.assigned_at = datetime.utcnow()
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            logger.info(
                f"Assigned task {task.id} ({task.verification_type.value}) "
                f"to agent {agent_id}"
            )
            
            # Invalidate workflow cache
            self._cache.invalidate_transaction_cache(task.transaction_id)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to assign task: {e}")
            raise WorkflowExecutionError(f"Failed to assign task: {e}")
        finally:
            db.close()
    
    async def execute_task(
        self,
        task: VerificationTask,
        retry_count: int = 0
    ) -> Optional[VerificationReport]:
        """
        Execute a verification task with automatic retry logic.
        
        Args:
            task: Task to execute
            retry_count: Current retry attempt (for internal use)
            
        Returns:
            VerificationReport if successful, None otherwise
        """
        handler = self._task_handlers.get(task.verification_type)
        if not handler:
            logger.warning(
                f"No handler registered for {task.verification_type.value}, "
                f"task {task.id} will remain assigned"
            )
            return None
        
        try:
            # Update task status to in progress
            await self._update_task_status(task, TaskStatus.IN_PROGRESS)
            
            # Execute handler
            logger.info(f"Executing task {task.id} ({task.verification_type.value})")
            report = await handler(task)
            
            # Update task status to completed
            await self._update_task_status(task, TaskStatus.COMPLETED)
            task.completed_at = datetime.utcnow()
            
            return report
            
        except Exception as e:
            logger.error(
                f"Task {task.id} execution failed (attempt {retry_count + 1}): {e}"
            )
            
            # Retry with exponential backoff
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAYS[min(retry_count, len(self.RETRY_DELAYS) - 1)]
                logger.info(f"Retrying task {task.id} in {delay} seconds...")
                await asyncio.sleep(delay)
                return await self.execute_task(task, retry_count + 1)
            else:
                # Max retries exceeded
                logger.error(f"Task {task.id} failed after {self.MAX_RETRIES} retries")
                await self._update_task_status(task, TaskStatus.FAILED)
                return None
    
    async def handle_task_completion(
        self,
        task: VerificationTask,
        report: VerificationReport
    ) -> None:
        """
        Handle completion of a verification task.
        
        Args:
            task: Completed task
            report: Verification report submitted
        """
        db = next(get_db())
        try:
            # Link report to task
            task.report_id = report.id
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            logger.info(
                f"Task {task.id} completed with report {report.id} "
                f"(status: {report.status.value})"
            )
            
            # Invalidate workflow cache
            self._cache.invalidate_transaction_cache(task.transaction_id)
            
            # Check if workflow is complete
            workflow = await self._get_workflow(task.transaction_id)
            if workflow and workflow.is_workflow_complete():
                logger.info(f"Workflow complete for transaction {task.transaction_id}")
                await self._trigger_completion_callbacks(task.transaction_id, workflow)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to handle task completion: {e}")
            raise WorkflowExecutionError(f"Failed to handle task completion: {e}")
        finally:
            db.close()
    
    async def execute_parallel_tasks(
        self,
        transaction_id: str
    ) -> List[Optional[VerificationReport]]:
        """
        Execute all tasks that can run in parallel based on dependencies.
        
        Args:
            transaction_id: ID of transaction
            
        Returns:
            List of verification reports from executed tasks
        """
        workflow = await self._get_workflow(transaction_id)
        if not workflow:
            raise WorkflowExecutionError(f"Workflow not found for transaction {transaction_id}")
        
        # Get executable tasks
        executable_types = workflow.get_executable_tasks()
        if not executable_types:
            logger.info(f"No executable tasks for transaction {transaction_id}")
            return []
        
        # Get task instances from database
        db = next(get_db())
        try:
            tasks = db.query(VerificationTask).filter(
                VerificationTask.transaction_id == transaction_id,
                VerificationTask.verification_type.in_(executable_types),
                VerificationTask.status == TaskStatus.ASSIGNED
            ).all()
            
            if not tasks:
                return []
            
            logger.info(
                f"Executing {len(tasks)} parallel tasks for transaction {transaction_id}"
            )
            
            # Execute tasks in parallel
            results = await asyncio.gather(
                *[self.execute_task(task) for task in tasks],
                return_exceptions=True
            )
            
            # Filter out exceptions and None values
            reports = [r for r in results if isinstance(r, VerificationReport)]
            
            return reports
        finally:
            db.close()
    
    async def check_deadlines(
        self,
        transaction_id: str
    ) -> List[Dict[str, Any]]:
        """
        Check for overdue tasks and return escalation information.
        
        Args:
            transaction_id: ID of transaction
            
        Returns:
            List of overdue task information
        """
        workflow = await self._get_workflow(transaction_id)
        if not workflow:
            return []
        
        overdue_tasks = workflow.get_overdue_tasks()
        
        if overdue_tasks:
            logger.warning(
                f"Found {len(overdue_tasks)} overdue tasks for transaction {transaction_id}"
            )
        
        return overdue_tasks
    
    async def get_workflow_progress(
        self,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Get workflow progress for a transaction.
        
        Args:
            transaction_id: ID of transaction
            
        Returns:
            Progress information
        """
        workflow = await self._get_workflow(transaction_id)
        if not workflow:
            return {
                "error": "Workflow not found",
                "transaction_id": transaction_id
            }
        
        progress = workflow.get_workflow_progress()
        progress["transaction_id"] = transaction_id
        
        return progress
    
    async def _update_task_status(
        self,
        task: VerificationTask,
        status: TaskStatus
    ) -> None:
        """Update task status in database and cache."""
        db = next(get_db())
        try:
            task.status = status
            task.updated_at = datetime.utcnow()
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # Invalidate workflow cache
            self._cache.invalidate_transaction_cache(task.transaction_id)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update task status: {e}")
            raise
        finally:
            db.close()
    
    async def _get_workflow(
        self,
        transaction_id: str
    ) -> Optional[VerificationWorkflow]:
        """
        Get workflow from cache or reconstruct from database.
        
        Args:
            transaction_id: ID of transaction
            
        Returns:
            VerificationWorkflow instance or None
        """
        # Try cache first
        cached_data = self._cache.get_workflow_state(transaction_id)
        
        if cached_data:
            logger.debug(f"Workflow cache hit for transaction {transaction_id}")
            workflow = self._deserialize_workflow(cached_data)
            if workflow:
                return workflow
        
        # Reconstruct from database
        db = next(get_db())
        try:
            from models.transaction import Transaction
            
            transaction = db.query(Transaction).filter(
                Transaction.id == transaction_id
            ).first()
            
            if not transaction:
                return None
            
            # Get tasks
            tasks = db.query(VerificationTask).filter(
                VerificationTask.transaction_id == transaction_id
            ).all()
            
            if not tasks:
                return None
            
            # Reconstruct workflow
            workflow = VerificationWorkflow(transaction)
            
            # Update workflow state from tasks
            for task in tasks:
                workflow.update_task_status(task.verification_type, task.status)
                workflow._task_deadlines[task.verification_type] = task.deadline
            
            # Cache workflow
            workflow_data = self._serialize_workflow(workflow)
            self._cache.cache_workflow_state(transaction_id, workflow_data)
            
            return workflow
        finally:
            db.close()
    
    def _serialize_workflow(self, workflow: VerificationWorkflow) -> Dict[str, Any]:
        """Serialize workflow state for caching."""
        return {
            "transaction_id": workflow.transaction.id,
            "task_status": {
                k.value: v.value for k, v in workflow._task_status.items()
            },
            "task_deadlines": {
                k.value: v.isoformat() for k, v in workflow._task_deadlines.items()
            }
        }
    
    def _deserialize_workflow(self, cached_data: Dict[str, Any]) -> Optional[VerificationWorkflow]:
        """Deserialize workflow from cached data."""
        try:
            # This is a simplified deserialization
            # In production, you'd want to fully reconstruct the workflow
            # For now, we'll return None to force database reconstruction
            return None
        except Exception as e:
            logger.error(f"Failed to deserialize workflow: {e}")
            return None
    
    async def _trigger_completion_callbacks(
        self,
        transaction_id: str,
        workflow: VerificationWorkflow
    ) -> None:
        """Trigger all registered completion callbacks."""
        for callback in self._completion_callbacks:
            try:
                await callback(transaction_id, workflow)
            except Exception as e:
                logger.error(f"Completion callback failed: {e}")


# Global workflow engine instance
workflow_engine = WorkflowEngine()
