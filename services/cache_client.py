"""Redis cache client for caching API results and escrow workflow state."""
import json
import logging
from typing import Optional, Any, List, Dict
import redis
from redis.exceptions import RedisError
from redis import ConnectionPool

from config.settings import settings

logger = logging.getLogger(__name__)


class CacheKeyGenerator:
    """Utility class for generating consistent cache keys."""
    
    # Cache key prefixes
    TRANSACTION_PREFIX = "transaction"
    VERIFICATION_REPORT_PREFIX = "verification_report"
    AGENT_PROFILE_PREFIX = "agent_profile"
    BLOCKCHAIN_EVENT_PREFIX = "blockchain_event"
    WORKFLOW_STATE_PREFIX = "workflow_state"
    
    @staticmethod
    def transaction_key(transaction_id: str) -> str:
        """Generate cache key for transaction state."""
        return f"{CacheKeyGenerator.TRANSACTION_PREFIX}:{transaction_id}"
    
    @staticmethod
    def verification_report_key(report_id: str) -> str:
        """Generate cache key for verification report."""
        return f"{CacheKeyGenerator.VERIFICATION_REPORT_PREFIX}:{report_id}"
    
    @staticmethod
    def agent_profile_key(agent_id: str) -> str:
        """Generate cache key for agent profile."""
        return f"{CacheKeyGenerator.AGENT_PROFILE_PREFIX}:{agent_id}"
    
    @staticmethod
    def blockchain_event_key(transaction_id: str, event_type: str) -> str:
        """Generate cache key for blockchain events."""
        return f"{CacheKeyGenerator.BLOCKCHAIN_EVENT_PREFIX}:{transaction_id}:{event_type}"
    
    @staticmethod
    def workflow_state_key(transaction_id: str) -> str:
        """Generate cache key for workflow state."""
        return f"{CacheKeyGenerator.WORKFLOW_STATE_PREFIX}:{transaction_id}"
    
    @staticmethod
    def transaction_pattern() -> str:
        """Get pattern for all transaction keys."""
        return f"{CacheKeyGenerator.TRANSACTION_PREFIX}:*"
    
    @staticmethod
    def verification_report_pattern() -> str:
        """Get pattern for all verification report keys."""
        return f"{CacheKeyGenerator.VERIFICATION_REPORT_PREFIX}:*"
    
    @staticmethod
    def blockchain_event_pattern(transaction_id: Optional[str] = None) -> str:
        """Get pattern for blockchain event keys."""
        if transaction_id:
            return f"{CacheKeyGenerator.BLOCKCHAIN_EVENT_PREFIX}:{transaction_id}:*"
        return f"{CacheKeyGenerator.BLOCKCHAIN_EVENT_PREFIX}:*"


class CacheClient:
    """Client for interacting with Redis cache with connection pooling."""
    
    def __init__(self, redis_url: Optional[str] = None, pool_size: int = 20, max_overflow: int = 10):
        """
        Initialize the cache client with connection pooling.
        
        Args:
            redis_url: Redis connection URL (defaults to settings.redis_url)
            pool_size: Base connection pool size
            max_overflow: Maximum overflow connections
        """
        self.redis_url = redis_url or settings.redis_url
        self.pool = None
        self.client = None
        
        try:
            # Create connection pool for better performance
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=pool_size + max_overflow,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            
            # Create client from pool
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            self.client.ping()
            logger.info(f"Redis cache connected successfully with pool size {pool_size}")
        except RedisError as e:
            logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
            self.client = None
            self.pool = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value (deserialized from JSON) or None if not found
        """
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            logger.debug(f"Cache miss: {key}")
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set a value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be serialized to JSON)
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except (RedisError, TypeError, json.JSONEncodeError) as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return True
        except RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "search:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except RedisError as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    def invalidate_transaction(self, transaction_id: str) -> bool:
        """
        Invalidate all cache entries related to a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Delete transaction state
            transaction_key = CacheKeyGenerator.transaction_key(transaction_id)
            self.delete(transaction_key)
            
            # Delete workflow state
            workflow_key = CacheKeyGenerator.workflow_state_key(transaction_id)
            self.delete(workflow_key)
            
            # Delete blockchain events for this transaction
            event_pattern = CacheKeyGenerator.blockchain_event_pattern(transaction_id)
            self.clear_pattern(event_pattern)
            
            logger.info(f"Invalidated cache for transaction: {transaction_id}")
            return True
        except RedisError as e:
            logger.error(f"Cache invalidation error for transaction {transaction_id}: {e}")
            return False
    
    def invalidate_verification_report(self, report_id: str) -> bool:
        """
        Invalidate cache entry for a verification report.
        
        Args:
            report_id: Report ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            report_key = CacheKeyGenerator.verification_report_key(report_id)
            self.delete(report_key)
            logger.info(f"Invalidated cache for verification report: {report_id}")
            return True
        except RedisError as e:
            logger.error(f"Cache invalidation error for report {report_id}: {e}")
            return False
    
    def invalidate_agent_profile(self, agent_id: str) -> bool:
        """
        Invalidate cache entry for an agent profile.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            agent_key = CacheKeyGenerator.agent_profile_key(agent_id)
            self.delete(agent_key)
            logger.info(f"Invalidated cache for agent profile: {agent_id}")
            return True
        except RedisError as e:
            logger.error(f"Cache invalidation error for agent {agent_id}: {e}")
            return False
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        if not self.pool:
            return {"status": "disabled"}
        
        try:
            return {
                "status": "active",
                "max_connections": self.pool.max_connections,
                "connection_kwargs": {
                    "socket_connect_timeout": self.pool.connection_kwargs.get("socket_connect_timeout"),
                    "socket_timeout": self.pool.connection_kwargs.get("socket_timeout"),
                }
            }
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def close(self):
        """Close the connection pool."""
        if self.pool:
            self.pool.disconnect()
            logger.info("Redis connection pool closed")


# Global cache client instance
cache_client = CacheClient()
