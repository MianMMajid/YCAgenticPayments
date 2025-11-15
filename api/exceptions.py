"""Custom exceptions and global exception handlers for the Counter API."""
import logging
import traceback
from typing import Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ExternalServiceError(APIError):
    """Exception raised when an external service fails."""
    
    def __init__(self, service_name: str, message: str, details: dict = None):
        super().__init__(
            message=f"{service_name} service error: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service_name, **(details or {})}
        )


class CacheError(APIError):
    """Exception raised when cache operations fail."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=f"Cache error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class DatabaseError(APIError):
    """Exception raised when database operations fail."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=f"Database error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


# Escrow-specific exceptions

class EscrowError(APIError):
    """Base exception for escrow system errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=f"Escrow error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ValidationError(EscrowError):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=f"Validation failed: {message}",
            details=error_details
        )
        self.status_code = status.HTTP_400_BAD_REQUEST


class PaymentError(EscrowError):
    """Exception raised when payment operations fail."""
    
    def __init__(
        self,
        message: str,
        payment_id: str = None,
        amount: str = None,
        details: dict = None
    ):
        error_details = details or {}
        if payment_id:
            error_details["payment_id"] = payment_id
        if amount:
            error_details["amount"] = amount
        super().__init__(
            message=f"Payment failed: {message}",
            details=error_details
        )
        self.status_code = status.HTTP_402_PAYMENT_REQUIRED


class WorkflowError(EscrowError):
    """Exception raised when workflow execution fails."""
    
    def __init__(
        self,
        message: str,
        transaction_id: str = None,
        workflow_state: str = None,
        details: dict = None
    ):
        error_details = details or {}
        if transaction_id:
            error_details["transaction_id"] = transaction_id
        if workflow_state:
            error_details["workflow_state"] = workflow_state
        super().__init__(
            message=f"Workflow error: {message}",
            details=error_details
        )


class IntegrationError(EscrowError):
    """Exception raised when external integration fails."""
    
    def __init__(
        self,
        service_name: str,
        message: str,
        operation: str = None,
        details: dict = None
    ):
        error_details = details or {}
        error_details["service"] = service_name
        if operation:
            error_details["operation"] = operation
        super().__init__(
            message=f"{service_name} integration error: {message}",
            details=error_details
        )
        self.status_code = status.HTTP_503_SERVICE_UNAVAILABLE


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    Handle custom APIError exceptions.
    
    Args:
        request: The incoming request
        exc: The APIError exception
        
    Returns:
        JSONResponse with error details
    """
    # Log the error with full context
    logger.error(
        f"APIError: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
            "stack_trace": traceback.format_exc()
        }
    )
    
    # Return user-friendly error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code,
            "details": exc.details
        }
    )


async def validation_error_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: The incoming request
        exc: The validation error
        
    Returns:
        JSONResponse with validation error details
    """
    # Extract validation errors
    errors = []
    if isinstance(exc, RequestValidationError):
        errors = exc.errors()
    elif isinstance(exc, ValidationError):
        errors = exc.errors()
    
    # Log validation error
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={
            "errors": errors,
            "body": await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
        }
    )
    
    # Format user-friendly error messages
    formatted_errors = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Invalid value")
        formatted_errors.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "details": {
                "messages": formatted_errors,
                "errors": errors
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions.
    
    Args:
        request: The incoming request
        exc: The unhandled exception
        
    Returns:
        JSONResponse with generic error message
    """
    # Log the full exception with stack trace
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "stack_trace": traceback.format_exc()
        },
        exc_info=True
    )
    
    # Return generic error message (don't expose internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred. Please try again later.",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "details": {
                "type": type(exc).__name__
            }
        }
    )


async def escrow_error_handler(request: Request, exc: EscrowError) -> JSONResponse:
    """
    Handle escrow-specific errors.
    
    Args:
        request: The incoming request
        exc: The EscrowError exception
        
    Returns:
        JSONResponse with error details
    """
    # Log the error with full context
    logger.error(
        f"EscrowError: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
            "error_type": type(exc).__name__
        }
    )
    
    # Return user-friendly error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_type": type(exc).__name__,
            "status_code": exc.status_code,
            "details": exc.details
        }
    )


async def payment_error_handler(request: Request, exc: PaymentError) -> JSONResponse:
    """
    Handle payment-specific errors with additional logging.
    
    Args:
        request: The incoming request
        exc: The PaymentError exception
        
    Returns:
        JSONResponse with error details
    """
    # Log payment errors with high priority
    logger.error(
        f"PaymentError: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
            "payment_id": exc.details.get("payment_id"),
            "amount": exc.details.get("amount")
        }
    )
    
    # Return payment-specific error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_type": "PaymentError",
            "status_code": exc.status_code,
            "details": exc.details,
            "retry_allowed": True  # Indicate that payment can be retried
        }
    )


async def workflow_error_handler(request: Request, exc: WorkflowError) -> JSONResponse:
    """
    Handle workflow-specific errors.
    
    Args:
        request: The incoming request
        exc: The WorkflowError exception
        
    Returns:
        JSONResponse with error details
    """
    # Log workflow errors with context
    logger.error(
        f"WorkflowError: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
            "transaction_id": exc.details.get("transaction_id"),
            "workflow_state": exc.details.get("workflow_state")
        }
    )
    
    # Return workflow-specific error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_type": "WorkflowError",
            "status_code": exc.status_code,
            "details": exc.details
        }
    )


async def integration_error_handler(request: Request, exc: IntegrationError) -> JSONResponse:
    """
    Handle external integration errors.
    
    Args:
        request: The incoming request
        exc: The IntegrationError exception
        
    Returns:
        JSONResponse with error details
    """
    # Log integration errors with service context
    logger.error(
        f"IntegrationError: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
            "service": exc.details.get("service"),
            "operation": exc.details.get("operation")
        }
    )
    
    # Return integration-specific error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_type": "IntegrationError",
            "status_code": exc.status_code,
            "details": exc.details,
            "service_unavailable": True
        }
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Register escrow-specific handlers first (more specific)
    app.add_exception_handler(PaymentError, payment_error_handler)
    app.add_exception_handler(WorkflowError, workflow_error_handler)
    app.add_exception_handler(IntegrationError, integration_error_handler)
    app.add_exception_handler(EscrowError, escrow_error_handler)
    
    # Register general handlers
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")
