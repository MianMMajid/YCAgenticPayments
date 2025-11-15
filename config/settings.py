"""Application configuration settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/counter_db"
    
    # External API Keys
    rentcast_api_key: str = ""
    fema_api_key: Optional[str] = None
    apify_api_token: str = ""
    docusign_integration_key: str = ""
    docusign_secret_key: str = ""
    docusign_account_id: str = ""
    docusign_webhook_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_calendar_client_id: str = ""
    google_calendar_client_secret: str = ""
    openai_api_key: str = ""
    sendgrid_api_key: Optional[str] = None
    gmail_api_credentials: Optional[str] = None
    crimeometer_api_key: Optional[str] = None
    
    # Twilio (for SMS notifications)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    encryption_key: str = ""
    
    # TLS/SSL Configuration
    tls_enabled: bool = False
    tls_cert_file: Optional[str] = None
    tls_key_file: Optional[str] = None
    tls_ca_file: Optional[str] = None
    
    # Key Management (AWS KMS or similar)
    kms_enabled: bool = False
    kms_key_id: Optional[str] = None
    kms_region: str = "us-east-1"
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    timezone: str = "America/New_York"  # Default timezone for calendar events
    
    # Agentic Stripe (for escrow smart contract wallets)
    agentic_stripe_api_key: str = ""
    agentic_stripe_webhook_secret: str = ""
    agentic_stripe_network: str = "testnet"  # mainnet or testnet
    
    # Blockchain (for audit trail logging)
    blockchain_rpc_url: str = ""
    blockchain_network: str = "testnet"
    blockchain_contract_address: str = ""
    blockchain_private_key: str = ""
    
    # Circuit Breaker Configuration
    # Agentic Stripe circuit breaker
    agentic_stripe_circuit_breaker_failure_threshold: int = 5
    agentic_stripe_circuit_breaker_timeout: int = 60  # seconds
    
    # Blockchain circuit breaker
    blockchain_circuit_breaker_failure_threshold: int = 10
    blockchain_circuit_breaker_timeout: int = 30  # seconds
    
    # Notification circuit breaker
    notification_circuit_breaker_failure_threshold: int = 3
    notification_circuit_breaker_timeout: int = 120  # seconds
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    sentry_traces_sample_rate: float = 0.1
    sentry_profiles_sample_rate: float = 0.1
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
