# Database Setup Guide

## Overview

The Counter AI Real Estate Broker uses PostgreSQL for persistent data storage with SQLAlchemy as the ORM. All sensitive user data (phone numbers, emails, calendar tokens) are encrypted at rest using Fernet symmetric encryption.

## Database Models

### User
Stores buyer profiles and preferences:
- Encrypted fields: `phone_number`, `email`, `google_calendar_token`
- Preferences: `preferred_locations`, `max_budget`, `min_beds`, `min_baths`
- Pre-approval status and amount
- Session tracking with `last_active`

### SearchHistory
Tracks property searches:
- Search parameters (location, price, beds, baths)
- Cached results (JSON)
- Links to User

### RiskAnalysis
Stores property risk assessments:
- Risk flags (JSON array)
- Overall risk level
- Source data (estimated value, tax assessment, flood zone, crime score)
- Links to User and property

### Viewing
Tracks property viewing appointments:
- Property and appointment details
- Listing agent contact info
- Status tracking (requested, confirmed, cancelled, completed)
- Calendar integration
- Links to User

### Offer
Stores purchase offers:
- Offer terms (price, closing, financing, contingencies)
- Docusign integration (envelope_id, signing_url)
- Status tracking (draft, sent, signed, rejected, accepted)
- Links to User

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/counter_db
ENCRYPTION_KEY=<generate-with-fernet>
```

To generate an encryption key:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### 3. Create Database

```bash
createdb counter_db
```

Or using psql:

```sql
CREATE DATABASE counter_db;
```

### 4. Run Migrations

```bash
python scripts/migrate.py upgrade
```

## Migration Commands

### Apply migrations
```bash
python scripts/migrate.py upgrade
```

### Create new migration
```bash
python scripts/migrate.py create "description of changes"
```

### Rollback last migration
```bash
python scripts/migrate.py rollback
```

## Database Indexes

The following indexes are created for performance:

- `users.phone_number` (unique)
- `search_history.user_id`
- `search_history.created_at`
- `risk_analyses.user_id`
- `risk_analyses.property_id`
- `risk_analyses.created_at`
- `viewings.user_id`
- `viewings.status`
- `viewings.created_at`
- `offers.user_id`
- `offers.status`
- `offers.created_at`
- `offers.envelope_id` (unique)

## Connection Pooling

The database engine is configured with:
- Pool size: 5 connections
- Max overflow: 10 connections
- Pre-ping: Enabled (verifies connections before use)

## Security Features

### Encryption at Rest
Sensitive fields are encrypted using Fernet (symmetric encryption):
- User phone numbers
- User emails
- Google Calendar tokens

### Best Practices
- Use parameterized queries (SQLAlchemy handles this)
- Store encryption key in environment variables
- Rotate encryption keys periodically
- Use connection pooling to prevent connection exhaustion
- Enable SSL for production database connections

## Usage Example

```python
from models import User, SearchHistory, get_db

# Get database session
db = next(get_db())

# Create a user
user = User(
    phone_number="+1234567890",
    email="buyer@example.com",
    name="John Doe",
    preferred_locations=["Baltimore, MD"],
    max_budget=400000,
    min_beds=3
)
db.add(user)
db.commit()

# Query users
user = db.query(User).filter(User.phone_number == "+1234567890").first()
print(user.name)  # "John Doe"

# Create search history
search = SearchHistory(
    user_id=user.id,
    location="Baltimore, MD",
    max_price=400000,
    results=[{"address": "123 Main St", "price": 385000}]
)
db.add(search)
db.commit()
```

## Troubleshooting

### Connection Issues
- Verify DATABASE_URL is correct
- Check PostgreSQL is running: `pg_isready`
- Verify user has permissions: `GRANT ALL ON DATABASE counter_db TO user;`

### Migration Errors
- Check Alembic version table: `SELECT * FROM alembic_version;`
- Reset migrations (development only): Drop database and recreate
- View migration history: `alembic history`

### Encryption Issues
- Ensure ENCRYPTION_KEY is set in environment
- Key must be valid Fernet key (44 characters, base64 encoded)
- Changing the key will make existing encrypted data unreadable
