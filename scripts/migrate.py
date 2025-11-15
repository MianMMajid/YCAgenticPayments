#!/usr/bin/env python3
"""Database migration script."""
import sys
from alembic.config import Config
from alembic import command


def run_migrations():
    """Run database migrations."""
    alembic_cfg = Config("alembic.ini")
    
    try:
        print("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✓ Migrations completed successfully!")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)


def create_migration(message: str):
    """Create a new migration."""
    alembic_cfg = Config("alembic.ini")
    
    try:
        print(f"Creating migration: {message}")
        command.revision(alembic_cfg, message=message, autogenerate=True)
        print("✓ Migration created successfully!")
    except Exception as e:
        print(f"✗ Migration creation failed: {e}")
        sys.exit(1)


def rollback():
    """Rollback last migration."""
    alembic_cfg = Config("alembic.ini")
    
    try:
        print("Rolling back last migration...")
        command.downgrade(alembic_cfg, "-1")
        print("✓ Rollback completed successfully!")
    except Exception as e:
        print(f"✗ Rollback failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/migrate.py upgrade    - Run migrations")
        print("  python scripts/migrate.py create 'message' - Create new migration")
        print("  python scripts/migrate.py rollback   - Rollback last migration")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "upgrade":
        run_migrations()
    elif action == "create":
        if len(sys.argv) < 3:
            print("Error: Please provide a migration message")
            sys.exit(1)
        create_migration(sys.argv[2])
    elif action == "rollback":
        rollback()
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
