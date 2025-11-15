# Error Handling and Monitoring Implementation

This document describes the error handling and monitoring features implemented for the Counter AI Real Estate Broker API.

## Overview

Task 11 has been completed, implementing comprehensive error handling, monitoring, rate limiting, and metrics collection across the application.

## Components Implemented

### 1. Global Exception Handlers (`api/exceptions.py`)

**Custom Exception Classes:**
- `APIError`: Base exception for API errors with status codes and details
- `ExternalServiceError`: For external service failures (503 status)
- `CacheError`: For cache operation failures
- `DatabaseError`: For database operation failures

**Exception Handlers:**
- `api_error_handler`: Handles custom APIError exceptions with full logging
- `validation_error_handler`: Handles Pydantic validation errors with user-friendly messages
- `generic_exception_handler`: Catches all unhandled exceptions and logs with stack traces

**Features:**
- User-friendly error messages (no internal details exposed)
- Full error logging with stack traces
- Structured error responses with status codes and details

### 2. Graceful Degradation (`api/tools/search.py`, `api/tools/analyze_risk.py`)

**Search Endpoint:**
- Falls back to cached results when RentCast API fails
- Attempts to retrieve location-based cached data
- Returns clear error messages when no fallback available

**Risk Analysis Endpoint:**
- Continues analysis even when optional data sources (crime) are unavailable
- Adds informational flags when critical data is missing
- Logs missing data sources for monitoring

**Features:**
- Parallel API calls with timeout handling
- Individual API failure handling (doesn't fail entire request)
- Clear user messaging about data availability

### 3. Sentry Error Tracking (`api/monitoring.py`)

**Integration:**
- FastAPI, SQLAlchemy, and Redis integrations
- Automatic error capture with stack traces
- Performance monitoring with traces and profiles

**Custom Context:**
- User context (user_id, email)
- Tool context (tool_name, parameters)
- Breadcrumbs for debugging trail

**Configuration:**
- Environment-based configuration
- Configurable sampling rates
- Before-send hook for custom filtering

**Helper Functions:**
- `set_user_context()`: Set user information
- `set_tool_context()`: Set tool execution context
- `add_breadcrumb()`: Add debugging breadcrumbs
- `capture_exception()`: Manually capture exceptions
- `capture_message()`: Capture messages

### 4. Rate Limiting (`api/rate_limit.py`)

**Implementation:**
- Uses slowapi library for rate limiting
- 10 requests per minute per IP address
- Applied to all tool endpoints

**Features:**
- Custom identifier function (can use user_id or IP)
- Rate limit headers in responses
- 429 status with retry-after header
- Detailed logging of rate limit violations

**Protected Endpoints:**
- `/tools/search`
- `/tools/analyze-risk`
- `/tools/schedule`
- `/tools/draft-offer`

### 5. Custom Metrics and Logging (`api/metrics.py`)

**Metrics Tracked:**
- Tool execution time (per endpoint)
- External API latency (per service)
- Cache hit/miss rates
- Active users
- Offers generated
- Error counts by type

**MetricsCollector Class:**
- `track_tool_execution()`: Track tool performance
- `track_external_api_call()`: Track API latency
- `track_cache_hit/miss()`: Track cache performance
- `get_cache_hit_rate()`: Calculate hit rate
- `track_active_user()`: Track user activity
- `track_offer_generated()`: Track business metrics
- `track_error()`: Track error occurrences

**Middleware:**
- `MetricsMiddleware`: Tracks all HTTP requests
- Logs request duration and status codes

**Integration Points:**
- Search endpoint: Tracks execution time, cache hits/misses, active users
- Risk analysis endpoint: Tracks execution time, cache performance
- Draft offer endpoint: Tracks offer generation
- RentCast client: Tracks external API latency

## Configuration

### Environment Variables

Added to `.env.example`:
```bash
# Monitoring (Sentry)
SENTRY_DSN=your_sentry_dsn_here
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

### Dependencies

Added to `requirements.txt`:
- `sentry-sdk[fastapi]==1.39.1`
- `slowapi==0.1.9`

## Usage Examples

### Raising Custom Exceptions

```python
from api.exceptions import ExternalServiceError

raise ExternalServiceError(
    "rentcast",
    "Failed to fetch property data",
    details={"property_id": "123"}
)
```

### Adding Sentry Context

```python
from api.monitoring import set_user_context, set_tool_context, add_breadcrumb

set_user_context(user_id="user_123", email="user@example.com")
set_tool_context("search_properties", location="Baltimore", max_price=400000)
add_breadcrumb("Starting property search", category="tool")
```

### Tracking Metrics

```python
from api.metrics import metrics

# Track tool execution
metrics.track_tool_execution("search_properties", duration_ms=250, success=True)

# Track cache hit
metrics.track_cache_hit("search:user_123:abc123")

# Track offer generation
metrics.track_offer_generated("user_123", "prop_456", 350000)
```

### Applying Rate Limits

```python
from api.rate_limit import limiter

@router.post("/my-endpoint")
@limiter.limit("10/minute")
async def my_endpoint():
    ...
```

## Logging Format

All logs include structured extra data:
```python
logger.info(
    "Tool execution complete",
    extra={
        "metric_type": "tool_execution",
        "tool_name": "search_properties",
        "duration_ms": 250,
        "success": True
    }
)
```

## Production Considerations

### Metrics Export

The current implementation logs metrics. For production:
1. Integrate with Datadog using `datadog` library
2. Or integrate with CloudWatch using `boto3`
3. Uncomment the statsd examples in `api/metrics.py`

### Rate Limiting Storage

Current implementation uses in-memory storage. For production:
1. Change to Redis storage: `storage_uri="redis://localhost:6379"`
2. Ensures rate limits work across multiple instances

### Sentry Configuration

1. Set `SENTRY_DSN` environment variable
2. Adjust sampling rates based on traffic volume
3. Configure alerts in Sentry dashboard

## Testing

To test error handling:
```bash
# Test validation error
curl -X POST http://localhost:8000/tools/search \
  -H "Content-Type: application/json" \
  -d '{"location": ""}'  # Invalid empty location

# Test rate limiting (send 11 requests quickly)
for i in {1..11}; do
  curl -X POST http://localhost:8000/tools/search \
    -H "Content-Type: application/json" \
    -d '{"location": "Baltimore, MD", "max_price": 400000, "user_id": "test"}'
done
```

## Monitoring Dashboard

Key metrics to monitor:
- Tool execution time (p50, p95, p99)
- External API latency by service
- Cache hit rate (target: >70%)
- Error rate by type
- Rate limit violations
- Active users
- Offers generated per day

## Requirements Satisfied

- ✅ 6.4: Graceful degradation for API failures
- ✅ 6.6: Error handling, monitoring, and rate limiting
- ✅ 7.6: Secure error logging without exposing PII
