"""Enhanced encryption service for sensitive transaction data."""
import json
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64

from config.settings import settings
from api.structured_logging import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        """Initialize encryption service with key from settings."""
        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY must be set in environment")
        
        self.cipher = Fernet(settings.encryption_key.encode())
        logger.info("encryption_service_initialized")
    
    def encrypt_string(self, plaintext: str) -> str:
        """
        Encrypt a string value.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return plaintext
        
        try:
            encrypted = self.cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error("encryption_failed", error=str(e))
            raise
    
    def decrypt_string(self, ciphertext: str) -> str:
        """
        Decrypt a string value.
        
        Args:
            ciphertext: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ciphertext
        
        try:
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error("decryption_failed", error=str(e))
            raise
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt a dictionary by converting to JSON and encrypting.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted JSON string
        """
        if not data:
            return ""
        
        try:
            json_str = json.dumps(data)
            return self.encrypt_string(json_str)
        except Exception as e:
            logger.error("dict_encryption_failed", error=str(e))
            raise
    
    def decrypt_dict(self, ciphertext: str) -> Dict[str, Any]:
        """
        Decrypt an encrypted dictionary.
        
        Args:
            ciphertext: Base64-encoded encrypted JSON string
            
        Returns:
            Decrypted dictionary
        """
        if not ciphertext:
            return {}
        
        try:
            json_str = self.decrypt_string(ciphertext)
            return json.loads(json_str)
        except Exception as e:
            logger.error("dict_decryption_failed", error=str(e))
            raise
    
    def encrypt_pii(self, pii_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Encrypt PII (Personally Identifiable Information) fields.
        
        Args:
            pii_data: Dictionary containing PII fields
            
        Returns:
            Dictionary with encrypted PII fields
        """
        encrypted_pii = {}
        
        for key, value in pii_data.items():
            if value is not None:
                if isinstance(value, str):
                    encrypted_pii[key] = self.encrypt_string(value)
                else:
                    # Convert to string first
                    encrypted_pii[key] = self.encrypt_string(str(value))
            else:
                encrypted_pii[key] = None
        
        logger.info("pii_encrypted", field_count=len(encrypted_pii))
        return encrypted_pii
    
    def decrypt_pii(self, encrypted_pii: Dict[str, str]) -> Dict[str, str]:
        """
        Decrypt PII fields.
        
        Args:
            encrypted_pii: Dictionary with encrypted PII fields
            
        Returns:
            Dictionary with decrypted PII fields
        """
        decrypted_pii = {}
        
        for key, value in encrypted_pii.items():
            if value is not None:
                decrypted_pii[key] = self.decrypt_string(value)
            else:
                decrypted_pii[key] = None
        
        logger.info("pii_decrypted", field_count=len(decrypted_pii))
        return decrypted_pii
    
    def hash_sensitive_data(self, data: str, salt: Optional[bytes] = None) -> str:
        """
        Create a one-way hash of sensitive data (for comparison, not decryption).
        
        Args:
            data: Data to hash
            salt: Optional salt for hashing (generated if not provided)
            
        Returns:
            Base64-encoded hash
        """
        if salt is None:
            salt = settings.encryption_key.encode()[:16]  # Use first 16 bytes of key as salt
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(data.encode())
        return base64.b64encode(key).decode()


# Global encryption service instance
encryption_service = EncryptionService()


def encrypt_transaction_metadata(metadata: Dict[str, Any]) -> str:
    """
    Encrypt transaction metadata containing sensitive information.
    
    Args:
        metadata: Transaction metadata dictionary
        
    Returns:
        Encrypted metadata string
    """
    # Identify and encrypt sensitive fields
    sensitive_fields = [
        'ssn', 'tax_id', 'bank_account', 'routing_number',
        'credit_card', 'drivers_license', 'passport'
    ]
    
    encrypted_metadata = metadata.copy()
    
    for field in sensitive_fields:
        if field in encrypted_metadata and encrypted_metadata[field]:
            encrypted_metadata[field] = encryption_service.encrypt_string(
                str(encrypted_metadata[field])
            )
    
    return encryption_service.encrypt_dict(encrypted_metadata)


def decrypt_transaction_metadata(encrypted_metadata: str) -> Dict[str, Any]:
    """
    Decrypt transaction metadata.
    
    Args:
        encrypted_metadata: Encrypted metadata string
        
    Returns:
        Decrypted metadata dictionary
    """
    return encryption_service.decrypt_dict(encrypted_metadata)
