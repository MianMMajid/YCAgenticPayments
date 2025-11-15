"""Pytest configuration and fixtures for integration tests."""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet

from models.database import Base
from api.main import app
from models.database import get_db


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

# Generate test encryption key
TEST_ENCRYPTION_KEY = Fernet.generate_key().decode()

# Set test environment variables
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["ENCRYPTION_KEY"] = TEST_ENCRYPTION_KEY
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "CRITICAL"  # Suppress logs during tests
os.environ["RENTCAST_API_KEY"] = "test_rentcast_key"
os.environ["DOCUSIGN_INTEGRATION_KEY"] = "test_docusign_key"
os.environ["DOCUSIGN_SECRET_KEY"] = "test_docusign_secret"
os.environ["DOCUSIGN_ACCOUNT_ID"] = "test_account_id"
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["CRIMEOMETER_API_KEY"] = "test_crime_key"
os.environ["DISABLE_RATE_LIMITING"] = "true"
os.environ["AGENTIC_STRIPE_API_KEY"] = "test_stripe_key"
os.environ["BLOCKCHAIN_RPC_URL"] = "http://localhost:8545"
os.environ["BLOCKCHAIN_PRIVATE_KEY"] = "test_private_key"


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    # Create test engine
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "phone_number": "+1234567890",
        "email": "test@example.com",
        "name": "Test User",
        "preferred_locations": ["Baltimore, MD"],
        "max_budget": 400000,
        "min_beds": 3,
        "pre_approved": True,
        "pre_approval_amount": 450000
    }


@pytest.fixture
def sample_search_request():
    """Sample search request data."""
    return {
        "location": "Baltimore, MD",
        "max_price": 400000,
        "min_beds": 3,
        "min_baths": 2,
        "user_id": "test_user_123"
    }


@pytest.fixture
def sample_risk_request():
    """Sample risk analysis request data."""
    return {
        "property_id": "prop_123",
        "address": "123 Main St, Baltimore, MD 21201",
        "list_price": 385000,
        "user_id": "test_user_123",
        "city": "Baltimore",
        "state": "MD",
        "zip_code": "21201",
        "latitude": 39.2904,
        "longitude": -76.6122
    }


@pytest.fixture
def sample_offer_request():
    """Sample offer request data."""
    return {
        "property_id": "prop_123",
        "address": "123 Main St, Baltimore, MD 21201",
        "offer_price": 350000,
        "list_price": 385000,
        "closing_days": 30,
        "financing_type": "conventional",
        "contingencies": ["inspection", "appraisal", "financing"],
        "earnest_money": 10000,
        "special_terms": "Seller to provide home warranty",
        "user_id": "test_user_123",
        "user_email": "buyer@example.com",
        "user_name": "John Doe"
    }


@pytest.fixture
def mock_rentcast_listings():
    """Mock RentCast API listing response."""
    return [
        {
            "id": "prop_001",
            "addressLine1": "123 Main St",
            "city": "Baltimore",
            "state": "MD",
            "zipCode": "21201",
            "price": 385000,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "squareFootage": 1800,
            "propertyType": "Single Family",
            "status": "Active",
            "url": "https://example.com/listing1",
            "description": "Beautiful colonial home with updated kitchen"
        },
        {
            "id": "prop_002",
            "addressLine1": "456 Oak Ave",
            "city": "Baltimore",
            "state": "MD",
            "zipCode": "21202",
            "price": 395000,
            "bedrooms": 4,
            "bathrooms": 3,
            "squareFootage": 2100,
            "propertyType": "Single Family",
            "status": "Active",
            "url": "https://example.com/listing2",
            "description": "Spacious home with large backyard"
        },
        {
            "id": "prop_003",
            "addressLine1": "789 Elm St",
            "city": "Baltimore",
            "state": "MD",
            "zipCode": "21201",
            "price": 375000,
            "bedrooms": 3,
            "bathrooms": 2,
            "squareFootage": 1650,
            "propertyType": "Townhouse",
            "status": "Active",
            "url": "https://example.com/listing3",
            "description": "Modern townhouse in great location"
        }
    ]


@pytest.fixture
def mock_rentcast_property_value():
    """Mock RentCast property value response."""
    return {
        "estimated_value": 350000,
        "tax_assessment": 200000,
        "property_id": "prop_123"
    }


@pytest.fixture
def mock_fema_flood_data():
    """Mock FEMA flood zone response."""
    return {
        "flood_zone": "AE",
        "is_high_risk": True,
        "description": "Special Flood Hazard Area with base flood elevation"
    }


@pytest.fixture
def mock_crime_data():
    """Mock crime statistics response."""
    return {
        "crime_score": 75,
        "crime_level": "high",
        "incidents_count": 150
    }


@pytest.fixture
def mock_docusign_envelope():
    """Mock Docusign envelope creation response."""
    return {
        "envelope_id": "env_test_123",
        "signing_url": "https://demo.docusign.net/Signing/test_url",
        "status": "sent"
    }
