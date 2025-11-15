"""Email client for sending viewing requests to listing agents."""
import httpx
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailAPIError(Exception):
    """Exception raised for email API errors."""
    pass


class EmailClient:
    """Client for sending emails via SendGrid or Gmail API."""
    
    def __init__(self, sendgrid_api_key: Optional[str] = None):
        """Initialize the email client.
        
        Args:
            sendgrid_api_key: SendGrid API key for sending emails
        """
        self.sendgrid_api_key = sendgrid_api_key
        self.sendgrid_url = "https://api.sendgrid.com/v3/mail/send"
    
    async def send_viewing_request(
        self,
        to_email: str,
        agent_name: str,
        user_name: str,
        user_email: str,
        user_phone: str,
        property_address: str,
        requested_time: datetime,
        pre_approved: bool = False,
        from_email: str = "assistant@counter.app",
        from_name: str = "Counter Assistant"
    ) -> bool:
        """Send a viewing request email to a listing agent.
        
        Args:
            to_email: Agent's email address
            agent_name: Agent's name
            user_name: Buyer's name
            user_email: Buyer's email
            user_phone: Buyer's phone number
            property_address: Property address
            requested_time: Requested viewing time
            pre_approved: Whether buyer is pre-approved
            from_email: Sender email address
            from_name: Sender name
            
        Returns:
            True if email sent successfully
            
        Raises:
            EmailAPIError: If sending fails
        """
        logger.info(f"Sending viewing request to {to_email} for {property_address}")
        
        # Format the requested time
        time_str = requested_time.strftime('%A, %B %d at %I:%M %p')
        
        # Build email subject
        subject = f"Showing Request: {property_address}"
        
        # Build email body
        pre_approval_text = "Pre-approved" if pre_approved else "Working on pre-approval"
        
        body = f"""Hi {agent_name},

My client {user_name} is interested in viewing the property at {property_address}.

Requested Viewing Time: {time_str}
Buyer Status: {pre_approval_text}

Please confirm availability or suggest alternative times that work for you.

Buyer Contact Information:
Name: {user_name}
Email: {user_email}
Phone: {user_phone}

Best regards,
{from_name}
On behalf of {user_name}
"""
        
        # Send via SendGrid if API key is available
        if self.sendgrid_api_key:
            return await self._send_via_sendgrid(
                to_email=to_email,
                from_email=from_email,
                from_name=from_name,
                subject=subject,
                body=body
            )
        else:
            # Log the email that would be sent (for development/testing)
            logger.warning("No SendGrid API key configured. Email would be sent:")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body:\n{body}")
            return True
    
    async def send_automated_response(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: Optional[list] = None,
        from_email: str = "assistant@counter.app",
        from_name: str = "Counter Assistant"
    ) -> bool:
        """Send an automated email response with optional attachments.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            attachments: List of attachments [{"filename": "file.pdf", "content": bytes}]
            from_email: Sender email address
            from_name: Sender name
            
        Returns:
            True if email sent successfully
            
        Raises:
            EmailAPIError: If sending fails
        """
        if self.sendgrid_api_key:
            return await self._send_via_sendgrid(
                to_email=to_email,
                from_email=from_email,
                from_name=from_name,
                subject=subject,
                body=body,
                attachments=attachments
            )
        else:
            logger.warning("No SendGrid API key configured. Email would be sent:")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body:\n{body}")
            if attachments:
                logger.info(f"Attachments: {[a.get('filename') for a in attachments]}")
            return True
    
    async def _send_via_sendgrid(
        self,
        to_email: str,
        from_email: str,
        from_name: str,
        subject: str,
        body: str,
        attachments: Optional[list] = None
    ) -> bool:
        """Send email via SendGrid API.
        
        Args:
            to_email: Recipient email
            from_email: Sender email
            from_name: Sender name
            subject: Email subject
            body: Email body (plain text)
            
        Returns:
            True if successful
            
        Raises:
            EmailAPIError: If sending fails
        """
        headers = {
            "Authorization": f"Bearer {self.sendgrid_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {
                "email": from_email,
                "name": from_name
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": body
                }
            ]
        }
        
        # Add attachments if provided
        if attachments:
            import base64
            payload["attachments"] = []
            for attachment in attachments:
                content = attachment.get("content")
                if isinstance(content, bytes):
                    content_b64 = base64.b64encode(content).decode('utf-8')
                else:
                    content_b64 = content
                
                payload["attachments"].append({
                    "content": content_b64,
                    "filename": attachment.get("filename", "attachment"),
                    "type": attachment.get("type", "application/octet-stream"),
                    "disposition": "attachment"
                })
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.sendgrid_url,
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code in [200, 202]:
                    logger.info(f"Email sent successfully to {to_email}")
                    return True
                elif response.status_code == 401:
                    raise EmailAPIError("Invalid SendGrid API key")
                else:
                    error_msg = f"SendGrid API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data}"
                    except:
                        pass
                    raise EmailAPIError(error_msg)
                    
        except httpx.TimeoutException:
            raise EmailAPIError("Email send timeout")
        except httpx.NetworkError as e:
            raise EmailAPIError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, EmailAPIError):
                raise
            raise EmailAPIError(f"Unexpected error: {str(e)}")
