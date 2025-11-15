"""Smart Contract Wallet Manager for escrow transactions."""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from services.agentic_stripe_client import (
    AgenticStripeClient,
    Milestone,
    WalletDetails,
    PaymentResult,
    SettlementResult,
    AgenticStripeError,
    AgenticStripePaymentError
)
from models.transaction import Transaction, TransactionState
from models.payment import Payment, PaymentType, PaymentStatus
from models.settlement import Settlement
from config.settings import settings


logger = logging.getLogger(__name__)


class WalletManagerError(Exception):
    """Base exception for wallet manager errors."""
    pass


class SmartContractWalletManager:
    """Manager for smart contract wallet operations."""
    
    def __init__(self, db: Session):
        """Initialize wallet manager.
        
        Args:
            db: Database session
        """
        self.db = db
        self.client = AgenticStripeClient()
    
    async def close(self):
        """Close the Agentic Stripe client."""
        await self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    
    async def create_wallet(
        self,
        transaction: Transaction,
        initial_deposit: Decimal
    ) -> WalletDetails:
        """Create a new smart contract wallet for a transaction.
        
        Args:
            transaction: Transaction entity
            initial_deposit: Initial deposit amount (earnest money)
        
        Returns:
            WalletDetails with wallet information
        
        Raises:
            WalletManagerError: If wallet creation fails
        """
        try:
            logger.info(f"Creating wallet for transaction {transaction.id}")
            
            # Create wallet via Agentic Stripe
            metadata = {
                "transaction_id": transaction.id,
                "buyer_agent_id": transaction.buyer_agent_id,
                "seller_agent_id": transaction.seller_agent_id,
                "property_id": transaction.property_id
            }
            
            wallet = await self.client.create_wallet(
                transaction_id=transaction.id,
                initial_deposit=initial_deposit,
                metadata=metadata
            )
            
            # Update transaction with wallet ID
            transaction.wallet_id = wallet.wallet_id
            transaction.state = TransactionState.FUNDED
            self.db.commit()
            
            # Create payment record for earnest money
            payment = Payment(
                transaction_id=transaction.id,
                wallet_id=wallet.wallet_id,
                payment_type=PaymentType.EARNEST_MONEY,
                recipient_id=wallet.wallet_id,  # Deposited to wallet
                amount=initial_deposit,
                status=PaymentStatus.COMPLETED,
                blockchain_tx_hash="",  # Will be updated by blockchain logger
                initiated_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            self.db.add(payment)
            self.db.commit()
            
            logger.info(f"Wallet created successfully: {wallet.wallet_id}")
            return wallet
            
        except AgenticStripeError as e:
            logger.error(f"Agentic Stripe error creating wallet: {str(e)}")
            self.db.rollback()
            raise WalletManagerError(f"Failed to create wallet: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating wallet: {str(e)}")
            self.db.rollback()
            raise WalletManagerError(f"Unexpected error: {str(e)}")

    
    async def configure_milestones(
        self,
        transaction: Transaction,
        milestones: List[Milestone]
    ) -> None:
        """Configure milestones for a transaction's wallet.
        
        Args:
            transaction: Transaction entity
            milestones: List of milestone configurations
        
        Raises:
            WalletManagerError: If milestone configuration fails
        """
        try:
            if not transaction.wallet_id:
                raise WalletManagerError("Transaction does not have a wallet")
            
            logger.info(f"Configuring milestones for transaction {transaction.id}")
            
            # Configure milestones via Agentic Stripe
            await self.client.configure_milestones(
                wallet_id=transaction.wallet_id,
                milestones=milestones
            )
            
            logger.info(f"Milestones configured for transaction {transaction.id}")
            
        except AgenticStripeError as e:
            logger.error(f"Agentic Stripe error configuring milestones: {str(e)}")
            raise WalletManagerError(f"Failed to configure milestones: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error configuring milestones: {str(e)}")
            raise WalletManagerError(f"Unexpected error: {str(e)}")

    
    async def release_milestone_payment(
        self,
        transaction: Transaction,
        milestone_id: str,
        recipient_id: str,
        amount: Decimal,
        payment_type: PaymentType = PaymentType.VERIFICATION
    ) -> PaymentResult:
        """Release payment for a completed milestone.
        
        Args:
            transaction: Transaction entity
            milestone_id: Milestone identifier
            recipient_id: Payment recipient ID
            amount: Payment amount
            payment_type: Type of payment (default: VERIFICATION)
        
        Returns:
            PaymentResult with payment details
        
        Raises:
            WalletManagerError: If payment release fails
        """
        try:
            if not transaction.wallet_id:
                raise WalletManagerError("Transaction does not have a wallet")
            
            logger.info(f"Releasing milestone payment for transaction {transaction.id}")
            
            # Release payment via Agentic Stripe
            result = await self.client.release_milestone_payment(
                wallet_id=transaction.wallet_id,
                milestone_id=milestone_id,
                recipient=recipient_id,
                amount=amount
            )
            
            # Create payment record
            payment = Payment(
                transaction_id=transaction.id,
                wallet_id=transaction.wallet_id,
                payment_type=payment_type,
                recipient_id=recipient_id,
                amount=amount,
                status=PaymentStatus.COMPLETED if result.status == "completed" else PaymentStatus.PROCESSING,
                blockchain_tx_hash=result.transaction_hash,
                initiated_at=datetime.utcnow(),
                completed_at=result.timestamp if result.status == "completed" else None
            )
            self.db.add(payment)
            self.db.commit()
            
            logger.info(f"Payment released: {result.payment_id}")
            return result
            
        except AgenticStripePaymentError as e:
            logger.error(f"Agentic Stripe payment error: {str(e)}")
            
            # Create failed payment record
            payment = Payment(
                transaction_id=transaction.id,
                wallet_id=transaction.wallet_id,
                payment_type=payment_type,
                recipient_id=recipient_id,
                amount=amount,
                status=PaymentStatus.FAILED,
                blockchain_tx_hash="",
                initiated_at=datetime.utcnow()
            )
            self.db.add(payment)
            self.db.commit()
            
            raise WalletManagerError(f"Failed to release payment: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error releasing payment: {str(e)}")
            self.db.rollback()
            raise WalletManagerError(f"Unexpected error: {str(e)}")

    
    async def execute_final_settlement(
        self,
        transaction: Transaction,
        seller_amount: Decimal,
        buyer_agent_commission: Decimal,
        seller_agent_commission: Decimal,
        closing_costs: Decimal,
        additional_distributions: Optional[List[Dict[str, Any]]] = None
    ) -> SettlementResult:
        """Execute final settlement with fund distribution.
        
        Args:
            transaction: Transaction entity
            seller_amount: Amount to distribute to seller
            buyer_agent_commission: Buyer agent commission
            seller_agent_commission: Seller agent commission
            closing_costs: Total closing costs
            additional_distributions: Additional distribution details
        
        Returns:
            SettlementResult with settlement details
        
        Raises:
            WalletManagerError: If settlement execution fails
        """
        try:
            if not transaction.wallet_id:
                raise WalletManagerError("Transaction does not have a wallet")
            
            logger.info(f"Executing final settlement for transaction {transaction.id}")
            
            # Build distributions list
            distributions = [
                {
                    "recipient": transaction.seller_agent_id,
                    "amount": seller_amount,
                    "description": "Seller payment"
                },
                {
                    "recipient": transaction.buyer_agent_id,
                    "amount": buyer_agent_commission,
                    "description": "Buyer agent commission"
                },
                {
                    "recipient": transaction.seller_agent_id,
                    "amount": seller_agent_commission,
                    "description": "Seller agent commission"
                }
            ]
            
            # Add additional distributions if provided
            if additional_distributions:
                distributions.extend(additional_distributions)
            
            # Execute settlement via Agentic Stripe
            result = await self.client.execute_final_settlement(
                wallet_id=transaction.wallet_id,
                distributions=distributions
            )
            
            # Calculate total amount
            total_amount = seller_amount + buyer_agent_commission + seller_agent_commission + closing_costs
            
            # Create settlement record
            settlement = Settlement(
                transaction_id=transaction.id,
                total_amount=total_amount,
                seller_amount=seller_amount,
                buyer_agent_commission=buyer_agent_commission,
                seller_agent_commission=seller_agent_commission,
                closing_costs=closing_costs,
                distributions=result.distributions,
                blockchain_tx_hash=result.transaction_hash,
                executed_at=result.timestamp
            )
            self.db.add(settlement)
            
            # Update transaction state
            transaction.state = TransactionState.SETTLED
            transaction.actual_closing_date = datetime.utcnow()
            
            # Create payment records for each distribution
            for dist in distributions:
                payment = Payment(
                    transaction_id=transaction.id,
                    wallet_id=transaction.wallet_id,
                    payment_type=PaymentType.SETTLEMENT,
                    recipient_id=dist["recipient"],
                    amount=Decimal(str(dist["amount"])),
                    status=PaymentStatus.COMPLETED if result.status == "completed" else PaymentStatus.PROCESSING,
                    blockchain_tx_hash=result.transaction_hash,
                    initiated_at=datetime.utcnow(),
                    completed_at=result.timestamp if result.status == "completed" else None
                )
                self.db.add(payment)
            
            self.db.commit()
            
            logger.info(f"Settlement executed: {result.settlement_id}")
            return result
            
        except AgenticStripePaymentError as e:
            logger.error(f"Agentic Stripe settlement error: {str(e)}")
            self.db.rollback()
            raise WalletManagerError(f"Failed to execute settlement: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error executing settlement: {str(e)}")
            self.db.rollback()
            raise WalletManagerError(f"Unexpected error: {str(e)}")

    
    async def get_wallet_balance(
        self,
        transaction: Transaction
    ) -> Decimal:
        """Get current wallet balance for a transaction.
        
        Args:
            transaction: Transaction entity
        
        Returns:
            Current wallet balance
        
        Raises:
            WalletManagerError: If balance query fails
        """
        try:
            if not transaction.wallet_id:
                raise WalletManagerError("Transaction does not have a wallet")
            
            balance = await self.client.get_wallet_balance(transaction.wallet_id)
            return balance
            
        except AgenticStripeError as e:
            logger.error(f"Error querying wallet balance: {str(e)}")
            raise WalletManagerError(f"Failed to query balance: {str(e)}")
    
    async def get_wallet_state(
        self,
        transaction: Transaction
    ) -> Dict[str, Any]:
        """Get wallet state including balance and recent transactions.
        
        Args:
            transaction: Transaction entity
        
        Returns:
            Dictionary with wallet state information
        
        Raises:
            WalletManagerError: If state query fails
        """
        try:
            if not transaction.wallet_id:
                raise WalletManagerError("Transaction does not have a wallet")
            
            # Get balance
            balance = await self.client.get_wallet_balance(transaction.wallet_id)
            
            # Get recent transaction history
            history = await self.client.get_transaction_history(
                wallet_id=transaction.wallet_id,
                limit=10
            )
            
            # Get payments from database
            payments = self.db.query(Payment).filter(
                Payment.transaction_id == transaction.id
            ).order_by(Payment.created_at.desc()).limit(10).all()
            
            return {
                "wallet_id": transaction.wallet_id,
                "balance": balance,
                "transaction_state": transaction.state.value,
                "recent_blockchain_transactions": [
                    {
                        "transaction_id": item.transaction_id,
                        "type": item.transaction_type,
                        "amount": item.amount,
                        "recipient": item.recipient,
                        "timestamp": item.timestamp.isoformat(),
                        "status": item.status
                    }
                    for item in history
                ],
                "recent_payments": [
                    {
                        "payment_id": p.id,
                        "type": p.payment_type.value,
                        "amount": p.amount,
                        "recipient_id": p.recipient_id,
                        "status": p.status.value,
                        "initiated_at": p.initiated_at.isoformat(),
                        "completed_at": p.completed_at.isoformat() if p.completed_at else None
                    }
                    for p in payments
                ]
            }
            
        except AgenticStripeError as e:
            logger.error(f"Error querying wallet state: {str(e)}")
            raise WalletManagerError(f"Failed to query wallet state: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error querying wallet state: {str(e)}")
            raise WalletManagerError(f"Unexpected error: {str(e)}")
