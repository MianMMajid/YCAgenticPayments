"""Circuit breaker implementation for resilient external service calls."""
import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, service_name: str, message: str = None):
        self.service_name = service_name
        self.message = message or f"Circuit breaker is open for {service_name}"
        super().__init__(self.message)


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail fast
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the service/circuit
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        
        logger.info(
            f"Circuit breaker initialized: {name}",
            extra={
                "circuit": name,
                "failure_threshold": failure_threshold,
                "recovery_timeout": recovery_timeout
            }
        )
    
    async def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Result from function
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception if circuit is closed
        """
        # Check if circuit should transition to half-open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(
                    f"Circuit breaker transitioning to HALF_OPEN: {self.name}",
                    extra={"circuit": self.name, "state": "half_open"}
                )
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                # Circuit is still open, fail fast
                logger.warning(
                    f"Circuit breaker is OPEN, failing fast: {self.name}",
                    extra={
                        "circuit": self.name,
                        "state": "open",
                        "failure_count": self.failure_count
                    }
                )
                raise CircuitBreakerError(self.name)
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Record success
            self._on_success()
            
            return result
            
        except self.expected_exception as e:
            # Record failure
            self._on_failure()
            
            # Re-raise the original exception
            raise
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.last_failure_time = None
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            # If we have enough successes, close the circuit
            if self.success_count >= 2:
                logger.info(
                    f"Circuit breaker closing after successful recovery: {self.name}",
                    extra={
                        "circuit": self.name,
                        "state": "closed",
                        "success_count": self.success_count
                    }
                )
                self.state = CircuitState.CLOSED
                self.success_count = 0
                self.opened_at = None
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(
            f"Circuit breaker recorded failure: {self.name}",
            extra={
                "circuit": self.name,
                "failure_count": self.failure_count,
                "threshold": self.failure_threshold,
                "state": self.state
            }
        )
        
        # If in half-open state, immediately open on failure
        if self.state == CircuitState.HALF_OPEN:
            logger.warning(
                f"Circuit breaker opening after failed recovery attempt: {self.name}",
                extra={
                    "circuit": self.name,
                    "state": "open"
                }
            )
            self.state = CircuitState.OPEN
            self.opened_at = datetime.utcnow()
            self.success_count = 0
        
        # If failure threshold reached, open the circuit
        elif self.failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit breaker opening due to failures: {self.name}",
                extra={
                    "circuit": self.name,
                    "state": "open",
                    "failure_count": self.failure_count,
                    "threshold": self.failure_threshold
                }
            )
            self.state = CircuitState.OPEN
            self.opened_at = datetime.utcnow()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset."""
        if self.opened_at is None:
            return False
        
        elapsed = (datetime.utcnow() - self.opened_at).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current circuit breaker state.
        
        Returns:
            Dict with state information
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None
        }
    
    def reset(self):
        """Manually reset the circuit breaker."""
        logger.info(
            f"Circuit breaker manually reset: {self.name}",
            extra={"circuit": self.name}
        )
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        """Initialize circuit breaker registry."""
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def register(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ) -> CircuitBreaker:
        """
        Register a new circuit breaker.
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
            
        Returns:
            CircuitBreaker instance
        """
        if name in self._breakers:
            logger.warning(f"Circuit breaker already registered: {name}")
            return self._breakers[name]
        
        breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )
        
        self._breakers[name] = breaker
        logger.info(f"Circuit breaker registered: {name}")
        
        return breaker
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """
        Get circuit breaker by name.
        
        Args:
            name: Name of the circuit breaker
            
        Returns:
            CircuitBreaker instance or None
        """
        return self._breakers.get(name)
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get states of all circuit breakers.
        
        Returns:
            Dict mapping circuit names to their states
        """
        return {
            name: breaker.get_state()
            for name, breaker in self._breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()
        logger.info("All circuit breakers reset")


# Global circuit breaker registry
circuit_breaker_registry = CircuitBreakerRegistry()


def with_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception
):
    """
    Decorator for protecting async functions with circuit breaker.
    
    Args:
        name: Name of the circuit breaker
        failure_threshold: Number of failures before opening
        recovery_timeout: Seconds before attempting recovery
        expected_exception: Exception type to catch
        
    Returns:
        Decorated function
        
    Example:
        @with_circuit_breaker("my_service", failure_threshold=5, recovery_timeout=60.0)
        async def call_external_service():
            pass
    """
    def decorator(func: Callable):
        # Register circuit breaker
        breaker = circuit_breaker_registry.register(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        return wrapper
    
    return decorator


# Pre-configured circuit breakers for escrow services

def agentic_stripe_circuit_breaker(func: Callable):
    """
    Circuit breaker for Agentic Stripe operations.
    5 failures, 60s half-open timeout.
    
    Example:
        @agentic_stripe_circuit_breaker
        async def create_wallet():
            pass
    """
    return with_circuit_breaker(
        name="agentic_stripe",
        failure_threshold=5,
        recovery_timeout=60.0,
        expected_exception=Exception
    )(func)


def blockchain_circuit_breaker(func: Callable):
    """
    Circuit breaker for blockchain operations.
    10 failures, 30s half-open timeout.
    
    Example:
        @blockchain_circuit_breaker
        async def log_event():
            pass
    """
    return with_circuit_breaker(
        name="blockchain",
        failure_threshold=10,
        recovery_timeout=30.0,
        expected_exception=Exception
    )(func)


def notification_circuit_breaker(func: Callable):
    """
    Circuit breaker for notification operations.
    3 failures, 120s half-open timeout.
    
    Example:
        @notification_circuit_breaker
        async def send_notification():
            pass
    """
    return with_circuit_breaker(
        name="notification",
        failure_threshold=3,
        recovery_timeout=120.0,
        expected_exception=Exception
    )(func)
