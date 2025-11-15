"""Webhook handlers for incoming emails, Agentic Stripe, and verification agents."""
import logging
import base64
import hmac
import hashlib
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import User
from models.transaction import Transaction
from models.verification import VerificationTask, VerificationType, VerificationReport, ReportStatus
from models.payment import Payment, PaymentStatus
from services.email_client import EmailClient, EmailAPIError
from agents.escrow_agent_orchestrator import EscrowAgentOrchestrator
from config.settings import settings
from api.monitoring import add_breadcrumb

logger = logging.getLogger(__name__)

router = APIRouter()


class EmailWebhookEvent(BaseModel):
    """Model for incoming email webhook event."""
    
    from_email: str = Field(..., description="Sender email address")
    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    text: Optional[str] = Field(None, description="Plain text body")
    html: Optional[str] = Field(None, description="HTML body")
    attachments: list = Field(default_factory=list, description="Email attachments")
    headers: Dict[str, Any] = Field(default_factory=dict, description="Email headers")
    timestamp: str = Field(..., description="Email timestamp")


class EmailResponse(BaseModel):
    """Model for automated email response."""
    
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    email_sent: bool = Field(default=False, description="Whether response email was sent")


async def process_incoming_email(
    from_email: str,
    subject: str,
    text: Optional[str],
    html: Optional[str],
    attachments: list,
    db: Session
) -> EmailResponse:
    """
    Process incoming email and generate automated response.
    
    Args:
        from_email: Sender email address
        subject: Email subject
        text: Plain text body
        html: HTML body
        attachments: List of attachments
        db: Database session
        
    Returns:
        EmailResponse with processing status
    """
    logger.info(f"Processing incoming email from {from_email}, subject: {subject}")
    
    # Find user by email
    user = db.query(User).filter(User.email == from_email).first()
    
    if not user:
        logger.warning(f"No user found for email: {from_email}")
        return EmailResponse(
            status="error",
            message="User not found. Please register first.",
            email_sent=False
        )
    
    # Process email content based on subject/body
    # This is a basic implementation - you can extend this based on your needs
    
    # Check if email contains property-related keywords
    email_content = (text or html or "").lower()
    subject_lower = subject.lower()
    
    # Determine response based on email content
    response_subject = None
    response_body = None
    response_attachments = []
    
    # Example: Handle viewing confirmation requests
    if "viewing" in subject_lower or "viewing" in email_content:
        response_subject = "Viewing Request Confirmation"
        response_body = f"""Hi {user.name or 'there'},

Thank you for your viewing request. We've received your email and will process it shortly.

If you have any questions, please call us or reply to this email.

Best regards,
Counter Assistant
"""
    
    # Example: Handle offer-related emails
    elif "offer" in subject_lower or "offer" in email_content:
        response_subject = "Offer Received"
        response_body = f"""Hi {user.name or 'there'},

We've received your offer inquiry. Our team will review it and get back to you soon.

Best regards,
Counter Assistant
"""
    
    # Default response
    else:
        response_subject = "Thank you for contacting Counter"
        response_body = f"""Hi {user.name or 'there'},

Thank you for reaching out. We've received your email and will respond as soon as possible.

For immediate assistance, please call us at your convenience.

Best regards,
Counter Assistant
"""
    
    # Send automated response
    email_sent = False
    if response_subject and response_body:
        try:
            email_client = EmailClient(sendgrid_api_key=settings.sendgrid_api_key)
            
            # Add attachments if needed (e.g., property documents, offer templates)
            # Example: response_attachments = [{"filename": "property_info.pdf", "content": pdf_bytes}]
            response_attachments = []
            
            # You can add logic here to attach documents based on email content
            # For example, if user asks for property info, attach property PDF
            
            email_sent = await email_client.send_automated_response(
                to_email=from_email,
                subject=response_subject,
                body=response_body,
                attachments=response_attachments if response_attachments else None,
                from_email="assistant@counter.app",
                from_name="Counter Assistant"
            )
            
            logger.info(f"Sent automated response to {from_email}")
            
        except EmailAPIError as e:
            logger.error(f"Failed to send automated response: {e}")
    
    return EmailResponse(
        status="processed",
        message="Email processed successfully",
        email_sent=email_sent
    )


@router.post("/webhooks/email")
async def email_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature")
):
    """
    Handle incoming email webhook.
    
    This endpoint receives emails from email service providers (SendGrid Inbound Parse,
    Mailgun, etc.) and processes them to send automated responses.
    
    Args:
        request: FastAPI request object
        db: Database session
        x_webhook_signature: Webhook signature for validation
        
    Returns:
        Success acknowledgment
    """
    add_breadcrumb(
        message="Incoming email webhook received",
        category="webhook",
        data={"path": request.url.path}
    )
    
    try:
        # Parse incoming email data
        # Format depends on email service provider (SendGrid, Mailgun, etc.)
        form_data = await request.form()
        
        # Extract email fields (SendGrid Inbound Parse format)
        from_email = form_data.get("from", "")
        to_email = form_data.get("to", "")
        subject = form_data.get("subject", "")
        text = form_data.get("text", "")
        html = form_data.get("html", "")
        
        # Extract attachments
        attachments = []
        # Handle file attachments if present
        # for key, file in form_data.items():
        #     if key.startswith("attachment"):
        #         attachments.append({
        #             "filename": file.filename,
        #             "content": await file.read()
        #         })
        
        # Process the email
        result = await process_incoming_email(
            from_email=from_email,
            subject=subject,
            text=text,
            html=html,
            attachments=attachments,
            db=db
        )
        
        logger.info(f"Processed email from {from_email}, response sent: {result.email_sent}")
        
        return {
            "status": "success",
            "message": "Email processed",
            "response_sent": result.email_sent
        }
        
    except Exception as e:
        logger.error(f"Error processing email webhook: {e}", exc_info=True)
        # Return 200 to prevent email service from retrying
        return {
            "status": "error",
            "message": "Failed to process email but acknowledged receipt"
        }


@router.post("/webhooks/email/sendgrid")
async def sendgrid_email_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle SendGrid Inbound Parse webhook.
    
    SendGrid Inbound Parse sends emails as multipart/form-data.
    See: https://docs.sendgrid.com/for-developers/parsing-email/setting-up-the-inbound-parse-webhook
    """
    return await email_webhook(request, db)


@router.post("/webhooks/email/mailgun")
async def mailgun_email_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Mailgun webhook for incoming emails.
    
    Mailgun sends emails as form data.
    See: https://documentation.mailgun.com/en/latest/user_manual.html#receiving-messages
    """
    return await email_webhook(request, db)



# ============================================================================
# Agentic Stripe Webhook Handlers
# ============================================================================

class AgenticStripeWebhookEvent(BaseModel):
    """Model for Agentic Stripe webhook event."""
    
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    wallet_id: str = Field(..., description="Wallet identifier")
    transaction_id: Optional[str] = Field(None, description="Transaction identifier")
    payment_id: Optional[str] = Field(None, description="Payment identifier")
    amount: Optional[str] = Field(None, description="Payment amount")
    recipient: Optional[str] = Field(None, description="Payment recipient")
    status: str = Field(..., description="Event status")
    blockchain_tx_hash: Optional[str] = Field(None, description="Blockchain transaction hash")
    timestamp: str = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")


def verify_agentic_stripe_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """
    Verify Agentic Stripe webhook signature.
    
    Args:
        payload: Raw request payload
        signature: Signature from X-Agentic-Stripe-Signature header
        secret: Webhook secret
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Compute expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant-time comparison)
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying Agentic Stripe signature: {str(e)}")
        return False


async def handle_payment_success(
    event: AgenticStripeWebhookEvent,
    db: Session
) -> None:
    """
    Handle successful payment event from Agentic Stripe.
    
    Args:
        event: Webhook event
        db: Database session
    """
    logger.info(
        f"Processing payment success event: {event.event_id}",
        extra={
            "payment_id": event.payment_id,
            "wallet_id": event.wallet_id,
            "amount": event.amount
        }
    )
    
    try:
        # Find payment record by payment_id or wallet_id
        payment = None
        if event.payment_id:
            payment = db.query(Payment).filter(
                Payment.id == event.payment_id
            ).first()
        
        if not payment and event.wallet_id:
            # Find most recent pending payment for this wallet
            payment = db.query(Payment).filter(
                Payment.wallet_id == event.wallet_id,
                Payment.status == PaymentStatus.PROCESSING
            ).order_by(Payment.initiated_at.desc()).first()
        
        if payment:
            # Update payment status
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.fromisoformat(event.timestamp)
            if event.blockchain_tx_hash:
                payment.blockchain_tx_hash = event.blockchain_tx_hash
            
            db.add(payment)
            db.commit()
            
            logger.info(f"Payment {payment.id} marked as completed")
        else:
            logger.warning(
                f"No payment found for event {event.event_id}",
                extra={"payment_id": event.payment_id, "wallet_id": event.wallet_id}
            )
    
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")
        db.rollback()
        raise


async def handle_payment_failure(
    event: AgenticStripeWebhookEvent,
    db: Session
) -> None:
    """
    Handle failed payment event from Agentic Stripe.
    
    Args:
        event: Webhook event
        db: Database session
    """
    logger.warning(
        f"Processing payment failure event: {event.event_id}",
        extra={
            "payment_id": event.payment_id,
            "wallet_id": event.wallet_id,
            "amount": event.amount
        }
    )
    
    try:
        # Find payment record
        payment = None
        if event.payment_id:
            payment = db.query(Payment).filter(
                Payment.id == event.payment_id
            ).first()
        
        if not payment and event.wallet_id:
            # Find most recent pending payment for this wallet
            payment = db.query(Payment).filter(
                Payment.wallet_id == event.wallet_id,
                Payment.status == PaymentStatus.PROCESSING
            ).order_by(Payment.initiated_at.desc()).first()
        
        if payment:
            # Update payment status
            payment.status = PaymentStatus.FAILED
            
            db.add(payment)
            db.commit()
            
            logger.warning(f"Payment {payment.id} marked as failed")
            
            # TODO: Trigger notification to transaction parties about payment failure
            # TODO: Implement retry logic or escalation
        else:
            logger.warning(
                f"No payment found for failure event {event.event_id}",
                extra={"payment_id": event.payment_id, "wallet_id": event.wallet_id}
            )
    
    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")
        db.rollback()
        raise


async def handle_wallet_balance_update(
    event: AgenticStripeWebhookEvent,
    db: Session
) -> None:
    """
    Handle wallet balance update event from Agentic Stripe.
    
    Args:
        event: Webhook event
        db: Database session
    """
    logger.info(
        f"Processing wallet balance update: {event.event_id}",
        extra={
            "wallet_id": event.wallet_id,
            "balance": event.data.get("balance")
        }
    )
    
    try:
        # Find transaction by wallet_id
        transaction = db.query(Transaction).filter(
            Transaction.wallet_id == event.wallet_id
        ).first()
        
        if transaction:
            # Update transaction metadata with latest balance
            if not transaction.transaction_metadata:
                transaction.transaction_metadata = {}
            
            transaction.transaction_metadata["wallet_balance"] = event.data.get("balance")
            transaction.transaction_metadata["wallet_balance_updated_at"] = event.timestamp
            
            db.add(transaction)
            db.commit()
            
            logger.info(
                f"Updated wallet balance for transaction {transaction.id}",
                extra={"balance": event.data.get("balance")}
            )
        else:
            logger.warning(
                f"No transaction found for wallet {event.wallet_id}",
                extra={"event_id": event.event_id}
            )
    
    except Exception as e:
        logger.error(f"Error handling wallet balance update: {str(e)}")
        db.rollback()
        raise


@router.post("/webhooks/agentic-stripe")
async def agentic_stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_agentic_stripe_signature: Optional[str] = Header(None, alias="X-Agentic-Stripe-Signature")
):
    """
    Handle Agentic Stripe webhook events.
    
    This endpoint receives events from Agentic Stripe including:
    - payment.success: Payment successfully processed
    - payment.failure: Payment processing failed
    - wallet.balance_updated: Wallet balance changed
    
    Args:
        request: FastAPI request object
        db: Database session
        x_agentic_stripe_signature: Webhook signature for validation
    
    Returns:
        Success acknowledgment
    """
    add_breadcrumb(
        message="Agentic Stripe webhook received",
        category="webhook",
        data={"path": request.url.path}
    )
    
    try:
        # Get raw payload for signature verification
        payload = await request.body()
        
        # Verify webhook signature
        if settings.agentic_stripe_webhook_secret:
            if not x_agentic_stripe_signature:
                logger.error("Missing webhook signature")
                raise HTTPException(status_code=401, detail="Missing signature")
            
            if not verify_agentic_stripe_signature(
                payload,
                x_agentic_stripe_signature,
                settings.agentic_stripe_webhook_secret
            ):
                logger.error("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse event data
        event_data = await request.json()
        event = AgenticStripeWebhookEvent(**event_data)
        
        logger.info(
            f"Processing Agentic Stripe event: {event.event_type}",
            extra={
                "event_id": event.event_id,
                "wallet_id": event.wallet_id
            }
        )
        
        # Route event to appropriate handler
        if event.event_type == "payment.success":
            await handle_payment_success(event, db)
        elif event.event_type == "payment.failure":
            await handle_payment_failure(event, db)
        elif event.event_type == "wallet.balance_updated":
            await handle_wallet_balance_update(event, db)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")
        
        # Log webhook event
        logger.info(
            f"Agentic Stripe webhook processed successfully",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type
            }
        )
        
        return {
            "status": "success",
            "event_id": event.event_id,
            "message": "Webhook processed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Agentic Stripe webhook: {str(e)}", exc_info=True)
        # Return 200 to prevent Agentic Stripe from retrying
        return {
            "status": "error",
            "message": "Failed to process webhook but acknowledged receipt"
        }


# ============================================================================
# Verification Agent Webhook Handlers
# ============================================================================

class VerificationWebhookEvent(BaseModel):
    """Model for verification agent webhook event."""
    
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event (completion or failure)")
    transaction_id: str = Field(..., description="Transaction identifier")
    verification_type: str = Field(..., description="Type of verification")
    agent_id: str = Field(..., description="Agent identifier")
    report_id: Optional[str] = Field(None, description="Report identifier")
    status: str = Field(..., description="Verification status")
    findings: Optional[Dict[str, Any]] = Field(None, description="Verification findings")
    documents: Optional[list] = Field(None, description="Supporting documents")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    timestamp: str = Field(..., description="Event timestamp")


def verify_agent_webhook_signature(
    payload: bytes,
    signature: str,
    agent_id: str
) -> bool:
    """
    Verify verification agent webhook signature.
    
    Args:
        payload: Raw request payload
        signature: Signature from X-Agent-Signature header
        agent_id: Agent identifier
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # In production, each agent would have their own secret key
        # For now, we use a shared secret based on agent_id
        secret = f"{settings.encryption_key}:{agent_id}"
        
        # Compute expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant-time comparison)
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying agent webhook signature: {str(e)}")
        return False


async def handle_verification_completion(
    event: VerificationWebhookEvent,
    db: Session
) -> None:
    """
    Handle verification completion notification from agent.
    
    Args:
        event: Webhook event
        db: Database session
    """
    logger.info(
        f"Processing verification completion: {event.event_id}",
        extra={
            "transaction_id": event.transaction_id,
            "verification_type": event.verification_type,
            "agent_id": event.agent_id
        }
    )
    
    try:
        # Get verification type enum
        verification_type = VerificationType(event.verification_type)
        
        # Find or create verification report
        report = None
        if event.report_id:
            report = db.query(VerificationReport).filter(
                VerificationReport.id == event.report_id
            ).first()
        
        if not report:
            # Create new report
            report = VerificationReport(
                id=event.report_id or str(uuid.uuid4()),
                task_id="",  # Will be set by orchestrator
                agent_id=event.agent_id,
                report_type=verification_type,
                status=ReportStatus(event.status) if event.status in [s.value for s in ReportStatus] else ReportStatus.NEEDS_REVIEW,
                findings=event.findings or {},
                documents=event.documents or [],
                submitted_at=datetime.fromisoformat(event.timestamp)
            )
            db.add(report)
            db.commit()
            db.refresh(report)
        
        # Process verification completion through orchestrator
        orchestrator = EscrowAgentOrchestrator(db)
        try:
            await orchestrator.process_verification_completion(
                transaction_id=event.transaction_id,
                verification_type=verification_type,
                report=report
            )
        finally:
            await orchestrator.close()
        
        logger.info(
            f"Verification completion processed for transaction {event.transaction_id}"
        )
    
    except Exception as e:
        logger.error(f"Error handling verification completion: {str(e)}")
        db.rollback()
        raise


async def handle_verification_failure(
    event: VerificationWebhookEvent,
    db: Session
) -> None:
    """
    Handle verification failure notification from agent.
    
    Args:
        event: Webhook event
        db: Database session
    """
    logger.warning(
        f"Processing verification failure: {event.event_id}",
        extra={
            "transaction_id": event.transaction_id,
            "verification_type": event.verification_type,
            "agent_id": event.agent_id,
            "error": event.error_message
        }
    )
    
    try:
        # Get verification type enum
        verification_type = VerificationType(event.verification_type)
        
        # Find verification task
        task = db.query(VerificationTask).filter(
            VerificationTask.transaction_id == event.transaction_id,
            VerificationTask.verification_type == verification_type
        ).first()
        
        if task:
            # Update task status to failed
            from models.verification import TaskStatus
            task.status = TaskStatus.FAILED
            db.add(task)
            db.commit()
            
            logger.warning(
                f"Verification task {task.id} marked as failed",
                extra={"error": event.error_message}
            )
            
            # TODO: Trigger notification to transaction parties about verification failure
            # TODO: Implement retry logic or escalation
        else:
            logger.warning(
                f"No verification task found for failure event {event.event_id}",
                extra={
                    "transaction_id": event.transaction_id,
                    "verification_type": event.verification_type
                }
            )
    
    except Exception as e:
        logger.error(f"Error handling verification failure: {str(e)}")
        db.rollback()
        raise


@router.post("/webhooks/verification/{verification_type}")
async def verification_agent_webhook(
    verification_type: str,
    request: Request,
    db: Session = Depends(get_db),
    x_agent_signature: Optional[str] = Header(None, alias="X-Agent-Signature"),
    x_agent_id: Optional[str] = Header(None, alias="X-Agent-Id")
):
    """
    Handle verification agent webhook events.
    
    This endpoint receives events from verification agents including:
    - verification.completed: Verification successfully completed
    - verification.failed: Verification failed
    
    Args:
        verification_type: Type of verification (title_search, inspection, appraisal, lending)
        request: FastAPI request object
        db: Database session
        x_agent_signature: Webhook signature for validation
        x_agent_id: Agent identifier
    
    Returns:
        Success acknowledgment
    """
    add_breadcrumb(
        message=f"Verification agent webhook received: {verification_type}",
        category="webhook",
        data={"path": request.url.path, "verification_type": verification_type}
    )
    
    try:
        # Get raw payload for signature verification
        payload = await request.body()
        
        # Verify webhook signature
        if x_agent_id and x_agent_signature:
            if not verify_agent_webhook_signature(
                payload,
                x_agent_signature,
                x_agent_id
            ):
                logger.error("Invalid agent webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        else:
            logger.warning("Missing agent authentication headers")
        
        # Parse event data
        event_data = await request.json()
        event = VerificationWebhookEvent(**event_data)
        
        # Validate verification type matches
        if event.verification_type != verification_type:
            raise HTTPException(
                status_code=400,
                detail=f"Verification type mismatch: {event.verification_type} != {verification_type}"
            )
        
        logger.info(
            f"Processing verification agent event: {event.event_type}",
            extra={
                "event_id": event.event_id,
                "verification_type": verification_type,
                "agent_id": event.agent_id
            }
        )
        
        # Route event to appropriate handler
        if event.event_type == "verification.completed":
            await handle_verification_completion(event, db)
        elif event.event_type == "verification.failed":
            await handle_verification_failure(event, db)
        else:
            logger.warning(f"Unknown event type: {event.event_type}")
        
        # Log webhook event
        logger.info(
            f"Verification agent webhook processed successfully",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "verification_type": verification_type
            }
        )
        
        return {
            "status": "success",
            "event_id": event.event_id,
            "message": "Webhook processed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error processing verification agent webhook: {str(e)}",
            exc_info=True
        )
        # Return 200 to prevent agent from retrying
        return {
            "status": "error",
            "message": "Failed to process webhook but acknowledged receipt"
        }
