# Repository Index - Counter AI Real Estate Broker

## 📋 Overview

**Counter AI Real Estate Broker** is a voice-first AI buyer's agent system with intelligent escrow automation for real estate transactions. The platform enables self-represented home buyers to search properties, schedule viewings, analyze risks, draft purchase offers, and manage the entire escrow process through automated multi-agent coordination.

### Key Features
- **Voice-First AI Agent**: Natural language property search and analysis via Vapi.ai integration
- **Intelligent Escrow Agents**: Automated transaction management with milestone-based fund releases
- **Smart Contract Wallets**: Secure fund management via Agentic Stripe
- **Blockchain Audit Trail**: Immutable transaction logging per AP2 mandates
- **Multi-Agent Coordination**: Automated verification workflows (title, inspection, appraisal, lending)
- **Real-Time Notifications**: Multi-channel updates (email, SMS, webhooks)

---

## 🏗️ Architecture

### Tech Stack
- **Backend Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL (Supabase with connection pooling)
- **Cache**: Redis (Upstash/Redis Cloud)
- **ORM**: SQLAlchemy 2.0.23
- **Migrations**: Alembic 1.13.0
- **Voice API**: Vapi.ai with Twilio integration
- **Authentication**: JWT with python-jose
- **Monitoring**: Sentry SDK, Prometheus metrics
- **Deployment**: Vercel (serverless functions)

### Project Structure
```
realtorAIYC-main/
├── agents/              # Verification agents (title, inspection, appraisal, lending)
├── api/                 # FastAPI routes and endpoints
│   ├── escrow/         # Escrow transaction APIs
│   └── tools/          # AI agent tool endpoints
├── models/             # SQLAlchemy database models
├── services/           # External service integrations
├── workflows/          # State machines and workflow orchestration
├── config/             # Application configuration
├── scripts/            # Utility and setup scripts
├── tests/              # Test suite
└── docs/               # Documentation
```

---

## 📦 Core Components

### 1. Models (`models/`)

#### Database Models
- **Transaction** (`transaction.py`): Escrow transaction entity
  - States: `INITIATED`, `FUNDED`, `VERIFICATION_IN_PROGRESS`, `VERIFICATION_COMPLETE`, `SETTLEMENT_PENDING`, `SETTLED`, `DISPUTED`, `CANCELLED`
  - Fields: buyer_agent_id, seller_agent_id, property_id, earnest_money, total_purchase_price, wallet_id
  - Relationships: verification_tasks, payments, settlement, blockchain_events

- **VerificationTask** (`verification.py`): Verification task assignments
  - Types: `TITLE_SEARCH`, `INSPECTION`, `APPRAISAL`, `LENDING`
  - Status: `ASSIGNED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `CANCELLED`
  - Links to VerificationReport

- **VerificationReport** (`verification.py`): Agent-submitted verification reports
  - Status: `APPROVED`, `REJECTED`, `NEEDS_REVIEW`
  - Contains findings, documents, reviewer_notes

- **Payment** (`payment.py`): Payment transaction records
  - Types: `EARNEST_MONEY`, `VERIFICATION`, `COMMISSION`, `CLOSING_COST`, `SETTLEMENT`
  - Status: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED`
  - Links to blockchain transaction hash

- **Settlement** (`settlement.py`): Final settlement records
  - Contains seller_amount, agent commissions, closing_costs, distributions
  - Blockchain transaction hash for audit

- **BlockchainEvent** (`settlement.py`): On-chain event logs
  - Immutable audit trail per AP2 mandates
  - Links events to transactions with blockchain tx hash

- **User** (`user.py`): Buyer profiles and preferences
  - Encrypted PII (phone, email)
  - Preferences: locations, budget, property types
  - Google Calendar integration tokens

#### Base Models
- **BaseModel**: Common fields (id, created_at, updated_at) with UUID primary keys
- **EncryptedString**: Custom SQLAlchemy type for PII encryption at rest

---

### 2. Services (`services/`)

#### Payment & Wallet Services
- **agentic_stripe_client.py**: Smart contract wallet management
  - `create_wallet()`: Create escrow wallet with initial deposit
  - `configure_milestones()`: Set milestone-based release conditions
  - `release_milestone_payment()`: Release payment upon milestone completion
  - `execute_final_settlement()`: Distribute funds to all parties

- **smart_contract_wallet_manager.py**: High-level wallet orchestration
  - Wraps Agentic Stripe client
  - Manages transaction-to-wallet relationships
  - Handles milestone configuration and releases

- **blockchain_client.py**: Blockchain audit trail logging
  - `log_event()`: Log transaction events on-chain
  - `get_audit_trail()`: Retrieve immutable event history
  - `verify_event()`: Verify event authenticity
  - Circuit breaker pattern for resilience

- **blockchain_logger.py**: Abstraction layer for blockchain logging
  - Event types: `TRANSACTION_INITIATED`, `EARNEST_MONEY_DEPOSITED`, `VERIFICATION_TASK_ASSIGNED`, `VERIFICATION_COMPLETED`, `PAYMENT_RELEASED`, `SETTLEMENT_EXECUTED`, `DISPUTE_RAISED`, `DISPUTE_RESOLVED`, `TRANSACTION_CANCELLED`
  - Async processing support
  - Database persistence of blockchain events

#### External API Clients
- **rentcast_client.py**: Property listings and data
- **fema_client.py**: Flood zone information
- **apify_client.py**: Zillow agent scraper
- **docusign_client.py**: Contract generation and e-signature
- **calendar_client.py**: Google Calendar appointment scheduling
- **crime_client.py**: Crime statistics (CrimeoMeter)

#### Infrastructure Services
- **cache_client.py**: Redis caching layer
- **workflow_cache.py**: Workflow state caching
- **encryption_service.py**: PII encryption/decryption
- **key_management.py**: AWS KMS integration
- **circuit_breaker.py**: Resilience patterns (Opossum-style)
- **retry_utils.py**: Exponential backoff retry logic
- **notification_service.py**: Multi-channel notifications (email, SMS)
- **notification_engine.py**: Notification orchestration
- **notification_queue.py**: Async notification queue

---

### 3. Agents (`agents/`)

#### Base Agent
- **base_verification_agent.py**: `VerificationAgent` abstract base class
  - Abstract methods: `verify()`, `submit_report()`
  - Common agent lifecycle management

#### Specialized Agents
- **title_search_agent.py**: `TitleSearchAgent`
  - Performs title searches and lien checks
  - Verifies property ownership chain

- **inspection_agent.py**: `InspectionAgent`
  - Coordinates property inspections
  - Reviews inspection reports
  - Flags issues and required repairs

- **appraisal_agent.py**: `AppraisalAgent`
  - Coordinates property appraisals
  - Validates property valuation
  - Depends on inspection completion

- **lending_agent.py**: `LendingAgent`
  - Coordinates mortgage approval
  - Validates buyer financing
  - Depends on title search and appraisal

- **escrow_agent_orchestrator.py**: `EscrowAgentOrchestrator`
  - **Central orchestrator** for escrow lifecycle
  - Methods:
    - `initiate_transaction()`: Create transaction, wallet, deposit earnest money
    - `create_verification_workflow()`: Assign verification tasks to agents
    - `process_verification_completion()`: Handle report submission, release payments
    - `execute_settlement()`: Final fund distribution
    - `handle_dispute()`: Dispute resolution workflow
    - `cancel_transaction()`: Cancel and refund

---

### 4. Workflows (`workflows/`)

#### State Machine
- **state_machine.py**: `TransactionStateMachine`
  - Manages transaction state transitions with validation
  - Valid transitions:
    ```
    INITIATED → FUNDED → VERIFICATION_IN_PROGRESS → VERIFICATION_COMPLETE → SETTLEMENT_PENDING → SETTLED
                                                          ↓                    ↓
                                                    DISPUTED ←────────────────┘
                                                          ↓
                                                    CANCELLED
    ```
  - Transition guards enforce business rules
  - Event emission for state changes

#### Workflow Engine
- **workflow_engine.py**: `WorkflowEngine`
  - Orchestrates verification workflows
  - Task assignment and execution
  - Parallel task execution support
  - Deadline monitoring and escalation
  - Retry logic with exponential backoff
  - Workflow state caching

#### Verification Workflow
- **verification_workflow.py**: `VerificationWorkflow`
  - Defines task dependencies
  - Task deadline calculation
  - Progress tracking
  - Completion validation

---

### 5. API Endpoints (`api/`)

#### Main Application
- **main.py**: FastAPI application entry point
  - OpenAPI documentation configuration
  - Middleware setup (CORS, rate limiting, metrics, structured logging)
  - Router registration
  - Health check endpoints

#### Escrow APIs (`api/escrow/`)
- **transactions.py**: Transaction lifecycle management
  - `POST /api/escrow/transactions/initiate`: Create new transaction
  - `GET /api/escrow/transactions/{transaction_id}`: Get transaction details
  - `GET /api/escrow/transactions/{transaction_id}/state`: Get comprehensive state
  - `POST /api/escrow/transactions/{transaction_id}/cancel`: Cancel transaction

- **verifications.py**: Verification task management
  - `POST /api/escrow/transactions/{transaction_id}/verifications/workflow`: Create workflow
  - `POST /api/escrow/verifications/{task_id}/complete`: Submit verification report
  - `GET /api/escrow/transactions/{transaction_id}/verifications`: List tasks
  - `GET /api/escrow/transactions/{transaction_id}/overdue`: Check overdue tasks

- **payments.py**: Payment processing
  - `GET /api/escrow/transactions/{transaction_id}/payments`: List payments
  - `POST /api/escrow/payments/{payment_id}/retry`: Retry failed payment

- **settlements.py**: Settlement execution
  - `POST /api/escrow/transactions/{transaction_id}/settlement/execute`: Execute settlement
  - `GET /api/escrow/transactions/{transaction_id}/settlement/preview`: Calculate settlement

- **audit.py**: Blockchain audit trail
  - `GET /api/escrow/transactions/{transaction_id}/audit`: Get audit trail
  - `GET /api/escrow/events/{event_id}/verify`: Verify event

- **disputes.py**: Dispute management
  - `POST /api/escrow/transactions/{transaction_id}/disputes`: Raise dispute
  - `POST /api/escrow/disputes/{dispute_id}/resolve`: Resolve dispute
  - `GET /api/escrow/disputes/{dispute_id}/audit`: Get dispute audit trail

- **wallet_security.py**: Smart contract wallet security
  - `GET /api/escrow/wallets/{wallet_id}/security`: Get security status
  - `POST /api/escrow/wallets/{wallet_id}/freeze`: Freeze wallet (emergency)
  - `POST /api/escrow/wallets/{wallet_id}/unfreeze`: Unfreeze wallet

#### AI Agent Tools (`api/tools/`)
- **search.py**: Property search
  - `POST /tools/search`: Search properties by criteria

- **analyze_risk.py**: Risk analysis
  - `POST /tools/analyze-risk`: Analyze property risks (flood, crime, etc.)

- **schedule.py**: Viewing scheduler
  - `POST /tools/schedule`: Schedule property viewing

- **draft_offer.py**: Offer generation
  - `POST /tools/draft-offer`: Generate purchase offer

#### Other APIs
- **auth_endpoints.py**: Authentication (JWT)
- **users.py**: User management
- **webhooks.py**: External service webhooks (Vapi, Agentic Stripe, etc.)
- **health.py**: Health checks (liveness, readiness, dependencies)
- **escrow_metrics.py**: Escrow-specific metrics

---

### 6. Configuration (`config/`)

#### Settings
- **settings.py**: `Settings` (Pydantic)
  - Database URL (PostgreSQL)
  - External API keys (RentCast, FEMA, Apify, DocuSign, OpenAI, etc.)
  - Redis URL
  - Encryption key
  - TLS/SSL configuration
  - AWS KMS configuration
  - Agentic Stripe credentials
  - Blockchain RPC URL and contract address
  - Circuit breaker thresholds
  - Sentry DSN

#### TLS Configuration
- **tls_config.py**: TLS/SSL certificate management

---

### 7. Middleware & Infrastructure (`api/`)

- **middleware.py**: Request middleware
  - `EscrowMetricsMiddleware`: Escrow-specific metrics collection

- **rate_limit.py**: Rate limiting configuration
  - 1000 requests per 15 minutes per user

- **metrics.py**: Prometheus metrics
  - HTTP request metrics
  - Transaction state metrics
  - Payment metrics

- **monitoring.py**: Sentry integration
  - Error tracking
  - Performance monitoring
  - Circuit breaker management

- **structured_logging.py**: Structured logging
  - JSON logging in production
  - Correlation ID middleware
  - Request/response logging

- **exceptions.py**: Exception handlers
  - Custom exception classes
  - HTTP exception mapping

---

## 🔄 Transaction Lifecycle

### 1. Initiation
- Buyer agent initiates transaction via API
- Escrow orchestrator creates transaction record
- Smart contract wallet created via Agentic Stripe
- Earnest money deposited into wallet
- Transaction state: `INITIATED` → `FUNDED`
- Blockchain event: `TRANSACTION_INITIATED`, `EARNEST_MONEY_DEPOSITED`

### 2. Verification Phase
- Verification workflow created with 4 tasks:
  1. **Title Search** (5 days, $1,200)
  2. **Inspection** (7 days, $500)
  3. **Appraisal** (5 days, $400, depends on inspection)
  4. **Lending** (10 days, $0, depends on title & appraisal)
- Tasks assigned to specialized agents
- Milestones configured in smart contract wallet
- Transaction state: `FUNDED` → `VERIFICATION_IN_PROGRESS`
- Blockchain events: `VERIFICATION_TASK_ASSIGNED` (for each task)

### 3. Task Completion
- Agent completes verification and submits report
- Orchestrator processes completion:
  - Updates task status to `COMPLETED`
  - If report approved and payment amount > 0, releases milestone payment
  - Logs `VERIFICATION_COMPLETED` and `PAYMENT_RELEASED` on blockchain
  - Checks if all verifications complete
- When all complete: `VERIFICATION_IN_PROGRESS` → `VERIFICATION_COMPLETE`
- If all approved: `VERIFICATION_COMPLETE` → `SETTLEMENT_PENDING`

### 4. Settlement
- Orchestrator validates all verifications approved
- Calculates settlement amounts:
  - Seller amount = purchase_price - commissions - closing_costs
  - Buyer agent commission (3%)
  - Seller agent commission (3%)
  - Closing costs (verification payments + 1% of purchase price)
- Executes final settlement via smart contract wallet
- Funds distributed to seller, agents, service providers
- Transaction state: `SETTLEMENT_PENDING` → `SETTLED`
- Blockchain event: `SETTLEMENT_EXECUTED`

### 5. Dispute Handling
- Any party can raise dispute
- Transaction state transitions to `DISPUTED`
- Fund releases frozen
- Audit trail provided for resolution
- Resolution options: continue, cancel, retry_verification, adjust_settlement
- Blockchain events: `DISPUTE_RAISED`, `DISPUTE_RESOLVED`

---

## 🗄️ Database Schema

### Key Tables
- `transactions`: Escrow transactions
- `verification_tasks`: Verification task assignments
- `verification_reports`: Agent-submitted reports
- `payments`: Payment transaction records
- `settlements`: Final settlement records
- `blockchain_events`: On-chain event logs
- `users`: Buyer profiles
- `search_history`: Property search history
- `risk_analyses`: Risk analysis results
- `viewings`: Scheduled property viewings
- `offers`: Purchase offers

### Relationships
- Transaction → VerificationTasks (1:N)
- VerificationTask → VerificationReport (1:1)
- Transaction → Payments (1:N)
- Transaction → Settlement (1:1)
- Transaction → BlockchainEvents (1:N)
- User → SearchHistory (1:N)
- User → RiskAnalyses (1:N)
- User → Viewings (1:N)
- User → Offers (1:N)

---

## 🔐 Security Features

- **Encryption**: PII encrypted at rest using Fernet (cryptography library)
- **JWT Authentication**: Token-based authentication with refresh tokens
- **Rate Limiting**: 1000 requests per 15 minutes
- **TLS/SSL**: TLS 1.3 encryption for all communications
- **Multi-Signature**: Smart contract wallets support multi-sig for large settlements
- **Circuit Breakers**: Resilience patterns for external service calls
- **Input Validation**: Pydantic models and Zod schemas
- **Helmet**: Security headers middleware

---

## 📊 Performance & Monitoring

### Metrics
- HTTP request metrics (latency, status codes)
- Transaction state distribution
- Payment processing metrics
- Verification task completion times
- Cache hit rates
- Circuit breaker states

### Observability
- **Sentry**: Error tracking and performance monitoring
- **Structured Logging**: JSON logs in production
- **Correlation IDs**: Request tracing across services
- **Health Checks**: Liveness, readiness, dependency checks

### Caching
- **Redis**: Workflow state caching (5-minute TTL)
- **Transaction State**: Cached for fast retrieval
- **Verification Reports**: Cached after submission

---

## 🧪 Testing

### Test Suite (`tests/`)
- `test_escrow_end_to_end.py`: Full escrow workflow tests
- `test_offer_integration.py`: Offer generation tests
- `test_risk_analysis_integration.py`: Risk analysis tests
- `test_search_integration.py`: Property search tests
- `test_agentic_stripe_integration.py`: Wallet management tests
- `test_blockchain_integration.py`: Blockchain logging tests
- `test_database_operations.py`: Database operation tests
- `test_workflow_engine_integration.py`: Workflow engine tests

### Test Configuration
- **pytest.ini**: Pytest configuration
- **conftest.py**: Shared test fixtures

---

## 🚀 Deployment

### Production Setup
- **Hosting**: Vercel (serverless functions)
- **Database**: Supabase PostgreSQL with connection pooling
- **Cache**: Upstash Redis or Redis Cloud
- **Voice**: Vapi.ai with Twilio phone numbers
- **Environment Variables**: Configured via Vercel dashboard

### Deployment Scripts
- `scripts/deploy.sh`: Deployment automation
- `scripts/setup_database.sh`: Database initialization
- `scripts/setup_redis.sh`: Redis setup
- `scripts/load_demo_data.py`: Demo data generation
- `scripts/update_vapi_config.py`: Vapi configuration updates

### Demo Setup
- Demo user creation (phone: +14105551234)
- 10 sample Baltimore properties ($299k-$525k)
- Demo script generation for voice interactions

---

## 📚 Documentation (`docs/`)

- **API_DOCUMENTATION.md**: Complete API reference
- **deployment_guide.md**: Production deployment walkthrough
- **vapi_setup_guide.md**: Voice API configuration
- **ESCROW_AGENTS_DESIGN.md**: Agent architecture design
- **SECURITY_FEATURES.md**: Security implementation details
- **MONITORING_OBSERVABILITY.md**: Monitoring setup
- **NOTIFICATION_SYSTEM.md**: Notification architecture

---

## 🔗 External Integrations

### APIs & Services
- **RentCast**: Property listings
- **FEMA**: Flood zone data
- **Apify**: Zillow scraping
- **DocuSign**: E-signatures
- **Google Calendar**: Appointment scheduling
- **OpenAI**: Property summaries
- **SendGrid/Gmail**: Email notifications
- **Twilio**: SMS notifications
- **CrimeoMeter**: Crime statistics
- **Vapi.ai**: Voice interface
- **Agentic Stripe**: Smart contract wallets
- **Blockchain RPC**: Audit trail logging

---

## 🎯 Key Design Patterns

1. **Microservices Architecture**: Service-oriented design with clear boundaries
2. **State Machine**: Transaction state management with validation
3. **Agent Pattern**: Specialized verification agents
4. **Orchestrator Pattern**: Central coordination of multi-agent workflows
5. **Repository Pattern**: Database abstraction layer
6. **Circuit Breaker**: Resilience for external services
7. **Event-Driven**: Blockchain event logging for audit trail
8. **CQRS**: Command/Query separation for transactions
9. **Retry with Exponential Backoff**: Automatic retry logic
10. **Caching Strategy**: Redis for workflow state and transaction data

---

## 📝 Notes

- **AP2 Compliance**: Blockchain audit trail logging per AP2 mandates
- **Closing Cycle**: Target 7-14 days (vs traditional 30-45 days)
- **Automation**: 80% reduction in manual coordination tasks
- **Transparency**: Real-time status updates to all parties
- **Voice-First**: Primary interface via Vapi.ai voice calls
- **Agentic Payments**: Smart contract wallets for secure fund management

---

*Last Updated: November 15, 2025*
*Repository: realtorAIYC-main*


