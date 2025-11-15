# Implementation Plan

- [x] 1. Set up project structure and core dependencies
  - Create FastAPI project with proper directory structure (`/api/tools`, `/models`, `/services`, `/config`)
  - Install core dependencies: fastapi, uvicorn, sqlalchemy, pydantic, httpx, python-dotenv
  - Configure environment variables template (.env.example) for API keys and database URL
  - Set up vercel.json for serverless deployment configuration
  - _Requirements: 6.6_

- [x] 2. Implement database models and connection
  - [x] 2.1 Create SQLAlchemy base configuration and engine setup
    - Write database connection utility with connection pooling
    - Implement encrypted field type decorator using Fernet for PII protection
    - Create base model class with common fields (id, created_at, updated_at)
    - _Requirements: 7.6, 6.6_
  
  - [x] 2.2 Implement User model with preferences
    - Create User table with encrypted phone/email fields
    - Add preference fields (preferred_locations, max_budget, min_beds)
    - Add pre-approval status and Google Calendar token fields
    - _Requirements: 7.1, 7.2_
  
  - [x] 2.3 Implement SearchHistory, RiskAnalysis, Viewing, and Offer models
    - Create SearchHistory model with JSON results field
    - Create RiskAnalysis model with flags and source data
    - Create Viewing model with agent info and status tracking
    - Create Offer model with Docusign integration fields
    - _Requirements: 7.2, 7.3_
  
  - [x] 2.4 Create database migration script
    - Write Alembic migration to create all tables with indexes
    - Add indexes on user_id, created_at, and status fields
    - _Requirements: 7.2_

- [x] 3. Build external API client services
  - [x] 3.1 Implement RentCast API client
    - Create RentCastClient class with search_listings method
    - Implement property detail fetching with estimated value and tax data
    - Add error handling and retry logic for API failures
    - _Requirements: 1.2, 2.2, 6.1_
  
  - [x] 3.2 Implement FEMA flood zone API client
    - Create FEMAClient class to query flood zones by lat/lon
    - Parse flood zone classifications (AE, VE, A, X)
    - Add caching for flood zone lookups
    - _Requirements: 2.1, 6.2_
  
  - [x] 3.3 Implement Apify Zillow scraper client
    - Create ApifyClient class to run zillow-agent-scraper actor
    - Parse agent name, email, and phone from scraper results
    - Implement caching strategy for agent contact info
    - _Requirements: 3.1, 6.3_
  
  - [x] 3.4 Implement Docusign API client
    - Create DocusignClient class with OAuth authentication
    - Implement envelope creation method with template population
    - Add method to retrieve signing URL from envelope
    - _Requirements: 4.2, 4.3, 4.4_
  
  - [x] 3.5 Implement Google Calendar API client
    - Create CalendarClient class with OAuth token management
    - Add method to check availability at specific time slots
    - Implement event creation with pending status
    - _Requirements: 3.2, 3.6_

- [x] 4. Implement property search tool endpoint
  - [x] 4.1 Create /tools/search endpoint with request validation
    - Define SearchRequest and SearchResponse Pydantic models
    - Implement request validation for location, price, beds, baths
    - Set up endpoint routing in FastAPI
    - _Requirements: 1.1, 1.2_
  
  - [x] 4.2 Implement search logic with RentCast integration
    - Parse location string into city/state components
    - Call RentCast API with filters for active listings
    - Sort results by relevance (price proximity, bed/bath match)
    - Limit results to top 3 properties
    - _Requirements: 1.2, 1.3, 6.1_
  
  - [x] 4.3 Add property summary generation
    - Use GPT-4o-mini to generate 1-sentence property summaries
    - Include key features (beds, baths, notable amenities)
    - Format summaries for voice readability
    - _Requirements: 1.4_
  
  - [x] 4.4 Implement caching layer for search results
    - Create Redis cache key structure for searches
    - Cache results with 24-hour TTL
    - Return cached results when available
    - _Requirements: 6.5_
  
  - [x] 4.5 Store search history in database
    - Save search query and results to SearchHistory table
    - Link to user_id for history tracking
    - _Requirements: 7.2_

- [x] 5. Implement risk analysis tool endpoint
  - [x] 5.1 Create /tools/analyze-risk endpoint with request validation
    - Define RiskRequest, RiskFlag, and RiskResponse Pydantic models
    - Implement request validation for property_id, address, list_price
    - Set up endpoint routing in FastAPI
    - _Requirements: 2.1_
  
  - [x] 5.2 Implement parallel data fetching
    - Use asyncio.gather to fetch RentCast, FEMA, and CrimeoMeter data concurrently
    - Handle individual API failures gracefully
    - Set timeout of 5 seconds for external API calls
    - _Requirements: 2.1, 2.2, 2.3, 6.4_
  
  - [x] 5.3 Implement risk calculation rules
    - Create overpricing detection (list_price > estimated_value * 1.1)
    - Create flood risk detection (flood_zone in ["AE", "VE", "A"])
    - Create tax gap detection (tax_assessment < list_price * 0.6)
    - Create crime risk detection (crime_score > 70)
    - Assign severity levels (high, medium, low) to each flag
    - _Requirements: 2.4, 2.5, 2.6_
  
  - [x] 5.4 Format risk flags for voice presentation
    - Generate conversational messages for each risk flag
    - Sort flags by severity (high first)
    - Calculate overall risk level based on flag count and severity
    - _Requirements: 2.7_
  
  - [x] 5.5 Store risk analysis in database
    - Save analysis results to RiskAnalysis table
    - Include all source data for audit trail
    - Link to user_id and property_id
    - _Requirements: 7.3_

- [x] 6. Implement viewing scheduler tool endpoint
  - [x] 6.1 Create /tools/schedule endpoint with request validation
    - Define ScheduleRequest and ScheduleResponse Pydantic models
    - Implement request validation for property_id, listing_url, requested_time
    - Set up endpoint routing in FastAPI
    - _Requirements: 3.1_
  
  - [x] 6.2 Implement agent contact extraction
    - Call Apify Zillow scraper with listing URL
    - Parse agent name, email, phone from results
    - Cache agent info with 7-day TTL
    - Handle cases where agent info is not found
    - _Requirements: 3.1, 6.3_
  
  - [x] 6.3 Implement calendar availability checking
    - Query Google Calendar API for user's schedule
    - Check for conflicts at requested_time ± 2 hours
    - Generate alternative time slots if conflict exists
    - _Requirements: 3.2, 3.3_
  
  - [x] 6.4 Implement email sending to listing agent
    - Create professional email template with user details
    - Include requested time, buyer pre-approval status
    - Send via Gmail API or SendGrid
    - _Requirements: 3.4, 3.5_
  
  - [x] 6.5 Create pending calendar event
    - Add event to user's Google Calendar with "PENDING" status
    - Include agent contact info and property details in description
    - Store calendar_event_id for future updates
    - _Requirements: 3.6_
  
  - [x] 6.6 Store viewing request in database
    - Save viewing details to Viewing table
    - Track status (requested, confirmed, cancelled)
    - Link to user_id and property_id
    - _Requirements: 3.7_

- [x] 7. Implement offer generator tool endpoint
  - [x] 7.1 Create /tools/draft-offer endpoint with request validation
    - Define OfferRequest and OfferResponse Pydantic models
    - Implement request validation for all offer terms
    - Set up endpoint routing in FastAPI
    - _Requirements: 4.1_
  
  - [x] 7.2 Implement state template mapping
    - Create dictionary mapping states to Docusign template IDs
    - Parse state from property address
    - Handle unsupported states with clear error message
    - _Requirements: 4.1_
  
  - [x] 7.3 Implement contract field population
    - Map offer terms to Docusign template tabs (text, checkbox, date)
    - Format price with proper currency formatting
    - Calculate closing date from closing_days parameter
    - Map contingencies to checkbox tabs
    - _Requirements: 4.2, 4.6_
  
  - [x] 7.4 Implement Docusign envelope creation
    - Create envelope with populated template
    - Set recipient as user with email and name
    - Set envelope status to "sent"
    - Extract signing URL from response
    - _Requirements: 4.3_
  
  - [x] 7.5 Store offer in database
    - Save offer details to Offer table
    - Store Docusign envelope_id and signing_url
    - Track offer status (draft, sent, signed, rejected, accepted)
    - Link to user_id and property_id
    - _Requirements: 4.4_
  
  - [x] 7.6 Implement Docusign webhook handler
    - Create POST /webhooks/docusign endpoint
    - Validate webhook signature using HMAC
    - Update offer status when envelope is signed
    - Store signed_at timestamp
    - _Requirements: 4.5_

- [x] 8. Implement user session management
  - [x] 8.1 Create user lookup and creation endpoints
    - Implement GET /users/{phone_number} to retrieve or create user
    - Return user preferences and session data
    - _Requirements: 7.1_
  
  - [x] 8.2 Implement user preferences storage
    - Create PUT /users/{user_id}/preferences endpoint
    - Update preferred_locations, max_budget, min_beds
    - _Requirements: 7.2_
  
  - [x] 8.3 Implement conversation history retrieval
    - Create GET /users/{user_id}/history endpoint
    - Return recent searches, viewings, and offers
    - Limit to last 30 days of activity
    - _Requirements: 7.4_
  
  - [x] 8.4 Implement session timeout management
    - Update last_active timestamp on each API call
    - Mark sessions inactive after 30 days
    - _Requirements: 7.5_

- [x] 9. Implement caching and performance optimization
  - [x] 9.1 Set up Redis connection and cache utilities
    - Create Redis client with connection pooling
    - Implement cache key generation functions
    - Add cache get/set wrapper functions with TTL support
    - _Requirements: 6.5_
  
  - [x] 9.2 Add caching to property search
    - Cache search results with 24-hour TTL
    - Use location hash and price as cache key
    - Return cached results when available
    - _Requirements: 6.5_
  
  - [x] 9.3 Add caching to agent contact lookups
    - Cache agent info with 7-day TTL
    - Use listing URL hash as cache key
    - _Requirements: 6.3_
  
  - [x] 9.4 Add caching to risk analysis
    - Cache risk analysis results with 24-hour TTL
    - Use property_id as cache key
    - _Requirements: 6.5_

- [x] 10. Configure Vapi voice interface
  - [x] 10.1 Create Vapi assistant configuration
    - Set up GPT-4o model with system prompt
    - Configure Cartesia Sonic voice for TTS
    - Configure Deepgram Nova-2 for STT
    - Set temperature to 0.7 for natural responses
    - _Requirements: 5.1, 5.2_
  
  - [x] 10.2 Define tool functions in Vapi
    - Add search_properties function with parameters
    - Add analyze_risk function with parameters
    - Add schedule_viewing function with parameters
    - Add draft_offer function with parameters
    - Map each function to corresponding FastAPI endpoint URL
    - _Requirements: 5.3_
  
  - [x] 10.3 Configure filler phrases for latency masking
    - Add phrases: "Let me check the records on that..."
    - Add phrases: "Looking that up for you..."
    - Add phrases: "One moment while I verify..."
    - _Requirements: 5.3_
  
  - [x] 10.4 Configure interruption handling
    - Enable automatic TTS stopping on user speech
    - Set VAD sensitivity for quick detection
    - _Requirements: 5.5_
  
  - [x] 10.5 Set up Twilio phone number integration
    - Connect Twilio SIP trunk to Vapi
    - Configure phone number for inbound calls
    - Test call routing and audio quality
    - _Requirements: 5.1_

- [x] 11. Implement error handling and monitoring
  - [x] 11.1 Add global exception handlers
    - Create FastAPI exception handler for APIError
    - Create handler for validation errors
    - Return user-friendly error messages
    - Log all errors with stack traces
    - _Requirements: 6.4_
  
  - [x] 11.2 Implement graceful degradation for API failures
    - Return cached results when RentCast API fails
    - Skip optional data (crime) when API unavailable
    - Provide clear user messaging for outages
    - _Requirements: 6.4_
  
  - [x] 11.3 Set up Sentry error tracking
    - Initialize Sentry SDK in FastAPI app
    - Configure error sampling and environment tags
    - Add custom context (user_id, tool_name) to errors
    - _Requirements: 6.6_
  
  - [x] 11.4 Implement rate limiting
    - Add slowapi rate limiter to FastAPI
    - Set limit of 10 requests per minute per IP
    - Return 429 status with retry-after header
    - _Requirements: 6.6_
  
  - [x] 11.5 Add custom metrics and logging
    - Log tool execution time for each endpoint
    - Log external API latency
    - Track cache hit rates
    - Send metrics to Datadog or CloudWatch
    - _Requirements: 6.6_

- [x] 12. Deploy and configure production environment
  - [x] 12.1 Configure Vercel deployment
    - Set up vercel.json with Python runtime configuration
    - Configure environment variables in Vercel dashboard
    - Set function timeout to 10 seconds
    - _Requirements: 6.6_
  
  - [x] 12.2 Set up production database
    - Create Supabase PostgreSQL instance
    - Run database migrations
    - Configure connection pooling via Supavisor
    - _Requirements: 7.6_
  
  - [x] 12.3 Set up Redis cache
    - Create Redis instance (Upstash or Redis Cloud)
    - Configure connection URL in environment variables
    - Test cache connectivity
    - _Requirements: 6.5_
  
  - [x] 12.4 Configure API keys and secrets
    - Add RentCast API key to Vercel secrets
    - Add Docusign integration key and secret
    - Add Apify API token
    - Add Google Calendar OAuth credentials
    - Add encryption key for PII fields
    - _Requirements: 6.6, 7.6_
  
  - [x] 12.5 Update Vapi assistant with production URLs
    - Change tool function URLs to production domain
    - Test end-to-end voice flow in production
    - _Requirements: 5.3_

- [x] 13. Create integration tests
  - Write test for property search with mocked RentCast API
  - Write test for risk analysis with mocked external APIs
  - Write test for offer generation with mocked Docusign API
  - Write test for database operations (CRUD)
  - _Requirements: 1.2, 2.1, 4.3_

- [x] 14. Create demo data and test scenarios
  - Load 10 sample Baltimore properties into cache
  - Create test user with preferences
  - Prepare demo script for voice interaction
  - Set up secondary phone number for simulated agent calls
  - _Requirements: 1.2, 7.1_
