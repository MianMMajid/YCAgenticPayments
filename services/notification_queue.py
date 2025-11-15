"""Notification queue for async notification processing with retry logic."""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json

from services.cache_client import CacheClient
from services.notification_engine import NotificationEngine, NotificationChannel, NotificationEventType

logger = logging.getLogger(__name__)


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationQueueItem:
    """Notification queue item with retry tracking."""
    
    def __init__(
        self,
        notification_id: str,
        transaction_id: str,
        event_type: NotificationEventType,
        event_data: Dict[str, Any],
        recipients: List[Dict[str, Any]],
        channels: List[NotificationChannel],
        max_retries: int = 3,
        retry_interval: int = 5
    ):
        """Initialize notification queue item.
        
        Args:
            notification_id: Unique notification ID
            transaction_id: Transaction ID
            event_type: Type of notification event
            event_data: Event-specific data
            recipients: List of recipients
            channels: List of channels to use
            max_retries: Maximum number of retry attempts
            retry_interval: Seconds between retries
        """
        self.notification_id = notification_id
        self.transaction_id = transaction_id
        self.event_type = event_type
        self.event_data = event_data
        self.recipients = recipients
        self.channels = channels
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.retry_count = 0
        self.status = NotificationStatus.PENDING
        self.created_at = datetime.utcnow()
        self.last_attempt_at: Optional[datetime] = None
        self.delivered_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "notification_id": self.notification_id,
            "transaction_id": self.transaction_id,
            "event_type": self.event_type.value,
            "event_data": self.event_data,
            "recipients": self.recipients,
            "channels": [c.value for c in self.channels],
            "max_retries": self.max_retries,
            "retry_interval": self.retry_interval,
            "retry_count": self.retry_count,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationQueueItem":
        """Create from dictionary."""
        item = cls(
            notification_id=data["notification_id"],
            transaction_id=data["transaction_id"],
            event_type=NotificationEventType(data["event_type"]),
            event_data=data["event_data"],
            recipients=data["recipients"],
            channels=[NotificationChannel(c) for c in data["channels"]],
            max_retries=data["max_retries"],
            retry_interval=data["retry_interval"]
        )
        item.retry_count = data["retry_count"]
        item.status = NotificationStatus(data["status"])
        item.created_at = datetime.fromisoformat(data["created_at"])
        item.last_attempt_at = datetime.fromisoformat(data["last_attempt_at"]) if data["last_attempt_at"] else None
        item.delivered_at = datetime.fromisoformat(data["delivered_at"]) if data["delivered_at"] else None
        item.error_message = data["error_message"]
        return item


class NotificationQueue:
    """Queue for async notification processing with retry logic."""
    
    def __init__(
        self,
        notification_engine: NotificationEngine,
        cache_client: CacheClient,
        batch_size: int = 10,
        processing_interval: int = 1
    ):
        """Initialize notification queue.
        
        Args:
            notification_engine: Notification engine for sending
            cache_client: Cache client for queue storage
            batch_size: Number of notifications to process in batch
            processing_interval: Seconds between batch processing
        """
        self.notification_engine = notification_engine
        self.cache_client = cache_client
        self.batch_size = batch_size
        self.processing_interval = processing_interval
        self._processing = False
        self._queue_key = "notification_queue"
        self._tracking_key_prefix = "notification_tracking:"
    
    async def enqueue(
        self,
        transaction_id: str,
        event_type: NotificationEventType,
        event_data: Dict[str, Any],
        recipients: List[Dict[str, Any]],
        channels: List[NotificationChannel],
        max_retries: int = 3,
        retry_interval: int = 5
    ) -> str:
        """Add notification to queue.
        
        Args:
            transaction_id: Transaction ID
            event_type: Type of notification event
            event_data: Event-specific data
            recipients: List of recipients
            channels: List of channels to use
            max_retries: Maximum number of retry attempts
            retry_interval: Seconds between retries
            
        Returns:
            Notification ID
        """
        import uuid
        notification_id = str(uuid.uuid4())
        
        item = NotificationQueueItem(
            notification_id=notification_id,
            transaction_id=transaction_id,
            event_type=event_type,
            event_data=event_data,
            recipients=recipients,
            channels=channels,
            max_retries=max_retries,
            retry_interval=retry_interval
        )
        
        # Add to queue
        await self.cache_client.redis.lpush(self._queue_key, json.dumps(item.to_dict()))
        
        # Track notification
        await self._update_tracking(item)
        
        logger.info(f"Enqueued notification {notification_id} for transaction {transaction_id}")
        return notification_id
    
    async def process_queue(self) -> None:
        """Process notifications from queue in batches."""
        if self._processing:
            logger.warning("Queue processing already in progress")
            return
        
        self._processing = True
        logger.info("Starting notification queue processing")
        
        try:
            while self._processing:
                # Get batch of notifications
                batch = await self._get_batch()
                
                if batch:
                    logger.info(f"Processing batch of {len(batch)} notifications")
                    await self._process_batch(batch)
                else:
                    # No items in queue, wait before checking again
                    await asyncio.sleep(self.processing_interval)
        except Exception as e:
            logger.error(f"Error in queue processing: {str(e)}")
        finally:
            self._processing = False
    
    async def stop_processing(self) -> None:
        """Stop queue processing."""
        logger.info("Stopping notification queue processing")
        self._processing = False
    
    async def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get notification delivery status.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Notification status dict or None if not found
        """
        tracking_key = f"{self._tracking_key_prefix}{notification_id}"
        data = await self.cache_client.get(tracking_key)
        
        if data:
            return json.loads(data)
        return None
    
    async def get_transaction_notifications(self, transaction_id: str) -> List[Dict[str, Any]]:
        """Get all notifications for a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            List of notification status dicts
        """
        # Scan for all tracking keys for this transaction
        pattern = f"{self._tracking_key_prefix}*"
        notifications = []
        
        cursor = 0
        while True:
            cursor, keys = await self.cache_client.redis.scan(cursor, match=pattern, count=100)
            
            for key in keys:
                data = await self.cache_client.redis.get(key)
                if data:
                    notification = json.loads(data)
                    if notification.get("transaction_id") == transaction_id:
                        notifications.append(notification)
            
            if cursor == 0:
                break
        
        return notifications
    
    async def _get_batch(self) -> List[NotificationQueueItem]:
        """Get batch of notifications from queue.
        
        Returns:
            List of notification items
        """
        batch = []
        
        for _ in range(self.batch_size):
            data = await self.cache_client.redis.rpop(self._queue_key)
            if not data:
                break
            
            try:
                item_dict = json.loads(data)
                item = NotificationQueueItem.from_dict(item_dict)
                batch.append(item)
            except Exception as e:
                logger.error(f"Failed to deserialize notification: {str(e)}")
        
        return batch
    
    async def _process_batch(self, batch: List[NotificationQueueItem]) -> None:
        """Process batch of notifications.
        
        Args:
            batch: List of notification items
        """
        # Process notifications concurrently
        tasks = [self._process_notification(item) for item in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_notification(self, item: NotificationQueueItem) -> None:
        """Process single notification with retry logic.
        
        Args:
            item: Notification queue item
        """
        item.status = NotificationStatus.PROCESSING
        item.last_attempt_at = datetime.utcnow()
        await self._update_tracking(item)
        
        try:
            # Send notification
            results = await self.notification_engine.notify_transaction_parties(
                transaction_id=item.transaction_id,
                event_type=item.event_type,
                event_data=item.event_data,
                recipients=item.recipients,
                channels=item.channels
            )
            
            # Check if at least one channel succeeded
            if any(results.values()):
                item.status = NotificationStatus.DELIVERED
                item.delivered_at = datetime.utcnow()
                logger.info(f"Notification {item.notification_id} delivered successfully")
            else:
                raise Exception("All channels failed")
                
        except Exception as e:
            logger.error(f"Failed to send notification {item.notification_id}: {str(e)}")
            item.error_message = str(e)
            
            # Check if we should retry
            if item.retry_count < item.max_retries:
                item.retry_count += 1
                item.status = NotificationStatus.RETRYING
                
                # Re-queue for retry
                await asyncio.sleep(item.retry_interval)
                await self.cache_client.redis.lpush(self._queue_key, json.dumps(item.to_dict()))
                
                logger.info(f"Notification {item.notification_id} queued for retry {item.retry_count}/{item.max_retries}")
            else:
                item.status = NotificationStatus.FAILED
                logger.error(f"Notification {item.notification_id} failed after {item.max_retries} retries")
        
        # Update tracking
        await self._update_tracking(item)
    
    async def _update_tracking(self, item: NotificationQueueItem) -> None:
        """Update notification tracking in cache.
        
        Args:
            item: Notification queue item
        """
        tracking_key = f"{self._tracking_key_prefix}{item.notification_id}"
        
        # Store tracking data with 7-day TTL
        await self.cache_client.set(
            tracking_key,
            json.dumps(item.to_dict()),
            ttl=7 * 24 * 60 * 60  # 7 days
        )
    
    async def get_queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            Number of items in queue
        """
        return await self.cache_client.redis.llen(self._queue_key)
    
    async def clear_queue(self) -> None:
        """Clear all items from queue (for testing/maintenance)."""
        await self.cache_client.redis.delete(self._queue_key)
        logger.warning("Notification queue cleared")
