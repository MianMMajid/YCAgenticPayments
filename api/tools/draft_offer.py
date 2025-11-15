"""Offer generator tool endpoint."""
import logging
import re
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from config.settings import settings
from services.docusign_client import DocusignClient, DocusignAPIError
from models.database import get_db
from models.offer import Offer
from api.middleware import update_user_session
from models.user import User
from api.rate_limit import limiter
from api.metrics import metrics

logger = logging.getLogger(__name__)

router = APIRouter()


# State to Docusign Template ID Mapping
STATE_TEMPLATES = {
    "MD": "maryland_purchase_agreement_template",
    "VA": "virginia_purchase_agreement_template",
    "DC": "dc_purchase_agreement_template",
    "PA": "pennsylvania_purchase_agreement_template",
    "DE": "delaware_purchase_agreement_template",
    "NJ": "new_jersey_purchase_agreement_template",
    "NY": "new_york_purchase_agreement_template",
    "FL": "florida_purchase_agreement_template",
    "TX": "texas_purchase_agreement_template",
    "CA": "california_purchase_agreement_template",
}


def parse_state_from_address(address: str) -> Optional[str]:
    """
    Extract state abbreviation from property address.
    
    Args:
        address: Full property address
        
    Returns:
        Two-letter state abbreviation or None if not found
    """
    # Common patterns: "City, ST ZIP" or "City, State ZIP"
    # Look for 2-letter state codes
    state_pattern = r'\b([A-Z]{2})\b'
    matches = re.findall(state_pattern, address.upper())
    
    if matches:
        # Return the last match (most likely to be the state)
        potential_state = matches[-1]
        # Verify it's a valid state in our template mapping
        if potential_state in STATE_TEMPLATES:
            return potential_state
    
    return None


def format_currency(amount: int) -> str:
    """
    Format an integer amount as currency string.
    
    Args:
        amount: Dollar amount as integer
        
    Returns:
        Formatted currency string (e.g., "$385,000")
    """
    return f"${amount:,}"


def calculate_closing_date(closing_days: int) -> str:
    """
    Calculate closing date from current date plus specified days.
    
    Args:
        closing_days: Number of days until closing
        
    Returns:
        Closing date in MM/DD/YYYY format
    """
    closing_date = datetime.now() + timedelta(days=closing_days)
    return closing_date.strftime("%m/%d/%Y")


def build_docusign_tabs(
    address: str,
    offer_price: int,
    list_price: Optional[int],
    closing_date: str,
    financing_type: str,
    contingencies: List[str],
    earnest_money: Optional[int],
    special_terms: Optional[str],
    user_name: str
) -> dict:
    """
    Build Docusign template tabs with populated offer data.
    
    Args:
        address: Property address
        offer_price: Offer price amount
        list_price: Original listing price
        closing_date: Closing date string
        financing_type: Type of financing
        contingencies: List of contingency types
        earnest_money: Earnest money deposit amount
        special_terms: Additional special terms
        user_name: Buyer's full name
        
    Returns:
        Dictionary of Docusign tabs
    """
    tabs = {
        "textTabs": [
            {"tabLabel": "PropertyAddress", "value": address},
            {"tabLabel": "PurchasePrice", "value": format_currency(offer_price)},
            {"tabLabel": "ClosingDate", "value": closing_date},
            {"tabLabel": "BuyerName", "value": user_name},
            {"tabLabel": "FinancingType", "value": financing_type.upper()},
        ],
        "checkboxTabs": [
            {
                "tabLabel": "InspectionContingency",
                "selected": "inspection" in [c.lower() for c in contingencies]
            },
            {
                "tabLabel": "AppraisalContingency",
                "selected": "appraisal" in [c.lower() for c in contingencies]
            },
            {
                "tabLabel": "FinancingContingency",
                "selected": "financing" in [c.lower() for c in contingencies]
            },
            {
                "tabLabel": "HomeSaleContingency",
                "selected": "home_sale" in [c.lower() for c in contingencies]
            },
        ]
    }
    
    # Add optional fields
    if list_price:
        tabs["textTabs"].append({
            "tabLabel": "ListPrice",
            "value": format_currency(list_price)
        })
    
    if earnest_money:
        tabs["textTabs"].append({
            "tabLabel": "EarnestMoney",
            "value": format_currency(earnest_money)
        })
    
    if special_terms:
        tabs["textTabs"].append({
            "tabLabel": "SpecialTerms",
            "value": special_terms
        })
    
    return tabs


# Pydantic Models
class OfferRequest(BaseModel):
    """Request model for drafting a purchase offer."""
    
    property_id: str = Field(..., description="Unique property identifier")
    address: str = Field(..., description="Full property address", min_length=1)
    offer_price: int = Field(..., description="Offer price in dollars", gt=0)
    list_price: Optional[int] = Field(None, description="Original listing price", gt=0)
    closing_days: int = Field(..., description="Number of days until closing", ge=7, le=90)
    financing_type: str = Field(..., description="Type of financing (cash, conventional, fha, va)")
    contingencies: List[str] = Field(
        default_factory=list,
        description="List of contingencies (inspection, appraisal, financing, home_sale)"
    )
    earnest_money: Optional[int] = Field(None, description="Earnest money deposit amount", gt=0)
    special_terms: Optional[str] = Field(None, description="Additional special terms or conditions", max_length=2000)
    user_id: str = Field(..., description="User identifier")
    user_email: str = Field(..., description="User email address for signing")
    user_name: str = Field(..., description="User full name")
    
    @validator('financing_type')
    def validate_financing_type(cls, v):
        """Validate financing type is one of the allowed values."""
        allowed_types = ['cash', 'conventional', 'fha', 'va', 'usda']
        if v.lower() not in allowed_types:
            raise ValueError(f'financing_type must be one of: {", ".join(allowed_types)}')
        return v.lower()
    
    @validator('contingencies')
    def validate_contingencies(cls, v):
        """Validate contingency types."""
        allowed_contingencies = ['inspection', 'appraisal', 'financing', 'home_sale']
        for contingency in v:
            if contingency.lower() not in allowed_contingencies:
                raise ValueError(f'Invalid contingency: {contingency}. Must be one of: {", ".join(allowed_contingencies)}')
        return [c.lower() for c in v]
    
    @validator('offer_price')
    def validate_offer_price(cls, v, values):
        """Ensure offer price is reasonable if list price is provided."""
        if 'list_price' in values and values['list_price'] is not None:
            # Warn if offer is more than 20% above list price (unusual)
            if v > values['list_price'] * 1.2:
                logger.warning(f"Offer price {v} is more than 20% above list price {values['list_price']}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "property_id": "prop_123",
                "address": "123 Main St, Baltimore, MD 21201",
                "offer_price": 350000,
                "list_price": 385000,
                "closing_days": 30,
                "financing_type": "conventional",
                "contingencies": ["inspection", "appraisal", "financing"],
                "earnest_money": 10000,
                "special_terms": "Seller to provide home warranty",
                "user_id": "user_123",
                "user_email": "buyer@example.com",
                "user_name": "John Doe"
            }
        }


class OfferResponse(BaseModel):
    """Response model for offer generation."""
    
    status: str = Field(..., description="Status of the offer (sent, error)")
    message: str = Field(..., description="Human-readable status message")
    offer_id: Optional[str] = Field(None, description="Database offer ID")
    envelope_id: Optional[str] = Field(None, description="Docusign envelope ID")
    signing_url: Optional[str] = Field(None, description="URL for signing the document")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "sent",
                "message": "Offer sent successfully. Check your email for the signing link.",
                "offer_id": "offer_123",
                "envelope_id": "env_abc123",
                "signing_url": "https://demo.docusign.net/Signing/..."
            }
        }


@router.post("/draft-offer", response_model=OfferResponse)
@limiter.limit("10/minute")
async def draft_offer(
    request: OfferRequest,
    db: Session = Depends(get_db)
):
    """
    Draft and send a purchase offer for a property.
    
    This endpoint creates a state-specific purchase agreement using Docusign templates,
    populates it with the offer terms, and sends it to the buyer for e-signature.
    
    Args:
        request: Offer parameters including property details, price, and terms
        db: Database session
        
    Returns:
        OfferResponse with envelope ID and signing URL
        
    Raises:
        HTTPException: If offer creation fails or state is not supported
    """
    logger.info(f"Draft offer request: property={request.property_id}, price={request.offer_price}, user={request.user_id}")
    
    # Update user session timestamp
    update_user_session(request.user_id, db)
    
    try:
        # Parse state from address
        state = parse_state_from_address(request.address)
        
        if not state:
            logger.error(f"Could not parse state from address: {request.address}")
            raise HTTPException(
                status_code=400,
                detail="Could not determine state from property address. Please ensure address includes state abbreviation."
            )
        
        # Check if state template is supported
        if state not in STATE_TEMPLATES:
            logger.error(f"State {state} not supported")
            raise HTTPException(
                status_code=400,
                detail=f"Purchase agreements for {state} are not yet supported. Currently supported states: {', '.join(STATE_TEMPLATES.keys())}"
            )
        
        template_id = STATE_TEMPLATES[state]
        logger.info(f"Using template {template_id} for state {state}")
        
        # Calculate closing date
        closing_date_str = calculate_closing_date(request.closing_days)
        
        # Build Docusign tabs
        tabs = build_docusign_tabs(
            address=request.address,
            offer_price=request.offer_price,
            list_price=request.list_price,
            closing_date=closing_date_str,
            financing_type=request.financing_type,
            contingencies=request.contingencies,
            earnest_money=request.earnest_money,
            special_terms=request.special_terms,
            user_name=request.user_name
        )
        
        # Initialize Docusign client
        docusign_client = DocusignClient(
            integration_key=settings.docusign_integration_key,
            secret_key=settings.docusign_secret_key,
            account_id=settings.docusign_account_id,
            use_production=settings.environment == "production"
        )
        
        # Create envelope
        try:
            envelope_result = await docusign_client.create_envelope_from_template(
                template_id=template_id,
                signer_email=request.user_email,
                signer_name=request.user_name,
                tabs=tabs,
                email_subject=f"Purchase Offer for {request.address}",
                status="sent"
            )
            
            envelope_id = envelope_result["envelope_id"]
            signing_url = envelope_result["signing_url"]
            
            logger.info(f"Created Docusign envelope {envelope_id}")
            
        except DocusignAPIError as e:
            logger.error(f"Docusign API error: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to create offer document: {str(e)}"
            )
        
        # Store offer in database
        try:
            offer = Offer(
                user_id=request.user_id,
                property_id=request.property_id,
                address=request.address,
                offer_price=request.offer_price,
                list_price=request.list_price,
                closing_days=request.closing_days,
                closing_date=closing_date_str,
                financing_type=request.financing_type,
                contingencies=request.contingencies,
                earnest_money=request.earnest_money,
                special_terms=request.special_terms,
                envelope_id=envelope_id,
                signing_url=signing_url,
                template_id=template_id,
                status="sent",
                sent_at=datetime.now().isoformat()
            )
            
            db.add(offer)
            db.commit()
            db.refresh(offer)
            
            logger.info(f"Saved offer {offer.id} to database")
            
            # Track offer generation metric
            metrics.track_offer_generated(
                user_id=request.user_id,
                property_id=request.property_id,
                offer_price=request.offer_price
            )
            
            return OfferResponse(
                status="sent",
                message="Offer sent successfully. Check your email for the signing link.",
                offer_id=offer.id,
                envelope_id=envelope_id,
                signing_url=signing_url
            )
            
        except Exception as e:
            logger.error(f"Failed to save offer to database: {e}")
            db.rollback()
            # Still return success since envelope was created
            return OfferResponse(
                status="sent",
                message="Offer sent successfully, but failed to save to history. Check your email for the signing link.",
                offer_id=None,
                envelope_id=envelope_id,
                signing_url=signing_url
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in draft-offer endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while drafting the offer"
        )



# Webhook Models
class DocusignWebhookEvent(BaseModel):
    """Model for Docusign webhook event data."""
    
    event: str = Field(..., description="Event type (envelope-sent, envelope-completed, etc.)")
    apiVersion: str = Field(..., description="Docusign API version")
    uri: str = Field(..., description="Resource URI")
    retryCount: int = Field(default=0, description="Retry count for this webhook")
    configurationId: str = Field(..., description="Webhook configuration ID")
    generatedDateTime: str = Field(..., description="Event generation timestamp")
    data: dict = Field(..., description="Event data containing envelope information")


def validate_docusign_webhook_signature(
    request_body: bytes,
    signature: str,
    webhook_secret: str
) -> bool:
    """
    Validate Docusign webhook signature using HMAC.
    
    Args:
        request_body: Raw request body bytes
        signature: Signature from X-DocuSign-Signature-1 header
        webhook_secret: Webhook secret key
        
    Returns:
        True if signature is valid, False otherwise
    """
    import hmac
    import hashlib
    import base64
    
    # Compute HMAC-SHA256
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        request_body,
        hashlib.sha256
    ).digest()
    
    # Base64 encode
    expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')
    
    # Compare signatures
    return hmac.compare_digest(expected_signature_b64, signature)


@router.post("/webhooks/docusign")
async def docusign_webhook(
    event: DocusignWebhookEvent,
    db: Session = Depends(get_db)
):
    """
    Handle Docusign webhook events for envelope status updates.
    
    This endpoint receives notifications when envelopes are signed, completed,
    declined, or voided. It updates the offer status in the database accordingly.
    
    Args:
        event: Docusign webhook event data
        db: Database session
        
    Returns:
        Success acknowledgment
        
    Note:
        Signature validation should be added in production using middleware
        or by accessing the raw request body and X-DocuSign-Signature-1 header.
    """
    logger.info(f"Received Docusign webhook: event={event.event}, uri={event.uri}")
    
    try:
        # Extract envelope information
        envelope_summary = event.data.get("envelopeSummary", {})
        envelope_id = envelope_summary.get("envelopeId")
        status = envelope_summary.get("status")
        completed_datetime = envelope_summary.get("completedDateTime")
        
        if not envelope_id:
            logger.error("Webhook missing envelope ID")
            raise HTTPException(status_code=400, detail="Missing envelope ID in webhook data")
        
        logger.info(f"Processing webhook for envelope {envelope_id}, status={status}")
        
        # Find offer by envelope ID
        offer = db.query(Offer).filter(Offer.envelope_id == envelope_id).first()
        
        if not offer:
            logger.warning(f"No offer found for envelope {envelope_id}")
            # Return 200 to acknowledge receipt even if offer not found
            return {"status": "acknowledged", "message": "Envelope not found in database"}
        
        # Update offer status based on envelope status
        status_mapping = {
            "completed": "signed",
            "signed": "signed",
            "declined": "rejected",
            "voided": "rejected",
            "delivered": "sent",
        }
        
        new_status = status_mapping.get(status.lower(), offer.status)
        
        if new_status != offer.status:
            logger.info(f"Updating offer {offer.id} status from {offer.status} to {new_status}")
            offer.status = new_status
            
            # Set signed_at timestamp if completed
            if new_status == "signed" and completed_datetime:
                offer.signed_at = completed_datetime
            elif new_status == "signed" and not completed_datetime:
                offer.signed_at = datetime.now().isoformat()
            
            db.commit()
            logger.info(f"Successfully updated offer {offer.id}")
        else:
            logger.info(f"Offer {offer.id} status unchanged: {offer.status}")
        
        return {
            "status": "success",
            "message": f"Processed webhook for envelope {envelope_id}",
            "offer_id": offer.id,
            "new_status": offer.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Docusign webhook: {e}", exc_info=True)
        # Return 200 to prevent Docusign from retrying
        return {
            "status": "error",
            "message": "Failed to process webhook but acknowledged receipt"
        }
