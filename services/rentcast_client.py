"""RentCast API client for property listings and data."""
import httpx
import logging
import time
from typing import List, Dict, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class RentCastAPIError(Exception):
    """Exception raised for RentCast API errors."""
    pass


class RentCastClient:
    """Client for interacting with the RentCast API."""
    
    BASE_URL = "https://api.rentcast.io/v1"
    
    def __init__(self, api_key: str):
        """Initialize the RentCast client.
        
        Args:
            api_key: RentCast API key for authentication
        """
        if not api_key:
            raise ValueError("RentCast API key is required")
        
        self.api_key = api_key
        self.headers = {
            "X-Api-Key": api_key,
            "Accept": "application/json"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Make an HTTP request to the RentCast API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            timeout: Request timeout in seconds
            
        Returns:
            JSON response as dictionary
            
        Raises:
            RentCastAPIError: If the API request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        start_time = time.time()
        success = True
        status_code = None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    timeout=timeout
                )
                
                status_code = response.status_code
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    success = False
                    raise RentCastAPIError("Invalid API key")
                elif response.status_code == 429:
                    success = False
                    raise RentCastAPIError("Rate limit exceeded")
                else:
                    success = False
                    error_msg = f"RentCast API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('message', '')}"
                    except:
                        pass
                    raise RentCastAPIError(error_msg)
                    
        except httpx.TimeoutException:
            success = False
            logger.error(f"RentCast API timeout for {endpoint}")
            raise RentCastAPIError("Request timeout")
        except httpx.NetworkError as e:
            success = False
            logger.error(f"RentCast API network error: {e}")
            raise RentCastAPIError(f"Network error: {str(e)}")
        except Exception as e:
            success = False
            if isinstance(e, RentCastAPIError):
                raise
            logger.error(f"Unexpected error calling RentCast API: {e}")
            raise RentCastAPIError(f"Unexpected error: {str(e)}")
        finally:
            # Track API call metrics
            duration_ms = (time.time() - start_time) * 1000
            try:
                from api.metrics import metrics
                metrics.track_external_api_call(
                    "rentcast",
                    endpoint,
                    duration_ms,
                    success,
                    status_code
                )
            except ImportError:
                # Metrics module not available (e.g., during testing)
                pass

    
    async def search_listings(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        max_price: Optional[int] = None,
        min_price: Optional[int] = None,
        beds: Optional[int] = None,
        baths: Optional[int] = None,
        property_type: Optional[str] = None,
        status: str = "Active",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for property listings.
        
        Args:
            city: City name
            state: State abbreviation (e.g., "MD")
            zip_code: ZIP code
            max_price: Maximum listing price
            min_price: Minimum listing price
            beds: Minimum number of bedrooms
            baths: Minimum number of bathrooms
            property_type: Property type (e.g., "Single Family", "Condo")
            status: Listing status (default: "Active")
            limit: Maximum number of results
            
        Returns:
            List of property listings
            
        Raises:
            RentCastAPIError: If the API request fails
        """
        params = {
            "status": status,
            "limit": limit
        }
        
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        if zip_code:
            params["zipCode"] = zip_code
        if max_price:
            params["maxPrice"] = max_price
        if min_price:
            params["minPrice"] = min_price
        if beds:
            params["bedrooms"] = beds
        if baths:
            params["bathrooms"] = baths
        if property_type:
            params["propertyType"] = property_type
        
        logger.info(f"Searching listings with params: {params}")
        
        try:
            response = await self._make_request("GET", "/listings/sale", params=params)
            listings = response if isinstance(response, list) else response.get("data", [])
            logger.info(f"Found {len(listings)} listings")
            return listings
        except RentCastAPIError as e:
            logger.error(f"Failed to search listings: {e}")
            raise
    
    async def get_property_details(
        self,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed property information including estimated value and tax data.
        
        Args:
            address: Street address
            city: City name
            state: State abbreviation
            zip_code: ZIP code
            property_id: RentCast property ID (if known)
            
        Returns:
            Property details including estimated value and tax assessment
            
        Raises:
            RentCastAPIError: If the API request fails
        """
        params = {}
        
        if property_id:
            params["id"] = property_id
        else:
            if address:
                params["address"] = address
            if city:
                params["city"] = city
            if state:
                params["state"] = state
            if zip_code:
                params["zipCode"] = zip_code
        
        if not params:
            raise ValueError("Must provide either property_id or address components")
        
        logger.info(f"Fetching property details with params: {params}")
        
        try:
            response = await self._make_request("GET", "/properties", params=params)
            
            # RentCast may return a list or single object
            if isinstance(response, list):
                if not response:
                    raise RentCastAPIError("Property not found")
                property_data = response[0]
            else:
                property_data = response
            
            logger.info(f"Retrieved property details for {property_data.get('address')}")
            return property_data
            
        except RentCastAPIError as e:
            logger.error(f"Failed to get property details: {e}")
            raise
    
    async def get_property_value(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get estimated property value and tax assessment.
        
        Args:
            address: Street address
            city: City name
            state: State abbreviation
            zip_code: ZIP code (optional)
            
        Returns:
            Dictionary with estimated_value and tax_assessment
            
        Raises:
            RentCastAPIError: If the API request fails
        """
        params = {
            "address": address,
            "city": city,
            "state": state
        }
        
        if zip_code:
            params["zipCode"] = zip_code
        
        logger.info(f"Fetching property value for {address}, {city}, {state}")
        
        try:
            response = await self._make_request("GET", "/avm/value", params=params)
            
            result = {
                "estimated_value": response.get("price", 0),
                "tax_assessment": response.get("taxAssessment", 0),
                "confidence_score": response.get("confidence"),
                "price_range_low": response.get("priceRangeLow"),
                "price_range_high": response.get("priceRangeHigh")
            }
            
            logger.info(f"Estimated value: ${result['estimated_value']:,}")
            return result
            
        except RentCastAPIError as e:
            logger.error(f"Failed to get property value: {e}")
            raise
