# Complete API Requirements - Counter AI Real Estate Broker

**Last Updated**: November 15, 2025  
**Status**: Comprehensive evaluation of all APIs needed for full system functionality

---

## Executive Summary

**Total APIs Required**: 20  
- ✅ **Fully Implemented**: 11 APIs
- ⚠️ **Partially Implemented**: 2 APIs (Stripe, Blockchain)
- ❌ **Not Implemented**: 7 APIs (Escrow verification agents + Coinbase + VAPI)
- 🔧 **Optional/Enhancement**: 3 APIs

---

## API Categories

### Category 1: Core Infrastructure (✅ Fully Implemented)

#### 1.1 Supabase PostgreSQL Database ✅
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Service**: Supabase (PostgreSQL)
- **Purpose**: Primary database for all application data
- **Environment Variable**: `DATABASE_URL`
- **Implementation**: `models/database.py`
- **Cost**: Free tier (500MB) → $25/month (Pro)
- **Documentation**: https://supabase.com/docs
- **Setup**: Connection pooling URL (port 6543)

#### 1.2 Redis Cache ✅
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Service**: Upstash Redis or Redis Cloud
- **Purpose**: Caching for property searches, risk analyses, agent info
- **Environment Variable**: `REDIS_URL`
- **Implementation**: `services/cache_client.py`
- **Cost**: Free tier (10k commands/day) → $10/month
- **Documentation**: https://docs.upstash.com/redis

---

### Category 2: Property Search & Data (✅ Fully Implemented)

#### 2.1 RentCast API ✅
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Service**: RentCast Real Estate API
- **Purpose**: Property listings, estimated values, tax assessments
- **Environment Variable**: `RENTCAST_API_KEY`
- **Implementation**: `services/rentcast_client.py`
- **Endpoints Used**:
  - `GET /listings/sale` - Search properties
  - `GET /properties/{id}` - Property details
  - `GET /avm/value` - Estimated value
- **Cost**: Free (500 req/month) → $49/month
- **Documentation**: https://developers.rentcast.io/
- **Rate Limits**: 10 req/min (free), 60 req/min (paid)

#### 2.2 FEMA API ✅ (Optional)
- **Status**: ✅ **FULLY IMPLEMENTED** (Optional)
- **Service**: FEMA Flood Zone Data
- **Purpose**: Flood risk analysis
- **Environment Variable**: `FEMA_API_KEY` (optional)
- **Implementation**: `services/fema_client.py`
- **Cost**: Free (public API)
- **Documentation**: https://www.fema.gov/about/openfema/api
- **Note**: Works without API key but has lower rate limits

#### 2.3 CrimeoMeter API ✅ (Optional)
- **Status**: ✅ **FULLY IMPLEMENTED** (Optional)
- **Service**: CrimeoMeter Crime Statistics
- **Purpose**: Crime statistics for risk analysis
- **Environment Variable**: `CRIMEOMETER_API_KEY` (optional)
- **Implementation**: `services/crime_client.py`
- **Cost**: Contact for pricing
- **Documentation**: https://www.crimeometer.com/
- **Note**: If not configured, crime analysis is skipped

---

### Category 3: Document & Contract Management (✅ Fully Implemented)

#### 3.1 DocuSign API ✅
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Service**: DocuSign eSignature API
- **Purpose**: Generate and e-sign purchase agreements
- **Environment Variables**:
  - `DOCUSIGN_INTEGRATION_KEY`
  - `DOCUSIGN_SECRET_KEY`
  - `DOCUSIGN_ACCOUNT_ID`
  - `DOCUSIGN_WEBHOOK_SECRET`
- **Implementation**: `services/docusign_client.py`, `api/webhooks.py`
- **Endpoints Used**:
  - `POST /envelopes` - Create envelope
  - `GET /envelopes/{id}` - Get envelope status
  - Webhook: Envelope events
- **Cost**: Free (sandbox) → $0.50/envelope (production)
- **Documentation**: https://developers.docusign.com/
- **Webhook URL**: `https://your-domain.com/api/webhooks/docusign`

#### 3.2 OpenAI API ✅
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Service**: OpenAI GPT API
- **Purpose**: Generate property summaries
- **Environment Variable**: `OPENAI_API_KEY`
- **Implementation**: `api/tools/search.py` (generate_property_summary)
- **Model Used**: `gpt-4o-mini`
- **Cost**: ~$0.0001 per summary (~$5/month for moderate usage)
- **Documentation**: https://platform.openai.com/docs
- **Rate Limits**: Based on tier

---

### Category 4: Communication & Scheduling (✅ Fully Implemented)

#### 4.1 Google Calendar API ✅
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Service**: Google Calendar API
- **Purpose**: Check availability and create viewing appointments
- **Environment Variables**:
  - `GOOGLE_CALENDAR_CLIENT_ID`
  - `GOOGLE_CALENDAR_CLIENT_SECRET`
- **Implementation**: `services/calendar_client.py`
- **Scopes Required**:
  - `https://www.googleapis.com/auth/calendar`
  - `https://www.googleapis.com/auth/calendar.events`
- **Cost**: Free
- **Documentation**: https://developers.google.com/calendar
- **OAuth Redirect**: `https://your-domain.com/api/auth/callback/google`

#### 4.2 SendGrid API ✅
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Service**: SendGrid Email API
- **Purpose**: Send emails to listing agents for viewing requests
- **Environment Variable**: `SENDGRID_API_KEY`
- **Implementation**: `services/email_client.py`
- **Cost**: Free (100 emails/day) → $15/month (40k emails)
- **Documentation**: https://docs.sendgrid.com/
- **Setup**: Verify sender email address

#### 4.3 Apify API ✅
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Service**: Apify Web Scraping Platform
- **Purpose**: Scrape Zillow for listing agent contact information
- **Environment Variable**: `APIFY_API_TOKEN`
- **Implementation**: `services/apify_client.py`
- **Actor Used**: `zillow-agent-scraper`
- **Cost**: Free ($5 credit/month) → $49/month
- **Documentation**: https://docs.apify.com/
- **Usage**: ~$0.01 per agent lookup

#### 4.4 Twilio API ✅ (Optional)
- **Status**: ✅ **FULLY IMPLEMENTED** (Optional)
- **Service**: Twilio SMS/Phone API
- **Purpose**: SMS notifications (optional enhancement)
- **Environment Variables**:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_PHONE_NUMBER`
- **Implementation**: `services/notification_service.py`
- **Cost**: ~$0.0075 per SMS
- **Documentation**: https://www.twilio.com/docs

---

### Category 5: Payment Processing (⚠️ CRITICAL - Not Implemented)

#### 5.1 Stripe API ⚠️ **CRITICAL - NOT IMPLEMENTED**
- **Status**: ⚠️ **NOT IMPLEMENTED** (Placeholder code only)
- **Service**: Stripe Payment Processing
- **Purpose**: Escrow payments, earnest money deposits, milestone payments, settlements
- **Current File**: `services/agentic_stripe_client.py` (all methods raise `NotImplementedError`)
- **Required Implementation**: Replace with real Stripe API
- **Environment Variables Needed**:
  - `STRIPE_SECRET_KEY` (replace `agentic_stripe_api_key`)
  - `STRIPE_PUBLISHABLE_KEY`
  - `STRIPE_WEBHOOK_SECRET` (replace `agentic_stripe_webhook_secret`)
  - `STRIPE_CONNECT_CLIENT_ID` (optional)
- **Required Stripe Features**:
  1. **Stripe Connect** - Multi-party escrow payments
  2. **Payment Intents** - Hold earnest money deposits
  3. **Transfers** - Release milestone payments
  4. **Payouts** - Final settlement distribution
  5. **Balance API** - Check wallet balance
  6. **Webhooks** - Payment status updates
- **Implementation Files**:
  - Create: `services/stripe_client.py` (replace `agentic_stripe_client.py`)
  - Update: `services/smart_contract_wallet_manager.py`
  - Update: `config/settings.py`
  - Update: `api/webhooks.py`
  - Add: `stripe==7.0.0` to `requirements.txt`
- **Cost**: 2.9% + $0.30 per transaction
- **Documentation**: 
  - https://stripe.com/docs/connect
  - https://stripe.com/docs/api
- **Priority**: 🔴 **CRITICAL** - Blocks all escrow functionality
- **Setup Steps**:
  1. Create Stripe account: https://dashboard.stripe.com/
  2. Get API keys (test mode: `sk_test_...`)
  3. Enable Stripe Connect
  4. Set webhook endpoint: `https://your-domain.com/api/webhooks/stripe`
  5. Test with Stripe test cards

#### 5.2 Coinbase Commerce API ❌ (Optional)
- **Status**: ❌ **NOT IMPLEMENTED**
- **Service**: Coinbase Commerce
- **Purpose**: Crypto payment alternative (optional)
- **File**: Does not exist (needs `services/coinbase_client.py`)
- **Environment Variables Needed**:
  - `COINBASE_API_KEY`
  - `COINBASE_API_SECRET`
  - `COINBASE_WEBHOOK_SECRET`
- **Cost**: 1% transaction fee
- **Documentation**: https://commerce.coinbase.com/
- **Priority**: 🟡 **LOW** - Optional enhancement
- **Note**: Stripe is primary, Coinbase is alternative

---

### Category 6: Escrow Verification Agents (❌ Not Implemented)

#### 6.1 Title Company API ❌
- **Status**: ❌ **NOT IMPLEMENTED** (Uses mock)
- **Service**: Title Company API (First American, Fidelity, Stewart, etc.)
- **Purpose**: Title search verification ($1,200 payment)
- **Current File**: `agents/title_search_agent.py` (mock implementation)
- **Required Implementation**: Create `services/title_company_client.py`
- **Environment Variable Needed**: `TITLE_COMPANY_API_KEY`
- **Recommended Options**:
  1. **First American Title API** (Recommended)
     - Website: https://www.firstam.com/developers
     - Cost: $50-200 per search
  2. **Fidelity National Title API**
     - Website: https://www.fntic.com/
  3. **Stewart Title API**
     - Website: https://www.stewart.com/
  4. **TitleAPI.com** (Third-party aggregator)
     - Cost: $100-300 per search
- **Endpoints Needed**:
  - `POST /title-orders` - Create title order
  - `GET /title-orders/{id}` - Get status
  - `GET /title-orders/{id}/report` - Get report
- **Priority**: 🟠 **HIGH** - Required for production
- **Update File**: `agents/title_search_agent.py:_perform_title_search()`

#### 6.2 Inspection Service API ❌
- **Status**: ❌ **NOT IMPLEMENTED** (Uses mock)
- **Service**: Inspection Service API (HomeAdvisor, Thumbtack, etc.)
- **Purpose**: Property inspection coordination ($500 payment)
- **Current File**: `agents/inspection_agent.py` (mock implementation)
- **Required Implementation**: Create `services/inspection_client.py`
- **Environment Variable Needed**: `INSPECTION_SERVICE_API_KEY`
- **Recommended Options**:
  1. **HomeAdvisor API** (Recommended)
     - Website: https://www.homeadvisor.com/developers/
     - Cost: $50-150 per inspection
  2. **Thumbtack Pro API**
     - Website: https://www.thumbtack.com/pro/
     - Cost: Commission-based (15-20%)
  3. **Porch Pro API**
     - Website: https://pro.porch.com/
  4. **Custom Inspector Marketplace** (Build your own)
- **Endpoints Needed**:
  - `POST /inspections/request` - Request inspection
  - `GET /inspections/{id}/status` - Check status
  - `GET /inspections/{id}/report` - Get report
  - `GET /inspectors/available` - Find inspectors
- **Priority**: 🟠 **HIGH** - Required for production
- **Update File**: `agents/inspection_agent.py:_perform_inspection()`

#### 6.3 Appraisal Service API ❌
- **Status**: ❌ **NOT IMPLEMENTED** (Uses mock)
- **Service**: Appraisal Management Company (AMC) API
- **Purpose**: Property appraisal coordination ($400 payment)
- **Current File**: `agents/appraisal_agent.py` (mock implementation)
- **Required Implementation**: Create `services/appraisal_client.py`
- **Environment Variable Needed**: `APPRAISAL_SERVICE_API_KEY`
- **Recommended Options**:
  1. **AMC APIs** (Recommended)
     - **AppraisalPort**: https://www.appraisalport.com/
     - **AppraisalScope**: https://www.appraisalscope.com/
     - **LenderX**: https://www.lenderx.com/
     - **Clear Capital**: https://www.clearcapital.com/
     - Cost: $300-600 per appraisal
  2. **AVM APIs** (Faster, cheaper, less accurate)
     - **CoreLogic AVM**: https://www.corelogic.com/
     - **Black Knight AVM**: https://www.blackknightinc.com/
     - Cost: $10-50 per valuation
  3. **RentCast AVM** (Already have, but not full appraisal)
     - May not meet lender requirements
- **Endpoints Needed**:
  - `POST /appraisals/order` - Order appraisal
  - `GET /appraisals/{id}/status` - Check status
  - `GET /appraisals/{id}/report` - Get report
- **Priority**: 🟠 **HIGH** - Required for production
- **Update File**: `agents/appraisal_agent.py:_perform_appraisal()`

#### 6.4 Lender API ❌
- **Status**: ❌ **NOT IMPLEMENTED** (Uses mock)
- **Service**: Lender/Mortgage API (Rocket Mortgage, Chase, etc.)
- **Purpose**: Loan status verification
- **Current File**: `agents/lending_agent.py` (mock implementation)
- **Required Implementation**: Create `services/lending_client.py`
- **Environment Variable Needed**: `LENDER_API_KEY` (or lender-specific keys)
- **Recommended Options**:
  1. **Lender-Specific APIs** (Recommended)
     - **Rocket Mortgage API**: https://developer.rocketmortgage.com/
     - **Chase Mortgage API**: https://developer.chase.com/
     - **Wells Fargo Mortgage API**: Contact for partnership
     - Cost: Free (part of loan process, partnership required)
  2. **Mortgage Broker APIs**
     - **MortgageHippo**: https://www.mortgagehippo.com/
     - **Better.com**: https://www.better.com/developers
  3. **Underwriting System APIs**
     - **Encompass API** (Ellie Mae): https://www.elliemae.com/
     - **Calyx Point**: https://www.calyxsoftware.com/
  4. **Credit Bureau APIs** (Credit data only, not full loan status)
     - **Experian**: https://developer.experian.com/
     - **Equifax**: https://developer.equifax.com/
     - **TransUnion**: https://developer.transunion.com/
     - Cost: $0.50-2.00 per credit check
- **Endpoints Needed**:
  - `GET /loans/{id}/status` - Check loan status
  - `GET /loans/{id}/underwriting` - Get underwriting status
  - `GET /loans/{id}/commitment` - Get commitment letter
- **Priority**: 🟠 **HIGH** - Required for production
- **Update File**: `agents/lending_agent.py:_verify_loan_status()`

---

### Category 7: Blockchain & Audit Trail (⚠️ Partially Implemented)

#### 7.1 Blockchain RPC API ⚠️
- **Status**: ⚠️ **PARTIALLY IMPLEMENTED** (Structure exists, needs RPC endpoint)
- **Service**: Blockchain RPC (Ethereum, Polygon, etc.)
- **Purpose**: On-chain transaction logging for AP2 compliance
- **Environment Variables**:
  - `BLOCKCHAIN_RPC_URL`
  - `BLOCKCHAIN_NETWORK` (testnet/mainnet)
  - `BLOCKCHAIN_CONTRACT_ADDRESS`
  - `BLOCKCHAIN_PRIVATE_KEY`
- **Implementation**: `services/blockchain_client.py`, `services/blockchain_logger.py`
- **Required Setup**:
  1. Choose blockchain network (Ethereum, Polygon, etc.)
  2. Deploy smart contract for event logging
  3. Get RPC endpoint (Infura, Alchemy, QuickNode, etc.)
  4. Generate wallet for signing transactions
- **RPC Provider Options**:
  1. **Infura**: https://www.infura.io/
  2. **Alchemy**: https://www.alchemy.com/
  3. **QuickNode**: https://www.quicknode.com/
  4. **Public RPC**: Free but rate-limited
- **Cost**: 
  - Free tier: 100k requests/month
  - Paid: $50-200/month
  - Gas fees: ~$0.01-0.10 per transaction
- **Documentation**: 
  - Ethereum: https://ethereum.org/en/developers/docs/
  - Polygon: https://docs.polygon.technology/
- **Priority**: 🟡 **MEDIUM** - Required for AP2 compliance
- **Note**: Can use testnet for development

---

### Category 8: Voice Interface (❌ Not Configured)

#### 8.1 VAPI.ai API ❌
- **Status**: ❌ **NOT FULLY CONFIGURED**
- **Service**: VAPI.ai Voice AI Platform
- **Purpose**: Voice interface for property search and escrow management
- **Current Configuration**: `vapi_tools_config.json` (only 4 tools)
- **Environment Variables** (from VAPI dashboard):
  - `VAPI_PRIVATE_KEY`
  - `VAPI_PUBLIC_KEY`
- **Current Tools** (4):
  1. ✅ `search_properties`
  2. ✅ `analyze_risk`
  3. ✅ `schedule_viewing`
  4. ✅ `draft_offer`
- **Missing Escrow Tools** (5):
  1. ❌ `check_escrow_status`
  2. ❌ `deposit_earnest_money`
  3. ❌ `get_milestone_status`
  4. ❌ `get_payment_history`
  5. ❌ `create_escrow_transaction`
- **Required Actions**:
  1. Add 5 escrow tools to `vapi_tools_config.json`
  2. Update VAPI assistant configuration in dashboard
  3. Test voice commands
- **Backend Endpoints**: ✅ All exist at `/api/escrow/*`
- **Cost**: VAPI pricing (contact for details)
- **Documentation**: https://docs.vapi.ai/
- **Priority**: 🟡 **MEDIUM** - Enhances user experience
- **Update File**: `vapi_tools_config.json`, `scripts/update_vapi_config.py`

#### 8.2 Twilio Phone Integration ✅ (For VAPI)
- **Status**: ✅ **CONFIGURED** (via VAPI)
- **Service**: Twilio Phone Numbers
- **Purpose**: Phone number for VAPI voice calls
- **Setup**: Configured in VAPI dashboard
- **Documentation**: `vapi_twilio_integration.json`
- **Cost**: ~$1/month per number + usage
- **Note**: Managed through VAPI, not direct integration

---

### Category 9: Security & Monitoring (✅ Fully Implemented)

#### 9.1 Encryption Service ✅
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Service**: Local encryption (Fernet)
- **Purpose**: Encrypt PII in database
- **Environment Variable**: `ENCRYPTION_KEY`
- **Implementation**: `services/encryption_service.py`
- **Generation**: `python scripts/generate_encryption_key.py`
- **Cost**: Free
- **Note**: Key rotation every 90 days recommended

#### 9.2 AWS KMS ⚠️ (Optional Enhancement)
- **Status**: ⚠️ **PLACEHOLDER ONLY**
- **Service**: AWS Key Management Service
- **Purpose**: Cloud-based key management (optional)
- **Current File**: `services/key_management.py` (placeholder)
- **Environment Variables**:
  - `KMS_ENABLED` (set to `true`)
  - `KMS_KEY_ID`
  - `KMS_REGION`
- **Cost**: $1/month per key + $0.03 per 10k requests
- **Priority**: 🟢 **LOW** - Optional enhancement
- **Note**: Current Fernet encryption is sufficient

#### 9.3 Sentry API ✅ (Optional)
- **Status**: ✅ **FULLY IMPLEMENTED** (Optional)
- **Service**: Sentry Error Monitoring
- **Purpose**: Error tracking and monitoring
- **Environment Variables**:
  - `SENTRY_DSN`
  - `SENTRY_TRACES_SAMPLE_RATE`
  - `SENTRY_PROFILES_SAMPLE_RATE`
- **Implementation**: `api/main.py` (Sentry SDK)
- **Cost**: Free tier → $26/month (Team)
- **Documentation**: https://docs.sentry.io/

---

## Complete API Summary Table

| # | API/Service | Status | Priority | Cost | Implementation File |
|---|------------|--------|----------|------|---------------------|
| **Core Infrastructure** |
| 1 | Supabase PostgreSQL | ✅ Implemented | 🔴 Critical | Free-$25/mo | `models/database.py` |
| 2 | Redis (Upstash) | ✅ Implemented | 🔴 Critical | Free-$10/mo | `services/cache_client.py` |
| **Property Data** |
| 3 | RentCast API | ✅ Implemented | 🔴 Critical | Free-$49/mo | `services/rentcast_client.py` |
| 4 | FEMA API | ✅ Implemented | 🟢 Optional | Free | `services/fema_client.py` |
| 5 | CrimeoMeter API | ✅ Implemented | 🟢 Optional | Contact | `services/crime_client.py` |
| **Documents & AI** |
| 6 | DocuSign API | ✅ Implemented | 🔴 Critical | Free-$0.50/doc | `services/docusign_client.py` |
| 7 | OpenAI API | ✅ Implemented | 🔴 Critical | ~$5/mo | `api/tools/search.py` |
| **Communication** |
| 8 | Google Calendar API | ✅ Implemented | 🔴 Critical | Free | `services/calendar_client.py` |
| 9 | SendGrid API | ✅ Implemented | 🔴 Critical | Free-$15/mo | `services/email_client.py` |
| 10 | Apify API | ✅ Implemented | 🔴 Critical | Free-$49/mo | `services/apify_client.py` |
| 11 | Twilio API | ✅ Implemented | 🟢 Optional | ~$0.0075/SMS | `services/notification_service.py` |
| **Payment Processing** |
| 12 | **Stripe API** | ⚠️ **NOT IMPLEMENTED** | 🔴 **CRITICAL** | 2.9%+$0.30 | **NEEDS: `services/stripe_client.py`** |
| 13 | Coinbase Commerce | ❌ Not Implemented | 🟡 Low | 1% fee | Needs: `services/coinbase_client.py` |
| **Escrow Verification** |
| 14 | **Title Company API** | ❌ **NOT IMPLEMENTED** | 🟠 **HIGH** | $50-200/search | **NEEDS: `services/title_company_client.py`** |
| 15 | **Inspection Service API** | ❌ **NOT IMPLEMENTED** | 🟠 **HIGH** | $50-150/inspection | **NEEDS: `services/inspection_client.py`** |
| 16 | **Appraisal Service API** | ❌ **NOT IMPLEMENTED** | 🟠 **HIGH** | $300-600/appraisal | **NEEDS: `services/appraisal_client.py`** |
| 17 | **Lender API** | ❌ **NOT IMPLEMENTED** | 🟠 **HIGH** | Free (partnership) | **NEEDS: `services/lending_client.py`** |
| **Blockchain** |
| 18 | Blockchain RPC | ⚠️ Partial | 🟡 Medium | Free-$200/mo | `services/blockchain_client.py` |
| **Voice Interface** |
| 19 | **VAPI.ai API** | ❌ **NOT CONFIGURED** | 🟡 Medium | Contact | **NEEDS: Update `vapi_tools_config.json`** |
| 20 | Twilio (VAPI) | ✅ Configured | 🟡 Medium | ~$1/mo | Via VAPI dashboard |
| **Security** |
| 21 | Encryption (Fernet) | ✅ Implemented | 🔴 Critical | Free | `services/encryption_service.py` |
| 22 | AWS KMS | ⚠️ Placeholder | 🟢 Low | $1/mo | `services/key_management.py` |
| 23 | Sentry API | ✅ Implemented | 🟢 Optional | Free-$26/mo | `api/main.py` |

---

## Critical Path to Production

### Phase 1: Critical Blockers (Must Have)
1. ✅ **Stripe API** - Implement real Stripe integration
   - Replace `services/agentic_stripe_client.py`
   - Enable escrow payments
   - **Blocks**: All payment functionality

### Phase 2: Production Requirements (High Priority)
2. ✅ **Title Company API** - Real title searches
3. ✅ **Inspection Service API** - Real inspections
4. ✅ **Appraisal Service API** - Real appraisals
5. ✅ **Lender API** - Real loan verification

### Phase 3: Enhancements (Medium Priority)
6. ✅ **Blockchain RPC** - Complete blockchain integration
7. ✅ **VAPI Escrow Tools** - Add 5 escrow voice commands

### Phase 4: Optional (Low Priority)
8. ✅ **Coinbase API** - Crypto payment alternative
9. ✅ **AWS KMS** - Cloud key management

---

## Environment Variables Summary

### Currently Required (14 variables)
```bash
# Core
DATABASE_URL
REDIS_URL
ENCRYPTION_KEY

# Property Data
RENTCAST_API_KEY
FEMA_API_KEY (optional)
CRIMEOMETER_API_KEY (optional)

# Documents
DOCUSIGN_INTEGRATION_KEY
DOCUSIGN_SECRET_KEY
DOCUSIGN_ACCOUNT_ID
DOCUSIGN_WEBHOOK_SECRET
OPENAI_API_KEY

# Communication
GOOGLE_CALENDAR_CLIENT_ID
GOOGLE_CALENDAR_CLIENT_SECRET
SENDGRID_API_KEY
APIFY_API_TOKEN
```

### Missing for Production (9 variables)
```bash
# Payment (CRITICAL)
STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET

# Escrow Verification (HIGH PRIORITY)
TITLE_COMPANY_API_KEY
INSPECTION_SERVICE_API_KEY
APPRAISAL_SERVICE_API_KEY
LENDER_API_KEY

# Blockchain (MEDIUM)
BLOCKCHAIN_RPC_URL
BLOCKCHAIN_CONTRACT_ADDRESS
BLOCKCHAIN_PRIVATE_KEY
```

### Optional (3 variables)
```bash
COINBASE_API_KEY
COINBASE_API_SECRET
COINBASE_WEBHOOK_SECRET
```

---

## Cost Estimation

### Development/Testing (Free Tier)
- **Total**: ~$0-10/month
- All services on free tiers

### Production (Moderate Usage)
- **Infrastructure**: $35/month (Supabase + Redis)
- **Property Data**: $49/month (RentCast)
- **Documents**: $50/month (DocuSign, 100 envelopes)
- **Communication**: $64/month (Apify + SendGrid)
- **AI**: $5/month (OpenAI)
- **Payment Processing**: 2.9% + $0.30 per transaction
- **Escrow Services**: $400-950 per transaction
  - Title: $50-200
  - Inspection: $50-150
  - Appraisal: $300-600
- **Blockchain**: $50-200/month (RPC + gas)
- **Voice**: VAPI pricing (contact)

**Monthly Base**: ~$200-250/month  
**Per Transaction**: $400-950 + 2.9% + $0.30

---

## Implementation Priority Matrix

| Priority | APIs | Status | Action |
|----------|------|--------|--------|
| 🔴 **CRITICAL** | Stripe API | ❌ Not Implemented | **Implement immediately** |
| 🟠 **HIGH** | Title, Inspection, Appraisal, Lender APIs | ❌ Not Implemented | **Implement for production** |
| 🟡 **MEDIUM** | Blockchain RPC, VAPI Escrow Tools | ⚠️ Partial | **Complete integration** |
| 🟢 **LOW** | Coinbase, AWS KMS | ❌ Not Implemented | **Optional enhancements** |

---

## Next Steps

1. **Immediate**: Implement Stripe API (blocks all payments)
2. **Week 1-2**: Integrate Title Company API
3. **Week 3-4**: Integrate Inspection Service API
4. **Week 5-6**: Integrate Appraisal Service API
5. **Week 7-8**: Integrate Lender API
6. **Week 9**: Complete Blockchain RPC integration
7. **Week 10**: Add VAPI escrow tools

---

**Document Version**: 1.0  
**Last Updated**: November 15, 2025  
**Total APIs**: 23 (11 implemented, 2 partial, 7 missing, 3 optional)

