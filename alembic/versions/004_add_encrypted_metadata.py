"""Add encrypted metadata to transactions.

Revision ID: 004
Revises: 003
Create Date: 2025-01-14 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add encrypted_metadata column to transactions table."""
    op.add_column(
        'transactions',
        sa.Column('encrypted_metadata', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Remove encrypted_metadata column from transactions table."""
    op.drop_column('transactions', 'encrypted_metadata')
