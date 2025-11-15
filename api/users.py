"""User session management endpoints."""
from datetime import datetime, timedelta
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import User
from models.search_history import SearchHistory
from models.viewing import Viewing
from models.offer import Offer

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic Models
class UserPreferences(BaseModel):
    """User preferences for property search."""
    preferred_locations: Optional[list[str]] = Field(None, description="List of preferred cities/states")
    max_budget: Optional[int] = Field(None, description="Maximum budget in dollars")
    min_beds: Optional[int] = Field(None, description="Minimum number of bedrooms")
    min_baths: Optional[int] = Field(None, description="Minimum number of bathrooms")
    property_types: Optional[list[str]] = Field(None, description="Preferred property types")


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    phone_number: str
    email: Optional[str] = None
    name: Optional[str] = None
    preferred_locations: list[str] = []
    max_budget: Optional[int] = None
    min_beds: Optional[int] = None
    min_baths: Optional[int] = None
    property_types: list[str] = []
    pre_approved: bool = False
    pre_approval_amount: Optional[int] = None
    last_active: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class SearchHistoryItem(BaseModel):
    """Search history item."""
    id: str
    location: str
    max_price: Optional[int] = None
    min_beds: Optional[int] = None
    results: list = []
    created_at: str
    
    class Config:
        from_attributes = True


class ViewingItem(BaseModel):
    """Viewing appointment item."""
    id: str
    property_id: str
    address: str
    requested_time: str
    status: str
    agent_name: Optional[str] = None
    agent_email: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class OfferItem(BaseModel):
    """Offer item."""
    id: str
    property_id: str
    address: str
    offer_price: int
    financing_type: str
    status: str
    envelope_id: Optional[str] = None
    created_at: str
    signed_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserHistoryResponse(BaseModel):
    """User activity history response."""
    searches: list[SearchHistoryItem] = []
    viewings: list[ViewingItem] = []
    offers: list[OfferItem] = []


def update_last_active(user: User, db: Session):
    """Update user's last_active timestamp."""
    user.last_active = datetime.utcnow().isoformat()
    db.commit()


@router.get("/users/{phone_number}", response_model=UserResponse)
async def get_or_create_user(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve or create a user by phone number.
    
    This endpoint implements user lookup and creation as specified in Requirement 7.1.
    If the user exists, it returns their profile and preferences.
    If the user doesn't exist, it creates a new user record.
    """
    try:
        # Try to find existing user
        user = db.query(User).filter(User.phone_number == phone_number).first()
        
        if user:
            # Update last_active timestamp
            update_last_active(user, db)
            logger.info(f"Retrieved existing user: {user.id}")
        else:
            # Create new user
            user = User(phone_number=phone_number)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {user.id}")
        
        return UserResponse(
            id=user.id,
            phone_number=user.phone_number,
            email=user.email,
            name=user.name,
            preferred_locations=user.preferred_locations or [],
            max_budget=user.max_budget,
            min_beds=user.min_beds,
            min_baths=user.min_baths,
            property_types=user.property_types or [],
            pre_approved=user.pre_approved,
            pre_approval_amount=user.pre_approval_amount,
            last_active=user.last_active,
            created_at=user.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in get_or_create_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve or create user: {str(e)}"
        )


@router.put("/users/{user_id}/preferences", response_model=UserResponse)
async def update_user_preferences(
    user_id: str,
    preferences: UserPreferences,
    db: Session = Depends(get_db)
):
    """
    Update user preferences.
    
    This endpoint implements user preferences storage as specified in Requirement 7.2.
    Updates preferred_locations, max_budget, min_beds, and other search preferences.
    """
    try:
        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )
        
        # Update preferences (only update fields that are provided)
        if preferences.preferred_locations is not None:
            user.preferred_locations = preferences.preferred_locations
        if preferences.max_budget is not None:
            user.max_budget = preferences.max_budget
        if preferences.min_beds is not None:
            user.min_beds = preferences.min_beds
        if preferences.min_baths is not None:
            user.min_baths = preferences.min_baths
        if preferences.property_types is not None:
            user.property_types = preferences.property_types
        
        # Update last_active timestamp
        update_last_active(user, db)
        
        db.refresh(user)
        logger.info(f"Updated preferences for user: {user_id}")
        
        return UserResponse(
            id=user.id,
            phone_number=user.phone_number,
            email=user.email,
            name=user.name,
            preferred_locations=user.preferred_locations or [],
            max_budget=user.max_budget,
            min_beds=user.min_beds,
            min_baths=user.min_baths,
            property_types=user.property_types or [],
            pre_approved=user.pre_approved,
            pre_approval_amount=user.pre_approval_amount,
            last_active=user.last_active,
            created_at=user.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user preferences: {str(e)}"
        )


@router.get("/users/{user_id}/history", response_model=UserHistoryResponse)
async def get_user_history(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve user conversation history.
    
    This endpoint implements conversation history retrieval as specified in Requirement 7.4.
    Returns recent searches, viewings, and offers limited to the last 30 days of activity.
    """
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )
        
        # Update last_active timestamp
        update_last_active(user, db)
        
        # Calculate 30 days ago
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Retrieve search history from last 30 days
        searches = db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id,
            SearchHistory.created_at >= thirty_days_ago
        ).order_by(SearchHistory.created_at.desc()).all()
        
        # Retrieve viewings from last 30 days
        viewings = db.query(Viewing).filter(
            Viewing.user_id == user_id,
            Viewing.created_at >= thirty_days_ago
        ).order_by(Viewing.created_at.desc()).all()
        
        # Retrieve offers from last 30 days
        offers = db.query(Offer).filter(
            Offer.user_id == user_id,
            Offer.created_at >= thirty_days_ago
        ).order_by(Offer.created_at.desc()).all()
        
        logger.info(f"Retrieved history for user {user_id}: {len(searches)} searches, {len(viewings)} viewings, {len(offers)} offers")
        
        return UserHistoryResponse(
            searches=[
                SearchHistoryItem(
                    id=s.id,
                    location=s.location,
                    max_price=s.max_price,
                    min_beds=s.min_beds,
                    results=s.results or [],
                    created_at=s.created_at.isoformat()
                ) for s in searches
            ],
            viewings=[
                ViewingItem(
                    id=v.id,
                    property_id=v.property_id,
                    address=v.address,
                    requested_time=v.requested_time,
                    status=v.status,
                    agent_name=v.agent_name,
                    agent_email=v.agent_email,
                    created_at=v.created_at.isoformat()
                ) for v in viewings
            ],
            offers=[
                OfferItem(
                    id=o.id,
                    property_id=o.property_id,
                    address=o.address,
                    offer_price=o.offer_price,
                    financing_type=o.financing_type,
                    status=o.status,
                    envelope_id=o.envelope_id,
                    created_at=o.created_at.isoformat(),
                    signed_at=o.signed_at
                ) for o in offers
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user history: {str(e)}"
        )
