# Documentation Index

Welcome to the Counter AI Real Estate Broker & Intelligent Escrow Agents documentation.

## Quick Start

- **[API Quick Reference](API_QUICK_REFERENCE.md)** - Quick reference card for common operations
- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference with endpoints, authentication, and examples
- **[Integration Guide](INTEGRATION_GUIDE.md)** - Step-by-step integration instructions with code examples

## API Documentation

### Core Documentation
- **[API Documentation](API_DOCUMENTATION.md)** - Full API reference
  - Authentication flow
  - All endpoints (transactions, verifications, payments, settlements, audit, disputes)
  - Request/response examples
  - Error handling
  - Rate limiting
  - Webhooks
  - SDKs and client libraries

- **[Integration Guide](INTEGRATION_GUIDE.md)** - Integration best practices
  - Getting started
  - Authentication implementation
  - Webhook setup and handling
  - Error handling patterns
  - Common integration patterns
  - Testing strategies
  - Production checklist

### Interactive Documentation

When the API server is running, access interactive documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

To generate OpenAPI specification files:
```bash
python3 scripts/generate_openapi_spec.py
```

## System Architecture

- **[Escrow Agents Design](ESCROW_AGENTS_DESIGN.md)** - Intelligent escrow system architecture
- **[Integration Analysis](INTEGRATION_ANALYSIS.md)** - External service integrations

## Features

### Escrow System
- **[Notification System](NOTIFICATION_SYSTEM.md)** - Multi-channel notification engine
- **[Notification Implementation](NOTIFICATION_IMPLEMENTATION_SUMMARY.md)** - Implementation details
- **[Security Features](SECURITY_FEATURES.md)** - Security architecture and features
- **[Security Implementation](SECURITY_IMPLEMENTATION_SUMMARY.md)** - Security implementation details
- **[Error Handling & Resilience](ERROR_HANDLING_RESILIENCE.md)** - Error handling patterns
- **[Monitoring & Observability](MONITORING_OBSERVABILITY.md)** - Monitoring and metrics

## Setup & Deployment

- **[Database Setup](database_setup.md)** - Database configuration and migrations
- **[Deployment Guide](deployment_guide.md)** - Production deployment instructions
- **[API Keys Reference](api_keys_reference.md)** - Required API keys and configuration
- **[Error Handling & Monitoring](error_handling_monitoring.md)** - Production monitoring setup

## VAPI Integration

- **[VAPI Setup Guide](vapi_setup_guide.md)** - Voice AI integration setup
- **[VAPI Production Setup](vapi_production_setup.md)** - Production VAPI configuration
- **[Secondary Phone Setup](secondary_phone_setup.md)** - Additional phone number configuration
- **[Webhook URLs](WEBHOOK_URLS.md)** - Webhook endpoint configuration

## Database

- **[Supabase Pooling](SUPABASE_POOLING_EXPLAINED.md)** - Database connection pooling
- **[Supabase Fix](SUPABASE_FIX.md)** - Common database issues and fixes

## API Endpoints Overview

### Health & Monitoring
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

### Authentication
- `POST /auth/register` - Register agent
- `POST /auth/login` - Authenticate and get token

### Escrow Transactions
- `POST /api/escrow/transactions` - Create transaction
- `GET /api/escrow/transactions` - List transactions
- `GET /api/escrow/transactions/{id}` - Get transaction details
- `DELETE /api/escrow/transactions/{id}` - Cancel transaction

### Verifications
- `GET /api/escrow/transactions/{id}/verifications` - List verification tasks
- `POST /api/escrow/transactions/{id}/verifications` - Submit verification report
- `GET /api/escrow/verifications/{id}` - Get verification details

### Payments
- `GET /api/escrow/transactions/{id}/payments` - List payments
- `GET /api/escrow/payments/{id}` - Get payment details
- `POST /api/escrow/payments/{id}/retry` - Retry failed payment

### Settlements
- `POST /api/escrow/transactions/{id}/settlement` - Execute settlement
- `GET /api/escrow/transactions/{id}/settlement` - Get settlement details

### Audit Trail
- `GET /api/escrow/transactions/{id}/audit-trail` - Get blockchain audit trail
- `POST /api/escrow/events/{hash}/verify` - Verify blockchain event

### Disputes
- `POST /api/escrow/transactions/{id}/disputes` - Raise dispute
- `GET /api/escrow/transactions/{id}/disputes` - List disputes
- `PATCH /api/escrow/disputes/{id}` - Update dispute status

### Wallet Security
- `POST /api/escrow/transactions/{id}/wallet/multisig` - Configure multi-signature
- `POST /api/escrow/transactions/{id}/wallet/timelock` - Set time lock
- `POST /api/escrow/transactions/{id}/wallet/pause` - Emergency pause

## Key Features

### Intelligent Escrow Agents
- **Automated Transaction Management**: Reduce closing cycles from 30-45 days to 7-14 days
- **Smart Contract Wallets**: Secure fund management via Agentic Stripe
- **Milestone-Based Payments**: Automatic payment release upon task completion
- **Multi-Agent Coordination**: Parallel verification workflows (title, inspection, appraisal, lending)
- **Blockchain Audit Trail**: Immutable transaction logging per AP2 mandates
- **Real-Time Notifications**: Multi-channel updates (email, SMS, webhooks)

### Security & Compliance
- JWT-based authentication with role-based access control
- TLS 1.3 encryption for all communications
- Multi-signature requirements for large settlements
- Time locks for large fund releases
- Emergency pause circuit breaker
- PII encryption at rest and in transit
- AP2 mandate compliance

### Performance & Reliability
- Circuit breaker pattern for external services
- Exponential backoff retry logic
- Redis caching for workflow state
- Prometheus metrics collection
- Structured logging with correlation IDs
- Health check endpoints

## Support

- **Email**: support@counterai.com
- **Documentation**: https://docs.counterai.com
- **API Status**: https://status.counterai.com

## Contributing

For internal development:
1. Review the [Integration Guide](INTEGRATION_GUIDE.md) for development patterns
2. Check [Error Handling & Resilience](ERROR_HANDLING_RESILIENCE.md) for error handling standards
3. Follow [Security Features](SECURITY_FEATURES.md) for security best practices
4. Use [Monitoring & Observability](MONITORING_OBSERVABILITY.md) for instrumentation

## License

Proprietary - Counter AI Real Estate Broker
