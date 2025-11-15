"""Risk analysis tool endpoint."""
import logging
import asyncio
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.settings import settings
from services.rentcast_client import RentCastClient, RentCastAPIError
from services.fema_client import FEMAClient, FEMAAPIError
from services.crime_client import CrimeClient, CrimeAPIError
from services.cache_client import cache_client
from models.database import get_db
from models.risk_analysis import RiskAnalysis
from api.middleware import update_user_session
from api.monitoring import set_user_context, set_tool_context, add_breadcrumb
from api.rate_limit import limiter
from api.metrics import metrics

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper Functions
def parse_address(address: str) -> Dict[str, Optional[str]]:
    """Parse address string into components.
    
    Args:
        address: Full address string
        
    Returns:
        Dictionary with city, state, zip_code
    """
    parts = [p.strip() for p in address.split(',')]
    
    result = {
        "street": None,
        "city": None,
        "state": None,
        "zip_code": None
    }
    
    if len(parts) >= 1:
        result["street"] = parts[0]
    
    if len(parts) >= 2:
        result["city"] = parts[1]
    
    if len(parts) >= 3:
        # Last part might be "STATE ZIP"
        last_part = parts[2].strip()
        state_zip = last_part.split()
        if len(state_zip) >= 1:
            result["state"] = state_zip[0]
        if len(state_zip) >= 2:
            result["zip_code"] = state_zip[1]
    
    return result


async def fetch_rentcast_data(
    rentcast_client: RentCastClient,
    address: str,
    city: Optional[str],
    state: Optional[str],
    zip_code: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Fetch property value and tax data from RentCast.
    
    Args:
        rentcast_client: RentCast API client
        address: Street address
        city: City name
        state: State abbreviation
        zip_code: ZIP code
        
    Returns:
        Dictionary with estimated_value and tax_assessment, or None on failure
    """
    try:
        if not city or not state:
            logger.warning("Missing city or state for RentCast lookup")
            return None
        
        data = await rentcast_client.get_property_value(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code
        )
        
        logger.info(f"RentCast data: estimated_value=${data.get('estimated_value', 0):,}, tax_assessment=${data.get('tax_assessment', 0):,}")
        return data
        
    except RentCastAPIError as e:
        logger.error(f"RentCast API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching RentCast data: {e}")
        return None


async def fetch_fema_data(
    fema_client: FEMAClient,
    latitude: Optional[float],
    longitude: Optional[float]
) -> Optional[Dict[str, Any]]:
    """Fetch flood zone data from FEMA.
    
    Args:
        fema_client: FEMA API client
        latitude: Property latitude
        longitude: Property longitude
        
    Returns:
        Dictionary with flood zone information, or None on failure
    """
    try:
        if latitude is None or longitude is None:
            logger.warning("Missing coordinates for FEMA lookup")
            return None
        
        data = await fema_client.get_flood_zone(
            latitude=latitude,
            longitude=longitude
        )
        
        logger.info(f"FEMA data: flood_zone={data.get('flood_zone')}, is_high_risk={data.get('is_high_risk')}")
        return data
        
    except FEMAAPIError as e:
        logger.error(f"FEMA API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching FEMA data: {e}")
        return None


async def fetch_crime_data(
    crime_client: CrimeClient,
    latitude: Optional[float],
    longitude: Optional[float]
) -> Optional[Dict[str, Any]]:
    """Fetch crime statistics from CrimeoMeter.
    
    Args:
        crime_client: Crime API client
        latitude: Property latitude
        longitude: Property longitude
        
    Returns:
        Dictionary with crime score and details, or None on failure
    """
    try:
        if latitude is None or longitude is None:
            logger.warning("Missing coordinates for crime lookup")
            return None
        
        data = await crime_client.get_crime_score(
            latitude=latitude,
            longitude=longitude
        )
        
        logger.info(f"Crime data: score={data.get('crime_score')}, level={data.get('crime_level')}")
        return data
        
    except CrimeAPIError as e:
        logger.error(f"Crime API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching crime data: {e}")
        return None


async def fetch_all_risk_data(
    request: "RiskRequest"
) -> Dict[str, Any]:
    """Fetch data from all external APIs in parallel with timeout.
    
    Args:
        request: Risk analysis request
        
    Returns:
        Dictionary with data from all sources and success flags
    """
    # Initialize clients
    rentcast_client = RentCastClient(api_key=settings.rentcast_api_key)
    fema_client = FEMAClient(redis_client=cache_client.client if cache_client and cache_client.client else None)
    crime_client = CrimeClient(api_key=settings.crimeometer_api_key)
    
    # Parse address if needed
    if not request.city or not request.state:
        parsed = parse_address(request.address)
        city = request.city or parsed["city"]
        state = request.state or parsed["state"]
        zip_code = request.zip_code or parsed["zip_code"]
        street = parsed["street"]
    else:
        city = request.city
        state = request.state
        zip_code = request.zip_code
        street = request.address.split(',')[0] if ',' in request.address else request.address
    
    # Fetch data in parallel with 5-second timeout
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                fetch_rentcast_data(rentcast_client, street, city, state, zip_code),
                fetch_fema_data(fema_client, request.latitude, request.longitude),
                fetch_crime_data(crime_client, request.latitude, request.longitude),
                return_exceptions=True
            ),
            timeout=5.0
        )
        
        rentcast_data, fema_data, crime_data = results
        
        # Handle exceptions in results
        if isinstance(rentcast_data, Exception):
            logger.error(f"RentCast fetch failed: {rentcast_data}")
            rentcast_data = None
        
        if isinstance(fema_data, Exception):
            logger.error(f"FEMA fetch failed: {fema_data}")
            fema_data = None
        
        if isinstance(crime_data, Exception):
            logger.error(f"Crime fetch failed: {crime_data}")
            crime_data = None
        
    except asyncio.TimeoutError:
        logger.error("Timeout fetching risk data (5 seconds exceeded)")
        rentcast_data = None
        fema_data = None
        crime_data = None
    
    return {
        "rentcast": rentcast_data,
        "fema": fema_data,
        "crime": crime_data,
        "data_sources": {
            "rentcast": rentcast_data is not None,
            "fema": fema_data is not None,
            "crime": crime_data is not None
        }
    }


def calculate_risk_flags(
    list_price: int,
    rentcast_data: Optional[Dict[str, Any]],
    fema_data: Optional[Dict[str, Any]],
    crime_data: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Calculate risk flags based on property data.
    
    Args:
        list_price: Property listing price
        rentcast_data: RentCast property value data
        fema_data: FEMA flood zone data
        crime_data: Crime statistics data
        
    Returns:
        List of risk flag dictionaries
    """
    flags = []
    
    # 1. Overpricing Detection
    if rentcast_data:
        estimated_value = rentcast_data.get("estimated_value", 0)
        if estimated_value > 0:
            # Check if list_price > estimated_value * 1.1 (10% overpriced)
            threshold = estimated_value * 1.1
            if list_price > threshold:
                difference_percent = int(((list_price - estimated_value) / estimated_value) * 100)
                flags.append({
                    "severity": "high",
                    "category": "pricing",
                    "message": f"Property is overpriced by {difference_percent}% compared to estimated value",
                    "details": {
                        "list_price": list_price,
                        "estimated_value": estimated_value,
                        "difference_percent": difference_percent
                    }
                })
                logger.info(f"Overpricing flag: {difference_percent}% above estimated value")
    
    # 2. Flood Risk Detection
    if fema_data:
        flood_zone = fema_data.get("flood_zone", "").upper()
        is_high_risk = fema_data.get("is_high_risk", False)
        
        # Check if flood_zone in ["AE", "VE", "A"]
        if flood_zone in ["AE", "VE", "A"] or is_high_risk:
            flags.append({
                "severity": "high",
                "category": "flood",
                "message": f"Flood insurance required - property is in high-risk zone {flood_zone}",
                "details": {
                    "flood_zone": flood_zone,
                    "description": fema_data.get("description", ""),
                    "requires_insurance": True
                }
            })
            logger.info(f"Flood risk flag: zone {flood_zone}")
    
    # 3. Tax Gap Detection
    if rentcast_data:
        tax_assessment = rentcast_data.get("tax_assessment", 0)
        if tax_assessment > 0:
            # Check if tax_assessment < list_price * 0.6 (60% threshold)
            threshold = list_price * 0.6
            if tax_assessment < threshold:
                gap_percent = int(((list_price - tax_assessment) / list_price) * 100)
                flags.append({
                    "severity": "medium",
                    "category": "tax",
                    "message": f"Tax bill may increase after sale - current assessment is {gap_percent}% below list price",
                    "details": {
                        "list_price": list_price,
                        "tax_assessment": tax_assessment,
                        "gap_percent": gap_percent
                    }
                })
                logger.info(f"Tax gap flag: assessment {gap_percent}% below list price")
    
    # 4. Crime Risk Detection
    if crime_data:
        crime_score = crime_data.get("crime_score", 0)
        # Check if crime_score > 70
        if crime_score > 70:
            crime_level = crime_data.get("crime_level", "high")
            incidents_count = crime_data.get("incidents_count", 0)
            flags.append({
                "severity": "medium",
                "category": "crime",
                "message": f"Above-average crime rate in area - score {crime_score}/100",
                "details": {
                    "crime_score": crime_score,
                    "crime_level": crime_level,
                    "incidents_count": incidents_count
                }
            })
            logger.info(f"Crime risk flag: score {crime_score}/100")
    
    return flags


def sort_flags_by_severity(flags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort risk flags by severity (high first, then medium, then low).
    
    Args:
        flags: List of risk flag dictionaries
        
    Returns:
        Sorted list of risk flags
    """
    severity_order = {"high": 0, "medium": 1, "low": 2}
    
    return sorted(
        flags,
        key=lambda x: severity_order.get(x.get("severity", "low"), 2)
    )


def calculate_overall_risk(flags: List[Dict[str, Any]]) -> str:
    """Calculate overall risk level based on flag count and severity.
    
    Args:
        flags: List of risk flag dictionaries
        
    Returns:
        Overall risk level: "high", "medium", or "low"
    """
    if not flags:
        return "low"
    
    # Count flags by severity
    high_count = sum(1 for f in flags if f.get("severity") == "high")
    medium_count = sum(1 for f in flags if f.get("severity") == "medium")
    
    # Determine overall risk
    if high_count >= 2:
        # 2+ high severity flags = high overall risk
        return "high"
    elif high_count >= 1:
        # 1 high severity flag = high overall risk
        return "high"
    elif medium_count >= 2:
        # 2+ medium severity flags = medium overall risk
        return "medium"
    elif medium_count >= 1:
        # 1 medium severity flag = medium overall risk
        return "medium"
    else:
        # Only low severity flags or no flags
        return "low"


def format_flags_for_voice(flags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format risk flags with conversational messages for voice presentation.
    
    Args:
        flags: List of risk flag dictionaries
        
    Returns:
        List of flags with enhanced voice-friendly messages
    """
    # Messages are already conversational from calculate_risk_flags
    # Just ensure they're sorted by severity
    return sort_flags_by_severity(flags)


# Pydantic Models
class RiskRequest(BaseModel):
    """Request model for risk analysis."""
    
    property_id: str = Field(..., description="Unique property identifier")
    address: str = Field(..., description="Full property address", min_length=1)
    list_price: int = Field(..., description="Property listing price", gt=0)
    user_id: str = Field(..., description="User identifier")
    
    # Optional fields for better analysis
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State abbreviation")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    latitude: Optional[float] = Field(None, description="Property latitude")
    longitude: Optional[float] = Field(None, description="Property longitude")
    
    class Config:
        json_schema_extra = {
            "example": {
                "property_id": "prop_123",
                "address": "123 Main St, Baltimore, MD 21201",
                "list_price": 385000,
                "user_id": "user_123",
                "city": "Baltimore",
                "state": "MD",
                "zip_code": "21201",
                "latitude": 39.2904,
                "longitude": -76.6122
            }
        }


class RiskFlag(BaseModel):
    """Model for a single risk flag."""
    
    severity: str = Field(..., description="Risk severity: high, medium, or low")
    category: str = Field(..., description="Risk category: pricing, flood, tax, crime")
    message: str = Field(..., description="Human-readable risk description")
    details: Optional[dict] = Field(None, description="Additional details about the risk")
    
    class Config:
        json_schema_extra = {
            "example": {
                "severity": "high",
                "category": "pricing",
                "message": "Property is overpriced by 12% compared to estimated value",
                "details": {
                    "list_price": 385000,
                    "estimated_value": 343750,
                    "difference_percent": 12
                }
            }
        }


class RiskResponse(BaseModel):
    """Response model for risk analysis."""
    
    flags: List[RiskFlag] = Field(default_factory=list, description="List of identified risk flags")
    overall_risk: str = Field(..., description="Overall risk level: high, medium, or low")
    data_sources: dict = Field(default_factory=dict, description="Which data sources were successfully queried")
    
    class Config:
        json_schema_extra = {
            "example": {
                "flags": [
                    {
                        "severity": "high",
                        "category": "pricing",
                        "message": "Property is overpriced by 12% compared to estimated value",
                        "details": {"difference_percent": 12}
                    },
                    {
                        "severity": "high",
                        "category": "flood",
                        "message": "Flood insurance required - property is in high-risk zone AE",
                        "details": {"flood_zone": "AE"}
                    }
                ],
                "overall_risk": "high",
                "data_sources": {
                    "rentcast": True,
                    "fema": True,
                    "crime": False
                }
            }
        }


@router.post("/analyze-risk", response_model=RiskResponse)
@limiter.limit("10/minute")
async def analyze_risk(
    request: RiskRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze property for potential risk factors.
    
    This endpoint performs parallel analysis of property data from multiple sources
    to identify red flags including overpricing, flood risk, tax gaps, and crime concerns.
    
    Args:
        request: Risk analysis parameters including property details
        db: Database session
        
    Returns:
        RiskResponse with identified risk flags and overall risk level
        
    Raises:
        HTTPException: If the analysis fails or required services are unavailable
    """
    logger.info(f"Risk analysis request: property_id={request.property_id}, address={request.address}, user_id={request.user_id}")
    
    # Track active user
    metrics.track_active_user(request.user_id)
    
    # Set Sentry context for error tracking
    set_user_context(request.user_id)
    set_tool_context(
        "analyze_risk",
        property_id=request.property_id,
        address=request.address,
        list_price=request.list_price
    )
    add_breadcrumb(
        message="Risk analysis initiated",
        category="tool",
        data={"property_id": request.property_id, "address": request.address}
    )
    
    # Update user session timestamp
    update_user_session(request.user_id, db)
    
    # Track execution time
    start_time = time.time()
    
    try:
        # Generate cache key using property_id
        cache_key = f"risk:{request.property_id}"
        
        # Check cache first (24-hour TTL)
        cached_result = cache_client.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached risk analysis for property {request.property_id}")
            metrics.track_cache_hit(cache_key)
            
            # Track execution time
            duration_ms = (time.time() - start_time) * 1000
            metrics.track_tool_execution("analyze_risk", duration_ms, success=True)
            
            return RiskResponse(
                flags=[RiskFlag(**flag) for flag in cached_result['flags']],
                overall_risk=cached_result['overall_risk'],
                data_sources=cached_result.get('data_sources', {})
            )
        
        # Cache miss
        metrics.track_cache_miss(cache_key)
        logger.info(f"Cache miss for property {request.property_id}, performing fresh analysis")
        # Fetch data from all sources in parallel
        risk_data = await fetch_all_risk_data(request)
        
        # Extract data
        rentcast_data = risk_data.get("rentcast")
        fema_data = risk_data.get("fema")
        crime_data = risk_data.get("crime")
        data_sources = risk_data.get("data_sources", {})
        
        # Log data source availability for graceful degradation
        missing_sources = [k for k, v in data_sources.items() if not v]
        if missing_sources:
            logger.warning(f"Risk analysis proceeding with missing data sources: {', '.join(missing_sources)}")
        
        # Calculate risk flags (gracefully handles missing data)
        flags_data = calculate_risk_flags(
            list_price=request.list_price,
            rentcast_data=rentcast_data,
            fema_data=fema_data,
            crime_data=crime_data
        )
        
        # Add informational flag if critical data is missing
        if not rentcast_data:
            flags_data.append({
                "severity": "low",
                "category": "data",
                "message": "Property valuation data temporarily unavailable - some risk checks could not be performed",
                "details": {"missing_source": "rentcast"}
            })
        
        # Format flags for voice presentation (sorts by severity)
        formatted_flags = format_flags_for_voice(flags_data)
        
        # Calculate overall risk level
        overall_risk = calculate_overall_risk(formatted_flags)
        
        logger.info(f"Risk analysis complete: {len(formatted_flags)} flags, overall risk: {overall_risk}, data sources: {data_sources}")
        
        # Convert to RiskFlag models
        flags = [RiskFlag(**flag) for flag in formatted_flags]
        
        # Prepare response data for caching
        response_data = {
            "flags": formatted_flags,
            "overall_risk": overall_risk,
            "data_sources": data_sources
        }
        
        # Cache results with 24-hour TTL (86400 seconds)
        cache_client.set(cache_key, response_data, ttl=86400)
        logger.info(f"Cached risk analysis for property {request.property_id}")
        
        # Store risk analysis in database
        try:
            risk_analysis = RiskAnalysis(
                user_id=request.user_id,
                property_id=request.property_id,
                address=request.address,
                list_price=request.list_price,
                flags=formatted_flags,
                overall_risk=overall_risk,
                estimated_value=rentcast_data.get("estimated_value") if rentcast_data else None,
                tax_assessment=rentcast_data.get("tax_assessment") if rentcast_data else None,
                flood_zone=fema_data.get("flood_zone") if fema_data else None,
                crime_score=crime_data.get("crime_score") if crime_data else None,
                data_sources=data_sources
            )
            db.add(risk_analysis)
            db.commit()
            logger.info(f"Saved risk analysis for property {request.property_id}, user {request.user_id}")
        except Exception as e:
            logger.error(f"Failed to save risk analysis: {e}")
            db.rollback()
            # Don't fail the request if database save fails
        
        # Track execution time
        duration_ms = (time.time() - start_time) * 1000
        metrics.track_tool_execution("analyze_risk", duration_ms, success=True)
        
        return RiskResponse(
            flags=flags,
            overall_risk=overall_risk,
            data_sources=data_sources
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in risk analysis endpoint: {e}", exc_info=True)
        
        # Track execution time and error
        duration_ms = (time.time() - start_time) * 1000
        metrics.track_tool_execution("analyze_risk", duration_ms, success=False)
        metrics.track_error("risk_analysis_error", str(e), {"property_id": request.property_id})
        
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during risk analysis"
        )
