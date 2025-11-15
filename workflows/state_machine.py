"""Transaction state machine for workflow orchestration."""
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum
import logging

from models.transaction import Transaction, TransactionState
from models.database import get_db

logger = logging.getLogger(__name__)


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class TransactionStateMachine:
    """
    State machine for managing transaction state transitions.
    
    Implements state validation, transition guards, and event emission
    for transaction lifecycle management.
    """
    
    # Define valid state transitions
    VALID_TRANSITIONS: Dict[TransactionState, List[TransactionState]] = {
        TransactionState.INITIATED: [
            TransactionState.FUNDED,
            TransactionState.CANCELLED
        ],
        TransactionState.FUNDED: [
            TransactionState.VERIFICATION_IN_PROGRESS,
            TransactionState.CANCELLED,
            TransactionState.DISPUTED
        ],
        TransactionState.VERIFICATION_IN_PROGRESS: [
            TransactionState.VERIFICATION_COMPLETE,
            TransactionState.CANCELLED,
            TransactionState.DISPUTED
        ],
        TransactionState.VERIFICATION_COMPLETE: [
            TransactionState.SETTLEMENT_PENDING,
            TransactionState.DISPUTED
        ],
        TransactionState.SETTLEMENT_PENDING: [
            TransactionState.SETTLED,
            TransactionState.DISPUTED
        ],
        TransactionState.SETTLED: [],  # Terminal state
        TransactionState.DISPUTED: [
            TransactionState.VERIFICATION_IN_PROGRESS,
            TransactionState.SETTLEMENT_PENDING,
            TransactionState.CANCELLED
        ],
        TransactionState.CANCELLED: []  # Terminal state
    }
    
    def __init__(self, transaction: Transaction):
        """
        Initialize state machine for a transaction.
        
        Args:
            transaction: The transaction to manage
        """
        self.transaction = transaction
        self._event_listeners: Dict[str, List[Callable]] = {}
    
    def can_transition_to(self, target_state: TransactionState) -> bool:
        """
        Check if transition to target state is valid.
        
        Args:
            target_state: The state to transition to
            
        Returns:
            True if transition is valid, False otherwise
        """
        current_state = self.transaction.state
        valid_targets = self.VALID_TRANSITIONS.get(current_state, [])
        return target_state in valid_targets
    
    def validate_transition(
        self,
        target_state: TransactionState,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Validate if transition is allowed based on business rules.
        
        Args:
            target_state: The state to transition to
            context: Additional context for validation
            
        Returns:
            True if transition passes all guards, False otherwise
        """
        # Check if transition is structurally valid
        if not self.can_transition_to(target_state):
            return False
        
        # Apply transition guards based on target state
        context = context or {}
        
        if target_state == TransactionState.FUNDED:
            # Guard: Earnest money must be deposited
            return context.get("earnest_money_deposited", False)
        
        elif target_state == TransactionState.VERIFICATION_IN_PROGRESS:
            # Guard: Wallet must be created and funded
            return bool(self.transaction.wallet_id)
        
        elif target_state == TransactionState.VERIFICATION_COMPLETE:
            # Guard: All verification tasks must be completed
            return context.get("all_verifications_complete", False)
        
        elif target_state == TransactionState.SETTLEMENT_PENDING:
            # Guard: All verifications must be approved
            return context.get("all_verifications_approved", False)
        
        elif target_state == TransactionState.SETTLED:
            # Guard: Settlement must be executed
            return context.get("settlement_executed", False)
        
        # Default: allow transition
        return True
    
    async def transition_to(
        self,
        target_state: TransactionState,
        context: Optional[Dict[str, Any]] = None,
        persist: bool = True
    ) -> None:
        """
        Transition transaction to target state.
        
        Args:
            target_state: The state to transition to
            context: Additional context for validation and events
            persist: Whether to persist the state change to database
            
        Raises:
            StateTransitionError: If transition is invalid
        """
        current_state = self.transaction.state
        
        # Validate transition
        if not self.can_transition_to(target_state):
            raise StateTransitionError(
                f"Invalid transition from {current_state.value} to {target_state.value}"
            )
        
        if not self.validate_transition(target_state, context):
            raise StateTransitionError(
                f"Transition guard failed for {current_state.value} -> {target_state.value}"
            )
        
        # Update transaction state
        old_state = self.transaction.state
        self.transaction.state = target_state
        self.transaction.updated_at = datetime.utcnow()
        
        # Persist to database if requested
        if persist:
            await self._persist_state()
        
        # Emit state change event
        await self._emit_event("state_changed", {
            "transaction_id": self.transaction.id,
            "old_state": old_state.value,
            "new_state": target_state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        })
        
        logger.info(
            f"Transaction {self.transaction.id} transitioned from "
            f"{old_state.value} to {target_state.value}"
        )
    
    async def _persist_state(self) -> None:
        """Persist transaction state to database."""
        db = next(get_db())
        try:
            db.add(self.transaction)
            db.commit()
            db.refresh(self.transaction)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to persist transaction state: {e}")
            raise
        finally:
            db.close()
    
    def on_event(self, event_name: str, callback: Callable) -> None:
        """
        Register event listener.
        
        Args:
            event_name: Name of the event to listen for
            callback: Callback function to invoke when event occurs
        """
        if event_name not in self._event_listeners:
            self._event_listeners[event_name] = []
        self._event_listeners[event_name].append(callback)
    
    async def _emit_event(self, event_name: str, event_data: Dict[str, Any]) -> None:
        """
        Emit event to all registered listeners.
        
        Args:
            event_name: Name of the event
            event_data: Event data to pass to listeners
        """
        listeners = self._event_listeners.get(event_name, [])
        for listener in listeners:
            try:
                if callable(listener):
                    # Support both sync and async callbacks
                    if hasattr(listener, '__call__'):
                        result = listener(event_data)
                        # Await if it's a coroutine
                        if hasattr(result, '__await__'):
                            await result
            except Exception as e:
                logger.error(f"Error in event listener for {event_name}: {e}")
    
    def get_current_state(self) -> TransactionState:
        """Get current transaction state."""
        return self.transaction.state
    
    def get_valid_transitions(self) -> List[TransactionState]:
        """Get list of valid transitions from current state."""
        return self.VALID_TRANSITIONS.get(self.transaction.state, [])
    
    def is_terminal_state(self) -> bool:
        """Check if transaction is in a terminal state."""
        return self.transaction.state in [
            TransactionState.SETTLED,
            TransactionState.CANCELLED
        ]
