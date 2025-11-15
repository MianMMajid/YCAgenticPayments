"""Retry utilities for resilient service operations."""
import asyncio
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry_with_exponential_backoff(max_attempts=3, initial_delay=1.0)
        async def my_function():
            # Function that may fail
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {str(e)}",
                            extra={
                                "function": func.__name__,
                                "attempts": attempt,
                                "error": str(e)
                            }
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed, retrying in {delay}s: {str(e)}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt,
                            "delay": delay,
                            "error": str(e)
                        }
                    )
                    
                    await asyncio.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def retry_with_fixed_delay(
    max_attempts: int = 3,
    delay: float = 5.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retrying async functions with fixed delay.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Fixed delay in seconds between retries
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry_with_fixed_delay(max_attempts=3, delay=5.0)
        async def my_function():
            # Function that may fail
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {str(e)}",
                            extra={
                                "function": func.__name__,
                                "attempts": attempt,
                                "error": str(e)
                            }
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed, retrying in {delay}s: {str(e)}",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt,
                            "delay": delay,
                            "error": str(e)
                        }
                    )
                    
                    await asyncio.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


# Pre-configured retry decorators for common use cases

def retry_payment_operation(func: Callable):
    """
    Retry decorator for payment operations.
    3 retries with exponential backoff (1s, 2s, 4s).
    
    Example:
        @retry_payment_operation
        async def release_payment():
            pass
    """
    return retry_with_exponential_backoff(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=4.0,
        exponential_base=2.0,
        exceptions=(Exception,)
    )(func)


def retry_blockchain_operation(func: Callable):
    """
    Retry decorator for blockchain operations.
    5 retries with exponential backoff (2s, 4s, 8s, 16s, 32s).
    
    Example:
        @retry_blockchain_operation
        async def log_event():
            pass
    """
    return retry_with_exponential_backoff(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=32.0,
        exponential_base=2.0,
        exceptions=(Exception,)
    )(func)


def retry_notification_operation(func: Callable):
    """
    Retry decorator for notification operations.
    3 retries with fixed 5-second intervals.
    
    Example:
        @retry_notification_operation
        async def send_notification():
            pass
    """
    return retry_with_fixed_delay(
        max_attempts=3,
        delay=5.0,
        exceptions=(Exception,)
    )(func)


class RetryContext:
    """Context manager for tracking retry attempts."""
    
    def __init__(self, operation_name: str, max_attempts: int = 3):
        """
        Initialize retry context.
        
        Args:
            operation_name: Name of the operation being retried
            max_attempts: Maximum number of attempts
        """
        self.operation_name = operation_name
        self.max_attempts = max_attempts
        self.attempt = 0
        self.start_time = None
        self.last_error = None
    
    def __enter__(self):
        """Enter retry context."""
        self.attempt += 1
        self.start_time = datetime.utcnow()
        logger.info(
            f"Starting {self.operation_name} attempt {self.attempt}/{self.max_attempts}",
            extra={
                "operation": self.operation_name,
                "attempt": self.attempt,
                "max_attempts": self.max_attempts
            }
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit retry context."""
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type is None:
            logger.info(
                f"{self.operation_name} succeeded on attempt {self.attempt}",
                extra={
                    "operation": self.operation_name,
                    "attempt": self.attempt,
                    "duration": duration
                }
            )
        else:
            self.last_error = exc_val
            logger.warning(
                f"{self.operation_name} failed on attempt {self.attempt}: {str(exc_val)}",
                extra={
                    "operation": self.operation_name,
                    "attempt": self.attempt,
                    "duration": duration,
                    "error": str(exc_val)
                }
            )
        
        return False  # Don't suppress exceptions
    
    @property
    def should_retry(self) -> bool:
        """Check if operation should be retried."""
        return self.attempt < self.max_attempts
    
    @property
    def is_final_attempt(self) -> bool:
        """Check if this is the final attempt."""
        return self.attempt >= self.max_attempts
