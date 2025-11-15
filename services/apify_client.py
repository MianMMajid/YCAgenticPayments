"""Apify client for Zillow agent scraping."""
import httpx
import logging
import hashlib
import asyncio
from typing import Dict, Optional, Any
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ApifyAPIError(Exception):
    """Exception raised for Apify API errors."""
    pass


class ApifyClient:
    """Client for interacting with Apify actors (Zillow agent scraper)."""
    
    BASE_URL = "https://api.apify.com/v2"
    ZILLOW_ACTOR_ID = "maxcopell/zillow-agent-scraper"  # Popular Zillow scraper
    
    def __init__(self, api_token: str, redis_client: Optional[redis.Redis] = None, cache_ttl: int = 604800):
        """Initialize the Apify client.
        
        Args:
            api_token: Apify API token for authentication
            redis_client: Optional Redis client for caching
            cache_ttl: Cache time-to-live in seconds (default: 7 days)
        """
        if not api_token:
            raise ValueError("Apify API token is required")
        
        self.api_token = api_token
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
    
    def _get_cache_key(self, listing_url: str) -> str:
        """Generate cache key for agent contact info.
        
        Args:
            listing_url: Zillow listing URL
            
        Returns:
            Cache key string
        """
        url_hash = hashlib.md5(listing_url.encode()).hexdigest()
        return f"apify:agent:{url_hash}"
    
    async def _get_from_cache(self, listing_url: str) -> Optional[Dict[str, Any]]:
        """Get agent info from cache.
        
        Args:
            listing_url: Zillow listing URL
            
        Returns:
            Cached agent info or None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(listing_url)
            cached_value = await self.redis_client.get(cache_key)
            if cached_value:
                logger.info(f"Cache hit for agent info: {listing_url}")
                import json
                return json.loads(cached_value)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    async def _set_cache(self, listing_url: str, agent_info: Dict[str, Any]) -> None:
        """Store agent info in cache.
        
        Args:
            listing_url: Zillow listing URL
            agent_info: Agent contact information
        """
        if not self.redis_client:
            return
        
        try:
            import json
            cache_key = self._get_cache_key(listing_url)
            await self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(agent_info))
            logger.info(f"Cached agent info for: {listing_url}")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    
    async def scrape_agent_info(
        self,
        listing_url: str,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """Scrape listing agent contact information from Zillow.
        
        Args:
            listing_url: Full Zillow listing URL
            timeout: Maximum time to wait for scraper (default: 60 seconds)
            
        Returns:
            Dictionary with agent information:
            {
                "agent_name": str,
                "agent_email": str,
                "agent_phone": str,
                "brokerage": str,
                "found": bool
            }
            
        Raises:
            ApifyAPIError: If the API request fails
        """
        # Check cache first
        cached_info = await self._get_from_cache(listing_url)
        if cached_info:
            return cached_info
        
        logger.info(f"Scraping agent info from: {listing_url}")
        
        # Run the Zillow scraper actor
        try:
            run_id = await self._start_actor_run(listing_url)
            agent_info = await self._wait_for_results(run_id, timeout)
            
            # Cache the result
            await self._set_cache(listing_url, agent_info)
            
            return agent_info
            
        except Exception as e:
            if isinstance(e, ApifyAPIError):
                raise
            logger.error(f"Unexpected error scraping agent info: {e}")
            raise ApifyAPIError(f"Unexpected error: {str(e)}")
    
    async def _start_actor_run(self, listing_url: str) -> str:
        """Start an Apify actor run.
        
        Args:
            listing_url: Zillow listing URL to scrape
            
        Returns:
            Run ID for the actor execution
            
        Raises:
            ApifyAPIError: If starting the actor fails
        """
        url = f"{self.BASE_URL}/acts/{self.ZILLOW_ACTOR_ID}/runs"
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Actor input configuration
        payload = {
            "startUrls": [{"url": listing_url}],
            "maxItems": 1,
            "extendOutputFunction": "",
            "proxyConfiguration": {"useApifyProxy": True}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    data = response.json()
                    run_id = data["data"]["id"]
                    logger.info(f"Started actor run: {run_id}")
                    return run_id
                elif response.status_code == 401:
                    raise ApifyAPIError("Invalid Apify API token")
                else:
                    raise ApifyAPIError(f"Failed to start actor: {response.status_code}")
                    
        except httpx.TimeoutException:
            raise ApifyAPIError("Request timeout starting actor")
        except httpx.NetworkError as e:
            raise ApifyAPIError(f"Network error: {str(e)}")
    
    async def _wait_for_results(self, run_id: str, timeout: float) -> Dict[str, Any]:
        """Wait for actor run to complete and retrieve results.
        
        Args:
            run_id: Actor run ID
            timeout: Maximum time to wait in seconds
            
        Returns:
            Parsed agent information
            
        Raises:
            ApifyAPIError: If retrieving results fails
        """
        url = f"{self.BASE_URL}/actor-runs/{run_id}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with httpx.AsyncClient() as client:
                # Poll for completion
                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        raise ApifyAPIError("Actor run timeout")
                    
                    response = await client.get(url, headers=headers, timeout=10.0)
                    
                    if response.status_code != 200:
                        raise ApifyAPIError(f"Failed to check run status: {response.status_code}")
                    
                    data = response.json()
                    status = data["data"]["status"]
                    
                    if status == "SUCCEEDED":
                        # Get dataset results
                        dataset_id = data["data"]["defaultDatasetId"]
                        return await self._get_dataset_items(dataset_id)
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        raise ApifyAPIError(f"Actor run {status.lower()}")
                    
                    # Wait before polling again
                    await asyncio.sleep(2)
                    
        except httpx.TimeoutException:
            raise ApifyAPIError("Request timeout checking run status")
        except httpx.NetworkError as e:
            raise ApifyAPIError(f"Network error: {str(e)}")
    
    async def _get_dataset_items(self, dataset_id: str) -> Dict[str, Any]:
        """Retrieve and parse dataset items from completed run.
        
        Args:
            dataset_id: Dataset ID containing results
            
        Returns:
            Parsed agent information
            
        Raises:
            ApifyAPIError: If retrieving dataset fails
        """
        url = f"{self.BASE_URL}/datasets/{dataset_id}/items"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                
                if response.status_code != 200:
                    raise ApifyAPIError(f"Failed to get dataset: {response.status_code}")
                
                items = response.json()
                
                if not items:
                    logger.warning("No agent info found in scraper results")
                    return {
                        "agent_name": None,
                        "agent_email": None,
                        "agent_phone": None,
                        "brokerage": None,
                        "found": False
                    }
                
                # Parse agent info from first item
                return self._parse_agent_data(items[0])
                
        except httpx.TimeoutException:
            raise ApifyAPIError("Request timeout getting dataset")
        except httpx.NetworkError as e:
            raise ApifyAPIError(f"Network error: {str(e)}")
    
    def _parse_agent_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse agent contact information from scraper result.
        
        Args:
            item: Scraper result item
            
        Returns:
            Structured agent information
        """
        # Different scrapers may have different field names
        # Try common variations
        agent_name = (
            item.get("agentName") or
            item.get("agent_name") or
            item.get("listingAgent") or
            item.get("contactName")
        )
        
        agent_email = (
            item.get("agentEmail") or
            item.get("agent_email") or
            item.get("email") or
            item.get("contactEmail")
        )
        
        agent_phone = (
            item.get("agentPhone") or
            item.get("agent_phone") or
            item.get("phone") or
            item.get("contactPhone")
        )
        
        brokerage = (
            item.get("brokerage") or
            item.get("brokerageName") or
            item.get("officeName")
        )
        
        found = bool(agent_name or agent_email or agent_phone)
        
        result = {
            "agent_name": agent_name,
            "agent_email": agent_email,
            "agent_phone": agent_phone,
            "brokerage": brokerage,
            "found": found
        }
        
        logger.info(f"Parsed agent info: {result}")
        return result
