"""Verification workflow with DAG-based task scheduling and dependency resolution."""
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
import logging

from models.transaction import Transaction
from models.verification import VerificationType, TaskStatus, VerificationTask

logger = logging.getLogger(__name__)


@dataclass
class TaskDefinition:
    """Definition of a verification task with dependencies and configuration."""
    
    verification_type: VerificationType
    dependencies: List[VerificationType] = field(default_factory=list)
    deadline_days: int = 7
    payment_amount: Decimal = Decimal("0.00")
    agent_id: Optional[str] = None
    
    def __hash__(self):
        return hash(self.verification_type)


class WorkflowError(Exception):
    """Raised when workflow execution encounters an error."""
    pass


class CircularDependencyError(WorkflowError):
    """Raised when circular dependencies are detected in workflow."""
    pass


class VerificationWorkflow:
    """
    DAG-based verification workflow with parallel task execution and dependency resolution.
    
    Manages task scheduling, deadline tracking, and status monitoring for
    verification workflows in escrow transactions.
    """
    
    # Default task definitions
    DEFAULT_TASKS: Dict[VerificationType, TaskDefinition] = {
        VerificationType.TITLE_SEARCH: TaskDefinition(
            verification_type=VerificationType.TITLE_SEARCH,
            dependencies=[],
            deadline_days=5,
            payment_amount=Decimal("1200.00")
        ),
        VerificationType.INSPECTION: TaskDefinition(
            verification_type=VerificationType.INSPECTION,
            dependencies=[],
            deadline_days=7,
            payment_amount=Decimal("500.00")
        ),
        VerificationType.APPRAISAL: TaskDefinition(
            verification_type=VerificationType.APPRAISAL,
            dependencies=[VerificationType.INSPECTION],
            deadline_days=5,
            payment_amount=Decimal("400.00")
        ),
        VerificationType.LENDING: TaskDefinition(
            verification_type=VerificationType.LENDING,
            dependencies=[VerificationType.TITLE_SEARCH, VerificationType.APPRAISAL],
            deadline_days=10,
            payment_amount=Decimal("0.00")
        )
    }
    
    def __init__(
        self,
        transaction: Transaction,
        task_definitions: Optional[Dict[VerificationType, TaskDefinition]] = None
    ):
        """
        Initialize verification workflow.
        
        Args:
            transaction: The transaction to create workflow for
            task_definitions: Custom task definitions (uses defaults if not provided)
        """
        self.transaction = transaction
        self.task_definitions = task_definitions or self.DEFAULT_TASKS.copy()
        self._validate_dag()
        self._task_status: Dict[VerificationType, TaskStatus] = {}
        self._task_deadlines: Dict[VerificationType, datetime] = {}
    
    def _validate_dag(self) -> None:
        """
        Validate that task dependencies form a valid DAG (no cycles).
        
        Raises:
            CircularDependencyError: If circular dependencies are detected
        """
        visited: Set[VerificationType] = set()
        rec_stack: Set[VerificationType] = set()
        
        def has_cycle(task_type: VerificationType) -> bool:
            visited.add(task_type)
            rec_stack.add(task_type)
            
            task_def = self.task_definitions.get(task_type)
            if task_def:
                for dep in task_def.dependencies:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(task_type)
            return False
        
        for task_type in self.task_definitions.keys():
            if task_type not in visited:
                if has_cycle(task_type):
                    raise CircularDependencyError(
                        f"Circular dependency detected in workflow for task {task_type.value}"
                    )
    
    def get_executable_tasks(self) -> List[VerificationType]:
        """
        Get list of tasks that can be executed in parallel.
        
        Returns tasks whose dependencies are all completed.
        
        Returns:
            List of verification types that can be executed
        """
        executable = []
        
        for task_type, task_def in self.task_definitions.items():
            # Skip if already completed or in progress
            current_status = self._task_status.get(task_type)
            if current_status in [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS]:
                continue
            
            # Check if all dependencies are completed
            dependencies_met = all(
                self._task_status.get(dep) == TaskStatus.COMPLETED
                for dep in task_def.dependencies
            )
            
            if dependencies_met:
                executable.append(task_type)
        
        return executable
    
    def create_tasks(self, base_date: Optional[datetime] = None) -> List[VerificationTask]:
        """
        Create verification tasks for the transaction.
        
        Args:
            base_date: Base date for calculating deadlines (defaults to now)
            
        Returns:
            List of created VerificationTask instances
        """
        base_date = base_date or datetime.utcnow()
        tasks = []
        
        for task_type, task_def in self.task_definitions.items():
            # Calculate deadline based on dependencies
            deadline = self._calculate_deadline(task_type, base_date)
            
            task = VerificationTask(
                transaction_id=self.transaction.id,
                verification_type=task_type,
                assigned_agent_id=task_def.agent_id or f"agent_{task_type.value}",
                status=TaskStatus.ASSIGNED,
                deadline=deadline,
                payment_amount=task_def.payment_amount,
                assigned_at=datetime.utcnow()
            )
            
            tasks.append(task)
            self._task_status[task_type] = TaskStatus.ASSIGNED
            self._task_deadlines[task_type] = deadline
        
        return tasks
    
    def _calculate_deadline(
        self,
        task_type: VerificationType,
        base_date: datetime
    ) -> datetime:
        """
        Calculate deadline for a task based on dependencies.
        
        For tasks with dependencies, deadline is calculated from the latest
        dependency deadline plus the task's own deadline_days.
        
        Args:
            task_type: Type of verification task
            base_date: Base date for calculation
            
        Returns:
            Calculated deadline
        """
        task_def = self.task_definitions[task_type]
        
        if not task_def.dependencies:
            # No dependencies: deadline from base date
            return base_date + timedelta(days=task_def.deadline_days)
        
        # Has dependencies: find latest dependency deadline
        latest_dep_deadline = base_date
        for dep_type in task_def.dependencies:
            dep_deadline = self._task_deadlines.get(dep_type)
            if not dep_deadline:
                # Recursively calculate dependency deadline
                dep_deadline = self._calculate_deadline(dep_type, base_date)
                self._task_deadlines[dep_type] = dep_deadline
            
            if dep_deadline > latest_dep_deadline:
                latest_dep_deadline = dep_deadline
        
        # Add this task's deadline days to latest dependency
        return latest_dep_deadline + timedelta(days=task_def.deadline_days)
    
    def update_task_status(
        self,
        task_type: VerificationType,
        status: TaskStatus
    ) -> None:
        """
        Update status of a task.
        
        Args:
            task_type: Type of verification task
            status: New status
        """
        self._task_status[task_type] = status
        logger.info(
            f"Task {task_type.value} for transaction {self.transaction.id} "
            f"updated to status {status.value}"
        )
    
    def get_overdue_tasks(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get list of tasks that have exceeded their deadlines.
        
        Args:
            current_time: Current time for comparison (defaults to now)
            
        Returns:
            List of overdue task information
        """
        current_time = current_time or datetime.utcnow()
        overdue = []
        
        for task_type, deadline in self._task_deadlines.items():
            status = self._task_status.get(task_type)
            
            # Only check non-completed tasks
            if status != TaskStatus.COMPLETED and current_time > deadline:
                days_overdue = (current_time - deadline).days
                overdue.append({
                    "task_type": task_type,
                    "deadline": deadline,
                    "days_overdue": days_overdue,
                    "status": status,
                    "escalation_required": days_overdue > 2
                })
        
        return overdue
    
    def get_task_status(self, task_type: VerificationType) -> Optional[TaskStatus]:
        """Get current status of a task."""
        return self._task_status.get(task_type)
    
    def is_workflow_complete(self) -> bool:
        """Check if all tasks in workflow are completed."""
        return all(
            status == TaskStatus.COMPLETED
            for status in self._task_status.values()
        )
    
    def get_workflow_progress(self) -> Dict[str, Any]:
        """
        Get workflow progress summary.
        
        Returns:
            Dictionary with progress metrics
        """
        total_tasks = len(self.task_definitions)
        completed_tasks = sum(
            1 for status in self._task_status.values()
            if status == TaskStatus.COMPLETED
        )
        in_progress_tasks = sum(
            1 for status in self._task_status.values()
            if status == TaskStatus.IN_PROGRESS
        )
        failed_tasks = sum(
            1 for status in self._task_status.values()
            if status == TaskStatus.FAILED
        )
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "failed_tasks": failed_tasks,
            "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "is_complete": self.is_workflow_complete()
        }
    
    def get_dependency_chain(self, task_type: VerificationType) -> List[VerificationType]:
        """
        Get full dependency chain for a task (topologically sorted).
        
        Args:
            task_type: Type of verification task
            
        Returns:
            List of task types in dependency order
        """
        visited: Set[VerificationType] = set()
        chain: List[VerificationType] = []
        
        def visit(t_type: VerificationType):
            if t_type in visited:
                return
            visited.add(t_type)
            
            task_def = self.task_definitions.get(t_type)
            if task_def:
                for dep in task_def.dependencies:
                    visit(dep)
            
            chain.append(t_type)
        
        visit(task_type)
        return chain
