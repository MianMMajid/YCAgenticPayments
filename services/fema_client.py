"""FEMA flood zone API client."""
import httpx
import logging
import hashlib
from typing import Dict, Optional, Any
from datetime import timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class FEMAAPIError(Exception):
    """Exception raised for FEMA API errors."""
    pass


class FEMAClient:
    """Client for interacting with the FEMA flood zone API."""
    
    BASE_URL = "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer"
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, cache_ttl: int = 86400):
        """Initialize the FEMA client.
        
        Args:
            redis_client: Optional Redis client for caching
            cache_ttl: Cache time-to-live in seconds (default: 24 hours)
        """
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
    
    def _get_cache_key(self, lat: float, lon: float) -> str:
        """Generate cache key for flood zone lookup.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Cache key string
        """
        coords = f"{lat:.6f},{lon:.6f}"
        hash_key = hashlib.md5(coords.encode()).hexdigest()
        return f"fema:flood_zone:{hash_key}"
    
    async def _get_from_cache(self, lat: float, lon: float) -> Optional[str]:
        """Get flood zone from cache.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Cached flood zone or None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(lat, lon)
            cached_value = await self.redis_client.get(cache_key)
            if cached_value:
                logger.info(f"Cache hit for flood zone at ({lat}, {lon})")
                return cached_value.decode() if isinstance(cached_value, bytes) else cached_value
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    async def _set_cache(self, lat: float, lon: float, flood_zone: str) -> None:
        """Store flood zone in cache.
        
        Args:
            lat: Latitude
            lon: Longitude
            flood_zone: Flood zone classification
        """
        if not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(lat, lon)
            await self.redis_client.setex(cache_key, self.cache_ttl, flood_zone)
            logger.info(f"Cached flood zone for ({lat}, {lon})")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    
    async def get_flood_zone(
        self,
        latitude: float,
        longitude: float,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Query flood zone classification by latitude and longitude.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with flood zone information:
            {
                "flood_zone": "AE" | "VE" | "A" | "X" | "Unknown",
                "description": "Flood zone description",
                "is_high_risk": bool
            }
            
        Raises:
            FEMAAPIError: If the API request fails
        """
        # Check cache first
        cached_zone = await self._get_from_cache(latitude, longitude)
        if cached_zone:
            return self._parse_flood_zone(cached_zone)
        
        # Query FEMA API
        logger.info(f"Querying FEMA flood zone for ({latitude}, {longitude})")
        
        # FEMA NFHL uses identify endpoint with geometry
        url = f"{self.BASE_URL}/identify"
        
        params = {
            "geometry": f"{longitude},{latitude}",
            "geometryType": "esriGeometryPoint",
            "layers": "all:28",  # Layer 28 is flood zones
            "mapExtent": f"{longitude-0.01},{latitude-0.01},{longitude+0.01},{latitude+0.01}",
            "imageDisplay": "400,400,96",
            "returnGeometry": "false",
            "f": "json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=timeout)
                
                if response.status_code != 200:
                    raise FEMAAPIError(f"FEMA API error: {response.status_code}")
                
                data = response.json()
                
                # Parse flood zone from response
                flood_zone = self._extract_flood_zone(data)
                
                # Cache the result
                await self._set_cache(latitude, longitude, flood_zone)
                
                return self._parse_flood_zone(flood_zone)
                
        except httpx.TimeoutException:
            logger.error(f"FEMA API timeout for ({latitude}, {longitude})")
            raise FEMAAPIError("Request timeout")
        except httpx.NetworkError as e:
            logger.error(f"FEMA API network error: {e}")
            raise FEMAAPIError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, FEMAAPIError):
                raise
            logger.error(f"Unexpected error calling FEMA API: {e}")
            raise FEMAAPIError(f"Unexpected error: {str(e)}")
    
    def _extract_flood_zone(self, response_data: Dict[str, Any]) -> str:
        """Extract flood zone classification from FEMA API response.
        
        Args:
            response_data: FEMA API response JSON
            
        Returns:
            Flood zone classification string
        """
        try:
            results = response_data.get("results", [])
            
            if not results:
                logger.info("No flood zone data found, assuming Zone X (minimal risk)")
                return "X"
            
            # Look for FLD_ZONE attribute in results
            for result in results:
                attributes = result.get("attributes", {})
                flood_zone = attributes.get("FLD_ZONE") or attributes.get("ZONE_SUBTY")
                
                if flood_zone:
                    logger.info(f"Found flood zone: {flood_zone}")
                    return flood_zone.strip()
            
            # Default to X if no zone found
            return "X"
            
        except Exception as e:
            logger.warning(f"Error parsing FEMA response: {e}")
            return "Unknown"
    
    def _parse_flood_zone(self, flood_zone: str) -> Dict[str, Any]:
        """Parse flood zone classification into structured data.
        
        Args:
            flood_zone: Flood zone code (e.g., "AE", "VE", "A", "X")
            
        Returns:
            Dictionary with flood zone details
        """
        # Normalize zone code
        zone = flood_zone.upper().strip()
        
        # High-risk zones (Special Flood Hazard Areas)
        high_risk_zones = {
            "A": "High-risk flood zone without base flood elevation",
            "AE": "High-risk flood zone with base flood elevation",
            "AH": "High-risk flood zone with shallow flooding",
            "AO": "High-risk flood zone with sheet flow",
            "VE": "High-risk coastal flood zone with wave action",
            "V": "High-risk coastal flood zone"
        }
        
        # Moderate to low risk zones
        moderate_zones = {
            "X": "Minimal flood risk (outside 500-year floodplain)",
            "B": "Moderate flood risk (500-year floodplain)",
            "C": "Minimal flood risk",
            "SHADED X": "Moderate flood risk (500-year floodplain)"
        }
        
        is_high_risk = zone in high_risk_zones
        
        if zone in high_risk_zones:
            description = high_risk_zones[zone]
        elif zone in moderate_zones:
            description = moderate_zones[zone]
        else:
            description = "Unknown flood zone classification"
            is_high_risk = False
        
        return {
            "flood_zone": zone,
            "description": description,
            "is_high_risk": is_high_risk,
            "requires_insurance": is_high_risk
        }
