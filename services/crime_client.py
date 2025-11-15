"""CrimeoMeter API client for crime statistics."""
import httpx
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class CrimeAPIError(Exception):
    """Exception raised for Crime API errors."""
    pass


class CrimeClient:
    """Client for interacting with the CrimeoMeter API."""
    
    BASE_URL = "https://api.crimeometer.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Crime client.
        
        Args:
            api_key: CrimeoMeter API key for authentication (optional for basic usage)
        """
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["x-api-key"] = api_key
    
    async def get_crime_score(
        self,
        latitude: float,
        longitude: float,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """Get crime score for a location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with crime score and details:
            {
                "crime_score": int (0-100, higher is worse),
                "crime_level": str ("low", "medium", "high"),
                "incidents_count": int,
                "details": dict
            }
            
        Raises:
            CrimeAPIError: If the API request fails
        """
        logger.info(f"Querying crime data for ({latitude}, {longitude})")
        
        url = f"{self.BASE_URL}/incidents/stats"
        
        params = {
            "lat": latitude,
            "lon": longitude,
            "distance": "1mi",  # 1 mile radius
            "datetime_ini": None,  # Last 30 days by default
            "datetime_end": None
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_crime_data(data)
                elif response.status_code == 401:
                    raise CrimeAPIError("Invalid API key")
                elif response.status_code == 429:
                    raise CrimeAPIError("Rate limit exceeded")
                else:
                    error_msg = f"Crime API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('message', '')}"
                    except:
                        pass
                    raise CrimeAPIError(error_msg)
                    
        except httpx.TimeoutException:
            logger.error(f"Crime API timeout for ({latitude}, {longitude})")
            raise CrimeAPIError("Request timeout")
        except httpx.NetworkError as e:
            logger.error(f"Crime API network error: {e}")
            raise CrimeAPIError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, CrimeAPIError):
                raise
            logger.error(f"Unexpected error calling Crime API: {e}")
            raise CrimeAPIError(f"Unexpected error: {str(e)}")
    
    def _parse_crime_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse crime API response into structured data.
        
        Args:
            data: Crime API response JSON
            
        Returns:
            Dictionary with normalized crime score and details
        """
        try:
            # Extract total incidents
            total_incidents = data.get("total_incidents", 0)
            
            # Calculate crime score (0-100 scale)
            # Normalize based on typical incident counts
            # 0-10 incidents = low (0-30)
            # 10-50 incidents = medium (30-70)
            # 50+ incidents = high (70-100)
            if total_incidents <= 10:
                crime_score = min(30, total_incidents * 3)
            elif total_incidents <= 50:
                crime_score = 30 + ((total_incidents - 10) * 1.0)
            else:
                crime_score = min(100, 70 + ((total_incidents - 50) * 0.6))
            
            crime_score = int(crime_score)
            
            # Determine crime level
            if crime_score < 40:
                crime_level = "low"
            elif crime_score < 70:
                crime_level = "medium"
            else:
                crime_level = "high"
            
            # Extract incident types
            incident_types = data.get("incident_types", {})
            
            result = {
                "crime_score": crime_score,
                "crime_level": crime_level,
                "incidents_count": total_incidents,
                "details": {
                    "incident_types": incident_types,
                    "distance_radius": "1 mile"
                }
            }
            
            logger.info(f"Crime score: {crime_score} ({crime_level}), incidents: {total_incidents}")
            return result
            
        except Exception as e:
            logger.warning(f"Error parsing crime data: {e}")
            # Return safe defaults
            return {
                "crime_score": 50,
                "crime_level": "unknown",
                "incidents_count": 0,
                "details": {}
            }
