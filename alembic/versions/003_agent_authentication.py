"""Add agent authentication tables.

Revision ID: 003
Revises: 002
Create Date: 2025-01-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create agents table for authentication."""
    op.create_table(
        'agents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('agent_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.LargeBinary(), nullable=False),  # Encrypted
        sa.Column('api_key_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_agents_agent_id', 'agents', ['agent_id'], unique=True)
    op.create_index('ix_agents_role', 'agents', ['role'])


def downgrade() -> None:
    """Drop agents table."""
    op.drop_index('ix_agents_role', table_name='agents')
    op.drop_index('ix_agents_agent_id', table_name='agents')
    op.drop_table('agents')
