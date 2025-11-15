#!/usr/bin/env python3
"""
Verify database setup and configuration

This script checks that the database is properly configured with all
required tables, indexes, and connection pooling.

Usage:
    export DATABASE_URL='your-supabase-url'
    python scripts/verify_database.py
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import QueuePool

def check_connection(engine):
    """Test database connection"""
    print("🔌 Testing database connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            print(f"  ✓ Connected to PostgreSQL")
            print(f"    Version: {version.split()[0]} {version.split()[1]}")
            return True
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False

def check_tables(engine):
    """Verify all required tables exist"""
    print("\n📋 Checking tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = {
        'users': 'User profiles and preferences',
        'search_history': 'Property search records',
        'risk_analyses': 'Risk analysis results',
        'viewings': 'Viewing appointments',
        'offers': 'Purchase offers',
        'alembic_version': 'Migration tracking'
    }
    
    all_present = True
    for table, description in expected_tables.items():
        if table in tables:
            print(f"  ✓ {table:20} - {description}")
        else:
            print(f"  ❌ {table:20} - MISSING")
            all_present = False
    
    return all_present

def check_indexes(engine):
    """Verify required indexes exist"""
    print("\n📊 Checking indexes...")
    inspector = inspect(engine)
    
    expected_indexes = {
        'search_history': ['ix_search_history_user_id_created_at'],
        'risk_analyses': ['ix_risk_analyses_property_id'],
        'viewings': ['ix_viewings_user_id_requested_time'],
        'offers': ['ix_offers_user_id_created_at']
    }
    
    all_present = True
    for table, expected_idx_list in expected_indexes.items():
        indexes = inspector.get_indexes(table)
        index_names = [idx['name'] for idx in indexes]
        
        for expected_idx in expected_idx_list:
            if expected_idx in index_names:
                # Get index details
                idx_info = next(idx for idx in indexes if idx['name'] == expected_idx)
                cols = ', '.join(idx_info['column_names'])
                print(f"  ✓ {expected_idx:45} ({cols})")
            else:
                print(f"  ❌ {expected_idx:45} - MISSING")
                all_present = False
    
    return all_present

def check_columns(engine):
    """Verify key columns exist"""
    print("\n🔍 Checking key columns...")
    inspector = inspect(engine)
    
    critical_columns = {
        'users': ['id', 'phone_number', 'email', 'preferred_locations', 'max_budget'],
        'search_history': ['id', 'user_id', 'query', 'results'],
        'risk_analyses': ['id', 'property_id', 'user_id', 'flags', 'overall_risk'],
        'viewings': ['id', 'user_id', 'property_id', 'requested_time', 'status'],
        'offers': ['id', 'user_id', 'property_id', 'offer_price', 'envelope_id', 'status']
    }
    
    all_present = True
    for table, expected_cols in critical_columns.items():
        columns = [col['name'] for col in inspector.get_columns(table)]
        
        missing = set(expected_cols) - set(columns)
        if missing:
            print(f"  ❌ {table}: Missing columns {missing}")
            all_present = False
        else:
            print(f"  ✓ {table}: All critical columns present")
    
    return all_present

def check_connection_pooling(database_url):
    """Verify connection pooling configuration"""
    print("\n🏊 Checking connection pooling...")
    
    # Check if using Supavisor (port 6543)
    if ':6543/' in database_url:
        print("  ✓ Using Supabase connection pooler (port 6543)")
        print("    Transaction mode pooling enabled")
        return True
    elif ':5432/' in database_url:
        print("  ⚠️  Using direct connection (port 5432)")
        print("    Consider using connection pooler for production")
        return True
    else:
        print("  ❓ Unknown port configuration")
        return False

def test_crud_operations(engine):
    """Test basic CRUD operations"""
    print("\n🧪 Testing CRUD operations...")
    
    try:
        with engine.connect() as conn:
            # Test INSERT
            conn.execute(text("""
                INSERT INTO users (id, phone_number, email, name, created_at, last_active)
                VALUES ('test-user-123', '+15555555555', 'test@example.com', 'Test User', NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """))
            conn.commit()
            print("  ✓ INSERT successful")
            
            # Test SELECT
            result = conn.execute(text("""
                SELECT id, name FROM users WHERE id = 'test-user-123'
            """))
            row = result.fetchone()
            if row:
                print(f"  ✓ SELECT successful (found: {row[1]})")
            
            # Test UPDATE
            conn.execute(text("""
                UPDATE users SET name = 'Test User Updated' WHERE id = 'test-user-123'
            """))
            conn.commit()
            print("  ✓ UPDATE successful")
            
            # Test DELETE
            conn.execute(text("""
                DELETE FROM users WHERE id = 'test-user-123'
            """))
            conn.commit()
            print("  ✓ DELETE successful")
            
            return True
    except Exception as e:
        print(f"  ❌ CRUD test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Counter AI - Database Verification")
    print("=" * 60)
    print()
    
    # Check DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print()
        print("Set it with:")
        print("  export DATABASE_URL='your-supabase-connection-url'")
        sys.exit(1)
    
    # Mask password in output
    masked_url = database_url
    if '@' in masked_url:
        parts = masked_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            masked_url = f"{user_pass[0]}:****@{parts[1]}"
    
    print(f"Database URL: {masked_url}")
    print()
    
    # Create engine with connection pooling
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True  # Verify connections before using
    )
    
    # Run checks
    checks = [
        ("Connection", lambda: check_connection(engine)),
        ("Connection Pooling", lambda: check_connection_pooling(database_url)),
        ("Tables", lambda: check_tables(engine)),
        ("Indexes", lambda: check_indexes(engine)),
        ("Columns", lambda: check_columns(engine)),
        ("CRUD Operations", lambda: test_crud_operations(engine))
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n❌ {check_name} check failed with error: {e}")
            results.append((check_name, False))
    
    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    for check_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {status:10} - {check_name}")
    
    all_passed = all(result for _, result in results)
    
    print()
    if all_passed:
        print("✅ All checks passed! Database is ready for production.")
        print()
        print("Next steps:")
        print("  1. Add DATABASE_URL to Vercel:")
        print("     vercel env add DATABASE_URL production")
        print("  2. Deploy your application")
        print("  3. Monitor database performance in Supabase dashboard")
    else:
        print("❌ Some checks failed. Please review the errors above.")
        print()
        print("Common fixes:")
        print("  - Run migrations: alembic upgrade head")
        print("  - Check database permissions")
        print("  - Verify connection URL is correct")
        sys.exit(1)
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
