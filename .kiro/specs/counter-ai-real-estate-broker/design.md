# Counter AI Real Estate Broker - Design Document

## Overview

Counter is an event-driven, voice-first AI system that enables self-represented home buyers to search properties, analyze risks, schedule viewings, and generate purchase offers. The architecture uses Vapi as the orchestration layer for voice interactions, with a FastAPI backend providing specialized tools for property operations. The system maintains sub-1000ms response times through strategic caching and asynchronous processing.

### Key Design Principles

1. **Voice-First**: All interactions optimized for natural conversation flow
2. **Tool-Based Architecture**: Vapi triggers discrete FastAPI endpoints based on user intent
3. **Latency Optimization**: Filler phrases, caching, and async operations keep responses under 1 second
4. **Self-Representation Model**: AI acts as "Executive Assistant" to maintain legal compliance
5. **Fail-Safe Operations**: Graceful degradation when external APIs are unavailable

## Architecture

### High-Level System Diagram

```
┌─────────────┐
│    User     │
│  (Phone)    │
└──────┬──────┘
       │ Voice
       ▼
┌─────────────────────────────────────────┐
│           Vapi Orchestration            │
│  ┌─────────────────────────────────┐   │
│  │  GPT-4o (Intent Recognition)    │   │
│  │  Cartesia (TTS - 80ms)          │   │
│  │  Deepgram (STT - 150ms)         │   │
│  └─────────────────────────────────┘   │
└──────────┬──────────────────────────────┘
           │ Tool Calls (JSON-RPC)
           ▼
┌─────────────────────────────────────────┐
│       FastAPI Backend (Vercel)          │
│  ┌─────────────────────────────────┐   │
│  │  /tools/search                  │   │
│  │  /tools/analyze-risk            │   │
│  │  /tools/schedule                │   │
│  │  /tools/draft-offer             │   │
│  └─────────────────────────────────┘   │
└──────────┬──────────────────────────────┘
           │
           ├──────────┬──────────┬──────────┐
           ▼          ▼          ▼          ▼
    ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
    │ RentCast │ │  FEMA  │ │ Apify  │ │Docusign  │
    │   API    │ │  API   │ │Scraper │ │   API    │
    └──────────┘ └────────┘ └────────┘ └──────────┘
           │
           ▼
    ┌──────────────────────────┐
    │   PostgreSQL (User Data) │
    │   Pinecone (Vectors)     │
    └──────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | Vapi.ai | Voice conversation management, tool calling |
| **Telephony** | Twilio | SIP trunking, phone numbers |
| **Voice Synthesis** | Cartesia Sonic | Ultra-low latency TTS (<100ms) |
| **Speech Recognition** | Deepgram | Real-time STT (150ms) |
| **Intelligence** | GPT-4o | Intent recognition, reasoning |
| **Backend** | FastAPI (Python) | Tool endpoints, business logic |
| **Hosting** | Vercel/AWS Lambda | Serverless deployment |
| **Database** | PostgreSQL | User profiles, transaction history |
| **Vector Store** | Pinecone | Conversation memory, semantic search |
| **Property Data** | RentCast API | Listings, comps, tax data |
| **Agent Scraping** | Apify (Zillow) | Listing agent contact info |
| **Flood Data** | OpenFEMA API | Flood zone classifications |
| **Crime Data** | CrimeoMeter API | Neighborhood safety scores |
| **Signatures** | Docusign API | Contract generation and e-signature |

## Components and Interfaces

### 1. Voice Interface Layer (Vapi Configuration)

**Responsibility**: Manage voice conversation flow, detect intents, trigger backend tools

**Configuration Structure**:
```json
{
  "model": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "systemPrompt": "You are Counter, an executive assistant helping a home buyer..."
  },
  "voice": {
    "provider": "cartesia",
    "voiceId": "sonic-english-us"
  },
  "transcriber": {
    "provider": "deepgram",
    "model": "nova-2"
  },
  "functions": [
    {
      "name": "search_properties",
      "description": "Search for homes matching criteria",
      "parameters": {...},
      "url": "https://api.counter.app/tools/search"
    },
    {
      "name": "analyze_risk",
      "description": "Check property for red flags",
      "parameters": {...},
      "url": "https://api.counter.app/tools/analyze-risk"
    },
    {
      "name": "schedule_viewing",
      "description": "Book a property showing",
      "parameters": {...},
      "url": "https://api.counter.app/tools/schedule"
    },
    {
      "name": "draft_offer",
      "description": "Create purchase agreement",
      "parameters": {...},
      "url": "https://api.counter.app/tools/draft-offer"
    }
  ],
  "fillerPhrases": [
    "Let me check the records on that...",
    "Looking that up for you...",
    "One moment while I verify..."
  ]
}
```

**Key Features**:
- **Interruption Handling**: Vapi automatically stops TTS when user speaks
- **Filler Phrases**: Played during tool execution to mask latency
- **Context Retention**: Conversation history maintained in Vapi session

### 2. Backend API (FastAPI)

**Responsibility**: Execute property operations, integrate external services, manage data persistence

#### 2.1 Property Search Tool

**Endpoint**: `POST /tools/search`

**Request Schema**:
```python
class SearchRequest(BaseModel):
    location: str  # "Baltimore, MD"
    max_price: int  # 400000
    min_beds: Optional[int] = None
    min_baths: Optional[int] = None
    property_type: Optional[str] = None  # "single-family", "condo"
    user_id: str
```

**Response Schema**:
```python
class PropertyResult(BaseModel):
    address: str
    price: int
    beds: int
    baths: int
    sqft: int
    summary: str  # "3-bed colonial with updated kitchen"
    listing_url: str
    property_id: str

class SearchResponse(BaseModel):
    properties: List[PropertyResult]  # Max 3
    total_found: int
```

**Logic Flow**:
1. Parse location into city/state
2. Call RentCast `/listings/sale` with filters
3. Filter for `status == "Active"`
4. Sort by relevance (price proximity, bed/bath match)
5. Generate 1-sentence summary using GPT-4o-mini (fast)
6. Cache results in Redis (key: `search:{user_id}:{hash}`, TTL: 24h)
7. Return top 3 results

**Performance Target**: 200ms average response time

#### 2.2 Risk Analysis Tool

**Endpoint**: `POST /tools/analyze-risk`

**Request Schema**:
```python
class RiskRequest(BaseModel):
    property_id: str
    address: str
    list_price: int
    user_id: str
```

**Response Schema**:
```python
class RiskFlag(BaseModel):
    severity: str  # "high", "medium", "low"
    category: str  # "pricing", "flood", "tax", "crime"
    message: str  # "Property is overpriced by 12%"
    
class RiskResponse(BaseModel):
    flags: List[RiskFlag]
    overall_risk: str  # "high", "medium", "low"
```

**Logic Flow**:
1. **Parallel API Calls** (asyncio.gather):
   - RentCast: Get estimated value, tax assessment
   - FEMA: Get flood zone by lat/lon
   - CrimeoMeter: Get crime score by address
2. **Risk Rules**:
   ```python
   # Overpricing
   if list_price > estimated_value * 1.1:
       flags.append(RiskFlag(
           severity="high",
           category="pricing",
           message=f"Overpriced by {percent}%"
       ))
   
   # Flood Risk
   if flood_zone in ["AE", "VE", "A"]:
       flags.append(RiskFlag(
           severity="high",
           category="flood",
           message="Flood insurance required ($2k-5k/year)"
       ))
   
   # Tax Gap
   if tax_assessment < list_price * 0.6:
       flags.append(RiskFlag(
           severity="medium",
           category="tax",
           message="Tax bill may increase after sale"
       ))
   
   # Crime
   if crime_score > 70:  # Scale 0-100
       flags.append(RiskFlag(
           severity="medium",
           category="crime",
           message="Above-average crime rate"
       ))
   ```
3. Store analysis in PostgreSQL for user history
4. Return flags sorted by severity

**Performance Target**: 400ms (parallel API calls)

#### 2.3 Viewing Scheduler Tool

**Endpoint**: `POST /tools/schedule`

**Request Schema**:
```python
class ScheduleRequest(BaseModel):
    property_id: str
    listing_url: str  # Zillow URL
    requested_time: datetime
    user_id: str
    user_name: str
    user_email: str
```

**Response Schema**:
```python
class ScheduleResponse(BaseModel):
    status: str  # "requested", "conflict", "error"
    message: str
    calendar_event_id: Optional[str]
```

**Logic Flow**:
1. **Extract Agent Info**:
   - Call Apify Zillow scraper with `listing_url`
   - Parse agent name, email, phone from response
   - Cache agent info (key: `agent:{listing_url}`, TTL: 7d)

2. **Check Calendar Availability**:
   - Query Google Calendar API for user
   - Check for conflicts at `requested_time` ± 2 hours
   - If conflict, return alternative slots

3. **Send Email to Agent**:
   ```python
   subject = f"Showing Request: {address}"
   body = f"""
   Hi {agent_name},
   
   My client {user_name} is interested in viewing {address}.
   
   Requested Time: {requested_time.strftime('%A, %B %d at %I:%M %p')}
   Buyer Status: Pre-approved
   
   Please confirm availability or suggest alternatives.
   
   Best regards,
   Counter Assistant
   On behalf of {user_name}
   {user_email}
   """
   # Send via Gmail API or SendGrid
   ```

4. **Create Pending Calendar Event**:
   - Add to user's Google Calendar
   - Title: "Viewing: {address} (PENDING)"
   - Description: Include agent contact, lockbox code field

5. Return confirmation to user

**Performance Target**: 500ms (with cached agent data)

#### 2.4 Offer Generator Tool

**Endpoint**: `POST /tools/draft-offer`

**Request Schema**:
```python
class OfferRequest(BaseModel):
    property_id: str
    address: str
    offer_price: int
    closing_days: int  # 14, 30, 45
    financing_type: str  # "cash", "conventional", "fha"
    contingencies: List[str]  # ["inspection", "appraisal", "financing"]
    user_id: str
    user_email: str
```

**Response Schema**:
```python
class OfferResponse(BaseModel):
    status: str  # "sent", "error"
    docusign_envelope_id: str
    signing_url: str
    message: str
```

**Logic Flow**:
1. **Determine State Template**:
   - Parse state from address
   - Map to Docusign template ID:
     ```python
     TEMPLATES = {
         "MD": "template_md_purchase_agreement",
         "VA": "template_va_purchase_agreement",
         # ... other states
     }
     ```

2. **Populate Contract Fields**:
   ```python
   tabs = {
       "textTabs": [
           {"tabLabel": "PropertyAddress", "value": address},
           {"tabLabel": "PurchasePrice", "value": f"${offer_price:,}"},
           {"tabLabel": "ClosingDate", "value": closing_date.strftime("%m/%d/%Y")},
           {"tabLabel": "BuyerName", "value": user_name},
           {"tabLabel": "FinancingType", "value": financing_type.upper()},
       ],
       "checkboxTabs": [
           {"tabLabel": "InspectionContingency", "selected": "inspection" in contingencies},
           {"tabLabel": "AppraisalContingency", "selected": "appraisal" in contingencies},
       ]
   }
   ```

3. **Create Docusign Envelope**:
   ```python
   envelope = {
       "templateId": template_id,
       "status": "sent",
       "recipients": {
           "signers": [{
               "email": user_email,
               "name": user_name,
               "recipientId": "1",
               "tabs": tabs
           }]
       }
   }
   response = docusign_client.envelopes.create(account_id, envelope)
   ```

4. **Store Offer in Database**:
   - Save offer details to `offers` table
   - Link to property and user
   - Track status (draft, sent, signed, rejected)

5. Return signing URL to user

**Performance Target**: 600ms

### 3. Data Models

#### User Profile
```python
class User(Base):
    __tablename__ = "users"
    
    id: str = Column(String, primary_key=True)  # UUID
    phone_number: str = Column(String, unique=True, encrypted=True)
    email: str = Column(String, encrypted=True)
    name: str = Column(String)
    
    # Preferences
    preferred_locations: List[str] = Column(JSON)
    max_budget: int = Column(Integer)
    min_beds: int = Column(Integer)
    
    # Status
    pre_approved: bool = Column(Boolean, default=False)
    pre_approval_amount: Optional[int] = Column(Integer)
    
    # Calendar Integration
    google_calendar_token: str = Column(String, encrypted=True)
    
    created_at: datetime = Column(DateTime)
    last_active: datetime = Column(DateTime)
```

#### Property Search History
```python
class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id: str = Column(String, primary_key=True)
    user_id: str = Column(String, ForeignKey("users.id"))
    
    query: str = Column(String)  # Original voice query
    location: str = Column(String)
    max_price: int = Column(Integer)
    
    results: List[dict] = Column(JSON)  # Cached property results
    
    created_at: datetime = Column(DateTime)
```

#### Risk Analysis Cache
```python
class RiskAnalysis(Base):
    __tablename__ = "risk_analyses"
    
    id: str = Column(String, primary_key=True)
    property_id: str = Column(String, index=True)
    user_id: str = Column(String, ForeignKey("users.id"))
    
    flags: List[dict] = Column(JSON)
    overall_risk: str = Column(String)
    
    # Source Data
    estimated_value: int = Column(Integer)
    tax_assessment: int = Column(Integer)
    flood_zone: str = Column(String)
    crime_score: int = Column(Integer)
    
    created_at: datetime = Column(DateTime)
```

#### Viewing Appointments
```python
class Viewing(Base):
    __tablename__ = "viewings"
    
    id: str = Column(String, primary_key=True)
    user_id: str = Column(String, ForeignKey("users.id"))
    property_id: str = Column(String)
    
    address: str = Column(String)
    requested_time: datetime = Column(DateTime)
    
    # Agent Info
    agent_name: str = Column(String)
    agent_email: str = Column(String)
    agent_phone: str = Column(String)
    
    # Status
    status: str = Column(String)  # "requested", "confirmed", "cancelled"
    calendar_event_id: str = Column(String)
    
    created_at: datetime = Column(DateTime)
    updated_at: datetime = Column(DateTime)
```

#### Offers
```python
class Offer(Base):
    __tablename__ = "offers"
    
    id: str = Column(String, primary_key=True)
    user_id: str = Column(String, ForeignKey("users.id"))
    property_id: str = Column(String)
    
    address: str = Column(String)
    offer_price: int = Column(Integer)
    closing_days: int = Column(Integer)
    financing_type: str = Column(String)
    contingencies: List[str] = Column(JSON)
    
    # Docusign
    envelope_id: str = Column(String)
    signing_url: str = Column(String)
    
    # Status
    status: str = Column(String)  # "draft", "sent", "signed", "rejected", "accepted"
    
    created_at: datetime = Column(DateTime)
    signed_at: Optional[datetime] = Column(DateTime)
```

### 4. Vector Memory (Pinecone)

**Purpose**: Store conversation embeddings for context retrieval and personalization

**Index Structure**:
```python
# Namespace: user_{user_id}
{
    "id": "conv_{timestamp}_{turn_id}",
    "values": [0.123, -0.456, ...],  # 1536-dim embedding from text-embedding-3-small
    "metadata": {
        "user_id": "uuid",
        "timestamp": "2025-11-13T10:30:00Z",
        "user_message": "Find me a house in Baltimore",
        "assistant_response": "I found 3 properties...",
        "intent": "property_search",
        "properties_mentioned": ["123 Main St", "456 Oak Ave"]
    }
}
```

**Usage**:
- When user says "Tell me more about that house", query Pinecone for recent property mentions
- Retrieve user preferences from past conversations
- Personalize responses based on conversation history

## Error Handling

### External API Failures

**Strategy**: Graceful degradation with user notification

```python
# Example: RentCast API down
try:
    properties = rentcast_client.search(location, max_price)
except APIError as e:
    logger.error(f"RentCast API failed: {e}")
    return {
        "properties": [],
        "error": "Property search is temporarily unavailable. Please try again in a few minutes."
    }
```

**Fallback Hierarchy**:
1. **Primary**: RentCast API
2. **Fallback**: Cached results from previous searches in same area
3. **Last Resort**: Notify user of outage

### Docusign Template Errors

**Issue**: State template not found or fields mismatch

**Solution**:
```python
if state not in TEMPLATES:
    return {
        "status": "error",
        "message": f"Purchase agreements for {state} are not yet supported. Please contact support."
    }
```

### Calendar Conflicts

**Issue**: User has existing appointment at requested time

**Solution**:
```python
if has_conflict:
    alternatives = find_alternative_slots(requested_time, window_hours=48)
    return {
        "status": "conflict",
        "message": f"You have a conflict at {requested_time}. How about {alternatives[0]} or {alternatives[1]}?"
    }
```

### Agent Contact Info Not Found

**Issue**: Apify scraper fails to extract agent email

**Solution**:
```python
if not agent_email:
    return {
        "status": "manual_required",
        "message": "I couldn't find the agent's contact info. You can call the listing office directly at {office_phone}."
    }
```

## Testing Strategy

### 1. Unit Tests

**Coverage**: Individual tool functions, data models, risk calculation logic

**Framework**: pytest

**Example Tests**:
```python
def test_risk_analysis_overpricing():
    """Test that overpricing flag is raised correctly"""
    result = calculate_risk_flags(
        list_price=500000,
        estimated_value=400000,
        flood_zone="X",
        crime_score=30
    )
    assert any(f.category == "pricing" for f in result.flags)
    assert "25%" in result.flags[0].message

def test_search_filters_active_only():
    """Test that inactive listings are filtered out"""
    mock_listings = [
        {"status": "Active", "address": "123 Main"},
        {"status": "Pending", "address": "456 Oak"},
        {"status": "Active", "address": "789 Elm"}
    ]
    result = filter_active_listings(mock_listings)
    assert len(result) == 2
```

### 2. Integration Tests

**Coverage**: End-to-end tool execution with mocked external APIs

**Framework**: pytest + httpx

**Example Tests**:
```python
@pytest.mark.asyncio
async def test_search_tool_integration(test_client, mock_rentcast):
    """Test full search flow with mocked RentCast"""
    response = await test_client.post("/tools/search", json={
        "location": "Baltimore, MD",
        "max_price": 400000,
        "user_id": "test_user"
    })
    assert response.status_code == 200
    assert len(response.json()["properties"]) <= 3
```

### 3. Voice Interaction Tests

**Coverage**: Vapi conversation flows

**Approach**: Manual testing with test phone number

**Test Scenarios**:
1. **Happy Path**: "Find me a house" → Search → "Check for issues" → Risk analysis → "Make an offer"
2. **Interruption**: User interrupts during property description
3. **Clarification**: Ambiguous query requires follow-up questions
4. **Error Recovery**: API failure, graceful error message

### 4. Load Testing

**Tool**: Locust

**Scenarios**:
- 100 concurrent users searching properties
- Target: <1s p95 response time
- Database connection pooling validation

### 5. Security Testing

**Focus Areas**:
- SQL injection prevention (use parameterized queries)
- API key exposure (environment variables only)
- PII encryption (user phone, email)
- Docusign webhook signature validation

## Performance Optimization

### Latency Budget Breakdown

| Step | Target | Strategy |
|------|--------|----------|
| VAD | 10ms | Vapi built-in |
| STT | 150ms | Deepgram Nova-2 |
| LLM Decision | 400ms | GPT-4o with streaming |
| Backend Tool | 200ms | Caching, async, parallel APIs |
| TTS | 80ms | Cartesia Sonic |
| Audio Buffer | 50ms | Twilio optimization |
| **Total** | **890ms** | **Target: <1000ms** |

### Caching Strategy

```python
# Redis Cache Keys
CACHE_KEYS = {
    "property_search": "search:{user_id}:{location_hash}:{price}",  # TTL: 24h
    "agent_info": "agent:{listing_url_hash}",  # TTL: 7d
    "risk_analysis": "risk:{property_id}",  # TTL: 24h
    "user_preferences": "prefs:{user_id}",  # TTL: 30d
}
```

### Database Optimization

- **Connection Pooling**: Max 20 connections per instance
- **Indexes**: 
  - `users.phone_number` (unique)
  - `search_history.user_id, created_at` (composite)
  - `viewings.user_id, requested_time` (composite)
- **Read Replicas**: Route analytics queries to replica

### Async Processing

```python
# Parallel API calls in risk analysis
async def analyze_risk(property_id: str, address: str):
    results = await asyncio.gather(
        fetch_rentcast_data(property_id),
        fetch_fema_flood_zone(address),
        fetch_crime_score(address),
        return_exceptions=True
    )
    # Process results...
```

## Security Considerations

### 1. PII Encryption

**Approach**: Encrypt sensitive fields at rest using Fernet (symmetric encryption)

```python
from cryptography.fernet import Fernet

class EncryptedString(TypeDecorator):
    impl = String
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return cipher.encrypt(value.encode()).decode()
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return cipher.decrypt(value.encode()).decode()
        return value
```

### 2. API Key Management

**Storage**: Environment variables via Vercel secrets or AWS Secrets Manager

```python
RENTCAST_API_KEY = os.getenv("RENTCAST_API_KEY")
DOCUSIGN_INTEGRATION_KEY = os.getenv("DOCUSIGN_INTEGRATION_KEY")
```

### 3. Docusign Webhook Validation

**Purpose**: Verify webhook requests are from Docusign

```python
def validate_docusign_signature(request_body: bytes, signature: str):
    expected = hmac.new(
        DOCUSIGN_WEBHOOK_SECRET.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 4. Rate Limiting

**Tool**: slowapi (FastAPI rate limiter)

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/tools/search")
@limiter.limit("10/minute")
async def search_properties(request: SearchRequest):
    # ...
```

## Deployment Architecture

### Hosting: Vercel Serverless Functions

**Structure**:
```
/api
  /tools
    search.py          # Deployed as /api/tools/search
    analyze-risk.py    # Deployed as /api/tools/analyze-risk
    schedule.py        # Deployed as /api/tools/schedule
    draft-offer.py     # Deployed as /api/tools/draft-offer
```

**Configuration** (`vercel.json`):
```json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.11",
      "maxDuration": 10
    }
  },
  "env": {
    "DATABASE_URL": "@database-url",
    "RENTCAST_API_KEY": "@rentcast-key"
  }
}
```

### Database: Supabase (Managed PostgreSQL)

**Connection**: Use connection pooling via Supavisor

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

### Monitoring

**Tools**:
- **Vercel Analytics**: Function execution time, error rates
- **Sentry**: Error tracking and alerting
- **Datadog**: Custom metrics (API latency, cache hit rate)

**Key Metrics**:
```python
# Custom metrics to track
metrics = {
    "tool_execution_time": histogram,
    "external_api_latency": histogram,
    "cache_hit_rate": gauge,
    "active_users": gauge,
    "offers_generated": counter
}
```

## Hackathon Implementation Notes

### MVP Scope (24-48 hours)

**Must-Have**:
1. Property search with RentCast
2. Risk analysis (pricing + flood only)
3. Offer generation with Docusign template
4. Vapi voice interface with 3 tools

**Nice-to-Have**:
- Viewing scheduler (can be simulated)
- Crime data integration
- Vector memory (use simple session state instead)

### Shortcuts for Demo

1. **Hardcoded Contracts**: Upload MD purchase agreement to Docusign, manually place text fields, save as template
2. **Mock Agent Calls**: For scheduling demo, have Counter call a second phone number you control (voicemail or simple Vapi agent)
3. **Simplified Database**: Use SQLite instead of PostgreSQL for local testing
4. **Skip Calendar Integration**: Just return "Appointment requested" without actual Google Calendar API
5. **Cached Property Data**: Pre-load 10 sample properties in Baltimore to avoid RentCast rate limits

### Demo Script Flow

```
User: "Counter, find me a house in Baltimore under $400k"
→ Tool: search_properties
→ AI: "I found 123 Main Street, a 3-bed colonial for $385k..."

User: "Check for red flags"
→ Tool: analyze_risk
→ AI: "Warning: It's in a flood zone and priced 10% above comps..."

User: "Offer $350k, cash, 14 days"
→ Tool: draft_offer
→ AI: "Drafting offer... Sent to your email for signature"
```

### Testing Checklist

- [ ] Vapi responds within 1 second
- [ ] Search returns 3 properties
- [ ] Risk analysis identifies overpricing
- [ ] Docusign envelope created successfully
- [ ] Voice interruption handled gracefully
- [ ] Error message when API fails
