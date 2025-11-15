"""Locus OAuth 2.0 Client Credentials Authentication.

Based on MCP Spec: https://docs.paywithlocus.com/mcp-spec

OAuth 2.0 Client Credentials (M2M):
- Standard machine-to-machine authentication
- JWT tokens issued by AWS Cognito
- Scopes determine tool access
"""
import logging
import httpx
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# AWS Cognito token endpoint (typical for Locus OAuth)
# This might need to be adjusted based on actual Locus Cognito configuration
COGNITO_TOKEN_ENDPOINT = os.getenv(
    "LOCUS_COGNITO_TOKEN_ENDPOINT",
    "https://cognito-idp.us-east-1.amazonaws.com/oauth2/token"
)

# Alternative: Locus might have its own OAuth endpoint
LOCUS_OAUTH_ENDPOINT = os.getenv(
    "LOCUS_OAUTH_ENDPOINT",
    "https://api.paywithlocus.com/oauth/token"
)


class LocusOAuthClient:
    """
    OAuth 2.0 Client Credentials client for Locus.
    
    Handles OAuth token acquisition and refresh for MCP authentication.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        oauth_endpoint: Optional[str] = None
    ):
        """
        Initialize OAuth client.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            oauth_endpoint: Optional OAuth token endpoint
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_endpoint = oauth_endpoint or LOCUS_OAUTH_ENDPOINT
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        logger.info("Locus OAuth Client initialized")
    
    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get OAuth access token.
        
        Args:
            force_refresh: Force token refresh even if not expired
            
        Returns:
            Access token string
        """
        # Check if we have a valid token
        if (
            not force_refresh
            and self.access_token
            and self.token_expires_at
            and datetime.utcnow() < self.token_expires_at - timedelta(minutes=5)
        ):
            return self.access_token
        
        # Request new token
        logger.info("Requesting new OAuth access token")
        
        # Try different OAuth endpoints
        endpoints = [
            self.oauth_endpoint,
            LOCUS_OAUTH_ENDPOINT,
            COGNITO_TOKEN_ENDPOINT,
            "https://api.paywithlocus.com/api/oauth/token",
            "https://app.paywithlocus.com/api/oauth/token",
        ]
        
        # OAuth 2.0 Client Credentials grant
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        last_error = None
        for endpoint in endpoints:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Try as form data (standard OAuth)
                    response = await client.post(
                        endpoint,
                        data=data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            self.access_token = result.get("access_token")
                            expires_in = result.get("expires_in", 3600)  # Default 1 hour
                            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                            
                            logger.info(
                                f"OAuth token acquired, expires in {expires_in}s",
                                extra={"endpoint": endpoint}
                            )
                            
                            return self.access_token
                        except Exception as e:
                            logger.warning(f"Failed to parse token response: {e}")
                            last_error = f"Parse error: {e}"
                            continue
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                        logger.debug(f"Endpoint {endpoint} returned {response.status_code}")
                        continue
                        
            except httpx.TimeoutException:
                last_error = "Request timeout"
                continue
            except Exception as e:
                last_error = f"Error: {str(e)}"
                continue
        
        # If all endpoints failed, raise error
        raise Exception(
            f"Failed to acquire OAuth token. Last error: {last_error}. "
            f"Tried endpoints: {endpoints}"
        )
    
    def get_authorization_header(self) -> str:
        """
        Get Authorization header value.
        
        Returns:
            Bearer token string
        """
        if not self.access_token:
            raise Exception("No access token available. Call get_access_token() first.")
        
        return f"Bearer {self.access_token}"


async def get_locus_oauth_token() -> Optional[str]:
    """
    Helper function to get OAuth token from environment variables.
    
    Returns:
        Access token or None if credentials not configured
    """
    client_id = os.getenv("LOCUS_CLIENT_ID") or os.getenv("locus_client_id")
    client_secret = os.getenv("LOCUS_CLIENT_SECRET") or os.getenv("locus_client_secret")
    
    if not client_id or not client_secret:
        logger.warning("OAuth credentials not configured")
        return None
    
    client = LocusOAuthClient(client_id, client_secret)
    try:
        token = await client.get_access_token()
        return token
    except Exception as e:
        logger.error(f"Failed to get OAuth token: {e}")
        return None

