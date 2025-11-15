"""Example usage of the notification system for escrow transactions."""
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta

from services.notification_service import (
    NotificationService,
    NotificationPreferences,
    get_notification_service
)
from services.notification_engine import NotificationEventType, NotificationChannel


async def example_transaction_notifications():
    """Example of sending notifications throughout a transaction lifecycle."""
    
    # Get notification service instance
    notification_service = get_notification_service()
    
    # Set up notification preferences for transaction parties
    buyer_agent_prefs = NotificationPreferences(
        user_id="buyer_agent_123",
        email_enabled=True,
        sms_enabled=True,
        webhook_enabled=True,
        email_address="buyer.agent@example.com",
        phone_number="+15551234567",
        webhook_url="https://buyer-agent-system.example.com/webhooks/escrow",
        event_filters=[]  # Receive all events
    )
    await notification_service.set_preferences(buyer_agent_prefs)
    
    seller_agent_prefs = NotificationPreferences(
        user_id="seller_agent_456",
        email_enabled=True,
        sms_enabled=False,  # No SMS
        webhook_enabled=True,
        email_address="seller.agent@example.com",
        webhook_url="https://seller-agent-system.example.com/webhooks/escrow",
        event_filters=[
            "transaction_initiated",
            "verification_completed",
            "settlement_completed"
        ]  # Only receive specific events
    )
    await notification_service.set_preferences(seller_agent_prefs)
    
    title_agent_prefs = NotificationPreferences(
        user_id="title_agent_789",
        email_enabled=True,
        sms_enabled=True,
        webhook_enabled=False,
        email_address="title.agent@example.com",
        phone_number="+15559876543",
        event_filters=["verification_assigned", "payment_released"]
    )
    await notification_service.set_preferences(title_agent_prefs)
    
    # Example 1: Transaction initiated
    print("\n=== Example 1: Transaction Initiated ===")
    notification_id = await notification_service.notify_transaction_parties(
        transaction_id="txn_001",
        event_type=NotificationEventType.TRANSACTION_INITIATED,
        event_data={
            "transaction_id": "txn_001",
            "property_address": "123 Main St, Baltimore, MD 21201",
            "earnest_money": "5000.00",
            "target_closing_date": (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "buyer_agent_123_name": "John Buyer Agent",
            "seller_agent_456_name": "Jane Seller Agent"
        },
        party_ids=["buyer_agent_123", "seller_agent_456"],
        use_queue=True
    )
    print(f"Notification queued: {notification_id}")
    
    # Example 2: Verification task assigned
    print("\n=== Example 2: Verification Task Assigned ===")
    notification_id = await notification_service.notify_transaction_parties(
        transaction_id="txn_001",
        event_type=NotificationEventType.VERIFICATION_ASSIGNED,
        event_data={
            "transaction_id": "txn_001",
            "verification_type": "Title Search",
            "deadline": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
            "payment_amount": "1200.00",
            "title_agent_789_name": "Bob Title Agent"
        },
        party_ids=["title_agent_789"],
        use_queue=True
    )
    print(f"Notification queued: {notification_id}")
    
    # Example 3: Verification completed
    print("\n=== Example 3: Verification Completed ===")
    notification_id = await notification_service.notify_transaction_parties(
        transaction_id="txn_001",
        event_type=NotificationEventType.VERIFICATION_COMPLETED,
        event_data={
            "transaction_id": "txn_001",
            "verification_type": "Title Search",
            "status": "Approved",
            "agent_name": "Bob Title Agent",
            "payment_amount": "1200.00",
            "buyer_agent_123_name": "John Buyer Agent",
            "seller_agent_456_name": "Jane Seller Agent",
            "title_agent_789_name": "Bob Title Agent"
        },
        party_ids=["buyer_agent_123", "seller_agent_456", "title_agent_789"],
        use_queue=True
    )
    print(f"Notification queued: {notification_id}")
    
    # Example 4: Escalation alert for deadline exceeded
    print("\n=== Example 4: Escalation Alert ===")
    notification_id = await notification_service.send_escalation_alert(
        transaction_id="txn_001",
        issue_type="deadline_exceeded",
        issue_details={
            "verification_type": "Inspection",
            "deadline": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "overdue_duration": "1 day",
            "buyer_agent_123_name": "John Buyer Agent",
            "seller_agent_456_name": "Jane Seller Agent"
        },
        party_ids=["buyer_agent_123", "seller_agent_456"]
    )
    print(f"Escalation alert queued: {notification_id}")
    
    # Example 5: Settlement completed
    print("\n=== Example 5: Settlement Completed ===")
    notification_id = await notification_service.notify_transaction_parties(
        transaction_id="txn_001",
        event_type=NotificationEventType.SETTLEMENT_COMPLETED,
        event_data={
            "transaction_id": "txn_001",
            "property_address": "123 Main St, Baltimore, MD 21201",
            "total_amount": "450000.00",
            "closing_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "blockchain_tx_hash": "0x1234567890abcdef",
            "buyer_agent_123_name": "John Buyer Agent",
            "seller_agent_456_name": "Jane Seller Agent"
        },
        party_ids=["buyer_agent_123", "seller_agent_456"],
        use_queue=True
    )
    print(f"Notification queued: {notification_id}")
    
    # Check queue size
    queue_size = await notification_service.get_queue_size()
    print(f"\nCurrent queue size: {queue_size}")
    
    # Get notification status
    if notification_id:
        await asyncio.sleep(1)  # Wait a bit for processing
        status = await notification_service.get_notification_status(notification_id)
        if status:
            print(f"\nNotification status: {status['status']}")
    
    # Get all notifications for transaction
    notifications = await notification_service.get_transaction_notifications("txn_001")
    print(f"\nTotal notifications for transaction: {len(notifications)}")


async def example_preference_management():
    """Example of managing notification preferences."""
    
    notification_service = get_notification_service()
    
    print("\n=== Example: Preference Management ===")
    
    # Update preferences
    prefs = await notification_service.update_preferences(
        user_id="agent_001",
        email_enabled=True,
        sms_enabled=False,
        email_address="agent@example.com",
        event_filters=[
            "verification_assigned",
            "payment_released",
            "settlement_completed"
        ]
    )
    print(f"Updated preferences for {prefs.user_id}")
    print(f"Enabled channels: {prefs.get_enabled_channels()}")
    
    # Get preferences
    retrieved_prefs = await notification_service.get_preferences("agent_001")
    print(f"Retrieved preferences: {retrieved_prefs.to_dict()}")


async def example_immediate_notification():
    """Example of sending immediate notification (bypassing queue)."""
    
    notification_service = get_notification_service()
    
    print("\n=== Example: Immediate Notification ===")
    
    # Set up preferences
    prefs = NotificationPreferences(
        user_id="urgent_agent",
        email_enabled=True,
        email_address="urgent@example.com"
    )
    await notification_service.set_preferences(prefs)
    
    # Send immediately (use_queue=False)
    await notification_service.notify_transaction_parties(
        transaction_id="txn_urgent",
        event_type=NotificationEventType.DISPUTE_RAISED,
        event_data={
            "transaction_id": "txn_urgent",
            "property_address": "456 Oak Ave, Baltimore, MD",
            "dispute_type": "Inspection Issues",
            "raised_by": "Buyer Agent",
            "urgent_agent_name": "Urgent Agent"
        },
        party_ids=["urgent_agent"],
        use_queue=False  # Send immediately
    )
    print("Immediate notification sent")


async def main():
    """Run all examples."""
    print("=== Notification System Examples ===\n")
    
    # Run examples
    await example_transaction_notifications()
    await example_preference_management()
    await example_immediate_notification()
    
    print("\n=== Examples Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
