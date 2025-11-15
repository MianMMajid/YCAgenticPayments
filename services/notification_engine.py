"""Notification engine for multi-channel notifications to transaction parties."""
import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal

from config.settings import settings
from services.email_client import EmailClient
from services.retry_utils import retry_notification_operation
from services.circuit_breaker import notification_circuit_breaker

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification channel enum."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"


class NotificationEventType(str, Enum):
    """Notification event type enum."""
    TRANSACTION_INITIATED = "transaction_initiated"
    EARNEST_MONEY_RECEIVED = "earnest_money_received"
    VERIFICATION_ASSIGNED = "verification_assigned"
    VERIFICATION_COMPLETED = "verification_completed"
    VERIFICATION_FAILED = "verification_failed"
    PAYMENT_RELEASED = "payment_released"
    PAYMENT_FAILED = "payment_failed"
    SETTLEMENT_PENDING = "settlement_pending"
    SETTLEMENT_COMPLETED = "settlement_completed"
    DISPUTE_RAISED = "dispute_raised"
    DEADLINE_APPROACHING = "deadline_approaching"
    DEADLINE_EXCEEDED = "deadline_exceeded"


class NotificationError(Exception):
    """Exception raised for notification errors."""
    pass


class NotificationEngine:
    """Engine for sending multi-channel notifications to transaction parties."""
    
    def __init__(
        self,
        sendgrid_api_key: Optional[str] = None,
        twilio_account_sid: Optional[str] = None,
        twilio_auth_token: Optional[str] = None,
        twilio_phone_number: Optional[str] = None
    ):
        """Initialize the notification engine.
        
        Args:
            sendgrid_api_key: SendGrid API key for email
            twilio_account_sid: Twilio account SID for SMS
            twilio_auth_token: Twilio auth token for SMS
            twilio_phone_number: Twilio phone number for SMS
        """
        self.email_client = EmailClient(sendgrid_api_key=sendgrid_api_key)
        self.twilio_account_sid = twilio_account_sid
        self.twilio_auth_token = twilio_auth_token
        self.twilio_phone_number = twilio_phone_number
        self.twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json" if twilio_account_sid else None
    
    @notification_circuit_breaker
    @retry_notification_operation
    async def notify_transaction_parties(
        self,
        transaction_id: str,
        event_type: NotificationEventType,
        event_data: Dict[str, Any],
        recipients: List[Dict[str, Any]],
        channels: List[NotificationChannel]
    ) -> Dict[str, bool]:
        """Send notifications to all transaction parties.
        
        Args:
            transaction_id: Transaction ID
            event_type: Type of notification event
            event_data: Event-specific data for template rendering
            recipients: List of recipients with contact info
                [{"name": "John", "email": "john@example.com", "phone": "+1234567890", "role": "buyer_agent"}]
            channels: List of channels to use for notification
            
        Returns:
            Dict mapping channel to success status
            
        Raises:
            NotificationError: If all channels fail
        """
        logger.info(f"Sending {event_type} notification for transaction {transaction_id} to {len(recipients)} recipients")
        
        results = {}
        
        # Send via each channel
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    results[channel] = await self._send_email_notifications(
                        transaction_id, event_type, event_data, recipients
                    )
                elif channel == NotificationChannel.SMS:
                    results[channel] = await self._send_sms_notifications(
                        transaction_id, event_type, event_data, recipients
                    )
                elif channel == NotificationChannel.WEBHOOK:
                    results[channel] = await self._send_webhook_notifications(
                        transaction_id, event_type, event_data, recipients
                    )
            except Exception as e:
                logger.error(f"Failed to send {channel} notifications: {str(e)}")
                results[channel] = False
        
        # Check if at least one channel succeeded
        if not any(results.values()):
            raise NotificationError(f"All notification channels failed for transaction {transaction_id}")
        
        return results
    
    @notification_circuit_breaker
    @retry_notification_operation
    async def send_escalation_alert(
        self,
        transaction_id: str,
        issue_type: str,
        issue_details: Dict[str, Any],
        recipients: List[Dict[str, Any]],
        channels: List[NotificationChannel] = None
    ) -> Dict[str, bool]:
        """Send escalation alert for urgent issues.
        
        Args:
            transaction_id: Transaction ID
            issue_type: Type of issue (deadline_exceeded, payment_failed, etc.)
            issue_details: Details about the issue
            recipients: List of recipients with contact info
            channels: List of channels (defaults to all channels for escalations)
            
        Returns:
            Dict mapping channel to success status
        """
        logger.warning(f"Sending escalation alert for transaction {transaction_id}: {issue_type}")
        
        # Use all channels for escalations by default
        if channels is None:
            channels = [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.WEBHOOK]
        
        event_data = {
            "issue_type": issue_type,
            "issue_details": issue_details,
            "urgency": "high",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.notify_transaction_parties(
            transaction_id=transaction_id,
            event_type=NotificationEventType.DEADLINE_EXCEEDED if "deadline" in issue_type else NotificationEventType.PAYMENT_FAILED,
            event_data=event_data,
            recipients=recipients,
            channels=channels
        )
    
    async def _send_email_notifications(
        self,
        transaction_id: str,
        event_type: NotificationEventType,
        event_data: Dict[str, Any],
        recipients: List[Dict[str, Any]]
    ) -> bool:
        """Send email notifications to all recipients.
        
        Args:
            transaction_id: Transaction ID
            event_type: Type of notification event
            event_data: Event-specific data
            recipients: List of recipients
            
        Returns:
            True if all emails sent successfully
        """
        subject, body = self._render_email_template(event_type, event_data)
        
        success_count = 0
        for recipient in recipients:
            email = recipient.get("email")
            if not email:
                logger.warning(f"No email for recipient {recipient.get('name')}")
                continue
            
            try:
                await self.email_client.send_automated_response(
                    to_email=email,
                    subject=subject,
                    body=body,
                    from_email="escrow@counter.app",
                    from_name="Counter Escrow Agent"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send email to {email}: {str(e)}")
        
        return success_count == len([r for r in recipients if r.get("email")])
    
    async def _send_sms_notifications(
        self,
        transaction_id: str,
        event_type: NotificationEventType,
        event_data: Dict[str, Any],
        recipients: List[Dict[str, Any]]
    ) -> bool:
        """Send SMS notifications to all recipients.
        
        Args:
            transaction_id: Transaction ID
            event_type: Type of notification event
            event_data: Event-specific data
            recipients: List of recipients
            
        Returns:
            True if all SMS sent successfully
        """
        if not self.twilio_account_sid or not self.twilio_auth_token:
            logger.warning("Twilio credentials not configured, skipping SMS")
            return False
        
        message = self._render_sms_template(event_type, event_data)
        
        success_count = 0
        for recipient in recipients:
            phone = recipient.get("phone")
            if not phone:
                logger.warning(f"No phone for recipient {recipient.get('name')}")
                continue
            
            try:
                await self._send_twilio_sms(phone, message)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send SMS to {phone}: {str(e)}")
        
        return success_count == len([r for r in recipients if r.get("phone")])
    
    async def _send_webhook_notifications(
        self,
        transaction_id: str,
        event_type: NotificationEventType,
        event_data: Dict[str, Any],
        recipients: List[Dict[str, Any]]
    ) -> bool:
        """Send webhook notifications to all recipients.
        
        Args:
            transaction_id: Transaction ID
            event_type: Type of notification event
            event_data: Event-specific data
            recipients: List of recipients
            
        Returns:
            True if all webhooks sent successfully
        """
        payload = {
            "transaction_id": transaction_id,
            "event_type": event_type.value,
            "event_data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        success_count = 0
        for recipient in recipients:
            webhook_url = recipient.get("webhook_url")
            if not webhook_url:
                logger.debug(f"No webhook URL for recipient {recipient.get('name')}")
                continue
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        timeout=10.0
                    )
                    
                    if response.status_code in [200, 201, 202, 204]:
                        success_count += 1
                    else:
                        logger.error(f"Webhook failed with status {response.status_code}: {webhook_url}")
            except Exception as e:
                logger.error(f"Failed to send webhook to {webhook_url}: {str(e)}")
        
        return success_count == len([r for r in recipients if r.get("webhook_url")])
    
    async def _send_twilio_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS via Twilio API.
        
        Args:
            to_phone: Recipient phone number
            message: SMS message text
            
        Returns:
            True if successful
            
        Raises:
            NotificationError: If sending fails
        """
        if not self.twilio_url:
            raise NotificationError("Twilio not configured")
        
        import base64
        auth_string = f"{self.twilio_account_sid}:{self.twilio_auth_token}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "From": self.twilio_phone_number,
            "To": to_phone,
            "Body": message
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.twilio_url,
                    headers=headers,
                    data=data,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"SMS sent successfully to {to_phone}")
                    return True
                else:
                    error_msg = f"Twilio API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data}"
                    except:
                        pass
                    raise NotificationError(error_msg)
                    
        except httpx.TimeoutException:
            raise NotificationError("SMS send timeout")
        except httpx.NetworkError as e:
            raise NotificationError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, NotificationError):
                raise
            raise NotificationError(f"Unexpected error: {str(e)}")
    
    def _render_email_template(
        self,
        event_type: NotificationEventType,
        event_data: Dict[str, Any]
    ) -> tuple[str, str]:
        """Render email template for event type.
        
        Args:
            event_type: Type of notification event
            event_data: Event-specific data
            
        Returns:
            Tuple of (subject, body)
        """
        templates = {
            NotificationEventType.TRANSACTION_INITIATED: (
                "Transaction Initiated - {property_address}",
                """A new escrow transaction has been initiated.

Transaction ID: {transaction_id}
Property: {property_address}
Earnest Money: ${earnest_money}
Target Closing Date: {target_closing_date}

The earnest money has been deposited into the smart contract wallet.
All parties will be notified as verification tasks are assigned.

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.EARNEST_MONEY_RECEIVED: (
                "Earnest Money Received - {property_address}",
                """The earnest money deposit has been received and confirmed.

Transaction ID: {transaction_id}
Amount: ${earnest_money}
Wallet ID: {wallet_id}

Verification tasks are now being assigned to agents.

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.VERIFICATION_ASSIGNED: (
                "Verification Task Assigned - {verification_type}",
                """You have been assigned a verification task.

Transaction ID: {transaction_id}
Verification Type: {verification_type}
Deadline: {deadline}
Payment Amount: ${payment_amount}

Please complete this task by the deadline. Payment will be released automatically upon completion.

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.VERIFICATION_COMPLETED: (
                "Verification Completed - {verification_type}",
                """A verification task has been completed.

Transaction ID: {transaction_id}
Verification Type: {verification_type}
Status: {status}
Completed By: {agent_name}

Payment of ${payment_amount} has been released to the verification agent.

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.VERIFICATION_FAILED: (
                "Verification Failed - {verification_type}",
                """A verification task has failed.

Transaction ID: {transaction_id}
Verification Type: {verification_type}
Reason: {failure_reason}

This issue requires immediate attention. Please review and take appropriate action.

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.PAYMENT_RELEASED: (
                "Payment Released - ${amount}",
                """A payment has been released from the escrow wallet.

Transaction ID: {transaction_id}
Recipient: {recipient_name}
Amount: ${amount}
Payment Type: {payment_type}

Blockchain Transaction: {blockchain_tx_hash}

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.PAYMENT_FAILED: (
                "Payment Failed - Action Required",
                """A payment has failed and requires attention.

Transaction ID: {transaction_id}
Amount: ${amount}
Recipient: {recipient_name}
Failure Reason: {failure_reason}

Please review the transaction and take corrective action.

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.SETTLEMENT_PENDING: (
                "Settlement Pending - {property_address}",
                """All verifications are complete. Settlement is pending.

Transaction ID: {transaction_id}
Property: {property_address}
Total Amount: ${total_amount}
Seller Amount: ${seller_amount}

Settlement will be executed within 1 business day.

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.SETTLEMENT_COMPLETED: (
                "Settlement Completed - {property_address}",
                """The transaction has been successfully settled.

Transaction ID: {transaction_id}
Property: {property_address}
Settlement Amount: ${total_amount}
Closing Date: {closing_date}

All funds have been distributed. Blockchain transaction: {blockchain_tx_hash}

Congratulations on the successful transaction!

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.DISPUTE_RAISED: (
                "Dispute Raised - {property_address}",
                """A dispute has been raised for this transaction.

Transaction ID: {transaction_id}
Property: {property_address}
Dispute Type: {dispute_type}
Raised By: {raised_by}

The transaction is now in dispute status. All parties have access to the complete audit trail.

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.DEADLINE_APPROACHING: (
                "Deadline Approaching - {verification_type}",
                """A verification task deadline is approaching.

Transaction ID: {transaction_id}
Verification Type: {verification_type}
Deadline: {deadline}
Time Remaining: {time_remaining}

Please complete this task as soon as possible to avoid delays.

Best regards,
Counter Escrow Agent"""
            ),
            NotificationEventType.DEADLINE_EXCEEDED: (
                "URGENT: Deadline Exceeded - {verification_type}",
                """A verification task has exceeded its deadline.

Transaction ID: {transaction_id}
Verification Type: {verification_type}
Deadline: {deadline}
Overdue By: {overdue_duration}

This delay is impacting the transaction timeline. Immediate action required.

Best regards,
Counter Escrow Agent"""
            )
        }
        
        subject_template, body_template = templates.get(
            event_type,
            ("Transaction Update", "Transaction ID: {transaction_id}\n\n{event_data}")
        )
        
        # Format templates with event data
        try:
            subject = subject_template.format(**event_data)
            body = body_template.format(**event_data)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            subject = subject_template
            body = body_template
        
        return subject, body
    
    def _render_sms_template(
        self,
        event_type: NotificationEventType,
        event_data: Dict[str, Any]
    ) -> str:
        """Render SMS template for event type.
        
        Args:
            event_type: Type of notification event
            event_data: Event-specific data
            
        Returns:
            SMS message text
        """
        templates = {
            NotificationEventType.TRANSACTION_INITIATED: (
                "Counter Escrow: Transaction {transaction_id} initiated for {property_address}. "
                "Earnest money ${earnest_money} received."
            ),
            NotificationEventType.EARNEST_MONEY_RECEIVED: (
                "Counter Escrow: Earnest money ${earnest_money} confirmed for transaction {transaction_id}."
            ),
            NotificationEventType.VERIFICATION_ASSIGNED: (
                "Counter Escrow: You've been assigned {verification_type} task for transaction {transaction_id}. "
                "Deadline: {deadline}. Payment: ${payment_amount}."
            ),
            NotificationEventType.VERIFICATION_COMPLETED: (
                "Counter Escrow: {verification_type} completed for transaction {transaction_id}. "
                "Payment ${payment_amount} released."
            ),
            NotificationEventType.VERIFICATION_FAILED: (
                "Counter Escrow: {verification_type} failed for transaction {transaction_id}. "
                "Reason: {failure_reason}. Action required."
            ),
            NotificationEventType.PAYMENT_RELEASED: (
                "Counter Escrow: Payment ${amount} released to {recipient_name} for transaction {transaction_id}."
            ),
            NotificationEventType.PAYMENT_FAILED: (
                "Counter Escrow: Payment failed for transaction {transaction_id}. "
                "Amount: ${amount}. Action required."
            ),
            NotificationEventType.SETTLEMENT_PENDING: (
                "Counter Escrow: Settlement pending for {property_address}. "
                "Transaction {transaction_id}. Amount: ${total_amount}."
            ),
            NotificationEventType.SETTLEMENT_COMPLETED: (
                "Counter Escrow: Settlement completed for {property_address}! "
                "Transaction {transaction_id}. Amount: ${total_amount}."
            ),
            NotificationEventType.DISPUTE_RAISED: (
                "Counter Escrow: DISPUTE raised for transaction {transaction_id}. "
                "Type: {dispute_type}. Review required."
            ),
            NotificationEventType.DEADLINE_APPROACHING: (
                "Counter Escrow: Deadline approaching for {verification_type} task. "
                "Transaction {transaction_id}. Due: {deadline}."
            ),
            NotificationEventType.DEADLINE_EXCEEDED: (
                "Counter Escrow: URGENT - Deadline exceeded for {verification_type}. "
                "Transaction {transaction_id}. Overdue: {overdue_duration}."
            )
        }
        
        template = templates.get(
            event_type,
            "Counter Escrow: Update for transaction {transaction_id}"
        )
        
        # Format template with event data
        try:
            message = template.format(**event_data)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            message = template
        
        return message
