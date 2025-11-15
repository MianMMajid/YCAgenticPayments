"""Workflow state caching service for escrow transactions."""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

from services.cache_client import cache_client, CacheKeyGenerator

logger = logging.getLogger(__name__)


class WorkflowCache:
    """Service for caching workflow state with specific TTLs."""
    
    # TTL constants (in seconds)
    TRANSACTION_STATE_TTL = 300  # 5 minutes
    VERIFICATION_REPORT_TTL = 86400  # 24 hours
    AGENT_PROFILE_TTL = 3600  # 1 hour
    BLOCKCHAIN_EVENT_TTL = 900  # 15 minutes
    
    def __init__(self):
        """Initialize workflow cache service."""
        self.cache = cache_client
    
    def cache_transaction_state(self, transaction_id: str, transaction_data: Dict[str, Any]) -> bool:
        """
        Cache transaction state with 5-minute TTL.
        
        Args:
            transaction_id: Transaction ID
            transaction_data: Transaction state data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert Decimal values to strings for JSON serialization
            serializable_data = self._prepare_for_cache(transaction_data)
            
            key = CacheKeyGenerator.transaction_key(transaction_id)
            success = self.cache.set(key, serializable_data, ttl=self.TRANSACTION_STATE_TTL)
            
            if success:
                logger.debug(f"Cached transaction state: {transaction_id} (TTL: {self.TRANSACTION_STATE_TTL}s)")
            
            return success
        except Exception as e:
            logger.error(f"Error caching transaction state {transaction_id}: {e}")
            return False
    
    def get_transaction_state(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached transaction state.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction state data or None if not cached
        """
        try:
            key = CacheKeyGenerator.transaction_key(transaction_id)
            data = self.cache.get(key)
            
            if data:
                logger.debug(f"Retrieved cached transaction state: {transaction_id}")
            
            return data
        except Exception as e:
            logger.error(f"Error retrieving transaction state {transaction_id}: {e}")
            return None
    
    def cache_verification_report(self, report_id: str, report_data: Dict[str, Any]) -> bool:
        """
        Cache verification report with 24-hour TTL.
        
        Args:
            report_id: Report ID
            report_data: Verification report data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serializable_data = self._prepare_for_cache(report_data)
            
            key = CacheKeyGenerator.verification_report_key(report_id)
            success = self.cache.set(key, serializable_data, ttl=self.VERIFICATION_REPORT_TTL)
            
            if success:
                logger.debug(f"Cached verification report: {report_id} (TTL: {self.VERIFICATION_REPORT_TTL}s)")
            
            return success
        except Exception as e:
            logger.error(f"Error caching verification report {report_id}: {e}")
            return False
    
    def get_verification_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached verification report.
        
        Args:
            report_id: Report ID
            
        Returns:
            Verification report data or None if not cached
        """
        try:
            key = CacheKeyGenerator.verification_report_key(report_id)
            data = self.cache.get(key)
            
            if data:
                logger.debug(f"Retrieved cached verification report: {report_id}")
            
            return data
        except Exception as e:
            logger.error(f"Error retrieving verification report {report_id}: {e}")
            return None
    
    def cache_agent_profile(self, agent_id: str, agent_data: Dict[str, Any]) -> bool:
        """
        Cache agent profile with 1-hour TTL.
        
        Args:
            agent_id: Agent ID
            agent_data: Agent profile data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serializable_data = self._prepare_for_cache(agent_data)
            
            key = CacheKeyGenerator.agent_profile_key(agent_id)
            success = self.cache.set(key, serializable_data, ttl=self.AGENT_PROFILE_TTL)
            
            if success:
                logger.debug(f"Cached agent profile: {agent_id} (TTL: {self.AGENT_PROFILE_TTL}s)")
            
            return success
        except Exception as e:
            logger.error(f"Error caching agent profile {agent_id}: {e}")
            return False
    
    def get_agent_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached agent profile.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent profile data or None if not cached
        """
        try:
            key = CacheKeyGenerator.agent_profile_key(agent_id)
            data = self.cache.get(key)
            
            if data:
                logger.debug(f"Retrieved cached agent profile: {agent_id}")
            
            return data
        except Exception as e:
            logger.error(f"Error retrieving agent profile {agent_id}: {e}")
            return None
    
    def cache_blockchain_events(
        self, 
        transaction_id: str, 
        event_type: str, 
        events: List[Dict[str, Any]]
    ) -> bool:
        """
        Cache blockchain events with 15-minute TTL.
        
        Args:
            transaction_id: Transaction ID
            event_type: Event type
            events: List of blockchain events
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serializable_events = [self._prepare_for_cache(event) for event in events]
            
            key = CacheKeyGenerator.blockchain_event_key(transaction_id, event_type)
            success = self.cache.set(key, serializable_events, ttl=self.BLOCKCHAIN_EVENT_TTL)
            
            if success:
                logger.debug(
                    f"Cached blockchain events: {transaction_id}/{event_type} "
                    f"(TTL: {self.BLOCKCHAIN_EVENT_TTL}s)"
                )
            
            return success
        except Exception as e:
            logger.error(f"Error caching blockchain events {transaction_id}/{event_type}: {e}")
            return False
    
    def get_blockchain_events(
        self, 
        transaction_id: str, 
        event_type: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached blockchain events.
        
        Args:
            transaction_id: Transaction ID
            event_type: Event type
            
        Returns:
            List of blockchain events or None if not cached
        """
        try:
            key = CacheKeyGenerator.blockchain_event_key(transaction_id, event_type)
            data = self.cache.get(key)
            
            if data:
                logger.debug(f"Retrieved cached blockchain events: {transaction_id}/{event_type}")
            
            return data
        except Exception as e:
            logger.error(f"Error retrieving blockchain events {transaction_id}/{event_type}: {e}")
            return None
    
    def cache_workflow_state(self, transaction_id: str, workflow_data: Dict[str, Any]) -> bool:
        """
        Cache workflow execution state with 5-minute TTL.
        
        Args:
            transaction_id: Transaction ID
            workflow_data: Workflow state data (tasks, dependencies, status)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serializable_data = self._prepare_for_cache(workflow_data)
            
            key = CacheKeyGenerator.workflow_state_key(transaction_id)
            success = self.cache.set(key, serializable_data, ttl=self.TRANSACTION_STATE_TTL)
            
            if success:
                logger.debug(f"Cached workflow state: {transaction_id} (TTL: {self.TRANSACTION_STATE_TTL}s)")
            
            return success
        except Exception as e:
            logger.error(f"Error caching workflow state {transaction_id}: {e}")
            return False
    
    def get_workflow_state(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached workflow execution state.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Workflow state data or None if not cached
        """
        try:
            key = CacheKeyGenerator.workflow_state_key(transaction_id)
            data = self.cache.get(key)
            
            if data:
                logger.debug(f"Retrieved cached workflow state: {transaction_id}")
            
            return data
        except Exception as e:
            logger.error(f"Error retrieving workflow state {transaction_id}: {e}")
            return None
    
    def invalidate_transaction_cache(self, transaction_id: str) -> bool:
        """
        Invalidate all cache entries for a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.cache.invalidate_transaction(transaction_id)
    
    def invalidate_verification_report_cache(self, report_id: str) -> bool:
        """
        Invalidate cache entry for a verification report.
        
        Args:
            report_id: Report ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.cache.invalidate_verification_report(report_id)
    
    def invalidate_agent_profile_cache(self, agent_id: str) -> bool:
        """
        Invalidate cache entry for an agent profile.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.cache.invalidate_agent_profile(agent_id)
    
    def _prepare_for_cache(self, data: Any) -> Any:
        """
        Prepare data for caching by converting non-serializable types.
        
        Args:
            data: Data to prepare
            
        Returns:
            Serializable data
        """
        if isinstance(data, dict):
            return {k: self._prepare_for_cache(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_cache(item) for item in data]
        elif isinstance(data, Decimal):
            return str(data)
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, '__dict__'):
            # Handle objects with __dict__ (like SQLAlchemy models)
            return self._prepare_for_cache(data.__dict__)
        else:
            return data


# Global workflow cache instance
workflow_cache = WorkflowCache()
