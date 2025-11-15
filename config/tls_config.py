"""TLS/SSL configuration for secure API communications."""
import ssl
from typing import Optional
from pathlib import Path

from config.settings import settings
from api.structured_logging import get_logger

logger = get_logger(__name__)


class TLSConfig:
    """TLS configuration for HTTPS and secure communications."""
    
    def __init__(
        self,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_file: Optional[str] = None,
        min_version: int = ssl.TLSVersion.TLSv1_3
    ):
        """
        Initialize TLS configuration.
        
        Args:
            cert_file: Path to SSL certificate file
            key_file: Path to SSL private key file
            ca_file: Path to CA certificate file
            min_version: Minimum TLS version (default: TLS 1.3)
        """
        self.cert_file = cert_file
        self.key_file = key_file
        self.ca_file = ca_file
        self.min_version = min_version
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """
        Create SSL context with secure defaults.
        
        Returns:
            Configured SSL context
        """
        # Create SSL context with secure defaults
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        # Set minimum TLS version to 1.3
        context.minimum_version = self.min_version
        
        # Disable insecure protocols
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        
        # Use strong ciphers only
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Load certificate and key if provided
        if self.cert_file and self.key_file:
            if Path(self.cert_file).exists() and Path(self.key_file).exists():
                context.load_cert_chain(self.cert_file, self.key_file)
                logger.info(
                    "tls_certificates_loaded",
                    cert_file=self.cert_file,
                    key_file=self.key_file
                )
            else:
                logger.warning(
                    "tls_certificate_files_not_found",
                    cert_file=self.cert_file,
                    key_file=self.key_file
                )
        
        # Load CA certificate if provided
        if self.ca_file and Path(self.ca_file).exists():
            context.load_verify_locations(self.ca_file)
            logger.info("tls_ca_certificate_loaded", ca_file=self.ca_file)
        
        logger.info(
            "ssl_context_created",
            min_version=self.min_version.name,
            options=context.options
        )
        
        return context
    
    def get_uvicorn_ssl_config(self) -> dict:
        """
        Get SSL configuration for Uvicorn server.
        
        Returns:
            Dictionary with ssl_keyfile and ssl_certfile
        """
        if not self.cert_file or not self.key_file:
            logger.warning("tls_not_configured_for_uvicorn")
            return {}
        
        return {
            "ssl_keyfile": self.key_file,
            "ssl_certfile": self.cert_file,
            "ssl_version": ssl.PROTOCOL_TLS_SERVER,
            "ssl_cert_reqs": ssl.CERT_NONE,  # Can be changed to CERT_REQUIRED for mutual TLS
        }


def create_client_ssl_context(verify: bool = True) -> ssl.SSLContext:
    """
    Create SSL context for outgoing HTTPS requests.
    
    Args:
        verify: Whether to verify server certificates
        
    Returns:
        Configured SSL context for client connections
    """
    context = ssl.create_default_context()
    
    # Set minimum TLS version to 1.3
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    
    # Disable insecure protocols
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3
    context.options |= ssl.OP_NO_TLSv1
    context.options |= ssl.OP_NO_TLSv1_1
    
    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        logger.warning("client_ssl_verification_disabled")
    
    logger.info("client_ssl_context_created", verify=verify)
    
    return context


# Global TLS configuration
tls_config = TLSConfig(
    cert_file=getattr(settings, 'tls_cert_file', None),
    key_file=getattr(settings, 'tls_key_file', None),
    ca_file=getattr(settings, 'tls_ca_file', None)
)
