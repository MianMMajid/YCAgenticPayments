"""Structured logging configuration with correlation IDs."""
import logging
import json
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    
    Includes correlation IDs for request tracing and additional context fields.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        # Base log structure
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add any additional attributes from the record's __dict__
        # that aren't standard logging attributes
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
            'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'extra_fields'
        }
        
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                # Skip non-serializable values
                try:
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        return json.dumps(log_data)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and track correlation IDs for request tracing.
    
    Correlation IDs are:
    - Generated for each request if not provided
    - Extracted from X-Correlation-ID header if present
    - Added to response headers
    - Available in all logs during request processing
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and manage correlation ID.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response with correlation ID header
        """
        # Get or generate correlation ID
        correlation_id = request.headers.get('X-Correlation-ID')
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Set correlation ID in context
        correlation_id_var.set(correlation_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = correlation_id
        
        return response


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.
    
    Returns:
        Correlation ID if available, None otherwise
    """
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str):
    """
    Set the correlation ID in context.
    
    Args:
        correlation_id: The correlation ID to set
    """
    correlation_id_var.set(correlation_id)


class StructuredLogger:
    """
    Wrapper for structured logging with additional context.
    
    Provides methods for logging with structured data and correlation IDs.
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (typically __name__)
        """
        self.logger = logging.getLogger(name)
    
    def _log(self, level: int, message: str, **kwargs):
        """
        Internal log method with structured data.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional structured data
        """
        # Create a log record with extra fields
        extra = {'extra_fields': kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured data."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with structured data."""
        extra = {'extra_fields': kwargs}
        self.logger.exception(message, extra=extra)


def configure_structured_logging(
    level: str = "INFO",
    enable_json: bool = True,
    log_file: Optional[str] = None
):
    """
    Configure structured logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Whether to use JSON formatting
        log_file: Optional file path for log output
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Set formatter
    if enable_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure third-party loggers to reduce noise
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    root_logger.info(
        "Structured logging configured",
        extra={
            "log_level": level,
            "json_enabled": enable_json,
            "log_file": log_file
        }
    )


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# Log level filtering utilities
class LogLevelFilter(logging.Filter):
    """
    Filter logs by level range.
    
    Allows filtering logs to only include specific level ranges.
    """
    
    def __init__(self, min_level: int = logging.DEBUG, max_level: int = logging.CRITICAL):
        """
        Initialize filter.
        
        Args:
            min_level: Minimum log level to include
            max_level: Maximum log level to include
        """
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record by level.
        
        Args:
            record: Log record to filter
            
        Returns:
            True if record should be logged, False otherwise
        """
        return self.min_level <= record.levelno <= self.max_level


class ComponentFilter(logging.Filter):
    """
    Filter logs by component/module name.
    
    Allows filtering logs to only include specific components.
    """
    
    def __init__(self, components: list[str]):
        """
        Initialize filter.
        
        Args:
            components: List of component names to include
        """
        super().__init__()
        self.components = components
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record by component.
        
        Args:
            record: Log record to filter
            
        Returns:
            True if record should be logged, False otherwise
        """
        return any(record.name.startswith(comp) for comp in self.components)


# Context managers for temporary logging context
class LogContext:
    """
    Context manager for adding temporary logging context.
    
    Usage:
        with LogContext(transaction_id="123", user_id="456"):
            logger.info("Processing transaction")
    """
    
    def __init__(self, **context):
        """
        Initialize log context.
        
        Args:
            **context: Context key-value pairs
        """
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        """Enter context and add context to logs."""
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        self.old_factory = old_factory
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore original factory."""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)
