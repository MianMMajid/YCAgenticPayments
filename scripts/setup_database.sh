#!/bin/bash

# Counter AI - Database Setup Script
# This script helps set up the production database on Supabase

set -e  # Exit on error

echo "🗄️  Counter AI - Database Setup"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL not set${NC}"
    echo ""
    echo "Please set your Supabase connection pooling URL:"
    echo ""
    echo "  export DATABASE_URL='postgresql://postgres.[ref]:[password]@[region].pooler.supabase.com:6543/postgres'"
    echo ""
    echo "Get this URL from:"
    echo "  1. Go to your Supabase project"
    echo "  2. Settings → Database"
    echo "  3. Copy the 'Connection Pooling' URL (port 6543)"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ DATABASE_URL is set${NC}"
echo ""

# Parse database URL to extract host
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
echo "Database host: $DB_HOST"
echo ""

# Check if Alembic is installed
if ! command -v alembic &> /dev/null; then
    echo -e "${RED}❌ Alembic not found${NC}"
    echo "Install with: pip install alembic"
    exit 1
fi

echo -e "${GREEN}✓ Alembic found${NC}"
echo ""

# Test database connection
echo "Testing database connection..."
python -c "
import sys
from sqlalchemy import create_engine, text
import os

try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        version = result.fetchone()[0]
        print(f'✓ Connected to PostgreSQL')
        print(f'  Version: {version.split()[0]} {version.split()[1]}')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    sys.exit(1)
" || exit 1

echo ""

# Check current migration status
echo "Checking migration status..."
alembic current

echo ""

# Show pending migrations
echo "Pending migrations:"
alembic history

echo ""

# Ask user to confirm
read -p "Run database migrations? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled"
    exit 0
fi

echo ""
echo "Running migrations..."
echo ""

# Run migrations
alembic upgrade head

echo ""
echo -e "${GREEN}✓ Migrations completed successfully${NC}"
echo ""

# Verify tables were created
echo "Verifying tables..."
python -c "
from sqlalchemy import create_engine, inspect
import os

engine = create_engine(os.getenv('DATABASE_URL'))
inspector = inspect(engine)
tables = inspector.get_table_names()

expected_tables = ['users', 'search_history', 'risk_analyses', 'viewings', 'offers', 'alembic_version']

print('Tables found:')
for table in sorted(tables):
    if table in expected_tables:
        print(f'  ✓ {table}')
    else:
        print(f'  ? {table}')

missing = set(expected_tables) - set(tables)
if missing:
    print(f'\n❌ Missing tables: {missing}')
else:
    print(f'\n✓ All expected tables created')
"

echo ""

# Show indexes
echo "Verifying indexes..."
python -c "
from sqlalchemy import create_engine, inspect
import os

engine = create_engine(os.getenv('DATABASE_URL'))
inspector = inspect(engine)

tables = ['users', 'search_history', 'risk_analyses', 'viewings', 'offers']

for table in tables:
    indexes = inspector.get_indexes(table)
    if indexes:
        print(f'\n{table}:')
        for idx in indexes:
            cols = ', '.join(idx['column_names'])
            unique = ' (unique)' if idx.get('unique') else ''
            print(f'  - {idx[\"name\"]}: {cols}{unique}')
"

echo ""
echo -e "${GREEN}✅ Database setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Verify tables in Supabase dashboard"
echo "  2. Add DATABASE_URL to Vercel: vercel env add DATABASE_URL production"
echo "  3. Test database connectivity from your application"
echo ""
echo "Supabase Dashboard: https://app.supabase.com"
echo ""
