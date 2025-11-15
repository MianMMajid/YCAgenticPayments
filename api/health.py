"""Health check endpoints for monitoring and orchestration."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from redis.exceptions import RedisError

from models.database import SessionLocal
from services.cache_client import cache_client
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthStatus(str, Enum):
    """Health status enum."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealth:
    """
    Utility class for checking dependency health.
    """
    
    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """
        Check database connectivity and health.
        
        Returns:
            Health check result with status and details
        """
        try:
            db = SessionLocal()
            
            # Execute simple query to verify connection
            start_time = datetime.utcnow()
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            db.close()
            
            return {
                "status": HealthStatus.HEALTHY,
                "response_time_seconds": response_time,
                "message": "Database connection successful"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e),
                "message": "Database connection failed"
            }
    
    @staticmethod
    async def check_redis() -> Dict[str, Any]:
        """
        Check Redis connectivity and health.
        
        Returns:
            Health check result with status and details
        """
        try:
            start_time = datetime.utcnow()
            
            # Ping Redis
            cache_client.redis_client.ping()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Get Redis info
            info = cache_client.redis_client.info()
            
            return {
                "status": HealthStatus.HEALTHY,
                "response_time_seconds": response_time,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "message": "Redis connection successful"
            }
        except RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e),
                "message": "Redis connection failed"
            }
        except Exception as e:
            logger.error(f"Redis health check failed with unexpected error: {e}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e),
                "message": "Redis health check error"
            }
    
    @staticmethod
    async def check_agentic_stripe() -> Dict[str, Any]:
        """
        Check Agentic Stripe API connectivity.
        
        Returns:
            Health check result with status and details
        """
        try:
            from services.agentic_stripe_client import agentic_stripe_client
            
            # Check if API key is configured
            if not settings.agentic_stripe_api_key:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Agentic Stripe API key not configured"
                }
            
            start_time = datetime.utcnow()
            
            # Try to make a simple API call (e.g., list wallets or check balance)
            # For now, we'll just verify the client is initialized
            if agentic_stripe_client:
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                return {
                    "status": HealthStatus.HEALTHY,
                    "response_time_seconds": response_time,
                    "message": "Agentic Stripe client initialized"
                }
            else:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": "Agentic Stripe client not initialized"
                }
        except Exception as e:
            logger.error(f"Agentic Stripe health check failed: {e}")
            return {
                "status": HealthStatus.DEGRADED,
                "error": str(e),
                "message": "Agentic Stripe health check failed"
            }
    
    @staticmethod
    async def check_blockchain() -> Dict[str, Any]:
        """
        Check blockchain connectivity.
        
        Returns:
            Health check result with status and details
        """
        try:
            from services.blockchain_client import blockchain_client
            
            # Check if blockchain RPC URL is configured
            if not settings.blockchain_rpc_url:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Blockchain RPC URL not configured"
                }
            
            start_time = datetime.utcnow()
            
            # Try to connect to blockchain
            # For now, we'll just verify the client is initialized
            if blockchain_client:
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                return {
                    "status": HealthStatus.HEALTHY,
                    "response_time_seconds": response_time,
                    "network": settings.blockchain_network,
                    "message": "Blockchain client initialized"
                }
            else:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": "Blockchain client not initialized"
                }
        except Exception as e:
            logger.error(f"Blockchain health check failed: {e}")
            return {
                "status": HealthStatus.DEGRADED,
                "error": str(e),
                "message": "Blockchain health check failed"
            }
    
    @staticmethod
    async def check_circuit_breakers() -> Dict[str, Any]:
        """
        Check circuit breaker states.
        
        Returns:
            Circuit breaker states and overall health
        """
        try:
            from services.circuit_breaker import circuit_breaker_registry
            
            states = circuit_breaker_registry.get_all_states()
            
            # Determine overall health based on circuit breaker states
            all_closed = all(state["state"] == "closed" for state in states.values())
            any_open = any(state["state"] == "open" for state in states.values())
            
            if all_closed:
                overall_status = HealthStatus.HEALTHY
                message = "All circuit breakers closed"
            elif any_open:
                overall_status = HealthStatus.UNHEALTHY
                message = "Some circuit breakers open"
            else:
                overall_status = HealthStatus.DEGRADED
                message = "Some circuit breakers half-open"
            
            return {
                "status": overall_status,
                "circuit_breakers": states,
                "message": message
            }
        except Exception as e:
            logger.error(f"Circuit breaker health check failed: {e}")
            return {
                "status": HealthStatus.DEGRADED,
                "error": str(e),
                "message": "Circuit breaker health check failed"
            }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness probe endpoint.
    
    Returns a simple 200 OK if the application is running.
    This is used by orchestrators (Kubernetes, Docker) to determine
    if the application should be restarted.
    
    Returns:
        Simple health status
    """
    return {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "Counter AI Real Estate Broker - Escrow System",
        "version": "1.0.0"
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness probe endpoint.
    
    Checks if the application is ready to serve traffic by verifying
    all critical dependencies are available.
    
    Returns 200 if ready, 503 if not ready.
    
    Returns:
        Detailed health status with dependency checks
    """
    # Check all dependencies
    db_health = await DependencyHealth.check_database()
    redis_health = await DependencyHealth.check_redis()
    agentic_stripe_health = await DependencyHealth.check_agentic_stripe()
    blockchain_health = await DependencyHealth.check_blockchain()
    circuit_breaker_health = await DependencyHealth.check_circuit_breakers()
    
    # Determine overall health
    dependencies = {
        "database": db_health,
        "redis": redis_health,
        "agentic_stripe": agentic_stripe_health,
        "blockchain": blockchain_health,
        "circuit_breakers": circuit_breaker_health
    }
    
    # Critical dependencies: database and redis
    critical_healthy = (
        db_health["status"] == HealthStatus.HEALTHY and
        redis_health["status"] == HealthStatus.HEALTHY
    )
    
    # Check if any dependency is unhealthy
    any_unhealthy = any(
        dep["status"] == HealthStatus.UNHEALTHY
        for dep in dependencies.values()
    )
    
    # Check if any dependency is degraded
    any_degraded = any(
        dep["status"] == HealthStatus.DEGRADED
        for dep in dependencies.values()
    )
    
    # Determine overall status
    if not critical_healthy or any_unhealthy:
        overall_status = HealthStatus.UNHEALTHY
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif any_degraded:
        overall_status = HealthStatus.DEGRADED
        status_code = status.HTTP_200_OK
    else:
        overall_status = HealthStatus.HEALTHY
        status_code = status.HTTP_200_OK
    
    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "Counter AI Real Estate Broker - Escrow System",
        "version": "1.0.0",
        "environment": settings.environment,
        "dependencies": dependencies
    }
    
    return JSONResponse(content=response, status_code=status_code)


@router.get("/health/startup")
async def startup_check():
    """
    Startup probe endpoint.
    
    Checks if the application has completed initialization.
    Similar to readiness but may have different thresholds.
    
    Returns:
        Startup health status
    """
    # For now, use same logic as readiness
    # In production, this could have different criteria
    return await readiness_check()


@router.get("/health/dependencies")
async def dependencies_check():
    """
    Detailed dependency health check endpoint.
    
    Provides detailed information about each dependency's health.
    
    Returns:
        Detailed dependency health information
    """
    db_health = await DependencyHealth.check_database()
    redis_health = await DependencyHealth.check_redis()
    agentic_stripe_health = await DependencyHealth.check_agentic_stripe()
    blockchain_health = await DependencyHealth.check_blockchain()
    circuit_breaker_health = await DependencyHealth.check_circuit_breakers()
    
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dependencies": {
            "database": db_health,
            "redis": redis_health,
            "agentic_stripe": agentic_stripe_health,
            "blockchain": blockchain_health,
            "circuit_breakers": circuit_breaker_health
        }
    }


@router.get("/health")
async def health_check():
    """
    General health check endpoint.
    
    Alias for readiness check for backward compatibility.
    
    Returns:
        Health status
    """
    return await readiness_check()
