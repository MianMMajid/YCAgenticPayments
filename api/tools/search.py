"""Property search tool endpoint."""
import logging
import hashlib
import json
import uuid
import time
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
import openai

from config.settings import settings
from services.rentcast_client import RentCastClient, RentCastAPIError
from services.cache_client import cache_client
from models.database import get_db
from models.search_history import SearchHistory
from models.user import User
from api.middleware import update_user_session
from api.monitoring import set_user_context, set_tool_context, add_breadcrumb
from api.rate_limit import limiter
from api.metrics import metrics, track_execution_time

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper Functions
def generate_cache_key(
    user_id: str,
    location: str,
    max_price: Optional[int],
    min_price: Optional[int],
    min_beds: Optional[int],
    min_baths: Optional[int],
    property_type: Optional[str]
) -> str:
    """
    Generate a cache key for search results.
    
    Args:
        user_id: User identifier
        location: Location string
        max_price: Maximum price
        min_price: Minimum price
        min_beds: Minimum bedrooms
        min_baths: Minimum bathrooms
        property_type: Property type
        
    Returns:
        Cache key string
    """
    # Create a hash of the search parameters
    params = {
        "location": location.lower(),
        "max_price": max_price,
        "min_price": min_price,
        "min_beds": min_beds,
        "min_baths": min_baths,
        "property_type": property_type
    }
    
    # Create hash from JSON representation
    params_json = json.dumps(params, sort_keys=True)
    params_hash = hashlib.md5(params_json.encode()).hexdigest()
    
    return f"search:{user_id}:{params_hash}"


def parse_location(location: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse location string into city and state components.
    
    Args:
        location: Location string (e.g., "Baltimore, MD" or "Baltimore")
        
    Returns:
        Tuple of (city, state) where state may be None
    """
    parts = [p.strip() for p in location.split(',')]
    
    if len(parts) >= 2:
        city = parts[0]
        state = parts[1]
        return city, state
    elif len(parts) == 1:
        # Assume it's just a city
        return parts[0], None
    
    return None, None


def calculate_relevance_score(
    listing: dict,
    target_price: Optional[int],
    target_beds: Optional[int],
    target_baths: Optional[int]
) -> float:
    """
    Calculate relevance score for a listing based on how well it matches criteria.
    
    Args:
        listing: Property listing dictionary
        target_price: Target price (if specified)
        target_beds: Target number of bedrooms (if specified)
        target_baths: Target number of bathrooms (if specified)
        
    Returns:
        Relevance score (lower is better)
    """
    score = 0.0
    
    # Price proximity (normalized by target price)
    if target_price and listing.get('price'):
        price_diff = abs(listing['price'] - target_price)
        score += (price_diff / target_price) * 100
    
    # Bedroom match (penalize if doesn't meet minimum)
    if target_beds and listing.get('bedrooms'):
        if listing['bedrooms'] < target_beds:
            score += 50  # Heavy penalty for not meeting minimum
        else:
            # Small penalty for having more than needed
            score += abs(listing['bedrooms'] - target_beds) * 5
    
    # Bathroom match (penalize if doesn't meet minimum)
    if target_baths and listing.get('bathrooms'):
        if listing['bathrooms'] < target_baths:
            score += 50  # Heavy penalty for not meeting minimum
        else:
            score += abs(listing['bathrooms'] - target_baths) * 5
    
    return score


def format_property_result(listing: dict) -> dict:
    """
    Format a RentCast listing into a PropertyResult dictionary.
    
    Args:
        listing: Raw listing data from RentCast API
        
    Returns:
        Formatted property dictionary
    """
    # Extract address components
    address_line = listing.get('addressLine1', listing.get('address', ''))
    city = listing.get('city', '')
    state = listing.get('state', '')
    zip_code = listing.get('zipCode', '')
    
    # Build full address
    full_address = address_line
    if city and state:
        full_address += f", {city}, {state}"
        if zip_code:
            full_address += f" {zip_code}"
    
    return {
        "address": full_address,
        "price": listing.get('price', 0),
        "beds": listing.get('bedrooms', 0),
        "baths": listing.get('bathrooms', 0),
        "sqft": listing.get('squareFootage') or listing.get('livingArea'),
        "summary": "",  # Will be populated by AI in next subtask
        "listing_url": listing.get('url') or listing.get('listingUrl'),
        "property_id": listing.get('id', listing.get('propertyId', str(uuid.uuid4())))
    }


async def generate_property_summary(property_data: dict, listing_data: dict) -> str:
    """
    Generate a one-sentence property summary using GPT-4o-mini.
    
    Args:
        property_data: Formatted property dictionary
        listing_data: Raw listing data from RentCast (for additional details)
        
    Returns:
        One-sentence summary optimized for voice readability
    """
    try:
        # Extract key features from listing data
        features = []
        
        # Property type
        prop_type = listing_data.get('propertyType', '')
        if prop_type:
            features.append(prop_type.lower())
        
        # Key amenities
        amenities = listing_data.get('amenities', [])
        if isinstance(amenities, list):
            features.extend(amenities[:3])  # Top 3 amenities
        
        # Description snippet
        description = listing_data.get('description', '')
        
        # Build prompt for GPT-4o-mini
        prompt = f"""Generate a single, concise sentence (max 15 words) describing this property for a voice assistant. Focus on the most appealing features.

Property: {property_data['beds']} bed, {property_data['baths']} bath, {property_data['sqft'] or 'N/A'} sqft
Type: {prop_type or 'home'}
Features: {', '.join(features[:5]) if features else 'N/A'}
Description: {description[:200] if description else 'N/A'}

Summary:"""

        # Initialize OpenAI client
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Call GPT-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a real estate assistant that creates brief, appealing property descriptions for voice interfaces. Keep summaries under 15 words."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Remove quotes if present
        summary = summary.strip('"').strip("'")
        
        logger.info(f"Generated summary: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        # Fallback to basic description
        return f"{property_data['beds']}-bed {prop_type or 'home'} with {property_data['baths']} baths"


async def search_rentcast_properties(
    city: Optional[str],
    state: Optional[str],
    max_price: Optional[int],
    min_price: Optional[int],
    min_beds: Optional[int],
    min_baths: Optional[int],
    property_type: Optional[str]
) -> tuple[List[dict], int]:
    """
    Search RentCast API for properties and return top 3 results.
    
    Args:
        city: City name
        state: State abbreviation
        max_price: Maximum price
        min_price: Minimum price
        min_beds: Minimum bedrooms
        min_baths: Minimum bathrooms
        property_type: Property type filter
        
    Returns:
        Tuple of (list of up to 3 formatted property dictionaries, total count)
        
    Raises:
        RentCastAPIError: If the API request fails
    """
    # Initialize RentCast client
    client = RentCastClient(api_key=settings.rentcast_api_key)
    
    # Search for listings
    listings = await client.search_listings(
        city=city,
        state=state,
        max_price=max_price,
        min_price=min_price,
        beds=min_beds,
        baths=min_baths,
        property_type=property_type,
        status="Active",
        limit=50  # Get more results for better sorting
    )
    
    if not listings:
        return [], 0
    
    # Calculate relevance scores and sort
    for listing in listings:
        listing['_relevance_score'] = calculate_relevance_score(
            listing,
            target_price=max_price,
            target_beds=min_beds,
            target_baths=min_baths
        )
    
    # Sort by relevance (lower score is better)
    sorted_listings = sorted(listings, key=lambda x: x.get('_relevance_score', float('inf')))
    
    # Take top 3 and format
    top_listings = sorted_listings[:3]
    formatted_results = []
    
    for listing in top_listings:
        property_data = format_property_result(listing)
        # Generate AI summary
        property_data['summary'] = await generate_property_summary(property_data, listing)
        formatted_results.append(property_data)
    
    logger.info(f"Returning {len(formatted_results)} properties from {len(listings)} total found")
    
    return formatted_results, len(listings)


# Pydantic Models
class SearchRequest(BaseModel):
    """Request model for property search."""
    
    location: str = Field(..., description="Location string (e.g., 'Baltimore, MD')", min_length=1)
    max_price: Optional[int] = Field(None, description="Maximum listing price", gt=0)
    min_price: Optional[int] = Field(None, description="Minimum listing price", gt=0)
    min_beds: Optional[int] = Field(None, description="Minimum number of bedrooms", ge=0)
    min_baths: Optional[int] = Field(None, description="Minimum number of bathrooms", ge=0)
    property_type: Optional[str] = Field(None, description="Property type (e.g., 'Single Family', 'Condo')")
    user_id: str = Field(..., description="User identifier")
    
    @validator('max_price')
    def validate_max_price(cls, v, values):
        """Ensure max_price is greater than min_price if both are provided."""
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v <= values['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "Baltimore, MD",
                "max_price": 400000,
                "min_beds": 3,
                "min_baths": 2,
                "user_id": "user_123"
            }
        }


class PropertyResult(BaseModel):
    """Model for a single property result."""
    
    address: str
    price: int
    beds: int
    baths: float
    sqft: Optional[int] = None
    summary: str
    listing_url: Optional[str] = None
    property_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "123 Main St, Baltimore, MD 21201",
                "price": 385000,
                "beds": 3,
                "baths": 2.5,
                "sqft": 1800,
                "summary": "Charming 3-bed colonial with updated kitchen and hardwood floors",
                "listing_url": "https://www.zillow.com/...",
                "property_id": "prop_123"
            }
        }


class SearchResponse(BaseModel):
    """Response model for property search."""
    
    properties: List[PropertyResult] = Field(default_factory=list, max_length=3)
    total_found: int = Field(..., description="Total number of properties found")
    cached: bool = Field(default=False, description="Whether results were served from cache")
    
    class Config:
        json_schema_extra = {
            "example": {
                "properties": [
                    {
                        "address": "123 Main St, Baltimore, MD 21201",
                        "price": 385000,
                        "beds": 3,
                        "baths": 2.5,
                        "sqft": 1800,
                        "summary": "Charming 3-bed colonial with updated kitchen",
                        "listing_url": "https://www.zillow.com/...",
                        "property_id": "prop_123"
                    }
                ],
                "total_found": 15,
                "cached": False
            }
        }


@router.post("/search", response_model=SearchResponse)
@limiter.limit("10/minute")
async def search_properties(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search for properties matching the specified criteria.
    
    This endpoint searches for active property listings using the RentCast API,
    generates AI summaries for voice readability, and caches results for 24 hours.
    
    Args:
        request: Search parameters including location, price range, and property attributes
        db: Database session
        
    Returns:
        SearchResponse with up to 3 property results
        
    Raises:
        HTTPException: If the search fails or required services are unavailable
    """
    logger.info(f"Property search request: location={request.location}, max_price={request.max_price}, user_id={request.user_id}")
    
    # Track active user
    metrics.track_active_user(request.user_id)
    
    # Set Sentry context for error tracking
    set_user_context(request.user_id)
    set_tool_context(
        "search_properties",
        location=request.location,
        max_price=request.max_price,
        min_beds=request.min_beds
    )
    add_breadcrumb(
        message="Property search initiated",
        category="tool",
        data={"location": request.location, "max_price": request.max_price}
    )
    
    # Update user session timestamp
    update_user_session(request.user_id, db)
    
    # Track execution time
    start_time = time.time()
    
    try:
        # Generate cache key
        cache_key = generate_cache_key(
            user_id=request.user_id,
            location=request.location,
            max_price=request.max_price,
            min_price=request.min_price,
            min_beds=request.min_beds,
            min_baths=request.min_baths,
            property_type=request.property_type
        )
        
        # Check cache first
        cached_result = cache_client.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached results for user {request.user_id}")
            metrics.track_cache_hit(cache_key)
            
            # Track execution time
            duration_ms = (time.time() - start_time) * 1000
            metrics.track_tool_execution("search_properties", duration_ms, success=True)
            
            return SearchResponse(
                properties=[PropertyResult(**prop) for prop in cached_result['properties']],
                total_found=cached_result['total_found'],
                cached=True
            )
        
        # Cache miss
        metrics.track_cache_miss(cache_key)
        
        # Parse location
        city, state = parse_location(request.location)
        
        if not city:
            raise HTTPException(
                status_code=400,
                detail="Invalid location format. Please provide city and state (e.g., 'Baltimore, MD')"
            )
        
        # Search RentCast API
        try:
            properties, total_found = await search_rentcast_properties(
                city=city,
                state=state,
                max_price=request.max_price,
                min_price=request.min_price,
                min_beds=request.min_beds,
                min_baths=request.min_baths,
                property_type=request.property_type
            )
        except RentCastAPIError as e:
            logger.error(f"RentCast API error: {e}")
            
            # Graceful degradation: Try to find cached results from similar searches
            # Look for cached results in the same location with similar price range
            fallback_cache_key = f"search:{request.user_id}:*"
            logger.info(f"Attempting to retrieve fallback cached results for location: {request.location}")
            
            # Try to get any cached results for this user in this location
            # This is a simplified fallback - in production, you'd want more sophisticated cache lookup
            try:
                # Check if we have any recent searches for this location
                location_cache_key = generate_cache_key(
                    user_id="fallback",  # Use a generic key for location-based cache
                    location=request.location,
                    max_price=None,
                    min_price=None,
                    min_beds=None,
                    min_baths=None,
                    property_type=None
                )
                fallback_result = cache_client.get(location_cache_key)
                
                if fallback_result:
                    logger.info(f"Returning fallback cached results for user {request.user_id}")
                    return SearchResponse(
                        properties=[PropertyResult(**prop) for prop in fallback_result['properties']],
                        total_found=fallback_result['total_found'],
                        cached=True
                    )
            except Exception as cache_error:
                logger.error(f"Failed to retrieve fallback cache: {cache_error}")
            
            # If no cached results available, return user-friendly error
            raise HTTPException(
                status_code=503,
                detail="Property search is temporarily unavailable. Please try again in a few minutes."
            )
        
        # Prepare response
        response_data = {
            "properties": [prop for prop in properties],
            "total_found": total_found
        }
        
        # Cache results (24-hour TTL)
        cache_client.set(cache_key, response_data, ttl=86400)
        
        # Store search history in database
        try:
            search_history = SearchHistory(
                user_id=request.user_id,
                query=None,  # Voice query not available in this context
                location=request.location,
                max_price=request.max_price,
                min_price=request.min_price,
                min_beds=request.min_beds,
                min_baths=request.min_baths,
                property_type=request.property_type,
                results=properties,
                total_found=total_found
            )
            db.add(search_history)
            db.commit()
            logger.info(f"Saved search history for user {request.user_id}")
        except Exception as e:
            logger.error(f"Failed to save search history: {e}")
            db.rollback()
            # Don't fail the request if history save fails
        
        # Track execution time
        duration_ms = (time.time() - start_time) * 1000
        metrics.track_tool_execution("search_properties", duration_ms, success=True)
        
        return SearchResponse(
            properties=[PropertyResult(**prop) for prop in properties],
            total_found=total_found,
            cached=False
        )
        
    except HTTPException:
        # Track execution time for failed requests
        duration_ms = (time.time() - start_time) * 1000
        metrics.track_tool_execution("search_properties", duration_ms, success=False)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search endpoint: {e}", exc_info=True)
        
        # Track execution time and error
        duration_ms = (time.time() - start_time) * 1000
        metrics.track_tool_execution("search_properties", duration_ms, success=False)
        metrics.track_error("search_error", str(e), {"user_id": request.user_id})
        
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during property search"
        )
