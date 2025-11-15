"""Main FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config.settings import settings
from api.exceptions import register_exception_handlers
from api.monitoring import init_sentry
from api.rate_limit import configure_rate_limiting
from api.metrics import configure_metrics
from api.structured_logging import configure_structured_logging, CorrelationIdMiddleware, get_logger

# Configure structured logging
configure_structured_logging(
    level=settings.log_level,
    enable_json=settings.environment != "development",  # Use JSON in production
    log_file=None  # Can be configured via settings if needed
)

logger = get_logger(__name__)

# Initialize Sentry error tracking
init_sentry()

# Create FastAPI app with comprehensive OpenAPI configuration
app = FastAPI(
    title="Counter AI Real Estate Broker & Intelligent Escrow Agents",
    description="""
## Overview

Voice-first AI buyer's agent system with intelligent escrow automation for real estate transactions.

### Key Features

* **Voice-First AI Agent**: Natural language property search and analysis
* **Intelligent Escrow Agents**: Automated transaction management with milestone-based fund releases
* **Smart Contract Wallets**: Secure fund management via Agentic Stripe
* **Blockchain Audit Trail**: Immutable transaction logging per AP2 mandates
* **Multi-Agent Coordination**: Automated verification workflows (title, inspection, appraisal, lending)
* **Real-Time Notifications**: Multi-channel updates (email, SMS, webhooks)

### Transaction Lifecycle

1. **Initiation**: Buyer agent deposits earnest money into smart contract wallet
2. **Verification**: Parallel execution of verification tasks by specialized agents
3. **Payment Release**: Automatic milestone payments upon task completion
4. **Settlement**: Final fund distribution to all parties
5. **Audit**: Complete on-chain transaction history for dispute resolution

### Performance Metrics

* **Closing Cycle**: 7-14 days (vs traditional 30-45 days)
* **Automation**: 80% reduction in manual coordination tasks
* **Transparency**: Real-time status updates to all parties

### Security & Compliance

* JWT-based authentication with role-based access control
* TLS 1.3 encryption for all communications
* Multi-signature requirements for large settlements
* AP2 mandate compliance for audit trails
* PII encryption at rest and in transit
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@counterai.com",
    },
    license_info={
        "name": "Proprietary",
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "authentication",
            "description": "Agent authentication and authorization"
        },
        {
            "name": "escrow-transactions",
            "description": "Transaction lifecycle management - initiate, track, and manage real estate transactions"
        },
        {
            "name": "escrow-verifications",
            "description": "Verification task management - coordinate title search, inspection, appraisal, and lending verifications"
        },
        {
            "name": "escrow-payments",
            "description": "Payment processing - milestone payments and fund releases"
        },
        {
            "name": "escrow-settlements",
            "description": "Settlement execution - final fund distribution to all parties"
        },
        {
            "name": "escrow-audit",
            "description": "Blockchain audit trail - immutable transaction history and event verification"
        },
        {
            "name": "escrow-disputes",
            "description": "Dispute management - raise and resolve transaction disputes"
        },
        {
            "name": "escrow-wallet-security",
            "description": "Smart contract wallet security - multi-signature, time locks, and emergency controls"
        },
        {
            "name": "metrics",
            "description": "System metrics and performance monitoring"
        },
        {
            "name": "tools",
            "description": "AI agent tools - property search, risk analysis, scheduling, and offer drafting"
        },
        {
            "name": "users",
            "description": "User management"
        },
        {
            "name": "webhooks",
            "description": "Webhook handlers for external service integrations"
        }
    ],
    servers=[
        {
            "url": "https://api.counterai.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.counterai.com",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Register exception handlers
register_exception_handlers(app)

# Configure rate limiting
configure_rate_limiting(app)

# Configure metrics collection
configure_metrics(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Counter AI Real Estate Broker",
        "version": "1.0.0",
        "environment": settings.environment,
        "health_endpoints": {
            "liveness": "/health/live",
            "readiness": "/health/ready",
            "startup": "/health/startup",
            "dependencies": "/health/dependencies"
        }
    }


@app.post("/admin/circuit-breakers/reset")
async def reset_circuit_breakers():
    """Reset all circuit breakers (admin endpoint)."""
    from api.monitoring import reset_circuit_breakers
    
    reset_circuit_breakers()
    
    return {
        "status": "success",
        "message": "All circuit breakers have been reset"
    }


# Add correlation ID middleware (first, so it's available for all requests)
app.add_middleware(CorrelationIdMiddleware)

# Add escrow metrics middleware
from api.middleware import EscrowMetricsMiddleware
app.add_middleware(EscrowMetricsMiddleware)

# Import and include tool routers
from api.tools import search, analyze_risk, schedule, draft_offer
from api import users
from api import webhooks
from api import auth_endpoints
from api.escrow import transactions, verifications, payments, settlements, audit, disputes
from api import escrow_metrics
from api import health

app.include_router(search.router, prefix="/tools", tags=["tools"])
app.include_router(analyze_risk.router, prefix="/tools", tags=["tools"])
app.include_router(schedule.router, prefix="/tools", tags=["tools"])
app.include_router(draft_offer.router, prefix="/tools", tags=["tools"])
app.include_router(users.router, tags=["users"])
app.include_router(webhooks.router, tags=["webhooks"])
app.include_router(auth_endpoints.router, tags=["authentication"])

# Include escrow routers
app.include_router(transactions.router, prefix="/api/escrow", tags=["escrow-transactions"])
app.include_router(verifications.router, prefix="/api/escrow", tags=["escrow-verifications"])
app.include_router(payments.router, prefix="/api/escrow", tags=["escrow-payments"])
app.include_router(settlements.router, prefix="/api/escrow", tags=["escrow-settlements"])
app.include_router(audit.router, prefix="/api/escrow", tags=["escrow-audit"])
app.include_router(disputes.router, prefix="/api/escrow", tags=["escrow-disputes"])

# Include wallet security router
from api.escrow import wallet_security
app.include_router(wallet_security.router, prefix="/api/escrow", tags=["escrow-wallet-security"])

# Include metrics and health routers
app.include_router(escrow_metrics.router, tags=["metrics"])
app.include_router(health.router, tags=["health"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
