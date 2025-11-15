"""Notification service integrating notification engine, queue, and preferences."""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.settings import settings
from services.notification_engine import (
    NotificationEngine,
    NotificationChannel,
    NotificationEventType,
    NotificationError
)
from services.notification_queue import NotificationQueue
from services.cache_client import CacheClient

logger = logging.getLogger(__name__)


class NotificationPreferences:
    """Notification preferences for a user/agent."""
    
    def __init__(
        self,
        user_id: str,
        email_enabled: bool = True,
        sms_enabled: bool = True,
        webhook_enabled: bool = True,
        email_address: Optional[str] = None,
        phone_number: Optional[str] = None,
        webhook_url: Optional[str] = None,
        event_filters: Optional[List[str]] = None
    ):
        """Initialize notification preferences.
        
        Args:
            user_id: User/agent ID
            email_enabled: Whether email notifications are enabled
            sms_enabled: Whether SMS notifications are enabled
            webhook_enabled: Whether webhook notifications are enabled
            email_address: Email address for notifications
            phone_number: Phone number for SMS
            webhook_url: Webhook URL for notifications
            event_filters: List of event types to receive (None = all)
        """
        self.user_id = user_id
        self.email_enabled = email_enabled
        self.sms_enabled = sms_enabled
        self.webhook_enabled = webhook_enabled
        self.email_address = email_address
        self.phone_number = phone_number
        self.webhook_url = webhook_url
        self.event_filters = event_filters or []
    
    def should_notify(self, event_type: NotificationEventType) -> bool:
        """Check if user should be notified for this event type.
        
        Args:
            event_type: Type of notification event
            
        Returns:
            True if user should be notified
        """
        if not self.event_filters:
            return True
        return event_type.value in self.event_filters
    
    def get_enabled_channels(self) -> List[NotificationChannel]:
        """Get list of enabled notification channels.
        
        Returns:
            List of enabled channels
        """
        channels = []
        if self.email_enabled and self.email_address:
            channels.append(NotificationChannel.EMAIL)
        if self.sms_enabled and self.phone_number:
            channels.append(NotificationChannel.SMS)
        if self.webhook_enabled and self.webhook_url:
            channels.append(NotificationChannel.WEBHOOK)
        return channels
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "email_enabled": self.email_enabled,
            "sms_enabled": self.sms_enabled,
            "webhook_enabled": self.webhook_enabled,
            "email_address": self.email_address,
            "phone_number": self.phone_number,
            "webhook_url": self.webhook_url,
            "event_filters": self.event_filters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationPreferences":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            email_enabled=data.get("email_enabled", True),
            sms_enabled=data.get("sms_enabled", True),
            webhook_enabled=data.get("webhook_enabled", True),
            email_address=data.get("email_address"),
            phone_number=data.get("phone_number"),
            webhook_url=data.get("webhook_url"),
            event_filters=data.get("event_filters", [])
        )


class NotificationService:
    """Service for managing notifications with preferences and queueing."""
    
    def __init__(
        self,
        cache_client: Optional[CacheClient] = None,
        sendgrid_api_key: Optional[str] = None,
        twilio_account_sid: Optional[str] = None,
        twilio_auth_token: Optional[str] = None,
        twilio_phone_number: Optional[str] = None
    ):
        """Initialize notification service.
        
        Args:
            cache_client: Cache client for queue and preferences
            sendgrid_api_key: SendGrid API key
            twilio_account_sid: Twilio account SID
            twilio_auth_token: Twilio auth token
            twilio_phone_number: Twilio phone number
        """
        # Use settings if not provided
        sendgrid_api_key = sendgrid_api_key or settings.sendgrid_api_key
        twilio_account_sid = twilio_account_sid or settings.twilio_account_sid
        twilio_auth_token = twilio_auth_token or settings.twilio_auth_token
        twilio_phone_number = twilio_phone_number or settings.twilio_phone_number
        
        # Initialize notification engine
        self.notification_engine = NotificationEngine(
            sendgrid_api_key=sendgrid_api_key,
            twilio_account_sid=twilio_account_sid,
            twilio_auth_token=twilio_auth_token,
            twilio_phone_number=twilio_phone_number
        )
        
        # Initialize cache client if not provided
        self.cache_client = cache_client or CacheClient(redis_url=settings.redis_url)
        
        # Initialize notification queue
        self.notification_queue = NotificationQueue(
            notification_engine=self.notification_engine,
            cache_client=self.cache_client
        )
        
        self._preferences_key_prefix = "notification_preferences:"
    
    async def notify_transaction_parties(
        self,
        transaction_id: str,
        event_type: NotificationEventType,
        event_data: Dict[str, Any],
        party_ids: List[str],
        use_queue: bool = True
    ) -> Optional[str]:
        """Send notifications to transaction parties with preference filtering.
        
        Args:
            transaction_id: Transaction ID
            event_type: Type of notification event
            event_data: Event-specific data
            party_ids: List of party IDs (buyer_agent, seller_agent, etc.)
            use_queue: Whether to use async queue (default) or send immediately
            
        Returns:
            Notification ID if queued, None if sent immediately
        """
        # Get preferences for all parties
        recipients = []
        channels_set = set()
        
        for party_id in party_ids:
            prefs = await self.get_preferences(party_id)
            
            # Check if party should be notified for this event
            if not prefs.should_notify(event_type):
                logger.debug(f"Party {party_id} filtered out for event {event_type}")
                continue
            
            # Build recipient info
            recipient = {
                "user_id": party_id,
                "name": event_data.get(f"{party_id}_name", party_id),
                "email": prefs.email_address if prefs.email_enabled else None,
                "phone": prefs.phone_number if prefs.sms_enabled else None,
                "webhook_url": prefs.webhook_url if prefs.webhook_enabled else None
            }
            recipients.append(recipient)
            
            # Collect enabled channels
            channels_set.update(prefs.get_enabled_channels())
        
        if not recipients:
            logger.warning(f"No recipients for notification: {event_type} on transaction {transaction_id}")
            return None
        
        channels = list(channels_set)
        
        # Send via queue or immediately
        if use_queue:
            notification_id = await self.notification_queue.enqueue(
                transaction_id=transaction_id,
                event_type=event_type,
                event_data=event_data,
                recipients=recipients,
                channels=channels
            )
            return notification_id
        else:
            # Send immediately
            await self.notification_engine.notify_transaction_parties(
                transaction_id=transaction_id,
                event_type=event_type,
                event_data=event_data,
                recipients=recipients,
                channels=channels
            )
            return None
    
    async def send_escalation_alert(
        self,
        transaction_id: str,
        issue_type: str,
        issue_details: Dict[str, Any],
        party_ids: List[str]
    ) -> str:
        """Send escalation alert to transaction parties.
        
        Args:
            transaction_id: Transaction ID
            issue_type: Type of issue
            issue_details: Details about the issue
            party_ids: List of party IDs to notify
            
        Returns:
            Notification ID
        """
        # Get preferences for all parties
        recipients = []
        
        for party_id in party_ids:
            prefs = await self.get_preferences(party_id)
            
            recipient = {
                "user_id": party_id,
                "name": issue_details.get(f"{party_id}_name", party_id),
                "email": prefs.email_address if prefs.email_enabled else None,
                "phone": prefs.phone_number if prefs.sms_enabled else None,
                "webhook_url": prefs.webhook_url if prefs.webhook_enabled else None
            }
            recipients.append(recipient)
        
        # Use all channels for escalations
        channels = [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.WEBHOOK]
        
        event_data = {
            "issue_type": issue_type,
            "issue_details": issue_details,
            "urgency": "high",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Queue escalation with higher priority (lower retry interval)
        notification_id = await self.notification_queue.enqueue(
            transaction_id=transaction_id,
            event_type=NotificationEventType.DEADLINE_EXCEEDED if "deadline" in issue_type else NotificationEventType.PAYMENT_FAILED,
            event_data=event_data,
            recipients=recipients,
            channels=channels,
            max_retries=3,
            retry_interval=2  # Faster retry for escalations
        )
        
        return notification_id
    
    async def get_preferences(self, user_id: str) -> NotificationPreferences:
        """Get notification preferences for a user.
        
        Args:
            user_id: User/agent ID
            
        Returns:
            Notification preferences (defaults if not set)
        """
        import json
        
        key = f"{self._preferences_key_prefix}{user_id}"
        data = await self.cache_client.get(key)
        
        if data:
            prefs_dict = json.loads(data)
            return NotificationPreferences.from_dict(prefs_dict)
        
        # Return default preferences
        return NotificationPreferences(user_id=user_id)
    
    async def set_preferences(self, preferences: NotificationPreferences) -> None:
        """Set notification preferences for a user.
        
        Args:
            preferences: Notification preferences
        """
        import json
        
        key = f"{self._preferences_key_prefix}{preferences.user_id}"
        
        # Store preferences (no expiration)
        await self.cache_client.set(
            key,
            json.dumps(preferences.to_dict()),
            ttl=None
        )
        
        logger.info(f"Updated notification preferences for user {preferences.user_id}")
    
    async def update_preferences(
        self,
        user_id: str,
        email_enabled: Optional[bool] = None,
        sms_enabled: Optional[bool] = None,
        webhook_enabled: Optional[bool] = None,
        email_address: Optional[str] = None,
        phone_number: Optional[str] = None,
        webhook_url: Optional[str] = None,
        event_filters: Optional[List[str]] = None
    ) -> NotificationPreferences:
        """Update notification preferences for a user.
        
        Args:
            user_id: User/agent ID
            email_enabled: Whether email notifications are enabled
            sms_enabled: Whether SMS notifications are enabled
            webhook_enabled: Whether webhook notifications are enabled
            email_address: Email address for notifications
            phone_number: Phone number for SMS
            webhook_url: Webhook URL for notifications
            event_filters: List of event types to receive
            
        Returns:
            Updated preferences
        """
        # Get current preferences
        prefs = await self.get_preferences(user_id)
        
        # Update fields
        if email_enabled is not None:
            prefs.email_enabled = email_enabled
        if sms_enabled is not None:
            prefs.sms_enabled = sms_enabled
        if webhook_enabled is not None:
            prefs.webhook_enabled = webhook_enabled
        if email_address is not None:
            prefs.email_address = email_address
        if phone_number is not None:
            prefs.phone_number = phone_number
        if webhook_url is not None:
            prefs.webhook_url = webhook_url
        if event_filters is not None:
            prefs.event_filters = event_filters
        
        # Save updated preferences
        await self.set_preferences(prefs)
        
        return prefs
    
    async def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get notification delivery status.
        
        Args:
            notification_id: Notification ID
            
        Returns:
            Notification status dict or None if not found
        """
        return await self.notification_queue.get_notification_status(notification_id)
    
    async def get_transaction_notifications(self, transaction_id: str) -> List[Dict[str, Any]]:
        """Get all notifications for a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            List of notification status dicts
        """
        return await self.notification_queue.get_transaction_notifications(transaction_id)
    
    async def start_queue_processing(self) -> None:
        """Start async queue processing."""
        logger.info("Starting notification queue processing")
        await self.notification_queue.process_queue()
    
    async def stop_queue_processing(self) -> None:
        """Stop async queue processing."""
        await self.notification_queue.stop_processing()
    
    async def get_queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            Number of items in queue
        """
        return await self.notification_queue.get_queue_size()


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get global notification service instance.
    
    Returns:
        NotificationService instance
    """
    global _notification_service
    
    if _notification_service is None:
        _notification_service = NotificationService()
    
    return _notification_service
