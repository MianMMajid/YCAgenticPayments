"""Middleware for session management and request processing."""
from datetime import datetime
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from models.database import SessionLocal
from models.user import User

logger = logging.getLogger(__name__)


class SessionManagementMiddleware(BaseHTTPMiddleware):
    """
    Middleware to update user's last_active timestamp on each API call.
    
    This implements session timeout management as specified in Requirement 7.5.
    The last_active timestamp is updated on each request that includes a user_id.
    Sessions are considered inactive after 30 days of no activity.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and update user session."""
        
        # Process the request
        response = await call_next(request)
        
        # Try to extract user_id from request body or path
        user_id = None
        
        # Check if user_id is in path parameters
        if hasattr(request, 'path_params') and 'user_id' in request.path_params:
            user_id = request.path_params['user_id']
        
        # If we have a user_id, update their last_active timestamp
        if user_id:
            try:
                db = SessionLocal()
                user = db.query(User).filter(User.id == user_id).first()
                
                if user:
                    user.last_active = datetime.utcnow().isoformat()
                    db.commit()
                    logger.debug(f"Updated last_active for user: {user_id}")
                
                db.close()
            except Exception as e:
                logger.error(f"Error updating last_active timestamp: {str(e)}")
                # Don't fail the request if session update fails
        
        return response


def update_user_session(user_id: str, db):
    """
    Helper function to update user's last_active timestamp.
    
    Args:
        user_id: The user's ID
        db: Database session
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if user:
            user.last_active = datetime.utcnow().isoformat()
            db.commit()
            logger.debug(f"Updated session for user: {user_id}")
    except Exception as e:
        logger.error(f"Error updating user session: {str(e)}")
        # Don't raise exception - session update is non-critical


import time
from typing import Callable
from fastapi import Response


class EscrowMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track escrow API metrics.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and track metrics.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        # Only track escrow API endpoints
        if not request.url.path.startswith("/api/escrow"):
            return await call_next(request)
        
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Track metrics
        try:
            from api.escrow_metrics import escrow_metrics
            
            # Normalize endpoint path (remove IDs)
            endpoint = request.url.path
            for segment in endpoint.split('/'):
                # Replace UUID-like segments with placeholder
                if len(segment) == 36 and segment.count('-') == 4:
                    endpoint = endpoint.replace(segment, '{id}')
            
            escrow_metrics.track_api_request(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
                duration_seconds=duration
            )
        except Exception as e:
            logger.error(f"Failed to track API metrics: {e}")
        
        return response
