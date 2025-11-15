# Integration Tests for Counter AI Real Estate Broker

This directory contains comprehensive integration tests for the Counter AI system.

## Test Files

### 1. `test_database_operations.py`
Tests for database CRUD operations covering all models:
- **User CRUD**: Create, read, update, delete operations
- **SearchHistory CRUD**: Property search history tracking
- **RiskAnalysis CRUD**: Risk assessment storage
- **Viewing CRUD**: Appointment scheduling
- **Offer CRUD**: Purchase offer management
- **Relationships**: Tests for model relationships and cascading deletes

**Status**: ✅ All 20 tests passing

### 2. `test_search_integration.py`
Integration tests for the property search tool:
- Search with mocked RentCast API
- Cache hit scenarios
- API failure graceful degradation
- Search filtering and sorting
- Input validation

**Tests**: 6 integration tests covering Requirements 1.2

### 3. `test_risk_analysis_integration.py`
Integration tests for the risk analysis tool:
- Risk analysis with mocked external APIs (RentCast, FEMA, Crime)
- Overpricing detection
- Flood zone detection
- Cache hit scenarios
- Graceful degradation with partial API failures
- Flag sorting by severity

**Tests**: 7 integration tests covering Requirements 2.1

### 4. `test_offer_integration.py`
Integration tests for the offer generation tool:
- Offer generation with mocked Docusign API
- State-specific template mapping
- Unsupported state handling
- Contingency mapping
- Price formatting
- Closing date calculation
- API failure handling
- Input validation

**Tests**: 8 integration tests covering Requirement 4.3

## Running Tests

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_database_operations.py -v
```

### Run Specific Test
```bash
pytest tests/test_database_operations.py::TestUserCRUD::test_create_user -v
```

## Test Configuration

- **Database**: SQLite in-memory database for fast, isolated tests
- **Environment**: Test environment variables set in `conftest.py`
- **Fixtures**: Comprehensive fixtures for sample data and mocked responses
- **Async Support**: pytest-asyncio for testing async endpoints

## Test Coverage

The integration tests cover:
- ✅ Property search with mocked RentCast API (Requirement 1.2)
- ✅ Risk analysis with mocked external APIs (Requirement 2.1)
- ✅ Offer generation with mocked Docusign API (Requirement 4.3)
- ✅ Database operations (CRUD) for all models
- ✅ Error handling and graceful degradation
- ✅ Input validation
- ✅ Caching behavior

## Notes

- Tests use mocked external APIs to avoid rate limits and ensure consistent results
- Database tests use SQLite in-memory for speed and isolation
- Rate limiting is disabled in test environment via `DISABLE_RATE_LIMITING` environment variable
- All sensitive data (API keys, credentials) use test values
