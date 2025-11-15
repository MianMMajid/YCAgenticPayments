"""Custom metrics and logging for the Counter API."""
import logging
import time
from typing import Optional, Dict, Any
from functools import wraps
from contextlib import contextmanager

from fastapi import Request

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collector for custom application metrics.
    
    This class provides methods to track and log various metrics including:
    - Tool execution time
    - External API latency
    - Cache hit rates
    - Active users
    - Offers generated
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.cache_hits = 0
        self.cache_misses = 0
        self.active_users = set()
        self.offers_generated = 0
        
    def track_tool_execution(self, tool_name: str, duration_ms: float, success: bool = True):
        """
        Track tool execution time.
        
        Args:
            tool_name: Name of the tool executed
            duration_ms: Execution duration in milliseconds
            success: Whether the execution was successful
        """
        logger.info(
            f"Tool execution: {tool_name}",
            extra={
                "metric_type": "tool_execution",
                "tool_name": tool_name,
                "duration_ms": duration_ms,
                "success": success
            }
        )
        
        # In production, send to Datadog or CloudWatch
        # Example: statsd.histogram('tool.execution.time', duration_ms, tags=[f'tool:{tool_name}'])
    
    def track_external_api_call(
        self,
        service_name: str,
        endpoint: str,
        duration_ms: float,
        success: bool = True,
        status_code: Optional[int] = None
    ):
        """
        Track external API call latency.
        
        Args:
            service_name: Name of the external service (e.g., 'rentcast', 'fema')
            endpoint: API endpoint called
            duration_ms: Call duration in milliseconds
            success: Whether the call was successful
            status_code: HTTP status code (if applicable)
        """
        logger.info(
            f"External API call: {service_name}.{endpoint}",
            extra={
                "metric_type": "external_api_call",
                "service_name": service_name,
                "endpoint": endpoint,
                "duration_ms": duration_ms,
                "success": success,
                "status_code": status_code
            }
        )
        
        # In production, send to Datadog or CloudWatch
        # Example: statsd.histogram('external_api.latency', duration_ms, tags=[f'service:{service_name}'])
    
    def track_cache_hit(self, cache_key: str):
        """
        Track cache hit.
        
        Args:
            cache_key: The cache key that was hit
        """
        self.cache_hits += 1
        
        logger.debug(
            f"Cache hit: {cache_key}",
            extra={
                "metric_type": "cache_hit",
                "cache_key": cache_key,
                "total_hits": self.cache_hits
            }
        )
        
        # In production, send to Datadog or CloudWatch
        # Example: statsd.increment('cache.hit', tags=[f'key:{cache_key}'])
    
    def track_cache_miss(self, cache_key: str):
        """
        Track cache miss.
        
        Args:
            cache_key: The cache key that was missed
        """
        self.cache_misses += 1
        
        logger.debug(
            f"Cache miss: {cache_key}",
            extra={
                "metric_type": "cache_miss",
                "cache_key": cache_key,
                "total_misses": self.cache_misses
            }
        )
        
        # In production, send to Datadog or CloudWatch
        # Example: statsd.increment('cache.miss', tags=[f'key:{cache_key}'])
    
    def get_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate.
        
        Returns:
            Cache hit rate as a percentage (0-100)
        """
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        
        hit_rate = (self.cache_hits / total) * 100
        
        logger.info(
            f"Cache hit rate: {hit_rate:.2f}%",
            extra={
                "metric_type": "cache_hit_rate",
                "hit_rate": hit_rate,
                "total_hits": self.cache_hits,
                "total_misses": self.cache_misses
            }
        )
        
        return hit_rate
    
    def track_active_user(self, user_id: str):
        """
        Track active user.
        
        Args:
            user_id: User identifier
        """
        self.active_users.add(user_id)
        
        logger.debug(
            f"Active user: {user_id}",
            extra={
                "metric_type": "active_user",
                "user_id": user_id,
                "total_active_users": len(self.active_users)
            }
        )
        
        # In production, send to Datadog or CloudWatch
        # Example: statsd.gauge('users.active', len(self.active_users))
    
    def track_offer_generated(self, user_id: str, property_id: str, offer_price: int):
        """
        Track offer generation.
        
        Args:
            user_id: User identifier
            property_id: Property identifier
            offer_price: Offer price
        """
        self.offers_generated += 1
        
        logger.info(
            f"Offer generated: user={user_id}, property={property_id}, price=${offer_price:,}",
            extra={
                "metric_type": "offer_generated",
                "user_id": user_id,
                "property_id": property_id,
                "offer_price": offer_price,
                "total_offers": self.offers_generated
            }
        )
        
        # In production, send to Datadog or CloudWatch
        # Example: statsd.increment('offers.generated')
    
    def track_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """
        Track application error.
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context
        """
        logger.error(
            f"Error: {error_type} - {error_message}",
            extra={
                "metric_type": "error",
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {}
            }
        )
        
        # In production, send to Datadog or CloudWatch
        # Example: statsd.increment('errors.count', tags=[f'type:{error_type}'])


# Global metrics collector instance
metrics = MetricsCollector()


@contextmanager
def track_execution_time(operation_name: str):
    """
    Context manager to track execution time of an operation.
    
    Usage:
        with track_execution_time("search_properties"):
            # ... operation code ...
    
    Args:
        operation_name: Name of the operation being tracked
    """
    start_time = time.time()
    success = True
    
    try:
        yield
    except Exception as e:
        success = False
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        metrics.track_tool_execution(operation_name, duration_ms, success)


def track_api_call(service_name: str, endpoint: str):
    """
    Decorator to track external API call timing.
    
    Usage:
        @track_api_call("rentcast", "search_listings")
        async def search_listings(...):
            ...
    
    Args:
        service_name: Name of the external service
        endpoint: API endpoint being called
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            status_code = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                # Try to extract status code from exception
                if hasattr(e, 'status_code'):
                    status_code = e.status_code
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                metrics.track_external_api_call(
                    service_name,
                    endpoint,
                    duration_ms,
                    success,
                    status_code
                )
        
        return wrapper
    return decorator


class MetricsMiddleware:
    """
    Middleware to track request metrics.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration_ms = (time.time() - start_time) * 1000
                
                # Log request metrics
                logger.info(
                    f"Request: {scope['method']} {scope['path']}",
                    extra={
                        "metric_type": "http_request",
                        "method": scope["method"],
                        "path": scope["path"],
                        "duration_ms": duration_ms,
                        "status_code": message["status"]
                    }
                )
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


def configure_metrics(app):
    """
    Configure metrics collection for the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    logger.info("Metrics collection configured")
