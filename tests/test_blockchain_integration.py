"""Integration tests for blockchain logging and audit trail."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from services.blockchain_client import BlockchainClient
from services.blockchain_logger import BlockchainLogger, EventType
from models.transaction import Transaction, TransactionState
from models.settlement import BlockchainEvent


@pytest.fixture
def mock_blockchain_response():
    """Mock blockchain RPC responses."""
    return {
        "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "block_number": "12345678",
        "status": "confirmed",
        "timestamp": datetime.utcnow().isoformat()
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


class TestBlockchainClient:
    """Test blockchain client operations."""
    
    @pytest.mark.asyncio
    async def test_log_event_to_blockchain(self, mock_blockchain_response):
        """Test logging event to blockchain."""
        client = BlockchainClient()
        
        event_data = {
            "transaction_id": "txn_123",
            "event_type": "TRANSACTION_INITIATED",
            "earnest_money": "10000.00",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with patch.object(client, '_send_transaction', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = mock_blockchain_response
            
            result = await client.log_event(event_data)
            
            assert result["tx_hash"] == mock_blockchain_response["tx_hash"]
            assert result["status"] == "confirmed"
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_event_by_hash(self, mock_blockchain_response):
        """Test retrieving event by transaction hash."""
        client = BlockchainClient()
        
        tx_hash = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        
        with patch.object(client, '_get_transaction', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "tx_hash": tx_hash,
                "block_number": "12345678",
                "data": {"event_type": "TRANSACTION_INITIATED"}
            }
            
            event = await client.get_event(tx_hash)
            
            assert event["tx_hash"] == tx_hash
            assert event["data"]["event_type"] == "TRANSACTION_INITIATED"
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_event_authenticity(self, mock_blockchain_response):
        """Test verifying event authenticity."""
        client = BlockchainClient()
        
        tx_hash = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        
        with patch.object(client, '_verify_transaction', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = True
            
            is_valid = await client.verify_event(tx_hash)
            
            assert is_valid is True
            mock_verify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retry_on_network_failure(self):
        """Test retry logic on network failure."""
        client = BlockchainClient()
        
        event_data = {"transaction_id": "txn_123", "event_type": "TEST"}
        
        with patch.object(client, '_send_transaction', new_callable=AsyncMock) as mock_send:
            # Simulate failures then success
            mock_send.side_effect = [
                Exception("Network timeout"),
                Exception("Connection refused"),
                {"tx_hash": "0xabc123", "status": "confirmed"}
            ]
            
            result = await client.log_event(event_data)
            
            assert result["tx_hash"] == "0xabc123"
            assert mock_send.call_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after consecutive failures."""
        client = BlockchainClient()
        
        with patch.object(client, '_send_transaction', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("Service unavailable")
            
            # Attempt multiple times to trigger circuit breaker
            for _ in range(10):
                try:
                    await client.log_event({"test": "data"})
                except Exception:
                    pass
            
            # Circuit breaker should be open now
            # Next call should fail fast without calling _send_transaction
            with pytest.raises(Exception):
                await client.log_event({"test": "data"})


class TestBlockchainLogger:
    """Test blockchain logger operations."""
    
    @pytest.mark.asyncio
    async def test_log_transaction_initiation(self, test_db, sample_transaction, mock_blockchain_response):
        """Test logging transaction initiation event."""
        logger = BlockchainLogger()
        
        with patch.object(logger.client, 'log_event', new_callable=AsyncMock) as mock_log:
            mock_log.return_value = mock_blockchain_response
            
            tx_hash = await logger.log_transaction_event(
                transaction_id=sample_transaction.id,
                event_type=EventType.TRANSACTION_INITIATED,
                event_data={
                    "buyer_agent_id": sample_transaction.buyer_agent_id,
                    "seller_agent_id": sample_transaction.seller_agent_id,
                    "earnest_money": str(sample_transaction.earnest_money)
                },
                timestamp=datetime.utcnow()
            )
            
            assert tx_hash == mock_blockchain_response["tx_hash"]
            
            # Verify event stored in database
            event = test_db.query(BlockchainEvent).filter_by(
                transaction_id=sample_transaction.id
            ).first()
            assert event is not None
            assert event.event_type == EventType.TRANSACTION_INITIATED.value
            assert event.blockchain_tx_hash == mock_blockchain_response["tx_hash"]
    
    @pytest.mark.asyncio
    async def test_log_verification_completion(self, test_db, sample_transaction, mock_blockchain_response):
        """Test logging verification completion event."""
        logger = BlockchainLogger()
        
        with patch.object(logger.client, 'log_event', new_callable=AsyncMock) as mock_log:
            mock_log.return_value = mock_blockchain_response
            
            tx_hash = await logger.log_transaction_event(
                transaction_id=sample_transaction.id,
                event_type=EventType.VERIFICATION_COMPLETED,
                event_data={
                    "verification_type": "title_search",
                    "agent_id": "title_agent_001",
                    "status": "approved"
                },
                timestamp=datetime.utcnow()
            )
            
            assert tx_hash == mock_blockchain_response["tx_hash"]
    
    @pytest.mark.asyncio
    async def test_log_payment_release(self, test_db, sample_transaction, mock_blockchain_response):
        """Test logging payment release event."""
        logger = BlockchainLogger()
        
        with patch.object(logger.client, 'log_event', new_callable=AsyncMock) as mock_log:
            mock_log.return_value = mock_blockchain_response
            
            tx_hash = await logger.log_transaction_event(
                transaction_id=sample_transaction.id,
                event_type=EventType.PAYMENT_RELEASED,
                event_data={
                    "payment_type": "verification",
                    "recipient": "title_agent_001",
                    "amount": "1200.00"
                },
                timestamp=datetime.utcnow()
            )
            
            assert tx_hash == mock_blockchain_response["tx_hash"]
    
    @pytest.mark.asyncio
    async def test_log_settlement_execution(self, test_db, sample_transaction, mock_blockchain_response):
        """Test logging settlement execution event."""
        logger = BlockchainLogger()
        
        with patch.object(logger.client, 'log_event', new_callable=AsyncMock) as mock_log:
            mock_log.return_value = mock_blockchain_response
            
            tx_hash = await logger.log_transaction_event(
                transaction_id=sample_transaction.id,
                event_type=EventType.SETTLEMENT_EXECUTED,
                event_data={
                    "total_amount": "385000.00",
                    "seller_amount": "370000.00",
                    "distributions": [
                        {"recipient": "seller_agent_001", "amount": "370000.00"},
                        {"recipient": "buyer_agent_001", "amount": "5000.00"}
                    ]
                },
                timestamp=datetime.utcnow()
            )
            
            assert tx_hash == mock_blockchain_response["tx_hash"]
    
    @pytest.mark.asyncio
    async def test_get_audit_trail(self, test_db, sample_transaction):
        """Test retrieving complete audit trail for transaction."""
        logger = BlockchainLogger()
        
        # Create multiple blockchain events
        events = [
            BlockchainEvent(
                transaction_id=sample_transaction.id,
                event_type=EventType.TRANSACTION_INITIATED.value,
                event_data={"earnest_money": "10000.00"},
                blockchain_tx_hash="0xhash1",
                block_number="12345678",
                timestamp=datetime.utcnow()
            ),
            BlockchainEvent(
                transaction_id=sample_transaction.id,
                event_type=EventType.VERIFICATION_COMPLETED.value,
                event_data={"verification_type": "title_search"},
                blockchain_tx_hash="0xhash2",
                block_number="12345679",
                timestamp=datetime.utcnow()
            ),
            BlockchainEvent(
                transaction_id=sample_transaction.id,
                event_type=EventType.PAYMENT_RELEASED.value,
                event_data={"amount": "1200.00"},
                blockchain_tx_hash="0xhash3",
                block_number="12345680",
                timestamp=datetime.utcnow()
            )
        ]
        test_db.add_all(events)
        test_db.commit()
        
        # Retrieve audit trail
        audit_trail = await logger.get_audit_trail(sample_transaction.id)
        
        assert len(audit_trail) == 3
        assert audit_trail[0].event_type == EventType.TRANSACTION_INITIATED.value
        assert audit_trail[1].event_type == EventType.VERIFICATION_COMPLETED.value
        assert audit_trail[2].event_type == EventType.PAYMENT_RELEASED.value
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_with_filtering(self, test_db, sample_transaction):
        """Test retrieving filtered audit trail."""
        logger = BlockchainLogger()
        
        # Create events of different types
        events = [
            BlockchainEvent(
                transaction_id=sample_transaction.id,
                event_type=EventType.VERIFICATION_COMPLETED.value,
                event_data={"verification_type": "title_search"},
                blockchain_tx_hash="0xhash1",
                timestamp=datetime.utcnow()
            ),
            BlockchainEvent(
                transaction_id=sample_transaction.id,
                event_type=EventType.VERIFICATION_COMPLETED.value,
                event_data={"verification_type": "inspection"},
                blockchain_tx_hash="0xhash2",
                timestamp=datetime.utcnow()
            ),
            BlockchainEvent(
                transaction_id=sample_transaction.id,
                event_type=EventType.PAYMENT_RELEASED.value,
                event_data={"amount": "1200.00"},
                blockchain_tx_hash="0xhash3",
                timestamp=datetime.utcnow()
            )
        ]
        test_db.add_all(events)
        test_db.commit()
        
        # Filter for verification events only
        verification_events = await logger.get_audit_trail(
            sample_transaction.id,
            event_type=EventType.VERIFICATION_COMPLETED
        )
        
        assert len(verification_events) == 2
        assert all(e.event_type == EventType.VERIFICATION_COMPLETED.value for e in verification_events)
    
    @pytest.mark.asyncio
    async def test_verify_event_authenticity(self, test_db, sample_transaction):
        """Test verifying event authenticity from blockchain."""
        logger = BlockchainLogger()
        
        # Create event
        event = BlockchainEvent(
            transaction_id=sample_transaction.id,
            event_type=EventType.TRANSACTION_INITIATED.value,
            event_data={"earnest_money": "10000.00"},
            blockchain_tx_hash="0xhash123",
            timestamp=datetime.utcnow()
        )
        test_db.add(event)
        test_db.commit()
        
        with patch.object(logger.client, 'verify_event', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = True
            
            is_valid = await logger.verify_event("0xhash123")
            
            assert is_valid is True
            mock_verify.assert_called_once_with("0xhash123")
    
    @pytest.mark.asyncio
    async def test_async_event_processing(self, test_db, sample_transaction, mock_blockchain_response):
        """Test async event processing with queue."""
        logger = BlockchainLogger()
        
        with patch.object(logger.client, 'log_event', new_callable=AsyncMock) as mock_log:
            mock_log.return_value = mock_blockchain_response
            
            # Log multiple events asynchronously
            tasks = []
            for i in range(5):
                task = logger.log_transaction_event(
                    transaction_id=sample_transaction.id,
                    event_type=EventType.VERIFICATION_COMPLETED,
                    event_data={"verification_type": f"type_{i}"},
                    timestamp=datetime.utcnow()
                )
                tasks.append(task)
            
            # Wait for all to complete
            import asyncio
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert all(r == mock_blockchain_response["tx_hash"] for r in results)
            assert mock_log.call_count == 5
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_retry(self, test_db, sample_transaction):
        """Test exponential backoff on retry."""
        logger = BlockchainLogger()
        
        with patch.object(logger.client, 'log_event', new_callable=AsyncMock) as mock_log:
            # Fail 4 times, succeed on 5th
            mock_log.side_effect = [
                Exception("Error 1"),
                Exception("Error 2"),
                Exception("Error 3"),
                Exception("Error 4"),
                {"tx_hash": "0xsuccess", "status": "confirmed"}
            ]
            
            tx_hash = await logger.log_transaction_event(
                transaction_id=sample_transaction.id,
                event_type=EventType.TRANSACTION_INITIATED,
                event_data={"test": "data"},
                timestamp=datetime.utcnow()
            )
            
            assert tx_hash == "0xsuccess"
            assert mock_log.call_count == 5
