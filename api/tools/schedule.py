"""Viewing scheduler tool endpoint."""
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from config.settings import settings
from services.apify_client import ApifyClient, ApifyAPIError
from services.calendar_client import CalendarClient, CalendarAPIError
from services.email_client import EmailClient, EmailAPIError
from services.cache_client import cache_client
from models.database import get_db
from models.viewing import Viewing
from api.middleware import update_user_session
from models.user import User
from api.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic Models
class ScheduleRequest(BaseModel):
    """Request model for scheduling a property viewing."""
    
    property_id: str = Field(..., description="Property identifier", min_length=1)
    listing_url: str = Field(..., description="Zillow listing URL", min_length=1)
    requested_time: str = Field(..., description="Requested viewing time (ISO 8601 format)")
    user_id: str = Field(..., description="User identifier")
    user_name: str = Field(..., description="User's full name")
    user_email: str = Field(..., description="User's email address")
    user_phone: str = Field(..., description="User's phone number")
    property_address: str = Field(..., description="Property address")
    
    @validator('requested_time')
    def validate_requested_time(cls, v):
        """Ensure requested_time is a valid ISO 8601 datetime string."""
        try:
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            # Ensure it's in the future
            if dt < datetime.now(dt.tzinfo):
                raise ValueError('requested_time must be in the future')
            return v
        except ValueError as e:
            raise ValueError(f'Invalid datetime format: {str(e)}')
    
    @validator('listing_url')
    def validate_listing_url(cls, v):
        """Ensure listing_url is a valid URL."""
        if not v.startswith('http'):
            raise ValueError('listing_url must be a valid URL')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "property_id": "prop_123",
                "listing_url": "https://www.zillow.com/homedetails/123-Main-St/...",
                "requested_time": "2025-11-15T14:00:00Z",
                "user_id": "user_123",
                "user_name": "John Doe",
                "user_email": "john@example.com",
                "user_phone": "+1-555-123-4567",
                "property_address": "123 Main St, Baltimore, MD 21201"
            }
        }


class AlternativeSlot(BaseModel):
    """Model for an alternative time slot."""
    
    start: str = Field(..., description="Start time (ISO 8601)")
    end: str = Field(..., description="End time (ISO 8601)")


class ScheduleResponse(BaseModel):
    """Response model for viewing scheduler."""
    
    status: str = Field(..., description="Status: 'requested', 'conflict', 'error'")
    message: str = Field(..., description="Human-readable status message")
    calendar_event_id: Optional[str] = Field(None, description="Google Calendar event ID")
    viewing_id: Optional[str] = Field(None, description="Database viewing record ID")
    agent_name: Optional[str] = Field(None, description="Listing agent name")
    agent_email: Optional[str] = Field(None, description="Listing agent email")
    agent_phone: Optional[str] = Field(None, description="Listing agent phone")
    alternative_slots: List[AlternativeSlot] = Field(default_factory=list, description="Alternative time slots if conflict exists")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "requested",
                "message": "Viewing request sent to agent. Pending calendar event created.",
                "calendar_event_id": "evt_abc123",
                "viewing_id": "view_xyz789",
                "agent_name": "Jane Smith",
                "agent_email": "jane@realty.com",
                "agent_phone": "+1-555-987-6543",
                "alternative_slots": []
            }
        }


async def extract_agent_contact(listing_url: str) -> dict:
    """Extract listing agent contact information.
    
    Args:
        listing_url: Zillow listing URL
        
    Returns:
        Dictionary with agent contact info
        
    Raises:
        ApifyAPIError: If scraping fails
    """
    logger.info(f"Extracting agent contact from: {listing_url}")
    
    # Initialize Apify client with caching
    apify_client = ApifyClient(
        api_token=settings.apify_api_token,
        redis_client=cache_client.client if cache_client.client else None,
        cache_ttl=604800  # 7 days
    )
    
    try:
        agent_info = await apify_client.scrape_agent_info(listing_url)
        return agent_info
    except ApifyAPIError as e:
        logger.error(f"Failed to extract agent contact: {e}")
        raise


async def check_calendar_availability(
    user: User,
    requested_time: datetime,
    duration_minutes: int = 60
) -> dict:
    """Check user's calendar availability.
    
    Args:
        user: User object with calendar token
        requested_time: Requested viewing time
        duration_minutes: Duration of viewing (default: 60 minutes)
        
    Returns:
        Dictionary with availability info
        
    Raises:
        CalendarAPIError: If calendar check fails
    """
    logger.info(f"Checking calendar availability for user {user.id}")
    
    # Check if user has calendar integration
    if not user.google_calendar_token:
        logger.warning(f"User {user.id} has no calendar integration")
        return {
            "is_available": True,
            "conflicts": [],
            "alternative_slots": []
        }
    
    # Initialize Calendar client
    calendar_client = CalendarClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret
    )
    
    # Calculate time window (requested_time ± 2 hours)
    start_time = requested_time - timedelta(hours=2)
    end_time = requested_time + timedelta(hours=2)
    
    try:
        availability = await calendar_client.check_availability(
            access_token=user.google_calendar_token,
            start_time=start_time,
            end_time=end_time
        )
        return availability
    except CalendarAPIError as e:
        logger.error(f"Failed to check calendar: {e}")
        # Don't fail the request if calendar check fails
        return {
            "is_available": True,
            "conflicts": [],
            "alternative_slots": []
        }


async def send_agent_email(
    agent_email: str,
    agent_name: str,
    user_name: str,
    user_email: str,
    user_phone: str,
    property_address: str,
    requested_time: datetime,
    pre_approved: bool
) -> bool:
    """Send viewing request email to listing agent.
    
    Args:
        agent_email: Agent's email address
        agent_name: Agent's name
        user_name: Buyer's name
        user_email: Buyer's email
        user_phone: Buyer's phone
        property_address: Property address
        requested_time: Requested viewing time
        pre_approved: Whether buyer is pre-approved
        
    Returns:
        True if email sent successfully
        
    Raises:
        EmailAPIError: If sending fails
    """
    logger.info(f"Sending viewing request email to {agent_email}")
    
    # Initialize Email client
    email_client = EmailClient(sendgrid_api_key=settings.sendgrid_api_key)
    
    try:
        success = await email_client.send_viewing_request(
            to_email=agent_email,
            agent_name=agent_name,
            user_name=user_name,
            user_email=user_email,
            user_phone=user_phone,
            property_address=property_address,
            requested_time=requested_time,
            pre_approved=pre_approved
        )
        return success
    except EmailAPIError as e:
        logger.error(f"Failed to send email: {e}")
        raise


async def create_pending_calendar_event(
    user: User,
    property_address: str,
    requested_time: datetime,
    agent_name: Optional[str],
    agent_email: Optional[str],
    agent_phone: Optional[str],
    duration_minutes: int = 60
) -> Optional[str]:
    """Create a pending calendar event.
    
    Args:
        user: User object with calendar token
        property_address: Property address
        requested_time: Viewing time
        agent_name: Agent's name
        agent_email: Agent's email
        agent_phone: Agent's phone
        duration_minutes: Duration of viewing
        
    Returns:
        Calendar event ID or None if calendar not integrated
        
    Raises:
        CalendarAPIError: If event creation fails
    """
    logger.info(f"Creating pending calendar event for user {user.id}")
    
    # Check if user has calendar integration
    if not user.google_calendar_token:
        logger.warning(f"User {user.id} has no calendar integration")
        return None
    
    # Initialize Calendar client
    calendar_client = CalendarClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret
    )
    
    # Build event description
    description_parts = [
        f"Property Viewing - PENDING CONFIRMATION",
        f"",
        f"Property: {property_address}",
        f""
    ]
    
    if agent_name:
        description_parts.append(f"Agent: {agent_name}")
    if agent_email:
        description_parts.append(f"Email: {agent_email}")
    if agent_phone:
        description_parts.append(f"Phone: {agent_phone}")
    
    description_parts.append("")
    description_parts.append("This viewing is pending agent confirmation.")
    
    description = "\n".join(description_parts)
    
    # Calculate end time
    end_time = requested_time + timedelta(minutes=duration_minutes)
    
    try:
        result = await calendar_client.create_event(
            access_token=user.google_calendar_token,
            summary=f"Viewing: {property_address} (PENDING)",
            start_time=requested_time,
            end_time=end_time,
            description=description,
            location=property_address,
            status="tentative"
        )
        
        return result["event_id"]
    except CalendarAPIError as e:
        logger.error(f"Failed to create calendar event: {e}")
        # Don't fail the request if calendar event creation fails
        return None


@router.post("/schedule", response_model=ScheduleResponse)
@limiter.limit("10/minute")
async def schedule_viewing(
    request: ScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Schedule a property viewing appointment.
    
    This endpoint:
    1. Extracts listing agent contact information
    2. Checks user's calendar for conflicts
    3. Sends viewing request email to agent
    4. Creates pending calendar event
    5. Stores viewing request in database
    
    Args:
        request: Viewing request parameters
        db: Database session
        
    Returns:
        ScheduleResponse with viewing details and status
        
    Raises:
        HTTPException: If scheduling fails
    """
    logger.info(f"Viewing schedule request: property_id={request.property_id}, user_id={request.user_id}")
    
    # Update user session timestamp
    update_user_session(request.user_id, db)
    
    try:
        # Parse requested time
        requested_time = datetime.fromisoformat(request.requested_time.replace('Z', '+00:00'))
        
        # Get user from database
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Step 1: Extract agent contact information
        try:
            agent_info = await extract_agent_contact(request.listing_url)
        except ApifyAPIError as e:
            logger.error(f"Agent extraction failed: {e}")
            # Continue without agent info
            agent_info = {
                "agent_name": None,
                "agent_email": None,
                "agent_phone": None,
                "found": False
            }
        
        if not agent_info["found"]:
            logger.warning("Agent contact info not found")
            return ScheduleResponse(
                status="error",
                message="Could not find agent contact information. Please contact the listing office directly.",
                agent_name=agent_info.get("agent_name"),
                agent_email=agent_info.get("agent_email"),
                agent_phone=agent_info.get("agent_phone")
            )
        
        # Step 2: Check calendar availability
        try:
            availability = await check_calendar_availability(user, requested_time)
        except Exception as e:
            logger.error(f"Calendar check failed: {e}")
            # Continue without calendar check
            availability = {
                "is_available": True,
                "conflicts": [],
                "alternative_slots": []
            }
        
        # If there's a conflict, return alternative slots
        if not availability["is_available"]:
            logger.info(f"Calendar conflict found for user {request.user_id}")
            
            alternative_slots = [
                AlternativeSlot(start=slot["start"], end=slot["end"])
                for slot in availability.get("alternative_slots", [])
            ]
            
            conflict_messages = []
            for conflict in availability.get("conflicts", []):
                conflict_messages.append(conflict.get("summary", "Busy"))
            
            message = f"You have a conflict at the requested time: {', '.join(conflict_messages)}. "
            if alternative_slots:
                message += "Here are some alternative times."
            
            return ScheduleResponse(
                status="conflict",
                message=message,
                agent_name=agent_info.get("agent_name"),
                agent_email=agent_info.get("agent_email"),
                agent_phone=agent_info.get("agent_phone"),
                alternative_slots=alternative_slots
            )
        
        # Step 3: Send email to listing agent
        if agent_info.get("agent_email"):
            try:
                await send_agent_email(
                    agent_email=agent_info["agent_email"],
                    agent_name=agent_info.get("agent_name", "Agent"),
                    user_name=request.user_name,
                    user_email=request.user_email,
                    user_phone=request.user_phone,
                    property_address=request.property_address,
                    requested_time=requested_time,
                    pre_approved=user.pre_approved
                )
                logger.info("Viewing request email sent successfully")
            except EmailAPIError as e:
                logger.error(f"Failed to send email: {e}")
                # Continue even if email fails
        else:
            logger.warning("No agent email available, skipping email send")
        
        # Step 4: Create pending calendar event
        calendar_event_id = None
        try:
            calendar_event_id = await create_pending_calendar_event(
                user=user,
                property_address=request.property_address,
                requested_time=requested_time,
                agent_name=agent_info.get("agent_name"),
                agent_email=agent_info.get("agent_email"),
                agent_phone=agent_info.get("agent_phone")
            )
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            # Continue even if calendar event creation fails
        
        # Step 5: Store viewing request in database
        try:
            viewing = Viewing(
                user_id=request.user_id,
                property_id=request.property_id,
                address=request.property_address,
                listing_url=request.listing_url,
                requested_time=request.requested_time,
                agent_name=agent_info.get("agent_name"),
                agent_email=agent_info.get("agent_email"),
                agent_phone=agent_info.get("agent_phone"),
                status="requested",
                calendar_event_id=calendar_event_id
            )
            db.add(viewing)
            db.commit()
            db.refresh(viewing)
            
            logger.info(f"Saved viewing request {viewing.id} for user {request.user_id}")
            
            return ScheduleResponse(
                status="requested",
                message="Viewing request sent to agent. Pending calendar event created.",
                calendar_event_id=calendar_event_id,
                viewing_id=viewing.id,
                agent_name=agent_info.get("agent_name"),
                agent_email=agent_info.get("agent_email"),
                agent_phone=agent_info.get("agent_phone")
            )
            
        except Exception as e:
            logger.error(f"Failed to save viewing: {e}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to save viewing request"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in schedule endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while scheduling the viewing"
        )
