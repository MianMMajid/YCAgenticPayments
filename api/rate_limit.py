"""Rate limiting configuration for the Counter API."""
import logging
import os
from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)


class NoOpLimiter:
    """No-op rate limiter for testing."""
    def limit(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator


def get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    
    Uses IP address as the primary identifier, but can be extended
    to use user_id or API key for authenticated requests.
    
    Args:
        request: The incoming request
        
    Returns:
        Identifier string for rate limiting
    """
    # Try to get user_id from request body for authenticated requests
    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"
    
    # Fall back to IP address
    return get_remote_address(request)


# Initialize rate limiter
# Disable rate limiting in test environment
if os.getenv("DISABLE_RATE_LIMITING") == "true":
    limiter = NoOpLimiter()
else:
    limiter = Limiter(
        key_func=get_identifier,
        default_limits=["100/hour"],  # Global default limit
        storage_uri="memory://",  # Use in-memory storage (can be changed to Redis)
        headers_enabled=True,  # Add rate limit headers to responses
    )


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Returns a 429 status with retry-after header.
    
    Args:
        request: The incoming request
        exc: The RateLimitExceeded exception
        
    Returns:
        Response with 429 status and retry-after header
    """
    logger.warning(
        f"Rate limit exceeded for {get_identifier(request)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "identifier": get_identifier(request)
        }
    )
    
    # Get retry-after time from exception
    retry_after = exc.detail.split("Retry after ")[1] if "Retry after" in exc.detail else "60 seconds"
    
    return Response(
        content={
            "error": "Rate limit exceeded",
            "status_code": 429,
            "details": {
                "message": "Too many requests. Please try again later.",
                "retry_after": retry_after
            }
        },
        status_code=429,
        headers={
            "Retry-After": str(int(retry_after.split()[0]) if retry_after.split()[0].isdigit() else "60")
        }
    )


def configure_rate_limiting(app):
    """
    Configure rate limiting for the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Add rate limiter to app state
    app.state.limiter = limiter
    
    # Only add exception handler if not using no-op limiter
    if not isinstance(limiter, NoOpLimiter):
        # Add exception handler for rate limit exceeded
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    
    logger.info("Rate limiting configured")
