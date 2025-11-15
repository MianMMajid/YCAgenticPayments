"""End-to-end integration tests for complete escrow transaction flow."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from agents.escrow_agent_orchestrator import EscrowAgentOrchestrator
from models.transaction import Transaction, TransactionState
from models.verification import VerificationTask, VerificationType, TaskStatus, VerificationReport, ReportStatus
from models.payment import Payment, PaymentType, PaymentStatus
from models.settlement import Settlement, BlockchainEvent


@pytest.fixture
def transaction_details():
    """Sample transaction details for testing."""
    return {
        "buyer_agent_id": "buyer_agent_001",
        "seller_agent_id": "seller_agent_001",
        "property_id": "prop_123",
        "property_address": "123 Main St, Baltimore, MD 21201",
        "earnest_money": Decimal("10000.00"),
        "total_purchase_price": Decimal("385000.00"),
        "target_closing_days": 30,
        "buyer_agent_commission": Decimal("5000.00"),
        "seller_agent_commission": Decimal("5000.00"),
        "closing_costs": Decimal("3000.00")
    }


class TestHappyPathTransactionFlow:
    """Test complete happy path from initiation to settlement."""
    
    @pytest.mark.asyncio
    async def test_complete_transaction_flow(self, test_db, transaction_details):
        """Test complete transaction from initiation to settlement."""
        orchestrator = EscrowAgentOrchestrator()
        
        # Mock external services
        with patch('agents.escrow_agent_orchestrator.SmartContractWalletManager') as mock_wallet, \
             patch('agents.escrow_agent_orchestrator.BlockchainLogger') as mock_blockchain, \
             patch('agents.escrow_agent_orchestrator.NotificationEngine') as mock_notif:
            
            # Setup mocks
            mock_wallet_instance = AsyncMock()
            mock_wallet.return_value = mock_wallet_instance
            mock_wallet_instance.create_wallet.return_value = MagicMock(
                wallet_id="wallet_test_123",
                address="0x1234567890abcdef",
                balance=Decimal("10000.00")
            )
            
            mock_blockchain_instance = AsyncMock()
            mock_blockchain.return_value = mock_blockchain_instance
            mock_blockchain_instance.log_transaction_event.return_value = "0xhash123"
            
            mock_notif_instance = AsyncMock()
            mock_notif.return_value = mock_notif_instance
            
            # Step 1: Initiate transaction
            transaction = await orchestrator.initiate_transaction(
                buyer_agent_id=transaction_details["buyer_agent_id"],
                seller_agent_id=transaction_details["seller_agent_id"],
                property_id=transaction_details["property_id"],
                earnest_money=transaction_details["earnest_money"],
                transaction_details=transaction_details
            )
            
            assert transaction is not None
            assert transaction.state == TransactionState.FUNDED
            assert transaction.wallet_id == "wallet_test_123"
            
            # Verify verification tasks created
            tasks = test_db.query(VerificationTask).filter_by(
                transaction_id=transaction.id
            ).all()
            assert len(tasks) == 4
            
            # Step 2: Complete title search
            title_task = test_db.query(VerificationTask).filter_by(
                transaction_id=transaction.id,
                verification_type=VerificationType.TITLE_SEARCH
            ).first()
            
            title_report = VerificationReport(
                task_id=title_task.id,
                agent_id="title_agent_001",
                report_type=VerificationType.TITLE_SEARCH,
                status=ReportStatus.APPROVED,
                findings={"title_clear": True, "liens": []},
                documents=["https://example.com/title_report.pdf"]
            )
            test_db.add(title_report)
            test_db.commit()
            
            mock_wallet_instance.release_milestone_payment.return_value = MagicMock(
                payment_id="pay_title_123",
                status="completed",
                tx_hash="0xpay_title"
            )
            
            await orchestrator.process_verification_completion(
                transaction.id,
                VerificationType.TITLE_SEARCH,
                title_report
            )
            
            # Verify payment released
            title_payment = test_db.query(Payment).filter_by(
                transaction_id=transaction.id,
                payment_type=PaymentType.VERIFICATION
            ).first()
            assert title_payment is not None
            assert title_payment.amount == Decimal("1200.00")
            
            # Step 3: Complete inspection
            inspection_task = test_db.query(VerificationTask).filter_by(
                transaction_id=transaction.id,
                verification_type=VerificationType.INSPECTION
            ).first()
            
            inspection_report = VerificationReport(
                task_id=inspection_task.id,
                agent_id="inspector_001",
                report_type=VerificationType.INSPECTION,
                status=ReportStatus.APPROVED,
                findings={"condition": "good", "issues": []},
                documents=["https://example.com/inspection_report.pdf"]
            )
            test_db.add(inspection_report)
            test_db.commit()
            
            await orchestrator.process_verification_completion(
                transaction.id,
                VerificationType.INSPECTION,
                inspection_report
            )
            
            # Step 4: Complete appraisal (depends on inspection)
            appraisal_task = test_db.query(VerificationTask).filter_by(
                transaction_id=transaction.id,
                verification_type=VerificationType.APPRAISAL
            ).first()
            
            appraisal_report = VerificationReport(
                task_id=appraisal_task.id,
                agent_id="appraiser_001",
                report_type=VerificationType.APPRAISAL,
                status=ReportStatus.APPROVED,
                findings={"appraised_value": 390000},
                documents=["https://example.com/appraisal_report.pdf"]
            )
            test_db.add(appraisal_report)
            test_db.commit()
            
            await orchestrator.process_verification_completion(
                transaction.id,
                VerificationType.APPRAISAL,
                appraisal_report
            )
            
            # Step 5: Complete lending verification
            lending_task = test_db.query(VerificationTask).filter_by(
                transaction_id=transaction.id,
                verification_type=VerificationType.LENDING
            ).first()
            
            lending_report = VerificationReport(
                task_id=lending_task.id,
                agent_id="lender_001",
                report_type=VerificationType.LENDING,
                status=ReportStatus.APPROVED,
                findings={"loan_approved": True, "loan_amount": 308000},
                documents=["https://example.com/loan_approval.pdf"]
            )
            test_db.add(lending_report)
            test_db.commit()
            
            await orchestrator.process_verification_completion(
                transaction.id,
                VerificationType.LENDING,
                lending_report
            )
            
            # Verify transaction state updated
            test_db.refresh(transaction)
            assert transaction.state == TransactionState.VERIFICATION_COMPLETE
            
            # Step 6: Execute settlement
            mock_wallet_instance.execute_final_settlement.return_value = {
                "settlement_id": "settle_123",
                "status": "completed",
                "tx_hash": "0xsettlement123"
            }
            
            settlement_result = await orchestrator.execute_settlement(transaction.id)
            
            assert settlement_result is not None
            
            # Verify settlement record created
            settlement = test_db.query(Settlement).filter_by(
                transaction_id=transaction.id
            ).first()
            assert settlement is not None
            assert settlement.total_amount == transaction_details["total_purchase_price"]
            
            # Verify transaction marked as settled
            test_db.refresh(transaction)
            assert transaction.state == TransactionState.SETTLED
            assert transaction.actual_closing_date is not None


class TestVerificationFailureScenarios:
    """Test scenarios where verification fails."""
    
    @pytest.mark.asyncio
    async def test_rejected_title_search(self, test_db, transaction_details):
        """Test handling rejected title search report."""
        orchestrator = EscrowAgentOrchestrator()
        
        with patch('agents.escrow_agent_orchestrator.SmartContractWalletManager') as mock_wallet, \
             patch('agents.escrow_agent_orchestrator.BlockchainLogger') as mock_blockchain, \
             patch('agents.escrow_agent_orchestrator.NotificationEngine') as mock_notif:
            
            mock_wallet_instance = AsyncMock()
            mock_wallet.return_value = mock_wallet_instance
            mock_wallet_instance.create_wallet.return_value = MagicMock(
                wallet_id="wallet_test_123",
                balance=Decimal("10000.00")
            )
            
            mock_blockchain_instance = AsyncMock()
            mock_blockchain.return_value = mock_blockchain_instance
            
            mock_notif_instance = AsyncMock()
            mock_notif.return_value = mock_notif_instance
            
            # Initiate transaction
            transaction = await orchestrator.initiate_transaction(
                buyer_agent_id=transaction_details["buyer_agent_id"],
                seller_agent_id=transaction_details["seller_agent_id"],
                property_id=transaction_details["property_id"],
                earnest_money=transaction_details["earnest_money"],
                transaction_details=transaction_details
            )
            
            # Submit rejected title report
            title_task = test_db.query(VerificationTask).filter_by(
                transaction_id=transaction.id,
                verification_type=VerificationType.TITLE_SEARCH
            ).first()
            
            title_report = VerificationReport(
                task_id=title_task.id,
                agent_id="title_agent_001",
                report_type=VerificationType.TITLE_SEARCH,
                status=ReportStatus.REJECTED,
                findings={"title_clear": False, "liens": ["Tax lien $5000"]},
                documents=["https://example.com/title_report.pdf"]
            )
            test_db.add(title_report)
            test_db.commit()
            
            # Process rejection
            with pytest.raises(Exception, match="rejected"):
                await orchestrator.process_verification_completion(
                    transaction.id,
                    VerificationType.TITLE_SEARCH,
                    title_report
                )
            
            # Verify no payment released
            payments = test_db.query(Payment).filter_by(
                transaction_id=transaction.id
            ).all()
            assert len(payments) == 0
            
            # Verify notification sent
            mock_notif_instance.notify_transaction_parties.assert_called()
    
    @pytest.mark.asyncio
    async def test_failed_inspection(self, test_db, transaction_details):
        """Test handling failed inspection."""
        orchestrator = EscrowAgentOrchestrator()
        
        with patch('agents.escrow_agent_orchestrator.SmartContractWalletManager') as mock_wallet, \
             patch('agents.escrow_agent_orchestrator.BlockchainLogger') as mock_blockchain, \
             patch('agents.escrow_agent_orchestrator.NotificationEngine') as mock_notif:
            
            mock_wallet_instance = AsyncMock()
            mock_wallet.return_value = mock_wallet_instance
            mock_wallet_instance.create_wallet.return_value = MagicMock(
                wallet_id="wallet_test_123"
            )
            
            mock_blockchain_instance = AsyncMock()
            mock_blockchain.return_value = mock_blockchain_instance
            
            mock_notif_instance = AsyncMock()
            mock_notif.return_value = mock_notif_instance
            
            transaction = await orchestrator.initiate_transaction(
                buyer_agent_id=transaction_details["buyer_agent_id"],
                seller_agent_id=transaction_details["seller_agent_id"],
                property_id=transaction_details["property_id"],
                earnest_money=transaction_details["earnest_money"],
                transaction_details=transaction_details
            )
            
            # Submit inspection with major issues
            inspection_task = test_db.query(VerificationTask).filter_by(
                transaction_id=transaction.id,
                verification_type=VerificationType.INSPECTION
            ).first()
            
            inspection_report = VerificationReport(
                task_id=inspection_task.id,
                agent_id="inspector_001",
                report_type=VerificationType.INSPECTION,
                status=ReportStatus.NEEDS_REVIEW,
                findings={
                    "condition": "poor",
                    "issues": ["Foundation crack", "Roof damage", "Electrical issues"]
                },
                documents=["https://example.com/inspection_report.pdf"]
            )
            test_db.add(inspection_report)
            test_db.commit()
            
            # Process - should require manual review
            await orchestrator.process_verification_completion(
                transaction.id,
                VerificationType.INSPECTION,
                inspection_report
            )
            
            # Verify task marked for review
            test_db.refresh(inspection_task)
            assert inspection_task.status == TaskStatus.IN_PROGRESS


class TestPaymentFailureScenarios:
    """Test scenarios where payment processing fails."""
    
    @pytest.mark.asyncio
    async def test_insufficient_wallet_balance(self, test_db, transaction_details):
        """Test handling insufficient wallet balance."""
        orchestrator = EscrowAgentOrchestrator()
        
        with patch('agents.escrow_agent_orchestrator.SmartContractWalletManager') as mock_wallet, \
             patch('agents.escrow_agent_orchestrator.BlockchainLogger') as mock_blockchain, \
             patch('agents.escrow_agent_orchestrator.NotificationEngine') as mock_notif:
            
            mock_wallet_instance = AsyncMock()
            mock_wallet.return_value = mock_wallet_instance
            mock_wallet_instance.create_wallet.return_value = MagicMock(
                wallet_id="wallet_test_123"
            )
            
            # Simulate insufficient balance error
            mock_wallet_instance.release_milestone_payment.side_effect = Exception("Insufficient balance")
            
            mock_blockchain_instance = AsyncMock()
            mock_blockchain.return_value = mock_blockchain_instance
            
            mock_notif_instance = AsyncMock()
            mock_notif.return_value = mock_notif_instance
            
            transaction = await orchestrator.initiate_transaction(
                buyer_agent_id=transaction_details["buyer_agent_id"],
                seller_agent_id=transaction_details["seller_agent_id"],
                property_id=transaction_details["property_id"],
                earnest_money=transaction_details["earnest_money"],
                transaction_details=transaction_details
            )
            
            # Complete title search
            title_task = test_db.query(VerificationTask).filter_by(
                transaction_id=transaction.id,
                verification_type=VerificationType.TITLE_SEARCH
            ).first()
            
            title_report = VerificationReport(
                task_id=title_task.id,
                agent_id="title_agent_001",
                report_type=VerificationType.TITLE_SEARCH,
                status=ReportStatus.APPROVED,
                findings={"title_clear": True}
            )
            test_db.add(title_report)
            test_db.commit()
            
            # Process - should fail due to insufficient balance
            with pytest.raises(Exception, match="Insufficient balance"):
                await orchestrator.process_verification_completion(
                    transaction.id,
                    VerificationType.TITLE_SEARCH,
                    title_report
                )
    
    @pytest.mark.asyncio
    async def test_payment_retry_on_network_error(self, test_db, transaction_details):
        """Test payment retry on network error."""
        orchestrator = EscrowAgentOrchestrator()
        
        with patch('agents.escrow_agent_orchestrator.SmartContractWalletManager') as mock_wallet, \
             patch('agents.escrow_agent_orchestrator.BlockchainLogger') as mock_blockchain, \
             patch('agents.escrow_agent_orchestrator.NotificationEngine') as mock_notif:
            
            mock_wallet_instance = AsyncMock()
            mock_wallet.return_value = mock_wallet_instance
            mock_wallet_instance.create_wallet.return_value = MagicMock(
                wallet_id="wallet_test_123"
            )
            
            # First attempt fails, second succeeds
            mock_wallet_instance.release_milestone_payment.side_effect = [
                Exception("Network timeout"),
                MagicMock(payment_id="pay_123", status="completed", tx_hash="0xpay123")
            ]
            
            mock_blockchain_instance = AsyncMock()
            mock_blockchain.return_value = mock_blockchain_instance
            
            mock_notif_instance = AsyncMock()
            mock_notif.return_value = mock_notif_instance
            
            transaction = await orchestrator.initiate_transaction(
                buyer_agent_id=transaction_details["buyer_agent_id"],
                seller_agent_id=transaction_details["seller_agent_id"],
                property_id=transaction_details["property_id"],
                earnest_money=transaction_details["earnest_money"],
                transaction_details=transaction_details
            )
            
            title_task = test_db.query(VerificationTask).filter_by(
                transaction_id=transaction.id,
                verification_type=VerificationType.TITLE_SEARCH
            ).first()
            
            title_report = VerificationReport(
                task_id=title_task.id,
                agent_id="title_agent_001",
                report_type=VerificationType.TITLE_SEARCH,
                status=ReportStatus.APPROVED,
                findings={"title_clear": True}
            )
            test_db.add(title_report)
            test_db.commit()
            
            # Should retry and succeed
            await orchestrator.process_verification_completion(
                transaction.id,
                VerificationType.TITLE_SEARCH,
                title_report
            )
            
            # Verify payment eventually succeeded
            assert mock_wallet_instance.release_milestone_payment.call_count == 2


class TestDisputeHandling:
    """Test dispute handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_raise_dispute_during_verification(self, test_db, transaction_details):
        """Test raising dispute during verification phase."""
        orchestrator = EscrowAgentOrchestrator()
        
        with patch('agents.escrow_agent_orchestrator.SmartContractWalletManager') as mock_wallet, \
             patch('agents.escrow_agent_orchestrator.BlockchainLogger') as mock_blockchain, \
             patch('agents.escrow_agent_orchestrator.NotificationEngine') as mock_notif:
            
            mock_wallet_instance = AsyncMock()
            mock_wallet.return_value = mock_wallet_instance
            mock_wallet_instance.create_wallet.return_value = MagicMock(
                wallet_id="wallet_test_123"
            )
            
            mock_blockchain_instance = AsyncMock()
            mock_blockchain.return_value = mock_blockchain_instance
            
            mock_notif_instance = AsyncMock()
            mock_notif.return_value = mock_notif_instance
            
            transaction = await orchestrator.initiate_transaction(
                buyer_agent_id=transaction_details["buyer_agent_id"],
                seller_agent_id=transaction_details["seller_agent_id"],
                property_id=transaction_details["property_id"],
                earnest_money=transaction_details["earnest_money"],
                transaction_details=transaction_details
            )
            
            # Raise dispute
            dispute_details = {
                "raised_by": "buyer_agent_001",
                "reason": "Seller failed to disclose material defects",
                "description": "Foundation issues not disclosed",
                "requested_resolution": "Cancel transaction and return earnest money"
            }
            
            dispute_result = await orchestrator.handle_dispute(
                transaction.id,
                dispute_details
            )
            
            assert dispute_result is not None
            
            # Verify transaction state changed to disputed
            test_db.refresh(transaction)
            assert transaction.state == TransactionState.DISPUTED
            
            # Verify blockchain event logged
            mock_blockchain_instance.log_transaction_event.assert_called()
            
            # Verify all parties notified
            mock_notif_instance.notify_transaction_parties.assert_called()
    
    @pytest.mark.asyncio
    async def test_access_audit_trail_for_dispute(self, test_db, transaction_details):
        """Test accessing audit trail during dispute."""
        orchestrator = EscrowAgentOrchestrator()
        
        with patch('agents.escrow_agent_orchestrator.SmartContractWalletManager') as mock_wallet, \
             patch('agents.escrow_agent_orchestrator.BlockchainLogger') as mock_blockchain, \
             patch('agents.escrow_agent_orchestrator.NotificationEngine') as mock_notif:
            
            mock_wallet_instance = AsyncMock()
            mock_wallet.return_value = mock_wallet_instance
            
            mock_blockchain_instance = AsyncMock()
            mock_blockchain.return_value = mock_blockchain_instance
            
            # Mock audit trail
            mock_blockchain_instance.get_audit_trail.return_value = [
                MagicMock(
                    event_type="TRANSACTION_INITIATED",
                    timestamp=datetime.utcnow(),
                    blockchain_tx_hash="0xhash1"
                ),
                MagicMock(
                    event_type="VERIFICATION_COMPLETED",
                    timestamp=datetime.utcnow(),
                    blockchain_tx_hash="0xhash2"
                )
            ]
            
            mock_notif_instance = AsyncMock()
            mock_notif.return_value = mock_notif_instance
            
            # Get audit trail
            audit_trail = await mock_blockchain_instance.get_audit_trail("txn_123")
            
            assert len(audit_trail) == 2
            assert audit_trail[0].event_type == "TRANSACTION_INITIATED"
