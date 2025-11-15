# Notification System Documentation

## Overview

The notification system provides multi-channel notifications for escrow transactions with support for email, SMS, and webhooks. It includes async queueing, retry logic, delivery tracking, and user preference management.

## Architecture

### Components

1. **NotificationEngine** (`services/notification_engine.py`)
   - Core notification delivery engine
   - Multi-channel support (email, SMS, webhook)
   - Template rendering for all event types
   - Integration with SendGrid and Twilio

2. **NotificationQueue** (`services/notification_queue.py`)
   - Async notification processing with Redis queue
   - Batch delivery for efficiency
   - Automatic retry logic with exponential backoff
   - Delivery tracking and status monitoring

3. **NotificationService** (`services/notification_service.py`)
   - High-level service integrating engine and queue
   - User preference management
   - Event filtering based on preferences
   - Global service instance management

## Features

### Multi-Channel Delivery

- **Email**: Via SendGrid API with customizable templates
- **SMS**: Via Twilio API with concise message templates
- **Webhook**: HTTP POST to agent systems for agent-to-agent communication

### Notification Events

The system supports the following event types:

- `TRANSACTION_INITIATED` - New transaction created
- `EARNEST_MONEY_RECEIVED` - Earnest money deposit confirmed
- `VERIFICATION_ASSIGNED` - Verification task assigned to agent
- `VERIFICATION_COMPLETED` - Verification task completed
- `VERIFICATION_FAILED` - Verification task failed
- `PAYMENT_RELEASED` - Payment released from escrow
- `PAYMENT_FAILED` - Payment processing failed
- `SETTLEMENT_PENDING` - Settlement ready for execution
- `SETTLEMENT_COMPLETED` - Transaction settled successfully
- `DISPUTE_RAISED` - Dispute raised by party
- `DEADLINE_APPROACHING` - Task deadline approaching
- `DEADLINE_EXCEEDED` - Task deadline exceeded

### Async Queue Processing

- Notifications are queued in Redis for async processing
- Batch processing for efficiency (configurable batch size)
- Automatic retry with configurable max retries and intervals
- Delivery status tracking with 7-day retention

### User Preferences

Users can configure:
- Which channels to use (email, SMS, webhook)
- Contact information for each channel
- Event filters (receive only specific event types)
- Enable/disable notifications per channel

### Retry Logic

- **Default**: 3 retries with 5-second intervals
- **Escalations**: 3 retries with 2-second intervals (faster)
- Exponential backoff for external service failures
- Failed notifications tracked with error messages

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Email (SendGrid)
SENDGRID_API_KEY=your_sendgrid_api_key

# SMS (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+15551234567

# Redis (for queue)
REDIS_URL=redis://localhost:6379/0
```

### Settings

Configuration is managed in `config/settings.py`:

```python
from config.settings import settings

# Access configuration
sendgrid_key = settings.sendgrid_api_key
twilio_sid = settings.twilio_account_sid
```

## Usage

### Basic Usage

```python
from services.notification_service import get_notification_service
from services.notification_engine import NotificationEventType

# Get service instance
notification_service = get_notification_service()

# Send notification
notification_id = await notification_service.notify_transaction_parties(
    transaction_id="txn_001",
    event_type=NotificationEventType.TRANSACTION_INITIATED,
    event_data={
        "transaction_id": "txn_001",
        "property_address": "123 Main St",
        "earnest_money": "5000.00",
        "target_closing_date": "2025-12-01"
    },
    party_ids=["buyer_agent_123", "seller_agent_456"],
    use_queue=True  # Use async queue (default)
)
```

### Managing Preferences

```python
from services.notification_service import NotificationPreferences

# Set preferences
prefs = NotificationPreferences(
    user_id="agent_123",
    email_enabled=True,
    sms_enabled=True,
    webhook_enabled=True,
    email_address="agent@example.com",
    phone_number="+15551234567",
    webhook_url="https://agent-system.com/webhooks/escrow",
    event_filters=["verification_assigned", "payment_released"]
)
await notification_service.set_preferences(prefs)

# Update preferences
await notification_service.update_preferences(
    user_id="agent_123",
    sms_enabled=False,  # Disable SMS
    event_filters=[]  # Receive all events
)

# Get preferences
prefs = await notification_service.get_preferences("agent_123")
```

### Sending Escalation Alerts

```python
# Send urgent escalation (uses all channels)
notification_id = await notification_service.send_escalation_alert(
    transaction_id="txn_001",
    issue_type="deadline_exceeded",
    issue_details={
        "verification_type": "Inspection",
        "deadline": "2025-11-10 14:00",
        "overdue_duration": "2 days"
    },
    party_ids=["buyer_agent_123", "seller_agent_456"]
)
```

### Immediate Notifications

```python
# Bypass queue for urgent notifications
await notification_service.notify_transaction_parties(
    transaction_id="txn_001",
    event_type=NotificationEventType.DISPUTE_RAISED,
    event_data={...},
    party_ids=["agent_123"],
    use_queue=False  # Send immediately
)
```

### Tracking Notifications

```python
# Get notification status
status = await notification_service.get_notification_status(notification_id)
print(f"Status: {status['status']}")  # pending, processing, delivered, failed

# Get all notifications for transaction
notifications = await notification_service.get_transaction_notifications("txn_001")
for notif in notifications:
    print(f"{notif['event_type']}: {notif['status']}")
```

### Queue Management

```python
# Start queue processing (in background task)
await notification_service.start_queue_processing()

# Get queue size
size = await notification_service.get_queue_size()
print(f"Queue size: {size}")

# Stop queue processing
await notification_service.stop_queue_processing()
```

## Integration with Escrow Orchestrator

The notification system integrates with the escrow orchestrator:

```python
from agents.escrow_agent_orchestrator import EscrowAgentOrchestrator
from services.notification_service import get_notification_service

class EscrowAgentOrchestrator:
    def __init__(self):
        self.notification_service = get_notification_service()
    
    async def initiate_transaction(self, ...):
        # Create transaction
        transaction = await self._create_transaction(...)
        
        # Notify parties
        await self.notification_service.notify_transaction_parties(
            transaction_id=transaction.id,
            event_type=NotificationEventType.TRANSACTION_INITIATED,
            event_data={
                "transaction_id": transaction.id,
                "property_address": transaction.property_address,
                "earnest_money": str(transaction.earnest_money),
                "target_closing_date": transaction.target_closing_date.isoformat()
            },
            party_ids=[transaction.buyer_agent_id, transaction.seller_agent_id]
        )
```

## Templates

### Email Templates

Email templates are defined in `NotificationEngine._render_email_template()`. Each event type has:
- Subject line with dynamic variables
- Body text with transaction details
- Professional formatting

Example:
```
Subject: Transaction Initiated - {property_address}

A new escrow transaction has been initiated.

Transaction ID: {transaction_id}
Property: {property_address}
Earnest Money: ${earnest_money}
Target Closing Date: {target_closing_date}

Best regards,
Counter Escrow Agent
```

### SMS Templates

SMS templates are concise versions optimized for mobile:

```
Counter Escrow: Transaction {transaction_id} initiated for {property_address}. 
Earnest money ${earnest_money} received.
```

### Webhook Payloads

Webhooks receive JSON payloads:

```json
{
  "transaction_id": "txn_001",
  "event_type": "transaction_initiated",
  "event_data": {
    "property_address": "123 Main St",
    "earnest_money": "5000.00"
  },
  "timestamp": "2025-11-14T10:30:00Z"
}
```

## Error Handling

### Retry Strategy

- **Payment Operations**: 3 retries, exponential backoff
- **Blockchain Logging**: 5 retries, exponential backoff
- **Notifications**: 3 retries, 5-second intervals
- **Escalations**: 3 retries, 2-second intervals

### Circuit Breaker

Circuit breakers protect against cascading failures:

- **Notification Services**: Open after 3 failures, half-open after 120s
- Configured in `config/settings.py`

### Error Tracking

Failed notifications are tracked with:
- Error message
- Retry count
- Last attempt timestamp
- Final status (failed)

## Performance

### Batch Processing

- Default batch size: 10 notifications
- Processing interval: 1 second
- Configurable in `NotificationQueue` initialization

### Caching

- Notification tracking: 7-day TTL in Redis
- User preferences: No expiration (persistent)
- Queue items: Processed and removed

### Concurrency

- Batch notifications processed concurrently with `asyncio.gather()`
- Multiple channels sent in parallel
- Non-blocking queue processing

## Monitoring

### Metrics to Track

- Queue size
- Delivery success rate per channel
- Average delivery time
- Retry rate
- Failed notification count

### Logging

All operations are logged with appropriate levels:
- `INFO`: Successful deliveries, queue operations
- `WARNING`: Retries, missing configuration
- `ERROR`: Delivery failures, integration errors

## Testing

See `examples/notification_usage_example.py` for comprehensive examples.

### Unit Tests

Test individual components:
- Template rendering
- Channel delivery
- Preference filtering
- Queue operations

### Integration Tests

Test end-to-end flows:
- Transaction lifecycle notifications
- Multi-channel delivery
- Retry logic
- Preference management

## Best Practices

1. **Use Queue by Default**: Async processing prevents blocking
2. **Set Preferences Early**: Configure preferences before transactions
3. **Filter Events**: Reduce noise by filtering to relevant events
4. **Monitor Queue Size**: Alert if queue grows too large
5. **Test Webhooks**: Ensure webhook endpoints are reliable
6. **Handle Failures Gracefully**: Log and alert on persistent failures
7. **Use Escalations Sparingly**: Reserve for truly urgent issues

## Troubleshooting

### Notifications Not Sending

1. Check configuration (API keys, credentials)
2. Verify user preferences are set
3. Check queue size and processing status
4. Review logs for errors

### High Retry Rate

1. Check external service status (SendGrid, Twilio)
2. Verify network connectivity
3. Review circuit breaker status
4. Check rate limits

### Queue Growing

1. Increase batch size
2. Decrease processing interval
3. Add more queue processors
4. Check for blocking operations

## Future Enhancements

- Push notifications (mobile apps)
- In-app notifications (web dashboard)
- Notification templates customization
- A/B testing for templates
- Analytics dashboard
- Rate limiting per user
- Priority queues for urgent notifications
