"""Integration tests for Agentic Stripe smart contract wallet integration."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from services.agentic_stripe_client import AgenticStripeClient, WalletDetails, PaymentResult
from services.smart_contract_wallet_manager import SmartContractWalletManager, Milestone
from models.transaction import Transaction, TransactionState
from models.payment import Payment, PaymentType, PaymentStatus


@pytest.fixture
def mock_agentic_stripe_response():
    """Mock Agentic Stripe API responses."""
    return {
        "wallet": {
            "wallet_id": "wallet_test_123",
            "address": "0x1234567890abcdef",
            "balance": "100000.00",
            "status": "active"
        },
        "payment": {
            "payment_id": "pay_test_456",
            "status": "completed",
            "tx_hash": "0xabcdef1234567890",
            "amount": "1200.00"
        }
    }


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


class TestAgenticStripeClient:
    """Test Agentic Stripe client operations."""
    
    @pytest.mark.asyncio
    async def test_create_wallet(self, mock_agentic_stripe_response):
        """Test wallet creation with initial deposit."""
        client = AgenticStripeClient()
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_agentic_stripe_response["wallet"]
            
            wallet = await client.create_wallet(
                transaction_id="txn_123",
                initial_deposit=Decimal("10000.00")
            )
            
            assert wallet.wallet_id == "wallet_test_123"
            assert wallet.address == "0x1234567890abcdef"
            assert wallet.balance == Decimal("100000.00")
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_configure_milestones(self, mock_agentic_stripe_response):
        """Test milestone configuration for wallet."""
        client = AgenticStripeClient()
        
        milestones = [
            {"id": "m1", "name": "Title Search", "amount": "1200.00", "recipient": "agent_001"},
            {"id": "m2", "name": "Inspection", "amount": "500.00", "recipient": "agent_002"}
        ]
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "configured"}
            
            result = await client.configure_milestones("wallet_test_123", milestones)
            
            assert result["status"] == "configured"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_release_milestone_payment(self, mock_agentic_stripe_response):
        """Test releasing milestone payment."""
        client = AgenticStripeClient()
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_agentic_stripe_response["payment"]
            
            payment = await client.release_milestone_payment(
                wallet_id="wallet_test_123",
                milestone_id="m1",
                recipient="agent_001",
                amount=Decimal("1200.00")
            )
            
            assert payment.payment_id == "pay_test_456"
            assert payment.status == "completed"
            assert payment.tx_hash == "0xabcdef1234567890"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_final_settlement(self, mock_agentic_stripe_response):
        """Test final settlement execution."""
        client = AgenticStripeClient()
        
        distributions = [
            {"recipient": "seller_agent_001", "amount": "370000.00"},
            {"recipient": "buyer_agent_001", "amount": "5000.00"},
            {"recipient": "seller_agent_001", "amount": "5000.00"}
        ]
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "settlement_id": "settle_123",
                "status": "completed",
                "tx_hash": "0xsettlement123"
            }
            
            result = await client.execute_final_settlement("wallet_test_123", distributions)
            
            assert result["settlement_id"] == "settle_123"
            assert result["status"] == "completed"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_wallet_balance(self, mock_agentic_stripe_response):
        """Test querying wallet balance."""
        client = AgenticStripeClient()
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"balance": "98300.00"}
            
            balance = await client.get_wallet_balance("wallet_test_123")
            
            assert balance == Decimal("98300.00")
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_with_retry(self):
        """Test error handling and retry logic."""
        client = AgenticStripeClient()
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            # Simulate failure then success
            mock_request.side_effect = [
                Exception("Network error"),
                {"wallet_id": "wallet_test_123", "status": "active"}
            ]
            
            # Should retry and succeed
            wallet = await client.create_wallet("txn_123", Decimal("10000.00"))
            
            assert wallet.wallet_id == "wallet_test_123"
            assert mock_request.call_count == 2


class TestSmartContractWalletManager:
    """Test Smart Contract Wallet Manager operations."""
    
    @pytest.mark.asyncio
    async def test_create_wallet_with_transaction(self, test_db, sample_transaction, mock_agentic_stripe_response):
        """Test wallet creation linked to transaction."""
        manager = SmartContractWalletManager()
        
        with patch.object(manager.client, 'create_wallet', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = WalletDetails(
                wallet_id="wallet_test_123",
                address="0x1234567890abcdef",
                balance=Decimal("10000.00"),
                status="active"
            )
            
            wallet = await manager.create_wallet(
                sample_transaction.id,
                sample_transaction.earnest_money
            )
            
            assert wallet.wallet_id == "wallet_test_123"
            
            # Verify transaction updated
            test_db.refresh(sample_transaction)
            assert sample_transaction.wallet_id == "wallet_test_123"
    
    @pytest.mark.asyncio
    async def test_configure_verification_milestones(self, mock_agentic_stripe_response):
        """Test configuring verification milestones."""
        manager = SmartContractWalletManager()
        
        milestones = [
            Milestone(
                id="title_search",
                name="Title Search",
                amount=Decimal("1200.00"),
                recipient="title_agent_001",
                conditions=["title_report_approved"],
                auto_release=True
            ),
            Milestone(
                id="inspection",
                name="Inspection",
                amount=Decimal("500.00"),
                recipient="inspector_001",
                conditions=["inspection_report_approved"],
                auto_release=True
            )
        ]
        
        with patch.object(manager.client, 'configure_milestones', new_callable=AsyncMock) as mock_config:
            mock_config.return_value = {"status": "configured"}
            
            result = await manager.configure_milestones("wallet_test_123", milestones)
            
            assert result["status"] == "configured"
            mock_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_release_milestone_payment_with_db_record(self, test_db, sample_transaction):
        """Test milestone payment release with database record."""
        manager = SmartContractWalletManager()
        sample_transaction.wallet_id = "wallet_test_123"
        test_db.commit()
        
        with patch.object(manager.client, 'release_milestone_payment', new_callable=AsyncMock) as mock_release:
            mock_release.return_value = PaymentResult(
                payment_id="pay_test_456",
                status="completed",
                tx_hash="0xabcdef1234567890",
                amount=Decimal("1200.00")
            )
            
            payment = await manager.release_milestone_payment(
                wallet_id="wallet_test_123",
                milestone_id="title_search",
                recipient="title_agent_001",
                amount=Decimal("1200.00")
            )
            
            assert payment.status == "completed"
            assert payment.tx_hash == "0xabcdef1234567890"
    
    @pytest.mark.asyncio
    async def test_execute_final_settlement_with_distributions(self, test_db, sample_transaction):
        """Test final settlement with multiple distributions."""
        manager = SmartContractWalletManager()
        sample_transaction.wallet_id = "wallet_test_123"
        sample_transaction.state = TransactionState.SETTLEMENT_PENDING
        test_db.commit()
        
        distributions = [
            {"recipient": "seller_agent_001", "amount": Decimal("370000.00"), "type": "seller_proceeds"},
            {"recipient": "buyer_agent_001", "amount": Decimal("5000.00"), "type": "commission"},
            {"recipient": "seller_agent_001", "amount": Decimal("5000.00"), "type": "commission"}
        ]
        
        with patch.object(manager.client, 'execute_final_settlement', new_callable=AsyncMock) as mock_settle:
            mock_settle.return_value = {
                "settlement_id": "settle_123",
                "status": "completed",
                "tx_hash": "0xsettlement123"
            }
            
            result = await manager.execute_final_settlement("wallet_test_123", distributions)
            
            assert result["status"] == "completed"
            assert result["tx_hash"] == "0xsettlement123"
    
    @pytest.mark.asyncio
    async def test_insufficient_balance_error(self):
        """Test handling insufficient wallet balance."""
        manager = SmartContractWalletManager()
        
        with patch.object(manager.client, 'get_wallet_balance', new_callable=AsyncMock) as mock_balance:
            mock_balance.return_value = Decimal("500.00")
            
            with patch.object(manager.client, 'release_milestone_payment', new_callable=AsyncMock) as mock_release:
                mock_release.side_effect = Exception("Insufficient balance")
                
                with pytest.raises(Exception, match="Insufficient balance"):
                    await manager.release_milestone_payment(
                        wallet_id="wallet_test_123",
                        milestone_id="title_search",
                        recipient="title_agent_001",
                        amount=Decimal("1200.00")
                    )
    
    @pytest.mark.asyncio
    async def test_payment_retry_on_failure(self):
        """Test automatic retry on payment failure."""
        manager = SmartContractWalletManager()
        
        with patch.object(manager.client, 'release_milestone_payment', new_callable=AsyncMock) as mock_release:
            # First attempt fails, second succeeds
            mock_release.side_effect = [
                Exception("Temporary network error"),
                PaymentResult(
                    payment_id="pay_test_456",
                    status="completed",
                    tx_hash="0xabcdef1234567890",
                    amount=Decimal("1200.00")
                )
            ]
            
            payment = await manager.release_milestone_payment(
                wallet_id="wallet_test_123",
                milestone_id="title_search",
                recipient="title_agent_001",
                amount=Decimal("1200.00")
            )
            
            assert payment.status == "completed"
            assert mock_release.call_count == 2
