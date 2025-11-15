"""Escrow-specific metrics collection and Prometheus integration."""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

from models.transaction import TransactionState
from models.verification import TaskStatus
from models.payment import PaymentStatus

logger = logging.getLogger(__name__)

# Prometheus metrics
# Transaction metrics
transaction_initiated_total = Counter(
    'escrow_transactions_initiated_total',
    'Total number of escrow transactions initiated'
)

transaction_settled_total = Counter(
    'escrow_transactions_settled_total',
    'Total number of escrow transactions settled'
)

transaction_disputed_total = Counter(
    'escrow_transactions_disputed_total',
    'Total number of escrow transactions disputed'
)

transaction_cancelled_total = Counter(
    'escrow_transactions_cancelled_total',
    'Total number of escrow transactions cancelled'
)

# Closing cycle time metrics
closing_cycle_time_seconds = Histogram(
    'escrow_closing_cycle_time_seconds',
    'Time from transaction initiation to settlement in seconds',
    buckets=[
        86400,      # 1 day
        172800,     # 2 days
        345600,     # 4 days
        604800,     # 7 days
        1209600,    # 14 days
        1814400,    # 21 days
        2592000,    # 30 days
        3888000,    # 45 days
    ]
)

# Verification metrics
verification_tasks_assigned_total = Counter(
    'escrow_verification_tasks_assigned_total',
    'Total number of verification tasks assigned',
    ['verification_type']
)

verification_tasks_completed_total = Counter(
    'escrow_verification_tasks_completed_total',
    'Total number of verification tasks completed',
    ['verification_type']
)

verification_tasks_failed_total = Counter(
    'escrow_verification_tasks_failed_total',
    'Total number of verification tasks failed',
    ['verification_type']
)

verification_completion_time_seconds = Histogram(
    'escrow_verification_completion_time_seconds',
    'Time to complete verification tasks in seconds',
    ['verification_type'],
    buckets=[3600, 7200, 14400, 28800, 43200, 86400, 172800, 345600, 604800]  # 1h to 7d
)

# Payment metrics
payment_initiated_total = Counter(
    'escrow_payments_initiated_total',
    'Total number of payments initiated',
    ['payment_type']
)

payment_completed_total = Counter(
    'escrow_payments_completed_total',
    'Total number of payments completed',
    ['payment_type']
)

payment_failed_total = Counter(
    'escrow_payments_failed_total',
    'Total number of payments failed',
    ['payment_type']
)

payment_amount_total = Counter(
    'escrow_payment_amount_total_cents',
    'Total payment amount in cents',
    ['payment_type']
)

# API response time metrics
api_request_duration_seconds = Histogram(
    'escrow_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Active transactions gauge
active_transactions_gauge = Gauge(
    'escrow_active_transactions',
    'Number of active transactions by state',
    ['state']
)

# Workflow metrics
workflow_execution_time_seconds = Histogram(
    'escrow_workflow_execution_time_seconds',
    'Workflow execution time in seconds',
    ['workflow_type']
)

# Blockchain metrics
blockchain_events_logged_total = Counter(
    'escrow_blockchain_events_logged_total',
    'Total number of blockchain events logged',
    ['event_type']
)

blockchain_logging_errors_total = Counter(
    'escrow_blockchain_logging_errors_total',
    'Total number of blockchain logging errors'
)


class EscrowMetricsCollector:
    """
    Collector for escrow-specific metrics.
    
    Tracks transaction throughput, closing cycle times, verification completion rates,
    payment success rates, and API response times.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._lock = Lock()
        self._transaction_start_times: Dict[str, datetime] = {}
        self._verification_start_times: Dict[str, datetime] = {}
        self._payment_start_times: Dict[str, datetime] = {}
        
        # In-memory counters for rate calculations
        self._transaction_counts: Dict[str, int] = defaultdict(int)
        self._verification_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._payment_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    def track_transaction_initiated(self, transaction_id: str, initiated_at: datetime):
        """
        Track transaction initiation.
        
        Args:
            transaction_id: Transaction identifier
            initiated_at: Timestamp when transaction was initiated
        """
        with self._lock:
            self._transaction_start_times[transaction_id] = initiated_at
            self._transaction_counts['initiated'] += 1
        
        transaction_initiated_total.inc()
        
        logger.info(
            f"Transaction initiated: {transaction_id}",
            extra={
                "metric_type": "transaction_initiated",
                "transaction_id": transaction_id,
                "initiated_at": initiated_at.isoformat()
            }
        )
    
    def track_transaction_settled(self, transaction_id: str, settled_at: datetime):
        """
        Track transaction settlement and calculate closing cycle time.
        
        Args:
            transaction_id: Transaction identifier
            settled_at: Timestamp when transaction was settled
        """
        with self._lock:
            initiated_at = self._transaction_start_times.get(transaction_id)
            if initiated_at:
                cycle_time = (settled_at - initiated_at).total_seconds()
                closing_cycle_time_seconds.observe(cycle_time)
                
                # Clean up
                del self._transaction_start_times[transaction_id]
                
                logger.info(
                    f"Transaction settled: {transaction_id}, cycle_time={cycle_time:.2f}s ({cycle_time/86400:.2f} days)",
                    extra={
                        "metric_type": "transaction_settled",
                        "transaction_id": transaction_id,
                        "cycle_time_seconds": cycle_time,
                        "cycle_time_days": cycle_time / 86400
                    }
                )
            
            self._transaction_counts['settled'] += 1
        
        transaction_settled_total.inc()
    
    def track_transaction_disputed(self, transaction_id: str):
        """
        Track transaction dispute.
        
        Args:
            transaction_id: Transaction identifier
        """
        with self._lock:
            self._transaction_counts['disputed'] += 1
        
        transaction_disputed_total.inc()
        
        logger.warning(
            f"Transaction disputed: {transaction_id}",
            extra={
                "metric_type": "transaction_disputed",
                "transaction_id": transaction_id
            }
        )
    
    def track_transaction_cancelled(self, transaction_id: str):
        """
        Track transaction cancellation.
        
        Args:
            transaction_id: Transaction identifier
        """
        with self._lock:
            # Clean up tracking data
            self._transaction_start_times.pop(transaction_id, None)
            self._transaction_counts['cancelled'] += 1
        
        transaction_cancelled_total.inc()
        
        logger.info(
            f"Transaction cancelled: {transaction_id}",
            extra={
                "metric_type": "transaction_cancelled",
                "transaction_id": transaction_id
            }
        )
    
    def track_verification_assigned(
        self,
        verification_id: str,
        verification_type: str,
        assigned_at: datetime
    ):
        """
        Track verification task assignment.
        
        Args:
            verification_id: Verification task identifier
            verification_type: Type of verification (title_search, inspection, etc.)
            assigned_at: Timestamp when task was assigned
        """
        with self._lock:
            self._verification_start_times[verification_id] = assigned_at
            self._verification_counts[verification_type]['assigned'] += 1
        
        verification_tasks_assigned_total.labels(verification_type=verification_type).inc()
        
        logger.info(
            f"Verification assigned: {verification_id} ({verification_type})",
            extra={
                "metric_type": "verification_assigned",
                "verification_id": verification_id,
                "verification_type": verification_type,
                "assigned_at": assigned_at.isoformat()
            }
        )
    
    def track_verification_completed(
        self,
        verification_id: str,
        verification_type: str,
        completed_at: datetime
    ):
        """
        Track verification task completion.
        
        Args:
            verification_id: Verification task identifier
            verification_type: Type of verification
            completed_at: Timestamp when task was completed
        """
        with self._lock:
            assigned_at = self._verification_start_times.get(verification_id)
            if assigned_at:
                completion_time = (completed_at - assigned_at).total_seconds()
                verification_completion_time_seconds.labels(
                    verification_type=verification_type
                ).observe(completion_time)
                
                # Clean up
                del self._verification_start_times[verification_id]
                
                logger.info(
                    f"Verification completed: {verification_id} ({verification_type}), "
                    f"completion_time={completion_time:.2f}s ({completion_time/3600:.2f} hours)",
                    extra={
                        "metric_type": "verification_completed",
                        "verification_id": verification_id,
                        "verification_type": verification_type,
                        "completion_time_seconds": completion_time,
                        "completion_time_hours": completion_time / 3600
                    }
                )
            
            self._verification_counts[verification_type]['completed'] += 1
        
        verification_tasks_completed_total.labels(verification_type=verification_type).inc()
    
    def track_verification_failed(self, verification_id: str, verification_type: str):
        """
        Track verification task failure.
        
        Args:
            verification_id: Verification task identifier
            verification_type: Type of verification
        """
        with self._lock:
            # Clean up tracking data
            self._verification_start_times.pop(verification_id, None)
            self._verification_counts[verification_type]['failed'] += 1
        
        verification_tasks_failed_total.labels(verification_type=verification_type).inc()
        
        logger.warning(
            f"Verification failed: {verification_id} ({verification_type})",
            extra={
                "metric_type": "verification_failed",
                "verification_id": verification_id,
                "verification_type": verification_type
            }
        )
    
    def track_payment_initiated(
        self,
        payment_id: str,
        payment_type: str,
        amount: float,
        initiated_at: datetime
    ):
        """
        Track payment initiation.
        
        Args:
            payment_id: Payment identifier
            payment_type: Type of payment
            amount: Payment amount in dollars
            initiated_at: Timestamp when payment was initiated
        """
        with self._lock:
            self._payment_start_times[payment_id] = initiated_at
            self._payment_counts[payment_type]['initiated'] += 1
        
        payment_initiated_total.labels(payment_type=payment_type).inc()
        payment_amount_total.labels(payment_type=payment_type).inc(int(amount * 100))  # Convert to cents
        
        logger.info(
            f"Payment initiated: {payment_id} ({payment_type}), amount=${amount:.2f}",
            extra={
                "metric_type": "payment_initiated",
                "payment_id": payment_id,
                "payment_type": payment_type,
                "amount": amount,
                "initiated_at": initiated_at.isoformat()
            }
        )
    
    def track_payment_completed(self, payment_id: str, payment_type: str):
        """
        Track payment completion.
        
        Args:
            payment_id: Payment identifier
            payment_type: Type of payment
        """
        with self._lock:
            # Clean up tracking data
            self._payment_start_times.pop(payment_id, None)
            self._payment_counts[payment_type]['completed'] += 1
        
        payment_completed_total.labels(payment_type=payment_type).inc()
        
        logger.info(
            f"Payment completed: {payment_id} ({payment_type})",
            extra={
                "metric_type": "payment_completed",
                "payment_id": payment_id,
                "payment_type": payment_type
            }
        )
    
    def track_payment_failed(self, payment_id: str, payment_type: str):
        """
        Track payment failure.
        
        Args:
            payment_id: Payment identifier
            payment_type: Type of payment
        """
        with self._lock:
            # Clean up tracking data
            self._payment_start_times.pop(payment_id, None)
            self._payment_counts[payment_type]['failed'] += 1
        
        payment_failed_total.labels(payment_type=payment_type).inc()
        
        logger.warning(
            f"Payment failed: {payment_id} ({payment_type})",
            extra={
                "metric_type": "payment_failed",
                "payment_id": payment_id,
                "payment_type": payment_type
            }
        )
    
    def track_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float
    ):
        """
        Track API request metrics.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            status_code: HTTP status code
            duration_seconds: Request duration in seconds
        """
        api_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).observe(duration_seconds)
        
        logger.debug(
            f"API request: {method} {endpoint} - {status_code} ({duration_seconds*1000:.2f}ms)",
            extra={
                "metric_type": "api_request",
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "duration_seconds": duration_seconds,
                "duration_ms": duration_seconds * 1000
            }
        )
    
    def track_workflow_execution(self, workflow_type: str, duration_seconds: float):
        """
        Track workflow execution time.
        
        Args:
            workflow_type: Type of workflow
            duration_seconds: Execution duration in seconds
        """
        workflow_execution_time_seconds.labels(workflow_type=workflow_type).observe(duration_seconds)
        
        logger.info(
            f"Workflow executed: {workflow_type}, duration={duration_seconds:.2f}s",
            extra={
                "metric_type": "workflow_execution",
                "workflow_type": workflow_type,
                "duration_seconds": duration_seconds
            }
        )
    
    def track_blockchain_event(self, event_type: str, success: bool = True):
        """
        Track blockchain event logging.
        
        Args:
            event_type: Type of blockchain event
            success: Whether the logging was successful
        """
        if success:
            blockchain_events_logged_total.labels(event_type=event_type).inc()
            
            logger.debug(
                f"Blockchain event logged: {event_type}",
                extra={
                    "metric_type": "blockchain_event_logged",
                    "event_type": event_type
                }
            )
        else:
            blockchain_logging_errors_total.inc()
            
            logger.error(
                f"Blockchain event logging failed: {event_type}",
                extra={
                    "metric_type": "blockchain_logging_error",
                    "event_type": event_type
                }
            )
    
    def update_active_transactions_gauge(self, state_counts: Dict[str, int]):
        """
        Update active transactions gauge with current counts by state.
        
        Args:
            state_counts: Dictionary mapping transaction states to counts
        """
        for state, count in state_counts.items():
            active_transactions_gauge.labels(state=state).set(count)
    
    def get_verification_completion_rate(self, verification_type: Optional[str] = None) -> float:
        """
        Calculate verification completion rate.
        
        Args:
            verification_type: Optional specific verification type
            
        Returns:
            Completion rate as a percentage (0-100)
        """
        with self._lock:
            if verification_type:
                counts = self._verification_counts[verification_type]
                total = counts['assigned']
                completed = counts['completed']
            else:
                total = sum(counts['assigned'] for counts in self._verification_counts.values())
                completed = sum(counts['completed'] for counts in self._verification_counts.values())
            
            if total == 0:
                return 0.0
            
            rate = (completed / total) * 100
            
            logger.info(
                f"Verification completion rate: {rate:.2f}% "
                f"({completed}/{total}){f' for {verification_type}' if verification_type else ''}",
                extra={
                    "metric_type": "verification_completion_rate",
                    "verification_type": verification_type,
                    "rate": rate,
                    "completed": completed,
                    "total": total
                }
            )
            
            return rate
    
    def get_payment_success_rate(self, payment_type: Optional[str] = None) -> float:
        """
        Calculate payment success rate.
        
        Args:
            payment_type: Optional specific payment type
            
        Returns:
            Success rate as a percentage (0-100)
        """
        with self._lock:
            if payment_type:
                counts = self._payment_counts[payment_type]
                total = counts['initiated']
                completed = counts['completed']
            else:
                total = sum(counts['initiated'] for counts in self._payment_counts.values())
                completed = sum(counts['completed'] for counts in self._payment_counts.values())
            
            if total == 0:
                return 0.0
            
            rate = (completed / total) * 100
            
            logger.info(
                f"Payment success rate: {rate:.2f}% "
                f"({completed}/{total}){f' for {payment_type}' if payment_type else ''}",
                extra={
                    "metric_type": "payment_success_rate",
                    "payment_type": payment_type,
                    "rate": rate,
                    "completed": completed,
                    "total": total
                }
            )
            
            return rate


# Global metrics collector instance
escrow_metrics = EscrowMetricsCollector()


# Create router for metrics endpoints
router = APIRouter()


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format for scraping.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/metrics/verification-completion-rate")
async def verification_completion_rate(verification_type: Optional[str] = None):
    """
    Get verification completion rate.
    
    Args:
        verification_type: Optional specific verification type
        
    Returns:
        Completion rate statistics
    """
    rate = escrow_metrics.get_verification_completion_rate(verification_type)
    
    return {
        "verification_type": verification_type or "all",
        "completion_rate": rate,
        "unit": "percentage"
    }


@router.get("/metrics/payment-success-rate")
async def payment_success_rate(payment_type: Optional[str] = None):
    """
    Get payment success rate.
    
    Args:
        payment_type: Optional specific payment type
        
    Returns:
        Success rate statistics
    """
    rate = escrow_metrics.get_payment_success_rate(payment_type)
    
    return {
        "payment_type": payment_type or "all",
        "success_rate": rate,
        "unit": "percentage"
    }
