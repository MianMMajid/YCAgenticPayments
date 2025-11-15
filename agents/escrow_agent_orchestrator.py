"""Escrow Agent Orchestrator for managing real estate transactions."""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
import uuid

from sqlalchemy.orm import Session

from models.transaction import Transaction, TransactionState
from models.verification import (
    VerificationTask,
    VerificationType,
    TaskStatus,
    VerificationReport,
    ReportStatus
)
from models.payment import Payment, PaymentType, PaymentStatus
from models.settlement import Settlement
from services.smart_contract_wallet_manager import SmartContractWalletManager, WalletManagerError
from services.blockchain_logger import BlockchainLogger, EventType
from services.agentic_stripe_client import Milestone
from services.workflow_cache import workflow_cache
from workflows.state_machine import TransactionStateMachine, StateTransitionError
from workflows.workflow_engine import WorkflowEngine, workflow_engine
from workflows.verification_workflow import VerificationWorkflow


logger = logging.getLogger(__name__)


class EscrowError(Exception):
    """Base exception for escrow operations."""
    pass


class EscrowAgentOrchestrator:
    """
    Central orchestrator for escrow transaction lifecycle management.
    
    Coordinates between buyer agents, seller agents, verification agents,
    and manages milestone-based fund releases through smart contract wallets.
    """
    
    # Default verification task deadlines (in days)
    DEFAULT_DEADLINES = {
        VerificationType.TITLE_SEARCH: 5,
        VerificationType.INSPECTION: 7,
        VerificationType.APPRAISAL: 5,
        VerificationType.LENDING: 10
    }
    
    # Default payment amounts for verification agents
    DEFAULT_PAYMENT_AMOUNTS = {
        VerificationType.TITLE_SEARCH: Decimal("1200.00"),
        VerificationType.INSPECTION: Decimal("500.00"),
        VerificationType.APPRAISAL: Decimal("400.00"),
        VerificationType.LENDING: Decimal("0.00")  # Lender paid separately
    }
    
    def __init__(
        self,
        db: Session,
        wallet_manager: Optional[SmartContractWalletManager] = None,
        blockchain_logger: Optional[BlockchainLogger] = None,
        workflow_engine: Optional[WorkflowEngine] = None
    ):
        """
        Initialize the Escrow Agent Orchestrator.
        
        Args:
            db: Database session
            wallet_manager: Smart contract wallet manager (creates new if not provided)
            blockchain_logger: Blockchain logger (creates new if not provided)
            workflow_engine: Workflow engine (uses global instance if not provided)
        """
        self.db = db
        self.wallet_manager = wallet_manager or SmartContractWalletManager(db)
        self.blockchain_logger = blockchain_logger or BlockchainLogger()
        self.workflow_engine = workflow_engine or workflow_engine
        self.cache = workflow_cache
    
    async def initiate_transaction(
        self,
        buyer_agent_id: str,
        seller_agent_id: str,
        property_id: str,
        earnest_money: Decimal,
        total_purchase_price: Decimal,
        target_closing_date: datetime,
        transaction_metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Initiate a new escrow transaction with earnest money deposit.
        
        This method:
        1. Creates a new transaction record
        2. Creates a smart contract wallet
        3. Deposits earnest money into the wallet
        4. Logs transaction initiation on blockchain
        5. Transitions transaction to FUNDED state
        
        Args:
            buyer_agent_id: ID of the buyer's agent
            seller_agent_id: ID of the seller's agent
            property_id: ID of the property
            earnest_money: Earnest money deposit amount
            total_purchase_price: Total purchase price of the property
            target_closing_date: Target date for closing
            transaction_metadata: Additional transaction metadata
        
        Returns:
            Created Transaction entity
        
        Raises:
            EscrowError: If transaction initiation fails
        """
        logger.info(
            f"Initiating transaction for property {property_id}",
            extra={
                "buyer_agent_id": buyer_agent_id,
                "seller_agent_id": seller_agent_id,
                "earnest_money": str(earnest_money),
                "total_purchase_price": str(total_purchase_price)
            }
        )
        
        try:
            # Create transaction record
            transaction = Transaction(
                id=str(uuid.uuid4()),
                buyer_agent_id=buyer_agent_id,
                seller_agent_id=seller_agent_id,
                property_id=property_id,
                earnest_money=earnest_money,
                total_purchase_price=total_purchase_price,
                state=TransactionState.INITIATED,
                initiated_at=datetime.utcnow(),
                target_closing_date=target_closing_date,
                transaction_metadata=transaction_metadata or {}
            )
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            logger.info(f"Transaction created: {transaction.id}")
            
            # Log transaction initiation on blockchain
            await self.blockchain_logger.log_transaction_event(
                transaction_id=transaction.id,
                event_type=EventType.TRANSACTION_INITIATED,
                event_data={
                    "buyer_agent_id": buyer_agent_id,
                    "seller_agent_id": seller_agent_id,
                    "property_id": property_id,
                    "earnest_money": str(earnest_money),
                    "total_purchase_price": str(total_purchase_price),
                    "target_closing_date": target_closing_date.isoformat()
                },
                db=self.db,
                async_processing=False
            )
            
            # Create smart contract wallet and deposit earnest money
            wallet_details = await self.wallet_manager.create_wallet(
                transaction=transaction,
                initial_deposit=earnest_money
            )
            
            logger.info(
                f"Wallet created for transaction {transaction.id}: {wallet_details.wallet_id}"
            )
            
            # Log earnest money deposit on blockchain
            await self.blockchain_logger.log_transaction_event(
                transaction_id=transaction.id,
                event_type=EventType.EARNEST_MONEY_DEPOSITED,
                event_data={
                    "wallet_id": wallet_details.wallet_id,
                    "amount": str(earnest_money),
                    "balance": str(wallet_details.balance)
                },
                db=self.db,
                async_processing=False
            )
            
            # Transition to FUNDED state
            state_machine = TransactionStateMachine(transaction)
            await state_machine.transition_to(
                TransactionState.FUNDED,
                context={"earnest_money_deposited": True},
                persist=True
            )
            
            logger.info(
                f"Transaction {transaction.id} initiated successfully and funded",
                extra={
                    "transaction_id": transaction.id,
                    "wallet_id": wallet_details.wallet_id,
                    "state": transaction.state.value
                }
            )
            
            # Cache transaction state
            transaction_data = self._serialize_transaction(transaction)
            self.cache.cache_transaction_state(transaction.id, transaction_data)
            
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to initiate transaction: {str(e)}")
            self.db.rollback()
            raise EscrowError(f"Transaction initiation failed: {str(e)}")

    
    async def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """
        Get transaction by ID.
        
        Args:
            transaction_id: Transaction identifier
        
        Returns:
            Transaction entity or None if not found
        """
        return self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
    
    async def get_transaction_state(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get comprehensive transaction state including wallet and workflow status.
        Uses caching with 5-minute TTL for performance.
        
        Args:
            transaction_id: Transaction identifier
        
        Returns:
            Dictionary with transaction state information
        
        Raises:
            EscrowError: If transaction not found
        """
        # Try cache first
        cached_state = self.cache.get_transaction_state(transaction_id)
        if cached_state:
            logger.debug(f"Transaction state cache hit: {transaction_id}")
            return cached_state
        
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            raise EscrowError(f"Transaction {transaction_id} not found")
        
        # Get wallet state
        wallet_state = None
        if transaction.wallet_id:
            try:
                wallet_state = await self.wallet_manager.get_wallet_state(transaction)
            except Exception as e:
                logger.warning(f"Failed to get wallet state: {str(e)}")
        
        # Get workflow progress
        workflow_progress = await self.workflow_engine.get_workflow_progress(transaction_id)
        
        # Get verification tasks
        tasks = self.db.query(VerificationTask).filter(
            VerificationTask.transaction_id == transaction_id
        ).all()
        
        # Get payments
        payments = self.db.query(Payment).filter(
            Payment.transaction_id == transaction_id
        ).all()
        
        # Get settlement
        settlement = self.db.query(Settlement).filter(
            Settlement.transaction_id == transaction_id
        ).first()
        
        state_data = {
            "transaction_id": transaction.id,
            "state": transaction.state.value,
            "buyer_agent_id": transaction.buyer_agent_id,
            "seller_agent_id": transaction.seller_agent_id,
            "property_id": transaction.property_id,
            "earnest_money": str(transaction.earnest_money),
            "total_purchase_price": str(transaction.total_purchase_price),
            "initiated_at": transaction.initiated_at.isoformat(),
            "target_closing_date": transaction.target_closing_date.isoformat(),
            "actual_closing_date": transaction.actual_closing_date.isoformat() if transaction.actual_closing_date else None,
            "wallet_state": wallet_state,
            "workflow_progress": workflow_progress,
            "verification_tasks": [
                {
                    "task_id": task.id,
                    "type": task.verification_type.value,
                    "status": task.status.value,
                    "assigned_agent_id": task.assigned_agent_id,
                    "deadline": task.deadline.isoformat(),
                    "payment_amount": str(task.payment_amount),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
                for task in tasks
            ],
            "payments": [
                {
                    "payment_id": p.id,
                    "type": p.payment_type.value,
                    "recipient_id": p.recipient_id,
                    "amount": str(p.amount),
                    "status": p.status.value,
                    "initiated_at": p.initiated_at.isoformat(),
                    "completed_at": p.completed_at.isoformat() if p.completed_at else None
                }
                for p in payments
            ],
            "settlement": {
                "settlement_id": settlement.id,
                "total_amount": str(settlement.total_amount),
                "seller_amount": str(settlement.seller_amount),
                "buyer_agent_commission": str(settlement.buyer_agent_commission),
                "seller_agent_commission": str(settlement.seller_agent_commission),
                "closing_costs": str(settlement.closing_costs),
                "executed_at": settlement.executed_at.isoformat()
            } if settlement else None
        }
        
        # Cache the transaction state
        self.cache.cache_transaction_state(transaction_id, state_data)
        
        return state_data
    
    async def cancel_transaction(
        self,
        transaction_id: str,
        reason: str,
        refund_earnest_money: bool = True
    ) -> None:
        """
        Cancel a transaction and optionally refund earnest money.
        
        Args:
            transaction_id: Transaction identifier
            reason: Reason for cancellation
            refund_earnest_money: Whether to refund earnest money to buyer
        
        Raises:
            EscrowError: If cancellation fails
        """
        logger.info(
            f"Cancelling transaction {transaction_id}",
            extra={"reason": reason, "refund": refund_earnest_money}
        )
        
        try:
            transaction = await self.get_transaction(transaction_id)
            if not transaction:
                raise EscrowError(f"Transaction {transaction_id} not found")
            
            # Transition to CANCELLED state
            state_machine = TransactionStateMachine(transaction)
            await state_machine.transition_to(
                TransactionState.CANCELLED,
                context={"reason": reason},
                persist=True
            )
            
            # Cancel all pending verification tasks
            tasks = self.db.query(VerificationTask).filter(
                VerificationTask.transaction_id == transaction_id,
                VerificationTask.status.in_([TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS])
            ).all()
            
            for task in tasks:
                task.status = TaskStatus.CANCELLED
                self.db.add(task)
            
            self.db.commit()
            
            # Log cancellation on blockchain
            await self.blockchain_logger.log_transaction_event(
                transaction_id=transaction.id,
                event_type=EventType.TRANSACTION_CANCELLED,
                event_data={
                    "reason": reason,
                    "refund_earnest_money": refund_earnest_money
                },
                db=self.db,
                async_processing=False
            )
            
            logger.info(f"Transaction {transaction_id} cancelled successfully")
            
            # Invalidate cache
            self.cache.invalidate_transaction_cache(transaction_id)
            
        except Exception as e:
            logger.error(f"Failed to cancel transaction: {str(e)}")
            self.db.rollback()
            raise EscrowError(f"Transaction cancellation failed: {str(e)}")
    
    async def close(self):
        """Close resources and cleanup."""
        await self.wallet_manager.close()
        await self.blockchain_logger.close()

    
    async def create_verification_workflow(
        self,
        transaction_id: str,
        custom_deadlines: Optional[Dict[VerificationType, int]] = None,
        custom_payment_amounts: Optional[Dict[VerificationType, Decimal]] = None
    ) -> VerificationWorkflow:
        """
        Create verification workflow and assign tasks to agents.
        
        This method:
        1. Creates a verification workflow with task definitions
        2. Assigns tasks to verification agents
        3. Configures milestones in the smart contract wallet
        4. Logs task assignments on blockchain
        5. Transitions transaction to VERIFICATION_IN_PROGRESS state
        
        Args:
            transaction_id: Transaction identifier
            custom_deadlines: Custom deadline days for each verification type
            custom_payment_amounts: Custom payment amounts for each verification type
        
        Returns:
            Created VerificationWorkflow instance
        
        Raises:
            EscrowError: If workflow creation fails
        """
        logger.info(f"Creating verification workflow for transaction {transaction_id}")
        
        try:
            transaction = await self.get_transaction(transaction_id)
            if not transaction:
                raise EscrowError(f"Transaction {transaction_id} not found")
            
            # Merge custom deadlines and payment amounts with defaults
            deadlines = {**self.DEFAULT_DEADLINES, **(custom_deadlines or {})}
            payment_amounts = {**self.DEFAULT_PAYMENT_AMOUNTS, **(custom_payment_amounts or {})}
            
            # Build task definitions
            from workflows.verification_workflow import TaskDefinition
            
            task_definitions = {}
            for verification_type in VerificationType:
                deadline_days = deadlines.get(verification_type, 7)
                payment_amount = payment_amounts.get(verification_type, Decimal("0.00"))
                
                # Define dependencies
                dependencies = []
                if verification_type == VerificationType.APPRAISAL:
                    dependencies = [VerificationType.INSPECTION]
                elif verification_type == VerificationType.LENDING:
                    dependencies = [VerificationType.TITLE_SEARCH, VerificationType.APPRAISAL]
                
                task_definitions[verification_type] = TaskDefinition(
                    verification_type=verification_type,
                    dependencies=dependencies,
                    deadline_days=deadline_days,
                    payment_amount=payment_amount
                )
            
            # Create workflow
            workflow = await self.workflow_engine.create_workflow(
                transaction=transaction,
                task_definitions=task_definitions
            )
            
            # Get created tasks
            tasks = self.db.query(VerificationTask).filter(
                VerificationTask.transaction_id == transaction_id
            ).all()
            
            # Configure milestones in smart contract wallet
            milestones = []
            for task in tasks:
                if task.payment_amount > 0:
                    milestone = Milestone(
                        id=f"verification_{task.verification_type.value}_{task.id}",
                        name=f"{task.verification_type.value.replace('_', ' ').title()} Payment",
                        amount=task.payment_amount,
                        recipient=task.assigned_agent_id,
                        conditions=[f"verification_complete:{task.id}"],
                        auto_release=True
                    )
                    milestones.append(milestone)
            
            if milestones:
                await self.wallet_manager.configure_milestones(
                    transaction=transaction,
                    milestones=milestones
                )
            
            # Log task assignments on blockchain
            for task in tasks:
                await self.blockchain_logger.log_transaction_event(
                    transaction_id=transaction.id,
                    event_type=EventType.VERIFICATION_TASK_ASSIGNED,
                    event_data={
                        "task_id": task.id,
                        "verification_type": task.verification_type.value,
                        "assigned_agent_id": task.assigned_agent_id,
                        "deadline": task.deadline.isoformat(),
                        "payment_amount": str(task.payment_amount)
                    },
                    db=self.db,
                    async_processing=True
                )
            
            # Transition to VERIFICATION_IN_PROGRESS state
            state_machine = TransactionStateMachine(transaction)
            await state_machine.transition_to(
                TransactionState.VERIFICATION_IN_PROGRESS,
                context={},
                persist=True
            )
            
            logger.info(
                f"Verification workflow created for transaction {transaction_id} with {len(tasks)} tasks"
            )
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create verification workflow: {str(e)}")
            self.db.rollback()
            raise EscrowError(f"Workflow creation failed: {str(e)}")
    
    async def process_verification_completion(
        self,
        transaction_id: str,
        verification_type: VerificationType,
        report: VerificationReport
    ) -> None:
        """
        Process completion of a verification task.
        
        This method:
        1. Validates the verification report
        2. Updates task status to COMPLETED
        3. Releases payment to verification agent if report is approved
        4. Logs verification completion on blockchain
        5. Sends real-time status updates to all parties
        6. Checks if all verifications are complete and transitions state if needed
        
        Args:
            transaction_id: Transaction identifier
            verification_type: Type of verification completed
            report: Verification report submitted
        
        Raises:
            EscrowError: If processing fails
        """
        logger.info(
            f"Processing verification completion for transaction {transaction_id}",
            extra={
                "verification_type": verification_type.value,
                "report_id": report.id,
                "report_status": report.status.value
            }
        )
        
        try:
            transaction = await self.get_transaction(transaction_id)
            if not transaction:
                raise EscrowError(f"Transaction {transaction_id} not found")
            
            # Get the verification task
            task = self.db.query(VerificationTask).filter(
                VerificationTask.transaction_id == transaction_id,
                VerificationTask.verification_type == verification_type
            ).first()
            
            if not task:
                raise EscrowError(
                    f"Verification task not found for type {verification_type.value}"
                )
            
            # Update task with report
            task.report_id = report.id
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            self.db.add(task)
            self.db.commit()
            
            # Log verification completion on blockchain
            await self.blockchain_logger.log_transaction_event(
                transaction_id=transaction.id,
                event_type=EventType.VERIFICATION_COMPLETED,
                event_data={
                    "task_id": task.id,
                    "verification_type": verification_type.value,
                    "report_id": report.id,
                    "report_status": report.status.value,
                    "agent_id": report.agent_id
                },
                db=self.db,
                async_processing=True
            )
            
            # Release payment if report is approved
            if report.status == ReportStatus.APPROVED and task.payment_amount > 0:
                try:
                    payment_result = await self.wallet_manager.release_milestone_payment(
                        transaction=transaction,
                        milestone_id=f"verification_{verification_type.value}_{task.id}",
                        recipient_id=report.agent_id,
                        amount=task.payment_amount,
                        payment_type=PaymentType.VERIFICATION
                    )
                    
                    # Log payment release on blockchain
                    await self.blockchain_logger.log_transaction_event(
                        transaction_id=transaction.id,
                        event_type=EventType.PAYMENT_RELEASED,
                        event_data={
                            "payment_id": payment_result.payment_id,
                            "recipient_id": report.agent_id,
                            "amount": str(task.payment_amount),
                            "payment_type": "verification",
                            "verification_type": verification_type.value,
                            "transaction_hash": payment_result.transaction_hash
                        },
                        db=self.db,
                        async_processing=True
                    )
                    
                    logger.info(
                        f"Payment released to {report.agent_id} for {verification_type.value}: "
                        f"${task.payment_amount}"
                    )
                    
                except WalletManagerError as e:
                    logger.error(f"Failed to release payment: {str(e)}")
                    # Don't fail the entire process if payment fails
                    # Payment can be retried later
            
            # Check if all verifications are complete
            all_tasks = self.db.query(VerificationTask).filter(
                VerificationTask.transaction_id == transaction_id
            ).all()
            
            all_complete = all(t.status == TaskStatus.COMPLETED for t in all_tasks)
            all_approved = all(
                t.report and t.report.status == ReportStatus.APPROVED
                for t in all_tasks if t.report
            )
            
            if all_complete:
                logger.info(f"All verifications complete for transaction {transaction_id}")
                
                # Transition to VERIFICATION_COMPLETE state
                state_machine = TransactionStateMachine(transaction)
                await state_machine.transition_to(
                    TransactionState.VERIFICATION_COMPLETE,
                    context={"all_verifications_complete": True},
                    persist=True
                )
                
                # If all approved, transition to SETTLEMENT_PENDING
                if all_approved:
                    await state_machine.transition_to(
                        TransactionState.SETTLEMENT_PENDING,
                        context={"all_verifications_approved": True},
                        persist=True
                    )
                    
                    logger.info(
                        f"Transaction {transaction_id} ready for settlement"
                    )
            
            logger.info(
                f"Verification completion processed for transaction {transaction_id}"
            )
            
            # Invalidate cache after state changes
            self.cache.invalidate_transaction_cache(transaction_id)
            if report.id:
                self.cache.cache_verification_report(report.id, self._serialize_report(report))
            
        except Exception as e:
            logger.error(f"Failed to process verification completion: {str(e)}")
            self.db.rollback()
            raise EscrowError(f"Verification completion processing failed: {str(e)}")
    
    async def check_overdue_tasks(self, transaction_id: str) -> List[Dict[str, Any]]:
        """
        Check for overdue verification tasks and return escalation information.
        
        Args:
            transaction_id: Transaction identifier
        
        Returns:
            List of overdue task information
        """
        overdue_tasks = await self.workflow_engine.check_deadlines(transaction_id)
        
        if overdue_tasks:
            logger.warning(
                f"Found {len(overdue_tasks)} overdue tasks for transaction {transaction_id}",
                extra={"overdue_tasks": overdue_tasks}
            )
        
        return overdue_tasks

    
    async def execute_settlement(
        self,
        transaction_id: str,
        buyer_agent_commission_rate: Decimal = Decimal("0.03"),  # 3%
        seller_agent_commission_rate: Decimal = Decimal("0.03"),  # 3%
        closing_costs: Optional[Decimal] = None,
        additional_distributions: Optional[List[Dict[str, Any]]] = None
    ) -> Settlement:
        """
        Execute final settlement with fund distribution.
        
        This method:
        1. Validates all verifications are approved
        2. Calculates final settlement amounts
        3. Distributes funds to seller, agents, and service providers
        4. Logs settlement on blockchain
        5. Sends settlement completion notifications
        6. Transitions transaction to SETTLED state
        
        Args:
            transaction_id: Transaction identifier
            buyer_agent_commission_rate: Buyer agent commission rate (default 3%)
            seller_agent_commission_rate: Seller agent commission rate (default 3%)
            closing_costs: Total closing costs (calculated if not provided)
            additional_distributions: Additional distributions to make
        
        Returns:
            Created Settlement entity
        
        Raises:
            EscrowError: If settlement execution fails
        """
        logger.info(
            f"Executing settlement for transaction {transaction_id}",
            extra={
                "buyer_commission_rate": str(buyer_agent_commission_rate),
                "seller_commission_rate": str(seller_agent_commission_rate)
            }
        )
        
        try:
            transaction = await self.get_transaction(transaction_id)
            if not transaction:
                raise EscrowError(f"Transaction {transaction_id} not found")
            
            # Validate transaction is ready for settlement
            if transaction.state != TransactionState.SETTLEMENT_PENDING:
                raise EscrowError(
                    f"Transaction {transaction_id} is not ready for settlement. "
                    f"Current state: {transaction.state.value}"
                )
            
            # Validate all verifications are approved
            tasks = self.db.query(VerificationTask).filter(
                VerificationTask.transaction_id == transaction_id
            ).all()
            
            for task in tasks:
                if not task.report or task.report.status != ReportStatus.APPROVED:
                    raise EscrowError(
                        f"Verification {task.verification_type.value} is not approved. "
                        f"Cannot proceed with settlement."
                    )
            
            # Calculate settlement amounts
            total_purchase_price = transaction.total_purchase_price
            
            # Calculate commissions
            buyer_agent_commission = total_purchase_price * buyer_agent_commission_rate
            seller_agent_commission = total_purchase_price * seller_agent_commission_rate
            
            # Calculate closing costs if not provided
            if closing_costs is None:
                # Sum up verification payments as part of closing costs
                verification_costs = sum(
                    task.payment_amount for task in tasks
                )
                # Add typical closing costs (title insurance, recording fees, etc.)
                # For MVP, use 1% of purchase price
                estimated_other_costs = total_purchase_price * Decimal("0.01")
                closing_costs = verification_costs + estimated_other_costs
            
            # Calculate seller amount (purchase price minus commissions and costs)
            seller_amount = (
                total_purchase_price
                - buyer_agent_commission
                - seller_agent_commission
                - closing_costs
            )
            
            # Ensure seller amount is positive
            if seller_amount < 0:
                raise EscrowError(
                    f"Seller amount is negative: ${seller_amount}. "
                    f"Check commission rates and closing costs."
                )
            
            logger.info(
                f"Settlement calculation for transaction {transaction_id}:",
                extra={
                    "total_purchase_price": str(total_purchase_price),
                    "seller_amount": str(seller_amount),
                    "buyer_agent_commission": str(buyer_agent_commission),
                    "seller_agent_commission": str(seller_agent_commission),
                    "closing_costs": str(closing_costs)
                }
            )
            
            # Execute settlement via smart contract wallet
            settlement_result = await self.wallet_manager.execute_final_settlement(
                transaction=transaction,
                seller_amount=seller_amount,
                buyer_agent_commission=buyer_agent_commission,
                seller_agent_commission=seller_agent_commission,
                closing_costs=closing_costs,
                additional_distributions=additional_distributions
            )
            
            # Get the settlement record created by wallet manager
            settlement = self.db.query(Settlement).filter(
                Settlement.transaction_id == transaction_id
            ).first()
            
            if not settlement:
                raise EscrowError("Settlement record not created")
            
            # Log settlement on blockchain
            await self.blockchain_logger.log_transaction_event(
                transaction_id=transaction.id,
                event_type=EventType.SETTLEMENT_EXECUTED,
                event_data={
                    "settlement_id": settlement.id,
                    "total_amount": str(settlement.total_amount),
                    "seller_amount": str(settlement.seller_amount),
                    "buyer_agent_commission": str(settlement.buyer_agent_commission),
                    "seller_agent_commission": str(settlement.seller_agent_commission),
                    "closing_costs": str(settlement.closing_costs),
                    "transaction_hash": settlement.blockchain_tx_hash,
                    "distributions": settlement.distributions
                },
                db=self.db,
                async_processing=False
            )
            
            # Update transaction state to SETTLED
            transaction.state = TransactionState.SETTLED
            transaction.actual_closing_date = datetime.utcnow()
            self.db.add(transaction)
            self.db.commit()
            
            logger.info(
                f"Settlement executed successfully for transaction {transaction_id}",
                extra={
                    "settlement_id": settlement.id,
                    "seller_amount": str(seller_amount),
                    "total_distributions": len(settlement.distributions) if settlement.distributions else 0
                }
            )
            
            return settlement
            
        except Exception as e:
            logger.error(f"Failed to execute settlement: {str(e)}")
            self.db.rollback()
            raise EscrowError(f"Settlement execution failed: {str(e)}")
    
    async def calculate_settlement_preview(
        self,
        transaction_id: str,
        buyer_agent_commission_rate: Decimal = Decimal("0.03"),
        seller_agent_commission_rate: Decimal = Decimal("0.03"),
        closing_costs: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate settlement amounts without executing the settlement.
        
        Args:
            transaction_id: Transaction identifier
            buyer_agent_commission_rate: Buyer agent commission rate
            seller_agent_commission_rate: Seller agent commission rate
            closing_costs: Total closing costs (calculated if not provided)
        
        Returns:
            Dictionary with settlement calculation breakdown
        
        Raises:
            EscrowError: If calculation fails
        """
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            raise EscrowError(f"Transaction {transaction_id} not found")
        
        total_purchase_price = transaction.total_purchase_price
        
        # Calculate commissions
        buyer_agent_commission = total_purchase_price * buyer_agent_commission_rate
        seller_agent_commission = total_purchase_price * seller_agent_commission_rate
        
        # Calculate closing costs if not provided
        if closing_costs is None:
            tasks = self.db.query(VerificationTask).filter(
                VerificationTask.transaction_id == transaction_id
            ).all()
            
            verification_costs = sum(task.payment_amount for task in tasks)
            estimated_other_costs = total_purchase_price * Decimal("0.01")
            closing_costs = verification_costs + estimated_other_costs
        
        # Calculate seller amount
        seller_amount = (
            total_purchase_price
            - buyer_agent_commission
            - seller_agent_commission
            - closing_costs
        )
        
        return {
            "transaction_id": transaction_id,
            "total_purchase_price": str(total_purchase_price),
            "seller_amount": str(seller_amount),
            "buyer_agent_commission": str(buyer_agent_commission),
            "buyer_agent_commission_rate": str(buyer_agent_commission_rate),
            "seller_agent_commission": str(seller_agent_commission),
            "seller_agent_commission_rate": str(seller_agent_commission_rate),
            "closing_costs": str(closing_costs),
            "breakdown": {
                "seller_receives": str(seller_amount),
                "buyer_agent_receives": str(buyer_agent_commission),
                "seller_agent_receives": str(seller_agent_commission),
                "closing_costs_total": str(closing_costs)
            }
        }

    
    async def handle_dispute(
        self,
        transaction_id: str,
        raised_by: str,
        dispute_type: str,
        description: str,
        related_verification_type: Optional[VerificationType] = None,
        evidence: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a dispute raised during the transaction.
        
        This method:
        1. Transitions transaction to DISPUTED state
        2. Freezes fund releases
        3. Provides access to audit trail for dispute resolution
        4. Logs dispute on blockchain
        5. Initiates dispute resolution workflow
        
        Args:
            transaction_id: Transaction identifier
            raised_by: ID of party raising the dispute
            dispute_type: Type of dispute (verification, payment, settlement, etc.)
            description: Description of the dispute
            related_verification_type: Related verification type if applicable
            evidence: Evidence supporting the dispute
        
        Returns:
            Dictionary with dispute information and audit trail access
        
        Raises:
            EscrowError: If dispute handling fails
        """
        logger.info(
            f"Handling dispute for transaction {transaction_id}",
            extra={
                "raised_by": raised_by,
                "dispute_type": dispute_type,
                "related_verification": related_verification_type.value if related_verification_type else None
            }
        )
        
        try:
            transaction = await self.get_transaction(transaction_id)
            if not transaction:
                raise EscrowError(f"Transaction {transaction_id} not found")
            
            # Check if transaction is already in terminal state
            if transaction.state in [TransactionState.SETTLED, TransactionState.CANCELLED]:
                raise EscrowError(
                    f"Cannot raise dispute for transaction in {transaction.state.value} state"
                )
            
            # Store current state for potential rollback
            previous_state = transaction.state
            
            # Transition to DISPUTED state
            state_machine = TransactionStateMachine(transaction)
            await state_machine.transition_to(
                TransactionState.DISPUTED,
                context={
                    "dispute_type": dispute_type,
                    "raised_by": raised_by,
                    "previous_state": previous_state.value
                },
                persist=True
            )
            
            # Create dispute record in transaction metadata
            dispute_id = str(uuid.uuid4())
            dispute_record = {
                "dispute_id": dispute_id,
                "raised_by": raised_by,
                "dispute_type": dispute_type,
                "description": description,
                "related_verification_type": related_verification_type.value if related_verification_type else None,
                "evidence": evidence or {},
                "raised_at": datetime.utcnow().isoformat(),
                "status": "open",
                "previous_state": previous_state.value
            }
            
            # Update transaction metadata with dispute
            if not transaction.transaction_metadata:
                transaction.transaction_metadata = {}
            
            if "disputes" not in transaction.transaction_metadata:
                transaction.transaction_metadata["disputes"] = []
            
            transaction.transaction_metadata["disputes"].append(dispute_record)
            self.db.add(transaction)
            self.db.commit()
            
            # Log dispute on blockchain
            await self.blockchain_logger.log_transaction_event(
                transaction_id=transaction.id,
                event_type=EventType.DISPUTE_RAISED,
                event_data={
                    "dispute_id": dispute_id,
                    "raised_by": raised_by,
                    "dispute_type": dispute_type,
                    "description": description,
                    "related_verification_type": related_verification_type.value if related_verification_type else None,
                    "previous_state": previous_state.value
                },
                db=self.db,
                async_processing=False
            )
            
            # Get audit trail for dispute resolution
            audit_trail = await self.blockchain_logger.get_audit_trail(
                transaction_id=transaction_id,
                include_verification=True
            )
            
            # Get related verification report if applicable
            related_report = None
            if related_verification_type:
                task = self.db.query(VerificationTask).filter(
                    VerificationTask.transaction_id == transaction_id,
                    VerificationTask.verification_type == related_verification_type
                ).first()
                
                if task and task.report:
                    related_report = {
                        "report_id": task.report.id,
                        "status": task.report.status.value,
                        "findings": task.report.findings,
                        "documents": task.report.documents,
                        "submitted_at": task.report.submitted_at.isoformat(),
                        "reviewer_notes": task.report.reviewer_notes
                    }
            
            logger.info(
                f"Dispute {dispute_id} created for transaction {transaction_id}",
                extra={
                    "dispute_id": dispute_id,
                    "dispute_type": dispute_type,
                    "audit_trail_entries": len(audit_trail)
                }
            )
            
            return {
                "dispute_id": dispute_id,
                "transaction_id": transaction_id,
                "status": "open",
                "raised_by": raised_by,
                "dispute_type": dispute_type,
                "description": description,
                "raised_at": dispute_record["raised_at"],
                "previous_state": previous_state.value,
                "current_state": transaction.state.value,
                "audit_trail": audit_trail,
                "related_report": related_report,
                "resolution_options": self._get_dispute_resolution_options(
                    dispute_type,
                    previous_state
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to handle dispute: {str(e)}")
            self.db.rollback()
            raise EscrowError(f"Dispute handling failed: {str(e)}")
    
    async def resolve_dispute(
        self,
        transaction_id: str,
        dispute_id: str,
        resolution: str,
        resolution_details: Dict[str, Any],
        resolved_by: str
    ) -> None:
        """
        Resolve a dispute and transition transaction to appropriate state.
        
        Args:
            transaction_id: Transaction identifier
            dispute_id: Dispute identifier
            resolution: Resolution decision (continue, cancel, retry_verification, etc.)
            resolution_details: Details of the resolution
            resolved_by: ID of party resolving the dispute
        
        Raises:
            EscrowError: If dispute resolution fails
        """
        logger.info(
            f"Resolving dispute {dispute_id} for transaction {transaction_id}",
            extra={"resolution": resolution, "resolved_by": resolved_by}
        )
        
        try:
            transaction = await self.get_transaction(transaction_id)
            if not transaction:
                raise EscrowError(f"Transaction {transaction_id} not found")
            
            # Find dispute in metadata
            disputes = transaction.transaction_metadata.get("disputes", [])
            dispute = next((d for d in disputes if d["dispute_id"] == dispute_id), None)
            
            if not dispute:
                raise EscrowError(f"Dispute {dispute_id} not found")
            
            if dispute["status"] != "open":
                raise EscrowError(f"Dispute {dispute_id} is already {dispute['status']}")
            
            # Update dispute record
            dispute["status"] = "resolved"
            dispute["resolution"] = resolution
            dispute["resolution_details"] = resolution_details
            dispute["resolved_by"] = resolved_by
            dispute["resolved_at"] = datetime.utcnow().isoformat()
            
            self.db.add(transaction)
            self.db.commit()
            
            # Log dispute resolution on blockchain
            await self.blockchain_logger.log_transaction_event(
                transaction_id=transaction.id,
                event_type=EventType.DISPUTE_RESOLVED,
                event_data={
                    "dispute_id": dispute_id,
                    "resolution": resolution,
                    "resolution_details": resolution_details,
                    "resolved_by": resolved_by
                },
                db=self.db,
                async_processing=False
            )
            
            # Transition to appropriate state based on resolution
            state_machine = TransactionStateMachine(transaction)
            previous_state = TransactionState(dispute["previous_state"])
            
            if resolution == "continue":
                # Continue from previous state
                await state_machine.transition_to(
                    previous_state,
                    context={"dispute_resolved": True},
                    persist=True
                )
            elif resolution == "cancel":
                # Cancel transaction
                await self.cancel_transaction(
                    transaction_id=transaction_id,
                    reason=f"Cancelled due to dispute resolution: {dispute_id}",
                    refund_earnest_money=resolution_details.get("refund_earnest_money", True)
                )
            elif resolution == "retry_verification":
                # Retry specific verification
                verification_type = resolution_details.get("verification_type")
                if verification_type:
                    # Reset verification task
                    task = self.db.query(VerificationTask).filter(
                        VerificationTask.transaction_id == transaction_id,
                        VerificationTask.verification_type == VerificationType(verification_type)
                    ).first()
                    
                    if task:
                        task.status = TaskStatus.ASSIGNED
                        task.completed_at = None
                        task.report_id = None
                        self.db.add(task)
                        self.db.commit()
                
                # Return to verification in progress
                await state_machine.transition_to(
                    TransactionState.VERIFICATION_IN_PROGRESS,
                    context={"dispute_resolved": True},
                    persist=True
                )
            
            logger.info(f"Dispute {dispute_id} resolved successfully")
            
        except Exception as e:
            logger.error(f"Failed to resolve dispute: {str(e)}")
            self.db.rollback()
            raise EscrowError(f"Dispute resolution failed: {str(e)}")
    
    def _get_dispute_resolution_options(
        self,
        dispute_type: str,
        previous_state: TransactionState
    ) -> List[str]:
        """
        Get available resolution options for a dispute.
        
        Args:
            dispute_type: Type of dispute
            previous_state: State before dispute was raised
        
        Returns:
            List of available resolution options
        """
        base_options = ["continue", "cancel"]
        
        if dispute_type == "verification":
            base_options.append("retry_verification")
        
        if previous_state == TransactionState.SETTLEMENT_PENDING:
            base_options.append("adjust_settlement")
        
        return base_options
    
    async def get_dispute_audit_trail(
        self,
        transaction_id: str,
        dispute_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive audit trail for a specific dispute.
        
        Args:
            transaction_id: Transaction identifier
            dispute_id: Dispute identifier
        
        Returns:
            Dictionary with dispute details and full audit trail
        
        Raises:
            EscrowError: If dispute not found
        """
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            raise EscrowError(f"Transaction {transaction_id} not found")
        
        # Find dispute
        disputes = transaction.transaction_metadata.get("disputes", [])
        dispute = next((d for d in disputes if d["dispute_id"] == dispute_id), None)
        
        if not dispute:
            raise EscrowError(f"Dispute {dispute_id} not found")
        
        # Get full audit trail
        audit_trail = await self.blockchain_logger.get_audit_trail(
            transaction_id=transaction_id,
            include_verification=True
        )
        
        # Get all verification reports
        tasks = self.db.query(VerificationTask).filter(
            VerificationTask.transaction_id == transaction_id
        ).all()
        
        verification_reports = []
        for task in tasks:
            if task.report:
                verification_reports.append({
                    "verification_type": task.verification_type.value,
                    "report_id": task.report.id,
                    "status": task.report.status.value,
                    "findings": task.report.findings,
                    "documents": task.report.documents,
                    "submitted_at": task.report.submitted_at.isoformat(),
                    "reviewer_notes": task.report.reviewer_notes
                })
        
        # Get all payments
        payments = self.db.query(Payment).filter(
            Payment.transaction_id == transaction_id
        ).all()
        
        payment_history = [
            {
                "payment_id": p.id,
                "type": p.payment_type.value,
                "recipient_id": p.recipient_id,
                "amount": str(p.amount),
                "status": p.status.value,
                "blockchain_tx_hash": p.blockchain_tx_hash,
                "initiated_at": p.initiated_at.isoformat(),
                "completed_at": p.completed_at.isoformat() if p.completed_at else None
            }
            for p in payments
        ]
        
        return {
            "dispute": dispute,
            "transaction_id": transaction_id,
            "audit_trail": audit_trail,
            "verification_reports": verification_reports,
            "payment_history": payment_history,
            "transaction_state": transaction.state.value
        }
    
    def _serialize_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """
        Serialize transaction for caching.
        
        Args:
            transaction: Transaction to serialize
        
        Returns:
            Serializable transaction data
        """
        return {
            "id": transaction.id,
            "buyer_agent_id": transaction.buyer_agent_id,
            "seller_agent_id": transaction.seller_agent_id,
            "property_id": transaction.property_id,
            "earnest_money": str(transaction.earnest_money),
            "total_purchase_price": str(transaction.total_purchase_price),
            "state": transaction.state.value,
            "wallet_id": transaction.wallet_id,
            "initiated_at": transaction.initiated_at.isoformat(),
            "target_closing_date": transaction.target_closing_date.isoformat(),
            "actual_closing_date": transaction.actual_closing_date.isoformat() if transaction.actual_closing_date else None,
            "metadata": transaction.transaction_metadata
        }
    
    def _serialize_report(self, report: VerificationReport) -> Dict[str, Any]:
        """
        Serialize verification report for caching.
        
        Args:
            report: Verification report to serialize
        
        Returns:
            Serializable report data
        """
        return {
            "id": report.id,
            "task_id": report.task_id,
            "agent_id": report.agent_id,
            "report_type": report.report_type.value,
            "status": report.status.value,
            "findings": report.findings,
            "documents": report.documents,
            "submitted_at": report.submitted_at.isoformat(),
            "reviewed_at": report.reviewed_at.isoformat() if report.reviewed_at else None,
            "reviewer_notes": report.reviewer_notes
        }
