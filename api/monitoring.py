"""Monitoring and error tracking integration."""
import logging
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from config.settings import settings

logger = logging.getLogger(__name__)


def init_sentry():
    """
    Initialize Sentry error tracking with FastAPI integration.
    
    Configures Sentry with:
    - Error sampling and environment tags
    - FastAPI, SQLAlchemy, and Redis integrations
    - Custom context for user_id and tool_name
    """
    if not settings.sentry_dsn:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return
    
    try:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            profiles_sample_rate=settings.sentry_profiles_sample_rate,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                ),
            ],
            # Send PII (Personally Identifiable Information) - set to False in production
            send_default_pii=False,
            # Attach stack traces to messages
            attach_stacktrace=True,
            # Maximum breadcrumbs
            max_breadcrumbs=50,
            # Before send hook to add custom context
            before_send=before_send_hook,
        )
        
        logger.info(f"Sentry initialized for environment: {settings.environment}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_hook(event, hint):
    """
    Hook called before sending events to Sentry.
    
    Allows filtering or modifying events before they're sent.
    
    Args:
        event: The event dictionary
        hint: Additional context about the event
        
    Returns:
        Modified event or None to drop the event
    """
    # Add custom tags if available
    if "request" in event.get("contexts", {}):
        request_context = event["contexts"]["request"]
        
        # Extract user_id from request if available
        if "data" in request_context:
            data = request_context.get("data", {})
            if isinstance(data, dict) and "user_id" in data:
                event.setdefault("tags", {})["user_id"] = data["user_id"]
    
    return event


def set_user_context(user_id: str, email: Optional[str] = None):
    """
    Set user context for Sentry error tracking.
    
    Args:
        user_id: User identifier
        email: User email (optional)
    """
    sentry_sdk.set_user({
        "id": user_id,
        "email": email
    })


def set_tool_context(tool_name: str, **kwargs):
    """
    Set tool execution context for Sentry error tracking.
    
    Args:
        tool_name: Name of the tool being executed
        **kwargs: Additional context data
    """
    sentry_sdk.set_context("tool", {
        "name": tool_name,
        **kwargs
    })


def capture_exception(error: Exception, **context):
    """
    Manually capture an exception to Sentry with additional context.
    
    Args:
        error: The exception to capture
        **context: Additional context data
    """
    if context:
        sentry_sdk.set_context("custom", context)
    
    sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **context):
    """
    Capture a message to Sentry.
    
    Args:
        message: The message to capture
        level: Message level (debug, info, warning, error, fatal)
        **context: Additional context data
    """
    if context:
        sentry_sdk.set_context("custom", context)
    
    sentry_sdk.capture_message(message, level=level)


def add_breadcrumb(message: str, category: str = "default", level: str = "info", **data):
    """
    Add a breadcrumb for debugging context.
    
    Breadcrumbs are a trail of events that happened prior to an error.
    
    Args:
        message: Breadcrumb message
        category: Breadcrumb category (e.g., "http", "db", "cache")
        level: Breadcrumb level (debug, info, warning, error)
        **data: Additional data
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data
    )


def get_circuit_breaker_states():
    """
    Get the current state of all circuit breakers.
    
    Returns:
        Dict mapping circuit breaker names to their states
    """
    from services.circuit_breaker import circuit_breaker_registry
    
    return circuit_breaker_registry.get_all_states()


def reset_circuit_breakers():
    """Reset all circuit breakers to closed state."""
    from services.circuit_breaker import circuit_breaker_registry
    
    circuit_breaker_registry.reset_all()
    logger.info("All circuit breakers have been reset")
