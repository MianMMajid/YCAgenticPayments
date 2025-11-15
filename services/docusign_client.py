"""Docusign API client for contract generation and e-signature."""
import httpx
import logging
import base64
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DocusignAPIError(Exception):
    """Exception raised for Docusign API errors."""
    pass


class DocusignClient:
    """Client for interacting with the Docusign API."""
    
    BASE_URL = "https://demo.docusign.net/restapi"  # Use demo for development
    OAUTH_BASE_URL = "https://account-d.docusign.com"  # Demo OAuth
    
    def __init__(
        self,
        integration_key: str,
        secret_key: str,
        account_id: str,
        use_production: bool = False
    ):
        """Initialize the Docusign client.
        
        Args:
            integration_key: Docusign integration key (client ID)
            secret_key: Docusign secret key
            account_id: Docusign account ID
            use_production: Use production environment (default: False for demo)
        """
        if not integration_key or not secret_key or not account_id:
            raise ValueError("Docusign credentials are required")
        
        self.integration_key = integration_key
        self.secret_key = secret_key
        self.account_id = account_id
        
        # Set URLs based on environment
        if use_production:
            self.base_url = "https://www.docusign.net/restapi"
            self.oauth_base_url = "https://account.docusign.com"
        else:
            self.base_url = self.BASE_URL
            self.oauth_base_url = self.OAUTH_BASE_URL
        
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
    
    async def _get_access_token(self) -> str:
        """Get or refresh OAuth access token.
        
        Returns:
            Valid access token
            
        Raises:
            DocusignAPIError: If authentication fails
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expiry:
            if datetime.now() < self._token_expiry - timedelta(minutes=5):
                return self._access_token
        
        # Request new token using JWT grant
        logger.info("Requesting new Docusign access token")
        
        url = f"{self.oauth_base_url}/oauth/token"
        
        # Create basic auth header
        credentials = f"{self.integration_key}:{self.secret_key}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Use client credentials grant for server-to-server
        data = {
            "grant_type": "client_credentials",
            "scope": "signature impersonation"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=data, timeout=10.0)
                
                if response.status_code == 200:
                    token_data = response.json()
                    self._access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)
                    self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    logger.info("Successfully obtained access token")
                    return self._access_token
                else:
                    raise DocusignAPIError(f"Authentication failed: {response.status_code}")
                    
        except httpx.TimeoutException:
            raise DocusignAPIError("Authentication timeout")
        except httpx.NetworkError as e:
            raise DocusignAPIError(f"Network error during authentication: {str(e)}")
        except Exception as e:
            if isinstance(e, DocusignAPIError):
                raise
            raise DocusignAPIError(f"Unexpected authentication error: {str(e)}")

    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Docusign API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            json_data: Request body
            timeout: Request timeout
            
        Returns:
            Response JSON
            
        Raises:
            DocusignAPIError: If the request fails
        """
        access_token = await self._get_access_token()
        
        url = f"{self.base_url}/v2.1/accounts/{self.account_id}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    timeout=timeout
                )
                
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 401:
                    # Token might be invalid, clear cache and retry once
                    self._access_token = None
                    raise DocusignAPIError("Authentication failed")
                else:
                    error_msg = f"Docusign API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('message', '')}"
                    except:
                        pass
                    raise DocusignAPIError(error_msg)
                    
        except httpx.TimeoutException:
            raise DocusignAPIError("Request timeout")
        except httpx.NetworkError as e:
            raise DocusignAPIError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, DocusignAPIError):
                raise
            raise DocusignAPIError(f"Unexpected error: {str(e)}")
    
    async def create_envelope_from_template(
        self,
        template_id: str,
        signer_email: str,
        signer_name: str,
        tabs: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        email_subject: Optional[str] = None,
        status: str = "sent"
    ) -> Dict[str, Any]:
        """Create an envelope from a template with populated fields.
        
        Args:
            template_id: Docusign template ID
            signer_email: Email address of the signer
            signer_name: Full name of the signer
            tabs: Template tabs to populate (textTabs, checkboxTabs, etc.)
            email_subject: Custom email subject line
            status: Envelope status ("sent" or "created")
            
        Returns:
            Dictionary with envelope details:
            {
                "envelope_id": str,
                "status": str,
                "signing_url": str
            }
            
        Raises:
            DocusignAPIError: If envelope creation fails
        """
        logger.info(f"Creating envelope from template {template_id} for {signer_email}")
        
        # Build envelope definition
        envelope_definition = {
            "templateId": template_id,
            "status": status,
            "emailSubject": email_subject or "Please sign this document",
            "recipients": {
                "signers": [
                    {
                        "email": signer_email,
                        "name": signer_name,
                        "recipientId": "1",
                        "routingOrder": "1"
                    }
                ]
            }
        }
        
        # Add tabs if provided
        if tabs:
            envelope_definition["recipients"]["signers"][0]["tabs"] = tabs
        
        try:
            # Create the envelope
            response = await self._make_request("POST", "/envelopes", json_data=envelope_definition)
            
            envelope_id = response["envelopeId"]
            envelope_status = response["status"]
            
            logger.info(f"Created envelope {envelope_id} with status {envelope_status}")
            
            # Get signing URL
            signing_url = await self.get_recipient_view(
                envelope_id=envelope_id,
                signer_email=signer_email,
                signer_name=signer_name
            )
            
            return {
                "envelope_id": envelope_id,
                "status": envelope_status,
                "signing_url": signing_url
            }
            
        except DocusignAPIError as e:
            logger.error(f"Failed to create envelope: {e}")
            raise
    
    async def get_recipient_view(
        self,
        envelope_id: str,
        signer_email: str,
        signer_name: str,
        return_url: str = "https://counter.app/signing-complete"
    ) -> str:
        """Get the signing URL for a recipient.
        
        Args:
            envelope_id: Envelope ID
            signer_email: Signer's email address
            signer_name: Signer's full name
            return_url: URL to redirect after signing
            
        Returns:
            Signing URL
            
        Raises:
            DocusignAPIError: If getting the view fails
        """
        logger.info(f"Getting recipient view for envelope {envelope_id}")
        
        view_request = {
            "returnUrl": return_url,
            "authenticationMethod": "email",
            "email": signer_email,
            "userName": signer_name,
            "clientUserId": signer_email  # Use email as client user ID
        }
        
        try:
            response = await self._make_request(
                "POST",
                f"/envelopes/{envelope_id}/views/recipient",
                json_data=view_request
            )
            
            signing_url = response["url"]
            logger.info(f"Generated signing URL for {signer_email}")
            return signing_url
            
        except DocusignAPIError as e:
            logger.error(f"Failed to get recipient view: {e}")
            raise
    
    async def get_envelope_status(self, envelope_id: str) -> Dict[str, Any]:
        """Get the current status of an envelope.
        
        Args:
            envelope_id: Envelope ID
            
        Returns:
            Dictionary with envelope status information
            
        Raises:
            DocusignAPIError: If getting status fails
        """
        logger.info(f"Getting status for envelope {envelope_id}")
        
        try:
            response = await self._make_request("GET", f"/envelopes/{envelope_id}")
            
            return {
                "envelope_id": envelope_id,
                "status": response["status"],
                "created_at": response.get("createdDateTime"),
                "sent_at": response.get("sentDateTime"),
                "completed_at": response.get("completedDateTime"),
                "recipients": response.get("recipients", {})
            }
            
        except DocusignAPIError as e:
            logger.error(f"Failed to get envelope status: {e}")
            raise
    
    async def download_document(
        self,
        envelope_id: str,
        document_id: str = "combined"
    ) -> bytes:
        """Download a signed document from an envelope.
        
        Args:
            envelope_id: Envelope ID
            document_id: Document ID (default: "combined" for all documents)
            
        Returns:
            Document bytes (PDF)
            
        Raises:
            DocusignAPIError: If download fails
        """
        logger.info(f"Downloading document {document_id} from envelope {envelope_id}")
        
        access_token = await self._get_access_token()
        url = f"{self.base_url}/v2.1/accounts/{self.account_id}/envelopes/{envelope_id}/documents/{document_id}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/pdf"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                
                if response.status_code == 200:
                    logger.info(f"Successfully downloaded document")
                    return response.content
                else:
                    raise DocusignAPIError(f"Failed to download document: {response.status_code}")
                    
        except httpx.TimeoutException:
            raise DocusignAPIError("Download timeout")
        except httpx.NetworkError as e:
            raise DocusignAPIError(f"Network error: {str(e)}")
