# Complete File List - Counter AI Real Estate Broker

This document provides a comprehensive list of all files in the project, organized by directory structure. This is useful for understanding the codebase architecture and for AI tools like Perplexity to navigate the project.

---

## 📁 Root Directory Files

### Configuration & Setup Files
- `alembic.ini` - Alembic database migration configuration
- `pytest.ini` - Pytest testing configuration
- `requirements.txt` - Python dependencies
- `vercel.json` - Vercel deployment configuration

### Documentation Files
- `README.md` - Main project README
- `REPOSITORY_INDEX.md` - Comprehensive repository index and architecture overview
- `IMPLEMENTATION_SUMMARY.md` - Implementation summary
- `PRODUCTION_CHECKLIST.md` - Production deployment checklist
- `DEMO_DATA_README.md` - Demo data documentation
- `DEMO_QUICK_START.md` - Quick start guide for demos
- `DEMO_SCRIPT.md` - Demo script documentation
- `DEPLOYMENT_SUMMARY.md` - Deployment summary
- `VAPI_QUICK_REFERENCE.md` - Vapi.ai quick reference guide

### JSON Configuration Files
- `demo_properties.json` - Demo property data
- `vapi_assistant_config.json` - Vapi.ai assistant configuration
- `vapi_complete_config.json` - Complete Vapi.ai configuration
- `vapi_filler_phrases_config.json` - Vapi.ai filler phrases configuration
- `vapi_interruption_config.json` - Vapi.ai interruption handling configuration
- `vapi_tools_config.json` - Vapi.ai tools configuration
- `vapi_twilio_integration.json` - Vapi.ai Twilio integration configuration

---

## 🤖 Agents Directory (`agents/`)

### Core Agent Files
- `__init__.py` - Package initialization
- `base_verification_agent.py` - Abstract base class for verification agents
- `escrow_agent_orchestrator.py` - Main orchestrator for escrow transactions
- `title_search_agent.py` - Title search verification agent
- `inspection_agent.py` - Property inspection verification agent
- `appraisal_agent.py` - Property appraisal verification agent
- `lending_agent.py` - Lending/mortgage verification agent

---

## 🗄️ Database Migration Files (`alembic/`)

### Alembic Core
- `env.py` - Alembic environment configuration
- `script.py.mako` - Alembic migration script template

### Migration Versions (`alembic/versions/`)
- `001_initial_schema.py` - Initial database schema migration
- `002_escrow_tables.py` - Escrow-related tables migration
- `003_agent_authentication.py` - Agent authentication tables migration
- `004_add_encrypted_metadata.py` - Encrypted metadata fields migration
- `005_wallet_security.py` - Wallet security features migration

---

## 🌐 API Directory (`api/`)

### Core API Files
- `__init__.py` - Package initialization
- `main.py` - FastAPI application entry point
- `auth.py` - Authentication utilities
- `auth_endpoints.py` - Authentication API endpoints
- `users.py` - User management endpoints
- `webhooks.py` - Webhook handlers for external services
- `health.py` - Health check endpoints
- `exceptions.py` - Custom exception classes and handlers

### Middleware & Infrastructure
- `middleware.py` - Request middleware (metrics, etc.)
- `rate_limit.py` - Rate limiting configuration
- `metrics.py` - Prometheus metrics collection
- `monitoring.py` - Sentry monitoring integration
- `structured_logging.py` - Structured JSON logging
- `escrow_metrics.py` - Escrow-specific metrics

### Escrow API Endpoints (`api/escrow/`)
- `__init__.py` - Package initialization
- `transactions.py` - Transaction lifecycle management endpoints
- `verifications.py` - Verification task management endpoints
- `payments.py` - Payment processing endpoints
- `settlements.py` - Settlement execution endpoints
- `audit.py` - Blockchain audit trail endpoints
- `disputes.py` - Dispute management endpoints
- `wallet_security.py` - Smart contract wallet security endpoints

### AI Agent Tools (`api/tools/`)
- `__init__.py` - Package initialization
- `search.py` - Property search tool endpoint
- `analyze_risk.py` - Risk analysis tool endpoint
- `schedule.py` - Viewing scheduler tool endpoint
- `draft_offer.py` - Offer generation tool endpoint

---

## ⚙️ Configuration Directory (`config/`)

- `__init__.py` - Package initialization
- `settings.py` - Application settings (Pydantic models)
- `tls_config.py` - TLS/SSL certificate configuration

---

## 🎭 Demo Directory (`demo/`)

- `__init__.py` - Package initialization
- `README.md` - Demo documentation
- `mock_service_client.py` - Mock service client for demos
- `mock_services.py` - Mock external services
- `payment_helper.py` - Payment helper utilities for demos
- `run_demo.py` - Demo execution script

---

## 📚 Documentation Directory (`docs/`)

### API Documentation
- `API_DOCUMENTATION.md` - Complete API reference documentation
- `API_DOCUMENTATION_SUMMARY.md` - API documentation summary
- `API_QUICK_REFERENCE.md` - Quick reference for APIs
- `ALL_APIS_REQUIRED.md` - List of all required APIs
- `REQUIRED_APIS.md` - Required API integrations

### Setup & Configuration Guides
- `database_setup.md` - Database setup instructions
- `deployment_guide.md` - Production deployment guide
- `vapi_setup_guide.md` - Vapi.ai setup guide
- `vapi_production_setup.md` - Vapi.ai production setup
- `VAPI_UPDATE_GUIDE.md` - Vapi.ai update guide
- `CREATE_VAPI_TOOLS_API.md` - Guide for creating Vapi.ai tools API
- `secondary_phone_setup.md` - Secondary phone number setup
- `DASHBOARD_CONFIGURATION.md` - Dashboard configuration guide

### Integration Guides
- `INTEGRATION_GUIDE.md` - External service integration guide
- `INTEGRATION_ANALYSIS.md` - Integration analysis
- `WEBHOOK_URLS.md` - Webhook URL configuration

### Security & Monitoring
- `SECURITY_FEATURES.md` - Security features documentation
- `SECURITY_IMPLEMENTATION_SUMMARY.md` - Security implementation summary
- `MONITORING_OBSERVABILITY.md` - Monitoring and observability setup
- `ERROR_HANDLING_RESILIENCE.md` - Error handling and resilience patterns
- `error_handling_monitoring.md` - Error handling and monitoring guide

### Design & Architecture
- `ESCROW_AGENTS_DESIGN.md` - Escrow agents architecture design
- `ESCROW_IMPLEMENTATION_EVALUATION.md` - Escrow implementation evaluation
- `PROJECT_OVERVIEW_AND_PROBLEM_STATEMENT.md` - Project overview and problem statement

### System Documentation
- `NOTIFICATION_SYSTEM.md` - Notification system architecture
- `NOTIFICATION_IMPLEMENTATION_SUMMARY.md` - Notification implementation summary
- `SUPABASE_FIX.md` - Supabase connection fix documentation
- `SUPABASE_POOLING_EXPLAINED.md` - Supabase connection pooling explanation

### Status & Checklists
- `DEMO_READINESS_CHECKLIST.md` - Demo readiness checklist
- `FINAL_READINESS_CHECK.md` - Final production readiness check
- `YOUR_API_KEYS_STATUS.md` - API keys status documentation
- `api_keys_reference.md` - API keys reference guide

### General Documentation
- `README.md` - Documentation directory README

---

## 💡 Examples Directory (`examples/`)

- `notification_usage_example.py` - Example usage of notification service

---

## 📊 Models Directory (`models/`)

### Database Models
- `__init__.py` - Package initialization
- `database.py` - Database connection and session management
- `user.py` - User model
- `transaction.py` - Transaction model
- `verification.py` - Verification task and report models
- `payment.py` - Payment model
- `settlement.py` - Settlement and blockchain event models
- `offer.py` - Offer model
- `risk_analysis.py` - Risk analysis model
- `search_history.py` - Search history model
- `viewing.py` - Viewing/appointment model
- `agent.py` - Agent model

---

## 🔧 Scripts Directory (`scripts/`)

### Setup & Configuration Scripts
- `setup_database.sh` - Database initialization script
- `setup_redis.sh` - Redis setup script
- `configure_secrets.sh` - Secrets configuration script
- `generate_encryption_key.py` - Encryption key generation script

### Migration Scripts
- `migrate.py` - Database migration script
- `load_demo_data.py` - Demo data loading script

### Vapi.ai Configuration Scripts
- `create_vapi_tools.py` - Create Vapi.ai tools configuration
- `create_vapi_tools_curl.sh` - Create Vapi.ai tools via cURL
- `create_vapi_tools_direct.sh` - Create Vapi.ai tools directly
- `send_vapi_tools.sh` - Send Vapi.ai tools configuration
- `update_vapi_config.py` - Update Vapi.ai configuration

### Testing & Verification Scripts
- `test_all_connections.py` - Test all external service connections
- `test_production.sh` - Production environment testing script
- `verify_database.py` - Database verification script
- `verify_redis.py` - Redis verification script
- `verify_setup.py` - Overall setup verification script

### Deployment & Utilities
- `deploy.sh` - Deployment automation script
- `generate_openapi_spec.py` - OpenAPI specification generator

---

## 🔌 Services Directory (`services/`)

### Payment & Wallet Services
- `__init__.py` - Package initialization
- `agentic_stripe_client.py` - Agentic Stripe client for smart contract wallets
- `smart_contract_wallet_manager.py` - High-level wallet orchestration
- `wallet_security.py` - Wallet security management

### Blockchain Services
- `blockchain_client.py` - Blockchain RPC client
- `blockchain_logger.py` - Blockchain audit trail logging service

### External API Clients
- `rentcast_client.py` - RentCast API client (property listings)
- `fema_client.py` - FEMA API client (flood zone data)
- `apify_client.py` - Apify API client (Zillow scraping)
- `docusign_client.py` - DocuSign API client (e-signatures)
- `calendar_client.py` - Google Calendar API client
- `crime_client.py` - CrimeoMeter API client (crime statistics)
- `email_client.py` - Email service client (SendGrid/Gmail)

### Infrastructure Services
- `cache_client.py` - Redis caching client
- `workflow_cache.py` - Workflow state caching service
- `encryption_service.py` - PII encryption/decryption service
- `key_management.py` - AWS KMS key management integration
- `circuit_breaker.py` - Circuit breaker pattern implementation
- `retry_utils.py` - Exponential backoff retry utilities

### Notification Services
- `notification_service.py` - Multi-channel notification service
- `notification_engine.py` - Notification orchestration engine
- `notification_queue.py` - Async notification queue

### Mock Services
- `ai_mock_verification.py` - AI-powered mock verification service for demos

---

## 🧪 Tests Directory (`tests/`)

### Test Files
- `__init__.py` - Package initialization
- `README.md` - Testing documentation
- `conftest.py` - Pytest configuration and shared fixtures
- `test_escrow_end_to_end.py` - End-to-end escrow workflow tests
- `test_offer_integration.py` - Offer generation integration tests
- `test_risk_analysis_integration.py` - Risk analysis integration tests
- `test_search_integration.py` - Property search integration tests
- `test_agentic_stripe_integration.py` - Agentic Stripe integration tests
- `test_blockchain_integration.py` - Blockchain integration tests
- `test_database_operations.py` - Database operation tests
- `test_workflow_engine_integration.py` - Workflow engine integration tests

---

## 🔄 Workflows Directory (`workflows/`)

### Workflow Engine Files
- `__init__.py` - Package initialization
- `state_machine.py` - Transaction state machine implementation
- `workflow_engine.py` - Workflow orchestration engine
- `verification_workflow.py` - Verification workflow definition

---

## 📊 File Statistics

### Total Files by Category
- **Python Files (.py)**: ~100+ files
- **Documentation Files (.md)**: ~40+ files
- **Configuration Files (.json, .ini, .sh)**: ~15+ files
- **Test Files**: ~10 files

### Total Directories
- **Main Directories**: 12
- **Subdirectories**: 5

---

## 🎯 Key File Categories

### Core Application Files
- FastAPI application: `api/main.py`
- Database models: `models/*.py`
- API endpoints: `api/*.py`, `api/escrow/*.py`, `api/tools/*.py`
- Services: `services/*.py`
- Agents: `agents/*.py`
- Workflows: `workflows/*.py`

### Configuration Files
- Application settings: `config/settings.py`
- Database migrations: `alembic/versions/*.py`
- Vapi.ai configs: `vapi_*.json`
- Deployment: `vercel.json`, `alembic.ini`, `pytest.ini`

### Documentation Files
- Architecture: `docs/ESCROW_AGENTS_DESIGN.md`, `REPOSITORY_INDEX.md`
- API docs: `docs/API_DOCUMENTATION.md`
- Setup guides: `docs/deployment_guide.md`, `docs/vapi_setup_guide.md`
- Security: `docs/SECURITY_FEATURES.md`

### Testing Files
- Test suite: `tests/test_*.py`
- Test config: `tests/conftest.py`, `pytest.ini`

### Utility Scripts
- Setup: `scripts/setup_*.sh`, `scripts/configure_*.sh`
- Migration: `scripts/migrate.py`, `scripts/load_demo_data.py`
- Verification: `scripts/verify_*.py`, `scripts/test_*.py`

---

## 📝 Notes

- All Python files follow PEP 8 style guidelines
- Database migrations use Alembic versioning system
- API endpoints are organized by feature (escrow, tools, auth)
- Services are modular and follow dependency injection patterns
- Tests use pytest framework with fixtures
- Documentation is comprehensive and covers all major components

---

*Last Updated: Generated from project structure*
*Total Files: ~165+ files across all directories*

