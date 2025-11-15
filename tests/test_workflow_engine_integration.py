"""Integration tests for workflow engine and state machine."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from workflows.state_machine import TransactionStateMachine
from workflows.verification_workflow import VerificationWorkflow, Task
from workflows.workflow_engine import WorkflowEngine
from models.transaction import Transaction, TransactionState
from models.verification import VerificationTask, VerificationType, TaskStatus, VerificationReport, ReportStatus


@pytest.fixture
def sample_transaction(test_db):
    """Create a sample transaction for testing."""
    transaction = Transaction(
        buyer_agent_id="buyer_agent_001",
        seller_agent_id="seller_agent_001",
        property_id="prop_123",
        earnest_money=Decimal("10000.00"),
        total_purchase_price=Decimal("385000.00"),
        state=TransactionState.INITIATED,
        target_closing_date=datetime.utcnow() + timedelta(days=30)
    )
    test_db.add(transaction)
    test_db.commit()
    test_db.refresh(transaction)
    return transaction


class TestTransactionStateMachine:
    """Test transaction state machine transitions."""
    
    def test_initial_state(self, test_db, sample_transaction):
        """Test initial transaction state."""
        state_machine = TransactionStateMachine(sample_transaction)
        
        assert state_machine.current_state == TransactionState.INITIATED
    
    def test_transition_to_funded(self, test_db, sample_transaction):
        """Test transition from INITIATED to FUNDED."""
        state_machine = TransactionStateMachine(sample_transaction)
        
        # Transition to funded
        state_machine.transition_to(TransactionState.FUNDED)
        test_db.commit()
        test_db.refresh(sample_transaction)
        
        assert sample_transaction.state == TransactionState.FUNDED
    
    def test_transition_to_verification_in_progress(self, test_db, sample_transaction):
        """Test transition to VERIFICATION_IN_PROGRESS."""
        sample_transaction.state = TransactionState.FUNDED
        test_db.commit()
        
        state_machine = TransactionStateMachine(sample_transaction)
        state_machine.transition_to(TransactionState.VERIFICATION_IN_PROGRESS)
        test_db.commit()
        test_db.refresh(sample_transaction)
        
        assert sample_transaction.state == TransactionState.VERIFICATION_IN_PROGRESS
    
    def test_transition_to_verification_complete(self, test_db, sample_transaction):
        """Test transition to VERIFICATION_COMPLETE."""
        sample_transaction.state = TransactionState.VERIFICATION_IN_PROGRESS
        test_db.commit()
        
        state_machine = TransactionStateMachine(sample_transaction)
        state_machine.transition_to(TransactionState.VERIFICATION_COMPLETE)
        test_db.commit()
        test_db.refresh(sample_transaction)
        
        assert sample_transaction.state == TransactionState.VERIFICATION_COMPLETE
    
    def test_transition_to_settlement_pending(self, test_db, sample_transaction):
        """Test transition to SETTLEMENT_PENDING."""
        sample_transaction.state = TransactionState.VERIFICATION_COMPLETE
        test_db.commit()
        
        state_machine = TransactionStateMachine(sample_transaction)
        state_machine.transition_to(TransactionState.SETTLEMENT_PENDING)
        test_db.commit()
        test_db.refresh(sample_transaction)
        
        assert sample_transaction.state == TransactionState.SETTLEMENT_PENDING
    
    def test_transition_to_settled(self, test_db, sample_transaction):
        """Test transition to SETTLED."""
        sample_transaction.state = TransactionState.SETTLEMENT_PENDING
        test_db.commit()
        
        state_machine = TransactionStateMachine(sample_transaction)
        state_machine.transition_to(TransactionState.SETTLED)
        test_db.commit()
        test_db.refresh(sample_transaction)
        
        assert sample_transaction.state == TransactionState.SETTLED
        assert sample_transaction.actual_closing_date is not None
    
    def test_transition_to_disputed(self, test_db, sample_transaction):
        """Test transition to DISPUTED from any state."""
        sample_transaction.state = TransactionState.VERIFICATION_IN_PROGRESS
        test_db.commit()
        
        state_machine = TransactionStateMachine(sample_transaction)
        state_machine.transition_to(TransactionState.DISPUTED)
        test_db.commit()
        test_db.refresh(sample_transaction)
        
        assert sample_transaction.state == TransactionState.DISPUTED
    
    def test_invalid_transition(self, test_db, sample_transaction):
        """Test invalid state transition."""
        state_machine = TransactionStateMachine(sample_transaction)
        
        # Cannot go directly from INITIATED to SETTLED
        with pytest.raises(ValueError, match="Invalid state transition"):
            state_machine.transition_to(TransactionState.SETTLED)
    
    def test_state_change_event_emission(self, test_db, sample_transaction):
        """Test state change event emission."""
        state_machine = TransactionStateMachine(sample_transaction)
        
        events = []
        def event_handler(event):
            events.append(event)
        
        state_machine.on_state_change(event_handler)
        state_machine.transition_to(TransactionState.FUNDED)
        
        assert len(events) == 1
        assert events[0]["from_state"] == TransactionState.INITIATED
        assert events[0]["to_state"] == TransactionState.FUNDED


class TestVerificationWorkflow:
    """Test verification workflow with task dependencies."""
    
    def test_create_workflow_with_tasks(self, sample_transaction):
        """Test creating workflow with verification tasks."""
        workflow = VerificationWorkflow(sample_transaction)
        
        assert "title_search" in workflow.tasks
        assert "inspection" in workflow.tasks
        assert "appraisal" in workflow.tasks
        assert "lending" in workflow.tasks
    
    def test_task_dependencies(self, sample_transaction):
        """Test task dependency resolution."""
        workflow = VerificationWorkflow(sample_transaction)
        
        # Appraisal depends on inspection
        appraisal_task = workflow.tasks["appraisal"]
        assert "inspection" in appraisal_task.dependencies
        
        # Lending depends on title_search and appraisal
        lending_task = workflow.tasks["lending"]
        assert "title_search" in lending_task.dependencies
        assert "appraisal" in lending_task.dependencies
    
    def test_parallel_task_execution(self, sample_transaction):
        """Test identifying tasks that can run in parallel."""
        workflow = VerificationWorkflow(sample_transaction)
        
        # Title search and inspection have no dependencies, can run in parallel
        ready_tasks = workflow.get_ready_tasks()
        
        assert "title_search" in ready_tasks
        assert "inspection" in ready_tasks
        assert "appraisal" not in ready_tasks  # Depends on inspection
        assert "lending" not in ready_tasks  # Depends on title_search and appraisal
    
    def test_task_completion_unlocks_dependent_tasks(self, sample_transaction):
        """Test that completing a task unlocks dependent tasks."""
        workflow = VerificationWorkflow(sample_transaction)
        
        # Complete inspection
        workflow.mark_task_complete("inspection")
        
        # Now appraisal should be ready
        ready_tasks = workflow.get_ready_tasks()
        assert "appraisal" in ready_tasks
    
    def test_all_tasks_complete(self, sample_transaction):
        """Test checking if all tasks are complete."""
        workflow = VerificationWorkflow(sample_transaction)
        
        assert not workflow.is_complete()
        
        # Complete all tasks
        workflow.mark_task_complete("title_search")
        workflow.mark_task_complete("inspection")
        workflow.mark_task_complete("appraisal")
        workflow.mark_task_complete("lending")
        
        assert workflow.is_complete()
    
    def test_deadline_tracking(self, sample_transaction):
        """Test deadline tracking for tasks."""
        workflow = VerificationWorkflow(sample_transaction)
        
        title_task = workflow.tasks["title_search"]
        assert title_task.deadline_days == 5
        
        # Check if task is overdue
        title_task.assigned_at = datetime.utcnow() - timedelta(days=6)
        assert workflow.is_task_overdue("title_search")


class TestWorkflowEngine:
    """Test workflow engine orchestration."""
    
    @pytest.mark.asyncio
    async def test_create_workflow_for_transaction(self, test_db, sample_transaction):
        """Test creating workflow for transaction."""
        engine = WorkflowEngine()
        
        workflow = await engine.create_workflow(sample_transaction.id)
        
        assert workflow is not None
        assert workflow.transaction.id == sample_transaction.id
        
        # Verify tasks created in database
        tasks = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id
        ).all()
        assert len(tasks) == 4  # title_search, inspection, appraisal, lending
    
    @pytest.mark.asyncio
    async def test_assign_tasks_to_agents(self, test_db, sample_transaction):
        """Test assigning tasks to verification agents."""
        engine = WorkflowEngine()
        
        workflow = await engine.create_workflow(sample_transaction.id)
        
        # Verify task assignments
        title_task = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id,
            verification_type=VerificationType.TITLE_SEARCH
        ).first()
        
        assert title_task is not None
        assert title_task.status == TaskStatus.ASSIGNED
        assert title_task.payment_amount == Decimal("1200.00")
    
    @pytest.mark.asyncio
    async def test_process_task_completion(self, test_db, sample_transaction):
        """Test processing task completion."""
        engine = WorkflowEngine()
        
        # Create workflow and tasks
        workflow = await engine.create_workflow(sample_transaction.id)
        
        # Get title search task
        title_task = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id,
            verification_type=VerificationType.TITLE_SEARCH
        ).first()
        
        # Create report
        report = VerificationReport(
            task_id=title_task.id,
            agent_id="title_agent_001",
            report_type=VerificationType.TITLE_SEARCH,
            status=ReportStatus.APPROVED,
            findings={"title_clear": True},
            documents=["https://example.com/title_report.pdf"]
        )
        test_db.add(report)
        test_db.commit()
        
        # Process completion
        with patch('workflows.workflow_engine.BlockchainLogger') as mock_logger:
            mock_logger_instance = AsyncMock()
            mock_logger.return_value = mock_logger_instance
            
            await engine.process_task_completion(title_task.id, report.id)
        
        # Verify task marked complete
        test_db.refresh(title_task)
        assert title_task.status == TaskStatus.COMPLETED
        assert title_task.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_automatic_retry_on_task_failure(self, test_db, sample_transaction):
        """Test automatic retry on task failure."""
        engine = WorkflowEngine()
        
        workflow = await engine.create_workflow(sample_transaction.id)
        
        # Get inspection task
        inspection_task = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id,
            verification_type=VerificationType.INSPECTION
        ).first()
        
        # Simulate task failure
        inspection_task.status = TaskStatus.FAILED
        test_db.commit()
        
        # Retry task
        await engine.retry_task(inspection_task.id)
        
        test_db.refresh(inspection_task)
        assert inspection_task.status == TaskStatus.ASSIGNED
    
    @pytest.mark.asyncio
    async def test_deadline_escalation(self, test_db, sample_transaction):
        """Test deadline tracking and escalation."""
        engine = WorkflowEngine()
        
        workflow = await engine.create_workflow(sample_transaction.id)
        
        # Get title task and set it overdue
        title_task = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id,
            verification_type=VerificationType.TITLE_SEARCH
        ).first()
        
        title_task.deadline = datetime.utcnow() - timedelta(days=1)
        test_db.commit()
        
        # Check for overdue tasks
        with patch('workflows.workflow_engine.NotificationEngine') as mock_notif:
            mock_notif_instance = AsyncMock()
            mock_notif.return_value = mock_notif_instance
            
            overdue_tasks = await engine.check_overdue_tasks(sample_transaction.id)
            
            assert len(overdue_tasks) == 1
            assert overdue_tasks[0].id == title_task.id
    
    @pytest.mark.asyncio
    async def test_workflow_state_caching(self, test_db, sample_transaction):
        """Test workflow state caching in Redis."""
        engine = WorkflowEngine()
        
        with patch('workflows.workflow_engine.WorkflowCache') as mock_cache:
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            workflow = await engine.create_workflow(sample_transaction.id)
            
            # Verify cache was updated
            mock_cache_instance.set_workflow_state.assert_called()
    
    @pytest.mark.asyncio
    async def test_parallel_task_execution(self, test_db, sample_transaction):
        """Test parallel execution of independent tasks."""
        engine = WorkflowEngine()
        
        workflow = await engine.create_workflow(sample_transaction.id)
        
        # Get title and inspection tasks (no dependencies)
        title_task = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id,
            verification_type=VerificationType.TITLE_SEARCH
        ).first()
        
        inspection_task = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id,
            verification_type=VerificationType.INSPECTION
        ).first()
        
        # Both should be in ASSIGNED state (ready to execute)
        assert title_task.status == TaskStatus.ASSIGNED
        assert inspection_task.status == TaskStatus.ASSIGNED
        
        # Simulate parallel execution
        title_task.status = TaskStatus.IN_PROGRESS
        inspection_task.status = TaskStatus.IN_PROGRESS
        test_db.commit()
        
        # Both can be in progress simultaneously
        in_progress_tasks = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id,
            status=TaskStatus.IN_PROGRESS
        ).all()
        
        assert len(in_progress_tasks) == 2
    
    @pytest.mark.asyncio
    async def test_dependent_task_waits_for_prerequisite(self, test_db, sample_transaction):
        """Test that dependent tasks wait for prerequisites."""
        engine = WorkflowEngine()
        
        workflow = await engine.create_workflow(sample_transaction.id)
        
        # Appraisal should not start until inspection is complete
        appraisal_task = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id,
            verification_type=VerificationType.APPRAISAL
        ).first()
        
        inspection_task = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id,
            verification_type=VerificationType.INSPECTION
        ).first()
        
        # Check if appraisal can start
        can_start = await engine.can_start_task(appraisal_task.id)
        assert not can_start  # Should wait for inspection
        
        # Complete inspection
        inspection_task.status = TaskStatus.COMPLETED
        test_db.commit()
        
        # Now appraisal can start
        can_start = await engine.can_start_task(appraisal_task.id)
        assert can_start
    
    @pytest.mark.asyncio
    async def test_workflow_completion_triggers_settlement(self, test_db, sample_transaction):
        """Test that workflow completion triggers settlement."""
        engine = WorkflowEngine()
        
        workflow = await engine.create_workflow(sample_transaction.id)
        
        # Complete all tasks
        tasks = test_db.query(VerificationTask).filter_by(
            transaction_id=sample_transaction.id
        ).all()
        
        for task in tasks:
            task.status = TaskStatus.COMPLETED
        test_db.commit()
        
        # Check workflow completion
        is_complete = await engine.is_workflow_complete(sample_transaction.id)
        assert is_complete
        
        # Verify transaction state updated
        test_db.refresh(sample_transaction)
        assert sample_transaction.state == TransactionState.VERIFICATION_COMPLETE
